# 🚀 Quick Start - Phase 3 (v3.0)

**Analyse Financière LBO** - Application professionnelle pour acquisitions PME 2-20M€

---

## ⚡ Démarrage Rapide (5 minutes)

### 1. Installation

```bash
cd "Analyse Financiere"
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# OU
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. Lancement Application v3

```bash
streamlit run src/ui/app_v3.py
```

L'application s'ouvre automatiquement dans votre navigateur à `http://localhost:8501`

---

## 📊 Workflow Standard (Premier Lancement)

### Étape 1: Onglet 1 - Données

1. Cliquez sur **"📥 Charger Données de Test"**
   - Charge automatiquement les données de ACME SARL (CA 8.5M€)

2. Vérifiez le **Data Quality Center**
   - ✅ Bilan équilibré
   - ✅ Résultat cohérent
   - ✅ CA dans cible 2-20M€
   - ✅ EBE positif

3. **Normalisation Comptable**
   - EBE initial affiché : **850 000 €**
   - Cliquez sur **"💡 Suggestions Automatiques"**
   - Cliquez **"➕ Ajouter"** pour "Rémunération dirigeant excessive"
   - OU ajoutez manuellement:
     ```
     Nom: Loyers crédit-bail
     Montant: 150 000 €
     Catégorie: Rent
     ```

4. Visualisez le **Waterfall Chart**
   - EBE → + Retraitements → EBITDA banque

5. Configurez **EBITDA Equity**
   - Taux IS: **25%**
   - Capex maintenance: **250 000 €**
   - → EBITDA equity calculé automatiquement

6. Cliquez **"✅ Valider les Données Normalisées"**

### Étape 2: Onglet 2 - Montage LBO

1. Configurez les **Sliders de Financement** (colonne gauche):
   ```
   Prix d'acquisition: 5 000 000 €
   Dette senior: 60% (3M€) à 4.5% sur 7 ans
   ☑ Bpifrance: 10% (500k€) à 3.0%
   ☑ Crédit vendeur: 15% (750k€)
   Equity: 1 750 000 € (auto-calculé)
   Part entrepreneur: 70%
   ```

2. Visualisez en temps réel (colonne centre):
   - **Donut chart** : Structure de financement
   - **Ratios** : Levier, Dette/Equity, Multiple acquisition

3. Analysez les **KPIs Décisifs** (colonne droite):
   - 🟢 DSCR (approx): **1.82**
   - 🟢 Dette/EBITDA: **4.0x**
   - 🟡 Marge EBITDA: **12.4%**
   - **Décision Préliminaire**: 🟡 **WATCH** (Score 75/100)

4. Ajustez les sliders pour améliorer le score:
   - Réduisez dette senior à **55%** → DSCR monte à **2.0**
   - Décision passe à 🟢 **GO**

5. Cliquez **"✅ Valider Montage"**

### Étape 3: Onglet 3 - Viabilité

🚧 **En développement**

Fonctionnalités prévues:
- Stress tests automatiques
- Covenant tracking
- Décision finale GO/WATCH/NO-GO

### Étape 4: Onglet 4 - Synthèse

🚧 **En développement**

Fonctionnalités prévues:
- Export PDF professionnel
- Rapport banquier/investisseur

---

## 🎯 Cas d'Usage Réel

### Analyser une Acquisition de 5M€

**Contexte**: PME services B2B, CA 8.5M€, EBITDA 12%

#### 1. Import Données (Tab 1)
- Upload liasse fiscale PDF OU données de test
- **Résultat**: EBE = 850k€

#### 2. Normalisation (Tab 1)
- Ajout retraitement loyers: +150k€
- Ajout retraitement rémunération: +80k€
- **Résultat**: EBITDA banque = **1 080k€** (12.7% marge)

#### 3. Montage LBO (Tab 2)
- Prix: 5M€ (4.6x EBITDA)
- Dette senior: 3M€ (60%) à 4.5% / 7 ans
- Bpifrance: 500k€ (10%) à 3.0% / 8 ans
- Crédit vendeur: 750k€ (15%) différé 2 ans
- Equity: 750k€ (15%)
- **Résultat**: DSCR = 1.8, Dette/EBITDA = 3.9x → 🟢 **GO**

#### 4. Décision
- ✅ Levier acceptable (3.9x)
- ✅ DSCR confortable (1.8 > 1.25)
- ⚠️ Marge un peu faible (12.7% vs 15% objectif)
- **Recommandation**: GO sous condition amélioration marge

---

## 💡 Astuces

### Formatage des Nombres
Tous les montants sont affichés avec **espaces insécables** pour faciliter la lecture:
- ✅ **1 200 000 €** (facile à lire)
- ❌ 1200000 € (difficile)

### Navigation Séquentielle
Le workflow est conçu pour être suivi dans l'ordre:
1. Données → 2. Montage → 3. Viabilité → 4. Synthèse

Les boutons **"✅ Valider"** vous guident vers l'onglet suivant.

### Sliders Intelligents
- Ajustez les sliders pour voir l'**impact temps réel** sur les KPIs
- Les zones colorées indiquent:
  - 🟢 Vert: Zone saine
  - 🟡 Orange: Zone acceptable
  - 🔴 Rouge: Zone risquée

### Data Quality Center
Vérifications automatiques:
- Cohérence comptable (Actif = Passif)
- CA dans cible LBO (2-20M€)
- EBE positif
- BFR < 25% CA (point d'attention si dépassé)

---

## 🔧 Dépannage

### Erreur "Module not found"
```bash
pip install -r requirements.txt
```

### Port déjà utilisé
```bash
streamlit run src/ui/app_v3.py --server.port 8502
```

### Données ne se sauvegardent pas
Les données sont stockées en **session** uniquement (pas de BDD pour l'instant).
Rechargez les données de test ou re-uploadez votre liasse après rafraîchissement.

---

## 📚 Documentation Complète

- [README.md](README.md) : Documentation générale
- [PHASE_3_PLAN.md](PHASE_3_PLAN.md) : Plan détaillé Phase 3
- [docs/formulas.md](docs/formulas.md) : Formules financières

---

## 🆕 Nouveautés Phase 3

### Workflow Normalisation ⭐ KILLER FEATURE
- EBE → EBITDA banque → EBITDA equity
- Waterfall chart temps réel
- Suggestions automatiques de retraitements
- Traçabilité audit complète

### Formatage Milliers
- **1 200 000 €** au lieu de 1200000
- Lisibilité améliorée partout

### Structure LBO Interactive
- 3 tranches de dette (Senior, Bpifrance, Crédit vendeur)
- Equity auto-calculé
- Visualisation donut temps réel

### KPIs Décisifs
- DSCR (approx)
- Dette/EBITDA
- Marge EBITDA
- Décision préliminaire GO/WATCH/NO-GO

---

## ❓ Support

**Questions ?** Ouvre une [issue](https://github.com/cbdb-code/analyse-financiere/issues)

**Améliorations ?** Les contributions sont bienvenues !

---

**Version**: 3.0 (Janvier 2026)
**Auteur**: Christophe Berly
**Développé avec**: Claude Opus 4.5
