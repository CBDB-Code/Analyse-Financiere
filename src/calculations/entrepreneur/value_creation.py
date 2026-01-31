"""
Metriques de creation de valeur pour l'analyse entrepreneuriale.

Ce module contient les metriques utilisees par les entrepreneurs et investisseurs
pour evaluer la creation de valeur dans le cadre d'une acquisition LBO :
- IRR (Internal Rate of Return / TRI)
- NPV (Net Present Value / VAN)
- ExitMultiple (Multiple de sortie)
- CashOnCashReturn (Rendement cash sur cash)
- EquityMultiple (Multiple sur equity)
- ValueCreation (Creation de valeur en euros)
- CumulativeROI (ROI cumule sur la periode)
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


def _get_net_income(financial_data: dict) -> float:
    """
    Recupere le resultat net.

    Args:
        financial_data: Dictionnaire contenant les donnees financieres

    Returns:
        float: Valeur du resultat net
    """
    try:
        net_income = financial_data.get("income_statement", {}).get("net_income", 0)
    except (TypeError, AttributeError):
        net_income = 0

    return net_income


def _get_scenario_params(financial_data: dict) -> dict:
    """
    Recupere les parametres du scenario LBO.

    Args:
        financial_data: Dictionnaire contenant les donnees financieres

    Returns:
        dict: Parametres du scenario avec valeurs par defaut
    """
    scenario = financial_data.get("scenario", {})

    return {
        "holding_period": scenario.get("holding_period", 5),
        "exit_multiple": scenario.get("exit_multiple", 6.0),
        "equity_amount": scenario.get("equity_amount", 0),
        "debt_amount": scenario.get("debt_amount", 0),
    }


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


@register_metric
class IRR(FinancialMetric):
    """
    Internal Rate of Return - TRI (Taux de Rendement Interne).

    Version simplifiee pour MVP: ROE annualise sur la periode de holding.
    Mesure le taux de rendement annuel equivalent de l'investissement.

    Note: Cette version simplifiee sera amelioree en Phase 3 pour
    prendre en compte les flux de tresorerie reels.
    """

    _metadata = MetricMetadata(
        name="irr",
        formula_latex=r"(1 + ROE)^{\frac{1}{periode}} - 1",
        description=(
            "Taux de Rendement Interne (simplifie). "
            "Mesure le rendement annualise de l'investissement "
            "sur la periode de holding. Version MVP basee sur ROE."
        ),
        unit="%",
        category=MetricCategory.ENTREPRENEUR,
        source_fields=[
            "income_statement.net_income",
            "balance_sheet.liabilities.equity.total",
            "scenario.holding_period",
        ],
        interpretation=(
            "> 25% = Excellent | 20-25% = Tres bon | "
            "15-20% = Bon | 10-15% = Acceptable | < 10% = Faible"
        ),
        benchmark_ranges={
            "excellent": 25.0,
            "good": 20.0,
            "acceptable": 15.0,
            "risky": 10.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le TRI simplifie.

        Formule MVP: ((1 + ROE) ^ (1/holding_period)) - 1
        Ou ROE = Resultat net / Capitaux propres

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: TRI en pourcentage
        """
        net_income = _get_net_income(financial_data)
        equity = _get_equity(financial_data)
        params = _get_scenario_params(financial_data)
        holding_period = params["holding_period"]

        # Calcul du ROE
        if equity <= 0:
            return 0.0

        roe = net_income / equity

        # Gestion des cas ou ROE est negatif
        if roe <= -1:
            return -100.0

        # Calcul du TRI annualise
        try:
            irr = ((1 + roe) ** (1 / holding_period)) - 1
            return irr * 100
        except (ValueError, ZeroDivisionError):
            return 0.0


@register_metric
class NPV(FinancialMetric):
    """
    Net Present Value - VAN (Valeur Actuelle Nette).

    Version simplifiee pour MVP: (EBITDA x Multiple sortie) - Investissement total
    Mesure la creation de valeur nette de l'investissement.

    Une VAN positive indique que l'investissement cree de la valeur.
    """

    _metadata = MetricMetadata(
        name="npv",
        formula_latex=r"(EBITDA \times Multiple_{sortie}) - Investissement_{total}",
        description=(
            "Valeur Actuelle Nette (simplifiee). "
            "Mesure la creation de valeur nette entre "
            "la valeur de sortie et l'investissement initial."
        ),
        unit="euro",
        category=MetricCategory.ENTREPRENEUR,
        source_fields=[
            "income_statement.operating_income",
            "income_statement.operating_expenses.depreciation",
            "scenario.exit_multiple",
            "scenario.equity_amount",
            "scenario.debt_amount",
        ],
        interpretation=(
            "> 0 = Creation de valeur | < 0 = Destruction de valeur"
        ),
        benchmark_ranges=None,  # Pas de benchmarks en valeur absolue
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule la VAN simplifiee.

        Formule MVP: (EBITDA x Multiple sortie) - Investissement total
        Ou Investissement total = Equity + Dette

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: VAN en euros
        """
        ebitda = _get_ebitda(financial_data)
        params = _get_scenario_params(financial_data)

        exit_multiple = params["exit_multiple"]
        equity_amount = params["equity_amount"]
        debt_amount = params["debt_amount"]

        # Si pas d'investissement specifie, utiliser les valeurs du bilan
        if equity_amount == 0:
            equity_amount = _get_equity(financial_data)
        if debt_amount == 0:
            debt_amount = _get_total_debt(financial_data)

        total_investment = equity_amount + debt_amount
        exit_value = ebitda * exit_multiple

        return exit_value - total_investment


@register_metric
class ExitMultiple(FinancialMetric):
    """
    Multiple de sortie.

    Mesure le multiple de valorisation a la sortie par rapport
    a l'EBITDA. Indicateur cle pour evaluer la valorisation
    dans un contexte de LBO.

    Un multiple eleve indique une valorisation attractive.
    """

    _metadata = MetricMetadata(
        name="exit_multiple",
        formula_latex=r"\frac{Valeur_{sortie}}{EBITDA}",
        description=(
            "Multiple de sortie. Rapport entre la valeur "
            "de l'entreprise a la sortie et son EBITDA. "
            "Indicateur de valorisation cle pour un LBO."
        ),
        unit="fois",
        category=MetricCategory.ENTREPRENEUR,
        source_fields=[
            "scenario.exit_multiple",
            "income_statement.operating_income",
            "income_statement.operating_expenses.depreciation",
        ],
        interpretation=(
            "> 8x = Excellente valorisation | 6-8x = Bonne | "
            "4-6x = Correcte | < 4x = Faible"
        ),
        benchmark_ranges={
            "excellent": 8.0,
            "good": 6.0,
            "acceptable": 4.0,
            "risky": 3.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le multiple de sortie.

        Retourne le multiple de sortie du scenario, ou le calcule
        a partir de la valeur entreprise et de l'EBITDA.

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Multiple de sortie
        """
        params = _get_scenario_params(financial_data)
        exit_multiple = params["exit_multiple"]

        # Si un multiple est defini dans le scenario, le retourner directement
        if exit_multiple > 0:
            return exit_multiple

        # Sinon, calculer a partir de la valeur entreprise
        ebitda = _get_ebitda(financial_data)
        equity = _get_equity(financial_data)
        debt = _get_total_debt(financial_data)

        enterprise_value = equity + debt

        if ebitda == 0:
            return 0.0

        return enterprise_value / ebitda


@register_metric
class CashOnCashReturn(FinancialMetric):
    """
    Rendement Cash-on-Cash.

    Mesure le rendement annuel en cash par rapport a l'equity investi.
    Pour le MVP, utilise l'EBITDA comme proxy du cash-flow.

    Un rendement eleve indique une bonne generation de cash.
    """

    _metadata = MetricMetadata(
        name="cash_on_cash_return",
        formula_latex=r"\frac{Cash\ flow\ annuel}{Equity\ investi} \times 100",
        description=(
            "Rendement cash-on-cash. Mesure le rendement annuel "
            "en cash par rapport a l'equity investi. "
            "EBITDA utilise comme proxy du cash-flow pour MVP."
        ),
        unit="%",
        category=MetricCategory.ENTREPRENEUR,
        source_fields=[
            "income_statement.operating_income",
            "income_statement.operating_expenses.depreciation",
            "scenario.equity_amount",
        ],
        interpretation=(
            "> 30% = Excellent | 20-30% = Tres bon | "
            "15-20% = Bon | 10-15% = Acceptable | < 10% = Faible"
        ),
        benchmark_ranges={
            "excellent": 30.0,
            "good": 20.0,
            "acceptable": 15.0,
            "risky": 10.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le rendement cash-on-cash.

        Formule: (EBITDA / Equity investi) x 100

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Rendement en pourcentage
        """
        ebitda = _get_ebitda(financial_data)
        params = _get_scenario_params(financial_data)
        equity_amount = params["equity_amount"]

        # Si pas d'equity specifie dans le scenario, utiliser les capitaux propres
        if equity_amount == 0:
            equity_amount = _get_equity(financial_data)

        if equity_amount <= 0:
            return 0.0

        return (ebitda / equity_amount) * 100


@register_metric
class EquityMultiple(FinancialMetric):
    """
    Multiple sur Equity (MoIC - Multiple on Invested Capital).

    Mesure combien de fois l'investissement en equity a ete multiplie
    a la fin de la periode de holding.

    Un multiple de 2x signifie que l'investissement a double.
    """

    _metadata = MetricMetadata(
        name="equity_multiple",
        formula_latex=r"\frac{Valeur\ finale}{Equity\ investi}",
        description=(
            "Multiple sur equity (MoIC). Mesure combien de fois "
            "l'investissement initial a ete multiplie. "
            "Valeur finale = (EBITDA x Multiple sortie) - Dette residuelle."
        ),
        unit="fois",
        category=MetricCategory.ENTREPRENEUR,
        source_fields=[
            "income_statement.operating_income",
            "income_statement.operating_expenses.depreciation",
            "scenario.exit_multiple",
            "scenario.equity_amount",
            "scenario.debt_amount",
        ],
        interpretation=(
            "> 3x = Excellent | 2-3x = Tres bon | "
            "1.5-2x = Bon | 1-1.5x = Acceptable | < 1x = Perte"
        ),
        benchmark_ranges={
            "excellent": 3.0,
            "good": 2.0,
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
        Calcule le multiple sur equity.

        Formule: Valeur finale / Equity investi
        Ou Valeur finale = (EBITDA x exit_multiple) - Dette residuelle
        Dette residuelle = Dette initiale x 0.5 (simplifie: 50% rembourse)

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Multiple sur equity
        """
        ebitda = _get_ebitda(financial_data)
        params = _get_scenario_params(financial_data)

        exit_multiple = params["exit_multiple"]
        equity_amount = params["equity_amount"]
        debt_amount = params["debt_amount"]

        # Si pas d'equity specifie, utiliser les capitaux propres
        if equity_amount == 0:
            equity_amount = _get_equity(financial_data)
        if debt_amount == 0:
            debt_amount = _get_total_debt(financial_data)

        if equity_amount <= 0:
            return 0.0

        # Valeur de sortie
        exit_value = ebitda * exit_multiple

        # Dette residuelle (simplifie: 50% rembourse sur la periode de holding)
        residual_debt = debt_amount * 0.5

        # Valeur finale pour les actionnaires
        final_equity_value = exit_value - residual_debt

        return final_equity_value / equity_amount


@register_metric
class ValueCreation(FinancialMetric):
    """
    Creation de valeur en euros.

    Mesure le gain net en valeur absolue sur la periode de holding.
    C'est la difference entre la valeur finale des actions et
    l'investissement initial en equity.

    Une valeur positive indique une creation de richesse.
    """

    _metadata = MetricMetadata(
        name="value_creation",
        formula_latex=r"Valeur\ finale - Investissement\ total",
        description=(
            "Creation de valeur nette. Gain absolu en euros "
            "entre la valeur finale et l'investissement initial. "
            "Indicateur de la richesse creee."
        ),
        unit="euro",
        category=MetricCategory.ENTREPRENEUR,
        source_fields=[
            "income_statement.operating_income",
            "income_statement.operating_expenses.depreciation",
            "scenario.exit_multiple",
            "scenario.equity_amount",
            "scenario.debt_amount",
        ],
        interpretation=(
            "> 0 = Creation de valeur | < 0 = Destruction de valeur"
        ),
        benchmark_ranges=None,  # Pas de benchmarks en valeur absolue
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule la creation de valeur en euros.

        Formule: Valeur finale - Investissement total
        Ou Valeur finale = (EBITDA x exit_multiple) - Dette residuelle
        Investissement total = Equity + Dette

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: Creation de valeur en euros
        """
        ebitda = _get_ebitda(financial_data)
        params = _get_scenario_params(financial_data)

        exit_multiple = params["exit_multiple"]
        equity_amount = params["equity_amount"]
        debt_amount = params["debt_amount"]

        # Si pas de valeurs specifiees, utiliser le bilan
        if equity_amount == 0:
            equity_amount = _get_equity(financial_data)
        if debt_amount == 0:
            debt_amount = _get_total_debt(financial_data)

        total_investment = equity_amount + debt_amount

        # Valeur de sortie
        exit_value = ebitda * exit_multiple

        # Dette residuelle (simplifie: 50% rembourse)
        residual_debt = debt_amount * 0.5

        # Valeur finale pour les actionnaires
        final_value = exit_value - residual_debt

        return final_value - total_investment


@register_metric
class CumulativeROI(FinancialMetric):
    """
    ROI cumule sur la periode de holding.

    Mesure le retour total sur l'investissement en equity
    sur toute la periode de holding, exprime en pourcentage.

    Un ROI de 100% signifie que l'investissement a double.
    """

    _metadata = MetricMetadata(
        name="cumulative_roi",
        formula_latex=r"\frac{Valeur\ finale - Equity\ investi}{Equity\ investi} \times 100",
        description=(
            "ROI cumule. Retour total sur l'equity investi "
            "sur la periode de holding, exprime en pourcentage. "
            "Indicateur de performance globale de l'investissement."
        ),
        unit="%",
        category=MetricCategory.ENTREPRENEUR,
        source_fields=[
            "income_statement.operating_income",
            "income_statement.operating_expenses.depreciation",
            "scenario.exit_multiple",
            "scenario.equity_amount",
            "scenario.debt_amount",
        ],
        interpretation=(
            "> 200% = Excellent | 100-200% = Tres bon | "
            "50-100% = Bon | 0-50% = Acceptable | < 0% = Perte"
        ),
        benchmark_ranges={
            "excellent": 200.0,
            "good": 100.0,
            "acceptable": 50.0,
            "risky": 0.0,
        },
    )

    @property
    def metadata(self) -> MetricMetadata:
        """Retourne les metadonnees de la metrique."""
        return self._metadata

    def calculate(self, financial_data: dict) -> float:
        """
        Calcule le ROI cumule.

        Formule: ((Valeur finale - Equity investi) / Equity investi) x 100
        Ou Valeur finale = (EBITDA x exit_multiple) - Dette residuelle

        Args:
            financial_data: Dictionnaire contenant les donnees financieres

        Returns:
            float: ROI cumule en pourcentage
        """
        ebitda = _get_ebitda(financial_data)
        params = _get_scenario_params(financial_data)

        exit_multiple = params["exit_multiple"]
        equity_amount = params["equity_amount"]
        debt_amount = params["debt_amount"]

        # Si pas d'equity specifie, utiliser les capitaux propres
        if equity_amount == 0:
            equity_amount = _get_equity(financial_data)
        if debt_amount == 0:
            debt_amount = _get_total_debt(financial_data)

        if equity_amount <= 0:
            return 0.0

        # Valeur de sortie
        exit_value = ebitda * exit_multiple

        # Dette residuelle (simplifie: 50% rembourse)
        residual_debt = debt_amount * 0.5

        # Valeur finale pour les actionnaires
        final_equity_value = exit_value - residual_debt

        # ROI cumule
        return ((final_equity_value - equity_amount) / equity_amount) * 100


__all__ = [
    "IRR",
    "NPV",
    "ExitMultiple",
    "CashOnCashReturn",
    "EquityMultiple",
    "ValueCreation",
    "CumulativeROI",
]
