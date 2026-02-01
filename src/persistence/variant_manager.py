"""
Module de gestion des variantes de montage LBO.

Permet de sauvegarder, charger et comparer différentes versions
d'un même montage financier pour faciliter l'optimisation.
"""

from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from enum import Enum


class VariantStatus(str, Enum):
    """Statut d'une variante."""
    DRAFT = "draft"
    VALIDATED = "validated"
    REJECTED = "rejected"
    ARCHIVED = "archived"


@dataclass
class LBOVariant:
    """
    Variante d'un montage LBO.

    Attributes:
        id: Identifiant unique
        name: Nom de la variante
        company_name: Nom entreprise
        created_at: Date création
        modified_at: Date dernière modification
        status: Statut (draft/validated/rejected)
        description: Description libre
        lbo_structure: Structure LBO (dette, equity)
        norm_data: Données normalisées
        financial_data: Données financières complètes
        metrics: Métriques calculées (DSCR, leverage, etc.)
        decision: Décision finale (GO/WATCH/NO-GO)
        tags: Tags pour filtrage
    """
    id: str
    name: str
    company_name: str
    created_at: str
    modified_at: str
    status: VariantStatus
    description: str
    lbo_structure: Dict
    norm_data: Dict
    financial_data: Dict
    metrics: Dict
    decision: Optional[Dict] = None
    tags: List[str] = None

    def __post_init__(self):
        """Initialiser tags si non fournis."""
        if self.tags is None:
            self.tags = []


class VariantManager:
    """
    Gestionnaire de variantes de montage LBO.

    Fonctionnalités:
    - Sauvegarde variantes sur disque (JSON)
    - Chargement variantes sauvegardées
    - Listing et filtrage
    - Comparaison côte à côte
    - Export/Import batch
    """

    def __init__(self, storage_dir: str = "data/variants"):
        """
        Initialiser le gestionnaire.

        Args:
            storage_dir: Répertoire de stockage des variantes
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_variant(
        self,
        name: str,
        company_name: str,
        lbo_structure: Dict,
        norm_data: Dict,
        financial_data: Dict,
        metrics: Dict,
        description: str = "",
        status: VariantStatus = VariantStatus.DRAFT,
        decision: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        variant_id: Optional[str] = None
    ) -> LBOVariant:
        """
        Sauvegarder une variante.

        Args:
            name: Nom de la variante
            company_name: Nom entreprise
            lbo_structure: Structure LBO
            norm_data: Données normalisées
            financial_data: Données financières
            metrics: Métriques calculées
            description: Description
            status: Statut
            decision: Décision finale
            tags: Tags
            variant_id: ID existant (pour mise à jour)

        Returns:
            LBOVariant sauvegardée
        """
        # Générer ID si nouveau
        if variant_id is None:
            import uuid
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_suffix = str(uuid.uuid4())[:8]
            variant_id = f"{company_name}_{timestamp}_{unique_suffix}".replace(" ", "_")

        # Charger variante existante si ID fourni
        now = datetime.now().isoformat()
        if variant_id and self._variant_exists(variant_id):
            existing = self.load_variant(variant_id)
            created_at = existing.created_at
        else:
            created_at = now

        # Créer variante
        variant = LBOVariant(
            id=variant_id,
            name=name,
            company_name=company_name,
            created_at=created_at,
            modified_at=now,
            status=status,
            description=description,
            lbo_structure=lbo_structure,
            norm_data=norm_data,
            financial_data=financial_data,
            metrics=metrics,
            decision=decision,
            tags=tags or []
        )

        # Sauvegarder sur disque
        self._write_variant(variant)

        return variant

    def load_variant(self, variant_id: str) -> Optional[LBOVariant]:
        """
        Charger une variante.

        Args:
            variant_id: ID de la variante

        Returns:
            LBOVariant ou None si non trouvée
        """
        filepath = self._get_variant_filepath(variant_id)

        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Recréer variante
        return LBOVariant(**data)

    def list_variants(
        self,
        company_name: Optional[str] = None,
        status: Optional[VariantStatus] = None,
        tags: Optional[List[str]] = None
    ) -> List[LBOVariant]:
        """
        Lister les variantes avec filtres.

        Args:
            company_name: Filtrer par entreprise
            status: Filtrer par statut
            tags: Filtrer par tags (OU logique)

        Returns:
            Liste de variantes
        """
        variants = []

        # Parcourir tous les fichiers
        for filepath in self.storage_dir.glob("*.json"):
            try:
                variant = self.load_variant(filepath.stem)
                if variant is None:
                    continue

                # Filtres
                if company_name and variant.company_name != company_name:
                    continue

                if status and variant.status != status:
                    continue

                if tags and not any(t in variant.tags for t in tags):
                    continue

                variants.append(variant)

            except Exception as e:
                # Fichier corrompu, ignorer
                print(f"Erreur chargement {filepath}: {e}")
                continue

        # Trier par date modification (plus récent en premier)
        variants.sort(key=lambda v: v.modified_at, reverse=True)

        return variants

    def delete_variant(self, variant_id: str) -> bool:
        """
        Supprimer une variante.

        Args:
            variant_id: ID de la variante

        Returns:
            True si supprimée, False sinon
        """
        filepath = self._get_variant_filepath(variant_id)

        if not filepath.exists():
            return False

        filepath.unlink()
        return True

    def compare_variants(self, variant_ids: List[str]) -> Dict:
        """
        Comparer plusieurs variantes côte à côte.

        Args:
            variant_ids: Liste IDs variantes à comparer

        Returns:
            Dict avec comparaison structurée
        """
        # Charger variantes
        variants = []
        for vid in variant_ids:
            variant = self.load_variant(vid)
            if variant:
                variants.append(variant)

        if not variants:
            return {"error": "Aucune variante trouvée"}

        # Structure comparaison
        comparison = {
            "variants": [
                {
                    "id": v.id,
                    "name": v.name,
                    "status": v.status,
                    "modified_at": v.modified_at
                }
                for v in variants
            ],
            "metrics_comparison": self._compare_metrics(variants),
            "structure_comparison": self._compare_structures(variants),
            "decision_comparison": self._compare_decisions(variants)
        }

        return comparison

    def _compare_metrics(self, variants: List[LBOVariant]) -> Dict:
        """
        Comparer les métriques clés entre variantes.

        Returns:
            Dict avec métriques par variante
        """
        metrics_keys = [
            "dscr_min",
            "leverage",
            "margin",
            "equity_pct",
            "fcf_year3"
        ]

        comparison = {}

        for key in metrics_keys:
            comparison[key] = [
                v.metrics.get(key, None) for v in variants
            ]

        return comparison

    def _compare_structures(self, variants: List[LBOVariant]) -> Dict:
        """
        Comparer les structures LBO entre variantes.

        Returns:
            Dict avec structures par variante
        """
        comparison = {
            "acquisition_price": [],
            "total_debt": [],
            "equity_amount": [],
            "senior_debt_pct": [],
            "debt_layers_count": []
        }

        for variant in variants:
            lbo = variant.lbo_structure

            comparison["acquisition_price"].append(
                lbo.get("acquisition_price", 0)
            )
            comparison["total_debt"].append(
                lbo.get("total_debt", 0)
            )
            comparison["equity_amount"].append(
                lbo.get("equity_amount", 0)
            )

            # Calcul % dette senior
            layers = lbo.get("debt_layers", [])
            total_debt = lbo.get("total_debt", 1)
            senior_amount = 0

            for layer in layers:
                if "senior" in layer.get("name", "").lower():
                    senior_amount = layer.get("amount", 0)

            comparison["senior_debt_pct"].append(
                (senior_amount / total_debt * 100) if total_debt > 0 else 0
            )
            comparison["debt_layers_count"].append(len(layers))

        return comparison

    def _compare_decisions(self, variants: List[LBOVariant]) -> Dict:
        """
        Comparer les décisions entre variantes.

        Returns:
            Dict avec décisions par variante
        """
        comparison = {
            "decisions": [],
            "scores": [],
            "deal_breakers_count": [],
            "warnings_count": []
        }

        for variant in variants:
            decision = variant.decision or {}

            comparison["decisions"].append(
                decision.get("decision", {}).get("value", "N/A")
            )
            comparison["scores"].append(
                decision.get("overall_score", 0)
            )
            comparison["deal_breakers_count"].append(
                len(decision.get("deal_breakers", []))
            )
            comparison["warnings_count"].append(
                len(decision.get("warnings", []))
            )

        return comparison

    def export_variants(
        self,
        variant_ids: List[str],
        export_path: str
    ) -> bool:
        """
        Exporter plusieurs variantes dans un fichier unique.

        Args:
            variant_ids: IDs des variantes à exporter
            export_path: Chemin fichier export

        Returns:
            True si succès
        """
        variants_data = []

        for vid in variant_ids:
            variant = self.load_variant(vid)
            if variant:
                variants_data.append(asdict(variant))

        if not variants_data:
            return False

        export_file = Path(export_path)
        export_file.parent.mkdir(parents=True, exist_ok=True)

        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(variants_data, f, indent=2, ensure_ascii=False)

        return True

    def import_variants(self, import_path: str) -> int:
        """
        Importer variantes depuis un fichier.

        Args:
            import_path: Chemin fichier import

        Returns:
            Nombre de variantes importées
        """
        import_file = Path(import_path)

        if not import_file.exists():
            return 0

        with open(import_file, 'r', encoding='utf-8') as f:
            variants_data = json.load(f)

        count = 0

        for data in variants_data:
            try:
                variant = LBOVariant(**data)
                self._write_variant(variant)
                count += 1
            except Exception as e:
                print(f"Erreur import variante: {e}")
                continue

        return count

    def _variant_exists(self, variant_id: str) -> bool:
        """Vérifier si une variante existe."""
        return self._get_variant_filepath(variant_id).exists()

    def _get_variant_filepath(self, variant_id: str) -> Path:
        """Obtenir le chemin fichier d'une variante."""
        return self.storage_dir / f"{variant_id}.json"

    def _write_variant(self, variant: LBOVariant) -> None:
        """Écrire une variante sur disque."""
        filepath = self._get_variant_filepath(variant.id)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(variant), f, indent=2, ensure_ascii=False)


# Tests unitaires
if __name__ == "__main__":
    import tempfile
    import shutil

    # Créer répertoire temporaire
    temp_dir = tempfile.mkdtemp()

    try:
        # Initialiser manager
        manager = VariantManager(storage_dir=temp_dir)

        # Données de test
        test_lbo = {
            "acquisition_price": 5_000_000,
            "total_debt": 3_500_000,
            "equity_amount": 1_500_000,
            "debt_layers": [
                {"name": "Senior", "amount": 3_000_000, "interest_rate": 0.045},
                {"name": "Bpifrance", "amount": 500_000, "interest_rate": 0.03}
            ]
        }

        test_norm = {
            "ebitda_bank": 1_050_000,
            "ebitda_equity": 950_000
        }

        test_financial = {
            "income_statement": {
                "revenues": {"net_revenue": 8_500_000}
            }
        }

        test_metrics = {
            "dscr_min": 0.83,
            "leverage": 3.3,
            "margin": 12.4,
            "equity_pct": 30.0
        }

        test_decision = {
            "decision": {"value": "WATCH"},
            "overall_score": 75,
            "deal_breakers": [],
            "warnings": ["DSCR limite"]
        }

        # Test 1: Sauvegarder variante
        print("Test 1: Sauvegarde variante...")
        variant1 = manager.save_variant(
            name="Variante Base",
            company_name="ACME SARL",
            lbo_structure=test_lbo,
            norm_data=test_norm,
            financial_data=test_financial,
            metrics=test_metrics,
            description="Montage initial 70% dette",
            status=VariantStatus.DRAFT,
            decision=test_decision,
            tags=["initial", "70pct_dette"]
        )
        print(f"✅ Variante sauvegardée: {variant1.id}")

        # Test 2: Charger variante
        print("\nTest 2: Chargement variante...")
        loaded = manager.load_variant(variant1.id)
        assert loaded is not None
        assert loaded.name == "Variante Base"
        print(f"✅ Variante chargée: {loaded.name}")

        # Test 3: Sauvegarder variante optimisée
        print("\nTest 3: Sauvegarde variante optimisée...")
        test_lbo_optimized = test_lbo.copy()
        test_lbo_optimized["total_debt"] = 3_000_000
        test_lbo_optimized["equity_amount"] = 2_000_000

        test_metrics_optimized = test_metrics.copy()
        test_metrics_optimized["dscr_min"] = 1.15
        test_metrics_optimized["equity_pct"] = 40.0

        variant2 = manager.save_variant(
            name="Variante Optimisée",
            company_name="ACME SARL",
            lbo_structure=test_lbo_optimized,
            norm_data=test_norm,
            financial_data=test_financial,
            metrics=test_metrics_optimized,
            description="Montage avec plus d'equity (60% dette)",
            status=VariantStatus.VALIDATED,
            tags=["optimisé", "60pct_dette"]
        )
        print(f"✅ Variante optimisée sauvegardée: {variant2.id}")

        # Test 4: Lister variantes
        print("\nTest 4: Listing variantes...")
        all_variants = manager.list_variants()
        assert len(all_variants) == 2
        print(f"✅ {len(all_variants)} variantes trouvées")

        # Test 5: Filtrer par statut
        print("\nTest 5: Filtrage par statut...")
        validated = manager.list_variants(status=VariantStatus.VALIDATED)
        assert len(validated) == 1
        assert validated[0].name == "Variante Optimisée"
        print(f"✅ {len(validated)} variante validée trouvée")

        # Test 6: Comparer variantes
        print("\nTest 6: Comparaison variantes...")
        comparison = manager.compare_variants([variant1.id, variant2.id])
        print(f"✅ Comparaison générée:")
        print(f"  - DSCR: {comparison['metrics_comparison']['dscr_min']}")
        print(f"  - Equity %: {comparison['metrics_comparison']['equity_pct']}")
        print(f"  - Décisions: {comparison['decision_comparison']['decisions']}")

        # Test 7: Export/Import
        print("\nTest 7: Export/Import...")
        export_file = Path(temp_dir) / "export_test.json"
        success = manager.export_variants([variant1.id, variant2.id], str(export_file))
        assert success
        print(f"✅ Export réussi: {export_file}")

        # Supprimer variantes
        manager.delete_variant(variant1.id)
        manager.delete_variant(variant2.id)
        assert len(manager.list_variants()) == 0

        # Importer
        count = manager.import_variants(str(export_file))
        assert count == 2
        assert len(manager.list_variants()) == 2
        print(f"✅ Import réussi: {count} variantes")

        print("\n" + "="*50)
        print("✅ TOUS LES TESTS PASSÉS")
        print("="*50)

    finally:
        # Nettoyer
        shutil.rmtree(temp_dir)
