"""
Module de calculs financiers.

Ce module centralise toutes les metriques financieres et expose
le systeme de registre pour les gerer.

Sous-modules:
- banker: Metriques pour l'analyse banquier
- entrepreneur: Metriques pour l'analyse entrepreneur
- standard: Metriques standard (liquidite, profitabilite)
- trends: Analyse de tendances multi-exercices
"""

from src.calculations.base import (
    MetricCategory,
    MetricMetadata,
    FinancialMetric,
    MetricRegistry,
    register_metric,
)

# Import du module trends
from src.calculations.trends import (
    TrendAnalyzer,
    TrendResult,
    AnomalyResult,
    calculate_yoy_growth,
    calculate_volatility,
    detect_trend_direction,
    calculate_cagr,
    linear_regression,
    predict_value,
)

# Import des metriques pour les enregistrer automatiquement
from src.calculations.banker import (
    DSCR,
    ICR,
    NetDebtToEBITDA,
    Gearing,
    LTV,
    DebtCapacity,
    CurrentRatio,
    QuickRatio,
    FinancialAutonomy,
    DebtToAssets,
)
from src.calculations.entrepreneur import (
    ROE,
    PaybackPeriod,
    IRR,
    NPV,
    ExitMultiple,
    CashOnCashReturn,
    EquityMultiple,
    ValueCreation,
    CumulativeROI,
)
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
    # Module Trends - Analyse multi-exercices
    "TrendAnalyzer",
    "TrendResult",
    "AnomalyResult",
    "calculate_yoy_growth",
    "calculate_volatility",
    "detect_trend_direction",
    "calculate_cagr",
    "linear_regression",
    "predict_value",
    # Metriques Banquier - Couverture de dette
    "DSCR",
    "ICR",
    # Metriques Banquier - Levier et structure financiere
    "NetDebtToEBITDA",
    "Gearing",
    "LTV",
    "DebtCapacity",
    "CurrentRatio",
    "QuickRatio",
    "FinancialAutonomy",
    "DebtToAssets",
    # Metriques Entrepreneur - Rendement
    "ROE",
    "PaybackPeriod",
    # Metriques Entrepreneur - Creation de valeur
    "IRR",
    "NPV",
    "ExitMultiple",
    "CashOnCashReturn",
    "EquityMultiple",
    "ValueCreation",
    "CumulativeROI",
    # Metriques Liquidite
    "FondsDeRoulement",
    "BFR",
    # Metriques Rentabilite
    "EBITDA",
    "MargeBrute",
    "MargeExploitation",
    "MargeNette",
]
