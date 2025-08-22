import os
import requests
import boto3
from datetime import datetime

class ICDownloader:
    MODES = {
        'gefs': {
            'bucket_name': 'noaa-ncepdev-none-ca-ufs-cpldcld',
            'root_directory': 'gefs',
        },
        'gfs': {
            'bucket_name': 'noaa-gfs-bdp-pds',
            'root_directory': 'gdas',
        }
    }

    def __init__(self, mode, start_datetime, end_datetime, member=None, download_source='s3', download_directory=None):
        self.mode = mode
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.member = member
        self.download_source = download_source
        self.bucket_name = self.MODES[mode]['bucket_name']
        self.root_directory = self.MODES[mode]['root_directory']
        self.download_directory = download_directory or os.getcwd()

    def s3bucket(self, date_str, time_str, local_directory):
        if self.mode == 'gefs':
            member_str = f"ge{self.member}"
        else:
            member_str = "gdas"
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
            if self.mode == 'gefs':
                curr_file = f"ge{self.member}.t{time_str}z.{file_format}"
            else:
                curr_file = f"gdas.t{time_str}z.{file_format}"
            get_data(s3_prefix, curr_file, local_directory)

    def archive(self, date_str, time_str, local_directory):
        data_path = "/lfs/h2/emc/ptmp/jun.wang"
        def get_data(data_path, file_format, local_directory):
            file_objects = glob.glob(f"{data_path}/{self.root_directory}.{date_str}/{time_str}/*/*/*")
            for obj_key in file_objects:
                if obj_key.endswith(f'{file_format}'):
                    local_file_path = os.path.join(local_directory, os.path.basename(obj_key))
                    try:
                        os.symlink(obj_key, local_file_path)
                        print(f"Symbolic link created: {obj_key} -> {local_directory}")
                    except OSError as e:
                        print(f"Error creating symbolic link: {e}")
        for file_format in self.file_formats:
            if self.mode == 'gefs':
                curr_file = f"ge{self.member}.t{time_str}z.{file_format}"
            else:
                curr_file = f"gdas.t{time_str}z.{file_format}"
            get_data(data_path, curr_file, local_directory)

    def download(self):
        import boto3
        from datetime import timedelta
        profile_name = os.environ.get('AWS_PROFILE', 'default')
        session = boto3.Session(profile_name=profile_name)
        current_credentials = session.get_credentials().get_frozen_credentials()
        self.s3 = session.client(
            's3',
            aws_access_key_id=current_credentials.access_key,
            aws_secret_access_key=current_credentials.secret_key,
        )
        if self.mode == 'gefs':
            self.file_formats = ['pgrb2.0p25.f000', 'pgrb2s.0p25.f000'] if self.member and self.member.isdigit() and int(self.member) <= 30 else ['pgrb2.0p25.f000', 'pgrb2b.0p25.f000', 'pgrb2.0p25.f006']
        else:
            self.file_formats = ['pgrb2.0p25.f000', 'pgrb2.0p25.f006']
        current_datetime = self.start_datetime
        while current_datetime <= self.end_datetime:
            date_str = current_datetime.strftime("%Y%m%d")
            time_str = current_datetime.strftime("%H")
            if self.mode == 'gefs':
                local_directory = os.path.join(self.download_directory or os.getcwd(), self.bucket_name+f'_{len(self.file_formats)}_{self.member}', date_str, time_str)
            else:
                local_directory = os.path.join(self.download_directory or os.getcwd(), self.bucket_name+f'_{len(self.file_formats)}', date_str, time_str)
            os.makedirs(local_directory, exist_ok=True)
            if self.download_source == 's3':
                self.s3bucket(date_str, time_str, local_directory)
            elif self.download_source == 'wcoss2':
                self.archive(date_str, time_str, local_directory)
            else:
                raise ValueError(f'data source {self.download_source} is not supported, choose either s3 or wcoss2!')
            current_datetime += timedelta(hours=6)
        print("Download completed.")
