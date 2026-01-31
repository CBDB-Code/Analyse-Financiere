"""
Metriques financieres standard.

Ce module expose les metriques de liquidite et de rentabilite
utilisees dans l'analyse financiere classique.
"""

from src.calculations.standard.liquidity import FondsDeRoulement, BFR
from src.calculations.standard.profitability import (
    EBITDA,
    MargeBrute,
    MargeExploitation,
    MargeNette,
)

__all__ = [
    # Liquidite
    "FondsDeRoulement",
    "BFR",
    # Rentabilite
    "EBITDA",
    "MargeBrute",
    "MargeExploitation",
    "MargeNette",
]
