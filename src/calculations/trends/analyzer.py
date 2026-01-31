"""
Analyseur de tendances multi-exercices pour l'analyse financiere.

Ce module fournit la classe TrendAnalyzer qui permet d'analyser
les tendances sur plusieurs exercices fiscaux:
- Calcul du CAGR (Compound Annual Growth Rate)
- Evolution des metriques avec volatilite
- Detection d'anomalies
- Predictions par regression lineaire

Example:
    >>> fiscal_data = [
    ...     {"year": 2021, "revenues": 1000000, "ebitda": 200000},
    ...     {"year": 2022, "revenues": 1200000, "ebitda": 250000},
    ...     {"year": 2023, "revenues": 1500000, "ebitda": 320000}
    ... ]
    >>> analyzer = TrendAnalyzer(fiscal_data)
    >>> cagr = analyzer.calculate_cagr("revenues")
    >>> print(f"CAGR CA: {cagr:.1%}")
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import json
from datetime import date


@dataclass
class TrendResult:
    """Resultat d'une analyse de tendance pour une metrique."""
    years: List[int]
    values: List[float]
    cagr: float
    volatility: float
    trend: str
    yoy_changes: List[float]

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            "years": self.years,
            "values": self.values,
            "cagr": self.cagr,
            "volatility": self.volatility,
            "trend": self.trend,
            "yoy_changes": self.yoy_changes
        }


@dataclass
class AnomalyResult:
    """Resultat de detection d'anomalie."""
    year: int
    variation: float
    message: str
    severity: str  # "warning", "critical"

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            "year": self.year,
            "variation": self.variation,
            "message": self.message,
            "severity": self.severity
        }


class TrendAnalyzer:
    """
    Analyseur de tendances multi-exercices.

    Cette classe analyse les donnees financieres sur plusieurs exercices
    pour identifier les tendances, calculer les taux de croissance composes
    et detecter les anomalies.

    Attributes:
        fiscal_years_data: Liste des donnees fiscales triees chronologiquement
        n_years: Nombre d'annees dans l'analyse

    Example:
        >>> analyzer = TrendAnalyzer(fiscal_data_list)
        >>> trends = analyzer.get_all_trends()
        >>> anomalies = analyzer.detect_anomalies("revenues", threshold=0.3)
    """

    # Metriques principales a analyser
    MAIN_METRICS = [
        "revenues",
        "ebitda",
        "net_income",
        "total_assets",
        "equity",
        "total_debt",
        "operating_cash_flow",
        "ebitda_margin",
        "net_margin",
        "roe",
        "debt_to_equity",
        "current_ratio"
    ]

    # Labels francais pour les metriques
    METRIC_LABELS = {
        "revenues": "Chiffre d'affaires",
        "ebitda": "EBITDA",
        "net_income": "Resultat net",
        "total_assets": "Total actif",
        "equity": "Capitaux propres",
        "total_debt": "Dette totale",
        "operating_cash_flow": "Cash-flow operationnel",
        "ebitda_margin": "Marge EBITDA",
        "net_margin": "Marge nette",
        "roe": "ROE",
        "debt_to_equity": "Dette/Capitaux propres",
        "current_ratio": "Ratio de liquidite"
    }

    def __init__(self, fiscal_years_data: List[Dict[str, Any]]):
        """
        Initialise l'analyseur avec les donnees de plusieurs exercices.

        Args:
            fiscal_years_data: Liste de dictionnaires contenant les donnees
                fiscales de chaque exercice. Chaque dict doit avoir une cle
                "year" ou "year_end" pour identifier l'annee.

        Raises:
            ValueError: Si moins de 2 exercices sont fournis
        """
        if not fiscal_years_data:
            raise ValueError("Aucune donnee fiscale fournie")

        if len(fiscal_years_data) < 2:
            raise ValueError(
                "Au moins 2 exercices sont necessaires pour l'analyse de tendances. "
                f"Fourni: {len(fiscal_years_data)} exercice(s)"
            )

        # Normaliser et trier les donnees
        self.fiscal_years_data = self._normalize_and_sort(fiscal_years_data)
        self.n_years = len(self.fiscal_years_data)

        # Cache pour les metriques extraites
        self._metrics_cache: Dict[str, List[float]] = {}

    def _normalize_and_sort(
        self,
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Normalise et trie les donnees par annee (ordre chronologique).

        Args:
            data: Donnees fiscales non triees

        Returns:
            Liste triee par annee croissante
        """
        normalized = []

        for item in data:
            # Copier les donnees
            entry = dict(item)

            # Extraire l'annee depuis differents formats
            if "year" in entry:
                year = entry["year"]
            elif "year_end" in entry:
                year_end = entry["year_end"]
                if isinstance(year_end, date):
                    year = year_end.year
                elif isinstance(year_end, str):
                    # Format ISO: "2023-12-31"
                    year = int(year_end[:4])
                else:
                    year = int(year_end)
            else:
                raise ValueError(
                    "Chaque exercice doit avoir une cle 'year' ou 'year_end'"
                )

            entry["year"] = int(year)
            normalized.append(entry)

        # Trier par annee croissante
        return sorted(normalized, key=lambda x: x["year"])

    def _extract_metric_values(self, metric_name: str) -> List[float]:
        """
        Extrait les valeurs d'une metrique pour tous les exercices.

        Args:
            metric_name: Nom de la metrique a extraire

        Returns:
            Liste des valeurs pour chaque annee
        """
        if metric_name in self._metrics_cache:
            return self._metrics_cache[metric_name]

        values = []

        for fiscal_year in self.fiscal_years_data:
            value = self._get_nested_value(fiscal_year, metric_name)
            values.append(value if value is not None else 0.0)

        self._metrics_cache[metric_name] = values
        return values

    def _get_nested_value(
        self,
        data: Dict[str, Any],
        key: str
    ) -> Optional[float]:
        """
        Recupere une valeur potentiellement imbriquee dans un dict.

        Cherche dans l'ordre:
        1. Cle directe
        2. Cle imbriquee (ex: "income_statement.revenues.net_revenue")
        3. Structures connues de la liasse fiscale

        Args:
            data: Dictionnaire de donnees
            key: Cle ou chemin vers la valeur

        Returns:
            Valeur numerique ou None si non trouve
        """
        # 1. Recherche directe
        if key in data:
            return self._to_float(data[key])

        # 2. Recherche imbriquee avec points
        if "." in key:
            parts = key.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    current = None
                    break
            if current is not None:
                return self._to_float(current)

        # 3. Recherche dans les structures connues
        return self._search_in_known_structures(data, key)

    def _search_in_known_structures(
        self,
        data: Dict[str, Any],
        key: str
    ) -> Optional[float]:
        """
        Cherche une metrique dans les structures connues de liasse fiscale.

        Args:
            data: Donnees fiscales
            key: Nom de la metrique

        Returns:
            Valeur ou None
        """
        # Mapping des metriques vers les chemins possibles
        known_paths = {
            "revenues": [
                "income_statement.revenues.net_revenue",
                "revenues.total.value",
                "income_statement.revenues.total",
                "chiffre_affaires",
                "ca"
            ],
            "ebitda": [
                "profitability.ebitda.value",
                "ebitda",
                "excedent_brut_exploitation"
            ],
            "net_income": [
                "income_statement.net_income",
                "resultat_net",
                "net_income"
            ],
            "total_assets": [
                "balance_sheet.assets.total_assets",
                "total_actif",
                "total_assets"
            ],
            "equity": [
                "balance_sheet.liabilities.equity.total",
                "capitaux_propres",
                "equity"
            ],
            "total_debt": [
                "balance_sheet.liabilities.debt.total_financial_debt",
                "dette_financiere",
                "total_debt"
            ],
            "operating_cash_flow": [
                "cash_flow.operating.total",
                "cash_flow_operationnel",
                "operating_cash_flow"
            ],
            "ebitda_margin": [
                "ratios.ebitda_margin",
                "marge_ebitda",
                "ebitda_margin"
            ],
            "net_margin": [
                "ratios.net_margin",
                "marge_nette",
                "net_margin"
            ],
            "roe": [
                "ratios.roe",
                "rentabilite_capitaux_propres",
                "roe"
            ],
            "debt_to_equity": [
                "ratios.debt_to_equity",
                "dette_sur_capitaux",
                "debt_to_equity"
            ],
            "current_ratio": [
                "ratios.current_ratio",
                "ratio_liquidite",
                "current_ratio"
            ]
        }

        paths = known_paths.get(key, [])

        for path in paths:
            value = self._get_by_path(data, path)
            if value is not None:
                return self._to_float(value)

        return None

    def _get_by_path(
        self,
        data: Dict[str, Any],
        path: str
    ) -> Optional[Any]:
        """
        Recupere une valeur par chemin de type 'a.b.c'.

        Args:
            data: Dictionnaire source
            path: Chemin separe par des points

        Returns:
            Valeur ou None
        """
        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _to_float(self, value: Any) -> Optional[float]:
        """
        Convertit une valeur en float.

        Args:
            value: Valeur a convertir

        Returns:
            Float ou None si conversion impossible
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, dict):
            # Cas ou la valeur est un dict avec cle "value"
            if "value" in value:
                return self._to_float(value["value"])
            return None

        if isinstance(value, str):
            try:
                # Nettoyer les espaces et remplacer virgule par point
                clean = value.replace(" ", "").replace(",", ".")
                return float(clean)
            except ValueError:
                return None

        return None

    def get_years(self) -> List[int]:
        """
        Retourne la liste des annees analysees.

        Returns:
            Liste des annees dans l'ordre chronologique
        """
        return [fy["year"] for fy in self.fiscal_years_data]

    def calculate_cagr(self, metric_name: str) -> float:
        """
        Calcule le CAGR (Compound Annual Growth Rate) pour une metrique.

        Le CAGR represente le taux de croissance annuel compose:
        CAGR = (Valeur finale / Valeur initiale) ^ (1 / nb annees) - 1

        Args:
            metric_name: Nom de la metrique

        Returns:
            CAGR en decimale (ex: 0.15 pour 15%)

        Example:
            >>> cagr = analyzer.calculate_cagr("revenues")
            >>> print(f"CAGR: {cagr:.1%}")  # "CAGR: 22.5%"
        """
        values = self._extract_metric_values(metric_name)

        if not values or len(values) < 2:
            return 0.0

        initial_value = values[0]
        final_value = values[-1]

        # Eviter division par zero
        if initial_value == 0 or initial_value is None:
            return 0.0

        # Eviter valeurs negatives pour le calcul de racine
        if initial_value < 0 or final_value < 0:
            # Utiliser la formule alternative pour valeurs negatives
            return self._calculate_average_growth(values)

        n_years = len(values) - 1

        if n_years == 0:
            return 0.0

        # CAGR = (Final / Initial) ^ (1/n) - 1
        try:
            cagr = (final_value / initial_value) ** (1 / n_years) - 1
            return cagr
        except (ValueError, ZeroDivisionError):
            return 0.0

    def _calculate_average_growth(self, values: List[float]) -> float:
        """
        Calcule la croissance moyenne (alternative au CAGR pour valeurs negatives).

        Args:
            values: Liste des valeurs

        Returns:
            Taux de croissance moyen
        """
        if len(values) < 2:
            return 0.0

        growths = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                growth = (values[i] - values[i-1]) / abs(values[i-1])
                growths.append(growth)

        if not growths:
            return 0.0

        return sum(growths) / len(growths)

    def get_metric_evolution(self, metric_name: str) -> Dict[str, Any]:
        """
        Retourne l'evolution complete d'une metrique.

        Calcule:
        - Les valeurs annuelles
        - Le CAGR
        - La volatilite
        - La tendance (croissance, stable, decroissance)
        - Les variations annuelles

        Args:
            metric_name: Nom de la metrique

        Returns:
            Dictionnaire avec l'evolution complete

        Example:
            >>> evolution = analyzer.get_metric_evolution("revenues")
            >>> {
            ...     "years": [2021, 2022, 2023],
            ...     "values": [1000000, 1200000, 1500000],
            ...     "cagr": 0.225,
            ...     "volatility": 0.15,
            ...     "trend": "croissance",
            ...     "yoy_changes": [None, 0.20, 0.25]
            ... }
        """
        years = self.get_years()
        values = self._extract_metric_values(metric_name)

        # Calculer les variations YoY
        yoy_changes = self._calculate_yoy_changes(values)

        # Calculer le CAGR
        cagr = self.calculate_cagr(metric_name)

        # Calculer la volatilite
        volatility = self._calculate_volatility(values)

        # Determiner la tendance
        trend = self._detect_trend_direction(values)

        result = TrendResult(
            years=years,
            values=values,
            cagr=cagr,
            volatility=volatility,
            trend=trend,
            yoy_changes=yoy_changes
        )

        return result.to_dict()

    def _calculate_yoy_changes(self, values: List[float]) -> List[Optional[float]]:
        """
        Calcule les variations annuelles (Year-over-Year).

        Args:
            values: Liste des valeurs

        Returns:
            Liste des variations (None pour la premiere annee)
        """
        if len(values) < 2:
            return [None] * len(values)

        changes: List[Optional[float]] = [None]  # Premiere annee = pas de variation

        for i in range(1, len(values)):
            if values[i-1] != 0:
                change = (values[i] - values[i-1]) / abs(values[i-1])
            else:
                change = 0.0 if values[i] == 0 else float('inf')
            changes.append(change)

        return changes

    def _calculate_volatility(self, values: List[float]) -> float:
        """
        Calcule la volatilite (ecart-type / moyenne).

        Args:
            values: Liste des valeurs

        Returns:
            Coefficient de variation
        """
        if not values or len(values) < 2:
            return 0.0

        # Filtrer les valeurs None et zeros
        valid_values = [v for v in values if v is not None and v != 0]

        if len(valid_values) < 2:
            return 0.0

        # Calcul manuel de moyenne et ecart-type
        mean = sum(valid_values) / len(valid_values)

        if mean == 0:
            return 0.0

        variance = sum((v - mean) ** 2 for v in valid_values) / len(valid_values)
        std_dev = variance ** 0.5

        return abs(std_dev / mean)

    def _detect_trend_direction(self, values: List[float]) -> str:
        """
        Detecte la direction de la tendance.

        Utilise une regression lineaire simple pour determiner
        si la tendance est a la croissance, stable ou en decroissance.

        Args:
            values: Liste des valeurs

        Returns:
            "croissance", "stable" ou "decroissance"
        """
        if len(values) < 2:
            return "stable"

        # Calcul de la pente par regression lineaire simple
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n

        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        # Normaliser la pente par rapport a la moyenne
        if y_mean != 0:
            relative_slope = slope / abs(y_mean)
        else:
            relative_slope = slope

        # Seuils pour determiner la tendance
        if relative_slope > 0.02:  # Croissance > 2% par an
            return "croissance"
        elif relative_slope < -0.02:  # Decroissance > 2% par an
            return "decroissance"
        else:
            return "stable"

    def detect_anomalies(
        self,
        metric_name: str,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Detecte les anomalies dans l'evolution d'une metrique.

        Une anomalie est une variation annuelle superieure au seuil defini.

        Args:
            metric_name: Nom de la metrique
            threshold: Seuil de variation (0.3 = 30%)

        Returns:
            Liste des anomalies detectees

        Example:
            >>> anomalies = analyzer.detect_anomalies("revenues", threshold=0.3)
            >>> [{"year": 2022, "variation": 0.45, "message": "Hausse anormale de 45%"}]
        """
        values = self._extract_metric_values(metric_name)
        years = self.get_years()

        anomalies: List[Dict[str, Any]] = []

        for i in range(1, len(values)):
            if values[i-1] == 0:
                continue

            variation = (values[i] - values[i-1]) / abs(values[i-1])

            if abs(variation) > threshold:
                # Determiner le type et la severite
                if variation > 0:
                    direction = "Hausse"
                    severity = "warning" if variation < 0.5 else "critical"
                else:
                    direction = "Baisse"
                    severity = "warning" if abs(variation) < 0.5 else "critical"

                metric_label = self.METRIC_LABELS.get(metric_name, metric_name)

                anomaly = AnomalyResult(
                    year=years[i],
                    variation=variation,
                    message=f"{direction} anormale de {abs(variation):.0%} sur {metric_label}",
                    severity=severity
                )
                anomalies.append(anomaly.to_dict())

        return anomalies

    def get_all_trends(self) -> Dict[str, Dict[str, Any]]:
        """
        Retourne les tendances pour toutes les metriques principales.

        Returns:
            Dictionnaire avec les tendances de chaque metrique

        Example:
            >>> trends = analyzer.get_all_trends()
            >>> {
            ...     "revenues": {"cagr": 0.10, "trend": "croissance", ...},
            ...     "ebitda": {"cagr": 0.15, "trend": "croissance", ...},
            ...     "net_income": {"cagr": -0.05, "trend": "decroissance", ...}
            ... }
        """
        trends = {}

        for metric_name in self.MAIN_METRICS:
            try:
                evolution = self.get_metric_evolution(metric_name)
                # Verifier si des valeurs existent
                if any(v != 0 for v in evolution["values"]):
                    trends[metric_name] = evolution
            except Exception:
                # Ignorer les metriques non disponibles
                continue

        return trends

    def get_all_anomalies(self, threshold: float = 0.3) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detecte les anomalies pour toutes les metriques.

        Args:
            threshold: Seuil de variation

        Returns:
            Dictionnaire des anomalies par metrique
        """
        all_anomalies = {}

        for metric_name in self.MAIN_METRICS:
            try:
                anomalies = self.detect_anomalies(metric_name, threshold)
                if anomalies:
                    all_anomalies[metric_name] = anomalies
            except Exception:
                continue

        return all_anomalies

    def predict_next_year(self, metric_name: str) -> Optional[float]:
        """
        Predit la valeur pour l'annee suivante par regression lineaire.

        Utilise une regression lineaire simple (moindres carres) pour
        projeter la valeur de la metrique pour l'annee N+1.

        Args:
            metric_name: Nom de la metrique

        Returns:
            Valeur predite ou None si prediction impossible

        Example:
            >>> prediction = analyzer.predict_next_year("revenues")
            >>> print(f"CA prevu N+1: {prediction:,.0f} EUR")
        """
        values = self._extract_metric_values(metric_name)

        if len(values) < 2:
            return None

        # Regression lineaire simple: y = ax + b
        n = len(values)
        x = list(range(n))  # 0, 1, 2, ...

        # Calcul des moyennes
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        # Calcul de la pente (a) et de l'ordonnee a l'origine (b)
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            # Valeurs constantes - retourner la moyenne
            return y_mean

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Prediction pour x = n (annee suivante)
        prediction = slope * n + intercept

        return prediction

    def predict_all_metrics(self) -> Dict[str, Optional[float]]:
        """
        Predit les valeurs N+1 pour toutes les metriques disponibles.

        Returns:
            Dictionnaire des predictions par metrique
        """
        predictions = {}

        for metric_name in self.MAIN_METRICS:
            try:
                pred = self.predict_next_year(metric_name)
                if pred is not None:
                    predictions[metric_name] = pred
            except Exception:
                continue

        return predictions

    def get_summary(self) -> Dict[str, Any]:
        """
        Retourne un resume de l'analyse de tendances.

        Returns:
            Dictionnaire avec le resume global
        """
        trends = self.get_all_trends()
        anomalies = self.get_all_anomalies()
        predictions = self.predict_all_metrics()

        # Compter les tendances
        trend_counts = {"croissance": 0, "stable": 0, "decroissance": 0}
        for trend_data in trends.values():
            trend = trend_data.get("trend", "stable")
            trend_counts[trend] = trend_counts.get(trend, 0) + 1

        # Compter les anomalies par severite
        anomaly_counts = {"warning": 0, "critical": 0}
        for metric_anomalies in anomalies.values():
            for anomaly in metric_anomalies:
                severity = anomaly.get("severity", "warning")
                anomaly_counts[severity] = anomaly_counts.get(severity, 0) + 1

        return {
            "years_analyzed": self.get_years(),
            "n_years": self.n_years,
            "metrics_analyzed": list(trends.keys()),
            "n_metrics": len(trends),
            "trend_summary": trend_counts,
            "anomaly_summary": anomaly_counts,
            "total_anomalies": sum(len(a) for a in anomalies.values()),
            "predictions_available": list(predictions.keys())
        }


# Pour faciliter l'import
__all__ = [
    "TrendAnalyzer",
    "TrendResult",
    "AnomalyResult"
]
