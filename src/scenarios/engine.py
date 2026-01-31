"""
Moteur de simulation de scenarios financiers.

Ce module contient le moteur principal pour appliquer des scenarios financiers
aux donnees d'entreprise, calculer les metriques et comparer differentes
configurations de financement.

Le ScenarioEngine permet de:
- Appliquer des parametres de dette, equity et croissance aux donnees financieres
- Calculer le service de la dette selon differents types d'amortissement
- Simuler des scenarios de stress
- Calculer toutes les metriques financieres pour un scenario
- Comparer plusieurs scenarios cote a cote
"""

from copy import deepcopy
from typing import Optional

import pandas as pd

from src.scenarios.parameters import (
    ScenarioParameters,
    DebtParameters,
    EquityParameters,
    GrowthAssumptions,
    StressScenario,
)
from src.calculations.base import MetricRegistry


class ScenarioEngine:
    """
    Moteur de simulation pour appliquer des scenarios aux donnees financieres.

    Cette classe permet de modifier des donnees financieres de base en fonction
    de parametres de scenario (dette, equity, croissance, stress) et de calculer
    l'ensemble des metriques financieres resultantes.

    Attributes:
        financial_data: Dictionnaire contenant les donnees financieres de base

    Example:
        >>> data = {"revenues": {"total": {"value": 1000000}}, ...}
        >>> engine = ScenarioEngine(data)
        >>> scenario = ScenarioParameters(name="Test", debt=..., equity=..., growth=...)
        >>> result = engine.apply_scenario(scenario)
        >>> metrics = engine.calculate_all_metrics(result)
    """

    # Champs requis pour la validation des donnees financieres
    REQUIRED_FIELDS = [
        "revenues",
        "expenses",
        "profitability",
        "balance_sheet",
    ]

    def __init__(self, financial_data: dict) -> None:
        """
        Initialise le moteur de scenario avec les donnees financieres de base.

        Args:
            financial_data: Dictionnaire contenant les donnees financieres
                de l'entreprise. Doit contenir au minimum les champs
                revenues, expenses, profitability et balance_sheet.

        Raises:
            ValueError: Si financial_data est None, vide ou incomplet
            TypeError: Si financial_data n'est pas un dictionnaire

        Example:
            >>> data = load_financial_data("entreprise.json")
            >>> engine = ScenarioEngine(data)
        """
        if financial_data is None:
            raise ValueError("Les donnees financieres ne peuvent pas etre None")

        if not isinstance(financial_data, dict):
            raise TypeError(
                f"Les donnees financieres doivent etre un dictionnaire, "
                f"pas {type(financial_data).__name__}"
            )

        if not financial_data:
            raise ValueError("Les donnees financieres ne peuvent pas etre vides")

        # Validation des champs requis
        self._validate_data_completeness(financial_data)

        self.financial_data = financial_data

    def _validate_data_completeness(self, data: dict) -> None:
        """
        Valide que les donnees financieres contiennent les champs requis.

        Args:
            data: Dictionnaire de donnees financieres a valider

        Raises:
            ValueError: Si des champs requis sont manquants
        """
        missing_fields = [
            field for field in self.REQUIRED_FIELDS
            if field not in data
        ]

        if missing_fields:
            raise ValueError(
                f"Donnees financieres incompletes. Champs manquants: {missing_fields}"
            )

    def apply_scenario(self, params: ScenarioParameters) -> dict:
        """
        Applique un scenario aux donnees financieres de base.

        Cette methode cree une copie des donnees financieres et y injecte
        les parametres du scenario, incluant le calcul du service de dette,
        les hypotheses de croissance et les eventuels stress tests.

        Args:
            params: Parametres du scenario a appliquer (ScenarioParameters)

        Returns:
            dict: Copie des donnees financieres modifiees avec:
                - Un nouveau champ 'scenario' contenant les parametres
                - Le service de dette annuel calcule
                - Les ajustements de croissance appliques
                - Les effets du stress test si present

        Raises:
            TypeError: Si params n'est pas une instance de ScenarioParameters

        Example:
            >>> scenario = ScenarioParameters(
            ...     name="LBO Standard",
            ...     debt=DebtParameters(debt_amount=500000, interest_rate=0.05, loan_duration=7),
            ...     equity=EquityParameters(equity_amount=300000, target_roe=0.15, exit_multiple=6, holding_period=5),
            ...     growth=GrowthAssumptions(revenue_growth=0.05)
            ... )
            >>> modified_data = engine.apply_scenario(scenario)
        """
        if not isinstance(params, ScenarioParameters):
            raise TypeError(
                f"params doit etre une instance de ScenarioParameters, "
                f"pas {type(params).__name__}"
            )

        # Copie profonde des donnees pour eviter les effets de bord
        data = deepcopy(self.financial_data)

        # Injection des parametres du scenario
        data["scenario"] = {
            "name": params.name,
            "debt": params.debt.model_dump(),
            "equity": params.equity.model_dump(),
            "growth": params.growth.model_dump(),
            "stress": params.stress.model_dump() if params.stress else None,
            "total_financing": params.total_financing,
            "leverage_ratio": params.leverage_ratio,
            "debt_to_equity": params.debt_to_equity,
        }

        # Calcul du service de dette annuel
        annual_debt_service = self._calculate_debt_service(params.debt)
        data["scenario"]["annual_debt_service"] = annual_debt_service

        # Ajout du service de dette aux charges financieres
        self._inject_debt_service(data, annual_debt_service)

        # Application des hypotheses de croissance
        data = self._apply_growth(data, params.growth)

        # Application du stress test si present
        if params.stress is not None:
            data = self._apply_stress(data, params.stress)

        return data

    def _calculate_debt_service(self, debt: DebtParameters) -> float:
        """
        Calcule le service de dette annuel selon le type d'amortissement.

        Pour l'amortissement constant (annuites constantes):
            Formule: P * [r(1+r)^n] / [(1+r)^n - 1]
            Ou P = principal, r = taux annuel, n = nombre de periodes

        Pour l'amortissement lineaire:
            Formule: (P/n) + (P * r)
            Premiere annee avec le principal complet

        Le differe (grace_period) reduit la duree d'amortissement effective.

        Args:
            debt: Parametres de la dette (DebtParameters)

        Returns:
            float: Montant du service de dette annuel en euros

        Example:
            >>> debt = DebtParameters(
            ...     debt_amount=500000,
            ...     interest_rate=0.05,
            ...     loan_duration=7,
            ...     grace_period=1,
            ...     amortization_type="constant"
            ... )
            >>> service = engine._calculate_debt_service(debt)
            >>> print(f"Service annuel: {service:,.2f} EUR")
        """
        principal = debt.debt_amount
        rate = debt.interest_rate
        duration = debt.loan_duration
        grace_period = debt.grace_period

        # Si pas de dette, pas de service
        if principal <= 0:
            return 0.0

        # Duree d'amortissement effective (apres differe)
        effective_duration = duration - grace_period

        # Si la duree effective est nulle ou negative, pas de remboursement
        if effective_duration <= 0:
            # Pendant le differe, on ne paie que les interets
            return principal * rate

        n = effective_duration

        if debt.amortization_type == "constant":
            # Amortissement constant (annuites constantes)
            if rate == 0:
                # Cas special: taux d'interet nul
                return principal / n
            else:
                # Formule de l'annuite constante
                # A = P * [r(1+r)^n] / [(1+r)^n - 1]
                numerator = rate * ((1 + rate) ** n)
                denominator = ((1 + rate) ** n) - 1
                return principal * (numerator / denominator)

        elif debt.amortization_type == "linear":
            # Amortissement lineaire (capital constant + interets degressifs)
            # On calcule le service moyen de la premiere annee
            # Capital constant: P/n
            # Interets premiere annee: P * r
            capital_payment = principal / n
            interest_payment = principal * rate
            return capital_payment + interest_payment

        else:
            # Type d'amortissement inconnu, utilise constant par defaut
            if rate == 0:
                return principal / n
            numerator = rate * ((1 + rate) ** n)
            denominator = ((1 + rate) ** n) - 1
            return principal * (numerator / denominator)

    def _inject_debt_service(self, data: dict, annual_debt_service: float) -> None:
        """
        Injecte le service de dette dans les charges financieres.

        Args:
            data: Donnees financieres a modifier (modifiees in place)
            annual_debt_service: Montant du service de dette annuel
        """
        # Assure que la structure expenses.financial existe
        if "expenses" not in data:
            data["expenses"] = {}

        if "financial" not in data["expenses"]:
            data["expenses"]["financial"] = {}

        # Ajoute le service de dette
        data["expenses"]["financial"]["debt_service"] = {
            "value": annual_debt_service,
            "label": "Service de la dette"
        }

    def _apply_growth(self, data: dict, growth: GrowthAssumptions) -> dict:
        """
        Applique les hypotheses de croissance aux donnees financieres.

        Cette version simplifiee pour le MVP applique:
        - Le taux de croissance au chiffre d'affaires
        - L'evolution de marge a l'EBITDA

        Note: Une projection complete multi-annees sera implementee en Phase 2.

        Args:
            data: Donnees financieres (copie modifiable)
            growth: Hypotheses de croissance (GrowthAssumptions)

        Returns:
            dict: Donnees financieres avec croissance appliquee

        Example:
            >>> growth = GrowthAssumptions(revenue_growth=0.05, ebitda_margin_evolution=0.01)
            >>> data = engine._apply_growth(data, growth)
        """
        # Application de la croissance au CA
        try:
            current_revenue = self._get_nested_value(
                data, "revenues.total.value"
            )
            if current_revenue is not None:
                new_revenue = current_revenue * (1 + growth.revenue_growth)
                self._set_nested_value(data, "revenues.total.value", new_revenue)

                # Stocke aussi les valeurs originales pour reference
                data["scenario"]["original_revenue"] = current_revenue
                data["scenario"]["projected_revenue"] = new_revenue
        except (KeyError, TypeError):
            # Si la structure n'existe pas, on continue sans erreur
            pass

        # Application de l'evolution de marge a l'EBITDA
        try:
            current_ebitda = self._get_nested_value(
                data, "profitability.ebitda.value"
            )
            current_revenue = self._get_nested_value(
                data, "revenues.total.value"
            )

            if current_ebitda is not None and current_revenue is not None and current_revenue > 0:
                # Calcul de la marge actuelle
                current_margin = current_ebitda / current_revenue

                # Nouvelle marge avec evolution
                new_margin = current_margin + growth.ebitda_margin_evolution

                # Nouvel EBITDA avec la nouvelle marge appliquee au nouveau CA
                new_ebitda = current_revenue * new_margin
                self._set_nested_value(data, "profitability.ebitda.value", new_ebitda)

                # Stocke les valeurs pour reference
                data["scenario"]["original_ebitda"] = current_ebitda
                data["scenario"]["projected_ebitda"] = new_ebitda
                data["scenario"]["original_margin"] = current_margin
                data["scenario"]["projected_margin"] = new_margin
        except (KeyError, TypeError):
            pass

        return data

    def _apply_stress(self, data: dict, stress: StressScenario) -> dict:
        """
        Applique un scenario de stress aux donnees financieres.

        Le stress test simule des conditions adverses:
        - Choc sur le chiffre d'affaires (revenue_shock)
        - Compression des marges (margin_compression)
        - Hausse des taux d'interet (interest_rate_increase)

        Args:
            data: Donnees financieres (copie modifiable)
            stress: Parametres du scenario de stress (StressScenario)

        Returns:
            dict: Donnees financieres avec stress applique

        Example:
            >>> stress = StressScenario(
            ...     revenue_shock=-0.10,
            ...     margin_compression=-0.05,
            ...     interest_rate_increase=0.01
            ... )
            >>> stressed_data = engine._apply_stress(data, stress)
        """
        # Application du choc sur le CA
        try:
            current_revenue = self._get_nested_value(
                data, "revenues.total.value"
            )
            if current_revenue is not None:
                stressed_revenue = current_revenue * (1 + stress.revenue_shock)
                self._set_nested_value(data, "revenues.total.value", stressed_revenue)

                # Stocke la valeur stressee
                data["scenario"]["stressed_revenue"] = stressed_revenue
        except (KeyError, TypeError):
            pass

        # Compression des marges - appliquee proportionnellement a l'EBITDA
        try:
            current_ebitda = self._get_nested_value(
                data, "profitability.ebitda.value"
            )
            current_revenue = self._get_nested_value(
                data, "revenues.total.value"
            )

            if current_ebitda is not None and current_revenue is not None and current_revenue > 0:
                # Marge actuelle
                current_margin = current_ebitda / current_revenue

                # Compression de la marge
                stressed_margin = current_margin + stress.margin_compression
                stressed_margin = max(0, stressed_margin)  # Evite les marges negatives

                # Nouvel EBITDA stresse
                stressed_ebitda = current_revenue * stressed_margin
                self._set_nested_value(data, "profitability.ebitda.value", stressed_ebitda)

                data["scenario"]["stressed_ebitda"] = stressed_ebitda
                data["scenario"]["stressed_margin"] = stressed_margin
        except (KeyError, TypeError):
            pass

        # Augmentation des charges financieres
        try:
            current_interest = self._get_nested_value(
                data, "expenses.financial.interest_expense.value"
            )
            if current_interest is not None:
                # Augmentation proportionnelle des charges d'interet
                # On utilise le ratio d'augmentation des taux
                increase_factor = 1 + stress.interest_rate_increase
                stressed_interest = current_interest * increase_factor
                self._set_nested_value(
                    data,
                    "expenses.financial.interest_expense.value",
                    stressed_interest
                )

                data["scenario"]["stressed_interest_expense"] = stressed_interest
        except (KeyError, TypeError):
            pass

        # Marque le scenario comme stresse
        data["scenario"]["is_stressed"] = True

        return data

    def _get_nested_value(self, data: dict, path: str) -> Optional[float]:
        """
        Recupere une valeur imbriquee dans un dictionnaire.

        Args:
            data: Dictionnaire source
            path: Chemin vers la valeur (ex: "revenues.total.value")

        Returns:
            Optional[float]: La valeur si trouvee, None sinon
        """
        keys = path.split(".")
        current = data

        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]

        return current

    def _set_nested_value(self, data: dict, path: str, value: float) -> None:
        """
        Definit une valeur imbriquee dans un dictionnaire.

        Cree les cles intermediaires si necessaire.

        Args:
            data: Dictionnaire a modifier
            path: Chemin vers la valeur (ex: "revenues.total.value")
            value: Valeur a definir
        """
        keys = path.split(".")
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def calculate_all_metrics(self, scenario_data: dict) -> dict[str, float]:
        """
        Calcule toutes les metriques financieres pour un scenario.

        Parcourt toutes les metriques enregistrees dans le MetricRegistry
        et calcule leur valeur a partir des donnees du scenario.

        Args:
            scenario_data: Donnees financieres avec scenario applique

        Returns:
            dict[str, float]: Dictionnaire {nom_metrique: valeur}
                La valeur est None si le calcul a echoue

        Example:
            >>> scenario_data = engine.apply_scenario(params)
            >>> metrics = engine.calculate_all_metrics(scenario_data)
            >>> for name, value in metrics.items():
            ...     print(f"{name}: {value}")
        """
        results: dict[str, float] = {}

        # Recupere toutes les metriques enregistrees
        all_metrics = MetricRegistry.get_all_metrics()

        for metric_class in all_metrics:
            try:
                # Instancie la metrique
                metric_instance = metric_class()
                metric_name = metric_instance.metadata.name

                # Calcule la valeur
                value = metric_instance.calculate(scenario_data)
                results[metric_name] = value

            except Exception as e:
                # En cas d'erreur, on stocke None et on continue
                try:
                    metric_name = metric_class().metadata.name
                except Exception:
                    metric_name = metric_class.__name__

                results[metric_name] = None

                # Log optionnel de l'erreur (pourrait etre ameliore avec logging)
                # print(f"Erreur calcul {metric_name}: {e}")

        return results

    def compare_scenarios(
        self,
        scenarios: list[ScenarioParameters]
    ) -> pd.DataFrame:
        """
        Compare plusieurs scenarios en calculant toutes les metriques.

        Pour chaque scenario fourni:
        1. Applique le scenario aux donnees de base
        2. Calcule toutes les metriques
        3. Compile les resultats dans un DataFrame

        Args:
            scenarios: Liste de ScenarioParameters a comparer

        Returns:
            pd.DataFrame: DataFrame avec:
                - Index: noms des scenarios
                - Colonnes: noms des metriques
                - Valeurs: resultats des calculs (ou NaN si echec)

        Raises:
            ValueError: Si la liste de scenarios est vide

        Example:
            >>> scenarios = [CONSERVATIVE_SCENARIO, BALANCED_SCENARIO, LEVERAGED_SCENARIO]
            >>> comparison = engine.compare_scenarios(scenarios)
            >>> print(comparison.to_string())
        """
        if not scenarios:
            raise ValueError("La liste de scenarios ne peut pas etre vide")

        results_list = []

        for scenario in scenarios:
            # Applique le scenario
            scenario_data = self.apply_scenario(scenario)

            # Calcule toutes les metriques
            metrics = self.calculate_all_metrics(scenario_data)

            # Ajoute le nom du scenario et les infos de financement
            row = {
                "scenario_name": scenario.name,
                "total_financing": scenario.total_financing,
                "leverage_ratio": scenario.leverage_ratio,
                "debt_to_equity": scenario.debt_to_equity,
                "annual_debt_service": scenario_data["scenario"]["annual_debt_service"],
            }

            # Ajoute les metriques
            row.update(metrics)

            results_list.append(row)

        # Cree le DataFrame
        df = pd.DataFrame(results_list)

        # Utilise le nom du scenario comme index
        df = df.set_index("scenario_name")

        return df


def create_base_scenario(financial_data: dict) -> ScenarioParameters:
    """
    Cree un scenario de base sans dette ni croissance.

    Ce scenario utilise les capitaux propres actuels de l'entreprise
    comme unique source de financement (100% equity).
    Utile comme reference pour comparer l'impact des scenarios de financement.

    Args:
        financial_data: Dictionnaire des donnees financieres de l'entreprise
            Doit contenir balance_sheet.equity ou shareholders_equity

    Returns:
        ScenarioParameters: Scenario de base avec:
            - Aucune dette
            - Equity = capitaux propres actuels
            - Pas de croissance ni stress

    Raises:
        ValueError: Si les capitaux propres ne peuvent pas etre determines

    Example:
        >>> data = load_financial_data("entreprise.json")
        >>> base = create_base_scenario(data)
        >>> print(f"Scenario base: {base.name}")
        >>> print(f"Equity: {base.equity.equity_amount:,.0f} EUR")
    """
    # Tentative de recuperation des capitaux propres
    equity_amount = None

    # Structure possible 1: balance_sheet.equity.value
    try:
        if "balance_sheet" in financial_data:
            bs = financial_data["balance_sheet"]
            if "equity" in bs:
                if isinstance(bs["equity"], dict) and "value" in bs["equity"]:
                    equity_amount = bs["equity"]["value"]
                elif isinstance(bs["equity"], (int, float)):
                    equity_amount = bs["equity"]
    except (KeyError, TypeError):
        pass

    # Structure possible 2: balance_sheet.shareholders_equity.value
    if equity_amount is None:
        try:
            if "balance_sheet" in financial_data:
                bs = financial_data["balance_sheet"]
                if "shareholders_equity" in bs:
                    if isinstance(bs["shareholders_equity"], dict):
                        equity_amount = bs["shareholders_equity"].get("value")
                    else:
                        equity_amount = bs["shareholders_equity"]
        except (KeyError, TypeError):
            pass

    # Structure possible 3: equity directement a la racine
    if equity_amount is None:
        try:
            if "equity" in financial_data:
                if isinstance(financial_data["equity"], dict):
                    equity_amount = financial_data["equity"].get("value", 0)
                else:
                    equity_amount = financial_data["equity"]
        except (KeyError, TypeError):
            pass

    # Valeur par defaut si non trouve
    if equity_amount is None:
        raise ValueError(
            "Impossible de determiner les capitaux propres. "
            "Verifiez que les donnees contiennent balance_sheet.equity, "
            "balance_sheet.shareholders_equity ou equity."
        )

    # Creation du scenario de base
    return ScenarioParameters(
        name="Base (sans financement)",
        debt=DebtParameters(
            debt_amount=0,
            interest_rate=0.0,
            loan_duration=1,  # Minimum requis
            grace_period=0,
            amortization_type="constant"
        ),
        equity=EquityParameters(
            equity_amount=float(equity_amount),
            target_roe=0.0,  # Pas d'objectif de rendement
            exit_multiple=0.0,  # Pas de sortie prevue
            holding_period=1  # Minimum requis
        ),
        growth=GrowthAssumptions(
            revenue_growth=0.0,
            ebitda_margin_evolution=0.0,
            capex_percentage=0.0,
            inflation_rate=0.0
        ),
        stress=None  # Pas de stress test
    )


__all__ = [
    "ScenarioEngine",
    "create_base_scenario",
]
