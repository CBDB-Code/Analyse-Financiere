"""
Orchestrateur principal pour l'extraction de liasses fiscales.

Ce module fournit la classe FiscalDataExtractor qui combine
l'extraction PDF native et le fallback AI pour obtenir les
meilleures données possibles depuis une liasse fiscale.
"""

import logging
from pathlib import Path
from typing import Optional, Union
from datetime import date
from dataclasses import dataclass, field

from ..core.models import (
    FiscalData,
    Metadata,
    BalanceSheet,
    IncomeStatement,
    Assets,
    FixedAssets,
    CurrentAssets,
    Liabilities,
    Equity,
    Provisions,
    Debt,
    OperatingLiabilities,
    Revenues,
    OperatingExpenses,
    FinancialResult,
    ExceptionalResult,
    FinancialField,
)

from .pdf_parser import PDFParser
from .ai_fallback import AIExtractor
from .exceptions import (
    ExtractionError,
    InvalidPDFError,
    ValidationError,
    AIExtractionError,
)


logger = logging.getLogger(__name__)


@dataclass
class ExtractionReport:
    """
    Rapport détaillé d'une extraction.

    Attributes:
        pdf_path: Chemin du fichier PDF traité.
        success: Indique si l'extraction a réussi.
        method_used: Méthode d'extraction utilisée ("pdf_parser", "ai_claude", "hybrid").
        confidence_score: Score de confiance (0-1).
        validation_passed: Si la validation des données a réussi.
        validation_errors: Liste des erreurs de validation.
        warnings: Avertissements lors de l'extraction.
        form_types: Types de formulaires détectés.
        is_scanned: Si le PDF était scanné.
        tokens_used: Tokens API utilisés (si AI).
        cost_estimate: Coût estimé en USD (si AI).
        duration_seconds: Durée de l'extraction.
    """
    pdf_path: str
    success: bool = False
    method_used: str = ""
    confidence_score: float = 0.0
    validation_passed: bool = False
    validation_errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    form_types: list = field(default_factory=list)
    is_scanned: bool = False
    tokens_used: int = 0
    cost_estimate: float = 0.0
    duration_seconds: float = 0.0


class FiscalDataExtractor:
    """
    Orchestrateur principal pour l'extraction de liasses fiscales.

    Cette classe combine PDFParser (extraction textuelle) et AIExtractor
    (extraction via Claude) pour maximiser la qualité des données extraites.

    Stratégie d'extraction:
    1. Tenter l'extraction PDF native (rapide, gratuite)
    2. Valider les données extraites
    3. Si échec et use_ai_fallback=True, utiliser Claude AI
    4. Retourner les données au format FiscalData (Pydantic)

    Attributes:
        pdf_parser: Instance de PDFParser.
        ai_extractor: Instance de AIExtractor (lazy loading).
        use_ai_fallback: Active le fallback AI.
        validation_threshold: Seuil de confiance minimum.

    Example:
        >>> extractor = FiscalDataExtractor()
        >>> fiscal_data = extractor.extract("/path/to/liasse.pdf")
        >>> print(fiscal_data.income_statement.net_income)
    """

    # Seuil de confiance minimum pour accepter l'extraction PDF native
    DEFAULT_CONFIDENCE_THRESHOLD = 0.5

    def __init__(
        self,
        use_ai_fallback: bool = True,
        ai_api_key: Optional[str] = None,
        ai_model: Optional[str] = None,
        validation_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        cache_ai_results: bool = True
    ):
        """
        Initialise l'extracteur.

        Args:
            use_ai_fallback: Active le fallback AI si extraction PDF insuffisante.
            ai_api_key: Clé API Anthropic pour le fallback AI.
            ai_model: Modèle Claude à utiliser.
            validation_threshold: Seuil de confiance pour l'extraction PDF.
            cache_ai_results: Cache les résultats AI pour économiser les appels.
        """
        self.use_ai_fallback = use_ai_fallback
        self.ai_api_key = ai_api_key
        self.ai_model = ai_model
        self.validation_threshold = validation_threshold
        self.cache_ai_results = cache_ai_results

        # Initialisation lazy des extracteurs
        self._pdf_parser: Optional[PDFParser] = None
        self._ai_extractor: Optional[AIExtractor] = None

        # Rapport de la dernière extraction
        self._last_report: Optional[ExtractionReport] = None

        logger.info(
            f"FiscalDataExtractor initialisé - "
            f"AI fallback: {use_ai_fallback}, "
            f"Seuil validation: {validation_threshold}"
        )

    @property
    def pdf_parser(self) -> PDFParser:
        """Retourne le PDFParser (lazy loading)."""
        if self._pdf_parser is None:
            self._pdf_parser = PDFParser()
        return self._pdf_parser

    @property
    def ai_extractor(self) -> AIExtractor:
        """Retourne l'AIExtractor (lazy loading)."""
        if self._ai_extractor is None:
            self._ai_extractor = AIExtractor(
                api_key=self.ai_api_key,
                model=self.ai_model
            )
        return self._ai_extractor

    def extract(
        self,
        pdf_path: str,
        use_ai_fallback: Optional[bool] = None,
        validate: bool = True
    ) -> FiscalData:
        """
        Extrait les données d'une liasse fiscale et retourne un FiscalData.

        Cette méthode est le point d'entrée principal. Elle:
        1. Tente l'extraction PDF native
        2. Valide les données
        3. Utilise le fallback AI si nécessaire
        4. Convertit les données en modèle Pydantic FiscalData

        Args:
            pdf_path: Chemin vers le fichier PDF.
            use_ai_fallback: Override du paramètre global use_ai_fallback.
            validate: Valider les données avant de retourner.

        Returns:
            Instance de FiscalData contenant toutes les données extraites.

        Raises:
            InvalidPDFError: Si le fichier PDF est invalide.
            ExtractionError: Si l'extraction échoue complètement.
            ValidationError: Si les données sont invalides et validate=True.

        Example:
            >>> extractor = FiscalDataExtractor()
            >>> data = extractor.extract("/path/to/liasse_2050.pdf")
            >>> print(f"Total actif: {data.balance_sheet.assets.total_assets}")
            >>> print(f"Résultat net: {data.income_statement.net_income}")
        """
        import time
        start_time = time.time()

        pdf_path = Path(pdf_path)
        use_fallback = use_ai_fallback if use_ai_fallback is not None else self.use_ai_fallback

        # Initialiser le rapport
        report = ExtractionReport(pdf_path=str(pdf_path))

        logger.info(f"Début extraction: {pdf_path}")

        # Phase 1: Extraction PDF native
        raw_data = None
        pdf_extraction_ok = False

        try:
            raw_data = self.pdf_parser.extract_from_pdf(str(pdf_path))
            pdf_extraction_ok = True
            report.method_used = "pdf_parser"
            report.is_scanned = raw_data.get("is_scanned", False)
            report.form_types = raw_data.get("form_types", [])
            report.confidence_score = raw_data.get("extraction_confidence", 0.0)

            logger.info(
                f"Extraction PDF terminée - "
                f"Confiance: {report.confidence_score:.2f}, "
                f"Formulaires: {report.form_types}"
            )

            # Valider les données
            is_valid, errors = self.pdf_parser.validate_data(raw_data)
            report.validation_passed = is_valid
            report.validation_errors = errors

        except InvalidPDFError:
            # PDF invalide - pas de fallback possible
            raise
        except Exception as e:
            logger.warning(f"Extraction PDF échouée: {e}")
            report.warnings.append(f"Extraction PDF échouée: {e}")

        # Phase 2: Décider si on utilise le fallback AI
        needs_ai_fallback = False

        if not pdf_extraction_ok:
            needs_ai_fallback = True
            logger.info("Extraction PDF échouée - fallback AI nécessaire")
        elif report.confidence_score < self.validation_threshold:
            needs_ai_fallback = True
            logger.info(
                f"Confiance insuffisante ({report.confidence_score:.2f} < "
                f"{self.validation_threshold}) - fallback AI suggéré"
            )
        elif report.is_scanned:
            needs_ai_fallback = True
            logger.info("PDF scanné détecté - fallback AI suggéré")
        elif not report.validation_passed:
            needs_ai_fallback = True
            logger.info(
                f"Validation échouée ({len(report.validation_errors)} erreurs) - "
                f"fallback AI suggéré"
            )

        # Phase 3: Fallback AI si nécessaire et activé
        if needs_ai_fallback and use_fallback:
            try:
                logger.info("Tentative d'extraction via Claude AI...")
                ai_data = self.ai_extractor.extract_with_claude(str(pdf_path))

                # Fusionner ou remplacer les données
                if pdf_extraction_ok:
                    # Mode hybride: garder les meilleures données
                    raw_data = self._merge_extraction_results(raw_data, ai_data)
                    report.method_used = "hybrid"
                else:
                    raw_data = ai_data
                    report.method_used = "ai_claude"

                report.confidence_score = 0.85  # Score de confiance AI
                report.form_types = ai_data.get("metadata", {}).get("form_types", [])

                # Re-valider après AI
                # Note: La validation sera faite lors de la conversion Pydantic

                logger.info("Extraction AI réussie")

            except AIExtractionError as e:
                logger.error(f"Fallback AI échoué: {e}")
                report.warnings.append(f"Fallback AI échoué: {e}")

                if not pdf_extraction_ok:
                    raise ExtractionError(
                        f"Toutes les méthodes d'extraction ont échoué",
                        pdf_path=str(pdf_path)
                    )

        # Phase 4: Vérifier qu'on a des données
        if raw_data is None:
            raise ExtractionError(
                "Aucune donnée extraite du PDF",
                pdf_path=str(pdf_path)
            )

        # Phase 5: Convertir en FiscalData (Pydantic)
        try:
            fiscal_data = self._convert_to_fiscal_data(raw_data)
            report.success = True
        except Exception as e:
            logger.error(f"Conversion en FiscalData échouée: {e}")
            if validate:
                raise ValidationError(
                    f"Données extraites invalides: {e}",
                    errors=[str(e)],
                    pdf_path=str(pdf_path)
                )
            else:
                # Créer un FiscalData minimal
                fiscal_data = self._create_minimal_fiscal_data(raw_data)
                report.warnings.append(f"Conversion partielle: {e}")
                report.success = True

        # Finaliser le rapport
        report.duration_seconds = time.time() - start_time
        self._last_report = report

        logger.info(
            f"Extraction terminée en {report.duration_seconds:.2f}s - "
            f"Méthode: {report.method_used}, "
            f"Succès: {report.success}"
        )

        return fiscal_data

    def get_extraction_report(self, pdf_path: Optional[str] = None) -> ExtractionReport:
        """
        Retourne le rapport de la dernière extraction.

        Si pdf_path est fourni, effectue une nouvelle extraction
        et retourne le rapport.

        Args:
            pdf_path: Chemin vers le PDF (optionnel).

        Returns:
            Rapport détaillé de l'extraction.

        Example:
            >>> extractor = FiscalDataExtractor()
            >>> data = extractor.extract("/path/to/liasse.pdf")
            >>> report = extractor.get_extraction_report()
            >>> print(f"Méthode: {report.method_used}")
            >>> print(f"Confiance: {report.confidence_score}")
        """
        if pdf_path:
            # Effectuer l'extraction pour générer le rapport
            try:
                self.extract(pdf_path, validate=False)
            except Exception:
                pass  # Le rapport sera quand même rempli

        if self._last_report is None:
            return ExtractionReport(pdf_path=pdf_path or "")

        return self._last_report

    def _merge_extraction_results(
        self,
        pdf_data: dict,
        ai_data: dict
    ) -> dict:
        """
        Fusionne les résultats PDF et AI en privilégiant AI.

        Args:
            pdf_data: Données extraites par PDFParser.
            ai_data: Données extraites par AIExtractor.

        Returns:
            Données fusionnées.
        """
        result = {}

        # Métadonnées: combiner les deux
        pdf_meta = pdf_data.get("metadata", {})
        ai_meta = ai_data.get("metadata", {})
        result["metadata"] = {**pdf_meta, **ai_meta}

        # Balance sheet: préférer AI
        result["balance_sheet"] = ai_data.get(
            "balance_sheet",
            pdf_data.get("balance_sheet", {})
        )

        # Income statement: préférer AI
        result["income_statement"] = ai_data.get(
            "income_statement",
            pdf_data.get("income_statement", {})
        )

        # Raw fields: combiner
        pdf_fields = pdf_data.get("raw_fields", {})
        ai_fields = ai_data.get("raw_fields", {})
        result["raw_fields"] = {**pdf_fields, **ai_fields}

        # Autres champs
        result["form_types"] = ai_data.get(
            "form_types",
            pdf_data.get("form_types", [])
        )
        result["is_scanned"] = pdf_data.get("is_scanned", True)

        return result

    def _convert_to_fiscal_data(self, raw_data: dict) -> FiscalData:
        """
        Convertit les données brutes en instance FiscalData.

        Args:
            raw_data: Dictionnaire avec les données extraites.

        Returns:
            Instance FiscalData validée.
        """
        # Extraire les sous-dictionnaires
        meta_dict = raw_data.get("metadata", {})
        bs_dict = raw_data.get("balance_sheet", {})
        is_dict = raw_data.get("income_statement", {})
        raw_fields_dict = raw_data.get("raw_fields", {})

        # Construire Metadata
        metadata = Metadata(
            company_name=meta_dict.get("company_name", "Entreprise non identifiée"),
            siren=meta_dict.get("siren", "000000000"),
            siret=meta_dict.get("siret"),
            naf_code=meta_dict.get("naf_code"),
            legal_form=meta_dict.get("legal_form"),
            fiscal_year_start=self._parse_date(meta_dict.get("fiscal_year_start")),
            fiscal_year_end=self._parse_date(meta_dict.get("fiscal_year_end")) or date.today(),
            fiscal_year_duration_months=meta_dict.get("fiscal_year_duration_months", 12),
            extraction_date=date.today(),
            source_file=meta_dict.get("source_file"),
            form_types=meta_dict.get("form_types", []),
            confidence_score=raw_data.get("extraction_confidence", 1.0),
            extraction_warnings=meta_dict.get("extraction_warnings", [])
        )

        # Construire BalanceSheet
        balance_sheet = self._build_balance_sheet(bs_dict)

        # Construire IncomeStatement
        income_statement = self._build_income_statement(is_dict)

        # Construire raw_fields
        raw_fields = {}
        for code, field_data in raw_fields_dict.items():
            if isinstance(field_data, dict):
                value = field_data.get("value", 0.0)
            else:
                value = float(field_data) if field_data else 0.0
            raw_fields[code] = FinancialField(code=code, value=value)

        # Créer FiscalData
        fiscal_data = FiscalData(
            metadata=metadata,
            balance_sheet=balance_sheet,
            income_statement=income_statement,
            raw_fields=raw_fields if raw_fields else None
        )

        return fiscal_data

    def _build_balance_sheet(self, bs_dict: dict) -> BalanceSheet:
        """Construit un BalanceSheet depuis un dictionnaire."""
        assets_dict = bs_dict.get("assets", {})
        liab_dict = bs_dict.get("liabilities", {})

        # Fixed Assets
        fa_dict = assets_dict.get("fixed_assets", {})
        fixed_assets = FixedAssets(
            intangible_assets=fa_dict.get("intangible_assets", 0.0),
            tangible_assets=fa_dict.get("tangible_assets", 0.0),
            financial_assets=fa_dict.get("financial_assets", 0.0),
            total=fa_dict.get("total", 0.0)
        )

        # Current Assets
        ca_dict = assets_dict.get("current_assets", {})
        current_assets = CurrentAssets(
            inventory=ca_dict.get("inventory", 0.0),
            trade_receivables=ca_dict.get("trade_receivables", 0.0),
            other_receivables=ca_dict.get("other_receivables", 0.0),
            prepaid_expenses=ca_dict.get("prepaid_expenses", 0.0),
            marketable_securities=ca_dict.get("marketable_securities", 0.0),
            cash=ca_dict.get("cash", 0.0),
            total=ca_dict.get("total", 0.0)
        )

        # Assets
        assets = Assets(
            fixed_assets=fixed_assets,
            current_assets=current_assets,
            total_assets=assets_dict.get("total_assets", 0.0)
        )

        # Equity
        eq_dict = liab_dict.get("equity", {})
        equity = Equity(
            share_capital=eq_dict.get("share_capital", 0.0),
            share_premium=eq_dict.get("share_premium", 0.0),
            revaluation_reserve=eq_dict.get("revaluation_reserve", 0.0),
            legal_reserve=eq_dict.get("legal_reserve", 0.0),
            statutory_reserves=eq_dict.get("statutory_reserves", 0.0),
            other_reserves=eq_dict.get("other_reserves", 0.0),
            retained_earnings=eq_dict.get("retained_earnings", 0.0),
            net_income=eq_dict.get("net_income", 0.0),
            investment_subsidies=eq_dict.get("investment_subsidies", 0.0),
            regulated_provisions=eq_dict.get("regulated_provisions", 0.0),
            total=eq_dict.get("total", 0.0)
        )

        # Provisions
        prov_dict = liab_dict.get("provisions", {})
        provisions = Provisions(
            provisions_for_risks=prov_dict.get("provisions_for_risks", 0.0),
            provisions_for_charges=prov_dict.get("provisions_for_charges", 0.0),
            total=prov_dict.get("total", 0.0)
        )

        # Debt
        debt_dict = liab_dict.get("debt", {})
        debt = Debt(
            long_term_debt=debt_dict.get("long_term_debt", 0.0),
            short_term_debt=debt_dict.get("short_term_debt", 0.0),
            bank_overdrafts=debt_dict.get("bank_overdrafts", 0.0),
            lease_obligations=debt_dict.get("lease_obligations", 0.0),
            bonds=debt_dict.get("bonds", 0.0),
            shareholder_loans=debt_dict.get("shareholder_loans", 0.0),
            total_financial_debt=debt_dict.get("total_financial_debt", 0.0)
        )

        # Operating Liabilities
        op_dict = liab_dict.get("operating_liabilities", {})
        operating_liabilities = OperatingLiabilities(
            trade_payables=op_dict.get("trade_payables", 0.0),
            tax_liabilities=op_dict.get("tax_liabilities", 0.0),
            social_liabilities=op_dict.get("social_liabilities", 0.0),
            advances_received=op_dict.get("advances_received", 0.0),
            deferred_revenue=op_dict.get("deferred_revenue", 0.0),
            other_liabilities=op_dict.get("other_liabilities", 0.0),
            total=op_dict.get("total", 0.0)
        )

        # Liabilities
        liabilities = Liabilities(
            equity=equity,
            provisions=provisions,
            debt=debt,
            operating_liabilities=operating_liabilities,
            total_liabilities=liab_dict.get("total_liabilities", 0.0)
        )

        return BalanceSheet(assets=assets, liabilities=liabilities)

    def _build_income_statement(self, is_dict: dict) -> IncomeStatement:
        """Construit un IncomeStatement depuis un dictionnaire."""
        # Revenues
        rev_dict = is_dict.get("revenues", {})
        revenues = Revenues(
            sales_of_goods=rev_dict.get("sales_of_goods", 0.0),
            sales_of_services=rev_dict.get("sales_of_services", 0.0),
            sales_of_products=rev_dict.get("sales_of_products", 0.0),
            net_revenue=rev_dict.get("net_revenue", 0.0),
            stored_production=rev_dict.get("stored_production", 0.0),
            capitalized_production=rev_dict.get("capitalized_production", 0.0),
            operating_subsidies=rev_dict.get("operating_subsidies", 0.0),
            other_operating_income=rev_dict.get("other_operating_income", 0.0),
            reversal_of_provisions=rev_dict.get("reversal_of_provisions", 0.0),
            total=rev_dict.get("total", 0.0)
        )

        # Operating Expenses
        exp_dict = is_dict.get("operating_expenses", {})
        operating_expenses = OperatingExpenses(
            purchases_of_goods=exp_dict.get("purchases_of_goods", 0.0),
            purchases_of_raw_materials=exp_dict.get("purchases_of_raw_materials", 0.0),
            inventory_variation=exp_dict.get("inventory_variation", 0.0),
            external_charges=exp_dict.get("external_charges", 0.0),
            taxes_and_duties=exp_dict.get("taxes_and_duties", 0.0),
            wages_and_salaries=exp_dict.get("wages_and_salaries", 0.0),
            social_charges=exp_dict.get("social_charges", 0.0),
            personnel_costs=exp_dict.get("personnel_costs", 0.0),
            depreciation=exp_dict.get("depreciation", 0.0),
            provisions=exp_dict.get("provisions", 0.0),
            other_operating_expenses=exp_dict.get("other_operating_expenses", 0.0),
            total=exp_dict.get("total", 0.0)
        )

        # Financial Result
        fin_dict = is_dict.get("financial_result", {})
        financial_result = FinancialResult(
            financial_income=fin_dict.get("financial_income", 0.0),
            interest_income=fin_dict.get("interest_income", 0.0),
            reversal_of_financial_provisions=fin_dict.get("reversal_of_financial_provisions", 0.0),
            foreign_exchange_gains=fin_dict.get("foreign_exchange_gains", 0.0),
            total_financial_income=fin_dict.get("total_financial_income", 0.0),
            interest_expense=fin_dict.get("interest_expense", 0.0),
            financial_provisions=fin_dict.get("financial_provisions", 0.0),
            foreign_exchange_losses=fin_dict.get("foreign_exchange_losses", 0.0),
            total_financial_expense=fin_dict.get("total_financial_expense", 0.0),
            net_financial_result=fin_dict.get("net_financial_result", 0.0)
        )

        # Exceptional Result
        exc_dict = is_dict.get("exceptional_result", {})
        exceptional_result = ExceptionalResult(
            exceptional_income=exc_dict.get("exceptional_income", 0.0),
            exceptional_income_capital=exc_dict.get("exceptional_income_capital", 0.0),
            reversal_of_exceptional_provisions=exc_dict.get("reversal_of_exceptional_provisions", 0.0),
            total_exceptional_income=exc_dict.get("total_exceptional_income", 0.0),
            exceptional_expense=exc_dict.get("exceptional_expense", 0.0),
            exceptional_expense_capital=exc_dict.get("exceptional_expense_capital", 0.0),
            exceptional_provisions=exc_dict.get("exceptional_provisions", 0.0),
            total_exceptional_expense=exc_dict.get("total_exceptional_expense", 0.0),
            net_exceptional_result=exc_dict.get("net_exceptional_result", 0.0)
        )

        return IncomeStatement(
            revenues=revenues,
            operating_expenses=operating_expenses,
            operating_income=is_dict.get("operating_income", 0.0),
            financial_result=financial_result,
            current_income_before_tax=is_dict.get("current_income_before_tax", 0.0),
            exceptional_result=exceptional_result,
            employee_profit_sharing=is_dict.get("employee_profit_sharing", 0.0),
            income_tax_expense=is_dict.get("income_tax_expense", 0.0),
            net_income=is_dict.get("net_income", 0.0)
        )

    def _create_minimal_fiscal_data(self, raw_data: dict) -> FiscalData:
        """Crée un FiscalData minimal en cas d'erreur de conversion."""
        meta_dict = raw_data.get("metadata", {})

        metadata = Metadata(
            company_name=meta_dict.get("company_name", "Non identifié"),
            siren=meta_dict.get("siren", "000000000"),
            fiscal_year_end=date.today(),
            extraction_date=date.today(),
            confidence_score=0.3,
            extraction_warnings=["Conversion partielle - données incomplètes"]
        )

        return FiscalData(
            metadata=metadata,
            balance_sheet=BalanceSheet(),
            income_statement=IncomeStatement()
        )

    def _parse_date(self, date_value: Optional[Union[str, date]]) -> Optional[date]:
        """Parse une valeur en date."""
        if date_value is None:
            return None

        if isinstance(date_value, date):
            return date_value

        if isinstance(date_value, str):
            try:
                from datetime import datetime
                # Format ISO
                return datetime.strptime(date_value, "%Y-%m-%d").date()
            except ValueError:
                try:
                    # Format français
                    return datetime.strptime(date_value, "%d/%m/%Y").date()
                except ValueError:
                    return None

        return None


# =============================================================================
# FONCTION UTILITAIRE POUR USAGE SIMPLE
# =============================================================================

def extract_fiscal_data(
    pdf_path: str,
    use_ai_fallback: bool = True,
    api_key: Optional[str] = None
) -> FiscalData:
    """
    Fonction utilitaire pour extraire simplement une liasse fiscale.

    Args:
        pdf_path: Chemin vers le fichier PDF.
        use_ai_fallback: Utiliser Claude AI si extraction PDF insuffisante.
        api_key: Clé API Anthropic (optionnel).

    Returns:
        Instance FiscalData avec les données extraites.

    Example:
        >>> from src.extraction import extract_fiscal_data
        >>> data = extract_fiscal_data("/path/to/liasse.pdf")
        >>> print(f"CA: {data.income_statement.revenues.net_revenue}")
    """
    extractor = FiscalDataExtractor(
        use_ai_fallback=use_ai_fallback,
        ai_api_key=api_key
    )
    return extractor.extract(pdf_path)
