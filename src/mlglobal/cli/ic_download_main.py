import argparse
from datetime import datetime
from mlglobal.ic_downloader import ICDownloader

def main():
    parser = argparse.ArgumentParser(description="Download IC data (GEFS/GFS)")
    parser.add_argument('--mode', choices=['gefs', 'gfs'], required=True)
    parser.add_argument('--start', required=True, help='Start datetime (YYYYMMDDHH)')
    parser.add_argument('--end', required=True, help='End datetime (YYYYMMDDHH)')
    parser.add_argument('--member', help='Ensemble member (for GEFS)')
    parser.add_argument('--download-source', choices=['s3', 'nomads'], default='s3')
    parser.add_argument('--download-directory', default=None)
    args = parser.parse_args()

    start_dt = datetime.strptime(args.start, '%Y%m%d%H')
    end_dt = datetime.strptime(args.end, '%Y%m%d%H')
    downloader = ICDownloader(
        mode=args.mode,
        start_datetime=start_dt,
        end_datetime=end_dt,
        member=args.member,
        download_source=args.download_source,
        download_directory=args.download_directory
    )
    downloader.download()

if __name__ == '__main__':
    main()
