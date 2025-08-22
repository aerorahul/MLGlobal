import os
import argparse
import pandas as pd
import xarray as xr
from mlglobal.nc2grib2 import Netcdf2Grib

def main():
    parser = argparse.ArgumentParser(description="Convert NetCDF to GRIB2 using eccodes or grib2io backend.")
    parser.add_argument("--input", required=True, help="Input NetCDF file")
    parser.add_argument("--outdir", required=True, help="Output directory")
    parser.add_argument("--gefs_member", default="c00", help="GEFS member string")
    parser.add_argument("--start_date", required=True, help="Forecast start date (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--backend", choices=["grib2io", "eccodes"], default="grib2io", help="Backend to use")
    parser.add_argument("--table_file", default="tables.json", help="Path to tables.json (for grib2io backend)")
    args = parser.parse_args()
    start_date = pd.to_datetime(args.start_date)
    ds = xr.open_dataset(args.input)
    os.makedirs(args.outdir, exist_ok=True)
    converter = Netcdf2Grib(backend=args.backend, start_date=start_date, table_file=args.table_file)
    converter.save_grib2(ds, args.gefs_member, args.outdir)

if __name__ == "__main__":
    main()
