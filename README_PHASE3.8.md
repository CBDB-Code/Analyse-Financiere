# 🚀 Phase 3.8 - Dashboard Comparaison Multi-Dossiers

**Date**: Février 2026
**Statut**: Module créé - Intégration optionnelle

---

## 📦 Module Créé

### `src/ui/multi_deal_dashboard.py` - Dashboard Comparatif ⭐

**Objectif** : Comparer plusieurs opportunités d'investissement LBO côte à côte pour identifier les meilleurs dossiers.

---

## ✨ Fonctionnalités Principales

### 1️⃣ Sélection Multi-Dossiers

```python
from src.ui.multi_deal_dashboard import render_multi_deal_selector

# Sélectionner jusqu'à 10 dossiers
selected_ids = render_multi_deal_selector()
```

**Filtres disponibles** :
- **Statuts** : Brouillon / Validé / Rejeté / Archivé (multi-sélection)
- **Entreprises** : Sélection par nom entreprise
- Affichage métriques clés par dossier (DSCR, décision)
- Checkbox sélection (max 10 dossiers)

### 2️⃣ Comparaison Métriques Clés

```python
from src.ui.multi_deal_dashboard import render_metrics_comparison

render_metrics_comparison(selected_ids)
```

**Tableau comparatif** :
| Entreprise | Variante | Décision | Score | DSCR | Dette/EBITDA | Marge % | Equity % | FCF Y3 |
|------------|----------|----------|-------|------|--------------|---------|----------|--------|
| ACME SARL  | Base     | WATCH    | 75/100| 0.83 | 3.30x        | 12.4%   | 30.0%    | 150k€  |
| XYZ Corp   | Optimisé | GO       | 85/100| 1.35 | 2.80x        | 15.2%   | 40.0%    | 420k€  |

**Métriques agrégées** :
- DSCR Moyen (avec maximum)
- Leverage Moyen (avec minimum)
- Marge Moyenne (avec maximum)
- Score Moyen (avec maximum)

### 3️⃣ Visualisations Comparatives

```python
from src.ui.multi_deal_dashboard import render_visual_comparison

render_visual_comparison(selected_ids)
```

**3 onglets graphiques** :

#### 📊 Graphique Radar - Métriques Clés
- DSCR normalisé (0-100)
- Marge % normalisée
- Score global
- Conversion FCF normalisée
- **Usage** : Identifier dossier le plus équilibré

#### 💰 Graphique Barres Empilées - Structure Financement
- Dette (rouge)
- Equity (vert)
- Barres par dossier
- **Usage** : Comparer structures capitalistiques

#### ⚡ Graphique Barres Multiples - Performance
- DSCR minimum (seuil 1.25)
- Dette/EBITDA (seuil 4.0x)
- Score global (seuil 70)
- Couleurs automatiques selon seuils (vert/orange/rouge)
- **Usage** : Identifier dossiers sous-performants

### 4️⃣ Matrice de Décision

```python
from src.ui.multi_deal_dashboard import render_decision_matrix

render_decision_matrix(selected_ids)
```

**Podium top 3** :
```
🥇 1er: XYZ Corp (85/100)
🥈 2ème: ABC SARL (78/100)
🥉 3ème: ACME SARL (75/100)
```

**Analyse détaillée par dossier** :
- Rang (trié par score décroissant)
- Métriques principales
- Structure financement
- ❌ Deal breakers
- ⚠️ Points d'attention
- 💡 Recommandations

### 5️⃣ Dashboard Complet

```python
from src.ui.multi_deal_dashboard import render_multi_deal_dashboard

# Page dédiée ou Tab 4
render_multi_deal_dashboard()
```

**Workflow complet** :
1. Sélection dossiers (avec filtres)
2. Tableau métriques comparatif
3. Visualisations graphiques
4. Matrice décision avec podium
5. Actions (export, rapport)

---

## 🎯 Cas d'Usage

### Scénario 1 : Sélection Meilleur Deal

**Contexte** : Fonds LBO avec 5 opportunités analysées, budget pour 1 seule acquisition

**Workflow** :

1. **Charger tous les dossiers validés**
   - Dashboard → Filtrer par statut "🟢 Validé"
   - 5 dossiers affichés

2. **Sélectionner les 5**
   - Cocher les 5 checkboxes
   - Tableau comparatif s'affiche

3. **Analyser métriques**
   - Trier mentalement par DSCR (capacité remboursement)
   - Trier par Score global
   - Identifier dossier optimal

4. **Visualiser graphiquement**
   - Radar : Voir dossier le plus équilibré
   - Barres performance : Identifier valeurs aberrantes

5. **Matrice décision**
   - Podium révèle : XYZ Corp 1er (85/100)
   - Lire recommandations XYZ Corp
   - **Décision** : Acquérir XYZ Corp

### Scénario 2 : Benchmark Sectoriel

**Contexte** : Analyser 8 PME du même secteur (services B2B)

**Workflow** :

1. **Filtrer par entreprise**
   - Sélectionner les 8 PME du secteur
   - Tag commun : `services_b2b`

2. **Comparer métriques sectorielles**
   - DSCR moyen du secteur : 1.15
   - Leverage moyen : 3.5x
   - Marge moyenne : 13.2%

3. **Identifier outliers**
   - Graphique barres : 2 dossiers sous seuil DSCR
   - Radar : 1 dossier déséquilibré (forte dette, faible marge)

4. **Recommandations benchmark**
   - Dossiers conformes : 6/8
   - Dossiers à écarter : 2/8
   - Benchmark sectoriel documenté pour futurs deals

### Scénario 3 : Portefeuille LBO

**Contexte** : Gérer portefeuille de 12 acquisitions sur 3 ans

**Workflow** :

1. **Vue d'ensemble annuelle**
   - Filtrer par année : `2024`, `2025`, `2026`
   - Comparer performance par millésime

2. **Analyse évolution**
   - Scores moyens : 2024 (82), 2025 (78), 2026 (85)
   - Tendance amélioration 2026

3. **Identifier deals problématiques**
   - Matrice décision : 3 dossiers avec deal breakers
   - Actions correctives à prévoir

4. **Reporting investisseurs**
   - Exporter comparaison CSV
   - Générer rapport comparatif PDF (future)

---

## 📊 Exemples Visuels (Conceptuel)

### Sélecteur Dossiers

```
┌────────────────────────────────────────────────────┐
│ 📂 Sélection Dossiers                              │
├────────────────────────────────────────────────────┤
│                                                    │
│  Statuts: [🟢 Validé ▼]                            │
│  Entreprises: [ACME SARL, XYZ Corp, ABC SARL ▼]    │
│                                                    │
│  **5 dossier(s) disponible(s)**                    │
│                                                    │
│  ACME SARL              🟡 WATCH (75/100)  DSCR: 0.83  [✓]│
│  Montage Base                                      │
│                                                    │
│  XYZ Corp               🟢 GO (85/100)     DSCR: 1.35  [✓]│
│  Montage Optimisé                                  │
│                                                    │
│  📊 2 dossier(s) sélectionné(s)                    │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Tableau Métriques Comparatif

```
┌──────────────────────────────────────────────────────────────────────┐
│ 📊 Comparaison Métriques Clés                                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Entreprise │ Variante  │ Décision │ DSCR │ Dette/EB │ Marge │ Equity│
│────────────┼───────────┼──────────┼──────┼──────────┼───────┼───────│
│ ACME SARL  │ Base      │ WATCH    │ 0.83 │ 3.30x    │ 12.4% │ 30.0% │
│ XYZ Corp   │ Optimisé  │ GO       │ 1.35 │ 2.80x    │ 15.2% │ 40.0% │
│ ABC SARL   │ Variante 2│ GO       │ 1.28 │ 3.10x    │ 14.1% │ 35.0% │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  DSCR Moyen: 1.15    Leverage Moyen: 3.07x    Score Moyen: 79/100   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Graphique Radar (Conceptuel)

```
         DSCR
          ╱ ╲
         ╱   ╲
  Score ●─────● Marge
         ╲   ╱
          ╲ ╱
      Conv. FCF

Legend:
─── ACME SARL (rouge)
─── XYZ Corp (vert)
─── ABC SARL (bleu)
```

### Podium

```
┌────────────────────────────────────────────────────┐
│ 🎯 Matrice de Décision                             │
├────────────────────────────────────────────────────┤
│                                                    │
│  🥇 1er: XYZ Corp           🥈 2ème: ABC SARL       🥉 3ème: ACME SARL│
│     Score: 85/100              Score: 78/100          Score: 75/100 │
│                                                    │
├────────────────────────────────────────────────────┤
│ 📋 Analyse Détaillée                               │
│                                                    │
│  #1 - 🟢 XYZ Corp - Montage Optimisé (85/100)     │
│  ▼  Métriques: DSCR 1.35, Dette/EB 2.8x           │
│     💡 Recommandations:                            │
│     • Covenant trimestriel recommandé              │
│     • Opportunité d'amélioration marge +1pt        │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 🔧 Intégration dans l'App

### Option A : Page Dédiée (Recommandé)

Créer page Streamlit autonome :

```python
# src/ui/pages/6_multi_deal.py

import streamlit as st
from src.ui.multi_deal_dashboard import render_multi_deal_dashboard

st.set_page_config(
    page_title="Comparaison Multi-Dossiers",
    page_icon="🏆",
    layout="wide"
)

render_multi_deal_dashboard()
```

**Avantages** :
- Dashboard full-width optimal
- Navigation claire (sidebar)
- Pas de collision avec autres tabs

### Option B : Ajouter à Tab 4

Intégrer dans Tab 4 existant :

```python
# Dans app_v3.py - Tab 4

from src.ui.multi_deal_dashboard import render_multi_deal_dashboard

with tab4:
    st.markdown("---")
    st.subheader("🏆 Comparaison Multi-Dossiers")

    if st.button("📊 Ouvrir Dashboard Comparatif"):
        st.session_state.show_multi_deal = True

    if st.session_state.get('show_multi_deal'):
        render_multi_deal_dashboard()
```

### Option C : Menu Principal

Ajouter lien dans sidebar :

```python
# Dans app_v3.py

with st.sidebar:
    st.markdown("---")
    if st.button("🏆 Dashboard Multi-Dossiers", use_container_width=True):
        # Redirection vers page dédiée
        st.switch_page("pages/6_multi_deal.py")
```

---

## 📈 Métriques Comparées

### Métriques Principales

| Métrique | Description | Seuil Optimal |
|----------|-------------|---------------|
| **DSCR** | Capacité remboursement dette | > 1.25 (🟢 GO) |
| **Dette/EBITDA** | Niveau endettement | < 4.0x (🟢 GO) |
| **Marge EBITDA** | Rentabilité opérationnelle | > 12% (🟢 GO) |
| **Equity %** | Capitaux propres | > 30% (🟢 GO) |
| **FCF Y3** | Cash flow libre année 3 | > 0€ (🟢 GO) |
| **Score Global** | Viabilité globale | > 80 (🟢 GO) |

### Métriques Agrégées

- **Moyenne** : Indicateur tendance centrale
- **Maximum** : Identifier meilleur performer
- **Minimum** : Détecter outliers négatifs
- **Écart-type** (future) : Mesurer dispersion

---

## ✅ Tests Validation

### Tests Manuels Recommandés

```bash
# Tester le dashboard
streamlit run src/ui/pages/6_multi_deal.py

# Workflow test:
# 1. Créer 3-5 variantes différentes (Phase 3.7)
# 2. Marquer 2-3 comme "Validé"
# 3. Ouvrir dashboard multi-dossiers
# 4. Filtrer par statut "Validé"
# 5. Sélectionner 3 dossiers
# 6. Vérifier tableau comparatif
# 7. Vérifier graphiques (radar, barres)
# 8. Vérifier podium et matrice décision
```

### Cas de Test

**Données minimales** :
- Au moins 2 variantes sauvegardées
- Au moins 1 variante avec statut "Validé"
- Métriques complètes dans chaque variante

**Résultat attendu** :
- Tableau affiche correctement toutes les métriques
- Graphiques se génèrent sans erreur
- Podium trie par score décroissant
- Filtres fonctionnent correctement

---

## 🚀 Roadmap Future (Phase 3.9)

Améliorations envisagées :

- [ ] **Export CSV** : Télécharger tableau comparatif
- [ ] **Rapport PDF Comparatif** : Générer rapport multi-dossiers
- [ ] **Filtres avancés** : Par secteur, par taille CA, par région
- [ ] **Tri colonnes** : Cliquer en-tête pour trier tableau
- [ ] **Graphiques supplémentaires** :
  - Scatter plot DSCR vs Leverage
  - Timeline évolution scores
  - Heatmap risques
- [ ] **Scoring pondéré personnalisé** : Ajuster poids métriques
- [ ] **Alertes automatiques** : Notification dossier sous-performant
- [ ] **Benchmarks sectoriels** : Comparer vs moyennes secteur

---

## 📚 Documentation API

### Fonctions Principales

```python
def render_multi_deal_selector() -> List[str]:
    """Sélectionner dossiers à comparer. Returns: IDs variantes."""

def render_metrics_comparison(variant_ids: List[str]) -> None:
    """Afficher tableau comparatif métriques."""

def render_visual_comparison(variant_ids: List[str]) -> None:
    """Afficher graphiques comparatifs (3 onglets)."""

def render_decision_matrix(variant_ids: List[str]) -> None:
    """Afficher podium + matrice décision détaillée."""

def render_multi_deal_dashboard() -> None:
    """Dashboard complet (orchestration toutes fonctions)."""
```

### Fonctions Utilitaires

```python
def create_radar_chart(variants: List, labels: List[str]) -> go.Figure:
    """Créer graphique radar métriques normalisées."""

def create_financing_structure_chart(variants: List, labels: List[str]) -> go.Figure:
    """Créer graphique barres empilées financement."""

def create_performance_bars(variants: List, labels: List[str]) -> go.Figure:
    """Créer graphique barres performance avec seuils."""
```

---

## 💡 Best Practices

### Sélection Dossiers

**Recommandations** :
- **2-5 dossiers** : Optimal pour comparaison lisible
- **6-10 dossiers** : Acceptable, graphiques chargés
- **> 10 dossiers** : Éviter, surcharge visuelle

### Filtres Statuts

- **Validé** : Comparer dossiers finalisés
- **Brouillon** : Comparer variantes en cours (même dossier)
- **Rejeté** : Analyser pourquoi rejetés (retour expérience)

### Interprétation Podium

- **Top 3** : Dossiers à présenter investisseurs
- **Reste** : Dossiers à améliorer ou écarter
- **Analyser écarts** : Si écart top 1 vs top 2 < 5 pts → départage difficile

---

## 🎓 Conclusion

### Avant Phase 3.8
❌ Comparaison manuelle laborieuse
❌ Pas de vue d'ensemble portfolio
❌ Sélection basée sur intuition

### Après Phase 3.8
✅ Comparaison visuelle immédiate (2-10 dossiers)
✅ Métriques agrégées automatiques
✅ Podium objectif basé sur scoring
✅ Graphiques radar + barres
✅ Matrice décision avec recommandations
✅ Filtres puissants (statut, entreprise)

---

**Version**: 3.8
**Statut**: ✅ **Module créé et prêt**
**Prochaine étape**: Phase 3.9 - Upload PDF réel avec OCR

🎉 **Dashboard de comparaison multi-dossiers prêt à être déployé !**
