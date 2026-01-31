"""
Moteur de Décision pour Acquisitions LBO.

Analyse les métriques et génère une recommandation:
- GO: Acquisition recommandée
- WATCH: Dossier acceptable avec conditions
- NO-GO: Acquisition déconseillée

Basé sur 5 métriques décisives + algorithme de scoring.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from src.core.models_v3 import (
    Decision,
    DecisionCriteria,
    AcquisitionDecision
)


@dataclass
class DecisionRule:
    """
    Règle de décision pour un critère.

    Attributes:
        metric_name: Nom de la métrique
        display_name: Nom affiché
        threshold_excellent: Seuil pour score 100
        threshold_good: Seuil pour score 80
        threshold_acceptable: Seuil pour score 50
        higher_is_better: True si valeur élevée = meilleur
        weight: Poids dans le score global (1.0 = normal, 2.0 = double poids)
    """
    metric_name: str
    display_name: str
    threshold_excellent: float
    threshold_good: float
    threshold_acceptable: float
    higher_is_better: bool = True
    weight: float = 1.0


class DecisionEngine:
    """
    Moteur de décision pour acquisitions LBO.

    Évalue un dossier selon 5 critères décisifs et produit
    une recommandation GO/WATCH/NO-GO avec justification.
    """

    # Les 5 métriques décisives selon référentiel business
    DECISIVE_METRICS = [
        DecisionRule(
            metric_name="dscr_min",
            display_name="DSCR minimum (7 ans)",
            threshold_excellent=1.5,
            threshold_good=1.35,
            threshold_acceptable=1.25,
            higher_is_better=True,
            weight=2.0  # Double poids: critère le plus important
        ),
        DecisionRule(
            metric_name="leverage",
            display_name="Dette nette / EBITDA",
            threshold_excellent=3.5,
            threshold_good=4.0,
            threshold_acceptable=4.5,
            higher_is_better=False,  # Plus bas = meilleur
            weight=1.5  # Poids élevé
        ),
        DecisionRule(
            metric_name="margin",
            display_name="Marge EBITDA (%)",
            threshold_excellent=15.0,
            threshold_good=12.0,
            threshold_acceptable=8.0,
            higher_is_better=True,
            weight=1.0
        ),
        DecisionRule(
            metric_name="ebitda_to_fcf_conversion",
            display_name="Conversion EBITDA → FCF (%)",
            threshold_excellent=40.0,
            threshold_good=30.0,
            threshold_acceptable=20.0,
            higher_is_better=True,
            weight=1.0
        ),
        DecisionRule(
            metric_name="fcf_positive_year",
            display_name="FCF positif dès année",
            threshold_excellent=1.0,
            threshold_good=2.0,
            threshold_acceptable=3.0,
            higher_is_better=False,  # Plus tôt = meilleur
            weight=1.0
        ),
    ]

    @staticmethod
    def evaluate_criterion(
        rule: DecisionRule,
        actual_value: float
    ) -> DecisionCriteria:
        """
        Évalue un critère individuel.

        Args:
            rule: Règle de décision
            actual_value: Valeur réelle obtenue

        Returns:
            DecisionCriteria avec score calculé
        """
        criteria = DecisionCriteria(
            name=rule.display_name,
            metric_name=rule.metric_name,
            actual_value=actual_value,
            threshold_excellent=rule.threshold_excellent,
            threshold_good=rule.threshold_good,
            threshold_acceptable=rule.threshold_acceptable,
            weight=rule.weight
        )

        # Calcul du score
        criteria.calculate_score(higher_is_better=rule.higher_is_better)

        return criteria

    @staticmethod
    def extract_metrics(
        projections: Dict[int, Dict],
        normalization_data: Dict,
        baseline_data: Dict
    ) -> Dict[str, float]:
        """
        Extrait les métriques nécessaires à la décision.

        Args:
            projections: Projections financières sur N années
            normalization_data: Données normalisées
            baseline_data: Données de base

        Returns:
            Dict des métriques clés
        """
        # DSCR minimum sur 7 ans
        dscr_values = [projections[y].get("dscr", 0) for y in range(1, 8) if y in projections]
        dscr_min = min(dscr_values) if dscr_values else 0

        # Dette/EBITDA année 1
        leverage = projections.get(1, {}).get("leverage", 0)

        # Marge EBITDA
        ca = baseline_data.get("income_statement", {}).get("revenues", {}).get("net_revenue", 1)
        ebitda = normalization_data.get("ebitda_bank", 0)
        margin = (ebitda / ca * 100) if ca > 0 else 0

        # Conversion EBITDA → FCF (moyenne 3 premières années)
        fcf_year1 = projections.get(1, {}).get("fcf", 0)
        fcf_year2 = projections.get(2, {}).get("fcf", 0)
        fcf_year3 = projections.get(3, {}).get("fcf", 0)
        avg_fcf = (fcf_year1 + fcf_year2 + fcf_year3) / 3

        ebitda_avg = (
            projections.get(1, {}).get("ebitda", 0) +
            projections.get(2, {}).get("ebitda", 0) +
            projections.get(3, {}).get("ebitda", 0)
        ) / 3

        conversion = (avg_fcf / ebitda_avg * 100) if ebitda_avg > 0 else 0

        # FCF positif dès quelle année
        fcf_positive_year = 10  # Par défaut jamais
        for year in range(1, 8):
            if year in projections and projections[year].get("fcf", 0) > 0:
                fcf_positive_year = year
                break

        return {
            "dscr_min": dscr_min,
            "leverage": leverage,
            "margin": margin,
            "ebitda_to_fcf_conversion": conversion,
            "fcf_positive_year": fcf_positive_year
        }

    @staticmethod
    def make_decision(
        projections: Dict[int, Dict],
        normalization_data: Dict,
        baseline_data: Dict,
        scenario_id: Optional[str] = None
    ) -> AcquisitionDecision:
        """
        Prend la décision d'acquisition finale.

        Args:
            projections: Projections financières
            normalization_data: Données normalisées
            baseline_data: Données de base
            scenario_id: ID du scénario

        Returns:
            AcquisitionDecision complète avec recommandations
        """
        # Extraire métriques
        metrics = DecisionEngine.extract_metrics(
            projections,
            normalization_data,
            baseline_data
        )

        # Évaluer chaque critère
        criteria_list = []

        for rule in DecisionEngine.DECISIVE_METRICS:
            actual_value = metrics.get(rule.metric_name, 0)
            criterion = DecisionEngine.evaluate_criterion(rule, actual_value)
            criteria_list.append(criterion)

        # Créer décision à partir des critères
        decision = AcquisitionDecision.from_criteria(
            criteria=criteria_list,
            scenario_id=scenario_id
        )

        # Ajouter recommandations spécifiques supplémentaires
        DecisionEngine._enrich_recommendations(decision, metrics, projections)

        return decision

    @staticmethod
    def _enrich_recommendations(
        decision: AcquisitionDecision,
        metrics: Dict,
        projections: Dict[int, Dict]
    ) -> None:
        """
        Enrichit les recommandations avec analyses détaillées.

        Args:
            decision: Décision à enrichir (modifié in-place)
            metrics: Métriques calculées
            projections: Projections
        """
        # Analyse DSCR
        dscr_min = metrics.get("dscr_min", 0)
        if dscr_min < 1.35:
            if dscr_min < 1.25:
                decision.recommendations.append(
                    "🔴 CRITIQUE: DSCR trop faible. Réduire dette de 15-20% ou augmenter equity."
                )
            else:
                decision.recommendations.append(
                    "⚠️ DSCR limite: Négocier covenant DSCR trimestriel pour surveillance rapprochée."
                )

        # Analyse Dette/EBITDA
        leverage = metrics.get("leverage", 0)
        if leverage > 4.0:
            decision.recommendations.append(
                f"⚠️ Levier élevé ({leverage:.1f}x): Envisager crédit vendeur ou augmenter equity."
            )

        # Analyse Marge
        margin = metrics.get("margin", 0)
        if margin < 12.0:
            decision.recommendations.append(
                f"📊 Marge faible ({margin:.1f}%): Identifier leviers amélioration (prix, mix, coûts)."
            )
            if margin < 8.0:
                decision.deal_breakers.append(
                    f"❌ Marge EBITDA trop faible ({margin:.1f}%) pour supporter LBO."
                )

        # Analyse FCF
        fcf_year = metrics.get("fcf_positive_year", 10)
        if fcf_year > 2:
            decision.warnings.append(
                f"⏱️ FCF positif tardif (année {fcf_year}): Prévoir covenant de cash minimum."
            )

        # Analyse évolution dette
        debt_year1 = projections.get(1, {}).get("debt_remaining", 0)
        debt_year3 = projections.get(3, {}).get("debt_remaining", 0)
        debt_reduction = ((debt_year1 - debt_year3) / debt_year1 * 100) if debt_year1 > 0 else 0

        if debt_reduction < 15:
            decision.warnings.append(
                f"💰 Amortissement dette lent ({debt_reduction:.0f}% en 3 ans): Vérifier capacité sortie."
            )

        # Recommandations positives si GO
        if decision.decision == Decision.GO:
            decision.recommendations.insert(
                0,
                "✅ Dossier solide: Tous les critères décisifs sont au vert."
            )
            decision.recommendations.append(
                "💡 Suggestion: Négocier clause d'earn-out pour optimiser prix."
            )

    @staticmethod
    def get_decision_color(decision: Decision) -> str:
        """Retourne la couleur associée à la décision."""
        return {
            Decision.GO: "green",
            Decision.WATCH: "orange",
            Decision.NO_GO: "red"
        }.get(decision, "gray")

    @staticmethod
    def get_decision_icon(decision: Decision) -> str:
        """Retourne l'icône associée à la décision."""
        return {
            Decision.GO: "🟢",
            Decision.WATCH: "🟡",
            Decision.NO_GO: "🔴"
        }.get(decision, "⚪")


# Exemple d'utilisation
if __name__ == "__main__":
    # Import du covenant tracker pour générer projections
    from src.calculations.covenant_tracker import CovenantTracker

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
        "revenue_growth_rate": [0.05] * 7,
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
        test_assumptions
    )

    # Prendre décision
    decision = DecisionEngine.make_decision(
        projections,
        test_norm,
        test_baseline,
        scenario_id="test_scenario_1"
    )

    # Afficher résultat
    print("="*70)
    print(f"DÉCISION D'ACQUISITION: {DecisionEngine.get_decision_icon(decision.decision)} {decision.decision.value.upper()}")
    print("="*70)
    print(f"\nScore global: {decision.overall_score}/100")

    print("\n" + "─"*70)
    print("CRITÈRES ÉVALUÉS")
    print("─"*70)

    for criterion in decision.criteria:
        icon = "🟢" if criterion.status == "PASS" else "🟡" if criterion.status == "WARNING" else "🔴"
        print(f"{icon} {criterion.name:<30} {criterion.actual_value:>8.2f} (seuil: {criterion.threshold_good:.2f}) → Score: {criterion.score}/100")

    if decision.deal_breakers:
        print("\n" + "─"*70)
        print("❌ PROBLÈMES BLOQUANTS")
        print("─"*70)
        for db in decision.deal_breakers:
            print(f"  {db}")

    if decision.warnings:
        print("\n" + "─"*70)
        print("⚠️ POINTS D'ATTENTION")
        print("─"*70)
        for warning in decision.warnings:
            print(f"  {warning}")

    if decision.recommendations:
        print("\n" + "─"*70)
        print("💡 RECOMMANDATIONS")
        print("─"*70)
        for rec in decision.recommendations:
            print(f"  {rec}")

    print("\n" + "="*70)
    print(f"Décision prise le: {decision.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
