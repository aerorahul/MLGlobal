#!/usr/bin/env python3

import os
import subprocess
import argparse
from datetime import timedelta

import json
import grib2io
import xarray as xr
import numpy as np
import pandas as pd

class Netcdf2Grib:
    """
    Class for converting NetCDF data to GRIB2 using either eccodes/iris or grib2io backend.
    """
    def __init__(self, backend="grib2io", start_date=None, table_file="tables.json"):
        """
        Initialize the Netcdf2Grib converter.

        Parameters
        ----------
        backend : str, optional
            Backend to use for conversion ('eccodes' or 'grib2io'). Default is 'eccodes'.
        start_date : datetime-like, optional
            Forecast initialization time.
        table_file : str, optional
            Path to tables.json (required for grib2io backend).
        """
        self.backend = backend
        self.start_date = start_date
        self.table_file = table_file

        # Attribute mapping for eccodes/iris backend
        self.ATTR_MAPS = {
            '10m_u_component_of_wind': [10, 'x_wind', 'm s**-1'],
            '10m_v_component_of_wind': [10, 'y_wind', 'm s**-1'],
            'mean_sea_level_pressure': [0, 'air_pressure_at_sea_level', 'Pa'],
            '2m_temperature': [2, 'air_temperature', 'K'],
            'total_precipitation_6hr': [0, 'precipitation_amount', 'kg m**-2'],
            'total_precipitation_cumsum': [0, 'precipitation_amount', 'kg m**-2'],
            'vertical_velocity': [None, 'lagrangian_tendency_of_air_pressure', 'Pa s**-1'],
            'specific_humidity': [None, 'specific_humidity', 'kg kg**-1'],
            'temperature': [None, 'air_temperature', 'K'],
            'geopotential': [None, 'geopotential_height', 'm'],
            'u_component_of_wind': [None, 'x_wind', 'm s**-1'],
            'v_component_of_wind': [None, 'y_wind', 'm s**-1'],
        }
        # Section 3 template for grib2io backend
        self.SECTION3 = np.array([0, 1038240, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 1440, 721, 0, -1, 90000000, 0, 48, -90000000, 359750000,250000, 250000, 0])

        # Backend-specific imports (restored to method scope)
        if backend == "grib2io":
            with open(table_file or "utils/tables.json", "r") as f:
                self.attrs = json.load(f)


    def save_grib2(self, ds, gefs_member, outdir):
        """
        Convert NetCDF dataset to GRIB2 files using the selected backend and generate wgrib2 index files.

        Parameters
        ----------
        ds : xarray.Dataset
            Input NetCDF dataset.
        gefs_member : str
            GEFS member string (e.g., 'c00').
        outdir : str
            Output directory for GRIB2 files.
        """
        grib2_files = []
        if self.backend == "eccodes":
            grib2_files = self.save_grib2_eccodes(ds, gefs_member, outdir)
        elif self.backend == "grib2io":
            grib2_files = self.save_grib2_grib2io(ds, gefs_member, outdir)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

        # Generate grib2 index for each output file
        for grib2_file in grib2_files:
            self.generate_wgrib2_index(grib2_file)


    def save_grib2_eccodes(self, forecasts, gefs_member, outdir):
        """
        Convert NetCDF dataset to GRIB2 files using eccodes/iris backend.

        Parameters
        ----------
        forecasts : xarray.Dataset
            Input NetCDF dataset.
        gefs_member : str
            GEFS member string.
        outdir : str
            Output directory for GRIB2 files.
        """
        import cf_units
        import iris
        import iris_grib

        # Reverse latitude for GRIB2 convention
        forecasts = forecasts.reindex(lat=list(reversed(forecasts.lat)))
        # Remove 'batch' dimension if present
        for var in forecasts.variables:
            if 'batch' in forecasts[var].dims:
                forecasts[var] = forecasts[var].squeeze(dim='batch')
        # Convert units as needed
        forecasts['level'] = forecasts['level'] * 100
        forecasts['level'].attrs['long_name'] = 'pressure'
        forecasts['level'].attrs['units'] = 'Pa'
        forecasts['geopotential'] = forecasts['geopotential'] / 9.80665
        if 'total_precipitation_6hr' in forecasts:
            forecasts['total_precipitation_6hr'] = (forecasts['total_precipitation_6hr'].clip(min=0)) * 1000
            forecasts['total_precipitation_cumsum'] = forecasts['total_precipitation_6hr'].cumsum(axis=0)

        # Write intermediate NetCDF file for iris
        filename = os.path.join(outdir, f"forecast_to_grib2_{gefs_member}.nc")
        forecasts.to_netcdf(filename)
        cubes = iris.load(filename)
        times = cubes[0].coord('time').points
        forecast_starttime = self.start_date
        cycle = forecast_starttime.hour
        print(f'Forecast start time is {forecast_starttime}')
        datevectors = [forecast_starttime + timedelta(hours=int(t)) for t in times]
        time_unit_str = f"Hours since {forecast_starttime.strftime('%Y-%m-%d %H:00:00')}"
        new_time_unit = cf_units.Unit(time_unit_str, calendar=cf_units.CALENDAR_STANDARD)
        new_time_points = [new_time_unit.date2num(dt) for dt in datevectors]

        new_time_coord = iris.coords.DimCoord(new_time_points, standard_name='time', units=new_time_unit)
        grib2_files = []
        for date in datevectors:
            print(f"Processing for time {date.strftime('%Y-%m-%d %H:00:00')}")
            hrs = int((date - forecast_starttime).total_seconds() // 3600)
            outfile = os.path.join(outdir, f'mlgefs{gefs_member}.t{cycle:02d}z.pgrb2.0p25.f{hrs:03d}')
            print(outfile)
            for cube in sorted(cubes, key=lambda cube: cube.name()):
                var_name = cube.name()
                # Replace time coordinate with new time points
                time_coord_dim = cube.coord_dims('time')
                cube.remove_coord('time')
                cube.add_dim_coord(new_time_coord, time_coord_dim)
                # Extract the slice for the current time
                hour_6 = iris.Constraint(time=iris.time.PartialDateTime(month=date.month, day=date.day, hour=date.hour))
                cube_slice = cube.extract(hour_6)
                # Set coordinate system for latitude/longitude
                cube_slice.coord('latitude').coord_system = iris.coord_systems.GeogCS(4326)
                cube_slice.coord('longitude').coord_system = iris.coord_systems.GeogCS(4326)
                # Handle 3D and 2D variables
                if len(cube_slice.data.shape) == 3:
                    levels = cube_slice.coord('pressure').points
                    for level in levels:
                        cube_slice_level = cube_slice.extract(iris.Constraint(pressure=level))
                        cube_slice_level.add_aux_coord(iris.coords.DimCoord(hrs, standard_name='forecast_period', units='hours'))
                        cube_slice_level.standard_name = self.ATTR_MAPS[var_name][1]
                        cube_slice_level.units = self.ATTR_MAPS[var_name][2]
                        iris.save(cube_slice_level, outfile, saver='grib2', append=True)
                else:
                    cube_slice.add_aux_coord(iris.coords.DimCoord(hrs, standard_name='forecast_period', units='hours'))
                    cube_slice.standard_name = self.ATTR_MAPS[var_name][1]
                    cube_slice.units = self.ATTR_MAPS[var_name][2]
                    # Add height/altitude or use tweaked messages for special variables
                    if var_name not in ['mean_sea_level_pressure', 'total_precipitation_6hr', 'total_precipitation_cumsum']:
                        cube_slice.add_aux_coord(iris.coords.DimCoord(self.ATTR_MAPS[var_name][0], standard_name='height', units='m'))
                        iris.save(cube_slice, outfile, saver='grib2', append=True)
                    elif var_name == 'total_precipitation_6hr':
                        iris_grib.save_messages(self.tweaked_messages(cube_slice, f'{hrs-6}-{hrs}'), outfile, append=True)
                    elif var_name == 'total_precipitation_cumsum':
                        iris_grib.save_messages(self.tweaked_messages(cube_slice, f'0-{hrs}'), outfile, append=True)
                    elif var_name == 'mean_sea_level_pressure':
                        cube_slice.add_aux_coord(iris.coords.DimCoord(self.ATTR_MAPS[var_name][0], standard_name='altitude', units='m'))
                        iris_grib.save_messages(self.tweaked_messages(cube_slice, f'{hrs-6}-{hrs}'), outfile, append=True)

            grib2_files.append(outfile)

        # Remove intermediate NetCDF file
        if os.path.isfile(filename):

            print(f'Deleting intermediate nc file {filename}: ')

            os.remove(filename)

        return grib2_files

    def tweaked_messages(self, cube, time_range):
        """
        Adjust GRIB messages for special variables using eccodes.

        Parameters
        ----------
        cube : iris.cube.Cube
            Iris cube for the variable.
        time_range : str
            Step range string for GRIB2 (e.g., '0-6').

        Yields
        ------
        grib_message : eccodes.GribMessage
            Tweaked GRIB2 message for writing.
        """
        import eccodes
        import iris_grib
        for cube, grib_message in iris_grib.save_pairs_from_cube(cube):
            # Set center to 'kwbc' (NCEP)
            eccodes.codes_set(grib_message, 'centre', 'kwbc')
            # Special handling for precipitation and pressure
            if cube.standard_name == 'precipitation_amount':
                eccodes.codes_set(grib_message, 'stepType', 'accum')
                eccodes.codes_set(grib_message, 'stepRange', time_range)
                eccodes.codes_set(grib_message, 'discipline', 0)
                eccodes.codes_set(grib_message, 'parameterCategory', 1)
                eccodes.codes_set(grib_message, 'parameterNumber', 8)
                eccodes.codes_set(grib_message, 'typeOfFirstFixedSurface', 1)
                eccodes.codes_set(grib_message, 'typeOfStatisticalProcessing', 1)
            elif cube.standard_name == 'air_pressure_at_sea_level':
                eccodes.codes_set(grib_message, 'discipline', 0)
                eccodes.codes_set(grib_message, 'parameterCategory', 3)
                eccodes.codes_set(grib_message, 'parameterNumber', 1)
                eccodes.codes_set(grib_message, 'typeOfFirstFixedSurface', 101)
            yield grib_message

    def save_grib2_grib2io(self, xarray_ds, gefs_member, outdir):
        """
        Convert NetCDF dataset to GRIB2 files using grib2io backend.

        Parameters
        ----------
        xarray_ds : xarray.Dataset
            Input NetCDF dataset.
        gefs_member : str
            GEFS member string.
        outdir : str
            Output directory for GRIB2 files.
        """
        # Convert geopotential to geopotential height
        xarray_ds["geopotential"] = xarray_ds["geopotential"] / 9.80665
        # Accumulate 6-hr precipitation and cumsum
        if "total_precipitation_6hr" in xarray_ds:
            xarray_ds["total_precipitation_6hr"] = xarray_ds["total_precipitation_6hr"].clip(min=0) * 1000
            xarray_ds["total_precipitation_cumsum"] = xarray_ds["total_precipitation_6hr"].cumsum(axis=0)
        # Convert levels from mb to Pa
        xarray_ds["level"] = xarray_ds["level"] * 100
        # Remove batch dimension if present
        xarray_ds = xarray_ds.squeeze(dim="batch")
        # Reverse latitude for GRIB2 convention
        xarray_ds = xarray_ds.reindex(lat = xarray_ds.lat[::-1])

        grib2_files = []
        for time in xarray_ds.coords["time"]:
            ds_singletime = xarray_ds.sel(time=time)
            cycle = self.start_date.hour
            lead = int(time.dt.total_seconds()//3600)
            outfile = os.path.join(outdir, f"mlgefs{gefs_member}.t{cycle:02d}z.pgrb2.0p25.f{lead:03d}")
            # Remove old file if exists
            if os.path.isfile(outfile):
                os.remove(outfile)
            grib2_out = grib2io.open(outfile, mode="w")
            print(f" Opening GRIB2 File: {outfile}")
            # Write each variable to GRIB2
            for var in sorted(xarray_ds.data_vars):
                da = ds_singletime[var]
                if "level" in da.coords.keys():
                    for level in da.coords["level"]:
                        msg = self.create_grib2_message(var, da, lead, level=level)
                        msg.data = da.sel(level=level).values
                        msg.pack()
                        print(f"\t{msg}")
                        grib2_out.write(msg)
                else:
                    msg = self.create_grib2_message(var, da, lead)
                    msg.data = da.values
                    msg.pack()
                    print(f"\t{msg}")
                    grib2_out.write(msg)
            grib2_out.close()
            grib2_files.append(outfile)
        return grib2_files


    def create_grib2_message(self, var, da, lead, level=None):
        """
        Create a GRIB2 message for a variable using grib2io backend.

        Parameters
        ----------
        var : str
            Variable name.
        da : xarray.DataArray
            DataArray for the variable.
        lead : int
            Lead time in hours.
        level : float, optional
            Pressure level value (Pa), if applicable.

        Returns
        -------
        msg : grib2io.Grib2Message
            Configured GRIB2 message ready for packing and writing.
        """

        # Set duration for precipitation variables
        duration = timedelta(hours=0)
        if var == "total_precipitation_6hr":
            duration = timedelta(hours=6)
        elif var == "total_precipitation_cumsum":
            duration = timedelta(hours=lead)
        # Create GRIB2 message
        msg = grib2io.Grib2Message(
            section3=self.SECTION3,
            pdtn=self.attrs[var]["templates"]["pdtn"],
            drtn=self.attrs[var]["templates"]["drtn"],
        )
        # Set attributes from table
        for k,v in self.attrs[var]["attrs"].items():
            setattr(msg, k, v)
        msg.refDate = self.start_date
        msg.duration = duration
        msg.unitOfForecastTime = 1 # Hour
        msg.leadTime = timedelta(hours=lead)
        if level is not None:
            msg.scaledValueOfFirstFixedSurface = level
        return msg


    @staticmethod
    def generate_wgrib2_index(grib2_file):
        """
        Generate a grib2 index file for a given GRIB2 file.

        Parameters
        ----------
        grib2_file : str
            Path to the GRIB2 file for which to generate the index.
        """
        output_idx_file = f"{grib2_file}.idx"
        wgrib2_command = ['wgrib2', '-s', grib2_file]
        try:
            with open(output_idx_file, "w") as f_out:
                subprocess.run(wgrib2_command, stdout=f_out, check=True)
            print(f"Index file created successfully: {output_idx_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error running wgrib2 command: {e}")

