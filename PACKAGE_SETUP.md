# MLGEFS Package Structure

## Installation Instructions

To convert this project into a pip-installable package, follow these steps:

1. **Copy Python modules to the package structure:**
   ```bash
   # Copy operational scripts
   cp oper/*.py mlgefs/oper/
   cp oper/utils/*.py mlgefs/oper/utils/

   # Copy training scripts
   cp training/*.py mlgefs/training/
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   ```

3. **Or install from source:**
   ```bash
   pip install .
   ```

4. **Or build and distribute:**
   ```bash
   python -m build
   pip install dist/mlgefs-0.1.0-py3-none-any.whl
   ```

## Package Structure

```
mlgefs/
├── __init__.py                    # Main package init
├── oper/                         # Operational modules
│   ├── __init__.py
│   ├── gen_gefs_ics.py          # GEFS initial conditions generation
│   ├── run_graphcast_ens.py     # GraphCast ensemble runner
│   ├── submit_job_aws.py        # AWS job submission
│   ├── submit_mlgefs_job.py     # MLGEFS job submission
│   └── utils/
│       ├── __init__.py
│       └── nc2grib.py           # NetCDF to GRIB2 converter
├── training/                     # Training modules
│   ├── __init__.py
│   └── generate_batch_files.py  # Batch file generation
```

## Command Line Tools

Once installed, the following command-line tools will be available:

- `mlgefs-gen-ics`: Generate GEFS initial conditions
- `mlgefs-run-forecast`: Run GraphCast ensemble forecast
- `mlgefs-generate-batch`: Generate batch files for training

## Usage Examples

```bash
# Generate initial conditions
mlgefs-gen-ics 2025080100 2025080106 c00 -l 13 -o ./output

# Run ensemble forecast
mlgefs-run-forecast -i input.nc -w ./weights -l 40 -m c00 -c config.pkl

# Generate batch files
mlgefs-generate-batch --input ./gefs_data --output ./batch_files
```
