"""MLGlobal: Machine Learning Global Applications

This package implements Google DeepMind GraphCast for the Global Applications
as part of the Experimental AI Global and Limited-area Ensemble project (EAGLE).

For detailed usage instructions, see README.md
"""

__version__ = "0.1.0"
__author__ = "Linlin Cui, Jun Wang, Sadegh Tabas"
__email__ = "linlin.cui@noaa.gov, jun.wang@noaa.gov"
__license__ = "CC0-1.0"

__all__ = ["__version__", "__author__", "__email__", "__license__"]

from .nc2grib2 import Netcdf2Grib
from .gen_gefs_ics import GEFSDownloader, GEFSPreprocessor
from .graphcast_model import GraphCastModel

# Add available modules to __all__
__all__.append("GEFSDownloader")
__all__.append("GEFSPreprocessor")
__all__.append("GraphCastModel")
__all__.append("Netcdf2Grib")