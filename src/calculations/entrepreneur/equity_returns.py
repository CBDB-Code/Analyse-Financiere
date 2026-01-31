"""
Metriques de rendement pour l'analyse entrepreneuriale.

Ce module contient les metriques utilisees par les entrepreneurs et investisseurs
pour evaluer la rentabilite de leurs investissements :
- ROE (Return on Equity)
- Payback Period (Delai de recuperation)
"""

from src.calculations.base import (
    FinancialMetric,
    MetricMetadata,
    MetricCategory,
    register_metric,
)


@register_metric
class ROE(FinancialMetric):
    """
    Return on Equity (Rentabilite des capitaux propres).

    Mesure le rendement genere pour les actionnaires par rapport
    aux capitaux qu'ils ont investis dans l'entreprise.

    Un ROE eleve indique une utilisation efficace des fonds propres.
    """

    _metadata = MetricMetadata(
        name="roe",
        formula_latex=r"\frac{Resultat\ net}{Capitaux\ propres} \times 100",
        description=(
            "Rentabilite des capitaux propres. "
            "Mesure le rendement genere pour chaque euro "
            "investi par les actionnaires."
        ),
        unit="%",
        category=MetricCategory.ENTREPRENEUR,
        source_fields=[
            "income_statement.net_income",
            "balance_sheet.liabilities.equity.total",
        ],
        interpretation=(
            "ROE > 15% = Excellente rentabilite | "
            "10-15% = Bonne | "
            "5-10% = Acceptable | "
            "< 5% = Faible"
        ),
        benchmark_ranges={
            "excellent": 20.0,
            "good": 15.0,
            "acceptable": 10.0,
            "risky": 5.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le ROE.

        Formule: (Resultat net / Capitaux propres) x 100

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: ROE en pourcentage (0 si capitaux propres <= 0)
        """
        # Extraction du resultat net
        try:
            net_income = financial_data.get("income_statement", {}).get(
                "net_income", 0
            )
        except (TypeError, AttributeError):
            net_income = 0

        # Extraction des capitaux propres
        try:
            equity = (
                financial_data.get("balance_sheet", {})
                .get("liabilities", {})
                .get("equity", {})
                .get("total", 0)
            )
        except (TypeError, AttributeError):
            equity = 0

        # Gestion des capitaux propres nuls ou negatifs
        if equity <= 0:
            return 0.0

        return (net_income / equity) * 100


@register_metric
class PaybackPeriod(FinancialMetric):
    """
    Payback Period (Delai de recuperation de l'investissement).

    Mesure le temps necessaire pour recuperer l'investissement initial
    grace aux cash-flows generes par l'entreprise.

    Un delai court est preferable car il reduit le risque.
    """

    _metadata = MetricMetadata(
        name="payback_period",
        formula_latex=r"\frac{Investissement\ initial}{Cash\ flow\ annuel\ moyen}",
        description=(
            "Delai de recuperation de l'investissement. "
            "Nombre d'annees necessaires pour recuperer "
            "l'investissement initial via les cash-flows."
        ),
        unit="annees",
        category=MetricCategory.ENTREPRENEUR,
        source_fields=[
            "scenario.equity_amount",
            "income_statement.operating_income",
            "income_statement.operating_expenses.depreciation",
        ],
        interpretation=(
            "< 3 ans = Excellent | "
            "3-5 ans = Bon | "
            "5-7 ans = Acceptable | "
            "> 7 ans = Risque eleve"
        ),
        benchmark_ranges={
            # Pour le payback, plus bas = mieux, donc ordre inverse
            "excellent": 3.0,
            "good": 5.0,
            "acceptable": 7.0,
            "risky": 10.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le Payback Period.

        Formule simplifiee (MVP): Investissement / EBITDA
        Ou EBITDA est utilise comme proxy du cash-flow operationnel.

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Delai en annees (inf si cash-flow <= 0)
        """
        # Extraction du montant de l'investissement (equity)
        try:
            equity_amount = financial_data.get("scenario", {}).get(
                "equity_amount", 0
            )
        except (TypeError, AttributeError):
            equity_amount = 0

        # Si pas d'investissement specifie, utiliser les capitaux propres
        if equity_amount == 0:
            try:
                equity_amount = (
                    financial_data.get("balance_sheet", {})
                    .get("liabilities", {})
                    .get("equity", {})
                    .get("total", 0)
                )
            except (TypeError, AttributeError):
                equity_amount = 0

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

        # Calcul de l'EBITDA comme proxy du cash-flow annuel
        ebitda = operating_income + depreciation

        # Gestion des cas speciaux
        if equity_amount <= 0:
            return 0.0

        if ebitda <= 0:
            return float("inf")

        return equity_amount / ebitda

    def _get_rating(self, value: float, ranges: dict[str, float]) -> str:
        """
        Determine le rating (pour le payback, plus bas = mieux).

        Override de la methode parente car le payback a une logique inversee.

        Args:
            value: La valeur calculee
            ranges: Dictionnaire des seuils

        Returns:
            str: Le rating
        """
        excellent = ranges.get("excellent", 3.0)
        good = ranges.get("good", 5.0)
        acceptable = ranges.get("acceptable", 7.0)
        risky = ranges.get("risky", 10.0)

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


__all__ = ["ROE", "PaybackPeriod"]
