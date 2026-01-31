"""
Utilitaires de formatage pour l'affichage.

Gère le formatage des nombres avec espaces insécables
pour améliorer la lisibilité.
"""

from typing import Optional


def format_number(
    value: Optional[float],
    decimals: int = 0,
    unit: str = "€",
    show_unit: bool = True
) -> str:
    """
    Formate un nombre avec espaces insécables tous les 3 chiffres.

    Exemples:
        1200000 → "1 200 000 €"
        1234.56 → "1 234.56 €"
        -500000 → "-500 000 €"

    Args:
        value: Valeur à formater (None → "N/A")
        decimals: Nombre de décimales (0 par défaut)
        unit: Unité à afficher ("€", "k€", "M€")
        show_unit: Afficher l'unité ou non

    Returns:
        str: Nombre formaté avec espaces
    """
    if value is None:
        return "N/A"

    if value == float("inf"):
        return "∞"

    if value == float("-inf"):
        return "-∞"

    # Formatage avec virgule comme séparateur de milliers
    if decimals == 0:
        formatted = f"{value:,.0f}"
    else:
        formatted = f"{value:,.{decimals}f}"

    # Remplacement virgule par espace insécable (U+00A0)
    formatted = formatted.replace(",", "\u00A0")

    # Ajout unité
    if show_unit and unit:
        formatted = f"{formatted} {unit}"

    return formatted


def format_percentage(
    value: Optional[float],
    decimals: int = 1,
    as_decimal: bool = False
) -> str:
    """
    Formate un pourcentage.

    Args:
        value: Valeur à formater (0.05 ou 5 selon as_decimal)
        decimals: Nombre de décimales
        as_decimal: Si True, value est déjà en décimal (0.05 = 5%)

    Returns:
        str: Pourcentage formaté (ex: "5.0 %")
    """
    if value is None:
        return "N/A"

    if value == float("inf") or value == float("-inf"):
        return "∞ %"

    # Conversion si nécessaire
    pct_value = value * 100 if as_decimal else value

    return f"{pct_value:.{decimals}f} %"


def format_ratio(value: Optional[float], decimals: int = 2) -> str:
    """
    Formate un ratio (sans unité).

    Args:
        value: Valeur du ratio
        decimals: Nombre de décimales

    Returns:
        str: Ratio formaté (ex: "1.25")
    """
    if value is None:
        return "N/A"

    if value == float("inf"):
        return "∞"

    if value == float("-inf"):
        return "-∞"

    return f"{value:.{decimals}f}"


def format_currency_compact(value: Optional[float]) -> str:
    """
    Formate une valeur monétaire en notation compacte.

    Exemples:
        1_200_000 → "1.2 M€"
        850_000 → "850 k€"
        1_500 → "1 500 €"

    Args:
        value: Valeur en euros

    Returns:
        str: Valeur formatée compacte
    """
    if value is None:
        return "N/A"

    if value == float("inf") or value == float("-inf"):
        return "∞"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000:
        # Millions
        return f"{sign}{abs_value / 1_000_000:.1f} M€"
    elif abs_value >= 1_000:
        # Milliers
        return f"{sign}{abs_value / 1_000:.0f} k€"
    else:
        # Unités
        return format_number(value, decimals=0, unit="€")


def format_years(value: Optional[float], short: bool = False) -> str:
    """
    Formate une durée en années.

    Args:
        value: Nombre d'années
        short: Si True, format court ("ans" au lieu de "années")

    Returns:
        str: Durée formatée (ex: "5 ans" ou "5.2 années")
    """
    if value is None:
        return "N/A"

    if value == float("inf"):
        return "∞"

    unit = "ans" if short else "années"

    if value == int(value):
        return f"{int(value)} {unit}"
    else:
        return f"{value:.1f} {unit}"


def format_multiple(value: Optional[float]) -> str:
    """
    Formate un multiple (ex: 4.5x).

    Args:
        value: Valeur du multiple

    Returns:
        str: Multiple formaté (ex: "4.5x")
    """
    if value is None:
        return "N/A"

    if value == float("inf"):
        return "∞x"

    return f"{value:.1f}x"


# Tests
if __name__ == "__main__":
    print("Tests formatage:")
    print(f"1200000 → {format_number(1200000)}")
    print(f"1234.56 → {format_number(1234.56, decimals=2)}")
    print(f"0.05 (decimal) → {format_percentage(0.05, as_decimal=True)}")
    print(f"5 (pct) → {format_percentage(5)}")
    print(f"1.25 (ratio) → {format_ratio(1.25)}")
    print(f"1200000 (compact) → {format_currency_compact(1200000)}")
    print(f"850000 (compact) → {format_currency_compact(850000)}")
    print(f"5 (years) → {format_years(5, short=True)}")
    print(f"4.5 (multiple) → {format_multiple(4.5)}")
