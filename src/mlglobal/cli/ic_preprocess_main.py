import argparse
from datetime import datetime
from mlglobal.ic_preprocessor import ICPreprocessor

def main():
    parser = argparse.ArgumentParser(description="Preprocess IC data (GEFS/GFS)")
    parser.add_argument('--mode', choices=['gefs', 'gfs'], required=True)
    parser.add_argument('--start', required=True, help='Start datetime (YYYYMMDDHH)')
    parser.add_argument('--end', required=True, help='End datetime (YYYYMMDDHH)')
    parser.add_argument('--num-pressure-levels', type=int, choices=[13, 37], default=13)
    parser.add_argument('--member', help='Ensemble member (for GEFS)')
    parser.add_argument('--output-directory', default=None)
    parser.add_argument('--download-directory', default=None)
    parser.add_argument('--keep-downloaded-data', action='store_true')
    args = parser.parse_args()

    start_dt = datetime.strptime(args.start, '%Y%m%d%H')
    end_dt = datetime.strptime(args.end, '%Y%m%d%H')
    preprocessor = ICPreprocessor(
        mode=args.mode,
        start_datetime=start_dt,
        end_datetime=end_dt,
        num_pressure_levels=args.num_pressure_levels,
        member=args.member,
        output_directory=args.output_directory,
        download_directory=args.download_directory,
        keep_downloaded_data=args.keep_downloaded_data
    )
    preprocessor.process_data_with_wgrib2()

if __name__ == '__main__':
    main()
