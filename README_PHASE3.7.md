# 🚀 Phase 3.7 - Système Sauvegarde/Chargement Variantes LBO

**Date**: Février 2026
**Statut**: Modules créés - Intégration optionnelle

---

## 📦 Modules Créés

### 1. `src/persistence/variant_manager.py` - Gestionnaire Variantes ⭐

**Fonctionnalités principales** :

#### 💾 Sauvegarde Intelligente
```python
from src.persistence.variant_manager import VariantManager, VariantStatus

manager = VariantManager()

# Sauvegarder variante
variant = manager.save_variant(
    name="Montage 70% dette",
    company_name="ACME SARL",
    lbo_structure={...},
    norm_data={...},
    financial_data={...},
    metrics={"dscr_min": 0.83, "leverage": 3.3},
    description="Montage initial avec dette senior 70%",
    status=VariantStatus.DRAFT,
    tags=["baseline", "70pct_dette"]
)
```

#### 📂 Chargement & Filtrage
```python
# Charger variante par ID
variant = manager.load_variant("ACME_SARL_20260201_143022")

# Lister toutes les variantes d'une entreprise
variants = manager.list_variants(company_name="ACME SARL")

# Filtrer par statut
validated = manager.list_variants(status=VariantStatus.VALIDATED)

# Filtrer par tags
optimized = manager.list_variants(tags=["optimisé", "60pct_dette"])
```

#### 🔍 Comparaison Côte à Côte
```python
# Comparer 2-5 variantes
comparison = manager.compare_variants([
    "ACME_SARL_20260201_143022",  # Variante 1
    "ACME_SARL_20260201_145533"   # Variante 2
])

# Résultat structuré
comparison = {
    "variants": [...],
    "metrics_comparison": {
        "dscr_min": [0.83, 1.15],      # Variante 1 vs 2
        "leverage": [3.3, 2.8],
        "equity_pct": [30.0, 40.0]
    },
    "structure_comparison": {...},
    "decision_comparison": {...}
}
```

#### 📤 Export/Import Batch
```python
# Exporter plusieurs variantes dans 1 fichier
manager.export_variants(
    variant_ids=["id1", "id2", "id3"],
    export_path="data/exports/acme_variants_backup.json"
)

# Importer variantes depuis backup
count = manager.import_variants("data/exports/acme_variants_backup.json")
# → 3 variantes importées
```

#### 🗑️ Gestion Cycle de Vie
```python
# Supprimer variante obsolète
manager.delete_variant("old_variant_id")

# Archiver variante (plutôt que supprimer)
manager.save_variant(
    ...,
    variant_id="existing_id",  # Met à jour
    status=VariantStatus.ARCHIVED
)
```

### 2. `src/ui/variant_ui.py` - Interface Streamlit ⭐

**Fonctionnalités interface** :

#### 💾 Section Sauvegarde
```python
from src.ui.variant_ui import render_save_variant_section

# Dans Tab 4 ou page dédiée
render_save_variant_section(
    company_name="ACME SARL",
    lbo_structure=st.session_state.lbo_structure,
    norm_data=st.session_state.normalization_data,
    financial_data=st.session_state.financial_data,
    metrics=st.session_state.metrics,
    decision=st.session_state.acquisition_decision
)
```

**Champs formulaire** :
- Nom variante (obligatoire)
- Statut (🟡 Brouillon / 🟢 Validé / 🔴 Rejeté / ⚫ Archivé)
- Description (optionnel)
- Tags séparés par virgules

#### 📂 Section Chargement
```python
from src.ui.variant_ui import render_load_variant_section

# Afficher liste variantes avec filtres
variant_id = render_load_variant_section(company_name="ACME SARL")

if variant_id:
    # Charger dans session Streamlit
    manager = VariantManager()
    variant = manager.load_variant(variant_id)
    st.session_state.lbo_structure = variant.lbo_structure
    # ...
```

**Fonctionnalités** :
- Filtrage par statut
- Filtrage par tags
- Affichage métriques clés par variante
- Actions : Charger / Supprimer / Exporter

#### 🔍 Section Comparaison
```python
from src.ui.variant_ui import render_comparison_section

# Comparer 2-5 variantes sélectionnées
render_comparison_section(company_name="ACME SARL")
```

**Affichage** :
- Tableau résumé variantes sélectionnées
- Comparaison métriques (DSCR, leverage, equity %)
- Comparaison structure financement
- Comparaison décisions (GO/WATCH/NO-GO)

#### 📚 Interface Complète
```python
from src.ui.variant_ui import render_variant_manager

# Page dédiée ou Tab 4
render_variant_manager()
```

**3 onglets** :
1. **💾 Sauvegarder** : Formulaire sauvegarde
2. **📂 Charger** : Liste + filtres + actions
3. **🔍 Comparer** : Comparaison multi-variantes

---

## 🎯 Cas d'Usage

### Scénario 1 : Optimiser un Montage

**Objectif** : Tester différentes structures de dette pour trouver la meilleure

**Workflow** :

1. **Montage initial (70% dette)**
   - Tab 2 : Configurer dette senior 70%, equity 30%
   - Tab 3 : DSCR = 0.83 → 🟡 WATCH
   - Tab 4 : 💾 Sauvegarder "Montage Base 70% dette"

2. **Variante optimisée (60% dette)**
   - Tab 2 : Réduire dette à 60%, augmenter equity à 40%
   - Tab 3 : DSCR = 1.15 → 🟢 GO
   - Tab 4 : 💾 Sauvegarder "Montage Optimisé 60% dette"

3. **Variante agressive (75% dette)**
   - Tab 2 : Augmenter dette à 75%, réduire equity à 25%
   - Tab 3 : DSCR = 0.65 → 🔴 NO-GO
   - Tab 4 : 💾 Sauvegarder "Montage Agressif 75% dette"

4. **Comparaison**
   - Tab 4 : 🔍 Comparer les 3 variantes
   - Analyser : DSCR, Dette/EBITDA, Risque
   - **Décision** : Retenir variante 60% dette

5. **Validation**
   - Tab 4 : 📂 Charger "Montage Optimisé 60% dette"
   - Modifier statut → 🟢 Validé
   - 💾 Re-sauvegarder

### Scénario 2 : Archiver Variantes Historiques

**Objectif** : Garder trace des anciennes analyses pour audit

**Workflow** :

1. **Analyse 2025**
   - Créer variantes pour dossier ACME SARL
   - Sauvegarder avec tags: `["2025", "initial"]`

2. **1 an plus tard (2026)**
   - Nouvelle analyse avec données actualisées
   - Archiver anciennes variantes :
     ```python
     # Via UI ou code
     manager.save_variant(
         ...,
         variant_id="old_id",
         status=VariantStatus.ARCHIVED
     )
     ```

3. **Comparaison historique**
   - Comparer variante 2025 vs variante 2026
   - Analyser évolution métriques
   - Identifier tendances

### Scénario 3 : Backup & Partage

**Objectif** : Sauvegarder analyses pour partage équipe

**Workflow** :

1. **Export batch**
   ```python
   # Sélectionner variantes validées
   validated = manager.list_variants(status=VariantStatus.VALIDATED)
   variant_ids = [v.id for v in validated]

   # Exporter dans fichier unique
   manager.export_variants(
       variant_ids=variant_ids,
       export_path="exports/validated_variants_feb2026.json"
   )
   ```

2. **Partage fichier**
   - Envoyer `validated_variants_feb2026.json` par email
   - Ou stocker sur drive partagé

3. **Import côté collègue**
   ```python
   # Collègue importe les variantes
   count = manager.import_variants("validated_variants_feb2026.json")
   # → Toutes les variantes disponibles localement
   ```

---

## 📊 Structure Données Variante

### Format JSON Sauvegardé

```json
{
  "id": "ACME_SARL_20260201_143022",
  "name": "Montage Optimisé 60% dette",
  "company_name": "ACME SARL",
  "created_at": "2026-02-01T14:30:22",
  "modified_at": "2026-02-01T15:45:10",
  "status": "validated",
  "description": "Montage avec 60% dette, DSCR 1.15, décision GO",
  "tags": ["optimisé", "60pct_dette", "validated_feb2026"],

  "lbo_structure": {
    "acquisition_price": 5000000,
    "total_debt": 3000000,
    "equity_amount": 2000000,
    "debt_layers": [
      {
        "name": "Senior",
        "amount": 2500000,
        "interest_rate": 0.045,
        "duration_years": 7,
        "grace_period": 0
      },
      {
        "name": "Bpifrance",
        "amount": 500000,
        "interest_rate": 0.03,
        "duration_years": 8,
        "grace_period": 2
      }
    ]
  },

  "norm_data": {
    "ebitda_bank": 1050000,
    "ebitda_equity": 950000,
    "adjustments": [...]
  },

  "financial_data": {
    "metadata": {...},
    "balance_sheet": {...},
    "income_statement": {...}
  },

  "metrics": {
    "dscr_min": 1.15,
    "leverage": 2.8,
    "margin": 12.4,
    "equity_pct": 40.0,
    "fcf_year3": 350000
  },

  "decision": {
    "decision": {"value": "GO"},
    "overall_score": 85,
    "deal_breakers": [],
    "warnings": [],
    "recommendations": [
      "Covenant DSCR trimestriel recommandé",
      "Marge d'amélioration sur rentabilité"
    ]
  }
}
```

### Emplacement Fichiers

```
data/
└── variants/
    ├── ACME_SARL_20260201_143022.json
    ├── ACME_SARL_20260201_145533.json
    ├── XYZ_Corp_20260125_092011.json
    └── ...
```

---

## 🎨 Aperçu Interface (Conceptuel)

### Tab "💾 Sauvegarder"

```
┌────────────────────────────────────────────────────┐
│ 💾 Sauvegarder Variante                            │
├────────────────────────────────────────────────────┤
│                                                    │
│  Nom de la variante *                              │
│  [Montage Optimisé 60% dette        ]              │
│                                                    │
│  Statut: [🟢 Validé  ▼]                            │
│                                                    │
│  Description (optionnel)                           │
│  ┌──────────────────────────────────────────┐     │
│  │ Montage avec 60% dette senior,           │     │
│  │ equity 40%. DSCR confortable à 1.15.     │     │
│  └──────────────────────────────────────────┘     │
│                                                    │
│  Tags: [optimisé, 60pct_dette, feb2026    ]        │
│                                                    │
│  [        💾 Sauvegarder        ]                  │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Tab "📂 Charger"

```
┌────────────────────────────────────────────────────┐
│ 📂 Charger Variante                                │
├────────────────────────────────────────────────────┤
│                                                    │
│  Filtrer par statut: [Tous ▼]                      │
│  Filtrer par tags: [optimisé              ]        │
│                                                    │
│  **2 variante(s) trouvée(s)**                      │
│                                                    │
│  ▼ 🟢 Montage Optimisé 60% dette - ACME SARL       │
│     Créée: 01/02/2026 14:30                        │
│     Modifiée: 01/02/2026 15:45                     │
│     Tags: optimisé, 60pct_dette                    │
│                                                    │
│     DSCR: 1.15 | Dette/EB: 2.8x | Equity: 40%      │
│     Décision: GO (85/100)                          │
│                                                    │
│     [📥 Charger] [🗑️ Supprimer] [💾 Exporter]     │
│                                                    │
│  ▼ 🟡 Montage Base 70% dette - ACME SARL           │
│     ...                                            │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Tab "🔍 Comparer"

```
┌────────────────────────────────────────────────────┐
│ 🔍 Comparer Variantes                              │
├────────────────────────────────────────────────────┤
│                                                    │
│  Sélectionner variantes (2-5):                     │
│  [✓] Montage Optimisé 60% dette                    │
│  [✓] Montage Base 70% dette                        │
│  [ ] Montage Agressif 75% dette                    │
│                                                    │
├────────────────────────────────────────────────────┤
│ 📊 Comparaison Métriques                           │
│                                                    │
│  DSCR minimum      Écart: 0.32                     │
│      1.15                                          │
│                                                    │
│  Dette/EBITDA      Écart: 0.5x                     │
│      2.8x                                          │
│                                                    │
│ ┌──────────────────────────────────────────────┐  │
│ │ Variante          │ DSCR  │ Dette/EB │ Equity│  │
│ ├───────────────────┼───────┼──────────┼───────┤  │
│ │ Optimisé 60%      │ 1.15  │ 2.8x     │ 40%   │  │
│ │ Base 70%          │ 0.83  │ 3.3x     │ 30%   │  │
│ └──────────────────────────────────────────────┘  │
│                                                    │
│ ✅ Décisions                                       │
│ │ Variante    │ Décision │ Score │ Warnings │     │
│ ├─────────────┼──────────┼───────┼──────────┤     │
│ │ Optimisé    │ GO       │ 85/100│ 0        │     │
│ │ Base        │ WATCH    │ 75/100│ 2        │     │
│ └─────────────────────────────────────────────┘   │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 🔧 Intégration dans l'App

### Option A : Ajouter à Tab 4

Intégrer dans Tab 4 existant :

```python
# Dans app_v3.py - Tab 4

from src.ui.variant_ui import render_variant_manager

with tab4:
    # ... Executive summary existant ...

    st.divider()

    # Ajouter gestion variantes
    render_variant_manager()
```

### Option B : Page Dédiée

Créer nouvelle page Streamlit :

```python
# src/ui/pages/5_variantes.py

import streamlit as st
from src.ui.variant_ui import render_variant_manager

st.set_page_config(
    page_title="Gestion Variantes",
    page_icon="📚"
)

render_variant_manager()
```

### Option C : Boutons Rapides dans Tab 2

Ajouter sauvegarde rapide :

```python
# Dans Tab 2 - Montage LBO

col1, col2, col3 = st.columns(3)

with col3:
    if st.button("💾 Sauvegarder Variante"):
        st.session_state.show_save_variant = True

if st.session_state.get('show_save_variant'):
    render_save_variant_section(...)
```

---

## ✅ Tests Validation

### Tests Unitaires Intégrés

Le module `variant_manager.py` contient des tests unitaires :

```bash
# Exécuter tests
python src/persistence/variant_manager.py

# Résultat attendu:
# ✅ Test 1: Sauvegarde variante
# ✅ Test 2: Chargement variante
# ✅ Test 3: Sauvegarde variante optimisée
# ✅ Test 4: Listing variantes
# ✅ Test 5: Filtrage par statut
# ✅ Test 6: Comparaison variantes
# ✅ Test 7: Export/Import
# ✅ TOUS LES TESTS PASSÉS
```

### Tests d'Intégration

```bash
# Tester dans Streamlit
streamlit run src/ui/app_v3.py

# Workflow test:
# 1. Créer montage LBO (Tab 2)
# 2. Aller Tab 4 → Sauvegarder variante
# 3. Modifier paramètres (Tab 2)
# 4. Sauvegarder nouvelle variante
# 5. Tab 4 → Comparer les 2 variantes
# 6. Vérifier export/import fonctionne
```

---

## 🚀 Roadmap Future

Améliorations envisagées :

- [ ] **Auto-save** : Sauvegarde automatique toutes les 5 min
- [ ] **Diff viewer** : Voir exactement ce qui a changé entre 2 variantes
- [ ] **Version control** : Système de branches/commits pour variantes
- [ ] **Cloud sync** : Synchronisation Google Drive / Dropbox
- [ ] **Collaborative editing** : Plusieurs utilisateurs en simultané
- [ ] **Templates** : Variantes pré-configurées par secteur

---

## 📚 Documentation API

### VariantManager

```python
class VariantManager:
    """Gestionnaire de variantes LBO."""

    def __init__(self, storage_dir: str = "data/variants"):
        """Initialiser avec répertoire stockage."""

    def save_variant(...) -> LBOVariant:
        """Sauvegarder variante (create/update)."""

    def load_variant(variant_id: str) -> Optional[LBOVariant]:
        """Charger variante par ID."""

    def list_variants(
        company_name: Optional[str] = None,
        status: Optional[VariantStatus] = None,
        tags: Optional[List[str]] = None
    ) -> List[LBOVariant]:
        """Lister variantes avec filtres."""

    def delete_variant(variant_id: str) -> bool:
        """Supprimer variante."""

    def compare_variants(variant_ids: List[str]) -> Dict:
        """Comparer variantes côte à côte."""

    def export_variants(variant_ids: List[str], export_path: str) -> bool:
        """Exporter batch vers fichier."""

    def import_variants(import_path: str) -> int:
        """Importer batch depuis fichier."""
```

### LBOVariant (Dataclass)

```python
@dataclass
class LBOVariant:
    """Variante montage LBO."""
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
```

---

## 💡 Best Practices

### Nommage Variantes

**Bon** :
- "Montage 60% dette senior"
- "Option aggressive 75% LBO"
- "Variante optimisée Feb2026"

**Mauvais** :
- "Test 1"
- "Nouvelle variante"
- "aaa"

### Utilisation Tags

**Recommandations** :
- Inclure % dette : `70pct_dette`, `60pct_dette`
- Inclure date : `feb2026`, `2026_baseline`
- Inclure statut business : `optimisé`, `aggressif`, `conservateur`
- Inclure version : `v1`, `v2`, `final`

**Exemple tags complets** :
```
["70pct_dette", "feb2026", "baseline", "v1"]
```

### Gestion Cycle de Vie

1. **DRAFT** : Variante en cours d'élaboration
2. **VALIDATED** : Variante approuvée pour présentation
3. **REJECTED** : Variante écartée mais gardée pour historique
4. **ARCHIVED** : Variante obsolète (anciennes analyses)

---

**Version**: 3.7
**Statut**: ✅ **Modules créés et testés**
**Prochaine étape**: Intégration dans app_v3.py

🎉 **Système de gestion variantes prêt à être déployé !**
