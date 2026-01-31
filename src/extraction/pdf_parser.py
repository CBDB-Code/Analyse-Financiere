"""
Parseur de PDF pour l'extraction de liasses fiscales françaises.

Ce module fournit la classe PDFParser qui extrait les données
depuis les formulaires fiscaux français (2033, 2050-2059) au format PDF.
"""

import re
import logging
from pathlib import Path
from typing import Optional, Any
from datetime import date

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

from .exceptions import (
    ExtractionError,
    InvalidPDFError,
    EmptyPDFError,
    PasswordProtectedPDFError,
    UnsupportedFormTypeError,
    ParsingError,
    DependencyError,
)
from .utils import (
    clean_amount,
    find_field_by_code,
    is_pdf_scanned,
    validate_siren,
    get_field_path_for_code,
    FISCAL_CODE_MAPPING_2050,
    FISCAL_CODE_MAPPING_2051,
    FISCAL_CODE_MAPPING_2052,
    FISCAL_CODE_MAPPING_2053,
)


logger = logging.getLogger(__name__)


class PDFParser:
    """
    Classe principale pour l'extraction de données depuis les PDFs
    de liasses fiscales françaises.

    Supporte les formulaires:
    - 2033 A-G (régime simplifié d'imposition)
    - 2050-2059 (régime réel normal)

    Attributes:
        pdf_path: Chemin vers le fichier PDF.
        is_scanned: Indique si le PDF est scanné (OCR nécessaire).
        form_types: Types de formulaires détectés.
        raw_text: Texte brut extrait du PDF.
        tables: Tableaux extraits du PDF.

    Example:
        >>> parser = PDFParser()
        >>> data = parser.extract_from_pdf("/path/to/liasse.pdf")
        >>> print(data["balance_sheet"]["assets"]["total"])
    """

    # Signatures textuelles pour la détection des types de formulaires
    FORM_SIGNATURES = {
        "2033-A": [
            "2033-A",
            "BILAN SIMPLIFIE",
            "REGIME SIMPLIFIE",
            "régime simplifié",
            "TABLEAU 2033-A"
        ],
        "2033-B": [
            "2033-B",
            "COMPTE DE RESULTAT SIMPLIFIE",
            "TABLEAU 2033-B"
        ],
        "2050": [
            "2050",
            "BILAN - ACTIF",
            "BILAN ACTIF",
            "TABLEAU 2050",
            "ACTIF IMMOBILISE"
        ],
        "2051": [
            "2051",
            "BILAN - PASSIF",
            "BILAN PASSIF",
            "TABLEAU 2051",
            "CAPITAUX PROPRES"
        ],
        "2052": [
            "2052",
            "COMPTE DE RESULTAT DE L'EXERCICE",
            "COMPTE DE RESULTAT",
            "TABLEAU 2052",
            "PRODUITS D'EXPLOITATION"
        ],
        "2053": [
            "2053",
            "TABLEAU 2053",
            "RESULTAT DE L'EXERCICE",
            "CHARGES D'EXPLOITATION"
        ],
        "2054": [
            "2054",
            "IMMOBILISATIONS",
            "TABLEAU 2054"
        ],
        "2055": [
            "2055",
            "AMORTISSEMENTS",
            "TABLEAU 2055"
        ],
        "2056": [
            "2056",
            "PROVISIONS",
            "TABLEAU 2056"
        ],
        "2057": [
            "2057",
            "ETAT DES ECHEANCES",
            "TABLEAU 2057"
        ],
        "2058-A": [
            "2058-A",
            "DETERMINATION DU RESULTAT FISCAL",
            "TABLEAU 2058-A"
        ],
        "2059-E": [
            "2059-E",
            "DETERMINATION DE LA VALEUR AJOUTEE",
            "TABLEAU 2059-E"
        ],
    }

    # Codes des champs obligatoires par type de formulaire
    REQUIRED_FIELDS = {
        "2050": ["CO"],  # Total actif
        "2051": ["EE"],  # Total passif
        "2052": ["FJ", "FQ"],  # CA et total produits
        "2053": ["GD", "HN"],  # Total charges et résultat net
        "2033-A": [],  # Simplifié
        "2033-B": [],  # Simplifié
    }

    def __init__(self):
        """Initialise le parseur PDF."""
        self._check_dependencies()
        self.pdf_path: Optional[str] = None
        self.is_scanned: bool = False
        self.form_types: list[str] = []
        self.raw_text: str = ""
        self.tables: list[list] = []
        self._extracted_fields: dict = {}

    def _check_dependencies(self) -> None:
        """Vérifie que les dépendances nécessaires sont installées."""
        if not HAS_PDFPLUMBER:
            raise DependencyError(
                "pdfplumber",
                "pip install pdfplumber"
            )

    def extract_from_pdf(self, pdf_path: str) -> dict:
        """
        Extrait toutes les données d'un fichier PDF de liasse fiscale.

        Cette méthode est le point d'entrée principal. Elle:
        1. Ouvre et valide le PDF
        2. Détermine si c'est un PDF natif ou scanné
        3. Extrait le texte et les tableaux
        4. Détecte le type de formulaire
        5. Parse les données selon le type
        6. Retourne un dictionnaire structuré

        Args:
            pdf_path: Chemin absolu vers le fichier PDF.

        Returns:
            Dictionnaire contenant les données extraites avec les clés:
            - metadata: Informations sur l'entreprise et l'exercice
            - balance_sheet: Bilan (actif et passif)
            - income_statement: Compte de résultat
            - raw_fields: Champs bruts avec leurs codes fiscaux
            - form_types: Liste des formulaires détectés
            - is_scanned: Indique si le PDF était scanné
            - extraction_confidence: Score de confiance (0-1)

        Raises:
            InvalidPDFError: Si le fichier PDF est invalide.
            EmptyPDFError: Si le PDF ne contient pas de texte.
            ExtractionError: Si l'extraction échoue.

        Example:
            >>> parser = PDFParser()
            >>> data = parser.extract_from_pdf("/path/to/liasse_2050.pdf")
            >>> print(f"Total actif: {data['balance_sheet']['assets']['total']}")
        """
        self.pdf_path = Path(pdf_path)
        logger.info(f"Début de l'extraction: {self.pdf_path}")

        # Validation du fichier
        self._validate_pdf_file()

        # Vérifier si le PDF est scanné
        self.is_scanned = is_pdf_scanned(str(self.pdf_path))
        if self.is_scanned:
            logger.warning(
                "PDF scanné détecté - extraction textuelle limitée. "
                "Utilisez AIExtractor pour de meilleurs résultats."
            )

        # Extraction du contenu
        try:
            self._extract_content()
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du contenu: {e}")
            raise ExtractionError(
                f"Impossible d'extraire le contenu du PDF: {e}",
                pdf_path=str(self.pdf_path)
            )

        # Vérifier qu'on a du contenu
        if not self.raw_text.strip() and not self.tables:
            raise EmptyPDFError(pdf_path=str(self.pdf_path))

        # Détecter les types de formulaires
        self.form_types = self._detect_all_form_types()
        logger.info(f"Formulaires détectés: {self.form_types}")

        # Parser les données
        result = self._parse_all_data()

        # Ajouter les métadonnées d'extraction
        result["form_types"] = self.form_types
        result["is_scanned"] = self.is_scanned
        result["source_file"] = str(self.pdf_path.name)

        logger.info("Extraction terminée avec succès")
        return result

    def _validate_pdf_file(self) -> None:
        """Valide que le fichier PDF existe et est lisible."""
        if not self.pdf_path.exists():
            raise InvalidPDFError(
                f"Le fichier n'existe pas: {self.pdf_path}",
                pdf_path=str(self.pdf_path)
            )

        if not self.pdf_path.is_file():
            raise InvalidPDFError(
                f"Le chemin n'est pas un fichier: {self.pdf_path}",
                pdf_path=str(self.pdf_path)
            )

        if self.pdf_path.suffix.lower() != '.pdf':
            raise InvalidPDFError(
                f"Le fichier n'est pas un PDF: {self.pdf_path}",
                pdf_path=str(self.pdf_path)
            )

        # Vérifier la taille du fichier
        if self.pdf_path.stat().st_size == 0:
            raise EmptyPDFError(pdf_path=str(self.pdf_path))

        # Vérifier si le PDF est protégé (avec pypdf si disponible)
        if HAS_PYPDF:
            try:
                reader = PdfReader(str(self.pdf_path))
                if reader.is_encrypted:
                    raise PasswordProtectedPDFError(pdf_path=str(self.pdf_path))
            except Exception as e:
                if "password" in str(e).lower():
                    raise PasswordProtectedPDFError(pdf_path=str(self.pdf_path))
                # Autres erreurs - laisser pdfplumber essayer

    def _extract_content(self) -> None:
        """Extrait le texte et les tableaux du PDF."""
        all_text = []
        all_tables = []

        with pdfplumber.open(str(self.pdf_path)) as pdf:
            logger.info(f"PDF ouvert: {len(pdf.pages)} page(s)")

            for i, page in enumerate(pdf.pages):
                # Extraction du texte
                text = page.extract_text() or ""
                all_text.append(text)
                logger.debug(f"Page {i+1}: {len(text)} caractères extraits")

                # Extraction des tableaux
                tables = page.extract_tables() or []
                for table in tables:
                    if table and len(table) > 1:  # Au moins un header + une ligne
                        all_tables.append({
                            "page": i + 1,
                            "data": table
                        })

                # Extraction des champs de formulaire si disponibles
                # (pour les PDF interactifs)
                try:
                    chars = page.chars
                    if chars:
                        # Regrouper les caractères par position
                        self._extract_fields_from_chars(chars, i + 1)
                except Exception:
                    pass  # Continuer même si l'extraction des champs échoue

        self.raw_text = "\n\n".join(all_text)
        self.tables = all_tables

        logger.info(
            f"Extraction terminée: {len(self.raw_text)} caractères, "
            f"{len(self.tables)} tableau(x)"
        )

    def _extract_fields_from_chars(self, chars: list, page_num: int) -> None:
        """
        Tente d'extraire les champs de formulaire depuis les caractères.

        Recherche les patterns code + valeur typiques des liasses fiscales.
        """
        text = "".join([c.get("text", "") for c in chars])

        # Pattern pour codes fiscaux avec valeurs
        pattern = r'\b([A-Z]{2})\s*[:\.]?\s*([\d\s,.()-]+)\b'

        for match in re.finditer(pattern, text):
            code = match.group(1)
            value_str = match.group(2).strip()

            if code in self._get_all_valid_codes():
                try:
                    value = clean_amount(value_str)
                    if code not in self._extracted_fields:
                        self._extracted_fields[code] = {
                            "value": value,
                            "page": page_num,
                            "raw": value_str
                        }
                except ValueError:
                    pass

    def _get_all_valid_codes(self) -> set:
        """Retourne l'ensemble des codes fiscaux valides."""
        all_codes = set()
        for mapping in [
            FISCAL_CODE_MAPPING_2050,
            FISCAL_CODE_MAPPING_2051,
            FISCAL_CODE_MAPPING_2052,
            FISCAL_CODE_MAPPING_2053,
        ]:
            all_codes.update(mapping.keys())
        return all_codes

    def detect_form_type(self, text: str) -> str:
        """
        Détecte le type de formulaire principal à partir du texte.

        Analyse le texte pour identifier les signatures caractéristiques
        des différents formulaires fiscaux français.

        Args:
            text: Texte extrait du PDF.

        Returns:
            Type de formulaire détecté (ex: "2050", "2033-A").
            Retourne "UNKNOWN" si non détecté.

        Example:
            >>> parser = PDFParser()
            >>> form_type = parser.detect_form_type("BILAN - ACTIF 2050")
            >>> print(form_type)  # "2050"
        """
        text_upper = text.upper()

        # Rechercher les signatures de chaque type
        scores = {}
        for form_type, signatures in self.FORM_SIGNATURES.items():
            score = 0
            for signature in signatures:
                if signature.upper() in text_upper:
                    score += 1
            if score > 0:
                scores[form_type] = score

        if not scores:
            return "UNKNOWN"

        # Retourner le type avec le meilleur score
        return max(scores, key=scores.get)

    def _detect_all_form_types(self) -> list[str]:
        """Détecte tous les types de formulaires présents dans le PDF."""
        detected = []
        text_upper = self.raw_text.upper()

        for form_type, signatures in self.FORM_SIGNATURES.items():
            for signature in signatures:
                if signature.upper() in text_upper:
                    if form_type not in detected:
                        detected.append(form_type)
                    break

        return detected if detected else ["UNKNOWN"]

    def parse_balance_sheet(self, tables: list) -> dict:
        """
        Parse les tableaux pour extraire les données du bilan.

        Analyse les tableaux du bilan (actif et passif) pour extraire
        les montants avec leurs codes fiscaux.

        Args:
            tables: Liste des tableaux extraits du PDF.

        Returns:
            Dictionnaire structuré avec:
            - assets: Actif (immobilisé et circulant)
            - liabilities: Passif (capitaux propres, provisions, dettes)
            - total_assets: Total de l'actif
            - total_liabilities: Total du passif

        Example:
            >>> balance_sheet = parser.parse_balance_sheet(tables)
            >>> print(balance_sheet["assets"]["fixed_assets"]["total"])
        """
        result = {
            "assets": {
                "fixed_assets": {
                    "intangible_assets": 0.0,
                    "tangible_assets": 0.0,
                    "financial_assets": 0.0,
                    "total": 0.0,
                },
                "current_assets": {
                    "inventory": 0.0,
                    "trade_receivables": 0.0,
                    "other_receivables": 0.0,
                    "prepaid_expenses": 0.0,
                    "marketable_securities": 0.0,
                    "cash": 0.0,
                    "total": 0.0,
                },
                "total_assets": 0.0,
            },
            "liabilities": {
                "equity": {
                    "share_capital": 0.0,
                    "share_premium": 0.0,
                    "revaluation_reserve": 0.0,
                    "legal_reserve": 0.0,
                    "statutory_reserves": 0.0,
                    "other_reserves": 0.0,
                    "retained_earnings": 0.0,
                    "net_income": 0.0,
                    "investment_subsidies": 0.0,
                    "regulated_provisions": 0.0,
                    "total": 0.0,
                },
                "provisions": {
                    "provisions_for_risks": 0.0,
                    "provisions_for_charges": 0.0,
                    "total": 0.0,
                },
                "debt": {
                    "long_term_debt": 0.0,
                    "short_term_debt": 0.0,
                    "bank_overdrafts": 0.0,
                    "lease_obligations": 0.0,
                    "bonds": 0.0,
                    "shareholder_loans": 0.0,
                    "total_financial_debt": 0.0,
                },
                "operating_liabilities": {
                    "trade_payables": 0.0,
                    "tax_liabilities": 0.0,
                    "social_liabilities": 0.0,
                    "advances_received": 0.0,
                    "deferred_revenue": 0.0,
                    "other_liabilities": 0.0,
                    "total": 0.0,
                },
                "total_liabilities": 0.0,
            },
        }

        # Parser les champs depuis les tableaux
        for table_info in tables:
            table = table_info.get("data", [])
            self._parse_table_for_balance_sheet(table, result)

        # Parser depuis le texte brut également
        self._parse_text_for_balance_sheet(self.raw_text, result)

        # Utiliser les champs extraits directement
        self._apply_extracted_fields_to_balance_sheet(result)

        # Calculer les totaux si non trouvés
        self._calculate_balance_sheet_totals(result)

        return result

    def _parse_table_for_balance_sheet(self, table: list, result: dict) -> None:
        """Parse un tableau pour extraire les données du bilan."""
        if not table:
            return

        for row in table:
            if not row:
                continue

            # Chercher un code fiscal dans la ligne
            row_text = " ".join(str(cell) if cell else "" for cell in row)

            for code in self._get_all_valid_codes():
                if code in row_text.upper():
                    # Trouver la valeur numérique
                    for cell in reversed(row):  # Valeurs généralement à droite
                        if cell:
                            try:
                                value = clean_amount(str(cell))
                                if value != 0.0:
                                    self._extracted_fields[code] = {
                                        "value": value,
                                        "raw": str(cell)
                                    }
                                    break
                            except ValueError:
                                continue

    def _parse_text_for_balance_sheet(self, text: str, result: dict) -> None:
        """Parse le texte brut pour extraire les données du bilan."""
        # Patterns pour les montants avec codes
        patterns = [
            r'([A-Z]{2})\s*[:\.\s]+\s*([\d\s,.()-]+)',
            r'([\d\s,.()-]+)\s*([A-Z]{2})\b',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                groups = match.groups()

                # Déterminer quel groupe est le code
                if groups[0] and groups[0].upper() in self._get_all_valid_codes():
                    code = groups[0].upper()
                    value_str = groups[1]
                elif len(groups) > 1 and groups[1] and groups[1].upper() in self._get_all_valid_codes():
                    code = groups[1].upper()
                    value_str = groups[0]
                else:
                    continue

                try:
                    value = clean_amount(value_str)
                    if code not in self._extracted_fields and value != 0.0:
                        self._extracted_fields[code] = {
                            "value": value,
                            "raw": value_str
                        }
                except ValueError:
                    continue

    def _apply_extracted_fields_to_balance_sheet(self, result: dict) -> None:
        """Applique les champs extraits à la structure du bilan."""
        # Mapping code -> chemin dans result
        field_mapping = {
            # Actif
            "AA": ("assets", "fixed_assets", "intangible_assets"),
            "AN": ("assets", "fixed_assets", "tangible_assets"),
            "CS": ("assets", "fixed_assets", "financial_assets"),
            "CW": ("assets", "fixed_assets", "total"),
            "BL": ("assets", "current_assets", "inventory"),
            "BX": ("assets", "current_assets", "trade_receivables"),
            "BZ": ("assets", "current_assets", "other_receivables"),
            "CB": ("assets", "current_assets", "prepaid_expenses"),
            "CD": ("assets", "current_assets", "marketable_securities"),
            "CF": ("assets", "current_assets", "cash"),
            "CJ": ("assets", "current_assets", "total"),
            "CO": ("assets", "total_assets"),

            # Passif - Capitaux propres
            "DA": ("liabilities", "equity", "share_capital"),
            "DB": ("liabilities", "equity", "share_premium"),
            "DC": ("liabilities", "equity", "revaluation_reserve"),
            "DD": ("liabilities", "equity", "legal_reserve"),
            "DE": ("liabilities", "equity", "statutory_reserves"),
            "DF": ("liabilities", "equity", "other_reserves"),
            "DG": ("liabilities", "equity", "retained_earnings"),
            "DH": ("liabilities", "equity", "net_income"),
            "DI": ("liabilities", "equity", "investment_subsidies"),
            "DJ": ("liabilities", "equity", "regulated_provisions"),
            "DL": ("liabilities", "equity", "total"),

            # Passif - Provisions
            "DO": ("liabilities", "provisions", "provisions_for_risks"),
            "DP": ("liabilities", "provisions", "provisions_for_charges"),
            "DQ": ("liabilities", "provisions", "total"),

            # Passif - Dettes financières
            "DS": ("liabilities", "debt", "bonds"),
            "DT": ("liabilities", "debt", "long_term_debt"),
            "DU": ("liabilities", "debt", "short_term_debt"),
            "DV": ("liabilities", "debt", "shareholder_loans"),
            "DW": ("liabilities", "debt", "bank_overdrafts"),
            "EC": ("liabilities", "debt", "total_financial_debt"),

            # Passif - Dettes d'exploitation
            "DX": ("liabilities", "operating_liabilities", "trade_payables"),
            "DY": ("liabilities", "operating_liabilities", "tax_liabilities"),
            "DZ": ("liabilities", "operating_liabilities", "social_liabilities"),
            "EA": ("liabilities", "operating_liabilities", "other_liabilities"),

            # Total passif
            "EE": ("liabilities", "total_liabilities"),
        }

        for code, path in field_mapping.items():
            if code in self._extracted_fields:
                value = self._extracted_fields[code].get("value", 0.0)
                self._set_nested_value(result, path, value)

    def _set_nested_value(self, d: dict, path: tuple, value: Any) -> None:
        """Définit une valeur dans un dictionnaire imbriqué."""
        for key in path[:-1]:
            d = d.setdefault(key, {})
        d[path[-1]] = value

    def _calculate_balance_sheet_totals(self, result: dict) -> None:
        """Calcule les totaux du bilan si non présents."""
        assets = result["assets"]
        liabilities = result["liabilities"]

        # Total actif immobilisé
        if assets["fixed_assets"]["total"] == 0.0:
            assets["fixed_assets"]["total"] = (
                assets["fixed_assets"]["intangible_assets"] +
                assets["fixed_assets"]["tangible_assets"] +
                assets["fixed_assets"]["financial_assets"]
            )

        # Total actif circulant
        if assets["current_assets"]["total"] == 0.0:
            assets["current_assets"]["total"] = (
                assets["current_assets"]["inventory"] +
                assets["current_assets"]["trade_receivables"] +
                assets["current_assets"]["other_receivables"] +
                assets["current_assets"]["prepaid_expenses"] +
                assets["current_assets"]["marketable_securities"] +
                assets["current_assets"]["cash"]
            )

        # Total actif
        if assets["total_assets"] == 0.0:
            assets["total_assets"] = (
                assets["fixed_assets"]["total"] +
                assets["current_assets"]["total"]
            )

        # Total capitaux propres
        if liabilities["equity"]["total"] == 0.0:
            liabilities["equity"]["total"] = sum([
                liabilities["equity"]["share_capital"],
                liabilities["equity"]["share_premium"],
                liabilities["equity"]["revaluation_reserve"],
                liabilities["equity"]["legal_reserve"],
                liabilities["equity"]["statutory_reserves"],
                liabilities["equity"]["other_reserves"],
                liabilities["equity"]["retained_earnings"],
                liabilities["equity"]["net_income"],
                liabilities["equity"]["investment_subsidies"],
                liabilities["equity"]["regulated_provisions"],
            ])

        # Total provisions
        if liabilities["provisions"]["total"] == 0.0:
            liabilities["provisions"]["total"] = (
                liabilities["provisions"]["provisions_for_risks"] +
                liabilities["provisions"]["provisions_for_charges"]
            )

        # Total dettes financières
        if liabilities["debt"]["total_financial_debt"] == 0.0:
            liabilities["debt"]["total_financial_debt"] = sum([
                liabilities["debt"]["long_term_debt"],
                liabilities["debt"]["short_term_debt"],
                liabilities["debt"]["bank_overdrafts"],
                liabilities["debt"]["lease_obligations"],
                liabilities["debt"]["bonds"],
                liabilities["debt"]["shareholder_loans"],
            ])

        # Total dettes d'exploitation
        if liabilities["operating_liabilities"]["total"] == 0.0:
            liabilities["operating_liabilities"]["total"] = sum([
                liabilities["operating_liabilities"]["trade_payables"],
                liabilities["operating_liabilities"]["tax_liabilities"],
                liabilities["operating_liabilities"]["social_liabilities"],
                liabilities["operating_liabilities"]["advances_received"],
                liabilities["operating_liabilities"]["deferred_revenue"],
                liabilities["operating_liabilities"]["other_liabilities"],
            ])

        # Total passif
        if liabilities["total_liabilities"] == 0.0:
            liabilities["total_liabilities"] = (
                liabilities["equity"]["total"] +
                liabilities["provisions"]["total"] +
                liabilities["debt"]["total_financial_debt"] +
                liabilities["operating_liabilities"]["total"]
            )

    def parse_income_statement(self, tables: list) -> dict:
        """
        Parse les tableaux pour extraire le compte de résultat.

        Analyse les tableaux du compte de résultat pour extraire
        les revenus, charges et différents niveaux de résultat.

        Args:
            tables: Liste des tableaux extraits du PDF.

        Returns:
            Dictionnaire structuré avec:
            - revenues: Produits d'exploitation
            - operating_expenses: Charges d'exploitation
            - operating_income: Résultat d'exploitation
            - financial_result: Résultat financier
            - exceptional_result: Résultat exceptionnel
            - net_income: Résultat net

        Example:
            >>> income_stmt = parser.parse_income_statement(tables)
            >>> print(f"CA: {income_stmt['revenues']['net_revenue']}")
        """
        result = {
            "revenues": {
                "sales_of_goods": 0.0,
                "sales_of_services": 0.0,
                "sales_of_products": 0.0,
                "net_revenue": 0.0,
                "stored_production": 0.0,
                "capitalized_production": 0.0,
                "operating_subsidies": 0.0,
                "other_operating_income": 0.0,
                "reversal_of_provisions": 0.0,
                "total": 0.0,
            },
            "operating_expenses": {
                "purchases_of_goods": 0.0,
                "purchases_of_raw_materials": 0.0,
                "inventory_variation": 0.0,
                "external_charges": 0.0,
                "taxes_and_duties": 0.0,
                "wages_and_salaries": 0.0,
                "social_charges": 0.0,
                "personnel_costs": 0.0,
                "depreciation": 0.0,
                "provisions": 0.0,
                "other_operating_expenses": 0.0,
                "total": 0.0,
            },
            "operating_income": 0.0,
            "financial_result": {
                "financial_income": 0.0,
                "interest_income": 0.0,
                "reversal_of_financial_provisions": 0.0,
                "foreign_exchange_gains": 0.0,
                "total_financial_income": 0.0,
                "interest_expense": 0.0,
                "financial_provisions": 0.0,
                "foreign_exchange_losses": 0.0,
                "total_financial_expense": 0.0,
                "net_financial_result": 0.0,
            },
            "current_income_before_tax": 0.0,
            "exceptional_result": {
                "exceptional_income": 0.0,
                "exceptional_income_capital": 0.0,
                "reversal_of_exceptional_provisions": 0.0,
                "total_exceptional_income": 0.0,
                "exceptional_expense": 0.0,
                "exceptional_expense_capital": 0.0,
                "exceptional_provisions": 0.0,
                "total_exceptional_expense": 0.0,
                "net_exceptional_result": 0.0,
            },
            "employee_profit_sharing": 0.0,
            "income_tax_expense": 0.0,
            "net_income": 0.0,
        }

        # Parser les champs depuis les tableaux
        for table_info in tables:
            table = table_info.get("data", [])
            self._parse_table_for_income_statement(table, result)

        # Parser depuis le texte brut
        self._parse_text_for_income_statement(self.raw_text, result)

        # Appliquer les champs extraits
        self._apply_extracted_fields_to_income_statement(result)

        # Calculer les totaux
        self._calculate_income_statement_totals(result)

        return result

    def _parse_table_for_income_statement(self, table: list, result: dict) -> None:
        """Parse un tableau pour le compte de résultat."""
        # Même logique que pour le bilan
        if not table:
            return

        for row in table:
            if not row:
                continue

            row_text = " ".join(str(cell) if cell else "" for cell in row)

            for code in self._get_all_valid_codes():
                if code in row_text.upper():
                    for cell in reversed(row):
                        if cell:
                            try:
                                value = clean_amount(str(cell))
                                if value != 0.0:
                                    self._extracted_fields[code] = {
                                        "value": value,
                                        "raw": str(cell)
                                    }
                                    break
                            except ValueError:
                                continue

    def _parse_text_for_income_statement(self, text: str, result: dict) -> None:
        """Parse le texte pour le compte de résultat."""
        # Patterns pour les revenus et charges
        revenue_keywords = [
            "chiffre d'affaires", "ventes", "production vendue",
            "produits d'exploitation", "CA net"
        ]
        expense_keywords = [
            "achats", "charges", "salaires", "charges sociales",
            "dotations", "amortissements"
        ]

        # Recherche des montants après les mots-clés
        for keyword in revenue_keywords:
            pattern = rf'{keyword}[:\s]*([\d\s,.()-]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = clean_amount(match.group(1))
                    # Stocker dans le bon champ
                    if "chiffre" in keyword.lower() or "CA" in keyword:
                        if result["revenues"]["net_revenue"] == 0.0:
                            result["revenues"]["net_revenue"] = value
                except ValueError:
                    pass

    def _apply_extracted_fields_to_income_statement(self, result: dict) -> None:
        """Applique les champs extraits au compte de résultat."""
        field_mapping = {
            # Revenus
            "FA": ("revenues", "sales_of_goods"),
            "FC": ("revenues", "sales_of_products"),
            "FD": ("revenues", "sales_of_services"),
            "FJ": ("revenues", "net_revenue"),
            "FK": ("revenues", "stored_production"),
            "FL": ("revenues", "capitalized_production"),
            "FM": ("revenues", "operating_subsidies"),
            "FN": ("revenues", "other_operating_income"),
            "FO": ("revenues", "reversal_of_provisions"),
            "FQ": ("revenues", "total"),

            # Charges d'exploitation
            "FS": ("operating_expenses", "purchases_of_goods"),
            "FU": ("operating_expenses", "purchases_of_raw_materials"),
            "FT": ("operating_expenses", "inventory_variation"),
            "FW": ("operating_expenses", "external_charges"),
            "FX": ("operating_expenses", "taxes_and_duties"),
            "FY": ("operating_expenses", "wages_and_salaries"),
            "FZ": ("operating_expenses", "social_charges"),
            "GA": ("operating_expenses", "depreciation"),
            "GB": ("operating_expenses", "provisions"),
            "GC": ("operating_expenses", "other_operating_expenses"),
            "GD": ("operating_expenses", "total"),

            # Résultats
            "GG": ("operating_income",),
            "GJ": ("financial_result", "total_financial_income"),
            "GK": ("financial_result", "total_financial_expense"),
            "GR": ("financial_result", "net_financial_result"),
            "GS": ("current_income_before_tax",),
            "HA": ("exceptional_result", "total_exceptional_income"),
            "HB": ("exceptional_result", "total_exceptional_expense"),
            "HC": ("exceptional_result", "net_exceptional_result"),
            "HJ": ("employee_profit_sharing",),
            "HK": ("income_tax_expense",),
            "HN": ("net_income",),
        }

        for code, path in field_mapping.items():
            if code in self._extracted_fields:
                value = self._extracted_fields[code].get("value", 0.0)
                if len(path) == 1:
                    result[path[0]] = value
                else:
                    self._set_nested_value(result, path, value)

    def _calculate_income_statement_totals(self, result: dict) -> None:
        """Calcule les totaux du compte de résultat."""
        revenues = result["revenues"]
        expenses = result["operating_expenses"]
        financial = result["financial_result"]
        exceptional = result["exceptional_result"]

        # CA net
        if revenues["net_revenue"] == 0.0:
            revenues["net_revenue"] = (
                revenues["sales_of_goods"] +
                revenues["sales_of_products"] +
                revenues["sales_of_services"]
            )

        # Total produits d'exploitation
        if revenues["total"] == 0.0:
            revenues["total"] = sum([
                revenues["net_revenue"],
                revenues["stored_production"],
                revenues["capitalized_production"],
                revenues["operating_subsidies"],
                revenues["other_operating_income"],
                revenues["reversal_of_provisions"],
            ])

        # Total charges d'exploitation
        if expenses["total"] == 0.0:
            personnel = expenses["personnel_costs"]
            if personnel == 0.0:
                personnel = expenses["wages_and_salaries"] + expenses["social_charges"]

            expenses["total"] = sum([
                expenses["purchases_of_goods"],
                expenses["purchases_of_raw_materials"],
                expenses["inventory_variation"],
                expenses["external_charges"],
                expenses["taxes_and_duties"],
                personnel,
                expenses["depreciation"],
                expenses["provisions"],
                expenses["other_operating_expenses"],
            ])

        # Résultat d'exploitation
        if result["operating_income"] == 0.0:
            result["operating_income"] = revenues["total"] - expenses["total"]

        # Résultat financier
        if financial["net_financial_result"] == 0.0:
            financial["net_financial_result"] = (
                financial["total_financial_income"] -
                financial["total_financial_expense"]
            )

        # Résultat courant avant impôts
        if result["current_income_before_tax"] == 0.0:
            result["current_income_before_tax"] = (
                result["operating_income"] +
                financial["net_financial_result"]
            )

        # Résultat exceptionnel
        if exceptional["net_exceptional_result"] == 0.0:
            exceptional["net_exceptional_result"] = (
                exceptional["total_exceptional_income"] -
                exceptional["total_exceptional_expense"]
            )

        # Résultat net
        if result["net_income"] == 0.0:
            result["net_income"] = (
                result["current_income_before_tax"] +
                exceptional["net_exceptional_result"] -
                result["employee_profit_sharing"] -
                result["income_tax_expense"]
            )

    def validate_data(self, data: dict) -> tuple[bool, list[str]]:
        """
        Valide la cohérence des données extraites.

        Effectue plusieurs vérifications:
        1. Équilibre Actif = Passif
        2. Cohérence résultat net (bilan vs compte de résultat)
        3. Présence des champs obligatoires
        4. Plausibilité des valeurs

        Args:
            data: Dictionnaire contenant les données extraites.

        Returns:
            Tuple (is_valid, list_of_errors):
            - is_valid: True si toutes les validations passent
            - list_of_errors: Liste des erreurs détectées

        Example:
            >>> is_valid, errors = parser.validate_data(data)
            >>> if not is_valid:
            ...     for error in errors:
            ...         print(f"Erreur: {error}")
        """
        errors = []

        # Récupérer les données du bilan
        balance_sheet = data.get("balance_sheet", {})
        income_statement = data.get("income_statement", {})

        total_assets = balance_sheet.get("assets", {}).get("total_assets", 0.0)
        total_liabilities = balance_sheet.get("liabilities", {}).get("total_liabilities", 0.0)

        # Vérification 1: Équilibre du bilan
        if total_assets > 0 and total_liabilities > 0:
            difference = abs(total_assets - total_liabilities)
            tolerance = max(1.0, total_assets * 0.001)  # 0.1% ou 1 euro

            if difference > tolerance:
                errors.append(
                    f"Déséquilibre du bilan: Actif ({total_assets:,.2f}) "
                    f"!= Passif ({total_liabilities:,.2f}). "
                    f"Différence: {difference:,.2f}"
                )

        # Vérification 2: Cohérence du résultat net
        equity_net_income = (
            balance_sheet.get("liabilities", {})
            .get("equity", {})
            .get("net_income", 0.0)
        )
        is_net_income = income_statement.get("net_income", 0.0)

        if equity_net_income != 0 and is_net_income != 0:
            difference = abs(equity_net_income - is_net_income)
            if difference > 1.0:
                errors.append(
                    f"Incohérence du résultat net: "
                    f"Bilan ({equity_net_income:,.2f}) != "
                    f"Compte de résultat ({is_net_income:,.2f})"
                )

        # Vérification 3: Champs obligatoires
        raw_fields = data.get("raw_fields", {})
        form_types = data.get("form_types", [])

        for form_type in form_types:
            required = self.REQUIRED_FIELDS.get(form_type, [])
            for code in required:
                if code not in raw_fields:
                    errors.append(
                        f"Champ obligatoire manquant pour {form_type}: {code}"
                    )

        # Vérification 4: Valeurs plausibles
        revenues = income_statement.get("revenues", {})
        net_revenue = revenues.get("net_revenue", 0.0)
        total_revenues = revenues.get("total", 0.0)

        if net_revenue < 0:
            errors.append(
                f"Chiffre d'affaires négatif invalide: {net_revenue:,.2f}"
            )

        if total_revenues < 0 and total_revenues != 0:
            errors.append(
                f"Total des produits négatif suspect: {total_revenues:,.2f}"
            )

        # Vérification 5: Présence de données
        if total_assets == 0 and total_liabilities == 0:
            errors.append("Aucune donnée de bilan extraite")

        if net_revenue == 0 and total_revenues == 0 and is_net_income == 0:
            errors.append("Aucune donnée de compte de résultat extraite")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info("Validation des données: OK")
        else:
            logger.warning(f"Validation des données: {len(errors)} erreur(s)")
            for error in errors:
                logger.warning(f"  - {error}")

        return is_valid, errors

    def _parse_all_data(self) -> dict:
        """Parse toutes les données du PDF."""
        # Parser le bilan
        balance_sheet = self.parse_balance_sheet(self.tables)

        # Parser le compte de résultat
        income_statement = self.parse_income_statement(self.tables)

        # Extraire les métadonnées
        metadata = self._extract_metadata()

        # Préparer les champs bruts
        raw_fields = {
            code: {"code": code, "value": info["value"]}
            for code, info in self._extracted_fields.items()
        }

        # Calculer le score de confiance
        confidence = self._calculate_confidence_score(
            balance_sheet, income_statement, raw_fields
        )

        return {
            "metadata": metadata,
            "balance_sheet": balance_sheet,
            "income_statement": income_statement,
            "raw_fields": raw_fields,
            "extraction_confidence": confidence,
        }

    def _extract_metadata(self) -> dict:
        """Extrait les métadonnées (entreprise, dates, etc.)."""
        metadata = {
            "company_name": "",
            "siren": "",
            "siret": None,
            "naf_code": None,
            "legal_form": None,
            "fiscal_year_start": None,
            "fiscal_year_end": None,
            "fiscal_year_duration_months": 12,
            "extraction_date": date.today().isoformat(),
            "source_file": str(self.pdf_path.name) if self.pdf_path else None,
            "form_types": self.form_types,
            "confidence_score": 1.0,
            "extraction_warnings": [],
        }

        # Recherche dans le texte brut
        text = self.raw_text

        # SIREN (9 chiffres)
        siren_match = re.search(r'\bSIREN\s*[:\s]*(\d{9})\b', text, re.IGNORECASE)
        if not siren_match:
            siren_match = re.search(r'\b(\d{9})\b', text)

        if siren_match:
            siren = siren_match.group(1)
            if validate_siren(siren):
                metadata["siren"] = siren

        # SIRET (14 chiffres)
        siret_match = re.search(r'\bSIRET\s*[:\s]*(\d{14})\b', text, re.IGNORECASE)
        if siret_match:
            metadata["siret"] = siret_match.group(1)

        # Raison sociale (souvent en début de document)
        company_patterns = [
            r'Raison sociale\s*[:\s]*([^\n]+)',
            r'Dénomination\s*[:\s]*([^\n]+)',
            r'Entreprise\s*[:\s]*([^\n]+)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata["company_name"] = match.group(1).strip()[:100]
                break

        # Code NAF
        naf_match = re.search(r'\b([A-Z]?\d{2}\.?\d{2}[A-Z]?)\b', text)
        if naf_match:
            metadata["naf_code"] = naf_match.group(1)

        # Forme juridique
        legal_forms = ["SA", "SAS", "SASU", "SARL", "EURL", "SNC", "SCI", "EI", "EIRL"]
        for form in legal_forms:
            if re.search(rf'\b{form}\b', text):
                metadata["legal_form"] = form
                break

        # Dates d'exercice
        date_patterns = [
            r'exercice\s+du\s+(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\s+au\s+(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
            r'du\s+(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\s+au\s+(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
            r'clôture\s*[:\s]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    metadata["fiscal_year_start"] = self._parse_date(match.group(1))
                    metadata["fiscal_year_end"] = self._parse_date(match.group(2))
                else:
                    metadata["fiscal_year_end"] = self._parse_date(match.group(1))
                break

        return metadata

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse une date au format français vers ISO."""
        if not date_str:
            return None

        # Essayer différents formats
        formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
        ]

        for fmt in formats:
            try:
                from datetime import datetime
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None

    def _calculate_confidence_score(
        self,
        balance_sheet: dict,
        income_statement: dict,
        raw_fields: dict
    ) -> float:
        """Calcule un score de confiance pour l'extraction."""
        score = 1.0
        reasons = []

        # Pénalité si PDF scanné
        if self.is_scanned:
            score -= 0.3
            reasons.append("PDF scanné")

        # Pénalité si peu de champs extraits
        if len(raw_fields) < 5:
            score -= 0.2
            reasons.append("Peu de champs extraits")

        # Pénalité si bilan déséquilibré
        total_assets = balance_sheet.get("assets", {}).get("total_assets", 0)
        total_liabilities = balance_sheet.get("liabilities", {}).get("total_liabilities", 0)

        if total_assets > 0 and total_liabilities > 0:
            if abs(total_assets - total_liabilities) > total_assets * 0.01:
                score -= 0.2
                reasons.append("Bilan déséquilibré")

        # Pénalité si pas de CA
        if income_statement.get("revenues", {}).get("net_revenue", 0) == 0:
            score -= 0.1
            reasons.append("CA non trouvé")

        # Bonus si type de formulaire identifié
        if "UNKNOWN" not in self.form_types:
            score += 0.1

        # Limiter entre 0 et 1
        score = max(0.0, min(1.0, score))

        if reasons:
            logger.debug(f"Score de confiance: {score:.2f} ({', '.join(reasons)})")

        return round(score, 2)
