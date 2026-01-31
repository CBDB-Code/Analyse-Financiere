"""
Normaliseur de données comptables.

Gère le workflow:
EBE → Retraitements → EBITDA banque → EBITDA equity
"""

from typing import Dict, List
from src.core.models_v3 import (
    NormalizationData,
    Adjustment,
    AdjustmentCategory
)


class DataNormalizer:
    """
    Normalise les données comptables pour analyse LBO.

    Le processus de normalisation permet de passer des données
    comptables brutes (liasse fiscale) à des données "banque-ready"
    exploitables pour l'analyse de viabilité financière.
    """

    @staticmethod
    def calculate_ebe(financial_data: Dict) -> float:
        """
        Calcule l'EBE (Excédent Brut d'Exploitation).

        Formule:
        EBE = CA - Achats consommés - Charges externes
              - Impôts & taxes - Charges de personnel

        Args:
            financial_data: Dictionnaire des données financières

        Returns:
            float: EBE calculé
        """
        # Chiffre d'affaires
        ca = financial_data.get("income_statement", {}).get("revenues", {}).get("net_revenue", 0)

        # Charges
        operating_expenses = financial_data.get("income_statement", {}).get("operating_expenses", {})

        purchases = operating_expenses.get("purchases_of_goods", 0)
        raw_materials = operating_expenses.get("purchases_of_raw_materials", 0)
        inventory_variation = operating_expenses.get("inventory_variation", 0)
        external_charges = operating_expenses.get("external_charges", 0)
        taxes_duties = operating_expenses.get("taxes_and_duties", 0)
        personnel_costs = operating_expenses.get("personnel_costs", 0)

        # Si personnel_costs agrégé pas disponible, calculer
        if personnel_costs == 0:
            wages = operating_expenses.get("wages_and_salaries", 0)
            social = operating_expenses.get("social_charges", 0)
            personnel_costs = wages + social

        ebe = (
            ca
            - purchases
            - raw_materials
            - inventory_variation
            - external_charges
            - taxes_duties
            - personnel_costs
        )

        return ebe

    @staticmethod
    def create_normalization_data(
        financial_data: Dict,
        custom_adjustments: List[Adjustment] = None
    ) -> NormalizationData:
        """
        Crée un objet NormalizationData avec calculs initiaux.

        Args:
            financial_data: Données financières brutes
            custom_adjustments: Liste d'ajustements personnalisés

        Returns:
            NormalizationData avec EBE calculé
        """
        ebe = DataNormalizer.calculate_ebe(financial_data)

        normalization = NormalizationData(
            ebe=ebe,
            adjustments=custom_adjustments or []
        )

        # Log initial
        normalization.audit_log.append(f"EBE initial calculé: {ebe:,.0f} €")

        return normalization

    @staticmethod
    def suggest_adjustments(financial_data: Dict) -> List[Adjustment]:
        """
        Suggère des ajustements basés sur l'analyse des données.

        Détecte automatiquement:
        - Rémunération dirigeant potentiellement excessive
        - Charges exceptionnelles
        - Crédit-bail à retraiter

        Args:
            financial_data: Données financières

        Returns:
            Liste d'ajustements suggérés
        """
        suggestions = []

        # 1. Détection rémunération dirigeant excessive
        # (heuristique: si charges personnel > 40% CA, suggérer retraitement)
        ca = financial_data.get("income_statement", {}).get("revenues", {}).get("net_revenue", 0)
        personnel = financial_data.get("income_statement", {}).get("operating_expenses", {}).get("personnel_costs", 0)

        if ca > 0 and personnel / ca > 0.40:
            excessive_amount = personnel - (ca * 0.35)  # Ramener à 35%
            if excessive_amount > 0:
                suggestions.append(
                    Adjustment(
                        name="Rémunération dirigeant excessive",
                        amount=excessive_amount,
                        category=AdjustmentCategory.PERSONNEL,
                        description=f"Charges de personnel ({personnel/ca*100:.1f}% CA) au-dessus de la norme (35%). Retraitement suggéré."
                    )
                )

        # 2. Charges exceptionnelles
        exceptional = financial_data.get("income_statement", {}).get("exceptional_result", {})
        exceptional_expense = exceptional.get("total_exceptional_expense", 0)

        if exceptional_expense > 0:
            suggestions.append(
                Adjustment(
                    name="Charges exceptionnelles",
                    amount=exceptional_expense,
                    category=AdjustmentCategory.EXCEPTIONAL,
                    description="Charges exceptionnelles non récurrentes à neutraliser"
                )
            )

        return suggestions

    @staticmethod
    def apply_normalization(
        normalization: NormalizationData,
        tax_rate: float = 0.25,
        capex_maintenance: float = 0.0
    ) -> NormalizationData:
        """
        Applique la normalisation complète.

        Calcule:
        1. EBITDA banque (EBE + ajustements)
        2. EBITDA equity (EBITDA banque - IS - Capex)

        Args:
            normalization: Données de normalisation
            tax_rate: Taux d'IS effectif
            capex_maintenance: Capex de maintenance annuel

        Returns:
            NormalizationData mis à jour
        """
        # Calcul EBITDA banque
        normalization.calculate_ebitda_bank()

        # Calcul EBITDA equity
        normalization.calculate_ebitda_equity(tax_rate, capex_maintenance)

        return normalization


# Exemple d'utilisation:
if __name__ == "__main__":
    # Données de test
    test_data = {
        "income_statement": {
            "revenues": {"net_revenue": 8_500_000},
            "operating_expenses": {
                "purchases_of_goods": 2_000_000,
                "purchases_of_raw_materials": 1_500_000,
                "inventory_variation": -50_000,
                "external_charges": 1_200_000,
                "taxes_and_duties": 150_000,
                "wages_and_salaries": 2_000_000,
                "social_charges": 800_000,
            }
        }
    }

    # Créer normalisation
    normalizer = DataNormalizer()
    norm_data = normalizer.create_normalization_data(test_data)
    print(f"EBE: {norm_data.ebe:,.0f} €")

    # Ajouter ajustements
    norm_data.adjustments.append(
        Adjustment(
            name="Loyers crédit-bail",
            amount=150_000,
            category=AdjustmentCategory.RENT,
            description="Retraitement loyers crédit-bail"
        )
    )

    # Appliquer normalisation
    normalizer.apply_normalization(norm_data, tax_rate=0.25, capex_maintenance=250_000)

    print(f"EBITDA banque: {norm_data.ebitda_bank:,.0f} €")
    print(f"EBITDA equity: {norm_data.ebitda_equity:,.0f} €")
    print("\nAudit log:")
    for log in norm_data.audit_log:
        print(f"  - {log}")
