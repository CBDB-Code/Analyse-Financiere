"""
Module de calculs financiers.

Ce module centralise toutes les metriques financieres et expose
le systeme de registre pour les gerer.
"""

from src.calculations.base import (
    MetricCategory,
    MetricMetadata,
    FinancialMetric,
    MetricRegistry,
    register_metric,
)

# Import des metriques pour les enregistrer automatiquement
from src.calculations.banker import DSCR, ICR
from src.calculations.entrepreneur import ROE, PaybackPeriod
from src.calculations.standard import (
    FondsDeRoulement,
    BFR,
    EBITDA,
    MargeBrute,
    MargeExploitation,
    MargeNette,
)

__all__ = [
    # Base classes et utilities
    "MetricCategory",
    "MetricMetadata",
    "FinancialMetric",
    "MetricRegistry",
    "register_metric",
    # Metriques Banquier
    "DSCR",
    "ICR",
    # Metriques Entrepreneur
    "ROE",
    "PaybackPeriod",
    # Metriques Liquidite
    "FondsDeRoulement",
    "BFR",
    # Metriques Rentabilite
    "EBITDA",
    "MargeBrute",
    "MargeExploitation",
    "MargeNette",
]
