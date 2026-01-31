"""
Covenant Tracker - Suivi des covenants bancaires.

Permet de:
- Définir les covenants (Dette/EBITDA, DSCR, etc.)
- Projeter les covenants sur N années
- Détecter les violations
- Générer graphiques timeline
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class CovenantType(str, Enum):
    """Types de covenants bancaires."""
    DEBT_TO_EBITDA = "debt_to_ebitda"
    DSCR = "dscr"
    EQUITY_RATIO = "equity_ratio"
    CAPEX_LIMIT = "capex_limit"
    CUSTOM = "custom"


@dataclass
class CovenantDefinition:
    """
    Définition d'un covenant bancaire.

    Attributes:
        name: Nom du covenant
        covenant_type: Type de covenant
        threshold: Seuil à respecter
        comparison: Type de comparaison ('>=', '<=', '>', '<')
        applicable_years: Années d'application (ex: [1,2,3])
        description: Description
    """
    name: str
    covenant_type: CovenantType
    threshold: float
    comparison: str  # '>=', '<=', '>', '<'
    applicable_years: Optional[List[int]] = None
    description: str = ""

    def is_applicable(self, year: int) -> bool:
        """Vérifie si covenant applicable cette année."""
        if self.applicable_years is None:
            return True
        return year in self.applicable_years

    def is_violated(self, actual_value: float) -> bool:
        """Vérifie si covenant violé."""
        if self.comparison == ">=":
            return actual_value < self.threshold
        elif self.comparison == "<=":
            return actual_value > self.threshold
        elif self.comparison == ">":
            return actual_value <= self.threshold
        elif self.comparison == "<":
            return actual_value >= self.threshold
        return False

    def get_status(self, actual_value: float, year: int) -> str:
        """
        Retourne le statut du covenant.

        Returns:
            'PASS', 'WARNING', 'VIOLATION', 'N/A'
        """
        if not self.is_applicable(year):
            return "N/A"

        if self.is_violated(actual_value):
            return "VIOLATION"

        # Warning si proche du seuil (10% de marge)
        margin = abs(actual_value - self.threshold)
        margin_pct = (margin / self.threshold * 100) if self.threshold != 0 else 0

        if margin_pct < 10:
            return "WARNING"

        return "PASS"


class CovenantTracker:
    """
    Suit et projette les covenants bancaires sur plusieurs années.
    """

    # Covenants standards pour LBO PME
    STANDARD_COVENANTS = [
        CovenantDefinition(
            name="Dette nette / EBITDA",
            covenant_type=CovenantType.DEBT_TO_EBITDA,
            threshold=4.0,
            comparison="<=",
            description="Levier financier maximal autorisé"
        ),
        CovenantDefinition(
            name="DSCR minimum",
            covenant_type=CovenantType.DSCR,
            threshold=1.25,
            comparison=">=",
            description="Capacité de remboursement minimum"
        ),
    ]

    def __init__(self, covenants: Optional[List[CovenantDefinition]] = None):
        """
        Initialise le tracker avec des covenants.

        Args:
            covenants: Liste de covenants (ou None pour standards)
        """
        self.covenants = covenants if covenants else self.STANDARD_COVENANTS.copy()

    def add_covenant(self, covenant: CovenantDefinition) -> None:
        """Ajoute un covenant."""
        self.covenants.append(covenant)

    def project_covenant(
        self,
        covenant: CovenantDefinition,
        projections: Dict[int, Dict],
        projection_years: int = 7
    ) -> Dict:
        """
        Projette un covenant sur N années.

        Args:
            covenant: Covenant à projeter
            projections: Dict {année: métriques} avec données projetées
            projection_years: Nombre d'années

        Returns:
            Dict avec valeurs, seuils, statuts par année
        """
        years = list(range(1, projection_years + 1))
        values = []
        statuses = []
        violations = []

        for year in years:
            year_data = projections.get(year, {})

            # Extraire la valeur selon le type de covenant
            if covenant.covenant_type == CovenantType.DEBT_TO_EBITDA:
                value = year_data.get("leverage", 0)
            elif covenant.covenant_type == CovenantType.DSCR:
                value = year_data.get("dscr", 0)
            elif covenant.covenant_type == CovenantType.EQUITY_RATIO:
                value = year_data.get("equity_ratio", 0)
            else:
                value = year_data.get("custom_metric", 0)

            values.append(value)

            # Statut
            status = covenant.get_status(value, year)
            statuses.append(status)

            # Violations
            if status == "VIOLATION":
                violations.append(year)

        return {
            "covenant": covenant,
            "years": years,
            "values": values,
            "threshold": covenant.threshold,
            "statuses": statuses,
            "violations": violations,
            "has_violations": len(violations) > 0
        }

    def project_all_covenants(
        self,
        projections: Dict[int, Dict],
        projection_years: int = 7
    ) -> List[Dict]:
        """
        Projette tous les covenants.

        Args:
            projections: Dict {année: métriques}
            projection_years: Nombre d'années

        Returns:
            Liste de résultats de projection
        """
        results = []

        for covenant in self.covenants:
            result = self.project_covenant(covenant, projections, projection_years)
            results.append(result)

        return results

    def get_summary(self, projections: Dict[int, Dict]) -> Dict:
        """
        Génère un résumé des covenants.

        Returns:
            Dict avec statistiques globales
        """
        all_results = self.project_all_covenants(projections)

        total_covenants = len(all_results)
        violated_covenants = [r for r in all_results if r["has_violations"]]
        warning_covenants = []

        for result in all_results:
            if not result["has_violations"] and "WARNING" in result["statuses"]:
                warning_covenants.append(result)

        return {
            "total_covenants": total_covenants,
            "violated_count": len(violated_covenants),
            "warning_count": len(warning_covenants),
            "pass_count": total_covenants - len(violated_covenants) - len(warning_covenants),
            "violated_covenants": violated_covenants,
            "warning_covenants": warning_covenants,
            "overall_status": "VIOLATION" if violated_covenants else "WARNING" if warning_covenants else "PASS"
        }

    @staticmethod
    def generate_projections(
        baseline_data: Dict,
        lbo_structure: Dict,
        normalization_data: Dict,
        operating_assumptions: Dict,
        projection_years: int = 7
    ) -> Dict[int, Dict]:
        """
        Génère les projections financières pour N années.

        Args:
            baseline_data: Données de base
            lbo_structure: Structure LBO
            normalization_data: Données normalisées
            operating_assumptions: Hypothèses (croissance, etc.)
            projection_years: Nombre d'années

        Returns:
            Dict {année: {métriques}} avec projections
        """
        projections = {}

        # Données année 0
        ca_base = baseline_data.get("income_statement", {}).get("revenues", {}).get("net_revenue", 0)
        ebitda_base = normalization_data.get("ebitda_bank", 0)
        margin_base = (ebitda_base / ca_base * 100) if ca_base > 0 else 0

        # Dette initiale
        total_debt_initial = sum(
            layer.get("amount", 0) for layer in lbo_structure.get("debt_layers", [])
        )

        # Hypothèses
        revenue_growth_rates = operating_assumptions.get("revenue_growth_rate", [0.05] * projection_years)
        margin_evolution = operating_assumptions.get("ebitda_margin_evolution", [0.0] * projection_years)
        tax_rate = operating_assumptions.get("tax_rate", 0.25)
        bfr_pct = operating_assumptions.get("bfr_percentage_of_revenue", 18.0) / 100
        capex_pct = operating_assumptions.get("capex_maintenance_pct", 3.0) / 100

        # Projection année par année
        ca = ca_base
        ebitda = ebitda_base
        margin = margin_base
        debt_remaining = total_debt_initial

        for year in range(1, projection_years + 1):
            # Croissance CA
            growth_rate = revenue_growth_rates[year - 1] if year - 1 < len(revenue_growth_rates) else 0.05
            ca = ca * (1 + growth_rate)

            # Évolution marge
            margin_change = margin_evolution[year - 1] if year - 1 < len(margin_evolution) else 0.0
            margin = margin + margin_change

            # EBITDA
            ebitda = ca * (margin / 100)

            # BFR
            bfr = ca * bfr_pct
            delta_bfr = bfr - (ca / (1 + growth_rate) * bfr_pct)  # Variation

            # Capex
            capex = ca * capex_pct

            # IS cash
            is_cash = ebitda * tax_rate

            # FCF
            fcf = ebitda - is_cash - delta_bfr - capex

            # Service de dette (approximation)
            annual_service = 0
            for layer in lbo_structure.get("debt_layers", []):
                amount = layer.get("amount", 0)
                rate = layer.get("interest_rate", 0)
                duration = layer.get("duration_years", 7)

                if year <= duration:
                    principal_payment = amount / duration
                    interest_payment = (debt_remaining * rate)
                    annual_service += principal_payment + interest_payment

            # Remboursement dette
            debt_repayment = min(fcf, annual_service) if fcf > 0 else 0
            debt_remaining = max(0, debt_remaining - debt_repayment)

            # CFADS (simplifié)
            cfads = ebitda - is_cash - delta_bfr - capex

            # DSCR
            dscr = (cfads / annual_service) if annual_service > 0 else float('inf')

            # Dette / EBITDA
            leverage = (debt_remaining / ebitda) if ebitda > 0 else float('inf')

            # Stocker projection
            projections[year] = {
                "ca": ca,
                "ebitda": ebitda,
                "margin": margin,
                "fcf": fcf,
                "debt_remaining": debt_remaining,
                "dscr": dscr,
                "leverage": leverage,
                "annual_service": annual_service,
                "cfads": cfads,
                "is_cash": is_cash,
                "capex": capex,
                "delta_bfr": delta_bfr
            }

        return projections


# Exemple d'utilisation
if __name__ == "__main__":
    # Données de test
    test_baseline = {
        "income_statement": {
            "revenues": {"net_revenue": 8_500_000}
        }
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

    test_assumptions = {
        "revenue_growth_rate": [0.05, 0.05, 0.03, 0.03, 0.02, 0.02, 0.02],
        "ebitda_margin_evolution": [0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
        "tax_rate": 0.25,
        "bfr_percentage_of_revenue": 18.0,
        "capex_maintenance_pct": 3.0
    }

    # Générer projections
    projections = CovenantTracker.generate_projections(
        test_baseline,
        test_lbo,
        test_norm,
        test_assumptions,
        projection_years=7
    )

    # Créer tracker
    tracker = CovenantTracker()

    # Projeter covenants
    results = tracker.project_all_covenants(projections)

    print("="*60)
    print("COVENANT TRACKING - PROJECTION 7 ANS")
    print("="*60)

    for result in results:
        covenant = result["covenant"]
        print(f"\n{covenant.name}")
        print(f"Seuil: {covenant.comparison} {covenant.threshold}")
        print(f"Violations: {result['violations']}")
        print("\nAnnée | Valeur | Statut")
        print("-" * 30)

        for year, value, status in zip(result["years"], result["values"], result["statuses"]):
            status_icon = "✅" if status == "PASS" else "⚠️" if status == "WARNING" else "❌"
            print(f"  {year}   | {value:>6.2f} | {status_icon} {status}")

    # Summary
    summary = tracker.get_summary(projections)
    print("\n" + "="*60)
    print("RÉSUMÉ")
    print("="*60)
    print(f"Total covenants: {summary['total_covenants']}")
    print(f"Pass: {summary['pass_count']}")
    print(f"Warning: {summary['warning_count']}")
    print(f"Violations: {summary['violated_count']}")
    print(f"\nStatut global: {summary['overall_status']}")
