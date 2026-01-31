"""
Modèles Pydantic Phase 3 - LBO & Normalisation.

Nouveaux modèles pour:
- Normalisation comptable (EBE → EBITDA banque → EBITDA equity)
- Structure LBO (tranches de dette, equity)
- Hypothèses d'exploitation
- Covenants bancaires
- Décision d'acquisition
"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# NORMALISATION COMPTABLE
# =============================================================================

class AdjustmentCategory(str, Enum):
    """Catégories de retraitements comptables."""
    PERSONNEL = "personnel"  # Rémunération dirigeant excessive
    RENT = "rent"  # Loyers (crédit-bail)
    EXCEPTIONAL = "exceptional"  # Charges exceptionnelles
    SUBSIDY = "subsidy"  # Subventions non récurrentes
    OTHER = "other"  # Autres ajustements


class Adjustment(BaseModel):
    """
    Retraitement comptable pour normalisation EBITDA.

    Permet de passer de l'EBE (Excédent Brut d'Exploitation)
    à un EBITDA normalisé "banque-ready".
    """
    name: str = Field(
        ...,
        description="Nom du retraitement (ex: 'Loyers crédit-bail')",
        min_length=1
    )
    amount: float = Field(
        ...,
        description="Montant du retraitement en euros (positif = augmente EBITDA)"
    )
    category: AdjustmentCategory = Field(
        ...,
        description="Catégorie du retraitement"
    )
    description: str = Field(
        default="",
        description="Description détaillée du retraitement"
    )

    @property
    def impact_on_ebitda(self) -> float:
        """Impact sur l'EBITDA (montant signé)."""
        return self.amount


class NormalizationData(BaseModel):
    """
    Données de normalisation comptable complètes.

    Workflow:
    1. EBE (Excédent Brut d'Exploitation) - données brutes
    2. + Retraitements (Adjustments)
    3. = EBITDA banque (normalisé)
    4. - IS cash - Capex maintenance
    5. = EBITDA equity (disponible pour entrepreneurs)
    """
    ebe: float = Field(
        ...,
        description="Excédent Brut d'Exploitation (CA - charges d'exploitation)",
        ge=0
    )
    adjustments: List[Adjustment] = Field(
        default_factory=list,
        description="Liste des retraitements appliqués"
    )
    ebitda_bank: float = Field(
        default=0.0,
        description="EBITDA normalisé banque (EBE + retraitements)"
    )
    ebitda_equity: float = Field(
        default=0.0,
        description="EBITDA equity (EBITDA banque - IS - Capex)"
    )

    # Métadonnées audit
    audit_log: List[str] = Field(
        default_factory=list,
        description="Log de traçabilité des opérations"
    )
    validated_at: Optional[datetime] = Field(
        default=None,
        description="Date/heure de validation"
    )
    validated_by: Optional[str] = Field(
        default=None,
        description="Utilisateur ayant validé"
    )

    def calculate_ebitda_bank(self) -> float:
        """Calcule EBITDA banque = EBE + somme des ajustements."""
        total_adjustments = sum(adj.impact_on_ebitda for adj in self.adjustments)
        self.ebitda_bank = self.ebe + total_adjustments
        self.audit_log.append(
            f"EBITDA banque calculé: {self.ebe:,.0f} + {total_adjustments:,.0f} = {self.ebitda_bank:,.0f}"
        )
        return self.ebitda_bank

    def calculate_ebitda_equity(
        self,
        tax_rate: float = 0.25,
        capex_maintenance: float = 0.0
    ) -> float:
        """
        Calcule EBITDA equity = EBITDA banque - IS cash - Capex.

        Args:
            tax_rate: Taux d'IS effectif (défaut 25%)
            capex_maintenance: Capex de maintenance annuel
        """
        is_cash = self.ebitda_bank * tax_rate
        self.ebitda_equity = self.ebitda_bank - is_cash - capex_maintenance
        self.audit_log.append(
            f"EBITDA equity calculé: {self.ebitda_bank:,.0f} - {is_cash:,.0f} (IS) - {capex_maintenance:,.0f} (Capex) = {self.ebitda_equity:,.0f}"
        )
        return self.ebitda_equity

    def validate(self, user: str = "system") -> None:
        """Valide les données de normalisation."""
        self.validated_at = datetime.now()
        self.validated_by = user
        self.audit_log.append(f"Validé par {user} le {self.validated_at.isoformat()}")


# =============================================================================
# STRUCTURE LBO
# =============================================================================

class AmortizationType(str, Enum):
    """Type d'amortissement de dette."""
    CONSTANT = "constant"  # Mensualités constantes
    LINEAR = "linear"  # Amortissement linéaire du capital
    BULLET = "bullet"  # Remboursement in fine


class DebtLayer(BaseModel):
    """
    Tranche de dette (senior, Bpifrance, crédit vendeur, etc.).

    Représente une source de financement par dette avec ses
    caractéristiques propres.
    """
    name: str = Field(
        ...,
        description="Nom de la tranche (ex: 'Dette senior', 'Bpifrance')",
        min_length=1
    )
    amount: float = Field(
        ...,
        description="Montant emprunté en euros",
        ge=0
    )
    interest_rate: float = Field(
        ...,
        description="Taux d'intérêt annuel (ex: 0.045 pour 4.5%)",
        ge=0,
        le=0.25  # Max 25%
    )
    duration_years: int = Field(
        ...,
        description="Durée du prêt en années",
        ge=1,
        le=30
    )
    grace_period: int = Field(
        default=0,
        description="Période de différé en années (seuls intérêts payés)",
        ge=0
    )
    amortization_type: AmortizationType = Field(
        default=AmortizationType.CONSTANT,
        description="Type d'amortissement"
    )

    @field_validator('grace_period')
    @classmethod
    def validate_grace_period(cls, v: int, info) -> int:
        """Vérifie que le différé < durée totale."""
        duration = info.data.get('duration_years', 0)
        if v >= duration:
            raise ValueError(
                f"Période de différé ({v} ans) doit être < durée totale ({duration} ans)"
            )
        return v

    def calculate_annual_service(self) -> float:
        """
        Calcule le service de dette annuel moyen.

        Simplifié pour MVP: assume amortissement constant.
        """
        if self.amortization_type == AmortizationType.BULLET:
            # Bullet: seulement intérêts pendant durée, puis capital à la fin
            return self.amount * self.interest_rate

        # Constant ou Linear: approximation service moyen
        principal_payment = self.amount / (self.duration_years - self.grace_period)
        interest_payment = self.amount * self.interest_rate * 0.5  # Moyenne
        return principal_payment + interest_payment


class LBOStructure(BaseModel):
    """
    Structure de financement LBO complète.

    Combine les différentes tranches de dette et l'equity
    pour financer l'acquisition.
    """
    acquisition_price: float = Field(
        ...,
        description="Prix d'acquisition de l'entreprise",
        ge=0
    )
    debt_layers: List[DebtLayer] = Field(
        default_factory=list,
        description="Tranches de dette (senior, Bpifrance, vendeur, etc.)"
    )
    equity_amount: float = Field(
        ...,
        description="Montant des capitaux propres investis",
        ge=0
    )
    equity_split: Dict[str, float] = Field(
        default_factory=lambda: {"entrepreneur": 0.70, "investors": 0.30},
        description="Répartition equity (ex: {'entrepreneur': 0.7, 'investors': 0.3})"
    )

    @property
    def total_debt(self) -> float:
        """Total des dettes."""
        return sum(layer.amount for layer in self.debt_layers)

    @property
    def total_financing(self) -> float:
        """Total financement (dette + equity)."""
        return self.total_debt + self.equity_amount

    @property
    def leverage_ratio(self) -> float:
        """Ratio de levier (Dette / (Dette + Equity))."""
        total = self.total_financing
        if total == 0:
            return 0.0
        return self.total_debt / total

    @property
    def debt_to_equity(self) -> float:
        """Ratio Dette / Equity."""
        if self.equity_amount == 0:
            return float('inf')
        return self.total_debt / self.equity_amount

    def calculate_total_annual_service(self) -> float:
        """Calcule le service de dette annuel total (toutes tranches)."""
        return sum(layer.calculate_annual_service() for layer in self.debt_layers)

    @field_validator('equity_split')
    @classmethod
    def validate_equity_split(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Vérifie que la répartition equity somme à 1.0 (100%)."""
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):  # Tolérance arrondi
            raise ValueError(
                f"La répartition equity doit sommer à 100% (actuellement {total*100:.1f}%)"
            )
        return v


# =============================================================================
# HYPOTHÈSES D'EXPLOITATION
# =============================================================================

class OperatingAssumptions(BaseModel):
    """
    Hypothèses d'exploitation pour projections financières.

    Permet de projeter le compte de résultat sur N années
    pour calculer les métriques de viabilité.
    """
    projection_years: int = Field(
        default=7,
        description="Nombre d'années de projection",
        ge=3,
        le=15
    )

    # Croissance CA
    revenue_growth_rate: List[float] = Field(
        default_factory=lambda: [0.05] * 7,
        description="Taux de croissance CA par année (ex: [0.05, 0.05, 0.03, ...])"
    )

    # Marge EBITDA
    ebitda_margin_evolution: List[float] = Field(
        default_factory=lambda: [0.0] * 7,
        description="Évolution marge EBITDA en points par année (ex: [0.5, 0.5, 0, ...])"
    )

    # BFR
    bfr_percentage_of_revenue: float = Field(
        default=0.18,
        description="BFR en % du CA",
        ge=0,
        le=1.0
    )

    # Capex
    capex_maintenance_pct: float = Field(
        default=0.03,
        description="Capex maintenance en % du CA",
        ge=0,
        le=0.20
    )
    capex_development: List[float] = Field(
        default_factory=list,
        description="Capex développement additionnel par année (en euros)"
    )

    # Fiscalité
    tax_rate: float = Field(
        default=0.25,
        description="Taux d'IS effectif",
        ge=0,
        le=0.50
    )

    @field_validator('revenue_growth_rate', 'ebitda_margin_evolution')
    @classmethod
    def validate_list_length(cls, v: List[float], info) -> List[float]:
        """Vérifie que les listes ont la bonne longueur."""
        projection_years = info.data.get('projection_years', 7)
        if len(v) != projection_years:
            # Étend ou tronque pour matcher projection_years
            if len(v) < projection_years:
                # Étend avec dernière valeur
                v = v + [v[-1]] * (projection_years - len(v)) if v else [0.0] * projection_years
            else:
                # Tronque
                v = v[:projection_years]
        return v


# =============================================================================
# COVENANTS BANCAIRES
# =============================================================================

class CovenantComparison(str, Enum):
    """Type de comparaison pour covenant."""
    GREATER = ">"
    GREATER_OR_EQUAL = ">="
    LESS = "<"
    LESS_OR_EQUAL = "<="


class Covenant(BaseModel):
    """
    Covenant bancaire (ratio à respecter).

    Les covenants sont des engagements contractuels pris
    envers la banque pour maintenir certains ratios.
    """
    name: str = Field(
        ...,
        description="Nom du covenant (ex: 'DSCR minimum')",
        min_length=1
    )
    metric_name: str = Field(
        ...,
        description="Nom de la métrique à surveiller (ex: 'dscr_french')"
    )
    threshold: float = Field(
        ...,
        description="Seuil à respecter"
    )
    comparison: CovenantComparison = Field(
        ...,
        description="Type de comparaison avec le seuil"
    )
    applicable_years: List[int] = Field(
        default_factory=list,
        description="Années d'application (ex: [1, 2, 3]) - vide = toutes"
    )

    def is_violated(self, actual_value: float, year: int = 1) -> bool:
        """
        Vérifie si le covenant est violé.

        Args:
            actual_value: Valeur réelle de la métrique
            year: Année de projection (1-indexed)

        Returns:
            True si covenant violé, False sinon
        """
        # Vérifier si applicable cette année
        if self.applicable_years and year not in self.applicable_years:
            return False

        if self.comparison == CovenantComparison.GREATER:
            return actual_value <= self.threshold
        elif self.comparison == CovenantComparison.GREATER_OR_EQUAL:
            return actual_value < self.threshold
        elif self.comparison == CovenantComparison.LESS:
            return actual_value >= self.threshold
        elif self.comparison == CovenantComparison.LESS_OR_EQUAL:
            return actual_value > self.threshold

        return False

    def get_status(self, actual_value: float, year: int = 1) -> str:
        """
        Retourne le statut du covenant.

        Returns:
            "PASS", "FAIL", ou "N/A"
        """
        if self.applicable_years and year not in self.applicable_years:
            return "N/A"

        return "FAIL" if self.is_violated(actual_value, year) else "PASS"


# =============================================================================
# DÉCISION D'ACQUISITION
# =============================================================================

class Decision(str, Enum):
    """Décision d'acquisition finale."""
    GO = "go"  # Acquisition recommandée
    WATCH = "watch"  # À renforcer / conditions
    NO_GO = "no_go"  # Acquisition déconseillée


class DecisionCriteria(BaseModel):
    """
    Critère de décision avec scoring.

    Chaque critère est évalué individuellement puis
    contribue au score global.
    """
    name: str = Field(
        ...,
        description="Nom du critère (ex: 'DSCR minimum')"
    )
    metric_name: str = Field(
        ...,
        description="Nom de la métrique associée"
    )
    actual_value: float = Field(
        ...,
        description="Valeur réelle obtenue"
    )
    threshold_excellent: float = Field(
        ...,
        description="Seuil pour score 100"
    )
    threshold_good: float = Field(
        ...,
        description="Seuil pour score 80"
    )
    threshold_acceptable: float = Field(
        ...,
        description="Seuil pour score 50"
    )
    score: int = Field(
        default=0,
        description="Score obtenu (0-100)",
        ge=0,
        le=100
    )
    weight: float = Field(
        default=1.0,
        description="Poids du critère dans le score global",
        ge=0,
        le=2.0
    )
    status: str = Field(
        default="",
        description="Statut: 'PASS', 'WARNING', 'FAIL'"
    )

    def calculate_score(self, higher_is_better: bool = True) -> int:
        """
        Calcule le score du critère (0-100).

        Args:
            higher_is_better: True si valeur haute = mieux (ex: DSCR)
                              False si valeur basse = mieux (ex: Dette/EBITDA)
        """
        if higher_is_better:
            if self.actual_value >= self.threshold_excellent:
                self.score = 100
                self.status = "PASS"
            elif self.actual_value >= self.threshold_good:
                self.score = 80
                self.status = "PASS"
            elif self.actual_value >= self.threshold_acceptable:
                self.score = 50
                self.status = "WARNING"
            else:
                self.score = 0
                self.status = "FAIL"
        else:
            if self.actual_value <= self.threshold_excellent:
                self.score = 100
                self.status = "PASS"
            elif self.actual_value <= self.threshold_good:
                self.score = 80
                self.status = "PASS"
            elif self.actual_value <= self.threshold_acceptable:
                self.score = 50
                self.status = "WARNING"
            else:
                self.score = 0
                self.status = "FAIL"

        return self.score


class AcquisitionDecision(BaseModel):
    """
    Décision d'acquisition finale avec justification.

    Agrège les résultats de tous les critères pour
    produire une recommandation GO/WATCH/NO-GO.
    """
    decision: Decision = Field(
        ...,
        description="Décision finale"
    )
    overall_score: int = Field(
        ...,
        description="Score global (0-100)",
        ge=0,
        le=100
    )
    criteria: List[DecisionCriteria] = Field(
        default_factory=list,
        description="Liste des critères évalués"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommandations pour améliorer le dossier"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Points d'attention"
    )
    deal_breakers: List[str] = Field(
        default_factory=list,
        description="Problèmes bloquants"
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Date/heure de la décision"
    )
    scenario_id: Optional[str] = Field(
        default=None,
        description="ID du scénario analysé"
    )

    @classmethod
    def from_criteria(
        cls,
        criteria: List[DecisionCriteria],
        scenario_id: Optional[str] = None
    ) -> 'AcquisitionDecision':
        """
        Crée une décision à partir des critères évalués.

        Logique de décision:
        - GO: Score >= 90 ET tous critères >= 80
        - WATCH: Score 70-89 OU 1-2 critères < 80
        - NO-GO: Score < 70 OU 1+ critère = 0
        """
        # Calcul score global pondéré
        total_weight = sum(c.weight for c in criteria)
        if total_weight == 0:
            overall_score = 0
        else:
            overall_score = int(
                sum(c.score * c.weight for c in criteria) / total_weight
            )

        # Identifier critères problématiques
        failed_criteria = [c for c in criteria if c.score == 0]
        warning_criteria = [c for c in criteria if c.score < 80 and c.score > 0]

        # Décision
        if failed_criteria:
            decision = Decision.NO_GO
        elif overall_score >= 90 and not warning_criteria:
            decision = Decision.GO
        elif overall_score >= 70:
            decision = Decision.WATCH
        else:
            decision = Decision.NO_GO

        # Génération recommandations
        recommendations = []
        warnings = []
        deal_breakers = []

        for criterion in failed_criteria:
            deal_breakers.append(
                f"❌ {criterion.name}: {criterion.actual_value:.2f} (seuil minimum: {criterion.threshold_acceptable:.2f})"
            )

        for criterion in warning_criteria:
            warnings.append(
                f"⚠️ {criterion.name}: {criterion.actual_value:.2f} (objectif: {criterion.threshold_good:.2f})"
            )

            # Recommandations spécifiques
            if "marge" in criterion.name.lower():
                recommendations.append(
                    "📊 Améliorer marge EBITDA: optimiser mix produits ou négocier prix"
                )
            elif "dscr" in criterion.name.lower():
                recommendations.append(
                    "💰 Améliorer DSCR: réduire dette ou augmenter equity"
                )
            elif "dette" in criterion.name.lower():
                recommendations.append(
                    "🏦 Réduire levier: négocier prix ou augmenter apport"
                )

        return cls(
            decision=decision,
            overall_score=overall_score,
            criteria=criteria,
            recommendations=recommendations,
            warnings=warnings,
            deal_breakers=deal_breakers,
            scenario_id=scenario_id
        )
