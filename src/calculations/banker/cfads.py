"""
CFADS (Cash Flow Available for Debt Service) - Norme bancaire française.

Le CFADS est le cash-flow réellement disponible pour rembourser la dette,
après avoir pris en compte:
- L'impôt sur les sociétés (IS) effectivement décaissé
- La variation du BFR (consommation ou libération de cash)
- Les investissements de maintenance (Capex)

Formule CFADS (standard bancaire français):
CFADS = EBITDA normalisé
        - IS cash (impôt décaissé)
        ± ΔBFR (variation BFR, négatif si augmentation = consommation cash)
        - Capex maintenance

Cette formule est utilisée par Bpifrance, les banques françaises et les fonds LBO
pour calculer le vrai DSCR (Debt Service Coverage Ratio).
"""

from typing import Dict, Optional
from src.calculations.base import FinancialMetric, MetricMetadata, MetricCategory, register_metric


@register_metric
class CFADS(FinancialMetric):
    """
    CFADS - Cash Flow Available for Debt Service.

    Mesure le cash-flow réellement disponible pour le service de la dette
    après IS, variation BFR et Capex maintenance.

    Formule:
    CFADS = EBITDA - IS cash ± ΔBFR - Capex maintenance

    Où:
    - EBITDA: EBITDA normalisé banque (issu du workflow de normalisation)
    - IS cash: Impôt société effectivement décaissé (EBITDA × taux IS effectif)
    - ΔBFR: Variation du BFR (positif = augmentation = consommation cash)
    - Capex maintenance: Investissements de maintien de l'outil

    Note: Ne pas confondre avec l'EBITDA equity qui intègre déjà IS et Capex
    mais pas le ΔBFR. Le CFADS est spécifiquement pour le calcul du DSCR.
    """

    metadata = MetricMetadata(
        name="cfads",
        formula_latex=r"\text{CFADS} = \text{EBITDA} - \text{IS}_{cash} \pm \Delta\text{BFR} - \text{Capex}_{maint}",
        description="Cash Flow Available for Debt Service",
        unit="euro",
        category=MetricCategory.BANKER,
        benchmark_ranges={
            "excellent": 500_000,
            "good": 300_000,
            "acceptable": 150_000,
            "risky": 50_000,
        },
        interpretation=(
            "Le CFADS représente le cash réellement disponible pour rembourser la dette. "
            "Un CFADS positif et croissant indique une bonne capacité de remboursement. "
            "Si CFADS < Service dette annuel, l'entreprise ne peut pas rembourser."
        )
    )

    def calculate(self, financial_data: Dict) -> float:
        """
        Calcule le CFADS.

        Args:
            financial_data: Dict contenant:
                - normalization.ebitda_bank: EBITDA normalisé
                - assumptions.tax_rate: Taux IS effectif (défaut 25%)
                - working_capital.bfr: BFR actuel
                - working_capital.bfr_previous: BFR année précédente
                - assumptions.capex_maintenance: Capex maintenance

        Returns:
            float: CFADS en euros
        """
        # 1. EBITDA normalisé
        ebitda = financial_data.get("normalization", {}).get("ebitda_bank", 0)

        # 2. IS cash (taux effectif × EBITDA)
        tax_rate = financial_data.get("assumptions", {}).get("tax_rate", 0.25)
        is_cash = ebitda * tax_rate

        # 3. ΔBFR (variation)
        bfr_current = financial_data.get("working_capital", {}).get("bfr", 0)
        bfr_previous = financial_data.get("working_capital", {}).get("bfr_previous", bfr_current)
        delta_bfr = bfr_current - bfr_previous  # Positif = augmentation = consommation cash

        # 4. Capex maintenance
        capex_maint = financial_data.get("assumptions", {}).get("capex_maintenance", 0)

        # 5. CFADS
        cfads = ebitda - is_cash - delta_bfr - capex_maint

        return cfads

    def get_interpretation(self, value: float) -> str:
        """
        Retourne l'interprétation de la valeur CFADS.

        Args:
            value: Valeur du CFADS

        Returns:
            str: Interprétation
        """
        if value >= 500_000:
            return (
                f"Excellent CFADS ({value:,.0f} €). "
                "Très forte capacité de remboursement de la dette. "
                "Possibilité de supporter un levier élevé."
            )
        elif value >= 300_000:
            return (
                f"Bon CFADS ({value:,.0f} €). "
                "Capacité de remboursement satisfaisante. "
                "Structure de dette solide possible."
            )
        elif value >= 150_000:
            return (
                f"CFADS acceptable ({value:,.0f} €). "
                "Capacité de remboursement limitée. "
                "Privilégier un levier modéré."
            )
        elif value >= 50_000:
            return (
                f"CFADS faible ({value:,.0f} €). "
                "Capacité de remboursement très limitée. "
                "Réduire significativement la dette ou augmenter l'equity."
            )
        else:
            return (
                f"CFADS négatif ou très faible ({value:,.0f} €). "
                "❌ CRITIQUE: Pas de cash disponible pour rembourser la dette. "
                "Montage LBO non viable en l'état."
            )


@register_metric
class DSCR_French(FinancialMetric):
    """
    DSCR (Debt Service Coverage Ratio) selon normes bancaires françaises.

    Mesure la capacité de l'entreprise à rembourser sa dette.
    Version correcte utilisant CFADS et non EBITDA brut.

    Formule:
    DSCR = CFADS / Service annuel de la dette

    Où:
    - CFADS: Cash Flow Available for Debt Service (voir métrique CFADS)
    - Service dette: Remboursement capital + Intérêts de l'année

    Interprétation:
    - DSCR > 1.5: Excellent (marge confortable)
    - DSCR 1.25-1.5: Bon (standard bancaire)
    - DSCR 1.0-1.25: Risqué (peu de marge)
    - DSCR < 1.0: Défaut (impossibilité de rembourser)

    Covenant bancaire standard: DSCR > 1.25
    Covenant Bpifrance: souvent DSCR > 1.30
    """

    metadata = MetricMetadata(
        name="dscr_french",
        formula_latex=r"\text{DSCR} = \frac{\text{CFADS}}{\text{Service dette}}",
        description="DSCR (norme bancaire française)",
        unit="ratio",
        category=MetricCategory.BANKER,
        benchmark_ranges={
            "excellent": 1.5,
            "good": 1.35,
            "acceptable": 1.25,
            "risky": 1.0,
        },
        interpretation=(
            "Le DSCR mesure le nombre de fois où le CFADS couvre le service de dette annuel. "
            "Un DSCR de 1.5 signifie que l'entreprise génère 50% de cash en plus du nécessaire "
            "pour rembourser, offrant une marge de sécurité. "
            "Covenant standard: DSCR > 1.25."
        )
    )

    def calculate(self, financial_data: Dict) -> float:
        """
        Calcule le DSCR selon la norme française.

        Args:
            financial_data: Dict contenant:
                - normalization.ebitda_bank
                - assumptions.tax_rate
                - working_capital.bfr, bfr_previous
                - assumptions.capex_maintenance
                - scenario.annual_debt_service

        Returns:
            float: DSCR (ratio)
        """
        # 1. Calculer CFADS via la métrique dédiée
        cfads_metric = CFADS()
        cfads = cfads_metric.calculate(financial_data)

        # 2. Service de dette annuel
        debt_service = financial_data.get("scenario", {}).get("annual_debt_service", 0)

        # 3. DSCR
        if debt_service == 0:
            return float('inf')  # Pas de dette = DSCR infini

        dscr = cfads / debt_service

        return dscr

    def get_interpretation(self, value: float) -> str:
        """
        Retourne l'interprétation du DSCR.

        Args:
            value: Valeur du DSCR

        Returns:
            str: Interprétation
        """
        if value == float('inf'):
            return "Pas de dette: DSCR non applicable."

        if value >= 1.5:
            return (
                f"DSCR excellent ({value:.2f}). "
                "🟢 Capacité de remboursement très confortable. "
                "Marge de sécurité de {:.0%} au-dessus du service dette.".format(value - 1)
            )
        elif value >= 1.35:
            return (
                f"DSCR bon ({value:.2f}). "
                "🟢 Capacité de remboursement satisfaisante. "
                "Conforme aux standards Bpifrance."
            )
        elif value >= 1.25:
            return (
                f"DSCR acceptable ({value:.2f}). "
                "🟡 Capacité de remboursement limite. "
                "Respecte le covenant minimum bancaire (1.25) mais peu de marge."
            )
        elif value >= 1.0:
            return (
                f"DSCR risqué ({value:.2f}). "
                "🔴 Capacité de remboursement très faible. "
                "⚠️ Sous le covenant standard: violation probable. "
                "Réduire dette ou améliorer CFADS."
            )
        else:
            return (
                f"DSCR insuffisant ({value:.2f}). "
                "🔴 ❌ CRITIQUE: Impossibilité de rembourser la dette. "
                "Le CFADS ne couvre pas le service annuel. "
                "Montage LBO non viable."
            )


# Test des métriques
if __name__ == "__main__":
    # Données de test
    test_data = {
        "normalization": {
            "ebitda_bank": 1_050_000  # EBITDA normalisé
        },
        "assumptions": {
            "tax_rate": 0.25,  # 25% IS
            "capex_maintenance": 250_000  # Capex maintenance
        },
        "working_capital": {
            "bfr": 1_530_000,  # BFR actuel (18% CA)
            "bfr_previous": 1_450_000  # BFR année précédente
        },
        "scenario": {
            "annual_debt_service": 550_000  # Service dette annuel
        }
    }

    # Test CFADS
    cfads_metric = CFADS()
    cfads_value = cfads_metric.calculate(test_data)
    print("="*60)
    print("CFADS (Cash Flow Available for Debt Service)")
    print("="*60)
    print(f"EBITDA normalisé:     1 050 000 €")
    print(f"- IS cash (25%):       -262 500 €")
    print(f"- ΔBFR:                 -80 000 € (augmentation = consommation)")
    print(f"- Capex maintenance:   -250 000 €")
    print(f"{'='*60}")
    print(f"= CFADS:               {cfads_value:>10,.0f} €")
    print(f"\nInterprétation: {cfads_metric.get_interpretation(cfads_value)}")

    # Test DSCR
    print("\n" + "="*60)
    print("DSCR (Debt Service Coverage Ratio)")
    print("="*60)
    dscr_metric = DSCR_French()
    dscr_value = dscr_metric.calculate(test_data)
    print(f"CFADS:                 {cfads_value:>10,.0f} €")
    print(f"Service dette annuel:  {test_data['scenario']['annual_debt_service']:>10,.0f} €")
    print(f"{'='*60}")
    print(f"= DSCR:                {dscr_value:>10.2f}")
    print(f"\nInterprétation: {dscr_metric.get_interpretation(dscr_value)}")

    # Comparaison avec ancien DSCR (EBITDA / Dette)
    print("\n" + "="*60)
    print("COMPARAISON: Ancien DSCR vs Nouveau DSCR")
    print("="*60)
    old_dscr = test_data["normalization"]["ebitda_bank"] / test_data["scenario"]["annual_debt_service"]
    print(f"Ancien DSCR (EBITDA/Dette):     {old_dscr:.2f} ❌ INCORRECT")
    print(f"Nouveau DSCR (CFADS/Dette):     {dscr_value:.2f} ✅ CORRECT")
    print(f"Différence:                     {old_dscr - dscr_value:.2f}")
    print(f"\n⚠️ L'ancien DSCR SURESTIME la capacité de remboursement!")
    print(f"   Il ignore IS, BFR et Capex → vision trop optimiste")
