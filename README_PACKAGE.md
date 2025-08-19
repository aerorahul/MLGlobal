# MLGEFS: Machine Learning Global Ensemble Forecast System

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

MLGEFS implements Google DeepMind's GraphCast for the Global Ensemble Forecast System (GEFS) as part of the Experimental AI Global and Limited-area Ensemble project (EAGLE). This package provides tools for downloading GEFS data, preprocessing it for GraphCast, running ensemble forecasts, and converting outputs to GRIB2 format.

## Features

- **GEFS Data Processing**: Download and preprocess GEFS ensemble data from AWS S3
- **GraphCast Integration**: Run GraphCast model with GEFS initial conditions
- **Ensemble Forecasting**: Support for 31-member ensemble forecasts
- **Format Conversion**: Convert NetCDF outputs to GRIB2 format
- **AWS Integration**: Upload results to S3 buckets
- **Flexible Configuration**: Support for different pressure levels (13 or 37)

## Installation

### Prerequisites

- Python 3.11 or higher
- GRIB utilities (`wgrib2`, `eccodes`)
- JAX (CPU or GPU version)

### From Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NOAA-EMC/MLGEFS.git
   cd MLGEFS
   ```

2. **Set up the package structure:**
   ```bash
   ./build_package.sh
   ```

3. **Install the package:**
   ```bash
   pip install -e .
   ```

### Using Conda Environment

1. **Create the conda environment:**
   ```bash
   conda env create -f environment.yml
   conda activate graphcast
   ```

2. **Install additional dependencies:**
   ```bash
   pip install -e .
   ```

3. **For GPU support:**
   ```bash
   pip install -U "jax[cuda12]"
   ```

## Usage

### Command Line Tools

After installation, the following CLI tools are available:

#### Generate Initial Conditions
```bash
mlgefs-gen-ics 2025080100 2025080106 c00 -l 13 -o ./output -d ./download
```

#### Run Ensemble Forecast
```bash
mlgefs-run-forecast -i input.nc -w ./model_weights -l 40 -m c00 -c config.pkl -o ./forecasts
```

#### Generate Training Batch Files
```bash
mlgefs-generate-batch --input ./gefs_data --output ./batch_files
```

### Python API

```python
from mlgefs.oper import GFSDataProcessor
from datetime import datetime

# Initialize data processor
processor = GFSDataProcessor(
    start_datetime=datetime(2025, 8, 1, 0),
    end_datetime=datetime(2025, 8, 1, 6),
    member="c00",
    num_pressure_levels=13
)

# Download and process data
processor.download_data()
processor.process_data_with_wgrib2()
```

## Configuration

### Model Weights

Download pre-trained model weights and statistics:
```bash
aws s3 cp --recursive s3://noaa-nws-graphcastgfs-pds/EAGLE_ensemble/model_weights model_weights --no-sign-request
```

### AWS Configuration

Set up AWS credentials for data access:
```bash
export AWS_PROFILE=your_profile
# or configure using aws configure
```

## Project Structure

```
mlgefs/
├── __init__.py                    # Main package
├── oper/                         # Operational tools
│   ├── gen_gefs_ics.py          # Initial conditions generator
│   ├── run_graphcast_ens.py     # Ensemble forecast runner
│   └── utils/
│       └── nc2grib.py           # NetCDF to GRIB2 converter
└── training/                     # Training utilities
    └── generate_batch_files.py  # Batch file generator
```

## Examples

### Complete Forecast Workflow

1. **Generate initial conditions:**
   ```bash
   mlgefs-gen-ics 2025080100 2025080106 c00 -l 13 -o ./ics
   ```

2. **Run forecast:**
   ```bash
   mlgefs-run-forecast -i ./ics/source-gec00_*.nc -w ./model_weights -l 40 -m c00 -c ./model_weights/c00.pkl
   ```

3. **Results are automatically converted to GRIB2 format**

### Ensemble Processing

Process all 31 ensemble members:
```bash
for member in c00 p{01..30}; do
    mlgefs-gen-ics 2025080100 2025080106 $member -l 13 -o ./ics_$member &
done
wait

for member in c00 p{01..30}; do
    mlgefs-run-forecast -i ./ics_$member/source-ge${member}_*.nc -w ./model_weights -l 40 -m $member -c ./model_weights/${member}.pkl &
done
wait
```

## Dependencies

### Core Dependencies
- numpy >= 1.21.0
- xarray >= 2022.6.0
- netCDF4 >= 1.6.0
- cartopy >= 0.21.0
- pygrib >= 2.1.4
- iris >= 3.4.0
- boto3 >= 1.26.0

### ML Dependencies
- jax >= 0.4.1
- haiku-dm >= 0.0.9
- dm-tree >= 0.1.7
- flax >= 0.6.0

### Optional Dependencies
- JAX GPU support: `pip install mlgefs[gpu]`
- Development tools: `pip install mlgefs[dev]`
- Jupyter notebooks: `pip install mlgefs[notebooks]`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Citation

If you use MLGEFS in your research, please cite:

```bibtex
@software{mlgefs2025,
  title={MLGEFS: Machine Learning Global Ensemble Forecast System},
  author={Cui, Linlin and Wang, Jun and Tabas, Sadegh},
  year={2025},
  organization={NOAA},
  url={https://github.com/NOAA-EMC/MLGEFS}
}
```

## Contact

- Linlin Cui: [linlin.cui@noaa.gov](mailto:linlin.cui@noaa.gov)
- Jun Wang: [jun.wang@noaa.gov](mailto:jun.wang@noaa.gov)

## Acknowledgments

- Google DeepMind for the GraphCast model
- NOAA Environmental Modeling Center
- GEFS development team
