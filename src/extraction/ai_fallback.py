"""
Extracteur de données via Claude AI pour les PDFs difficiles.

Ce module fournit une classe AIExtractor qui utilise l'API Claude
d'Anthropic pour extraire les données de liasses fiscales depuis
des images de PDF (notamment les PDFs scannés).
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Any
from datetime import date
from dataclasses import dataclass

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from .exceptions import (
    AIExtractionError,
    RateLimitError,
    TokenLimitExceededError,
    DependencyError,
    ExtractionError,
)
from .utils import (
    pdf_to_images,
    image_to_base64,
    clean_amount,
)


logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Résultat d'une extraction via AI."""
    data: dict
    tokens_used: int
    cached: bool
    confidence: float
    model: str
    cost_estimate: float


class AIExtractor:
    """
    Extracteur de liasses fiscales utilisant Claude AI.

    Cette classe convertit les PDFs en images et utilise les capacités
    de vision de Claude pour extraire les données structurées.

    Attributes:
        api_key: Clé API Anthropic.
        model: Modèle Claude à utiliser.
        max_tokens: Limite de tokens pour la réponse.
        cache_dir: Répertoire de cache des résultats.

    Example:
        >>> extractor = AIExtractor(api_key="sk-...")
        >>> data = extractor.extract_with_claude("/path/to/liasse.pdf")
        >>> print(data["balance_sheet"]["assets"]["total_assets"])
    """

    # Modèle par défaut
    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    # Limite de pages pour éviter les coûts excessifs
    MAX_PAGES_DEFAULT = 10

    # Coût estimé par million de tokens (approximatif)
    COST_PER_MILLION_INPUT_TOKENS = 3.0  # Claude Sonnet
    COST_PER_MILLION_OUTPUT_TOKENS = 15.0

    # Prompt système pour l'extraction
    SYSTEM_PROMPT = """Tu es un expert-comptable français spécialisé dans l'analyse de liasses fiscales.
Tu vas recevoir des images d'une liasse fiscale française (formulaires 2033 ou 2050-2059).

Ton objectif est d'extraire TOUTES les données financières présentes et de les retourner dans un format JSON structuré.

IMPORTANT:
- Extrais les montants avec précision, y compris les valeurs négatives (entre parenthèses ou avec signe moins)
- Les codes fiscaux (AA, AB, BH, etc.) sont importants - associe chaque valeur à son code
- Distingue bien les colonnes "Brut", "Amortissements/Dépréciations" et "Net"
- Pour le bilan, vérifie que Total Actif = Total Passif
- Pour le compte de résultat, identifie les différents niveaux de résultat
- Si une valeur n'est pas lisible ou absente, utilise null
- Convertis les montants en euros (pas de milliers de euros)
"""

    EXTRACTION_PROMPT = """Analyse ces images de liasse fiscale française et extrais les données au format JSON suivant.
Retourne UNIQUEMENT le JSON, sans texte avant ou après.

{
  "metadata": {
    "company_name": "Raison sociale si visible",
    "siren": "SIREN 9 chiffres si visible",
    "siret": "SIRET 14 chiffres si visible ou null",
    "naf_code": "Code NAF si visible ou null",
    "legal_form": "Forme juridique (SA, SAS, SARL, etc.) ou null",
    "fiscal_year_end": "Date de clôture au format YYYY-MM-DD",
    "fiscal_year_duration_months": 12,
    "form_types": ["Liste des formulaires détectés: 2050, 2051, 2052, etc."]
  },
  "balance_sheet": {
    "assets": {
      "fixed_assets": {
        "intangible_assets": 0.0,
        "tangible_assets": 0.0,
        "financial_assets": 0.0,
        "total": 0.0
      },
      "current_assets": {
        "inventory": 0.0,
        "trade_receivables": 0.0,
        "other_receivables": 0.0,
        "prepaid_expenses": 0.0,
        "marketable_securities": 0.0,
        "cash": 0.0,
        "total": 0.0
      },
      "total_assets": 0.0
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
        "total": 0.0
      },
      "provisions": {
        "provisions_for_risks": 0.0,
        "provisions_for_charges": 0.0,
        "total": 0.0
      },
      "debt": {
        "long_term_debt": 0.0,
        "short_term_debt": 0.0,
        "bank_overdrafts": 0.0,
        "lease_obligations": 0.0,
        "bonds": 0.0,
        "shareholder_loans": 0.0,
        "total_financial_debt": 0.0
      },
      "operating_liabilities": {
        "trade_payables": 0.0,
        "tax_liabilities": 0.0,
        "social_liabilities": 0.0,
        "advances_received": 0.0,
        "deferred_revenue": 0.0,
        "other_liabilities": 0.0,
        "total": 0.0
      },
      "total_liabilities": 0.0
    }
  },
  "income_statement": {
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
      "total": 0.0
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
      "total": 0.0
    },
    "operating_income": 0.0,
    "financial_result": {
      "financial_income": 0.0,
      "interest_expense": 0.0,
      "net_financial_result": 0.0
    },
    "current_income_before_tax": 0.0,
    "exceptional_result": {
      "exceptional_income": 0.0,
      "exceptional_expense": 0.0,
      "net_exceptional_result": 0.0
    },
    "employee_profit_sharing": 0.0,
    "income_tax_expense": 0.0,
    "net_income": 0.0
  },
  "raw_fields": {
    "AA": {"code": "AA", "value": 0.0},
    "BH": {"code": "BH", "value": 0.0}
  }
}

INSTRUCTIONS:
1. Remplis tous les champs avec les valeurs trouvées dans les images
2. Utilise 0.0 pour les champs vides ou non applicables
3. Dans raw_fields, liste TOUS les codes fiscaux trouvés avec leurs valeurs
4. Assure-toi que les totaux sont cohérents (Actif = Passif, etc.)
5. Le résultat net doit être identique dans equity.net_income et income_statement.net_income
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 8192,
        cache_dir: Optional[str] = None,
        max_pages: int = MAX_PAGES_DEFAULT
    ):
        """
        Initialise l'extracteur AI.

        Args:
            api_key: Clé API Anthropic. Si None, utilise ANTHROPIC_API_KEY.
            model: Modèle Claude à utiliser.
            max_tokens: Limite de tokens pour la réponse.
            cache_dir: Répertoire pour cacher les résultats.
            max_pages: Nombre maximum de pages à traiter.
        """
        self._check_dependencies()

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Clé API Anthropic requise. Définissez ANTHROPIC_API_KEY "
                "ou passez api_key au constructeur."
            )

        self.model = model or self.DEFAULT_MODEL
        self.max_tokens = max_tokens
        self.max_pages = max_pages

        # Initialiser le client Anthropic
        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Configuration du cache
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".cache" / "liasse_fiscale"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"AIExtractor initialisé avec modèle {self.model}")

    def _check_dependencies(self) -> None:
        """Vérifie que les dépendances sont installées."""
        if not HAS_ANTHROPIC:
            raise DependencyError(
                "anthropic",
                "pip install anthropic"
            )

    def extract_with_claude(
        self,
        pdf_path: str,
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> dict:
        """
        Extrait les données d'une liasse fiscale via Claude AI.

        Cette méthode:
        1. Vérifie le cache pour des résultats existants
        2. Convertit le PDF en images
        3. Envoie les images à Claude avec le prompt d'extraction
        4. Parse et valide la réponse JSON
        5. Cache le résultat

        Args:
            pdf_path: Chemin vers le fichier PDF.
            use_cache: Utiliser le cache si disponible.
            force_refresh: Forcer une nouvelle extraction.

        Returns:
            Dictionnaire contenant les données extraites, conformes
            au schéma FiscalData.

        Raises:
            AIExtractionError: Si l'extraction échoue.
            TokenLimitExceededError: Si le PDF est trop volumineux.

        Example:
            >>> extractor = AIExtractor()
            >>> data = extractor.extract_with_claude("/path/to/liasse.pdf")
            >>> print(f"CA: {data['income_statement']['revenues']['net_revenue']}")
        """
        pdf_path = Path(pdf_path)
        logger.info(f"Extraction AI: {pdf_path}")

        # Générer une clé de cache unique
        cache_key = self._generate_cache_key(pdf_path)

        # Vérifier le cache
        if use_cache and not force_refresh:
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.info("Résultat trouvé en cache")
                return cached_result

        # Convertir le PDF en images
        try:
            images = pdf_to_images(
                str(pdf_path),
                dpi=150,  # Résolution suffisante pour Claude
                max_pages=self.max_pages
            )
        except Exception as e:
            raise AIExtractionError(
                f"Impossible de convertir le PDF en images: {e}",
                pdf_path=str(pdf_path)
            )

        if not images:
            raise AIExtractionError(
                "Aucune image extraite du PDF",
                pdf_path=str(pdf_path)
            )

        logger.info(f"{len(images)} page(s) à traiter")

        # Vérifier si on doit découper (> max_pages)
        if len(images) > self.max_pages:
            logger.warning(
                f"PDF trop volumineux ({len(images)} pages), "
                f"traitement des {self.max_pages} premières pages"
            )
            images = images[:self.max_pages]

        # Préparer le message avec les images
        content = self._prepare_message_content(images)

        # Appeler Claude API
        try:
            result = self._call_claude_api(content)
        except anthropic.RateLimitError as e:
            raise RateLimitError(pdf_path=str(pdf_path))
        except anthropic.APIError as e:
            raise AIExtractionError(
                f"Erreur API Claude: {e}",
                pdf_path=str(pdf_path),
                api_error=str(e)
            )

        # Parser la réponse
        try:
            data = self._parse_response(result)
        except json.JSONDecodeError as e:
            raise AIExtractionError(
                f"Réponse JSON invalide de Claude: {e}",
                pdf_path=str(pdf_path)
            )

        # Ajouter les métadonnées d'extraction
        data["metadata"] = data.get("metadata", {})
        data["metadata"]["source_file"] = pdf_path.name
        data["metadata"]["extraction_date"] = date.today().isoformat()
        data["metadata"]["extraction_method"] = "ai_claude"
        data["metadata"]["model_used"] = self.model
        data["is_scanned"] = True  # Assumé pour AI extraction

        # Calculer les tokens utilisés et le coût
        tokens_input = result.usage.input_tokens
        tokens_output = result.usage.output_tokens
        cost = self._estimate_cost(tokens_input, tokens_output)

        logger.info(
            f"Extraction terminée - Tokens: {tokens_input} in / {tokens_output} out, "
            f"Coût estimé: ${cost:.4f}"
        )

        # Cacher le résultat
        if use_cache:
            self._cache_result(cache_key, data)

        return data

    def _prepare_message_content(self, images: list) -> list:
        """Prépare le contenu du message avec les images."""
        content = []

        # Ajouter chaque image
        for i, image in enumerate(images):
            # Convertir l'image en base64
            image_b64 = image_to_base64(image)

            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_b64
                }
            })

            logger.debug(f"Image {i+1}/{len(images)} ajoutée au message")

        # Ajouter le prompt d'extraction
        content.append({
            "type": "text",
            "text": self.EXTRACTION_PROMPT
        })

        return content

    def _call_claude_api(self, content: list) -> Any:
        """Appelle l'API Claude avec le contenu préparé."""
        logger.info(f"Appel API Claude ({self.model})...")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )

        return response

    def _parse_response(self, response: Any) -> dict:
        """Parse la réponse de Claude en dictionnaire."""
        # Extraire le texte de la réponse
        text_content = ""
        for block in response.content:
            if hasattr(block, "text"):
                text_content += block.text

        if not text_content.strip():
            raise AIExtractionError("Réponse vide de Claude")

        # Trouver le JSON dans la réponse
        # Parfois Claude ajoute du texte avant/après le JSON
        json_text = text_content.strip()

        # Essayer de trouver le JSON
        if not json_text.startswith("{"):
            # Chercher le début du JSON
            start = json_text.find("{")
            if start == -1:
                raise AIExtractionError(
                    "Pas de JSON trouvé dans la réponse de Claude"
                )
            json_text = json_text[start:]

        if not json_text.endswith("}"):
            # Chercher la fin du JSON
            end = json_text.rfind("}")
            if end == -1:
                raise AIExtractionError(
                    "JSON incomplet dans la réponse de Claude"
                )
            json_text = json_text[:end + 1]

        # Parser le JSON
        data = json.loads(json_text)

        # Valider et nettoyer les données
        data = self._validate_and_clean_data(data)

        return data

    def _validate_and_clean_data(self, data: dict) -> dict:
        """Valide et nettoie les données extraites."""
        # S'assurer que les structures de base existent
        if "metadata" not in data:
            data["metadata"] = {}

        if "balance_sheet" not in data:
            data["balance_sheet"] = {"assets": {}, "liabilities": {}}

        if "income_statement" not in data:
            data["income_statement"] = {}

        if "raw_fields" not in data:
            data["raw_fields"] = {}

        # Convertir les valeurs null en 0.0
        data = self._replace_nulls(data)

        # Nettoyer les montants (au cas où ils seraient en string)
        data = self._clean_amounts(data)

        return data

    def _replace_nulls(self, obj: Any, replacement: float = 0.0) -> Any:
        """Remplace les valeurs null par une valeur par défaut."""
        if obj is None:
            return replacement
        elif isinstance(obj, dict):
            return {k: self._replace_nulls(v, replacement) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_nulls(item, replacement) for item in obj]
        return obj

    def _clean_amounts(self, obj: Any) -> Any:
        """Nettoie les montants dans les données."""
        if isinstance(obj, str):
            # Essayer de convertir les strings numériques
            try:
                return clean_amount(obj)
            except ValueError:
                return obj
        elif isinstance(obj, dict):
            return {k: self._clean_amounts(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_amounts(item) for item in obj]
        return obj

    def _generate_cache_key(self, pdf_path: Path) -> str:
        """Génère une clé de cache unique pour un PDF."""
        # Utiliser le hash du fichier pour détecter les modifications
        hasher = hashlib.md5()

        # Ajouter le chemin et la taille
        hasher.update(str(pdf_path).encode())
        hasher.update(str(pdf_path.stat().st_size).encode())
        hasher.update(str(pdf_path.stat().st_mtime).encode())

        # Ajouter le modèle utilisé
        hasher.update(self.model.encode())

        return hasher.hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[dict]:
        """Récupère un résultat depuis le cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Cache corrompu, le supprimer
                cache_file.unlink(missing_ok=True)

        return None

    def _cache_result(self, cache_key: str, data: dict) -> None:
        """Sauvegarde un résultat dans le cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Résultat caché: {cache_file}")
        except IOError as e:
            logger.warning(f"Impossible de cacher le résultat: {e}")

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estime le coût de l'appel API."""
        input_cost = (input_tokens / 1_000_000) * self.COST_PER_MILLION_INPUT_TOKENS
        output_cost = (output_tokens / 1_000_000) * self.COST_PER_MILLION_OUTPUT_TOKENS
        return input_cost + output_cost

    def clear_cache(self) -> int:
        """
        Vide le cache des résultats.

        Returns:
            Nombre de fichiers supprimés.
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except IOError:
                pass

        logger.info(f"Cache vidé: {count} fichier(s) supprimé(s)")
        return count

    def get_cache_stats(self) -> dict:
        """
        Retourne des statistiques sur le cache.

        Returns:
            Dictionnaire avec taille, nombre de fichiers, etc.
        """
        files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)

        return {
            "cache_dir": str(self.cache_dir),
            "file_count": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }


def extract_with_claude_simple(
    pdf_path: str,
    api_key: Optional[str] = None
) -> dict:
    """
    Fonction utilitaire pour une extraction rapide via Claude.

    Args:
        pdf_path: Chemin vers le fichier PDF.
        api_key: Clé API Anthropic (optionnel, utilise ANTHROPIC_API_KEY sinon).

    Returns:
        Dictionnaire avec les données extraites.

    Example:
        >>> data = extract_with_claude_simple("/path/to/liasse.pdf")
        >>> print(data["income_statement"]["net_income"])
    """
    extractor = AIExtractor(api_key=api_key)
    return extractor.extract_with_claude(pdf_path)
