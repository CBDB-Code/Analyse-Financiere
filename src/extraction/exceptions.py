"""
Exceptions personnalisées pour le module d'extraction.

Ce module définit les exceptions spécifiques aux erreurs
d'extraction de données depuis les liasses fiscales.
"""


class ExtractionError(Exception):
    """
    Exception de base pour les erreurs d'extraction.

    Levée lorsque l'extraction de données depuis un PDF échoue
    pour une raison non spécifique.

    Attributes:
        message: Message d'erreur descriptif.
        pdf_path: Chemin du fichier PDF concerné.
        details: Détails supplémentaires sur l'erreur.
    """

    def __init__(
        self,
        message: str,
        pdf_path: str = None,
        details: dict = None
    ):
        self.message = message
        self.pdf_path = pdf_path
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.pdf_path:
            return f"{self.message} (fichier: {self.pdf_path})"
        return self.message


class InvalidPDFError(ExtractionError):
    """
    Exception levée lorsque le fichier PDF est invalide ou corrompu.

    Causes possibles:
    - Fichier non trouvé
    - Fichier vide
    - Format de fichier incorrect
    - PDF corrompu ou protégé par mot de passe
    """

    def __init__(
        self,
        message: str = "Le fichier PDF est invalide ou corrompu",
        pdf_path: str = None,
        details: dict = None
    ):
        super().__init__(message, pdf_path, details)


class EmptyPDFError(InvalidPDFError):
    """
    Exception levée lorsque le PDF est vide ou ne contient pas de données.
    """

    def __init__(
        self,
        message: str = "Le fichier PDF est vide ou ne contient pas de texte",
        pdf_path: str = None
    ):
        super().__init__(message, pdf_path)


class PasswordProtectedPDFError(InvalidPDFError):
    """
    Exception levée lorsque le PDF est protégé par mot de passe.
    """

    def __init__(
        self,
        message: str = "Le fichier PDF est protégé par mot de passe",
        pdf_path: str = None
    ):
        super().__init__(message, pdf_path)


class UnsupportedFormTypeError(ExtractionError):
    """
    Exception levée lorsque le type de formulaire n'est pas supporté.

    Les formulaires supportés sont:
    - 2033 (régime simplifié)
    - 2050-2059 (régime réel normal)
    """

    def __init__(
        self,
        form_type: str = None,
        pdf_path: str = None
    ):
        if form_type:
            message = f"Type de formulaire non supporté: {form_type}"
        else:
            message = "Impossible de détecter le type de formulaire"
        super().__init__(message, pdf_path, {"form_type": form_type})
        self.form_type = form_type


class ValidationError(ExtractionError):
    """
    Exception levée lorsque les données extraites échouent à la validation.

    Causes possibles:
    - Déséquilibre Actif/Passif
    - Champs obligatoires manquants
    - Incohérence entre les documents
    """

    def __init__(
        self,
        message: str = "Les données extraites sont invalides",
        errors: list = None,
        pdf_path: str = None
    ):
        details = {"validation_errors": errors or []}
        super().__init__(message, pdf_path, details)
        self.errors = errors or []


class AIExtractionError(ExtractionError):
    """
    Exception levée lorsque l'extraction via AI (Claude) échoue.

    Causes possibles:
    - Erreur API Claude
    - Limite de tokens dépassée
    - Réponse JSON invalide
    - Timeout
    """

    def __init__(
        self,
        message: str = "L'extraction via AI a échoué",
        pdf_path: str = None,
        api_error: str = None,
        tokens_used: int = None
    ):
        details = {}
        if api_error:
            details["api_error"] = api_error
        if tokens_used is not None:
            details["tokens_used"] = tokens_used
        super().__init__(message, pdf_path, details)
        self.api_error = api_error
        self.tokens_used = tokens_used


class RateLimitError(AIExtractionError):
    """
    Exception levée lorsque la limite de requêtes API est atteinte.
    """

    def __init__(
        self,
        retry_after: int = None,
        pdf_path: str = None
    ):
        message = "Limite de requêtes API atteinte"
        if retry_after:
            message += f" (réessayer dans {retry_after} secondes)"
        super().__init__(message, pdf_path)
        self.retry_after = retry_after


class TokenLimitExceededError(AIExtractionError):
    """
    Exception levée lorsque le PDF dépasse la limite de tokens.
    """

    def __init__(
        self,
        estimated_tokens: int = None,
        max_tokens: int = None,
        pdf_path: str = None
    ):
        message = "Le PDF dépasse la limite de tokens pour l'API"
        if estimated_tokens and max_tokens:
            message += f" ({estimated_tokens} / {max_tokens})"
        super().__init__(message, pdf_path)
        self.estimated_tokens = estimated_tokens
        self.max_tokens = max_tokens


class ParsingError(ExtractionError):
    """
    Exception levée lorsque le parsing des données échoue.

    Causes possibles:
    - Format de tableau non reconnu
    - Données mal formatées
    - Structure inattendue
    """

    def __init__(
        self,
        message: str = "Erreur lors du parsing des données",
        section: str = None,
        pdf_path: str = None
    ):
        details = {}
        if section:
            details["section"] = section
        super().__init__(message, pdf_path, details)
        self.section = section


class OCRError(ExtractionError):
    """
    Exception levée lorsque l'OCR échoue sur un PDF scanné.
    """

    def __init__(
        self,
        message: str = "Erreur lors de la reconnaissance de texte (OCR)",
        pdf_path: str = None,
        page_number: int = None
    ):
        details = {}
        if page_number is not None:
            details["page_number"] = page_number
        super().__init__(message, pdf_path, details)
        self.page_number = page_number


class DependencyError(ExtractionError):
    """
    Exception levée lorsqu'une dépendance requise n'est pas installée.
    """

    def __init__(
        self,
        dependency_name: str,
        install_command: str = None
    ):
        message = f"Dépendance manquante: {dependency_name}"
        if install_command:
            message += f" (installer avec: {install_command})"
        super().__init__(message)
        self.dependency_name = dependency_name
        self.install_command = install_command
