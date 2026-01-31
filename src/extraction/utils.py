"""
Utilitaires pour l'extraction de données depuis les liasses fiscales.

Ce module contient des fonctions helper pour:
- La conversion de PDF en images
- Le nettoyage des montants
- La recherche de champs par code
- La manipulation des données extraites
"""

import re
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional, Any
from decimal import Decimal, InvalidOperation

# Lazy imports pour éviter les erreurs si les dépendances ne sont pas installées
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False


logger = logging.getLogger(__name__)


# =============================================================================
# CONVERSION PDF EN IMAGES
# =============================================================================

def pdf_to_images(
    pdf_path: str,
    dpi: int = 200,
    output_format: str = "PNG",
    max_pages: Optional[int] = None
) -> list:
    """
    Convertit un fichier PDF en une liste d'images.

    Cette fonction est utilisée principalement pour l'extraction via AI
    (Claude vision) lorsque l'extraction textuelle échoue.

    Args:
        pdf_path: Chemin absolu vers le fichier PDF.
        dpi: Résolution des images générées (défaut: 200).
        output_format: Format de sortie (PNG, JPEG).
        max_pages: Nombre maximum de pages à convertir (None = toutes).

    Returns:
        Liste d'objets Image PIL.

    Raises:
        ImportError: Si pdf2image ou PIL ne sont pas installés.
        FileNotFoundError: Si le fichier PDF n'existe pas.
        ValueError: Si le PDF est invalide ou corrompu.

    Example:
        >>> images = pdf_to_images("/path/to/liasse.pdf")
        >>> print(f"{len(images)} pages converties")
    """
    if not HAS_PDF2IMAGE:
        raise ImportError(
            "pdf2image n'est pas installé. "
            "Installez-le avec: pip install pdf2image"
        )

    if not HAS_PIL:
        raise ImportError(
            "Pillow n'est pas installé. "
            "Installez-le avec: pip install Pillow"
        )

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Le fichier PDF n'existe pas: {pdf_path}")

    if not pdf_path.suffix.lower() == '.pdf':
        raise ValueError(f"Le fichier n'est pas un PDF: {pdf_path}")

    logger.info(f"Conversion du PDF en images: {pdf_path}")

    try:
        # Paramètres de conversion
        kwargs = {
            "pdf_path": str(pdf_path),
            "dpi": dpi,
            "fmt": output_format.lower(),
        }

        if max_pages is not None:
            kwargs["last_page"] = max_pages

        images = convert_from_path(**kwargs)

        logger.info(f"{len(images)} page(s) convertie(s) en images")
        return images

    except Exception as e:
        logger.error(f"Erreur lors de la conversion PDF -> images: {e}")
        raise ValueError(f"Impossible de convertir le PDF: {e}")


def save_images_to_temp(
    images: list,
    prefix: str = "liasse_page_"
) -> list[str]:
    """
    Sauvegarde une liste d'images PIL dans des fichiers temporaires.

    Args:
        images: Liste d'objets Image PIL.
        prefix: Préfixe pour les noms de fichiers.

    Returns:
        Liste des chemins vers les fichiers temporaires créés.
    """
    temp_paths = []
    temp_dir = tempfile.mkdtemp(prefix="liasse_extraction_")

    for i, image in enumerate(images):
        temp_path = os.path.join(temp_dir, f"{prefix}{i+1:03d}.png")
        image.save(temp_path, "PNG")
        temp_paths.append(temp_path)
        logger.debug(f"Image sauvegardée: {temp_path}")

    return temp_paths


def image_to_base64(image) -> str:
    """
    Convertit une image PIL en chaîne base64.

    Args:
        image: Objet Image PIL.

    Returns:
        Chaîne base64 de l'image au format PNG.
    """
    import base64
    import io

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.standard_b64encode(buffer.read()).decode("utf-8")


# =============================================================================
# NETTOYAGE DES MONTANTS
# =============================================================================

def clean_amount(text: str) -> float:
    """
    Nettoie et convertit un texte représentant un montant en float.

    Gère les formats français courants:
    - "1 234,56" -> 1234.56
    - "1.234,56" -> 1234.56
    - "(1 234,56)" -> -1234.56 (parenthèses = négatif)
    - "1234.56" -> 1234.56
    - "-1 234" -> -1234.0
    - "" ou None -> 0.0

    Args:
        text: Chaîne représentant un montant.

    Returns:
        Valeur flottante du montant.

    Raises:
        ValueError: Si le texte ne peut pas être converti en nombre.

    Example:
        >>> clean_amount("1 234,56")
        1234.56
        >>> clean_amount("(500)")
        -500.0
    """
    if text is None or text == "":
        return 0.0

    # Convertir en string si nécessaire
    text = str(text).strip()

    # Cas vide après strip
    if not text or text == "-" or text == "—":
        return 0.0

    # Détecter les valeurs négatives (parenthèses)
    is_negative = False
    if text.startswith("(") and text.endswith(")"):
        is_negative = True
        text = text[1:-1].strip()
    elif text.startswith("-"):
        is_negative = True
        text = text[1:].strip()

    # Supprimer les espaces et caractères non numériques (sauf , et .)
    text = re.sub(r'[^\d,.\-]', '', text)

    # Cas vide après nettoyage
    if not text:
        return 0.0

    # Déterminer le séparateur décimal
    # En français: 1 234,56 (virgule = décimal, point = milliers)
    # En anglais: 1,234.56 (point = décimal, virgule = milliers)

    # Compter les occurrences
    comma_count = text.count(',')
    dot_count = text.count('.')

    if comma_count == 1 and dot_count == 0:
        # Format: "1234,56" -> virgule est décimale
        text = text.replace(',', '.')
    elif comma_count == 0 and dot_count == 1:
        # Format: "1234.56" -> point est décimal
        pass
    elif comma_count >= 1 and dot_count >= 1:
        # Format mixte: déterminer le séparateur décimal par position
        last_comma = text.rfind(',')
        last_dot = text.rfind('.')

        if last_comma > last_dot:
            # Format français: "1.234,56"
            text = text.replace('.', '').replace(',', '.')
        else:
            # Format anglais: "1,234.56"
            text = text.replace(',', '')
    elif comma_count > 1:
        # Plusieurs virgules = séparateurs de milliers
        text = text.replace(',', '')
    elif dot_count > 1:
        # Plusieurs points = séparateurs de milliers (rare)
        text = text.replace('.', '')

    try:
        value = float(text)
        return -value if is_negative else value
    except ValueError:
        raise ValueError(f"Impossible de convertir '{text}' en nombre")


def format_amount_french(value: float, decimals: int = 2) -> str:
    """
    Formate un nombre au format français.

    Args:
        value: Valeur numérique.
        decimals: Nombre de décimales.

    Returns:
        Chaîne formatée (ex: "1 234,56 €").
    """
    if value < 0:
        sign = "-"
        value = abs(value)
    else:
        sign = ""

    # Formater avec séparateurs
    formatted = f"{value:,.{decimals}f}"

    # Convertir au format français
    formatted = formatted.replace(",", " ").replace(".", ",")

    return f"{sign}{formatted}"


# =============================================================================
# RECHERCHE DE CHAMPS PAR CODE
# =============================================================================

def find_field_by_code(data: dict, code: str) -> Optional[float]:
    """
    Trouve un champ par son code fiscal dans les données extraites.

    Les codes fiscaux (AA, AB, BH, etc.) sont utilisés dans les
    formulaires de liasses fiscales françaises.

    Args:
        data: Dictionnaire contenant les données extraites.
        code: Code fiscal à rechercher (ex: "AA", "BH", "DL").

    Returns:
        Valeur du champ ou None si non trouvé.

    Example:
        >>> data = {"fields": {"AA": 1234.56, "BH": 5000.0}}
        >>> find_field_by_code(data, "AA")
        1234.56
    """
    if not data or not code:
        return None

    code = code.upper().strip()

    # Recherche directe
    if code in data:
        value = data[code]
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, dict) and "value" in value:
            return float(value["value"])

    # Recherche dans un sous-dictionnaire "fields"
    if "fields" in data:
        return find_field_by_code(data["fields"], code)

    # Recherche dans "raw_fields"
    if "raw_fields" in data:
        return find_field_by_code(data["raw_fields"], code)

    # Recherche récursive dans tous les sous-dictionnaires
    for key, value in data.items():
        if isinstance(value, dict):
            result = find_field_by_code(value, code)
            if result is not None:
                return result

    return None


def extract_field_codes(text: str) -> list[tuple[str, str]]:
    """
    Extrait les codes de champs fiscaux et leurs valeurs associées d'un texte.

    Recherche les patterns typiques des liasses fiscales:
    - "AA 123456" ou "AA: 123456"
    - Codes de 2-3 lettres suivis de valeurs numériques

    Args:
        text: Texte à analyser.

    Returns:
        Liste de tuples (code, valeur).
    """
    # Pattern pour codes fiscaux français
    # Codes: 2-3 lettres majuscules, parfois suivies de chiffres
    pattern = r'\b([A-Z]{2,3}(?:\d)?)\s*[:=]?\s*([\d\s,.]+)\b'

    matches = re.findall(pattern, text)

    results = []
    for code, value in matches:
        # Nettoyer la valeur
        try:
            cleaned_value = clean_amount(value)
            results.append((code, str(cleaned_value)))
        except ValueError:
            continue

    return results


# =============================================================================
# VALIDATION ET VÉRIFICATION
# =============================================================================

def is_pdf_scanned(pdf_path: str, sample_pages: int = 3) -> bool:
    """
    Détermine si un PDF est scanné (images) ou natif (texte extractible).

    Args:
        pdf_path: Chemin vers le fichier PDF.
        sample_pages: Nombre de pages à analyser.

    Returns:
        True si le PDF semble être scanné, False s'il contient du texte.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber non installé, impossible de détecter le type de PDF")
        return False

    text_chars_found = 0
    pages_checked = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:sample_pages]:
                text = page.extract_text() or ""
                text_chars_found += len(text.strip())
                pages_checked += 1
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du PDF: {e}")
        return True  # En cas d'erreur, supposer scanné

    if pages_checked == 0:
        return True

    # Heuristique: moins de 100 caractères par page = probablement scanné
    avg_chars_per_page = text_chars_found / pages_checked
    is_scanned = avg_chars_per_page < 100

    logger.debug(
        f"PDF analysé: {avg_chars_per_page:.0f} chars/page en moyenne, "
        f"{'scanné' if is_scanned else 'natif'}"
    )

    return is_scanned


def validate_siren(siren: str) -> bool:
    """
    Valide un numéro SIREN français (algorithme de Luhn).

    Args:
        siren: Numéro SIREN à valider (9 chiffres).

    Returns:
        True si le SIREN est valide.
    """
    if not siren or len(siren) != 9 or not siren.isdigit():
        return False

    # Algorithme de Luhn
    total = 0
    for i, char in enumerate(siren):
        digit = int(char)
        if i % 2 == 1:  # Position paire (0-indexed, donc 1, 3, 5, 7)
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit

    return total % 10 == 0


def validate_siret(siret: str) -> bool:
    """
    Valide un numéro SIRET français (SIREN + NIC).

    Args:
        siret: Numéro SIRET à valider (14 chiffres).

    Returns:
        True si le SIRET est valide.
    """
    if not siret or len(siret) != 14 or not siret.isdigit():
        return False

    # Le SIREN est les 9 premiers chiffres
    siren = siret[:9]

    # Vérifier le SIREN
    if not validate_siren(siren):
        return False

    # Algorithme de Luhn sur les 14 chiffres
    total = 0
    for i, char in enumerate(siret):
        digit = int(char)
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit

    return total % 10 == 0


# =============================================================================
# MAPPING DES CODES FISCAUX
# =============================================================================

# Mapping des codes fiscaux vers les champs du modèle FiscalData
# Formulaire 2050 (Bilan - Actif)
FISCAL_CODE_MAPPING_2050 = {
    # Actif immobilisé - Immobilisations incorporelles
    "AA": "assets.fixed_assets.intangible_assets",
    "AB": "assets.fixed_assets.intangible_assets",  # Brut

    # Actif immobilisé - Immobilisations corporelles
    "AN": "assets.fixed_assets.tangible_assets",
    "AO": "assets.fixed_assets.tangible_assets",  # Brut

    # Actif immobilisé - Immobilisations financières
    "CS": "assets.fixed_assets.financial_assets",
    "CT": "assets.fixed_assets.financial_assets",  # Brut

    # Actif circulant - Stocks
    "BL": "assets.current_assets.inventory",
    "BM": "assets.current_assets.inventory",  # Brut

    # Actif circulant - Créances clients
    "BX": "assets.current_assets.trade_receivables",
    "BY": "assets.current_assets.trade_receivables",  # Brut

    # Actif circulant - Disponibilités
    "CF": "assets.current_assets.cash",

    # Total actif
    "CO": "assets.total_assets",
}

# Formulaire 2051 (Bilan - Passif)
FISCAL_CODE_MAPPING_2051 = {
    # Capitaux propres
    "DA": "liabilities.equity.share_capital",
    "DB": "liabilities.equity.share_premium",
    "DC": "liabilities.equity.revaluation_reserve",
    "DD": "liabilities.equity.legal_reserve",
    "DE": "liabilities.equity.statutory_reserves",
    "DF": "liabilities.equity.other_reserves",
    "DG": "liabilities.equity.retained_earnings",
    "DH": "liabilities.equity.net_income",
    "DI": "liabilities.equity.investment_subsidies",
    "DJ": "liabilities.equity.regulated_provisions",
    "DL": "liabilities.equity.total",

    # Provisions
    "DO": "liabilities.provisions.provisions_for_risks",
    "DP": "liabilities.provisions.provisions_for_charges",
    "DQ": "liabilities.provisions.total",

    # Dettes financières
    "DS": "liabilities.debt.bonds",
    "DT": "liabilities.debt.long_term_debt",
    "DU": "liabilities.debt.short_term_debt",
    "DV": "liabilities.debt.shareholder_loans",

    # Dettes d'exploitation
    "DW": "liabilities.operating_liabilities.advances_received",
    "DX": "liabilities.operating_liabilities.trade_payables",
    "DY": "liabilities.operating_liabilities.tax_liabilities",
    "DZ": "liabilities.operating_liabilities.social_liabilities",

    # Total passif
    "EE": "liabilities.total_liabilities",
}

# Formulaire 2052 (Compte de résultat - Produits)
FISCAL_CODE_MAPPING_2052 = {
    # Chiffre d'affaires
    "FA": "revenues.sales_of_goods",
    "FC": "revenues.sales_of_products",
    "FD": "revenues.sales_of_services",
    "FJ": "revenues.net_revenue",  # Total CA

    # Autres produits
    "FK": "revenues.stored_production",
    "FL": "revenues.capitalized_production",
    "FM": "revenues.operating_subsidies",
    "FN": "revenues.other_operating_income",
    "FO": "revenues.reversal_of_provisions",
    "FQ": "revenues.total",  # Total produits exploitation
}

# Formulaire 2053 (Compte de résultat - Charges)
FISCAL_CODE_MAPPING_2053 = {
    # Charges d'exploitation
    "FS": "operating_expenses.purchases_of_goods",
    "FT": "operating_expenses.inventory_variation",
    "FU": "operating_expenses.purchases_of_raw_materials",
    "FV": "operating_expenses.inventory_variation",
    "FW": "operating_expenses.external_charges",
    "FX": "operating_expenses.taxes_and_duties",
    "FY": "operating_expenses.wages_and_salaries",
    "FZ": "operating_expenses.social_charges",
    "GA": "operating_expenses.depreciation",
    "GB": "operating_expenses.provisions",
    "GC": "operating_expenses.other_operating_expenses",
    "GD": "operating_expenses.total",  # Total charges exploitation

    # Résultat d'exploitation
    "GG": "operating_income",

    # Résultat financier
    "GJ": "financial_result.total_financial_income",
    "GK": "financial_result.total_financial_expense",
    "GR": "financial_result.net_financial_result",

    # Résultat exceptionnel
    "HA": "exceptional_result.total_exceptional_income",
    "HB": "exceptional_result.total_exceptional_expense",
    "HC": "exceptional_result.net_exceptional_result",

    # Impôts et résultat net
    "HK": "income_tax_expense",
    "HN": "net_income",
}


def get_field_path_for_code(code: str, form_type: str = None) -> Optional[str]:
    """
    Retourne le chemin du champ dans FiscalData pour un code fiscal.

    Args:
        code: Code fiscal (ex: "AA", "DL").
        form_type: Type de formulaire (2050, 2051, 2052, 2053).

    Returns:
        Chemin du champ (ex: "balance_sheet.assets.total_assets").
    """
    code = code.upper().strip()

    # Chercher dans tous les mappings si form_type non spécifié
    mappings = []
    if form_type:
        if form_type == "2050":
            mappings = [FISCAL_CODE_MAPPING_2050]
        elif form_type == "2051":
            mappings = [FISCAL_CODE_MAPPING_2051]
        elif form_type == "2052":
            mappings = [FISCAL_CODE_MAPPING_2052]
        elif form_type == "2053":
            mappings = [FISCAL_CODE_MAPPING_2053]
    else:
        mappings = [
            FISCAL_CODE_MAPPING_2050,
            FISCAL_CODE_MAPPING_2051,
            FISCAL_CODE_MAPPING_2052,
            FISCAL_CODE_MAPPING_2053,
        ]

    for mapping in mappings:
        if code in mapping:
            return mapping[code]

    return None
