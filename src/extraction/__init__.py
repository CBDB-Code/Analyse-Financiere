"""
Module d'extraction de liasses fiscales françaises.

Ce module fournit les outils pour extraire automatiquement les données
depuis des PDFs de liasses fiscales (formulaires 2033, 2050-2059).

Classes principales:
    - FiscalDataExtractor: Orchestrateur principal (recommandé)
    - PDFParser: Extraction textuelle native depuis PDF
    - AIExtractor: Extraction via Claude AI (pour PDFs scannés)

Fonctions utilitaires:
    - extract_fiscal_data: Fonction simple pour extraction rapide
    - pdf_to_images: Convertit un PDF en images
    - clean_amount: Nettoie les montants (format français -> float)

Exceptions:
    - ExtractionError: Erreur générale d'extraction
    - InvalidPDFError: PDF invalide ou corrompu
    - ValidationError: Données extraites invalides
    - AIExtractionError: Erreur lors de l'extraction AI

Example:
    >>> from src.extraction import extract_fiscal_data
    >>> data = extract_fiscal_data("/path/to/liasse_fiscale.pdf")
    >>> print(f"CA: {data.income_statement.revenues.net_revenue:,.2f} EUR")
    >>> print(f"Resultat net: {data.income_statement.net_income:,.2f} EUR")

    # Ou avec plus de controle:
    >>> from src.extraction import FiscalDataExtractor
    >>> extractor = FiscalDataExtractor(use_ai_fallback=True)
    >>> fiscal_data = extractor.extract("/path/to/liasse.pdf")
    >>> report = extractor.get_extraction_report()
    >>> print(f"Methode: {report.method_used}, Confiance: {report.confidence_score}")
"""

# Classes principales
from .extractor import FiscalDataExtractor, ExtractionReport, extract_fiscal_data
from .pdf_parser import PDFParser
from .ai_fallback import AIExtractor, extract_with_claude_simple

# Exceptions
from .exceptions import (
    ExtractionError,
    InvalidPDFError,
    EmptyPDFError,
    PasswordProtectedPDFError,
    UnsupportedFormTypeError,
    ValidationError,
    AIExtractionError,
    RateLimitError,
    TokenLimitExceededError,
    ParsingError,
    OCRError,
    DependencyError,
)

# Utilitaires
from .utils import (
    pdf_to_images,
    image_to_base64,
    save_images_to_temp,
    clean_amount,
    format_amount_french,
    find_field_by_code,
    extract_field_codes,
    is_pdf_scanned,
    validate_siren,
    validate_siret,
    get_field_path_for_code,
    FISCAL_CODE_MAPPING_2050,
    FISCAL_CODE_MAPPING_2051,
    FISCAL_CODE_MAPPING_2052,
    FISCAL_CODE_MAPPING_2053,
)


__all__ = [
    # Classes principales
    "FiscalDataExtractor",
    "ExtractionReport",
    "PDFParser",
    "AIExtractor",

    # Fonctions utilitaires
    "extract_fiscal_data",
    "extract_with_claude_simple",
    "pdf_to_images",
    "image_to_base64",
    "save_images_to_temp",
    "clean_amount",
    "format_amount_french",
    "find_field_by_code",
    "extract_field_codes",
    "is_pdf_scanned",
    "validate_siren",
    "validate_siret",
    "get_field_path_for_code",

    # Mappings codes fiscaux
    "FISCAL_CODE_MAPPING_2050",
    "FISCAL_CODE_MAPPING_2051",
    "FISCAL_CODE_MAPPING_2052",
    "FISCAL_CODE_MAPPING_2053",

    # Exceptions
    "ExtractionError",
    "InvalidPDFError",
    "EmptyPDFError",
    "PasswordProtectedPDFError",
    "UnsupportedFormTypeError",
    "ValidationError",
    "AIExtractionError",
    "RateLimitError",
    "TokenLimitExceededError",
    "ParsingError",
    "OCRError",
    "DependencyError",
]
