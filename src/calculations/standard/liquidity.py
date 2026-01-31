"""
Metriques de liquidite pour l'analyse financiere.

Ce module contient les metriques de liquidite essentielles :
- Fonds de Roulement (FR)
- Besoin en Fonds de Roulement (BFR)
"""

from src.calculations.base import (
    FinancialMetric,
    MetricMetadata,
    MetricCategory,
    register_metric,
)


@register_metric
class FondsDeRoulement(FinancialMetric):
    """
    Fonds de Roulement (FR).

    Represente l'excedent des capitaux permanents (capitaux propres + dettes LT)
    sur les actifs immobilises.

    Un FR positif signifie que les ressources stables financent les
    immobilisations et degagent un excedent pour le cycle d'exploitation.
    """

    _metadata = MetricMetadata(
        name="fonds_de_roulement",
        formula_latex=r"Capitaux\ permanents - Actif\ immobilise",
        description=(
            "Fonds de Roulement. "
            "Difference entre les ressources stables (capitaux propres + dettes LT) "
            "et les emplois stables (immobilisations)."
        ),
        unit="euro",
        category=MetricCategory.LIQUIDITY,
        source_fields=[
            "balance_sheet.liabilities.equity.total",
            "balance_sheet.liabilities.debt.long_term_debt",
            "balance_sheet.assets.fixed_assets.total",
        ],
        interpretation=(
            "FR > 0 = Equilibre financier (ressources stables couvrent les immobilisations) | "
            "FR < 0 = Risque de liquidite (immobilisations financees par ressources court terme)"
        ),
        benchmark_ranges=None,  # Le FR est contextuel, pas de benchmark universel
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le Fonds de Roulement.

        Formule: (Capitaux propres + Dettes LT) - Immobilisations

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Fonds de Roulement en euros
        """
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

        # Extraction des dettes long terme
        try:
            long_term_debt = (
                financial_data.get("balance_sheet", {})
                .get("liabilities", {})
                .get("debt", {})
                .get("long_term_debt", 0)
            )
        except (TypeError, AttributeError):
            long_term_debt = 0

        # Extraction des provisions (font partie des ressources stables)
        try:
            provisions = (
                financial_data.get("balance_sheet", {})
                .get("liabilities", {})
                .get("provisions", {})
                .get("total", 0)
            )
        except (TypeError, AttributeError):
            provisions = 0

        # Calcul des capitaux permanents
        capitaux_permanents = equity + long_term_debt + provisions

        # Extraction des immobilisations
        try:
            fixed_assets = (
                financial_data.get("balance_sheet", {})
                .get("assets", {})
                .get("fixed_assets", {})
                .get("total", 0)
            )
        except (TypeError, AttributeError):
            fixed_assets = 0

        return capitaux_permanents - fixed_assets


@register_metric
class BFR(FinancialMetric):
    """
    Besoin en Fonds de Roulement (BFR).

    Represente le besoin de financement lie au cycle d'exploitation.
    Calcule comme la difference entre les emplois cycliques (stocks + creances)
    et les ressources cycliques (dettes d'exploitation).

    Un BFR positif indique un besoin de financement a couvrir.
    Un BFR negatif indique une ressource de tresorerie degagee.
    """

    _metadata = MetricMetadata(
        name="bfr",
        formula_latex=r"(Stocks + Creances) - Dettes\ court\ terme\ d'exploitation",
        description=(
            "Besoin en Fonds de Roulement. "
            "Mesure le besoin de financement lie au decalage entre "
            "les encaissements clients et les decaissements fournisseurs."
        ),
        unit="euro",
        category=MetricCategory.LIQUIDITY,
        source_fields=[
            "balance_sheet.assets.current_assets.inventory",
            "balance_sheet.assets.current_assets.trade_receivables",
            "balance_sheet.liabilities.operating_liabilities.trade_payables",
            "balance_sheet.liabilities.operating_liabilities.tax_liabilities",
            "balance_sheet.liabilities.operating_liabilities.social_liabilities",
        ],
        interpretation=(
            "BFR positif = Besoin de financement a couvrir | "
            "BFR negatif = Ressource de tresorerie degagee (ex: grande distribution)"
        ),
        benchmark_ranges=None,  # Le BFR est contextuel, depend du secteur
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le BFR.

        Formule: (Stocks + Creances clients) - (Fournisseurs + Dettes fiscales/sociales)

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: BFR en euros (positif = besoin, negatif = ressource)
        """
        # Extraction des stocks
        try:
            inventory = (
                financial_data.get("balance_sheet", {})
                .get("assets", {})
                .get("current_assets", {})
                .get("inventory", 0)
            )
        except (TypeError, AttributeError):
            inventory = 0

        # Extraction des creances clients
        try:
            trade_receivables = (
                financial_data.get("balance_sheet", {})
                .get("assets", {})
                .get("current_assets", {})
                .get("trade_receivables", 0)
            )
        except (TypeError, AttributeError):
            trade_receivables = 0

        # Extraction des autres creances (hors tresorerie)
        try:
            other_receivables = (
                financial_data.get("balance_sheet", {})
                .get("assets", {})
                .get("current_assets", {})
                .get("other_receivables", 0)
            )
        except (TypeError, AttributeError):
            other_receivables = 0

        # Extraction des charges constatees d'avance
        try:
            prepaid_expenses = (
                financial_data.get("balance_sheet", {})
                .get("assets", {})
                .get("current_assets", {})
                .get("prepaid_expenses", 0)
            )
        except (TypeError, AttributeError):
            prepaid_expenses = 0

        # Emplois cycliques
        emplois_cycliques = (
            inventory + trade_receivables + other_receivables + prepaid_expenses
        )

        # Extraction des dettes fournisseurs
        try:
            trade_payables = (
                financial_data.get("balance_sheet", {})
                .get("liabilities", {})
                .get("operating_liabilities", {})
                .get("trade_payables", 0)
            )
        except (TypeError, AttributeError):
            trade_payables = 0

        # Extraction des dettes fiscales
        try:
            tax_liabilities = (
                financial_data.get("balance_sheet", {})
                .get("liabilities", {})
                .get("operating_liabilities", {})
                .get("tax_liabilities", 0)
            )
        except (TypeError, AttributeError):
            tax_liabilities = 0

        # Extraction des dettes sociales
        try:
            social_liabilities = (
                financial_data.get("balance_sheet", {})
                .get("liabilities", {})
                .get("operating_liabilities", {})
                .get("social_liabilities", 0)
            )
        except (TypeError, AttributeError):
            social_liabilities = 0

        # Extraction des avances recues
        try:
            advances_received = (
                financial_data.get("balance_sheet", {})
                .get("liabilities", {})
                .get("operating_liabilities", {})
                .get("advances_received", 0)
            )
        except (TypeError, AttributeError):
            advances_received = 0

        # Extraction des produits constates d'avance
        try:
            deferred_revenue = (
                financial_data.get("balance_sheet", {})
                .get("liabilities", {})
                .get("operating_liabilities", {})
                .get("deferred_revenue", 0)
            )
        except (TypeError, AttributeError):
            deferred_revenue = 0

        # Ressources cycliques
        ressources_cycliques = (
            trade_payables
            + tax_liabilities
            + social_liabilities
            + advances_received
            + deferred_revenue
        )

        return emplois_cycliques - ressources_cycliques


__all__ = ["FondsDeRoulement", "BFR"]
