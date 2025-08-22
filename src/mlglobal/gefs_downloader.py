import os
import glob
import boto3
from datetime import timedelta

class GEFSDownloader:
    def __init__(self, start_datetime, end_datetime, member, num_pressure_levels=13, data_source='s3', download_directory=None):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.member = member
        self.num_levels = num_pressure_levels
        self.data_source = data_source
        self.download_directory = download_directory

        profile_name = os.environ.get('AWS_PROFILE', 'default')
        session = boto3.Session(profile_name=profile_name)
        current_credentials = session.get_credentials().get_frozen_credentials()
        self.s3 = session.client(
            's3',
            aws_access_key_id=current_credentials.access_key,
            aws_secret_access_key=current_credentials.secret_key,
        )
        self.bucket_name = 'noaa-ncepdev-none-ca-ufs-cpldcld'
        self.root_directory = 'gefs'
        if self.download_directory is None:
            self.local_base_directory = os.path.join(os.getcwd(), self.bucket_name+f'_{self.num_levels}_{self.member}')
        else:
            self.local_base_directory = os.path.join(self.download_directory, self.bucket_name+f'_{self.num_levels}_{self.member}')
        if self.num_levels == 13:
            self.file_formats = ['pgrb2.0p25.f000', 'pgrb2s.0p25.f000']
        else:
            self.file_formats = ['pgrb2.0p25.f000', 'pgrb2b.0p25.f000', 'pgrb2.0p25.f006']

    def s3bucket(self, date_str, time_str, local_directory):
        s3_prefix = f"Linlin.Cui/gefs_wcoss2/{self.root_directory}.{date_str}/{time_str}/atmos/"
        def get_data(s3_prefix, file_format, local_directory):
            s3_objects = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=s3_prefix)
            for obj in s3_objects.get('Contents', []):
                obj_key = obj['Key']
                if obj_key.endswith(f'{file_format}'):
                    local_file_path = os.path.join(local_directory, os.path.basename(obj_key))
                    self.s3.download_file(self.bucket_name, obj_key, local_file_path)
                    print(f"Downloaded {obj_key} to {local_file_path}")
        for file_format in self.file_formats:
            curr_file = f"ge{self.member}.t{time_str}z.{file_format}"
            get_data(s3_prefix, curr_file, local_directory)

    def archive(self, date_str, time_str, local_directory):
        data_path = "/lfs/h2/emc/ptmp/jun.wang"
        def get_data(data_path, file_format, local_directory):
            file_objects = glob.glob(f"{data_path}/gefs.{date_str}/{time_str}/*/*/*")
            for obj_key in file_objects:
                if obj_key.endswith(f'{file_format}'):
                    local_file_path = os.path.join(local_directory, os.path.basename(obj_key))
                    try:
                        os.symlink(obj_key, local_file_path)
                        print(f"Symbolic link created: {obj_key} -> {local_directory}")
                    except OSError as e:
                        print(f"Error creating symbolic link: {e}")
        for file_format in self.file_formats:
            curr_file = f"ge{self.member}.t{time_str}z.{file_format}"
            get_data(data_path, curr_file, local_directory)

    def download_data(self):
        current_datetime = self.start_datetime
        while current_datetime <= self.end_datetime:
            date_str = current_datetime.strftime("%Y%m%d")
            time_str = current_datetime.strftime("%H")
            local_directory = os.path.join(self.local_base_directory, date_str, time_str)
            os.makedirs(local_directory, exist_ok=True)
            if self.data_source == 's3':
                self.s3bucket(date_str, time_str, local_directory)
            elif self.data_source == 'wcoss2':
                self.archive(date_str, time_str, local_directory)
            else:
                raise ValueError(f'data source {self.data_source} is not supported, choose either s3 or wcoss2!')
            current_datetime += timedelta(hours=6)
        print("Download completed.")
