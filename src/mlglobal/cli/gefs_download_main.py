import argparse
from datetime import datetime
from mlglobal.gefs_downloader import GEFSDownloader

def main():
    parser = argparse.ArgumentParser(description="Download GEFS data only")
    parser.add_argument("start_datetime", help="Start datetime in the format 'YYYYMMDDHH'")
    parser.add_argument("end_datetime", help="End datetime in the format 'YYYYMMDDHH'")
    parser.add_argument("member", help="GEFS member options: [c00, p01, ..., p30]")
    parser.add_argument("-l", "--levels", help="number of pressure levels, options: 13, 37", default="13")
    parser.add_argument("-s", "--source", help="the source repository to download gdas grib2 data, options: s3 or wcoss2", default="s3")
    parser.add_argument("-d", "--download", help="Download directory for raw data")

    args = parser.parse_args()

    start_datetime = datetime.strptime(args.start_datetime, "%Y%m%d%H")
    end_datetime = datetime.strptime(args.end_datetime, "%Y%m%d%H")
    member = args.member
    num_pressure_levels = int(args.levels)
    data_source = args.source
    download_directory = args.download

    downloader = GEFSDownloader(
        start_datetime,
        end_datetime,
        member,
        num_pressure_levels,
        data_source,
        download_directory
    )
    downloader.download_data()

if __name__ == "__main__":
    main()
