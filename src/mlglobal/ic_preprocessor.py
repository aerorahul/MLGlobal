import os
import sys
import glob
import subprocess
from datetime import datetime, timedelta
import re
import numpy as np
import xarray as xr
import requests

class ICPreprocessor:
    # Static configuration for each mode
    MODES = {
        'gefs': {
            'bucket_name': 'noaa-ncepdev-none-ca-ufs-cpldcld',
            'root_directory': 'gefs',
            'file_formats': {13: ['pgrb2.0p25.f000', 'pgrb2s.0p25.f000'], 37: ['pgrb2.0p25.f000', 'pgrb2b.0p25.f000', 'pgrb2.0p25.f006']},
            'wgrib2_patterns': {
                13: {
                    '.pgrb2s.0p25.f000': {
                        ':HGT:': {'levels': [':surface:'], 'first_time_step_only': True},
                        ':TMP:': {'levels': [':2 m above ground:']},
                        ':PRMSL:': {'levels': [':mean sea level:']},
                        ':VGRD|UGRD:': {'levels': [':10 m above ground:']},
                    },
                    '.pgrb2.0p25.f000': {
                        ':LAND:': {'levels': [':surface:'], 'first_time_step_only': True},
                        ':SPFH|VVEL|VGRD|UGRD|HGT|TMP:': {'levels': [':(50|100|150|200|250|300|400|500|600|700|850|925|1000) mb:']},
                    }
                },
                37: {
                    '.pgrb2.0p25.f000': {
                        ':SPFH|VVEL|VGRD|UGRD|HGT|TMP:': {'levels': [':(1|2|3|5|7|10|20|30|50|70|100|150|200|250|300|350|400|450|500|550|600|650|700|750|800|850|900|925|950|975|1000) mb:']},
                    },
                    '.pgrb2b.0p25.f000': {
                        ':SPFH|VVEL|VGRD|UGRD|HGT|TMP:': {'levels': [':(125|175|225|775|825|875) mb:']},
                    }
                }
            },
        },
        'gfs': {
            'bucket_name': 'noaa-gfs-bdp-pds',
            'root_directory': 'gdas',
            'file_formats': {13: ['pgrb2.0p25.f000', 'pgrb2.0p25.f006'], 37: ['pgrb2.0p25.f000', 'pgrb2b.0p25.f000', 'pgrb2.0p25.f006']},
            'wgrib2_patterns': {
                13: {
                    '.pgrb2.0p25.f000': {
                        ':HGT:': {'levels': [':surface:'], 'first_time_step_only': True},
                        ':TMP:': {'levels': [':2 m above ground:']},
                        ':PRMSL:': {'levels': [':mean sea level:']},
                        ':VGRD|UGRD:': {'levels': [':10 m above ground:']},
                        ':SPFH|VVEL|VGRD|UGRD|HGT|TMP:': {'levels': [':(50|100|150|200|250|300|400|500|600|700|850|925|1000) mb:']},
                    },
                    '.pgrb2.0p25.f006': {
                        ':LAND:': {'levels': [':surface:'], 'first_time_step_only': True},
                        '^(597):': {'levels': [':surface:']},
                    }
                },
                37: {
                    '.pgrb2.0p25.f000': {
                        ':SPFH|VVEL|VGRD|UGRD|HGT|TMP:': {'levels': [':(1|2|3|5|7|10|20|30|50|70|100|150|200|250|300|350|400|450|500|550|600|650|700|750|800|850|900|925|950|975|1000) mb:']},
                    },
                    '.pgrb2b.0p25.f000': {
                        ':SPFH|VVEL|VGRD|UGRD|HGT|TMP:': {'levels': [':(125|175|225|775|825|875) mb:']},
                    }
                }
            },
        }
    }

    def __init__(self, mode, start_datetime, end_datetime, num_pressure_levels=13, member=None, download_source='s3', output_directory=None, download_directory=None, keep_downloaded_data=True):
        self.mode = mode
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.num_levels = num_pressure_levels
        self.member = member
        self.download_source = download_source
        self.output_directory = output_directory
        self.download_directory = download_directory
        self.keep_downloaded_data = keep_downloaded_data
        self.cycle = self.end_datetime.hour
        self.bucket_name = self.MODES[mode]['bucket_name']
        self.root_directory = self.MODES[mode]['root_directory']
        self.file_formats = self.MODES[mode]['file_formats'][num_pressure_levels]
        self.wgrib2_patterns = self.MODES[mode]['wgrib2_patterns'][num_pressure_levels]
        if self.download_directory is None:
            if mode == 'gefs':
                self.local_base_directory = os.path.join(os.getcwd(), self.bucket_name+f'_{self.num_levels}_{self.member}')
            else:
                self.local_base_directory = os.path.join(os.getcwd(), self.bucket_name+f'_{self.num_levels}')
        else:
            if mode == 'gefs':
                self.local_base_directory = os.path.join(self.download_directory, self.bucket_name+f'_{self.num_levels}_{self.member}')
            else:
                self.local_base_directory = os.path.join(self.download_directory, self.bucket_name+f'_{self.num_levels}')

    def process_data_with_wgrib2(self):
        import glob
        import re
        import subprocess
        import xarray as xr
        import numpy as np
        from datetime import timedelta
        data_directory = self.local_base_directory
        variables_to_extract = self.wgrib2_patterns
        extracted_datasets = []
        files = []
        print("Start extracting variables and associated levels from grib2 files:")
        date_folders = sorted(next(os.walk(data_directory))[1])
        for date_folder in date_folders:
            date_folder_path = os.path.join(data_directory, date_folder)
            for hour in ['00', '06', '12', '18']:
                subfolder_path = os.path.join(date_folder_path, hour)
                if os.path.exists(subfolder_path):
                    for file_extension, variable_data in variables_to_extract.items():
                        for variable, data in variable_data.items():
                            levels = data['levels']
                            first_time_step_only = data.get('first_time_step_only', False)
                            if self.mode == 'gefs':
                                pattern = os.path.join(subfolder_path, f'ge{self.member}.t*z{file_extension}')
                            else:
                                pattern = os.path.join(subfolder_path, f'gdas.t*z{file_extension}')
                            matching_files = glob.glob(pattern)
                            if len(matching_files) == 1:
                                grib2_file = matching_files[0]
                                print("Found file:", grib2_file)
                            else:
                                print("Error: Found multiple or no matching files.")
                                continue
                            for level in levels:
                                output_file = os.path.join(self.download_directory or os.getcwd(),f'{variable}_{level}_{date_folder}_{hour}{file_extension}_{self.num_levels}_{self.member}.nc')
                                files.append(output_file)
                                matches = re.findall(r'\d+', level)
                                curr_levels = [int(match) for match in matches]
                                number_of_levels = len(curr_levels)
                                wgrib2_command = ['wgrib2', '-nc_nlev', f'{number_of_levels}', grib2_file, '-match', f'{variable}', '-match', f'{level}', '-netcdf', output_file]
                                subprocess.run(wgrib2_command, check=True)
                                ds = xr.open_dataset(output_file)
                                if variable not in [':LAND:', ':HGT:']:
                                    extracted_datasets.append(ds)
                                else:
                                    if first_time_step_only:
                                        ds = ds.isel(time=0)
                                        extracted_datasets.append(ds)
                                        variables_to_extract[file_extension][variable]['first_time_step_only'] = False
        print("Merging grib2 files:")
        ds = xr.merge(extracted_datasets)
        print("Merging process completed.")
        print("Processing, Renaming and Reshaping the data")
        ds = ds.drop_dims('level')
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
            'HGT': 'geopotential',
            'TMP': 'temperature',
            'SPFH': 'specific_humidity',
            'VVEL': 'vertical_velocity',
            'UGRD': 'u_component_of_wind',
            'VGRD': 'v_component_of_wind'
        })
        ds = ds.assign_coords(datetime=ds.time)
        ds['lat'] = ds['lat'].astype('float32')
        ds['lon'] = ds['lon'].astype('float32')
        ds['level'] = ds['level'].astype('int32')
        ds['time'] = ds['time'] - ds.time[0]
        ds = ds.expand_dims(dim='batch')
        ds['datetime'] = ds['datetime'].expand_dims(dim='batch')
        ds['geopotential_at_surface'] = ds['geopotential_at_surface'].squeeze('batch')
        ds['land_sea_mask'] = ds['land_sea_mask'].squeeze('batch')
        ds['geopotential_at_surface'] = ds['geopotential_at_surface'] * 9.80665
        ds['geopotential'] = ds['geopotential'] * 9.80665
        other_dims = ['batch', 'time', 'lat', 'lon']
        zeros_shape = tuple(ds.sizes[dim] for dim in other_dims)
        zeros_array = np.zeros(zeros_shape, dtype=np.float32)
        ds['total_precipitation_6hr'] = (other_dims, zeros_array)
        date = (self.start_datetime + timedelta(hours=6)).strftime('%Y%m%d%H')
        steps = str(len(ds['time']))
        if self.output_directory is None:
            self.output_directory = os.getcwd()
        os.makedirs(self.output_directory, exist_ok=True)
        output_netcdf = os.path.join(self.output_directory, f"source-{self.mode}{self.member}_date-{date}_res-0.25_levels-{self.num_levels}_steps-{steps}.nc")
        ds.to_netcdf(output_netcdf)
        print(f"Saved merged NetCDF: {output_netcdf}")
