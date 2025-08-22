import argparse
from datetime import datetime
from mlglobal.gefs_preprocessor import GEFSPreprocessor

def main():
    parser = argparse.ArgumentParser(description="Preprocess previously downloaded GEFS data")
    parser.add_argument("start_datetime", help="Start datetime in the format 'YYYYMMDDHH'")
    parser.add_argument("end_datetime", help="End datetime in the format 'YYYYMMDDHH'")
    parser.add_argument("member", help="GEFS member options: [c00, p01, ..., p30]")
    parser.add_argument("-l", "--levels", help="number of pressure levels, options: 13, 37", default="13")
    parser.add_argument("-m", "--method", help="method to extract variables from grib2, options: wgrib2, pygrib", default="wgrib2")
    parser.add_argument("-o", "--output", help="Output directory for processed data")
    parser.add_argument("-d", "--download", help="Download directory for raw data")
    parser.add_argument("-k", "--keep", help="Keep downloaded data (yes or no)", default="no")

    args = parser.parse_args()

    start_datetime = datetime.strptime(args.start_datetime, "%Y%m%d%H")
    end_datetime = datetime.strptime(args.end_datetime, "%Y%m%d%H")
    member = args.member
    num_pressure_levels = int(args.levels)
    method = args.method
    output_directory = args.output
    download_directory = args.download
    keep_downloaded_data = args.keep.lower() == "yes"

    preprocessor = GEFSPreprocessor(
        start_datetime,
        end_datetime,
        member,
        num_pressure_levels,
        output_directory,
        download_directory,
        keep_downloaded_data
    )
    if method == "wgrib2":
        preprocessor.process_data_with_wgrib2()
    elif method == "pygrib":
        preprocessor.process_data_with_pygrib()
    else:
        raise NotImplementedError(f"Method {method} is not supported!")

if __name__ == "__main__":
    main()
