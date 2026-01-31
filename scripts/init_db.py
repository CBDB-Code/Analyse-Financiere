"""
Script d'initialisation de la base de donnees SQLite.

Ce script cree le schema de la base de donnees et optionnellement
y ajoute des donnees d'exemple pour les tests.

Usage:
    python scripts/init_db.py
"""

import sys
import json
from pathlib import Path
from datetime import date, datetime

# Ajoute le repertoire racine au path pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    Base,
    Company,
    FiscalYear,
    Analysis,
    Scenario,
    CalculatedMetric,
    AnalysisType,
    MetricCategory,
)


def create_database(db_path: str = "data/database/financials.db"):
    """
    Cree la base de donnees SQLite avec tous les schemas.

    Args:
        db_path: Chemin relatif vers le fichier de base de donnees.
                 Par defaut: data/database/financials.db

    Returns:
        Engine: L'engine SQLAlchemy connecte a la base de donnees

    Raises:
        Exception: Si la creation echoue
    """
    try:
        # Chemin absolu depuis la racine du projet
        full_path = project_root / db_path

        # Cree le dossier parent si necessaire
        full_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Creation de la base de donnees: {full_path}")

        # Cree l'engine SQLAlchemy
        engine = create_engine(
            f"sqlite:///{full_path}",
            echo=False,  # Mettre a True pour debug SQL
            future=True
        )

        # Cree toutes les tables definies dans Base
        Base.metadata.create_all(engine)

        print("Schema de base de donnees cree avec succes!")
        print(f"Tables creees: {', '.join(Base.metadata.tables.keys())}")

        return engine

    except Exception as e:
        print(f"Erreur lors de la creation de la base de donnees: {e}")
        raise


def seed_sample_data(engine):
    """
    Ajoute des donnees d'exemple dans la base de donnees.

    Cette fonction cree:
    - Une entreprise exemple
    - Un exercice fiscal avec des donnees JSON factices
    - Une analyse de type 'complete'
    - Un scenario de base

    Args:
        engine: L'engine SQLAlchemy connecte a la base de donnees

    Returns:
        Company: L'entreprise creee

    Raises:
        Exception: Si l'insertion echoue
    """
    try:
        # Creation de la session
        Session = sessionmaker(bind=engine)
        session = Session()

        print("Ajout des donnees d'exemple...")

        # Donnees financieres JSON factices
        sample_fiscal_data = {
            "balance_sheet": {
                "assets": {
                    "fixed_assets": {
                        "intangible_assets": 50000,
                        "tangible_assets": 300000,
                        "financial_assets": 20000,
                        "total": 370000
                    },
                    "current_assets": {
                        "inventory": 150000,
                        "trade_receivables": 200000,
                        "other_receivables": 30000,
                        "prepaid_expenses": 10000,
                        "marketable_securities": 25000,
                        "cash": 100000,
                        "total": 515000
                    },
                    "total_assets": 885000
                },
                "liabilities": {
                    "equity": {
                        "share_capital": 200000,
                        "share_premium": 50000,
                        "legal_reserve": 20000,
                        "retained_earnings": 80000,
                        "net_income": 75000,
                        "total": 425000
                    },
                    "provisions": {
                        "provisions_for_risks": 15000,
                        "provisions_for_charges": 10000,
                        "total": 25000
                    },
                    "debt": {
                        "long_term_debt": 200000,
                        "short_term_debt": 50000,
                        "bank_overdrafts": 10000,
                        "total_financial_debt": 260000
                    },
                    "operating_liabilities": {
                        "trade_payables": 120000,
                        "tax_liabilities": 25000,
                        "social_liabilities": 30000,
                        "total": 175000
                    },
                    "total_liabilities": 885000
                }
            },
            "income_statement": {
                "revenues": {
                    "sales_of_goods": 500000,
                    "sales_of_services": 700000,
                    "net_revenue": 1200000,
                    "total": 1220000
                },
                "operating_expenses": {
                    "purchases_of_goods": 300000,
                    "purchases_of_raw_materials": 100000,
                    "external_charges": 150000,
                    "wages_and_salaries": 250000,
                    "social_charges": 100000,
                    "depreciation": 50000,
                    "provisions": 10000,
                    "total": 1000000
                },
                "operating_income": 220000,
                "financial_result": {
                    "interest_expense": 25000,
                    "net_financial_result": -20000
                },
                "net_income": 75000
            },
            "metadata": {
                "company_name": "Exemple SARL",
                "siren": "123456789",
                "fiscal_year_end": "2024-12-31",
                "extraction_date": datetime.now().isoformat()
            }
        }

        # Creation de l'entreprise exemple
        company = Company(
            name="Exemple SARL",
            siren="123456789",
            sector="Services"
        )
        session.add(company)
        session.flush()  # Pour obtenir l'ID

        print(f"Entreprise creee: {company.name} (ID: {company.id})")

        # Creation de l'exercice fiscal
        fiscal_year = FiscalYear(
            company_id=company.id,
            year_end=date(2024, 12, 31),
            json_data=json.dumps(sample_fiscal_data, ensure_ascii=False, indent=2),
            pdf_path=None,
            extraction_confidence=0.95
        )
        session.add(fiscal_year)
        session.flush()

        print(f"Exercice fiscal cree: {fiscal_year.year_end} (ID: {fiscal_year.id})")

        # Creation d'une analyse
        analysis = Analysis(
            fiscal_year_id=fiscal_year.id,
            analysis_type=AnalysisType.COMPLETE.value
        )
        session.add(analysis)
        session.flush()

        print(f"Analyse creee: {analysis.analysis_type} (ID: {analysis.id})")

        # Creation d'un scenario
        scenario_params = {
            "name": "Scenario de base",
            "debt": {
                "debt_amount": 500000,
                "interest_rate": 0.05,
                "loan_duration": 7,
                "grace_period": 0,
                "amortization_type": "constant"
            },
            "equity": {
                "equity_amount": 500000,
                "target_roe": 0.12,
                "exit_multiple": 6.0,
                "holding_period": 5
            },
            "growth": {
                "revenue_growth": 0.05,
                "ebitda_margin_evolution": 0.0,
                "capex_percentage": 0.03,
                "inflation_rate": 0.02
            }
        }

        scenario = Scenario(
            analysis_id=analysis.id,
            name="Scenario de base",
            parameters=json.dumps(scenario_params, ensure_ascii=False)
        )
        session.add(scenario)
        session.flush()

        print(f"Scenario cree: {scenario.name} (ID: {scenario.id})")

        # Ajout de quelques metriques calculees
        sample_metrics = [
            ("dscr", MetricCategory.BANKER.value, 2.15),
            ("icr", MetricCategory.BANKER.value, 8.8),
            ("roe", MetricCategory.ENTREPRENEUR.value, 17.65),
            ("payback_period", MetricCategory.ENTREPRENEUR.value, 2.83),
            ("ebitda", MetricCategory.STANDARD.value, 280000.0),
            ("marge_brute", MetricCategory.STANDARD.value, 67.5),
            ("fonds_de_roulement", MetricCategory.STANDARD.value, 280000.0),
            ("bfr", MetricCategory.STANDARD.value, 95000.0),
        ]

        for metric_name, category, value in sample_metrics:
            metric = CalculatedMetric(
                scenario_id=scenario.id,
                metric_name=metric_name,
                metric_category=category,
                value=value
            )
            session.add(metric)

        print(f"Metriques calculees ajoutees: {len(sample_metrics)}")

        # Commit des changements
        session.commit()

        print("Donnees d'exemple ajoutees avec succes!")

        return company

    except Exception as e:
        session.rollback()
        print(f"Erreur lors de l'ajout des donnees d'exemple: {e}")
        raise

    finally:
        session.close()


def main():
    """
    Point d'entree principal du script.

    Cree la base de donnees et optionnellement ajoute des donnees d'exemple.
    """
    print("=" * 60)
    print("Initialisation de la base de donnees")
    print("=" * 60)

    try:
        # Creation de la base de donnees
        engine = create_database()

        # Demande si on veut ajouter des donnees d'exemple
        # Pour le MVP, on les ajoute par defaut
        print()
        print("-" * 60)
        print("Ajout des donnees d'exemple...")
        print("-" * 60)

        try:
            seed_sample_data(engine)
        except Exception as e:
            print(f"Note: Les donnees d'exemple n'ont pas pu etre ajoutees: {e}")
            print("Cela peut etre normal si les donnees existent deja.")

        print()
        print("=" * 60)
        print("Base de donnees initialisee avec succes!")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERREUR: {e}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
