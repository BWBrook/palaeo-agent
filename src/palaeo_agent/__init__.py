"""Explicit scientific operations with inspectable evidence."""

from .core import AnalysisError, RmaResult, RmaSpec, rma_regression
from .community import CommunityResult, CommunitySpec, analyse_community
from .permanova import PermanovaResult, PermanovaSpec, calculate_permanova, validate_permanova
from .methods import discover, validate
from .runs import inspect_run, reproduce, run
from .sensitivity import compare_community_runs, inspect_comparison

__version__ = "0.2.0.dev0"
__all__ = [
    "AnalysisError", "RmaResult", "RmaSpec", "discover", "inspect_run", "reproduce",
    "rma_regression", "run", "validate", "CommunitySpec", "CommunityResult", "analyse_community",
    "compare_community_runs", "inspect_comparison",
    "PermanovaResult", "PermanovaSpec",
    "calculate_permanova", "validate_permanova",
]
