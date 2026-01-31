"""
Module de calcul des tendances multi-exercices.

Ce module fournit des outils pour analyser les tendances financieres
sur plusieurs exercices fiscaux:
- TrendAnalyzer: Classe principale d'analyse
- Fonctions utilitaires pour les calculs de croissance et volatilite

Example:
    >>> from src.calculations.trends import TrendAnalyzer, calculate_yoy_growth
    >>> analyzer = TrendAnalyzer(fiscal_data)
    >>> cagr = analyzer.calculate_cagr("revenues")
    >>> growth = calculate_yoy_growth(120000, 100000)
"""

from typing import List, Optional, Tuple
import math

from src.calculations.trends.analyzer import (
    TrendAnalyzer,
    TrendResult,
    AnomalyResult,
)


def calculate_yoy_growth(current: float, previous: float) -> float:
    """
    Calcule la croissance annuelle (Year-over-Year).

    Args:
        current: Valeur de l'annee courante
        previous: Valeur de l'annee precedente

    Returns:
        Taux de croissance en decimale (0.20 = 20%)

    Example:
        >>> calculate_yoy_growth(120000, 100000)
        0.20  # 20% de croissance
    """
    if previous == 0:
        if current == 0:
            return 0.0
        return float('inf') if current > 0 else float('-inf')

    return (current - previous) / abs(previous)


def calculate_volatility(values: List[float]) -> float:
    """
    Calcule la volatilite (coefficient de variation).

    La volatilite est mesuree comme l'ecart-type divise par la moyenne,
    ce qui donne un indicateur sans unite de la dispersion relative.

    Args:
        values: Liste des valeurs

    Returns:
        Coefficient de variation (0.15 = 15% de volatilite)

    Example:
        >>> calculate_volatility([100, 110, 105, 115, 120])
        0.068  # Volatilite de ~6.8%
    """
    if not values or len(values) < 2:
        return 0.0

    # Filtrer les valeurs None
    valid_values = [v for v in values if v is not None]

    if len(valid_values) < 2:
        return 0.0

    mean = sum(valid_values) / len(valid_values)

    if mean == 0:
        return 0.0

    variance = sum((v - mean) ** 2 for v in valid_values) / len(valid_values)
    std_dev = math.sqrt(variance)

    return abs(std_dev / mean)


def detect_trend_direction(values: List[float]) -> str:
    """
    Detecte la direction de la tendance.

    Utilise une regression lineaire simple pour determiner
    si les valeurs suivent une tendance de croissance, stable ou decroissance.

    Args:
        values: Liste des valeurs chronologiques

    Returns:
        "croissance", "stable" ou "decroissance"

    Example:
        >>> detect_trend_direction([100, 110, 120, 130])
        "croissance"
        >>> detect_trend_direction([100, 100, 101, 99])
        "stable"
    """
    if len(values) < 2:
        return "stable"

    # Filtrer les valeurs None
    valid_values = [v for v in values if v is not None]

    if len(valid_values) < 2:
        return "stable"

    n = len(valid_values)
    x_mean = (n - 1) / 2
    y_mean = sum(valid_values) / n

    # Calcul de la pente
    numerator = sum((i - x_mean) * (valid_values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return "stable"

    slope = numerator / denominator

    # Normaliser par rapport a la moyenne pour avoir un seuil coherent
    if y_mean != 0:
        relative_slope = slope / abs(y_mean)
    else:
        relative_slope = slope

    # Seuils: croissance/decroissance si > 2% par periode
    if relative_slope > 0.02:
        return "croissance"
    elif relative_slope < -0.02:
        return "decroissance"
    else:
        return "stable"


def calculate_cagr(
    initial_value: float,
    final_value: float,
    n_years: int
) -> float:
    """
    Calcule le CAGR (Compound Annual Growth Rate).

    CAGR = (Valeur finale / Valeur initiale) ^ (1 / n) - 1

    Args:
        initial_value: Valeur de depart
        final_value: Valeur finale
        n_years: Nombre d'annees

    Returns:
        CAGR en decimale (0.10 = 10%)

    Example:
        >>> calculate_cagr(1000000, 1500000, 5)
        0.0845  # CAGR de ~8.45%
    """
    if n_years <= 0 or initial_value == 0:
        return 0.0

    if initial_value < 0 or final_value < 0:
        # Cas particulier: valeurs negatives
        if initial_value == 0:
            return 0.0
        return (final_value - initial_value) / abs(initial_value) / n_years

    try:
        return (final_value / initial_value) ** (1 / n_years) - 1
    except (ValueError, ZeroDivisionError):
        return 0.0


def linear_regression(values: List[float]) -> Tuple[float, float]:
    """
    Calcule les coefficients de regression lineaire.

    Retourne la pente (slope) et l'ordonnee a l'origine (intercept)
    pour la droite de regression y = ax + b.

    Args:
        values: Liste des valeurs chronologiques

    Returns:
        Tuple (slope, intercept)

    Example:
        >>> slope, intercept = linear_regression([100, 110, 120, 130])
        >>> slope
        10.0  # Croissance de 10 par periode
    """
    if len(values) < 2:
        return (0.0, values[0] if values else 0.0)

    # Filtrer les valeurs None
    valid_values = [v for v in values if v is not None]

    if len(valid_values) < 2:
        return (0.0, valid_values[0] if valid_values else 0.0)

    n = len(valid_values)
    x = list(range(n))

    x_mean = sum(x) / n
    y_mean = sum(valid_values) / n

    numerator = sum((x[i] - x_mean) * (valid_values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return (0.0, y_mean)

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    return (slope, intercept)


def predict_value(values: List[float], periods_ahead: int = 1) -> Optional[float]:
    """
    Predit une valeur future par regression lineaire.

    Args:
        values: Liste des valeurs historiques
        periods_ahead: Nombre de periodes a predire (defaut: 1)

    Returns:
        Valeur predite ou None

    Example:
        >>> predict_value([100, 110, 120, 130], periods_ahead=1)
        140.0  # Prediction pour la prochaine periode
    """
    if len(values) < 2:
        return None

    slope, intercept = linear_regression(values)

    # Prochaine valeur = derniere position + periodes
    next_x = len(values) - 1 + periods_ahead

    return slope * next_x + intercept


def calculate_moving_average(
    values: List[float],
    window: int = 3
) -> List[Optional[float]]:
    """
    Calcule la moyenne mobile.

    Args:
        values: Liste des valeurs
        window: Taille de la fenetre (defaut: 3)

    Returns:
        Liste des moyennes mobiles (None pour les premieres valeurs)

    Example:
        >>> calculate_moving_average([100, 110, 120, 130, 140], window=3)
        [None, None, 110.0, 120.0, 130.0]
    """
    if not values or window < 1:
        return []

    result: List[Optional[float]] = []

    for i in range(len(values)):
        if i < window - 1:
            result.append(None)
        else:
            window_values = values[i - window + 1:i + 1]
            valid = [v for v in window_values if v is not None]
            if valid:
                result.append(sum(valid) / len(valid))
            else:
                result.append(None)

    return result


def format_trend_label(trend: str) -> str:
    """
    Formate le label de tendance pour l'affichage.

    Args:
        trend: Direction de la tendance

    Returns:
        Label formate avec emoji

    Example:
        >>> format_trend_label("croissance")
        "Croissance"
    """
    labels = {
        "croissance": "Croissance",
        "stable": "Stable",
        "decroissance": "Decroissance"
    }
    return labels.get(trend.lower(), trend.capitalize())


def get_trend_color(trend: str) -> str:
    """
    Retourne la couleur associee a une tendance.

    Args:
        trend: Direction de la tendance

    Returns:
        Code couleur CSS

    Example:
        >>> get_trend_color("croissance")
        "#2ca02c"  # Vert
    """
    colors = {
        "croissance": "#2ca02c",  # Vert
        "stable": "#ff7f0e",      # Orange
        "decroissance": "#d62728" # Rouge
    }
    return colors.get(trend.lower(), "#7f7f7f")


# Exports du module
__all__ = [
    # Classes principales
    "TrendAnalyzer",
    "TrendResult",
    "AnomalyResult",
    # Fonctions utilitaires
    "calculate_yoy_growth",
    "calculate_volatility",
    "detect_trend_direction",
    "calculate_cagr",
    "linear_regression",
    "predict_value",
    "calculate_moving_average",
    "format_trend_label",
    "get_trend_color",
]
