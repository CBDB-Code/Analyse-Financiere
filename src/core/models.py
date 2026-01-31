"""
Modèles Pydantic pour représenter une liasse fiscale française complète.

Ce module contient tous les modèles de données pour:
- Le bilan (actif et passif)
- Le compte de résultat
- Le tableau des flux de trésorerie
- Les annexes et métadonnées

Conforme aux normes comptables françaises (PCG).
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# CLASSE DE BASE
# =============================================================================

class FinancialField(BaseModel):
    """
    Représente un champ financier individuel de la liasse fiscale.

    Chaque champ correspond à une case du formulaire fiscal avec son code
    (ex: AA, BH, FC) et sa valeur numérique.
    """

    code: str = Field(
        ...,
        description="Code du champ fiscal (ex: 'AA', 'BH', 'FC')",
        min_length=1,
        max_length=10
    )
    value: float = Field(
        ...,
        description="Valeur numérique du champ en euros"
    )

    @field_validator('value')
    @classmethod
    def validate_value_is_number(cls, v: float) -> float:
        """Vérifie que la valeur est un nombre valide."""
        if not isinstance(v, (int, float)):
            raise ValueError("La valeur doit être un nombre")
        if v != v:  # Check for NaN
            raise ValueError("La valeur ne peut pas être NaN")
        return float(v)


# =============================================================================
# MODÈLES DU BILAN - ACTIF (Balance Sheet - Assets)
# =============================================================================

class FixedAssets(BaseModel):
    """
    Immobilisations (actif immobilisé).

    Comprend les immobilisations incorporelles, corporelles et financières
    qui constituent les investissements à long terme de l'entreprise.
    """

    intangible_assets: float = Field(
        default=0.0,
        description="Immobilisations incorporelles (brevets, fonds de commerce, logiciels)",
        ge=0
    )
    tangible_assets: float = Field(
        default=0.0,
        description="Immobilisations corporelles (terrains, constructions, matériel)",
        ge=0
    )
    financial_assets: float = Field(
        default=0.0,
        description="Immobilisations financières (participations, prêts, dépôts)",
        ge=0
    )
    total: float = Field(
        default=0.0,
        description="Total de l'actif immobilisé"
    )

    @model_validator(mode='after')
    def calculate_total(self) -> 'FixedAssets':
        """Calcule et vérifie le total des immobilisations."""
        calculated_total = (
            self.intangible_assets +
            self.tangible_assets +
            self.financial_assets
        )
        if self.total == 0.0:
            self.total = calculated_total
        return self


class CurrentAssets(BaseModel):
    """
    Actif circulant.

    Comprend les éléments d'actif destinés à être transformés en liquidités
    dans le cycle d'exploitation normal de l'entreprise.
    """

    inventory: float = Field(
        default=0.0,
        description="Stocks et en-cours (matières premières, produits finis)",
        ge=0
    )
    trade_receivables: float = Field(
        default=0.0,
        description="Créances clients et comptes rattachés",
        ge=0
    )
    other_receivables: float = Field(
        default=0.0,
        description="Autres créances (fiscales, sociales, diverses)",
        ge=0
    )
    prepaid_expenses: float = Field(
        default=0.0,
        description="Charges constatées d'avance",
        ge=0
    )
    marketable_securities: float = Field(
        default=0.0,
        description="Valeurs mobilières de placement",
        ge=0
    )
    cash: float = Field(
        default=0.0,
        description="Disponibilités (caisse, banque)",
        ge=0
    )
    total: float = Field(
        default=0.0,
        description="Total de l'actif circulant"
    )

    @model_validator(mode='after')
    def calculate_total(self) -> 'CurrentAssets':
        """Calcule et vérifie le total de l'actif circulant."""
        calculated_total = (
            self.inventory +
            self.trade_receivables +
            self.other_receivables +
            self.prepaid_expenses +
            self.marketable_securities +
            self.cash
        )
        if self.total == 0.0:
            self.total = calculated_total
        return self


class Assets(BaseModel):
    """
    Actif total du bilan.

    Regroupe l'actif immobilisé et l'actif circulant pour former
    le total de l'actif du bilan.
    """

    fixed_assets: FixedAssets = Field(
        default_factory=FixedAssets,
        description="Actif immobilisé (immobilisations)"
    )
    current_assets: CurrentAssets = Field(
        default_factory=CurrentAssets,
        description="Actif circulant"
    )
    total_assets: float = Field(
        default=0.0,
        description="Total de l'actif"
    )

    @model_validator(mode='after')
    def calculate_total_assets(self) -> 'Assets':
        """Calcule le total de l'actif."""
        calculated_total = self.fixed_assets.total + self.current_assets.total
        if self.total_assets == 0.0:
            self.total_assets = calculated_total
        return self


# =============================================================================
# MODÈLES DU BILAN - PASSIF (Balance Sheet - Liabilities)
# =============================================================================

class Equity(BaseModel):
    """
    Capitaux propres.

    Représente les ressources appartenant aux actionnaires/associés,
    comprenant le capital, les réserves et le résultat de l'exercice.
    """

    share_capital: float = Field(
        default=0.0,
        description="Capital social ou individuel"
    )
    share_premium: float = Field(
        default=0.0,
        description="Primes d'émission, de fusion, d'apport",
        ge=0
    )
    revaluation_reserve: float = Field(
        default=0.0,
        description="Écarts de réévaluation"
    )
    legal_reserve: float = Field(
        default=0.0,
        description="Réserve légale",
        ge=0
    )
    statutory_reserves: float = Field(
        default=0.0,
        description="Réserves statutaires ou contractuelles"
    )
    other_reserves: float = Field(
        default=0.0,
        description="Autres réserves"
    )
    retained_earnings: float = Field(
        default=0.0,
        description="Report à nouveau"
    )
    net_income: float = Field(
        default=0.0,
        description="Résultat de l'exercice (bénéfice ou perte)"
    )
    investment_subsidies: float = Field(
        default=0.0,
        description="Subventions d'investissement",
        ge=0
    )
    regulated_provisions: float = Field(
        default=0.0,
        description="Provisions réglementées",
        ge=0
    )
    total: float = Field(
        default=0.0,
        description="Total des capitaux propres"
    )

    @model_validator(mode='after')
    def calculate_total(self) -> 'Equity':
        """Calcule le total des capitaux propres."""
        calculated_total = (
            self.share_capital +
            self.share_premium +
            self.revaluation_reserve +
            self.legal_reserve +
            self.statutory_reserves +
            self.other_reserves +
            self.retained_earnings +
            self.net_income +
            self.investment_subsidies +
            self.regulated_provisions
        )
        if self.total == 0.0:
            self.total = calculated_total
        return self


class Debt(BaseModel):
    """
    Dettes financières.

    Comprend l'ensemble des dettes portant intérêt contractées
    auprès d'établissements de crédit ou d'autres prêteurs.
    """

    long_term_debt: float = Field(
        default=0.0,
        description="Emprunts et dettes à plus d'un an",
        ge=0
    )
    short_term_debt: float = Field(
        default=0.0,
        description="Emprunts et dettes à moins d'un an",
        ge=0
    )
    bank_overdrafts: float = Field(
        default=0.0,
        description="Concours bancaires courants et soldes créditeurs de banque",
        ge=0
    )
    lease_obligations: float = Field(
        default=0.0,
        description="Dettes de crédit-bail",
        ge=0
    )
    bonds: float = Field(
        default=0.0,
        description="Emprunts obligataires",
        ge=0
    )
    shareholder_loans: float = Field(
        default=0.0,
        description="Emprunts et dettes auprès des associés",
        ge=0
    )
    total_financial_debt: float = Field(
        default=0.0,
        description="Total des dettes financières"
    )

    @model_validator(mode='after')
    def calculate_total(self) -> 'Debt':
        """Calcule le total des dettes financières."""
        calculated_total = (
            self.long_term_debt +
            self.short_term_debt +
            self.bank_overdrafts +
            self.lease_obligations +
            self.bonds +
            self.shareholder_loans
        )
        if self.total_financial_debt == 0.0:
            self.total_financial_debt = calculated_total
        return self


class OperatingLiabilities(BaseModel):
    """
    Dettes d'exploitation (dettes non financières).

    Comprend les dettes liées au cycle d'exploitation normal
    de l'entreprise (fournisseurs, fiscales, sociales).
    """

    trade_payables: float = Field(
        default=0.0,
        description="Dettes fournisseurs et comptes rattachés",
        ge=0
    )
    tax_liabilities: float = Field(
        default=0.0,
        description="Dettes fiscales (TVA, IS, autres impôts)",
        ge=0
    )
    social_liabilities: float = Field(
        default=0.0,
        description="Dettes sociales (salaires, charges sociales)",
        ge=0
    )
    advances_received: float = Field(
        default=0.0,
        description="Avances et acomptes reçus sur commandes",
        ge=0
    )
    deferred_revenue: float = Field(
        default=0.0,
        description="Produits constatés d'avance",
        ge=0
    )
    other_liabilities: float = Field(
        default=0.0,
        description="Autres dettes",
        ge=0
    )
    total: float = Field(
        default=0.0,
        description="Total des dettes d'exploitation"
    )

    @model_validator(mode='after')
    def calculate_total(self) -> 'OperatingLiabilities':
        """Calcule le total des dettes d'exploitation."""
        calculated_total = (
            self.trade_payables +
            self.tax_liabilities +
            self.social_liabilities +
            self.advances_received +
            self.deferred_revenue +
            self.other_liabilities
        )
        if self.total == 0.0:
            self.total = calculated_total
        return self


class Provisions(BaseModel):
    """
    Provisions pour risques et charges.

    Représente les passifs dont l'échéance ou le montant
    est incertain mais qui sont probables.
    """

    provisions_for_risks: float = Field(
        default=0.0,
        description="Provisions pour risques",
        ge=0
    )
    provisions_for_charges: float = Field(
        default=0.0,
        description="Provisions pour charges",
        ge=0
    )
    total: float = Field(
        default=0.0,
        description="Total des provisions"
    )

    @model_validator(mode='after')
    def calculate_total(self) -> 'Provisions':
        """Calcule le total des provisions."""
        calculated_total = self.provisions_for_risks + self.provisions_for_charges
        if self.total == 0.0:
            self.total = calculated_total
        return self


class Liabilities(BaseModel):
    """
    Passif total du bilan.

    Regroupe les capitaux propres, les provisions et les dettes
    pour former le total du passif du bilan.
    """

    equity: Equity = Field(
        default_factory=Equity,
        description="Capitaux propres"
    )
    provisions: Provisions = Field(
        default_factory=Provisions,
        description="Provisions pour risques et charges"
    )
    debt: Debt = Field(
        default_factory=Debt,
        description="Dettes financières"
    )
    operating_liabilities: OperatingLiabilities = Field(
        default_factory=OperatingLiabilities,
        description="Dettes d'exploitation"
    )
    total_liabilities: float = Field(
        default=0.0,
        description="Total du passif"
    )

    @model_validator(mode='after')
    def calculate_total_liabilities(self) -> 'Liabilities':
        """Calcule le total du passif."""
        calculated_total = (
            self.equity.total +
            self.provisions.total +
            self.debt.total_financial_debt +
            self.operating_liabilities.total
        )
        if self.total_liabilities == 0.0:
            self.total_liabilities = calculated_total
        return self


class BalanceSheet(BaseModel):
    """
    Bilan comptable complet.

    Représente la situation patrimoniale de l'entreprise à une date donnée,
    avec l'équilibre fondamental: Actif = Passif.
    """

    assets: Assets = Field(
        default_factory=Assets,
        description="Actif du bilan"
    )
    liabilities: Liabilities = Field(
        default_factory=Liabilities,
        description="Passif du bilan"
    )

    @model_validator(mode='after')
    def validate_balance_sheet_equilibrium(self) -> 'BalanceSheet':
        """
        Vérifie l'équilibre comptable fondamental: Actif = Passif.

        Autorise une tolérance de 1 euro pour les arrondis.
        """
        difference = abs(self.assets.total_assets - self.liabilities.total_liabilities)
        tolerance = 1.0  # Tolérance de 1 euro pour les arrondis

        if self.assets.total_assets > 0 and self.liabilities.total_liabilities > 0:
            if difference > tolerance:
                raise ValueError(
                    f"Déséquilibre du bilan: Actif ({self.assets.total_assets:.2f}) "
                    f"!= Passif ({self.liabilities.total_liabilities:.2f}). "
                    f"Différence: {difference:.2f} euros"
                )
        return self


# =============================================================================
# MODÈLES DU COMPTE DE RÉSULTAT (Income Statement)
# =============================================================================

class Revenues(BaseModel):
    """
    Produits d'exploitation.

    Représente l'ensemble des revenus générés par l'activité
    principale de l'entreprise.
    """

    sales_of_goods: float = Field(
        default=0.0,
        description="Ventes de marchandises",
        ge=0
    )
    sales_of_services: float = Field(
        default=0.0,
        description="Production vendue de services",
        ge=0
    )
    sales_of_products: float = Field(
        default=0.0,
        description="Production vendue de biens",
        ge=0
    )
    net_revenue: float = Field(
        default=0.0,
        description="Chiffre d'affaires net total",
        ge=0
    )
    stored_production: float = Field(
        default=0.0,
        description="Production stockée"
    )
    capitalized_production: float = Field(
        default=0.0,
        description="Production immobilisée",
        ge=0
    )
    operating_subsidies: float = Field(
        default=0.0,
        description="Subventions d'exploitation",
        ge=0
    )
    other_operating_income: float = Field(
        default=0.0,
        description="Autres produits d'exploitation",
        ge=0
    )
    reversal_of_provisions: float = Field(
        default=0.0,
        description="Reprises sur provisions et amortissements",
        ge=0
    )
    total: float = Field(
        default=0.0,
        description="Total des produits d'exploitation"
    )

    @model_validator(mode='after')
    def calculate_totals(self) -> 'Revenues':
        """Calcule les totaux des revenus."""
        # Calcul du CA si non renseigné
        if self.net_revenue == 0.0:
            self.net_revenue = (
                self.sales_of_goods +
                self.sales_of_services +
                self.sales_of_products
            )

        # Calcul du total des produits d'exploitation
        if self.total == 0.0:
            self.total = (
                self.net_revenue +
                self.stored_production +
                self.capitalized_production +
                self.operating_subsidies +
                self.other_operating_income +
                self.reversal_of_provisions
            )
        return self


class OperatingExpenses(BaseModel):
    """
    Charges d'exploitation.

    Représente l'ensemble des coûts engagés pour réaliser
    l'activité principale de l'entreprise.
    """

    purchases_of_goods: float = Field(
        default=0.0,
        description="Achats de marchandises",
        ge=0
    )
    purchases_of_raw_materials: float = Field(
        default=0.0,
        description="Achats de matières premières et autres approvisionnements",
        ge=0
    )
    inventory_variation: float = Field(
        default=0.0,
        description="Variation des stocks (positif = déstockage)"
    )
    external_charges: float = Field(
        default=0.0,
        description="Autres achats et charges externes",
        ge=0
    )
    taxes_and_duties: float = Field(
        default=0.0,
        description="Impôts, taxes et versements assimilés",
        ge=0
    )
    wages_and_salaries: float = Field(
        default=0.0,
        description="Salaires et traitements",
        ge=0
    )
    social_charges: float = Field(
        default=0.0,
        description="Charges sociales",
        ge=0
    )
    personnel_costs: float = Field(
        default=0.0,
        description="Total charges de personnel (si agrégé)",
        ge=0
    )
    depreciation: float = Field(
        default=0.0,
        description="Dotations aux amortissements sur immobilisations",
        ge=0
    )
    provisions: float = Field(
        default=0.0,
        description="Dotations aux provisions",
        ge=0
    )
    other_operating_expenses: float = Field(
        default=0.0,
        description="Autres charges d'exploitation",
        ge=0
    )
    total: float = Field(
        default=0.0,
        description="Total des charges d'exploitation"
    )

    @model_validator(mode='after')
    def calculate_total(self) -> 'OperatingExpenses':
        """Calcule le total des charges d'exploitation."""
        # Utiliser personnel_costs si renseigné, sinon wages + social
        personnel = self.personnel_costs if self.personnel_costs > 0 else (
            self.wages_and_salaries + self.social_charges
        )

        if self.total == 0.0:
            self.total = (
                self.purchases_of_goods +
                self.purchases_of_raw_materials +
                self.inventory_variation +
                self.external_charges +
                self.taxes_and_duties +
                personnel +
                self.depreciation +
                self.provisions +
                self.other_operating_expenses
            )
        return self


class FinancialResult(BaseModel):
    """
    Résultat financier.

    Représente le solde entre les produits et charges financières,
    liés aux opérations de financement et de placement.
    """

    financial_income: float = Field(
        default=0.0,
        description="Produits financiers (intérêts, dividendes reçus)",
        ge=0
    )
    interest_income: float = Field(
        default=0.0,
        description="Autres intérêts et produits assimilés",
        ge=0
    )
    reversal_of_financial_provisions: float = Field(
        default=0.0,
        description="Reprises sur provisions financières",
        ge=0
    )
    foreign_exchange_gains: float = Field(
        default=0.0,
        description="Gains de change",
        ge=0
    )
    total_financial_income: float = Field(
        default=0.0,
        description="Total des produits financiers",
        ge=0
    )
    interest_expense: float = Field(
        default=0.0,
        description="Intérêts et charges assimilées",
        ge=0
    )
    financial_provisions: float = Field(
        default=0.0,
        description="Dotations aux provisions financières",
        ge=0
    )
    foreign_exchange_losses: float = Field(
        default=0.0,
        description="Pertes de change",
        ge=0
    )
    total_financial_expense: float = Field(
        default=0.0,
        description="Total des charges financières",
        ge=0
    )
    net_financial_result: float = Field(
        default=0.0,
        description="Résultat financier net"
    )

    @model_validator(mode='after')
    def calculate_totals(self) -> 'FinancialResult':
        """Calcule les totaux financiers."""
        if self.total_financial_income == 0.0:
            self.total_financial_income = (
                self.financial_income +
                self.interest_income +
                self.reversal_of_financial_provisions +
                self.foreign_exchange_gains
            )

        if self.total_financial_expense == 0.0:
            self.total_financial_expense = (
                self.interest_expense +
                self.financial_provisions +
                self.foreign_exchange_losses
            )

        if self.net_financial_result == 0.0:
            self.net_financial_result = (
                self.total_financial_income - self.total_financial_expense
            )
        return self


class ExceptionalResult(BaseModel):
    """
    Résultat exceptionnel.

    Représente le solde des opérations exceptionnelles,
    non liées à l'exploitation courante.
    """

    exceptional_income: float = Field(
        default=0.0,
        description="Produits exceptionnels sur opérations de gestion",
        ge=0
    )
    exceptional_income_capital: float = Field(
        default=0.0,
        description="Produits exceptionnels sur opérations en capital",
        ge=0
    )
    reversal_of_exceptional_provisions: float = Field(
        default=0.0,
        description="Reprises sur provisions exceptionnelles",
        ge=0
    )
    total_exceptional_income: float = Field(
        default=0.0,
        description="Total des produits exceptionnels",
        ge=0
    )
    exceptional_expense: float = Field(
        default=0.0,
        description="Charges exceptionnelles sur opérations de gestion",
        ge=0
    )
    exceptional_expense_capital: float = Field(
        default=0.0,
        description="Charges exceptionnelles sur opérations en capital",
        ge=0
    )
    exceptional_provisions: float = Field(
        default=0.0,
        description="Dotations aux provisions exceptionnelles",
        ge=0
    )
    total_exceptional_expense: float = Field(
        default=0.0,
        description="Total des charges exceptionnelles",
        ge=0
    )
    net_exceptional_result: float = Field(
        default=0.0,
        description="Résultat exceptionnel net"
    )

    @model_validator(mode='after')
    def calculate_totals(self) -> 'ExceptionalResult':
        """Calcule les totaux exceptionnels."""
        if self.total_exceptional_income == 0.0:
            self.total_exceptional_income = (
                self.exceptional_income +
                self.exceptional_income_capital +
                self.reversal_of_exceptional_provisions
            )

        if self.total_exceptional_expense == 0.0:
            self.total_exceptional_expense = (
                self.exceptional_expense +
                self.exceptional_expense_capital +
                self.exceptional_provisions
            )

        if self.net_exceptional_result == 0.0:
            self.net_exceptional_result = (
                self.total_exceptional_income - self.total_exceptional_expense
            )
        return self


class IncomeStatement(BaseModel):
    """
    Compte de résultat complet.

    Représente la performance économique de l'entreprise sur l'exercice,
    détaillant la formation du résultat net.
    """

    revenues: Revenues = Field(
        default_factory=Revenues,
        description="Produits d'exploitation"
    )
    operating_expenses: OperatingExpenses = Field(
        default_factory=OperatingExpenses,
        description="Charges d'exploitation"
    )
    operating_income: float = Field(
        default=0.0,
        description="Résultat d'exploitation"
    )
    financial_result: FinancialResult = Field(
        default_factory=FinancialResult,
        description="Résultat financier"
    )
    current_income_before_tax: float = Field(
        default=0.0,
        description="Résultat courant avant impôts"
    )
    exceptional_result: ExceptionalResult = Field(
        default_factory=ExceptionalResult,
        description="Résultat exceptionnel"
    )
    employee_profit_sharing: float = Field(
        default=0.0,
        description="Participation des salariés aux résultats",
        ge=0
    )
    income_tax_expense: float = Field(
        default=0.0,
        description="Impôts sur les bénéfices"
    )
    net_income: float = Field(
        default=0.0,
        description="Résultat net de l'exercice"
    )

    @model_validator(mode='after')
    def calculate_results(self) -> 'IncomeStatement':
        """Calcule les différents niveaux de résultat."""
        # Résultat d'exploitation
        if self.operating_income == 0.0:
            self.operating_income = (
                self.revenues.total - self.operating_expenses.total
            )

        # Résultat courant avant impôts
        if self.current_income_before_tax == 0.0:
            self.current_income_before_tax = (
                self.operating_income +
                self.financial_result.net_financial_result
            )

        # Résultat net
        if self.net_income == 0.0:
            self.net_income = (
                self.current_income_before_tax +
                self.exceptional_result.net_exceptional_result -
                self.employee_profit_sharing -
                self.income_tax_expense
            )

        return self


# =============================================================================
# TABLEAU DES FLUX DE TRÉSORERIE (Cash Flow Statement)
# =============================================================================

class CashFlow(BaseModel):
    """
    Tableau des flux de trésorerie.

    Présente les mouvements de trésorerie classés par nature:
    exploitation, investissement et financement.
    """

    # Flux d'exploitation
    net_income: float = Field(
        default=0.0,
        description="Résultat net de l'exercice"
    )
    depreciation_and_amortization: float = Field(
        default=0.0,
        description="Dotations aux amortissements et provisions",
        ge=0
    )
    gains_losses_on_disposals: float = Field(
        default=0.0,
        description="Plus ou moins-values de cession"
    )
    change_in_working_capital: float = Field(
        default=0.0,
        description="Variation du besoin en fonds de roulement"
    )
    operating_activities: float = Field(
        default=0.0,
        description="Flux net de trésorerie lié à l'exploitation"
    )

    # Flux d'investissement
    capital_expenditures: float = Field(
        default=0.0,
        description="Acquisitions d'immobilisations",
        ge=0
    )
    proceeds_from_disposals: float = Field(
        default=0.0,
        description="Cessions d'immobilisations",
        ge=0
    )
    financial_investments: float = Field(
        default=0.0,
        description="Acquisitions de titres et placements"
    )
    investing_activities: float = Field(
        default=0.0,
        description="Flux net de trésorerie lié à l'investissement"
    )

    # Flux de financement
    capital_increase: float = Field(
        default=0.0,
        description="Augmentation de capital",
        ge=0
    )
    dividends_paid: float = Field(
        default=0.0,
        description="Dividendes versés",
        ge=0
    )
    new_borrowings: float = Field(
        default=0.0,
        description="Nouveaux emprunts",
        ge=0
    )
    loan_repayments: float = Field(
        default=0.0,
        description="Remboursements d'emprunts",
        ge=0
    )
    financing_activities: float = Field(
        default=0.0,
        description="Flux net de trésorerie lié au financement"
    )

    # Variation nette
    net_change_in_cash: float = Field(
        default=0.0,
        description="Variation nette de la trésorerie"
    )
    opening_cash: float = Field(
        default=0.0,
        description="Trésorerie à l'ouverture"
    )
    closing_cash: float = Field(
        default=0.0,
        description="Trésorerie à la clôture"
    )

    @model_validator(mode='after')
    def calculate_cash_flows(self) -> 'CashFlow':
        """Calcule les différents flux de trésorerie."""
        # Flux d'exploitation
        if self.operating_activities == 0.0:
            self.operating_activities = (
                self.net_income +
                self.depreciation_and_amortization -
                self.gains_losses_on_disposals -
                self.change_in_working_capital
            )

        # Flux d'investissement
        if self.investing_activities == 0.0:
            self.investing_activities = (
                self.proceeds_from_disposals -
                self.capital_expenditures -
                self.financial_investments
            )

        # Flux de financement
        if self.financing_activities == 0.0:
            self.financing_activities = (
                self.capital_increase +
                self.new_borrowings -
                self.dividends_paid -
                self.loan_repayments
            )

        # Variation nette
        if self.net_change_in_cash == 0.0:
            self.net_change_in_cash = (
                self.operating_activities +
                self.investing_activities +
                self.financing_activities
            )

        # Trésorerie de clôture
        if self.closing_cash == 0.0 and self.opening_cash != 0.0:
            self.closing_cash = self.opening_cash + self.net_change_in_cash

        return self


# =============================================================================
# ANNEXES ET NOTES
# =============================================================================

class Notes(BaseModel):
    """
    Informations annexes extraites de la liasse fiscale.

    Contient des données complémentaires importantes pour
    l'analyse financière.
    """

    employees_count: int = Field(
        default=0,
        description="Effectif moyen du personnel",
        ge=0
    )
    employees_end_of_year: int = Field(
        default=0,
        description="Effectif à la clôture de l'exercice",
        ge=0
    )
    avg_payment_terms_suppliers_days: int = Field(
        default=0,
        description="Délai moyen de paiement fournisseurs (en jours)",
        ge=0
    )
    avg_payment_terms_customers_days: int = Field(
        default=0,
        description="Délai moyen de paiement clients (en jours)",
        ge=0
    )
    leasing_commitments: float = Field(
        default=0.0,
        description="Engagements de crédit-bail",
        ge=0
    )
    pension_commitments: float = Field(
        default=0.0,
        description="Engagements de retraite",
        ge=0
    )
    pledges_and_guarantees: float = Field(
        default=0.0,
        description="Nantissements et garanties donnés",
        ge=0
    )
    related_party_transactions: float = Field(
        default=0.0,
        description="Transactions avec les parties liées"
    )
    research_and_development: float = Field(
        default=0.0,
        description="Dépenses de R&D",
        ge=0
    )
    cir_cice_credits: float = Field(
        default=0.0,
        description="Crédits d'impôt (CIR, CICE, etc.)",
        ge=0
    )


# =============================================================================
# MÉTADONNÉES
# =============================================================================

class Metadata(BaseModel):
    """
    Métadonnées de la liasse fiscale.

    Informations d'identification et de traçabilité
    des données extraites.
    """

    company_name: str = Field(
        ...,
        description="Raison sociale de l'entreprise",
        min_length=1
    )
    siren: str = Field(
        ...,
        description="Numéro SIREN de l'entreprise (9 chiffres)",
        min_length=9,
        max_length=9
    )
    siret: Optional[str] = Field(
        default=None,
        description="Numéro SIRET de l'établissement (14 chiffres)",
        min_length=14,
        max_length=14
    )
    naf_code: Optional[str] = Field(
        default=None,
        description="Code NAF/APE de l'activité"
    )
    legal_form: Optional[str] = Field(
        default=None,
        description="Forme juridique (SA, SAS, SARL, etc.)"
    )
    fiscal_year_start: Optional[date] = Field(
        default=None,
        description="Date de début de l'exercice fiscal"
    )
    fiscal_year_end: date = Field(
        ...,
        description="Date de clôture de l'exercice fiscal"
    )
    fiscal_year_duration_months: int = Field(
        default=12,
        description="Durée de l'exercice en mois",
        ge=1,
        le=24
    )
    extraction_date: date = Field(
        ...,
        description="Date d'extraction des données"
    )
    source_file: Optional[str] = Field(
        default=None,
        description="Nom du fichier source"
    )
    form_types: list[str] = Field(
        default_factory=list,
        description="Types de formulaires extraits (2050, 2051, 2052, etc.)"
    )
    confidence_score: float = Field(
        default=1.0,
        description="Score de confiance de l'extraction (0 à 1)",
        ge=0.0,
        le=1.0
    )
    extraction_warnings: list[str] = Field(
        default_factory=list,
        description="Avertissements lors de l'extraction"
    )

    @field_validator('siren')
    @classmethod
    def validate_siren(cls, v: str) -> str:
        """Vérifie que le SIREN contient uniquement des chiffres."""
        if not v.isdigit():
            raise ValueError("Le SIREN doit contenir uniquement des chiffres")
        return v

    @field_validator('siret')
    @classmethod
    def validate_siret(cls, v: Optional[str]) -> Optional[str]:
        """Vérifie que le SIRET contient uniquement des chiffres."""
        if v is not None and not v.isdigit():
            raise ValueError("Le SIRET doit contenir uniquement des chiffres")
        return v


# =============================================================================
# MODÈLE RACINE - DONNÉES FISCALES COMPLÈTES
# =============================================================================

class FiscalData(BaseModel):
    """
    Modèle racine représentant une liasse fiscale française complète.

    Regroupe l'ensemble des données financières extraites:
    - Métadonnées de l'entreprise
    - Bilan (actif et passif)
    - Compte de résultat
    - Tableau des flux de trésorerie (optionnel)
    - Annexes et notes (optionnel)

    Ce modèle constitue la structure de données principale pour
    l'analyse financière automatisée.
    """

    metadata: Metadata = Field(
        ...,
        description="Métadonnées et informations d'identification"
    )
    balance_sheet: BalanceSheet = Field(
        default_factory=BalanceSheet,
        description="Bilan comptable (actif et passif)"
    )
    income_statement: IncomeStatement = Field(
        default_factory=IncomeStatement,
        description="Compte de résultat"
    )
    cash_flow: Optional[CashFlow] = Field(
        default=None,
        description="Tableau des flux de trésorerie"
    )
    notes: Optional[Notes] = Field(
        default=None,
        description="Annexes et informations complémentaires"
    )

    # Données brutes pour référence
    raw_fields: Optional[dict[str, FinancialField]] = Field(
        default=None,
        description="Champs bruts extraits avec leurs codes fiscaux"
    )

    @model_validator(mode='after')
    def validate_consistency(self) -> 'FiscalData':
        """
        Vérifie la cohérence globale des données.

        - Résultat net du bilan = Résultat net du compte de résultat
        """
        equity_net_income = self.balance_sheet.liabilities.equity.net_income
        income_statement_net_income = self.income_statement.net_income

        # Vérification si les deux valeurs sont renseignées
        if equity_net_income != 0.0 and income_statement_net_income != 0.0:
            difference = abs(equity_net_income - income_statement_net_income)
            tolerance = 1.0  # Tolérance de 1 euro

            if difference > tolerance:
                raise ValueError(
                    f"Incohérence: le résultat net au bilan ({equity_net_income:.2f}) "
                    f"diffère du résultat net au compte de résultat "
                    f"({income_statement_net_income:.2f})"
                )

        return self

    def get_field_by_code(self, code: str) -> Optional[FinancialField]:
        """
        Récupère un champ par son code fiscal.

        Args:
            code: Code du champ fiscal (ex: 'AA', 'BH')

        Returns:
            Le champ financier correspondant ou None
        """
        if self.raw_fields:
            return self.raw_fields.get(code)
        return None


# =============================================================================
# MODÈLES DE COMPARAISON MULTI-EXERCICES
# =============================================================================

class MultiYearData(BaseModel):
    """
    Données financières sur plusieurs exercices.

    Permet l'analyse de l'évolution financière
    de l'entreprise dans le temps.
    """

    company_name: str = Field(
        ...,
        description="Raison sociale de l'entreprise"
    )
    siren: str = Field(
        ...,
        description="Numéro SIREN"
    )
    fiscal_years: list[FiscalData] = Field(
        default_factory=list,
        description="Données fiscales par exercice"
    )

    @field_validator('fiscal_years')
    @classmethod
    def validate_fiscal_years(cls, v: list[FiscalData]) -> list[FiscalData]:
        """Vérifie la cohérence des exercices."""
        if len(v) > 1:
            # Vérifier que tous les exercices concernent la même entreprise
            sirens = {fy.metadata.siren for fy in v}
            if len(sirens) > 1:
                raise ValueError(
                    "Tous les exercices doivent concerner la même entreprise"
                )
        return v

    def get_by_year(self, year: int) -> Optional[FiscalData]:
        """
        Récupère les données d'un exercice par année.

        Args:
            year: Année de clôture recherchée

        Returns:
            Les données fiscales de l'exercice ou None
        """
        for fy in self.fiscal_years:
            if fy.metadata.fiscal_year_end.year == year:
                return fy
        return None

    def get_sorted_years(self) -> list[FiscalData]:
        """
        Retourne les exercices triés par date de clôture.

        Returns:
            Liste des exercices triés chronologiquement
        """
        return sorted(
            self.fiscal_years,
            key=lambda x: x.metadata.fiscal_year_end
        )
