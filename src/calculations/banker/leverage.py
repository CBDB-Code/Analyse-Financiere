"""
Metriques de levier et de structure financiere pour l'analyse bancaire.

Ce module contient les metriques utilisees par les banquiers pour evaluer
la structure de financement et le niveau d'endettement d'une entreprise :
- NetDebtToEBITDA (Dette nette sur EBITDA)
- Gearing (Ratio d'endettement)
- LTV (Loan-to-Value)
- DebtCapacity (Capacite de remboursement)
- CurrentRatio (Ratio de liquidite generale)
- QuickRatio (Acid Test)
- FinancialAutonomy (Autonomie financiere)
- DebtToAssets (Dette sur actif)
"""

from src.calculations.base import (
    FinancialMetric,
    MetricMetadata,
    MetricCategory,
    register_metric,
)


def _get_ebitda(financial_data: dict) -> float:
    """
    Calcule l'EBITDA a partir des donnees financieres.

    EBITDA = Resultat d'exploitation + Dotations aux amortissements

    Args:
        financial_data: Dictionnaire contenant les donnees financieres

    Returns:
        float: Valeur de l'EBITDA
    """
    try:
        operating_income = financial_data.get("income_statement", {}).get(
            "operating_income", 0
        )
    except (TypeError, AttributeError):
        operating_income = 0

    try:
        depreciation = (
            financial_data.get("income_statement", {})
            .get("operating_expenses", {})
            .get("depreciation", 0)
        )
    except (TypeError, AttributeError):
        depreciation = 0

    return operating_income + depreciation


def _get_net_debt(financial_data: dict) -> float:
    """
    Calcule la dette nette.

    Dette nette = Dette financiere totale - Tresorerie

    Args:
        financial_data: Dictionnaire contenant les donnees financieres

    Returns:
        float: Valeur de la dette nette
    """
    # Extraction de la dette financiere
    try:
        total_debt = (
            financial_data.get("balance_sheet", {})
            .get("liabilities", {})
            .get("financial_liabilities", {})
            .get("total", 0)
        )
    except (TypeError, AttributeError):
        total_debt = 0

    # Si pas de dette structuree, essayer le champ debt_amount du scenario
    if total_debt == 0:
        try:
            total_debt = financial_data.get("scenario", {}).get("debt_amount", 0)
        except (TypeError, AttributeError):
            total_debt = 0

    # Extraction de la tresorerie
    try:
        cash = (
            financial_data.get("balance_sheet", {})
            .get("assets", {})
            .get("current_assets", {})
            .get("cash", 0)
        )
    except (TypeError, AttributeError):
        cash = 0

    return total_debt - cash


def _get_total_debt(financial_data: dict) -> float:
    """
    Recupere la dette financiere totale.

    Args:
        financial_data: Dictionnaire contenant les donnees financieres

    Returns:
        float: Valeur de la dette totale
    """
    try:
        total_debt = (
            financial_data.get("balance_sheet", {})
            .get("liabilities", {})
            .get("financial_liabilities", {})
            .get("total", 0)
        )
    except (TypeError, AttributeError):
        total_debt = 0

    # Si pas de dette structuree, essayer le champ debt_amount du scenario
    if total_debt == 0:
        try:
            total_debt = financial_data.get("scenario", {}).get("debt_amount", 0)
        except (TypeError, AttributeError):
            total_debt = 0

    return total_debt


def _get_equity(financial_data: dict) -> float:
    """
    Recupere les capitaux propres.

    Args:
        financial_data: Dictionnaire contenant les donnees financieres

    Returns:
        float: Valeur des capitaux propres
    """
    try:
        equity = (
            financial_data.get("balance_sheet", {})
            .get("liabilities", {})
            .get("equity", {})
            .get("total", 0)
        )
    except (TypeError, AttributeError):
        equity = 0

    return equity


def _get_current_assets(financial_data: dict) -> float:
    """
    Recupere l'actif circulant.

    Args:
        financial_data: Dictionnaire contenant les donnees financieres

    Returns:
        float: Valeur de l'actif circulant
    """
    try:
        current_assets = (
            financial_data.get("balance_sheet", {})
            .get("assets", {})
            .get("current_assets", {})
            .get("total", 0)
        )
    except (TypeError, AttributeError):
        current_assets = 0

    return current_assets


def _get_current_liabilities(financial_data: dict) -> float:
    """
    Recupere le passif circulant.

    Args:
        financial_data: Dictionnaire contenant les donnees financieres

    Returns:
        float: Valeur du passif circulant
    """
    try:
        current_liabilities = (
            financial_data.get("balance_sheet", {})
            .get("liabilities", {})
            .get("current_liabilities", {})
            .get("total", 0)
        )
    except (TypeError, AttributeError):
        current_liabilities = 0

    return current_liabilities


def _get_inventory(financial_data: dict) -> float:
    """
    Recupere la valeur des stocks.

    Args:
        financial_data: Dictionnaire contenant les donnees financieres

    Returns:
        float: Valeur des stocks
    """
    try:
        inventory = (
            financial_data.get("balance_sheet", {})
            .get("assets", {})
            .get("current_assets", {})
            .get("inventory", 0)
        )
    except (TypeError, AttributeError):
        inventory = 0

    return inventory


def _get_total_assets(financial_data: dict) -> float:
    """
    Recupere le total de l'actif.

    Args:
        financial_data: Dictionnaire contenant les donnees financieres

    Returns:
        float: Total de l'actif
    """
    try:
        total_assets = (
            financial_data.get("balance_sheet", {})
            .get("assets", {})
            .get("total", 0)
        )
    except (TypeError, AttributeError):
        total_assets = 0

    return total_assets


def _get_total_liabilities(financial_data: dict) -> float:
    """
    Recupere le total du passif.

    Args:
        financial_data: Dictionnaire contenant les donnees financieres

    Returns:
        float: Total du passif
    """
    try:
        total_liabilities = (
            financial_data.get("balance_sheet", {})
            .get("liabilities", {})
            .get("total", 0)
        )
    except (TypeError, AttributeError):
        total_liabilities = 0

    return total_liabilities


@register_metric
class NetDebtToEBITDA(FinancialMetric):
    """
    Ratio Dette Nette / EBITDA.

    Mesure le nombre d'annees necessaires pour rembourser la dette nette
    avec la generation de cash operationnel. C'est une metrique cle pour
    les banquiers dans le cadre d'un LBO.

    Une valeur inferieure a 3x est generalement consideree comme saine.
    """

    _metadata = MetricMetadata(
        name="net_debt_to_ebitda",
        formula_latex=r"\frac{Dette\ nette}{EBITDA}",
        description=(
            "Ratio de levier. Mesure le nombre d'annees necessaires "
            "pour rembourser la dette nette avec l'EBITDA. "
            "Metrique cle pour evaluer le niveau d'endettement."
        ),
        unit="ratio",
        category=MetricCategory.BANKER,
        source_fields=[
            "balance_sheet.liabilities.financial_liabilities.total",
            "balance_sheet.assets.current_assets.cash",
            "income_statement.operating_income",
            "income_statement.operating_expenses.depreciation",
        ],
        interpretation=(
            "< 2x = Bon | 2-3x = Acceptable | 3-4x = Eleve | > 4x = Tres risque"
        ),
        benchmark_ranges={
            "excellent": 1.0,
            "good": 2.0,
            "acceptable": 3.0,
            "risky": 4.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le ratio Dette Nette / EBITDA.

        Formule: Dette nette / EBITDA
        Ou Dette nette = Dette totale - Tresorerie

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Valeur du ratio (inf si EBITDA = 0)
        """
        net_debt = _get_net_debt(financial_data)
        ebitda = _get_ebitda(financial_data)

        if ebitda == 0:
            return float("inf") if net_debt > 0 else 0.0

        return net_debt / ebitda

    def _get_rating(self, value: float, ranges: dict) -> str:
        """
        Determine le rating (plus bas = mieux pour ce ratio).

        Args:
            value: La valeur calculee
            ranges: Dictionnaire des seuils

        Returns:
            str: Le rating
        """
        excellent = ranges.get("excellent", 1.0)
        good = ranges.get("good", 2.0)
        acceptable = ranges.get("acceptable", 3.0)
        risky = ranges.get("risky", 4.0)

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


@register_metric
class Gearing(FinancialMetric):
    """
    Gearing (Ratio d'endettement net).

    Mesure le rapport entre la dette nette et les capitaux propres.
    Permet d'evaluer le niveau de levier financier de l'entreprise.

    Un gearing inferieur a 100% indique que l'entreprise a plus de
    capitaux propres que de dette nette.
    """

    _metadata = MetricMetadata(
        name="gearing",
        formula_latex=r"\frac{Dette\ nette}{Capitaux\ propres} \times 100",
        description=(
            "Ratio d'endettement net. Mesure le rapport entre "
            "la dette nette et les capitaux propres. "
            "Indicateur cle de la structure financiere."
        ),
        unit="%",
        category=MetricCategory.BANKER,
        source_fields=[
            "balance_sheet.liabilities.financial_liabilities.total",
            "balance_sheet.assets.current_assets.cash",
            "balance_sheet.liabilities.equity.total",
        ],
        interpretation=(
            "< 100% = Bon | 100-150% = Acceptable | > 150% = Risque"
        ),
        benchmark_ranges={
            "excellent": 50.0,
            "good": 100.0,
            "acceptable": 150.0,
            "risky": 200.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le Gearing.

        Formule: (Dette nette / Capitaux propres) x 100

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Gearing en pourcentage (inf si capitaux propres <= 0)
        """
        net_debt = _get_net_debt(financial_data)
        equity = _get_equity(financial_data)

        if equity <= 0:
            return float("inf") if net_debt > 0 else 0.0

        return (net_debt / equity) * 100

    def _get_rating(self, value: float, ranges: dict) -> str:
        """
        Determine le rating (plus bas = mieux pour ce ratio).

        Args:
            value: La valeur calculee
            ranges: Dictionnaire des seuils

        Returns:
            str: Le rating
        """
        excellent = ranges.get("excellent", 50.0)
        good = ranges.get("good", 100.0)
        acceptable = ranges.get("acceptable", 150.0)
        risky = ranges.get("risky", 200.0)

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


@register_metric
class LTV(FinancialMetric):
    """
    Loan-to-Value (Ratio Dette / Valeur d'entreprise).

    Mesure le pourcentage de la valeur de l'entreprise qui est
    financee par de la dette. Metrique essentielle pour evaluer
    le risque dans un LBO.

    Une LTV elevee indique un risque plus important pour les preteurs.
    """

    _metadata = MetricMetadata(
        name="ltv",
        formula_latex=r"\frac{Dette\ totale}{Valeur\ entreprise} \times 100",
        description=(
            "Loan-to-Value. Mesure le pourcentage de la valeur "
            "de l'entreprise financee par dette. "
            "Valeur entreprise = Capitaux propres + Dette (simplifie)."
        ),
        unit="%",
        category=MetricCategory.BANKER,
        source_fields=[
            "balance_sheet.liabilities.financial_liabilities.total",
            "balance_sheet.liabilities.equity.total",
        ],
        interpretation=(
            "< 60% = Bon | 60-70% = Acceptable | > 70% = Risque"
        ),
        benchmark_ranges={
            "excellent": 40.0,
            "good": 60.0,
            "acceptable": 70.0,
            "risky": 80.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le LTV.

        Formule: (Dette totale / Valeur entreprise) x 100
        Ou Valeur entreprise = Capitaux propres + Dette (simplifie MVP)

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: LTV en pourcentage (100% si valeur = dette)
        """
        total_debt = _get_total_debt(financial_data)
        equity = _get_equity(financial_data)

        # Valeur entreprise simplifiee = Equity + Debt
        enterprise_value = equity + total_debt

        if enterprise_value <= 0:
            return 100.0 if total_debt > 0 else 0.0

        return (total_debt / enterprise_value) * 100

    def _get_rating(self, value: float, ranges: dict) -> str:
        """
        Determine le rating (plus bas = mieux pour ce ratio).

        Args:
            value: La valeur calculee
            ranges: Dictionnaire des seuils

        Returns:
            str: Le rating
        """
        excellent = ranges.get("excellent", 40.0)
        good = ranges.get("good", 60.0)
        acceptable = ranges.get("acceptable", 70.0)
        risky = ranges.get("risky", 80.0)

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


@register_metric
class DebtCapacity(FinancialMetric):
    """
    Capacite de remboursement (en annees).

    Mesure le nombre d'annees necessaires pour rembourser la dette nette
    en utilisant l'EBITDA. C'est essentiellement le meme calcul que
    NetDebtToEBITDA mais presente en annees.

    Un delai court indique une meilleure capacite de remboursement.
    """

    _metadata = MetricMetadata(
        name="debt_capacity",
        formula_latex=r"\frac{Dette\ nette}{EBITDA}",
        description=(
            "Capacite de remboursement. Nombre d'annees necessaires "
            "pour rembourser la dette nette avec l'EBITDA. "
            "Indicateur de la soutenabilite de la dette."
        ),
        unit="annees",
        category=MetricCategory.BANKER,
        source_fields=[
            "balance_sheet.liabilities.financial_liabilities.total",
            "balance_sheet.assets.current_assets.cash",
            "income_statement.operating_income",
            "income_statement.operating_expenses.depreciation",
        ],
        interpretation=(
            "< 5 ans = Bon | 5-7 ans = Acceptable | > 7 ans = Long"
        ),
        benchmark_ranges={
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
        Calcule la capacite de remboursement en annees.

        Formule: Dette nette / EBITDA

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Nombre d'annees (inf si EBITDA = 0)
        """
        net_debt = _get_net_debt(financial_data)
        ebitda = _get_ebitda(financial_data)

        if ebitda == 0:
            return float("inf") if net_debt > 0 else 0.0

        return net_debt / ebitda

    def _get_rating(self, value: float, ranges: dict) -> str:
        """
        Determine le rating (plus bas = mieux pour ce ratio).

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


@register_metric
class CurrentRatio(FinancialMetric):
    """
    Current Ratio (Ratio de liquidite generale).

    Mesure la capacite de l'entreprise a honorer ses dettes
    a court terme avec ses actifs circulants.

    Un ratio superieur a 1 indique que l'entreprise peut couvrir
    ses dettes courantes avec ses actifs courants.
    """

    _metadata = MetricMetadata(
        name="current_ratio",
        formula_latex=r"\frac{Actif\ circulant}{Passif\ circulant}",
        description=(
            "Ratio de liquidite generale. Mesure la capacite "
            "a rembourser les dettes a court terme avec les actifs "
            "circulants. Indicateur de liquidite cle."
        ),
        unit="ratio",
        category=MetricCategory.BANKER,
        source_fields=[
            "balance_sheet.assets.current_assets.total",
            "balance_sheet.liabilities.current_liabilities.total",
        ],
        interpretation=(
            "> 2 = Excellente liquidite | 1.5-2 = Bonne | "
            "1-1.5 = Acceptable | < 1 = Risque de liquidite"
        ),
        benchmark_ranges={
            "excellent": 2.0,
            "good": 1.5,
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
        Calcule le Current Ratio.

        Formule: Actif circulant / Passif circulant

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Valeur du ratio (inf si passif = 0)
        """
        current_assets = _get_current_assets(financial_data)
        current_liabilities = _get_current_liabilities(financial_data)

        if current_liabilities == 0:
            return float("inf") if current_assets > 0 else 0.0

        return current_assets / current_liabilities


@register_metric
class QuickRatio(FinancialMetric):
    """
    Quick Ratio (Acid Test / Ratio de liquidite immediate).

    Mesure la capacite de l'entreprise a honorer ses dettes
    a court terme avec ses actifs liquides (hors stocks).

    C'est une mesure plus stricte que le Current Ratio car
    les stocks peuvent etre difficiles a liquider rapidement.
    """

    _metadata = MetricMetadata(
        name="quick_ratio",
        formula_latex=r"\frac{Actif\ circulant - Stocks}{Passif\ circulant}",
        description=(
            "Ratio de liquidite immediate (Acid Test). "
            "Mesure la capacite a rembourser les dettes courantes "
            "sans recourir a la vente des stocks."
        ),
        unit="ratio",
        category=MetricCategory.BANKER,
        source_fields=[
            "balance_sheet.assets.current_assets.total",
            "balance_sheet.assets.current_assets.inventory",
            "balance_sheet.liabilities.current_liabilities.total",
        ],
        interpretation=(
            "> 1.5 = Excellente | 1-1.5 = Bonne | "
            "0.8-1 = Acceptable | < 0.8 = Risque"
        ),
        benchmark_ranges={
            "excellent": 1.5,
            "good": 1.0,
            "acceptable": 0.8,
            "risky": 0.5,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le Quick Ratio.

        Formule: (Actif circulant - Stocks) / Passif circulant

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Valeur du ratio (inf si passif = 0)
        """
        current_assets = _get_current_assets(financial_data)
        inventory = _get_inventory(financial_data)
        current_liabilities = _get_current_liabilities(financial_data)

        quick_assets = current_assets - inventory

        if current_liabilities == 0:
            return float("inf") if quick_assets > 0 else 0.0

        return quick_assets / current_liabilities


@register_metric
class FinancialAutonomy(FinancialMetric):
    """
    Autonomie financiere (Ratio de capitaux propres).

    Mesure la part des capitaux propres dans le financement total
    de l'entreprise. Plus ce ratio est eleve, plus l'entreprise
    est independante de ses creanciers.

    Un ratio eleve indique une structure financiere solide.
    """

    _metadata = MetricMetadata(
        name="financial_autonomy",
        formula_latex=r"\frac{Capitaux\ propres}{Total\ passif} \times 100",
        description=(
            "Autonomie financiere. Mesure la part des capitaux "
            "propres dans le financement total. "
            "Indicateur d'independance financiere."
        ),
        unit="%",
        category=MetricCategory.BANKER,
        source_fields=[
            "balance_sheet.liabilities.equity.total",
            "balance_sheet.liabilities.total",
        ],
        interpretation=(
            "> 50% = Excellent | 30-50% = Bon | 20-30% = Acceptable | "
            "< 20% = Faible"
        ),
        benchmark_ranges={
            "excellent": 50.0,
            "good": 30.0,
            "acceptable": 20.0,
            "risky": 10.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule l'autonomie financiere.

        Formule: (Capitaux propres / Total passif) x 100

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Autonomie financiere en pourcentage
        """
        equity = _get_equity(financial_data)
        total_liabilities = _get_total_liabilities(financial_data)

        # Si total passif est 0, utiliser le total actif (equilibre comptable)
        if total_liabilities == 0:
            total_liabilities = _get_total_assets(financial_data)

        if total_liabilities == 0:
            return 0.0

        return (equity / total_liabilities) * 100


@register_metric
class DebtToAssets(FinancialMetric):
    """
    Ratio Dette sur Actif.

    Mesure la part des actifs de l'entreprise qui est financee
    par de la dette. Plus ce ratio est eleve, plus l'entreprise
    est dependante de ses creanciers.

    Un ratio faible indique une structure financiere plus solide.
    """

    _metadata = MetricMetadata(
        name="debt_to_assets",
        formula_latex=r"\frac{Dette\ totale}{Actif\ total} \times 100",
        description=(
            "Ratio dette sur actif. Mesure la part des actifs "
            "financee par de la dette. "
            "Indicateur de la dependance aux creanciers."
        ),
        unit="%",
        category=MetricCategory.BANKER,
        source_fields=[
            "balance_sheet.liabilities.financial_liabilities.total",
            "balance_sheet.assets.total",
        ],
        interpretation=(
            "< 30% = Excellent | 30-50% = Bon | 50-70% = Acceptable | "
            "> 70% = Risque eleve"
        ),
        benchmark_ranges={
            "excellent": 30.0,
            "good": 50.0,
            "acceptable": 70.0,
            "risky": 80.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le ratio dette sur actif.

        Formule: (Dette totale / Actif total) x 100

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Ratio en pourcentage
        """
        total_debt = _get_total_debt(financial_data)
        total_assets = _get_total_assets(financial_data)

        if total_assets == 0:
            return 0.0

        return (total_debt / total_assets) * 100

    def _get_rating(self, value: float, ranges: dict) -> str:
        """
        Determine le rating (plus bas = mieux pour ce ratio).

        Args:
            value: La valeur calculee
            ranges: Dictionnaire des seuils

        Returns:
            str: Le rating
        """
        excellent = ranges.get("excellent", 30.0)
        good = ranges.get("good", 50.0)
        acceptable = ranges.get("acceptable", 70.0)
        risky = ranges.get("risky", 80.0)

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


__all__ = [
    "NetDebtToEBITDA",
    "Gearing",
    "LTV",
    "DebtCapacity",
    "CurrentRatio",
    "QuickRatio",
    "FinancialAutonomy",
    "DebtToAssets",
]
