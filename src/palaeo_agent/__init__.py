"""Explicit scientific operations with inspectable evidence."""

from .core import AnalysisError, RmaResult, RmaSpec, discover, rma_regression, validate
from .runs import inspect_run, reproduce, run

__version__ = "0.1.0.dev0"
__all__ = [
    "AnalysisError", "RmaResult", "RmaSpec", "discover", "inspect_run", "reproduce",
    "rma_regression", "run", "validate",
]
