"""Explicit scientific operations with inspectable evidence."""

from .core import AnalysisError, RmaResult, RmaSpec, rma_regression
from .community import CommunityResult, CommunitySpec, analyse_community
from .permanova import PermanovaResult, PermanovaSpec, calculate_permanova, validate_permanova
from .methods import discover, validate
from .runs import inspect_run, reproduce, run
from .sensitivity import compare_community_runs, inspect_comparison
from .study import StudySpec, inspect_study, reproduce_study, run_study
from .primer import primer
from .neotoma import NeotomaSpec, inspect_neotoma, neotoma_extract, reproduce_neotoma
from .rma_paired import RmaPairedResult, RmaPairedSpec, calculate_rma_paired
from .rarefaction import RarefactionSpec, RarefactionResult, calculate_rarefaction, validate_rarefaction
from .count_homogeneity import (
    CountHomogeneitySpec, CountHomogeneityResult, calculate_count_homogeneity, validate_count_homogeneity,
)

__version__ = "0.2.0.dev0"
__all__ = [
    "AnalysisError", "RmaResult", "RmaSpec", "discover", "inspect_run", "reproduce",
    "rma_regression", "RmaPairedSpec", "RmaPairedResult", "calculate_rma_paired", "run", "validate", "CommunitySpec", "CommunityResult", "analyse_community",
    "compare_community_runs", "inspect_comparison",
    "PermanovaResult", "PermanovaSpec",
    "calculate_permanova", "validate_permanova",
    "StudySpec", "run_study", "inspect_study", "reproduce_study",
    "primer", "NeotomaSpec", "neotoma_extract", "inspect_neotoma", "reproduce_neotoma", "RarefactionSpec", "RarefactionResult", "calculate_rarefaction", "validate_rarefaction",
    "CountHomogeneitySpec", "CountHomogeneityResult", "calculate_count_homogeneity", "validate_count_homogeneity",
]
