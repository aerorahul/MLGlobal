import os
import numpy as np
import xarray as xr
import glob
import re
import subprocess
from datetime import timedelta

class GEFSPreprocessor:
    def __init__(self, start_datetime, end_datetime, member, num_pressure_levels=13, output_directory=None, download_directory=None, keep_downloaded_data=True):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.member = member
        self.num_levels = num_pressure_levels
        self.output_directory = output_directory
        self.download_directory = download_directory
        self.keep_downloaded_data = keep_downloaded_data
        self.bucket_name = 'noaa-ncepdev-none-ca-ufs-cpldcld'
        if self.download_directory is None:
            self.local_base_directory = os.path.join(os.getcwd(), self.bucket_name+f'_{self.num_levels}_{self.member}')
        else:
            self.local_base_directory = os.path.join(self.download_directory, self.bucket_name+f'_{self.num_levels}_{self.member}')

    def process_data_with_wgrib2(self):
        # Define the directory where your GRIB2 files are located
        data_directory = self.local_base_directory

        # Create a dictionary to specify the variables, levels, and whether to extract only the first time step (if needed)
        variables_to_extract = {
            '.pgrb2s.0p25.f000': {
                ':HGT:': {
                    'levels': [':surface:'],
                    'first_time_step_only': True,  # Extract only the first time step
                },
                ':TMP:': {
                    'levels': [':2 m above ground:'],
                },
                ':PRMSL:': {
                    'levels': [':mean sea level:'],
                },
                ':VGRD|UGRD:': {
                    'levels': [':10 m above ground:'],
                },
            },
            '.pgrb2.0p25.f000': {
                ':LAND:': {
                    'levels': [':surface:'],
                    'first_time_step_only': True,  # Extract only the first time step
                },
                ':SPFH|VVEL|VGRD|UGRD|HGT|TMP:': {
                    'levels': [':(50|100|150|200|250|300|400|500|600|700|850|925|1000) mb:'],
                },
            }
        }
        if self.num_levels == 37:
            variables_to_extract['.pgrb2.0p25.f000'][':SPFH|VVEL|VGRD|UGRD|HGT|TMP:']['levels'] = [':(1|2|3|5|7|10|20|30|50|70|100|150|200|250|300|350|400|450|500|550|600|650|700|750|800|850|900|925|950|975|1000) mb:']
            variables_to_extract['.pgrb2b.0p25.f000'] = {}
            variables_to_extract['.pgrb2b.0p25.f000'][':SPFH|VVEL|VGRD|UGRD|HGT|TMP:'] = {}
            variables_to_extract['.pgrb2b.0p25.f000'][':SPFH|VVEL|VGRD|UGRD|HGT|TMP:']['levels'] = [':(125|175|225|775|825|875) mb:']

        # Create an empty list to store the extracted datasets
        extracted_datasets = []
        files = []
        print("Start extracting variables and associated levels from grib2 files:")
        # Loop through each folder (e.g., gdas.yyyymmdd)
        date_folders = sorted(next(os.walk(data_directory))[1])
        for date_folder in date_folders:
            date_folder_path = os.path.join(data_directory, date_folder)

            # Loop through each hour (e.g., '00', '06', '12', '18')
            for hour in ['00', '06', '12', '18']:
                subfolder_path = os.path.join(date_folder_path, hour)

                # Check if the subfolder exists before processing
                if os.path.exists(subfolder_path):
                    # Loop through each GRIB2 file (.f000, .f001, .f006)
                    for file_extension, variable_data in variables_to_extract.items():
                        for variable, data in variable_data.items():
                            levels = data['levels']
                            first_time_step_only = data.get('first_time_step_only', False)  # Default to False if not specified

                            pattern = os.path.join(subfolder_path, f'ge{self.member}.t*z{file_extension}')
                            # Use glob to search for files matching the pattern
                            matching_files = glob.glob(pattern)

                            # Check if there's exactly one matching file
                            if len(matching_files) == 1:
                                grib2_file = matching_files[0]
                                print("Found file:", grib2_file)
                            else:
                                print("Error: Found multiple or no matching files.")

                            # Extract the specified variables with levels from the GRIB2 file
                            for level in levels:
                                output_file = os.path.join(self.download_directory,f'{variable}_{level}_{date_folder}_{hour}{file_extension}_{self.num_levels}_{self.member}.nc')
                                files.append(output_file)

                                # Extracting levels using regular expression
                                matches = re.findall(r'\d+', level)

                                # Convert the extracted matches to integers
                                curr_levels = [int(match) for match in matches]

                                # Get the number of levels
                                number_of_levels = len(curr_levels)

                                # Use wgrib2 to extract the variable with level
                                wgrib2_command = ['wgrib2', '-nc_nlev', f'{number_of_levels}', grib2_file, '-match', f'{variable}', '-match', f'{level}', '-netcdf', output_file]
                                subprocess.run(wgrib2_command, check=True)

                                # Open the extracted netcdf file as an xarray dataset
                                ds = xr.open_dataset(output_file)

                                # if variable == '^(597):':
                                #    ds['time'] = ds['time'] - np.timedelta64(6, 'h')

                                # If specified, extract only the first time step
                                if variable not in [':LAND:', ':HGT:']:
                                    extracted_datasets.append(ds)
                                else:
                                    if first_time_step_only:
                                        # Append the dataset to the list
                                        ds = ds.isel(time=0)
                                        extracted_datasets.append(ds)
                                        variables_to_extract[file_extension][variable]['first_time_step_only'] = False

                                # Optionally, remove the intermediate GRIB2 file
                                # os.remove(output_file)
        print("Merging grib2 files:")
        ds = xr.merge(extracted_datasets)

        print("Merging process completed.")

        print("Processing, Renaming and Reshaping the data")
        # Drop the 'level' dimension
        ds = ds.drop_dims('level')

        # Rename variables and dimensions
        ds = ds.rename({
            'latitude': 'lat',
            'longitude': 'lon',
            'plevel': 'level',
            'HGT_surface': 'geopotential_at_surface',
            'LAND_surface': 'land_sea_mask',
            'PRMSL_meansealevel': 'mean_sea_level_pressure',
            'TMP_2maboveground': '2m_temperature',
            'UGRD_10maboveground': '10m_u_component_of_wind',
            'VGRD_10maboveground': '10m_v_component_of_wind',
            #'APCP_surface': 'total_precipitation_6hr',
            'HGT': 'geopotential',
            'TMP': 'temperature',
            'SPFH': 'specific_humidity',
            'VVEL': 'vertical_velocity',
            'UGRD': 'u_component_of_wind',
            'VGRD': 'v_component_of_wind'
        })

        # Assign 'datetime' as coordinates
        ds = ds.assign_coords(datetime=ds.time)

        # Convert data types
        ds['lat'] = ds['lat'].astype('float32')
        ds['lon'] = ds['lon'].astype('float32')
        ds['level'] = ds['level'].astype('int32')

        # Adjust time values relative to the first time step
        ds['time'] = ds['time'] - ds.time[0]

        # Expand dimensions
        ds = ds.expand_dims(dim='batch')
        ds['datetime'] = ds['datetime'].expand_dims(dim='batch')

        # Squeeze dimensions
        ds['geopotential_at_surface'] = ds['geopotential_at_surface'].squeeze('batch')
        ds['land_sea_mask'] = ds['land_sea_mask'].squeeze('batch')

        # Update geopotential unit to m2/s2 by multiplying 9.80665
        ds['geopotential_at_surface'] = ds['geopotential_at_surface'] * 9.80665
        ds['geopotential'] = ds['geopotential'] * 9.80665

        # Update total_precipitation_6hr unit to (m) from (kg/m^2) by dividing it by 1000kg/m³
        # ds['total_precipitation_6hr'] = ds['total_precipitation_6hr'] / 1000
        # add total precip with 0 values (does not impact the forecasts for 13 PLs)
        other_dims = ['batch', 'time', 'lat', 'lon']
        # Create an array filled with zeros for other dimensions
        zeros_shape = tuple(ds.sizes[dim] for dim in other_dims)
        zeros_array = np.zeros(zeros_shape, dtype=np.float32)

        # Add the zeros array as a new variable in the dataset
        ds['total_precipitation_6hr'] = (other_dims, zeros_array)

        # Define the output NetCDF file
        date = (self.start_datetime + timedelta(hours=6)).strftime('%Y%m%d%H')
        steps = str(len(ds['time']))

        if self.output_directory is None:
            self.output_directory = os.getcwd()  # Use current directory if not specified

        os.makedirs(self.output_directory, exist_ok=True)
        output_netcdf = os.path.join(self.output_directory, f"source-ge{self.member}_date-{date}_res-0.25_levels-{self.num_levels}_steps-{steps}.nc")

        # Save the merged dataset as a NetCDF file
        ds.to_netcdf(output_netcdf)
        print(f"Saved output to {output_netcdf}")
        for file in files:
            os.remove(file)

        # Optionally, remove downloaded data
        if not self.keep_downloaded_data:
            self.remove_downloaded_data()

        print(f"Process completed successfully, your inputs for GraphCast model generated at:\n {output_netcdf}")

    def remove_downloaded_data(self):
        # Remove downloaded data from the specified directory
        print("Removing downloaded grib2 data...")
        try:
            os.system(f"rm -rf {self.local_base_directory}")
            print("Downloaded data removed.")
        except Exception as e:
            print(f"Error removing downloaded data: {str(e)}")

    def get_dataarray(self, grbfile, var_name, level_type, desired_level):

        # Find the matching grib message
        variable_message = grbfile.select(shortName=var_name, typeOfLevel=level_type, level=desired_level)

        # create a netcdf dataset using the matching grib message
        lats, lons = variable_message[0].latlons()
        lats = lats[:,0]
        lons = lons[0,:]

        #check latitude range
        reverse_lat = False
        if lats[0] > 0:
            reverse_lat = True
            lats = lats[::-1]

        steps = variable_message[0].validDate
        if var_name=='tp':
            steps = steps + timedelta(hours=6)
        #precipitation rate has two stepType ('instant', 'avg'), use 'instant')
        if len(variable_message) > 2:
            data = []
            for message in variable_message:
                data.append(message.values)
            data = np.array(data)
            if reverse_lat:
                data = data[:, ::-1, :]
        else:
            data = variable_message[0].values
            if reverse_lat:
                data = data[::-1, :]

        if len(data.shape) == 2:
            da = xr.Dataset(
                data_vars={
                    var_name: (['lat', 'lon'], data.astype('float32'))
                },
                coords={
                    'lon': lons.astype('float32'),
                    'lat': lats.astype('float32'),
                    'time': steps,
                }
            )
        elif len(data.shape) == 3:
            da = xr.Dataset(
                data_vars={
                    var_name: (['level', 'lat', 'lon'], data.astype('float32'))
                },
                coords={
                    'lon': lons.astype('float32'),
                    'lat': lats.astype('float32'),
                    'level': np.array(desired_level).astype('int32'),
                    'time': steps,
                }
            )

        return da
