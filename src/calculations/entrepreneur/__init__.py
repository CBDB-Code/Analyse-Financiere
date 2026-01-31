"""
Metriques financieres pour l'analyse entrepreneuriale.

Ce module expose les metriques utilisees par les entrepreneurs
et investisseurs pour evaluer le rendement de leurs investissements.
"""

from src.calculations.entrepreneur.equity_returns import ROE, PaybackPeriod

__all__ = ["ROE", "PaybackPeriod"]
