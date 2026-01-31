"""
Metriques de rentabilite pour l'analyse financiere.

Ce module contient les metriques de rentabilite essentielles :
- EBITDA
- Marge Brute
- Marge d'Exploitation
- Marge Nette
"""

from src.calculations.base import (
    FinancialMetric,
    MetricMetadata,
    MetricCategory,
    register_metric,
)


@register_metric
class EBITDA(FinancialMetric):
    """
    EBITDA (Earnings Before Interest, Taxes, Depreciation and Amortization).

    Correspond au resultat d'exploitation avant dotations aux amortissements
    et provisions. Mesure la performance operationnelle pure.
    """

    _metadata = MetricMetadata(
        name="ebitda",
        formula_latex=r"Resultat\ d'exploitation + Dotations\ aux\ amortissements",
        description=(
            "EBITDA - Excedent Brut d'Exploitation. "
            "Mesure la capacite de l'entreprise a generer de la tresorerie "
            "a partir de son activite operationnelle."
        ),
        unit="euro",
        category=MetricCategory.PROFITABILITY,
        source_fields=[
            "income_statement.operating_income",
            "income_statement.operating_expenses.depreciation",
        ],
        interpretation=(
            "EBITDA positif = L'exploitation degage de la tresorerie | "
            "EBITDA negatif = L'exploitation consomme de la tresorerie"
        ),
        benchmark_ranges=None,  # L'EBITDA est contextuel, depend de la taille
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule l'EBITDA.

        Formule: Resultat d'exploitation + Dotations aux amortissements

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: EBITDA en euros
        """
        # Extraction du resultat d'exploitation
        try:
            operating_income = financial_data.get("income_statement", {}).get(
                "operating_income", 0
            )
        except (TypeError, AttributeError):
            operating_income = 0

        # Extraction des amortissements
        try:
            depreciation = (
                financial_data.get("income_statement", {})
                .get("operating_expenses", {})
                .get("depreciation", 0)
            )
        except (TypeError, AttributeError):
            depreciation = 0

        # Extraction des provisions (dotations)
        try:
            provisions = (
                financial_data.get("income_statement", {})
                .get("operating_expenses", {})
                .get("provisions", 0)
            )
        except (TypeError, AttributeError):
            provisions = 0

        return operating_income + depreciation + provisions


@register_metric
class MargeBrute(FinancialMetric):
    """
    Marge Brute (Gross Margin).

    Mesure le pourcentage du chiffre d'affaires restant apres deduction
    des couts d'achat des marchandises/matieres premieres.
    """

    _metadata = MetricMetadata(
        name="marge_brute",
        formula_latex=r"\frac{CA - Achats}{CA} \times 100",
        description=(
            "Marge Brute. "
            "Pourcentage du chiffre d'affaires restant apres "
            "deduction des achats de marchandises et matieres premieres."
        ),
        unit="%",
        category=MetricCategory.PROFITABILITY,
        source_fields=[
            "income_statement.revenues.net_revenue",
            "income_statement.operating_expenses.purchases_of_goods",
            "income_statement.operating_expenses.purchases_of_raw_materials",
        ],
        interpretation=(
            "Marge brute elevee = Bonne valeur ajoutee | "
            "Marge brute faible = Activite de negoce ou pression concurrentielle"
        ),
        benchmark_ranges={
            "excellent": 50.0,
            "good": 30.0,
            "acceptable": 15.0,
            "risky": 5.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule la Marge Brute.

        Formule: ((CA - Achats) / CA) x 100

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Marge brute en pourcentage (0 si CA = 0)
        """
        # Extraction du chiffre d'affaires
        try:
            net_revenue = (
                financial_data.get("income_statement", {})
                .get("revenues", {})
                .get("net_revenue", 0)
            )
        except (TypeError, AttributeError):
            net_revenue = 0

        # Si net_revenue n'est pas renseigne, calculer depuis le total
        if net_revenue == 0:
            try:
                net_revenue = (
                    financial_data.get("income_statement", {})
                    .get("revenues", {})
                    .get("total", 0)
                )
            except (TypeError, AttributeError):
                net_revenue = 0

        # Extraction des achats de marchandises
        try:
            purchases_goods = (
                financial_data.get("income_statement", {})
                .get("operating_expenses", {})
                .get("purchases_of_goods", 0)
            )
        except (TypeError, AttributeError):
            purchases_goods = 0

        # Extraction des achats de matieres premieres
        try:
            purchases_raw = (
                financial_data.get("income_statement", {})
                .get("operating_expenses", {})
                .get("purchases_of_raw_materials", 0)
            )
        except (TypeError, AttributeError):
            purchases_raw = 0

        # Extraction de la variation de stock
        try:
            inventory_variation = (
                financial_data.get("income_statement", {})
                .get("operating_expenses", {})
                .get("inventory_variation", 0)
            )
        except (TypeError, AttributeError):
            inventory_variation = 0

        # Total des achats consommes
        total_purchases = purchases_goods + purchases_raw + inventory_variation

        # Gestion de la division par zero
        if net_revenue == 0:
            return 0.0

        return ((net_revenue - total_purchases) / net_revenue) * 100


@register_metric
class MargeExploitation(FinancialMetric):
    """
    Marge d'Exploitation (Operating Margin).

    Mesure le pourcentage du chiffre d'affaires qui reste apres deduction
    de l'ensemble des charges d'exploitation.
    """

    _metadata = MetricMetadata(
        name="marge_exploitation",
        formula_latex=r"\frac{Resultat\ d'exploitation}{CA} \times 100",
        description=(
            "Marge d'Exploitation. "
            "Pourcentage du chiffre d'affaires constituant "
            "le resultat d'exploitation."
        ),
        unit="%",
        category=MetricCategory.PROFITABILITY,
        source_fields=[
            "income_statement.operating_income",
            "income_statement.revenues.net_revenue",
        ],
        interpretation=(
            "> 15% = Excellente marge | "
            "10-15% = Bonne marge | "
            "5-10% = Acceptable | "
            "< 5% = Marge faible"
        ),
        benchmark_ranges={
            "excellent": 15.0,
            "good": 10.0,
            "acceptable": 5.0,
            "risky": 0.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule la Marge d'Exploitation.

        Formule: (Resultat d'exploitation / CA) x 100

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Marge d'exploitation en pourcentage (0 si CA = 0)
        """
        # Extraction du resultat d'exploitation
        try:
            operating_income = financial_data.get("income_statement", {}).get(
                "operating_income", 0
            )
        except (TypeError, AttributeError):
            operating_income = 0

        # Extraction du chiffre d'affaires
        try:
            net_revenue = (
                financial_data.get("income_statement", {})
                .get("revenues", {})
                .get("net_revenue", 0)
            )
        except (TypeError, AttributeError):
            net_revenue = 0

        # Si net_revenue n'est pas renseigne, calculer depuis le total
        if net_revenue == 0:
            try:
                net_revenue = (
                    financial_data.get("income_statement", {})
                    .get("revenues", {})
                    .get("total", 0)
                )
            except (TypeError, AttributeError):
                net_revenue = 0

        # Gestion de la division par zero
        if net_revenue == 0:
            return 0.0

        return (operating_income / net_revenue) * 100


@register_metric
class MargeNette(FinancialMetric):
    """
    Marge Nette (Net Profit Margin).

    Mesure le pourcentage du chiffre d'affaires qui constitue
    le benefice net apres toutes les charges et impots.
    """

    _metadata = MetricMetadata(
        name="marge_nette",
        formula_latex=r"\frac{Resultat\ net}{CA} \times 100",
        description=(
            "Marge Nette. "
            "Pourcentage du chiffre d'affaires constituant "
            "le resultat net final."
        ),
        unit="%",
        category=MetricCategory.PROFITABILITY,
        source_fields=[
            "income_statement.net_income",
            "income_statement.revenues.net_revenue",
        ],
        interpretation=(
            "> 10% = Excellente rentabilite | "
            "5-10% = Bonne rentabilite | "
            "2-5% = Acceptable | "
            "< 2% = Rentabilite faible"
        ),
        benchmark_ranges={
            "excellent": 10.0,
            "good": 5.0,
            "acceptable": 2.0,
            "risky": 0.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule la Marge Nette.

        Formule: (Resultat net / CA) x 100

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Marge nette en pourcentage (0 si CA = 0)
        """
        # Extraction du resultat net
        try:
            net_income = financial_data.get("income_statement", {}).get(
                "net_income", 0
            )
        except (TypeError, AttributeError):
            net_income = 0

        # Extraction du chiffre d'affaires
        try:
            net_revenue = (
                financial_data.get("income_statement", {})
                .get("revenues", {})
                .get("net_revenue", 0)
            )
        except (TypeError, AttributeError):
            net_revenue = 0

        # Si net_revenue n'est pas renseigne, calculer depuis le total
        if net_revenue == 0:
            try:
                net_revenue = (
                    financial_data.get("income_statement", {})
                    .get("revenues", {})
                    .get("total", 0)
                )
            except (TypeError, AttributeError):
                net_revenue = 0

        # Gestion de la division par zero
        if net_revenue == 0:
            return 0.0

        return (net_income / net_revenue) * 100


__all__ = ["EBITDA", "MargeBrute", "MargeExploitation", "MargeNette"]
