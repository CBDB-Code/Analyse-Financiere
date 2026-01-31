"""
Base module for financial metrics registry system.

This module provides the foundational infrastructure for defining, registering,
and managing financial metrics used in financial analysis. It includes:
- MetricCategory enum for categorizing metrics
- MetricMetadata dataclass for storing metric documentation
- FinancialMetric abstract base class for metric implementations
- MetricRegistry singleton for centralized metric management
- register_metric decorator for automatic registration

Example usage:
    @register_metric
    class CurrentRatio(FinancialMetric):
        metadata = MetricMetadata(
            name="current_ratio",
            formula_latex=r"\\frac{Actifs Circulants}{Passifs Circulants}",
            description="Ratio de liquidité générale",
            unit="ratio",
            category=MetricCategory.LIQUIDITY,
            source_fields=["actifs_circulants", "passifs_circulants"],
            interpretation="Un ratio > 1 indique une bonne liquidité",
            benchmark_ranges={"excellent": 2.0, "good": 1.5, "acceptable": 1.0, "risky": 0.8}
        )

        def calculate(self, financial_data: dict) -> float:
            return financial_data["actifs_circulants"] / financial_data["passifs_circulants"]
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Type


class MetricCategory(Enum):
    """
    Categories for classifying financial metrics.

    Each category represents a different aspect of financial analysis,
    allowing metrics to be grouped and filtered based on their purpose.

    Attributes:
        BANKER: Metrics typically used by bankers for credit analysis
        ENTREPRENEUR: Metrics useful for business owners and managers
        LIQUIDITY: Metrics measuring short-term financial health
        PROFITABILITY: Metrics measuring profit generation ability
        ACTIVITY: Metrics measuring operational efficiency
        SOLVENCY: Metrics measuring long-term financial stability
    """
    BANKER = "banker"
    ENTREPRENEUR = "entrepreneur"
    LIQUIDITY = "liquidity"
    PROFITABILITY = "profitability"
    ACTIVITY = "activity"
    SOLVENCY = "solvency"


@dataclass
class MetricMetadata:
    """
    Metadata container for financial metric documentation and configuration.

    This dataclass stores all descriptive and configuration information
    about a financial metric, including its formula, interpretation guidelines,
    and benchmark values.

    Attributes:
        name: Unique identifier for the metric (snake_case)
        formula_latex: LaTeX representation of the calculation formula
        description: Detailed description of what the metric measures
        unit: Unit of measurement (%, euro, ratio, jours, etc.)
        category: MetricCategory classification
        source_fields: List of JSON field names required for calculation
        interpretation: Guidelines for interpreting the calculated value
        benchmark_ranges: Optional dict with threshold values for rating
            Keys should be: "excellent", "good", "acceptable", "risky"
            Values represent the minimum threshold for each rating

    Example:
        MetricMetadata(
            name="marge_brute",
            formula_latex=r"\\frac{Marge Brute}{Chiffre d'Affaires} \\times 100",
            description="Pourcentage de marge brute par rapport au CA",
            unit="%",
            category=MetricCategory.PROFITABILITY,
            source_fields=["marge_brute", "chiffre_affaires"],
            interpretation="Plus le ratio est élevé, meilleure est la rentabilité",
            benchmark_ranges={"excellent": 40.0, "good": 30.0, "acceptable": 20.0, "risky": 10.0}
        )
    """
    name: str
    formula_latex: str
    description: str
    unit: str
    category: MetricCategory
    source_fields: List[str] = field(default_factory=list)
    interpretation: str = ""
    benchmark_ranges: Optional[Dict[str, float]] = None

    def __post_init__(self) -> None:
        """Validate metadata after initialization."""
        if not self.name:
            raise ValueError("Le nom de la métrique ne peut pas être vide")
        if not self.formula_latex:
            raise ValueError("La formule LaTeX ne peut pas être vide")
        if not self.description:
            raise ValueError("La description ne peut pas être vide")
        if not self.unit:
            raise ValueError("L'unité ne peut pas être vide")


class FinancialMetric(ABC):
    """
    Abstract base class for all financial metrics.

    This class provides the interface and common functionality for financial
    metric implementations. Subclasses must define the `metadata` property
    and implement the `calculate` method.

    The class provides utility methods for input validation, value interpretation,
    and formatting based on the metric's unit type.

    Attributes:
        metadata: MetricMetadata instance describing the metric

    Example:
        class TauxMargeBrute(FinancialMetric):
            metadata = MetricMetadata(
                name="taux_marge_brute",
                formula_latex=r"\\frac{Marge Brute}{CA} \\times 100",
                description="Taux de marge brute",
                unit="%",
                category=MetricCategory.PROFITABILITY,
                source_fields=["marge_brute", "chiffre_affaires"],
                interpretation="Mesure l'efficacité de la production"
            )

            def calculate(self, financial_data: dict) -> float:
                ca = financial_data.get("chiffre_affaires", 0)
                if ca == 0:
                    return 0.0
                return (financial_data["marge_brute"] / ca) * 100
    """

    @property
    @abstractmethod
    def metadata(self) -> MetricMetadata:
        """
        Return the metadata describing this metric.

        This property must be implemented by all subclasses to provide
        the metric's documentation and configuration.

        Returns:
            MetricMetadata: The metadata for this metric
        """
        pass

    @abstractmethod
    def calculate(self, financial_data: dict) -> float:
        """
        Calculate the metric value from financial data.

        This method must be implemented by all subclasses to perform
        the actual metric calculation.

        Args:
            financial_data: Dictionary containing the financial data
                with keys matching the source_fields in metadata

        Returns:
            float: The calculated metric value

        Raises:
            KeyError: If required fields are missing from financial_data
            ZeroDivisionError: If division by zero would occur
            ValueError: If data values are invalid
        """
        pass

    def validate_inputs(self, financial_data: dict) -> bool:
        """
        Validate that all required input fields are present and valid.

        Checks that all fields specified in metadata.source_fields
        exist in the financial_data dictionary and contain numeric values.

        Args:
            financial_data: Dictionary containing the financial data

        Returns:
            bool: True if all required fields are present and valid,
                False otherwise

        Example:
            >>> metric = SomeMetric()
            >>> data = {"chiffre_affaires": 100000, "marge_brute": 30000}
            >>> metric.validate_inputs(data)
            True
        """
        if not financial_data:
            return False

        for field_name in self.metadata.source_fields:
            if field_name not in financial_data:
                return False

            value = financial_data[field_name]
            if value is None:
                return False

            # Check if value is numeric
            if not isinstance(value, (int, float)):
                try:
                    float(value)
                except (TypeError, ValueError):
                    return False

        return True

    def get_interpretation(self, value: float) -> str:
        """
        Get an interpretation of the calculated value based on benchmarks.

        Uses the benchmark_ranges from metadata to classify the value
        and returns an appropriate interpretation string.

        Args:
            value: The calculated metric value

        Returns:
            str: Interpretation of the value, including rating if benchmarks
                are defined, otherwise the general interpretation from metadata

        Example:
            >>> metric = SomeMetric()  # with benchmark_ranges defined
            >>> metric.get_interpretation(2.5)
            "Excellent - Un ratio > 1 indique une bonne liquidité"
        """
        base_interpretation = self.metadata.interpretation

        if self.metadata.benchmark_ranges is None:
            return base_interpretation

        ranges = self.metadata.benchmark_ranges
        rating = self._get_rating(value, ranges)

        if rating:
            return f"{rating} - {base_interpretation}"

        return base_interpretation

    def _get_rating(self, value: float, ranges: Dict[str, float]) -> str:
        """
        Determine the rating based on value and benchmark ranges.

        Args:
            value: The calculated metric value
            ranges: Dictionary of benchmark thresholds

        Returns:
            str: Rating label (Excellent, Bon, Acceptable, Risque, Critique)
        """
        # Get thresholds, with defaults if not all are defined
        excellent = ranges.get("excellent", float("inf"))
        good = ranges.get("good", float("inf"))
        acceptable = ranges.get("acceptable", float("inf"))
        risky = ranges.get("risky", float("-inf"))

        # Determine if higher is better (most common) or lower is better
        # If excellent > risky, higher values are better
        higher_is_better = excellent >= risky

        if higher_is_better:
            if value >= excellent:
                return "Excellent"
            elif value >= good:
                return "Bon"
            elif value >= acceptable:
                return "Acceptable"
            elif value >= risky:
                return "Risque"
            else:
                return "Critique"
        else:
            # Lower is better (e.g., debt ratios)
            if value <= excellent:
                return "Excellent"
            elif value <= good:
                return "Bon"
            elif value <= acceptable:
                return "Acceptable"
            elif value <= risky:
                return "Risque"
            else:
                return "Critique"

    def format_value(self, value: float) -> str:
        """
        Format the calculated value according to its unit type.

        Applies appropriate formatting based on the metric's unit:
        - %: Two decimal places with % suffix
        - euro/EUR: Thousands separator with euro symbol
        - ratio: Two decimal places
        - jours/days: Integer with "jours" suffix
        - fois/times: One decimal place with "x" suffix
        - Default: Two decimal places

        Args:
            value: The calculated metric value

        Returns:
            str: Formatted string representation of the value

        Example:
            >>> metric_pct = SomeMetric()  # unit = "%"
            >>> metric_pct.format_value(25.567)
            "25.57 %"

            >>> metric_euro = SomeMetric()  # unit = "euro"
            >>> metric_euro.format_value(1234567.89)
            "1 234 567.89 EUR"
        """
        unit = self.metadata.unit.lower()

        if unit == "%":
            return f"{value:.2f} %"

        elif unit in ("euro", "eur", "euros"):
            # Format with thousands separator (French style with spaces)
            formatted = f"{value:,.2f}".replace(",", " ")
            return f"{formatted} EUR"

        elif unit == "ratio":
            return f"{value:.2f}"

        elif unit in ("jours", "jour", "days", "day"):
            return f"{int(round(value))} jours"

        elif unit in ("fois", "times", "x"):
            return f"{value:.1f}x"

        elif unit in ("mois", "month", "months"):
            return f"{value:.1f} mois"

        elif unit in ("annees", "années", "year", "years", "ans"):
            return f"{value:.1f} ans"

        else:
            # Default formatting
            return f"{value:.2f} {self.metadata.unit}"


class MetricRegistry:
    """
    Singleton registry for managing financial metrics.

    This class provides a centralized repository for all registered
    financial metrics, allowing lookup by name or category.

    The registry uses class-level storage to ensure all metrics
    are accessible from anywhere in the application.

    Attributes:
        _metrics: Private dictionary mapping metric names to classes

    Example:
        # Register a metric
        MetricRegistry.register(CurrentRatio)

        # Retrieve a metric by name
        metric_class = MetricRegistry.get_metric("current_ratio")
        metric = metric_class()
        result = metric.calculate(financial_data)

        # Get all metrics in a category
        liquidity_metrics = MetricRegistry.get_by_category(MetricCategory.LIQUIDITY)
    """

    _metrics: Dict[str, Type["FinancialMetric"]] = {}

    @classmethod
    def register(cls, metric_class: Type[FinancialMetric]) -> None:
        """
        Register a financial metric class in the registry.

        Adds the metric class to the registry using its metadata.name
        as the key. If a metric with the same name already exists,
        it will be overwritten with a warning.

        Args:
            metric_class: The FinancialMetric subclass to register

        Raises:
            TypeError: If metric_class is not a subclass of FinancialMetric
            ValueError: If the metric class doesn't have valid metadata

        Example:
            MetricRegistry.register(TauxMargeBrute)
        """
        if not isinstance(metric_class, type) or not issubclass(metric_class, FinancialMetric):
            raise TypeError(
                f"La classe {metric_class} doit être une sous-classe de FinancialMetric"
            )

        # Create an instance to access metadata
        try:
            instance = metric_class()
            metric_name = instance.metadata.name
        except Exception as e:
            raise ValueError(
                f"Impossible d'accéder aux métadonnées de {metric_class.__name__}: {e}"
            )

        if metric_name in cls._metrics:
            import warnings
            warnings.warn(
                f"La métrique '{metric_name}' existe déjà et sera remplacée par {metric_class.__name__}",
                UserWarning
            )

        cls._metrics[metric_name] = metric_class

    @classmethod
    def get_metric(cls, name: str) -> Type[FinancialMetric]:
        """
        Retrieve a metric class by its name.

        Args:
            name: The unique name of the metric (as defined in metadata)

        Returns:
            Type[FinancialMetric]: The metric class

        Raises:
            KeyError: If no metric with the given name is registered

        Example:
            metric_class = MetricRegistry.get_metric("current_ratio")
            metric = metric_class()
            value = metric.calculate(data)
        """
        if name not in cls._metrics:
            available = ", ".join(cls._metrics.keys()) if cls._metrics else "aucune"
            raise KeyError(
                f"Métrique '{name}' non trouvée. Métriques disponibles: {available}"
            )

        return cls._metrics[name]

    @classmethod
    def get_all_metrics(cls) -> List[Type["FinancialMetric"]]:
        """
        Get all registered metric classes.

        Returns:
            List[Type[FinancialMetric]]: List of all registered metric classes

        Example:
            all_metrics = MetricRegistry.get_all_metrics()
            for metric_class in all_metrics:
                metric = metric_class()
                print(f"{metric.metadata.name}: {metric.metadata.description}")
        """
        return list(cls._metrics.values())

    @classmethod
    def get_by_category(cls, category: MetricCategory) -> List[Type["FinancialMetric"]]:
        """
        Get all metrics belonging to a specific category.

        Args:
            category: The MetricCategory to filter by

        Returns:
            List[Type[FinancialMetric]]: List of metric classes in the category

        Example:
            liquidity_metrics = MetricRegistry.get_by_category(MetricCategory.LIQUIDITY)
            for metric_class in liquidity_metrics:
                metric = metric_class()
                print(metric.metadata.name)
        """
        result = []
        for metric_class in cls._metrics.values():
            try:
                instance = metric_class()
                if instance.metadata.category == category:
                    result.append(metric_class)
            except Exception:
                # Skip metrics that can't be instantiated
                continue

        return result

    @classmethod
    def list_metric_names(cls) -> List[str]:
        """
        Get a list of all registered metric names.

        Returns:
            List[str]: Sorted list of metric names

        Example:
            names = MetricRegistry.list_metric_names()
            print("Available metrics:", names)
        """
        return sorted(cls._metrics.keys())

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered metrics.

        This method is primarily useful for testing purposes.

        Warning:
            This will remove ALL registered metrics from the registry.
        """
        cls._metrics.clear()

    @classmethod
    def count(cls) -> int:
        """
        Get the number of registered metrics.

        Returns:
            int: Number of metrics in the registry
        """
        return len(cls._metrics)


def register_metric(cls: Type[FinancialMetric]) -> Type[FinancialMetric]:
    """
    Decorator to automatically register a metric class.

    This decorator can be applied to any FinancialMetric subclass
    to automatically register it in the MetricRegistry upon class definition.

    Args:
        cls: The FinancialMetric subclass to register

    Returns:
        Type[FinancialMetric]: The same class, now registered

    Example:
        @register_metric
        class TauxMargeBrute(FinancialMetric):
            metadata = MetricMetadata(
                name="taux_marge_brute",
                formula_latex=r"\\frac{Marge Brute}{CA} \\times 100",
                description="Taux de marge brute",
                unit="%",
                category=MetricCategory.PROFITABILITY,
                source_fields=["marge_brute", "chiffre_affaires"],
                interpretation="Mesure l'efficacité de la production"
            )

            def calculate(self, financial_data: dict) -> float:
                ca = financial_data.get("chiffre_affaires", 0)
                if ca == 0:
                    return 0.0
                return (financial_data["marge_brute"] / ca) * 100
    """
    MetricRegistry.register(cls)
    return cls


# Type alias for metric calculation functions (useful for functional style)
MetricCalculator = Callable[[dict], float]


__all__ = [
    "MetricCategory",
    "MetricMetadata",
    "FinancialMetric",
    "MetricRegistry",
    "register_metric",
    "MetricCalculator",
]
