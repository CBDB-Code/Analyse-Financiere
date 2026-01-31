"""
Metriques de couverture de dette pour l'analyse bancaire.

Ce module contient les metriques utilisees par les banquiers pour evaluer
la capacite d'une entreprise a rembourser sa dette :
- DSCR (Debt Service Coverage Ratio)
- ICR (Interest Coverage Ratio)
"""

from src.calculations.base import (
    FinancialMetric,
    MetricMetadata,
    MetricCategory,
    register_metric,
)


@register_metric
class DSCR(FinancialMetric):
    """
    Debt Service Coverage Ratio (Ratio de couverture du service de la dette).

    Mesure la capacite de l'entreprise a couvrir le remboursement de sa dette
    (principal + interets) avec son cash-flow operationnel (EBITDA).

    Un DSCR > 1 signifie que l'entreprise genere suffisamment de tresorerie
    pour honorer ses echeances de dette.
    """

    _metadata = MetricMetadata(
        name="dscr",
        formula_latex=r"\frac{EBITDA}{Service\ annuel\ de\ la\ dette}",
        description=(
            "Ratio de couverture du service de la dette. "
            "Mesure la capacite de l'entreprise a rembourser sa dette "
            "avec son excedent brut d'exploitation."
        ),
        unit="ratio",
        category=MetricCategory.BANKER,
        source_fields=[
            "income_statement.operating_income",
            "income_statement.operating_expenses.depreciation",
            "scenario.annual_debt_service",
        ],
        interpretation=(
            "DSCR > 1.25 = Bonne couverture | "
            "1.0-1.25 = Acceptable | "
            "< 1.0 = Risque de defaut"
        ),
        benchmark_ranges={
            "excellent": 1.5,
            "good": 1.25,
            "acceptable": 1.0,
            "risky": 0.8,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le DSCR.

        Formule: EBITDA / Service annuel de la dette
        Ou EBITDA = Resultat d'exploitation + Dotations aux amortissements

        Args:
            financial_data: Dictionnaire contenant les donnees financieres
                avec la structure FiscalData et optionnellement un scenario

        Returns:
            float: Valeur du DSCR (inf si service de dette = 0)
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

        # Calcul de l'EBITDA
        ebitda = operating_income + depreciation

        # Extraction du service de dette annuel (depuis le scenario)
        try:
            annual_debt_service = financial_data.get("scenario", {}).get(
                "annual_debt_service", 0
            )
        except (TypeError, AttributeError):
            annual_debt_service = 0

        # Gestion de la division par zero
        if annual_debt_service == 0:
            return float("inf")

        return ebitda / annual_debt_service


@register_metric
class ICR(FinancialMetric):
    """
    Interest Coverage Ratio (Ratio de couverture des interets).

    Mesure la capacite de l'entreprise a payer ses charges financieres
    avec son resultat d'exploitation (EBIT).

    Un ICR eleve indique une bonne capacite a supporter la charge
    de la dette.
    """

    _metadata = MetricMetadata(
        name="icr",
        formula_latex=r"\frac{EBIT}{Charges\ financieres}",
        description=(
            "Ratio de couverture des interets. "
            "Mesure combien de fois le resultat d'exploitation "
            "couvre les charges financieres."
        ),
        unit="ratio",
        category=MetricCategory.BANKER,
        source_fields=[
            "income_statement.operating_income",
            "income_statement.financial_result.interest_expense",
        ],
        interpretation=(
            "ICR > 3 = Sain | "
            "1.5-3 = Acceptable | "
            "< 1.5 = Risque"
        ),
        benchmark_ranges={
            "excellent": 5.0,
            "good": 3.0,
            "acceptable": 1.5,
            "risky": 1.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule l'ICR.

        Formule: Resultat d'exploitation / Charges financieres

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Valeur de l'ICR (inf si charges financieres = 0)
        """
        # Extraction du resultat d'exploitation (EBIT)
        try:
            operating_income = financial_data.get("income_statement", {}).get(
                "operating_income", 0
            )
        except (TypeError, AttributeError):
            operating_income = 0

        # Extraction des charges financieres (interets)
        try:
            interest_expense = (
                financial_data.get("income_statement", {})
                .get("financial_result", {})
                .get("interest_expense", 0)
            )
        except (TypeError, AttributeError):
            interest_expense = 0

        # Si pas de charges financieres specifiques, essayer total_financial_expense
        if interest_expense == 0:
            try:
                interest_expense = (
                    financial_data.get("income_statement", {})
                    .get("financial_result", {})
                    .get("total_financial_expense", 0)
                )
            except (TypeError, AttributeError):
                interest_expense = 0

        # Gestion de la division par zero
        if interest_expense == 0:
            return float("inf")

        return operating_income / interest_expense


__all__ = ["DSCR", "ICR"]
