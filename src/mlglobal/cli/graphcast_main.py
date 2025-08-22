import os
import argparse
import pandas as pd
import xarray as xr
from mlglobal.graphcast_model import GraphCastModel

def main():
    parser = argparse.ArgumentParser(description="Run GraphCast model.")
    parser.add_argument("-i", "--input", help="input file path (including file name)", required=True)
    parser.add_argument("-w", "--weights", help="parent directory of the graphcast params and stats", required=True)
    parser.add_argument("-l", "--length", help="length of forecast (6-hourly), an integer number in range [1, 40]", required=True)
    parser.add_argument("-m", "--member", help="gefs member [c00, p01, ..., p30]", required=True)
    parser.add_argument("-c", "--config", help="GC weight member file", required=True)
    parser.add_argument("-o", "--output", help="output directory", default=None)
    parser.add_argument("-p", "--pressure", help="number of pressure levels", default=13)
    parser.add_argument("-u", "--upload", help="upload input data as well as forecasts to noaa s3 bucket (yes or no)", default = "no")
    parser.add_argument("-k", "--keep", help="keep input and output after uploading to noaa s3 bucket (yes or no)", default = "no")
    args = parser.parse_args()

    runner = GraphCastModel(args.weights, args.input, args.member, args.config, args.output, int(args.pressure), int(args.length))
    runner.load_pretrained_model()
    runner.load_gdas_data()
    runner.extract_inputs_targets_forcings()
    runner.load_normalization_stats()
    runner.get_predictions()

    upload_data = args.upload.lower() == "yes"
    keep_data = args.keep.lower() == "yes"
    if upload_data:
        runner.upload_to_s3(keep_data)

if __name__ == "__main__":
    main()
