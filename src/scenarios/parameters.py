"""
Modeles Pydantic pour les parametres de scenarios financiers.

Ce module definit les structures de donnees pour configurer differents scenarios
d'analyse financiere, incluant les parametres de dette, d'equity, de croissance
et de stress test.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, computed_field


class DebtParameters(BaseModel):
    """
    Parametres de la dette pour le financement d'une acquisition ou d'un projet.

    Attributes:
        debt_amount: Montant total de la dette en euros
        interest_rate: Taux d'interet annuel (entre 0 et 20%)
        loan_duration: Duree du pret en annees (1 a 30 ans)
        grace_period: Periode de differe en annees (0 a 5 ans)
        amortization_type: Type d'amortissement (constant ou linear)
    """

    debt_amount: float = Field(
        ge=0,
        description="Montant de la dette en euros"
    )
    interest_rate: float = Field(
        ge=0,
        le=0.20,
        description="Taux d'interet annuel (exprime en decimal, ex: 0.05 pour 5%)"
    )
    loan_duration: int = Field(
        ge=1,
        le=30,
        description="Duree du pret en annees"
    )
    grace_period: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Periode de differe en annees (pas de remboursement du principal)"
    )
    amortization_type: str = Field(
        default="constant",
        description="Type d'amortissement: 'constant' (annuites constantes) ou 'linear' (amortissement lineaire)"
    )

    @field_validator("interest_rate")
    @classmethod
    def validate_realistic_interest_rate(cls, v: float) -> float:
        """
        Valide que le taux d'interet est dans une fourchette realiste.

        Args:
            v: Taux d'interet a valider

        Returns:
            Le taux d'interet valide

        Raises:
            ValueError: Si le taux est hors de la fourchette realiste (1%-15%)
        """
        if v > 0 and (v < 0.01 or v > 0.15):
            raise ValueError(
                f"Le taux d'interet {v:.2%} est hors de la fourchette realiste (1%-15%). "
                "Utilisez 0 pour un financement sans interet ou un taux entre 1% et 15%."
            )
        return v

    @field_validator("amortization_type")
    @classmethod
    def validate_amortization_type(cls, v: str) -> str:
        """
        Valide le type d'amortissement.

        Args:
            v: Type d'amortissement a valider

        Returns:
            Le type d'amortissement valide en minuscules

        Raises:
            ValueError: Si le type n'est pas 'constant' ou 'linear'
        """
        v = v.lower()
        if v not in ("constant", "linear"):
            raise ValueError(
                f"Type d'amortissement '{v}' invalide. "
                "Utilisez 'constant' ou 'linear'."
            )
        return v


class EquityParameters(BaseModel):
    """
    Parametres des capitaux propres (equity) pour le financement.

    Attributes:
        equity_amount: Montant des capitaux propres investis en euros
        target_roe: Return on Equity (ROE) cible
        exit_multiple: Multiple de sortie par rapport a l'EBITDA
        holding_period: Periode de detention en annees
    """

    equity_amount: float = Field(
        ge=0,
        description="Montant des capitaux propres en euros"
    )
    target_roe: float = Field(
        ge=0,
        le=1.0,
        description="ROE (Return on Equity) cible (ex: 0.15 pour 15%)"
    )
    exit_multiple: float = Field(
        ge=0,
        description="Multiple de sortie (x EBITDA)"
    )
    holding_period: int = Field(
        ge=1,
        le=15,
        description="Periode de detention en annees"
    )


class GrowthAssumptions(BaseModel):
    """
    Hypotheses de croissance pour les projections financieres.

    Attributes:
        revenue_growth: Taux de croissance annuel du chiffre d'affaires
        ebitda_margin_evolution: Evolution annuelle de la marge EBITDA
        capex_percentage: Pourcentage du CA consacre aux investissements
        inflation_rate: Taux d'inflation annuel previsionnel
    """

    revenue_growth: float = Field(
        default=0.05,
        ge=-0.5,
        le=0.5,
        description="Croissance annuelle du chiffre d'affaires (ex: 0.05 pour +5%)"
    )
    ebitda_margin_evolution: float = Field(
        default=0.0,
        ge=-0.2,
        le=0.2,
        description="Evolution annuelle de la marge EBITDA en points (ex: 0.01 pour +1pt)"
    )
    capex_percentage: float = Field(
        default=0.03,
        ge=0,
        le=0.5,
        description="Pourcentage du CA pour les investissements (CapEx)"
    )
    inflation_rate: float = Field(
        default=0.02,
        ge=0,
        le=0.20,
        description="Taux d'inflation annuel previsionnel"
    )


class StressScenario(BaseModel):
    """
    Parametres pour les tests de stress (scenarios adverses).

    Permet de simuler des conditions de marche defavorables pour evaluer
    la resilience du business plan.

    Attributes:
        revenue_shock: Choc sur le chiffre d'affaires (negatif)
        margin_compression: Compression de la marge EBITDA (negatif)
        interest_rate_increase: Hausse du taux d'interet en points
    """

    revenue_shock: float = Field(
        default=-0.1,
        ge=-0.5,
        le=0.0,
        description="Choc sur le chiffre d'affaires en % (ex: -0.1 pour -10%)"
    )
    margin_compression: float = Field(
        default=-0.05,
        ge=-0.3,
        le=0.0,
        description="Compression de la marge EBITDA en points (ex: -0.05 pour -5pts)"
    )
    interest_rate_increase: float = Field(
        default=0.01,
        ge=0,
        le=0.10,
        description="Hausse du taux d'interet en points (ex: 0.01 pour +1pt)"
    )


class ScenarioParameters(BaseModel):
    """
    Modele principal regroupant tous les parametres d'un scenario financier.

    Ce modele combine les parametres de dette, d'equity, de croissance et
    optionnellement de stress pour definir un scenario complet d'analyse.

    Attributes:
        name: Nom identifiant du scenario
        debt: Parametres de la dette
        equity: Parametres des capitaux propres
        growth: Hypotheses de croissance
        stress: Scenario de stress optionnel
    """

    name: str = Field(
        description="Nom identifiant du scenario"
    )
    debt: DebtParameters = Field(
        description="Parametres de la dette"
    )
    equity: EquityParameters = Field(
        description="Parametres des capitaux propres"
    )
    growth: GrowthAssumptions = Field(
        description="Hypotheses de croissance"
    )
    stress: Optional[StressScenario] = Field(
        default=None,
        description="Scenario de stress optionnel pour les tests de resilience"
    )

    @computed_field
    @property
    def total_financing(self) -> float:
        """
        Calcule le financement total (dette + equity).

        Returns:
            Montant total du financement en euros
        """
        return self.debt.debt_amount + self.equity.equity_amount

    @computed_field
    @property
    def leverage_ratio(self) -> float:
        """
        Calcule le ratio de levier (LTV - Loan to Value).

        Represente la proportion de dette dans le financement total.

        Returns:
            Ratio dette/financement total (entre 0 et 1)
            Retourne 0 si le financement total est nul
        """
        if self.total_financing == 0:
            return 0.0
        return self.debt.debt_amount / self.total_financing

    @computed_field
    @property
    def debt_to_equity(self) -> float:
        """
        Calcule le ratio dette/equity (D/E ratio).

        Indicateur cle de l'effet de levier financier.

        Returns:
            Ratio dette/equity
            Retourne float('inf') si equity est nul et dette > 0
            Retourne 0 si dette et equity sont nuls
        """
        if self.equity.equity_amount == 0:
            if self.debt.debt_amount == 0:
                return 0.0
            return float('inf')
        return self.debt.debt_amount / self.equity.equity_amount


# =============================================================================
# SCENARIOS PREDEFINIS
# =============================================================================

CONSERVATIVE_SCENARIO = ScenarioParameters(
    name="Conservateur",
    debt=DebtParameters(
        debt_amount=200_000,
        interest_rate=0.04,
        loan_duration=10,
        grace_period=0,
        amortization_type="linear"
    ),
    equity=EquityParameters(
        equity_amount=800_000,
        target_roe=0.08,
        exit_multiple=5.0,
        holding_period=7
    ),
    growth=GrowthAssumptions(
        revenue_growth=0.02,
        ebitda_margin_evolution=0.0,
        capex_percentage=0.02,
        inflation_rate=0.02
    ),
    stress=StressScenario(
        revenue_shock=-0.05,
        margin_compression=-0.02,
        interest_rate_increase=0.005
    )
)
"""
Scenario conservateur avec peu de dette et croissance faible.

Caracteristiques:
- Ratio D/E: 0.25 (20% dette / 80% equity)
- Croissance CA: 2% par an
- Taux d'interet: 4%
- Horizon: 7 ans
"""

BALANCED_SCENARIO = ScenarioParameters(
    name="Equilibre",
    debt=DebtParameters(
        debt_amount=500_000,
        interest_rate=0.05,
        loan_duration=7,
        grace_period=1,
        amortization_type="constant"
    ),
    equity=EquityParameters(
        equity_amount=500_000,
        target_roe=0.12,
        exit_multiple=6.0,
        holding_period=5
    ),
    growth=GrowthAssumptions(
        revenue_growth=0.05,
        ebitda_margin_evolution=0.005,
        capex_percentage=0.03,
        inflation_rate=0.02
    ),
    stress=StressScenario(
        revenue_shock=-0.10,
        margin_compression=-0.05,
        interest_rate_increase=0.01
    )
)
"""
Scenario equilibre avec un mix 50/50 dette/equity.

Caracteristiques:
- Ratio D/E: 1.0 (50% dette / 50% equity)
- Croissance CA: 5% par an
- Taux d'interet: 5% avec 1 an de differe
- Horizon: 5 ans
"""

LEVERAGED_SCENARIO = ScenarioParameters(
    name="Leverage",
    debt=DebtParameters(
        debt_amount=700_000,
        interest_rate=0.06,
        loan_duration=7,
        grace_period=2,
        amortization_type="constant"
    ),
    equity=EquityParameters(
        equity_amount=300_000,
        target_roe=0.18,
        exit_multiple=7.0,
        holding_period=5
    ),
    growth=GrowthAssumptions(
        revenue_growth=0.08,
        ebitda_margin_evolution=0.01,
        capex_percentage=0.04,
        inflation_rate=0.025
    ),
    stress=StressScenario(
        revenue_shock=-0.15,
        margin_compression=-0.08,
        interest_rate_increase=0.02
    )
)
"""
Scenario avec fort effet de levier.

Caracteristiques:
- Ratio D/E: 2.33 (70% dette / 30% equity)
- Croissance CA: 8% par an
- Taux d'interet: 6% avec 2 ans de differe
- Horizon: 5 ans
- ROE cible eleve: 18%
"""

AGGRESSIVE_SCENARIO = ScenarioParameters(
    name="Agressif",
    debt=DebtParameters(
        debt_amount=850_000,
        interest_rate=0.07,
        loan_duration=5,
        grace_period=1,
        amortization_type="constant"
    ),
    equity=EquityParameters(
        equity_amount=150_000,
        target_roe=0.25,
        exit_multiple=8.0,
        holding_period=4
    ),
    growth=GrowthAssumptions(
        revenue_growth=0.12,
        ebitda_margin_evolution=0.02,
        capex_percentage=0.05,
        inflation_rate=0.03
    ),
    stress=StressScenario(
        revenue_shock=-0.20,
        margin_compression=-0.10,
        interest_rate_increase=0.03
    )
)
"""
Scenario agressif avec dette maximale et forte croissance.

Caracteristiques:
- Ratio D/E: 5.67 (85% dette / 15% equity)
- Croissance CA: 12% par an
- Taux d'interet: 7%
- Horizon: 4 ans
- ROE cible tres eleve: 25%
- Risque eleve en cas de stress
"""


# Liste des scenarios predefinis pour faciliter l'iteration
PREDEFINED_SCENARIOS = [
    CONSERVATIVE_SCENARIO,
    BALANCED_SCENARIO,
    LEVERAGED_SCENARIO,
    AGGRESSIVE_SCENARIO,
]
