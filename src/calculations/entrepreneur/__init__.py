"""
Metriques financieres pour l'analyse entrepreneuriale.

Ce module expose les metriques utilisees par les entrepreneurs
et investisseurs pour evaluer le rendement de leurs investissements.
"""

from src.calculations.entrepreneur.equity_returns import ROE, PaybackPeriod
from src.calculations.entrepreneur.value_creation import (
    IRR,
    NPV,
    ExitMultiple,
    CashOnCashReturn,
    EquityMultiple,
    ValueCreation,
    CumulativeROI,
)

__all__ = [
    # Metriques de rendement
    "ROE",
    "PaybackPeriod",
    # Metriques de creation de valeur
    "IRR",
    "NPV",
    "ExitMultiple",
    "CashOnCashReturn",
    "EquityMultiple",
    "ValueCreation",
    "CumulativeROI",
]
