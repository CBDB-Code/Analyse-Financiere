"""
Modèles SQLAlchemy pour la base de données de l'analyse financière.

Ce module définit le schéma de la base de données SQLite avec:
- Company: Informations sur les entreprises
- FiscalYear: Exercices comptables avec données de la liasse fiscale
- Analysis: Analyses effectuées (banquier, entrepreneur, complète)
- Scenario: Scénarios de simulation
- CalculatedMetric: Métriques calculées
- Comparison/ComparisonItem: Comparaisons multi-entreprises

Utilise SQLAlchemy 2.0 avec le pattern DeclarativeBase et Mapped.
"""

from datetime import datetime, date
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    String,
    Text,
    Float,
    ForeignKey,
    Index,
    UniqueConstraint,
    Enum,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """
    Classe de base pour tous les modèles SQLAlchemy.

    Fournit la configuration commune et les métadonnées pour
    la génération automatique du schéma de base de données.
    """
    pass


class AnalysisType(str, PyEnum):
    """
    Types d'analyses financières disponibles.

    Attributes:
        BANKER: Analyse orientée banquier (risques, solvabilité)
        ENTREPRENEUR: Analyse orientée entrepreneur (performance, croissance)
        COMPLETE: Analyse complète combinant les deux perspectives
    """
    BANKER = "banker"
    ENTREPRENEUR = "entrepreneur"
    COMPLETE = "complete"


class MetricCategory(str, PyEnum):
    """
    Catégories de métriques calculées.

    Attributes:
        BANKER: Métriques pour l'analyse banquier
        ENTREPRENEUR: Métriques pour l'analyse entrepreneur
        STANDARD: Métriques standard communes
        SCENARIO: Métriques issues de simulations
    """
    BANKER = "banker"
    ENTREPRENEUR = "entrepreneur"
    STANDARD = "standard"
    SCENARIO = "scenario"


class Company(Base):
    """
    Modèle représentant une entreprise.

    Stocke les informations d'identification de l'entreprise
    et maintient les relations vers ses exercices fiscaux.

    Attributes:
        id: Identifiant unique auto-incrémenté
        name: Nom de l'entreprise (obligatoire)
        siren: Numéro SIREN unique à 9 chiffres (optionnel)
        sector: Secteur d'activité de l'entreprise (optionnel)
        created_at: Date de création de l'enregistrement
        updated_at: Date de dernière modification
        fiscal_years: Liste des exercices fiscaux associés
    """
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    siren: Mapped[Optional[str]] = mapped_column(String(9), unique=True, nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relation one-to-many vers FiscalYear
    fiscal_years: Mapped[List["FiscalYear"]] = relationship(
        "FiscalYear",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}', siren='{self.siren}')>"


class FiscalYear(Base):
    """
    Modèle représentant un exercice fiscal.

    Stocke les données complètes de la liasse fiscale au format JSON,
    ainsi que les métadonnées d'extraction et le chemin vers le PDF source.

    Attributes:
        id: Identifiant unique auto-incrémenté
        company_id: Clé étrangère vers l'entreprise
        year_end: Date de clôture de l'exercice (obligatoire)
        json_data: Données complètes de la liasse fiscale en JSON
        pdf_path: Chemin vers le fichier PDF source (optionnel)
        extraction_confidence: Score de confiance de l'extraction (0-1)
        created_at: Date de création de l'enregistrement
        updated_at: Date de dernière modification
        company: Référence vers l'entreprise parente
        analyses: Liste des analyses effectuées
    """
    __tablename__ = "fiscal_years"
    __table_args__ = (
        UniqueConstraint("company_id", "year_end", name="uq_company_year"),
        Index("ix_fiscal_years_company_id", "company_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False
    )
    year_end: Mapped[date] = mapped_column(nullable=False)
    json_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    extraction_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relation many-to-one vers Company
    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="fiscal_years"
    )

    # Relation one-to-many vers Analysis
    analyses: Mapped[List["Analysis"]] = relationship(
        "Analysis",
        back_populates="fiscal_year",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Relation one-to-many vers ComparisonItem
    comparison_items: Mapped[List["ComparisonItem"]] = relationship(
        "ComparisonItem",
        back_populates="fiscal_year",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<FiscalYear(id={self.id}, company_id={self.company_id}, year_end={self.year_end})>"


class Analysis(Base):
    """
    Modèle représentant une analyse financière.

    Une analyse est effectuée sur un exercice fiscal et peut être
    de type banquier, entrepreneur ou complète.

    Attributes:
        id: Identifiant unique auto-incrémenté
        fiscal_year_id: Clé étrangère vers l'exercice fiscal
        analysis_type: Type d'analyse (banker, entrepreneur, complete)
        created_at: Date de création de l'analyse
        fiscal_year: Référence vers l'exercice fiscal
        scenarios: Liste des scénarios de simulation
    """
    __tablename__ = "analyses"
    __table_args__ = (
        Index("ix_analyses_fiscal_year_id", "fiscal_year_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fiscal_year_id: Mapped[int] = mapped_column(
        ForeignKey("fiscal_years.id", ondelete="CASCADE"),
        nullable=False
    )
    analysis_type: Mapped[str] = mapped_column(
        Enum(AnalysisType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now()
    )

    # Relation many-to-one vers FiscalYear
    fiscal_year: Mapped["FiscalYear"] = relationship(
        "FiscalYear",
        back_populates="analyses"
    )

    # Relation one-to-many vers Scenario
    scenarios: Mapped[List["Scenario"]] = relationship(
        "Scenario",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, type='{self.analysis_type}', fiscal_year_id={self.fiscal_year_id})>"


class Scenario(Base):
    """
    Modèle représentant un scénario de simulation.

    Un scénario permet de tester différentes hypothèses
    sur les données financières et de calculer les impacts.

    Attributes:
        id: Identifiant unique auto-incrémenté
        analysis_id: Clé étrangère vers l'analyse parente
        name: Nom descriptif du scénario (obligatoire)
        parameters: Paramètres du scénario en JSON
        created_at: Date de création du scénario
        analysis: Référence vers l'analyse parente
        calculated_metrics: Liste des métriques calculées
    """
    __tablename__ = "scenarios"
    __table_args__ = (
        Index("ix_scenarios_analysis_id", "analysis_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parameters: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now()
    )

    # Relation many-to-one vers Analysis
    analysis: Mapped["Analysis"] = relationship(
        "Analysis",
        back_populates="scenarios"
    )

    # Relation one-to-many vers CalculatedMetric
    calculated_metrics: Mapped[List["CalculatedMetric"]] = relationship(
        "CalculatedMetric",
        back_populates="scenario",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Scenario(id={self.id}, name='{self.name}', analysis_id={self.analysis_id})>"


class CalculatedMetric(Base):
    """
    Modèle représentant une métrique financière calculée.

    Stocke les résultats des calculs pour chaque scénario,
    avec support pour les valeurs spéciales (inf, nan).

    Attributes:
        id: Identifiant unique auto-incrémenté
        scenario_id: Clé étrangère vers le scénario
        metric_name: Nom de la métrique (obligatoire)
        metric_category: Catégorie de la métrique (banker, entrepreneur, etc.)
        value: Valeur numérique (nullable pour inf/nan)
        metadata: Métadonnées additionnelles en JSON
        calculated_at: Date de calcul de la métrique
        scenario: Référence vers le scénario parent
    """
    __tablename__ = "calculated_metrics"
    __table_args__ = (
        UniqueConstraint("scenario_id", "metric_name", name="uq_scenario_metric"),
        Index("ix_calculated_metrics_scenario_id", "scenario_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"),
        nullable=False
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_category: Mapped[str] = mapped_column(
        Enum(MetricCategory, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now()
    )

    # Relation many-to-one vers Scenario
    scenario: Mapped["Scenario"] = relationship(
        "Scenario",
        back_populates="calculated_metrics"
    )

    def __repr__(self) -> str:
        return f"<CalculatedMetric(id={self.id}, name='{self.metric_name}', value={self.value})>"


class Comparison(Base):
    """
    Modèle représentant une comparaison multi-entreprises.

    Permet de grouper plusieurs exercices fiscaux pour
    les comparer côte à côte.

    Attributes:
        id: Identifiant unique auto-incrémenté
        name: Nom de la comparaison (obligatoire)
        created_at: Date de création de la comparaison
        items: Liste des éléments de comparaison
    """
    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now()
    )

    # Relation one-to-many vers ComparisonItem
    items: Mapped[List["ComparisonItem"]] = relationship(
        "ComparisonItem",
        back_populates="comparison",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Comparison(id={self.id}, name='{self.name}')>"


class ComparisonItem(Base):
    """
    Modèle représentant un élément de comparaison.

    Lie un exercice fiscal à une comparaison pour permettre
    les analyses comparatives.

    Attributes:
        id: Identifiant unique auto-incrémenté
        comparison_id: Clé étrangère vers la comparaison
        fiscal_year_id: Clé étrangère vers l'exercice fiscal
        comparison: Référence vers la comparaison parente
        fiscal_year: Référence vers l'exercice fiscal
    """
    __tablename__ = "comparison_items"
    __table_args__ = (
        UniqueConstraint("comparison_id", "fiscal_year_id", name="uq_comparison_fiscal_year"),
        Index("ix_comparison_items_comparison_id", "comparison_id"),
        Index("ix_comparison_items_fiscal_year_id", "fiscal_year_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comparison_id: Mapped[int] = mapped_column(
        ForeignKey("comparisons.id", ondelete="CASCADE"),
        nullable=False
    )
    fiscal_year_id: Mapped[int] = mapped_column(
        ForeignKey("fiscal_years.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relation many-to-one vers Comparison
    comparison: Mapped["Comparison"] = relationship(
        "Comparison",
        back_populates="items"
    )

    # Relation many-to-one vers FiscalYear
    fiscal_year: Mapped["FiscalYear"] = relationship(
        "FiscalYear",
        back_populates="comparison_items"
    )

    def __repr__(self) -> str:
        return f"<ComparisonItem(id={self.id}, comparison_id={self.comparison_id}, fiscal_year_id={self.fiscal_year_id})>"
