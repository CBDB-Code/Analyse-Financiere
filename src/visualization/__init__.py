"""
Module de visualisation pour l'analyse financiere.

Ce module fournit:
- ChartFactory: Fabrique de graphiques Plotly interactifs
- BankerDashboard: Dashboard perspective banquier
- EntrepreneurDashboard: Dashboard perspective entrepreneur
- CompleteDashboard: Dashboard combine

Types de graphiques disponibles:
- Gauge charts pour les KPIs
- Waterfall charts pour la decomposition
- Barres groupees pour la comparaison de scenarios
- Lignes pour l'analyse de sensibilite
- Radar charts pour la comparaison 360
- Evolution temporelle multi-metriques

Example:
    >>> from src.visualization import ChartFactory, BankerDashboard
    >>>
    >>> # Creer un graphique
    >>> factory = ChartFactory()
    >>> fig = factory.create_metrics_gauge(
    ...     metrics={"DSCR": 1.45, "ICR": 3.2},
    ...     category="banker"
    ... )
    >>>
    >>> # Ou utiliser un dashboard complet
    >>> dashboard = BankerDashboard()
    >>> dashboard.render(scenario_data, metrics_results)
"""

from .charts import (
    ChartFactory,
    ColorPalette,
    chart_factory,
    create_kpi_card_figure,
)

from .dashboards import (
    BankerDashboard,
    EntrepreneurDashboard,
    CompleteDashboard,
    format_currency,
    format_percentage,
    format_ratio,
)


__all__ = [
    # Classes principales
    "ChartFactory",
    "ColorPalette",
    "BankerDashboard",
    "EntrepreneurDashboard",
    "CompleteDashboard",

    # Instances globales
    "chart_factory",

    # Fonctions utilitaires
    "create_kpi_card_figure",
    "format_currency",
    "format_percentage",
    "format_ratio",
]
