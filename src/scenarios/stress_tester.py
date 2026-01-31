"""
Module de stress tests pour analyse de viabilité LBO.

Simule différents scénarios de crise pour évaluer la robustesse
du montage financier:
- Baisse de CA
- Compression de marge
- Hausse des taux
- Augmentation BFR
- Scénarios combinés
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import copy


class StressScenarioType(str, Enum):
    """Types de scénarios de stress."""
    NOMINAL = "nominal"
    REVENUE_DOWN_10 = "revenue_down_10"
    REVENUE_DOWN_20 = "revenue_down_20"
    MARGIN_DOWN_2PTS = "margin_down_2pts"
    RATES_UP_200BPS = "rates_up_200bps"
    BFR_UP_5PTS = "bfr_up_5pts"
    COMBINED_CRISIS = "combined_crisis"


@dataclass
class StressScenario:
    """
    Scénario de stress test.

    Attributes:
        name: Nom du scénario
        scenario_type: Type de scénario
        description: Description détaillée
        revenue_shock: Choc sur CA (ex: -0.10 pour -10%)
        margin_shock: Choc sur marge EBITDA en points (ex: -2.0)
        interest_rate_shock: Choc sur taux en points de base (ex: 200 pour +2%)
        bfr_shock: Choc sur BFR en points de CA (ex: 5.0 pour +5 pts)
    """
    name: str
    scenario_type: StressScenarioType
    description: str
    revenue_shock: float = 0.0
    margin_shock: float = 0.0
    interest_rate_shock: float = 0.0  # en bps
    bfr_shock: float = 0.0  # en points de %


class StressTester:
    """
    Teste la robustesse d'un montage LBO sous stress.

    Applique différents scénarios de crise et calcule les métriques
    clés pour identifier les points de rupture.
    """

    # Scénarios prédéfinis
    SCENARIOS = [
        StressScenario(
            name="Nominal",
            scenario_type=StressScenarioType.NOMINAL,
            description="Scénario de base sans choc"
        ),
        StressScenario(
            name="CA -10%",
            scenario_type=StressScenarioType.REVENUE_DOWN_10,
            description="Baisse du chiffre d'affaires de 10%",
            revenue_shock=-0.10
        ),
        StressScenario(
            name="CA -20%",
            scenario_type=StressScenarioType.REVENUE_DOWN_20,
            description="Baisse du chiffre d'affaires de 20%",
            revenue_shock=-0.20
        ),
        StressScenario(
            name="Marge -2pts",
            scenario_type=StressScenarioType.MARGIN_DOWN_2PTS,
            description="Compression de la marge EBITDA de 2 points",
            margin_shock=-2.0
        ),
        StressScenario(
            name="Taux +200bps",
            scenario_type=StressScenarioType.RATES_UP_200BPS,
            description="Hausse des taux d'intérêt de 200 points de base (+2%)",
            interest_rate_shock=200
        ),
        StressScenario(
            name="BFR +5pts",
            scenario_type=StressScenarioType.BFR_UP_5PTS,
            description="Augmentation du BFR de 5 points de CA",
            bfr_shock=5.0
        ),
        StressScenario(
            name="Crise combinée",
            scenario_type=StressScenarioType.COMBINED_CRISIS,
            description="CA -15%, Marge -1pt, Taux +100bps",
            revenue_shock=-0.15,
            margin_shock=-1.0,
            interest_rate_shock=100
        ),
    ]

    @staticmethod
    def apply_stress_scenario(
        baseline_data: Dict,
        lbo_structure: Dict,
        normalization_data: Dict,
        scenario: StressScenario
    ) -> Dict:
        """
        Applique un scénario de stress aux données.

        Args:
            baseline_data: Données financières de base
            lbo_structure: Structure LBO
            normalization_data: Données de normalisation
            scenario: Scénario de stress à appliquer

        Returns:
            Dict avec données stressées et métriques recalculées
        """
        # Copie profonde pour ne pas modifier les originaux
        stressed_data = copy.deepcopy(baseline_data)
        stressed_lbo = copy.deepcopy(lbo_structure)
        stressed_norm = copy.deepcopy(normalization_data)

        # 1. Choc sur CA
        if scenario.revenue_shock != 0:
            current_ca = stressed_data.get("income_statement", {}).get("revenues", {}).get("net_revenue", 0)
            new_ca = current_ca * (1 + scenario.revenue_shock)
            stressed_data["income_statement"]["revenues"]["net_revenue"] = new_ca
            stressed_data["income_statement"]["revenues"]["total"] = new_ca

        # 2. Choc sur marge EBITDA
        current_ebitda = stressed_norm.get("ebitda_bank", 0)
        current_ca = stressed_data.get("income_statement", {}).get("revenues", {}).get("net_revenue", 1)

        if scenario.margin_shock != 0:
            # Choc sur marge = choc sur EBITDA
            margin_impact = (current_ca * scenario.margin_shock / 100)
            stressed_norm["ebitda_bank"] = max(0, current_ebitda + margin_impact)

        # Si choc CA, ajuster aussi l'EBITDA proportionnellement (hors choc marge)
        if scenario.revenue_shock != 0:
            # Hypothèse: EBITDA varie plus que CA (levier opérationnel)
            # CA -10% → EBITDA -15% environ
            ebitda_elasticity = 1.5
            ebitda_variation = scenario.revenue_shock * ebitda_elasticity
            stressed_norm["ebitda_bank"] = max(0, current_ebitda * (1 + ebitda_variation))

        # 3. Choc sur taux d'intérêt
        if scenario.interest_rate_shock != 0:
            rate_increase = scenario.interest_rate_shock / 10000  # bps to decimal
            for layer in stressed_lbo.get("debt_layers", []):
                layer["interest_rate"] = layer.get("interest_rate", 0) + rate_increase

        # 4. Choc sur BFR
        if scenario.bfr_shock != 0:
            # Augmentation BFR = consommation de cash
            current_bfr_pct = stressed_data.get("working_capital", {}).get("bfr_pct", 18.0)
            stressed_data.setdefault("working_capital", {})["bfr_pct"] = current_bfr_pct + scenario.bfr_shock

        # Calcul des métriques stressées
        metrics = StressTester._calculate_stress_metrics(
            stressed_data,
            stressed_lbo,
            stressed_norm
        )

        return {
            "scenario": scenario,
            "stressed_data": stressed_data,
            "stressed_lbo": stressed_lbo,
            "stressed_norm": stressed_norm,
            "metrics": metrics
        }

    @staticmethod
    def _calculate_stress_metrics(
        data: Dict,
        lbo: Dict,
        norm: Dict
    ) -> Dict:
        """
        Calcule les métriques clés pour un scénario stressé.

        Returns:
            Dict avec DSCR, Dette/EBITDA, FCF, etc.
        """
        ebitda = norm.get("ebitda_bank", 0)
        ca = data.get("income_statement", {}).get("revenues", {}).get("net_revenue", 1)

        # Dette totale
        total_debt = sum(layer.get("amount", 0) for layer in lbo.get("debt_layers", []))

        # Service de dette (approximation)
        annual_service = 0
        for layer in lbo.get("debt_layers", []):
            amount = layer.get("amount", 0)
            rate = layer.get("interest_rate", 0)
            duration = layer.get("duration_years", 7)

            # Service annuel moyen = capital + intérêts
            principal = amount / duration
            interest = amount * rate * 0.5  # Moyenne sur la période
            annual_service += principal + interest

        # Paramètres pour calcul CFADS
        tax_rate = 0.25
        bfr_pct = data.get("working_capital", {}).get("bfr_pct", 18.0)
        delta_bfr = ca * (bfr_pct / 100) * 0.1  # Approximation variation
        capex = ca * 0.03  # 3% CA

        # CFADS (Cash Flow Available for Debt Service) - Formule correcte
        # CFADS = EBITDA - IS cash ± ΔBFR - Capex maintenance
        is_cash = ebitda * tax_rate
        cfads = ebitda - is_cash - delta_bfr - capex

        # DSCR correct (norme bancaire française)
        dscr = (cfads / annual_service) if annual_service > 0 else float('inf')

        # Dette / EBITDA
        leverage = (total_debt / ebitda) if ebitda > 0 else float('inf')

        # Marge EBITDA
        margin = (ebitda / ca * 100) if ca > 0 else 0

        # FCF approximatif (année 3)
        # FCF = CFADS - Service dette
        fcf_year3 = cfads - annual_service

        return {
            "dscr_min": dscr,
            "leverage": leverage,
            "margin": margin,
            "fcf_year3": fcf_year3,
            "ebitda": ebitda,
            "cfads": cfads,
            "ca": ca,
            "annual_service": annual_service
        }

    @staticmethod
    def run_all_scenarios(
        baseline_data: Dict,
        lbo_structure: Dict,
        normalization_data: Dict
    ) -> List[Dict]:
        """
        Exécute tous les scénarios de stress prédéfinis.

        Args:
            baseline_data: Données financières de base
            lbo_structure: Structure LBO
            normalization_data: Données de normalisation

        Returns:
            Liste de résultats pour chaque scénario
        """
        results = []

        for scenario in StressTester.SCENARIOS:
            result = StressTester.apply_stress_scenario(
                baseline_data,
                lbo_structure,
                normalization_data,
                scenario
            )
            results.append(result)

        return results

    @staticmethod
    def generate_sensitivity_matrix(
        baseline_data: Dict,
        lbo_structure: Dict,
        normalization_data: Dict,
        metric: str = "dscr_min"
    ) -> Dict:
        """
        Génère une matrice de sensibilité CA x Marge.

        Args:
            baseline_data: Données de base
            lbo_structure: Structure LBO
            normalization_data: Données normalisation
            metric: Métrique à analyser ('dscr_min', 'leverage', etc.)

        Returns:
            Dict avec matrix (rows x cols) et labels
        """
        # Plages de variation
        ca_variations = [-20, -10, 0, 10, 20]  # %
        margin_variations = [-4, -2, 0, 2, 4]  # points

        matrix = []

        for margin_var in margin_variations:
            row = []
            for ca_var in ca_variations:
                # Créer scénario combiné
                scenario = StressScenario(
                    name=f"CA {ca_var:+d}%, Marge {margin_var:+d}pts",
                    scenario_type=StressScenarioType.COMBINED_CRISIS,
                    description="Scénario de sensibilité",
                    revenue_shock=ca_var / 100,
                    margin_shock=margin_var
                )

                # Appliquer stress
                result = StressTester.apply_stress_scenario(
                    baseline_data,
                    lbo_structure,
                    normalization_data,
                    scenario
                )

                # Extraire métrique
                value = result["metrics"].get(metric, 0)
                row.append(value)

            matrix.append(row)

        return {
            "matrix": matrix,
            "ca_labels": [f"{v:+d}%" for v in ca_variations],
            "margin_labels": [f"{v:+d}pts" for v in margin_variations],
            "metric": metric
        }

    @staticmethod
    def get_status_from_metrics(metrics: Dict) -> str:
        """
        Détermine le statut GO/WATCH/NO-GO à partir des métriques.

        Args:
            metrics: Dict des métriques calculées

        Returns:
            'GO', 'WATCH', ou 'NO-GO'
        """
        dscr = metrics.get("dscr_min", 0)
        leverage = metrics.get("leverage", float('inf'))
        margin = metrics.get("margin", 0)
        fcf = metrics.get("fcf_year3", 0)

        # Critères NO-GO
        if dscr < 1.0:
            return "NO-GO"
        if leverage > 6.0:
            return "NO-GO"
        if margin < 5.0:
            return "NO-GO"
        if fcf < -100_000:
            return "NO-GO"

        # Critères WATCH
        if dscr < 1.25:
            return "WATCH"
        if leverage > 4.5:
            return "WATCH"
        if margin < 10.0:
            return "WATCH"
        if fcf < 50_000:
            return "WATCH"

        # Sinon GO
        return "GO"


# Exemple d'utilisation
if __name__ == "__main__":
    # Données de test
    test_baseline = {
        "income_statement": {
            "revenues": {"net_revenue": 8_500_000, "total": 8_500_000}
        },
        "working_capital": {"bfr_pct": 18.0}
    }

    test_lbo = {
        "debt_layers": [
            {"name": "Senior", "amount": 3_000_000, "interest_rate": 0.045, "duration_years": 7},
            {"name": "Bpifrance", "amount": 500_000, "interest_rate": 0.03, "duration_years": 8}
        ]
    }

    test_norm = {
        "ebitda_bank": 1_050_000
    }

    # Test stress CA -10%
    scenario = StressTester.SCENARIOS[1]  # CA -10%
    result = StressTester.apply_stress_scenario(test_baseline, test_lbo, test_norm, scenario)

    print(f"Scénario: {scenario.name}")
    print(f"DSCR: {result['metrics']['dscr_min']:.2f}")
    print(f"Dette/EBITDA: {result['metrics']['leverage']:.2f}x")
    print(f"Statut: {StressTester.get_status_from_metrics(result['metrics'])}")

    # Test tous scénarios
    print("\n" + "="*50)
    print("TOUS LES SCÉNARIOS")
    print("="*50)

    all_results = StressTester.run_all_scenarios(test_baseline, test_lbo, test_norm)
    for res in all_results:
        scenario = res["scenario"]
        metrics = res["metrics"]
        status = StressTester.get_status_from_metrics(metrics)

        print(f"\n{scenario.name:<20} | DSCR: {metrics['dscr_min']:>5.2f} | Dette/EB: {metrics['leverage']:>4.1f}x | {status}")
