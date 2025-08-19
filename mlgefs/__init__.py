"""MLGEFS: Machine Learning Global Ensemble Forecast System

This package implements Google DeepMind GraphCast for the Global Ensemble
Forecast System (GEFS) as part of the Experimental AI Global and Limited-area
Ensemble project (EAGLE).

For detailed usage instructions, see README_PACKAGE.md
"""

__version__ = "0.1.0"
__author__ = "Linlin Cui, Jun Wang, Sadegh Tabas"
__email__ = "linlin.cui@noaa.gov, jun.wang@noaa.gov"
__license__ = "Apache-2.0"

# Conditional imports to handle missing dependencies gracefully
try:
    from . import oper
except ImportError:
    oper = None

try:
    from . import training
except ImportError:
    training = None

__all__ = ["__version__", "__author__", "__email__", "__license__"]

# Add available modules to __all__
if oper is not None:
    __all__.append("oper")
if training is not None:
    __all__.append("training")
