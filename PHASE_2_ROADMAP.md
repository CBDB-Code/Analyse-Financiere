# 🗺️ Roadmap Phase 2 - Fonctionnalités Complètes

**Objectif** : Transformer le MVP en application production-ready avec extraction PDF, 60+ métriques et visualisations avancées.

**Durée estimée** : 3-4 semaines
**Priorité** : Haute

---

## 📋 Vue d'Ensemble

### Ce qui existe (Phase 1)
✅ Architecture complète et extensible
✅ 10 métriques essentielles
✅ Scénarios interactifs
✅ Interface Streamlit basique
✅ Base SQLite

### Ce qui sera ajouté (Phase 2)
🔄 Extraction automatique PDF → JSON
🔄 50+ nouvelles métriques financières
🔄 Visualisations Plotly avancées
🔄 Dashboards spécialisés (Banquier/Entrepreneur)
🔄 Export PDF professionnel

---

## 🎯 Objectifs Phase 2

1. **Extraction PDF déterministe** avec fallback IA
2. **60+ métriques complètes** couvrant tous les cas d'usage
3. **Visualisations interactives** (graphiques, waterfall, sensibilité)
4. **Export PDF professionnel** pour présentations
5. **Tests unitaires** (>80% coverage)

---

## 📦 Tâches Détaillées

### 1. Module Extraction PDF (Priorité 1)

**Fichiers à créer** :
- `src/extraction/pdf_parser.py` : Extraction avec pdfplumber
- `src/extraction/form_recognizer.py` : Détection formulaires 2033/2050
- `src/extraction/validators.py` : Validation post-extraction
- `src/extraction/ai_extractor.py` : Fallback Claude API (optionnel)

**Fonctionnalités** :
- [ ] Détection type PDF (natif vs scanné)
- [ ] Extraction champs AcroForms (PyPDF2)
- [ ] Extraction tableaux (pdfplumber + camelot)
- [ ] Reconnaissance formulaires français (2033, 2050-2059)
- [ ] Validation checksums comptables (Actif = Passif)
- [ ] Mapping vers structure JSON standardisée
- [ ] Fallback OCR si nécessaire
- [ ] Interface upload dans Streamlit

**Tests** :
- [ ] Tester avec vraies liasses fiscales
- [ ] Valider précision extraction (>95%)
- [ ] Benchmark performance (temps par PDF)

---

### 2. Métriques Complètes (Priorité 1)

**50+ nouvelles métriques à implémenter** :

#### Métriques Banquier (+13)
- [ ] Gearing (Dette nette / Capitaux propres)
- [ ] Debt-to-Equity Ratio
- [ ] Net Debt / EBITDA
- [ ] Loan-to-Value (LTV)
- [ ] Capacité de remboursement (années)
- [ ] Taux de couverture du service de la dette
- [ ] Ratio de solvabilité
- [ ] Stress Test -10% CA (automatique)
- [ ] Stress Test -20% CA (automatique)
- [ ] Stress Test +100bps taux
- [ ] Break-even debt service
- [ ] Maximum sustainable debt
- [ ] Probability of default (score simplifié)

#### Métriques Entrepreneur (+10)
- [ ] TRI (Taux de Rendement Interne)
- [ ] Multiple de sortie (EV/EBITDA)
- [ ] Cash-on-Cash Return
- [ ] Equity Multiple
- [ ] Création de valeur (€)
- [ ] Dilution des parts
- [ ] Dividend Capacity
- [ ] Retour sur investissement cumulé
- [ ] VAN (Valeur Actuelle Nette)
- [ ] TRIM (TRI Modifié)

#### Métriques Liquidité (+6)
- [ ] Current Ratio
- [ ] Quick Ratio (Acid Test)
- [ ] Cash Ratio
- [ ] Working Capital Ratio
- [ ] Délai de rotation du BFR (jours)
- [ ] Trésorerie Nette

#### Métriques Rentabilité (+8)
- [ ] EBIT
- [ ] Marge EBITDA (%)
- [ ] ROA (Return on Assets)
- [ ] ROCE (Return on Capital Employed)
- [ ] Rentabilité économique
- [ ] Rentabilité financière
- [ ] Point mort opérationnel
- [ ] Levier opérationnel

#### Métriques Activité (+8)
- [ ] Rotation des stocks (jours)
- [ ] DSO (Days Sales Outstanding)
- [ ] DPO (Days Payable Outstanding)
- [ ] Cash Conversion Cycle
- [ ] Rotation de l'actif
- [ ] Rotation des immobilisations
- [ ] Productivité par employé
- [ ] CA par employé

#### Métriques Solvabilité (+8)
- [ ] Autonomie financière (%)
- [ ] Taux d'endettement global
- [ ] Capacité d'endettement résiduelle
- [ ] Coverage of fixed charges
- [ ] Debt-to-Assets Ratio
- [ ] Equity Ratio
- [ ] Financial Leverage
- [ ] Z-Score d'Altman (version française)

#### Métriques Tendances (+5)
- [ ] CAGR du CA (3 ans)
- [ ] CAGR de l'EBITDA (3 ans)
- [ ] Évolution du BFR
- [ ] Taux de croissance moyen
- [ ] Volatilité du CA

**Total : 58 nouvelles métriques + 10 existantes = 68 métriques**

**Fichiers à créer** :
- `src/calculations/banker/leverage.py`
- `src/calculations/banker/stress_tests.py`
- `src/calculations/entrepreneur/value_creation.py`
- `src/calculations/entrepreneur/multiples.py`
- `src/calculations/standard/activity.py`
- `src/calculations/standard/solvency.py`
- `src/calculations/trends/growth.py`

---

### 3. Visualisations Avancées (Priorité 2)

**Fichiers à créer** :
- `src/visualization/charts.py` : Factory de graphiques
- `src/visualization/dashboards.py` : Layouts complets
- `src/visualization/themes.py` : Styles graphiques

**Graphiques à implémenter** :
- [ ] **Waterfall chart** : Décomposition DSCR, ROE
- [ ] **Barres groupées** : Comparaison multi-scénarios
- [ ] **Lignes** : Évolution tendances multi-années
- [ ] **Radar chart** : Vue 360° métriques
- [ ] **Heatmap** : Analyse de sensibilité
- [ ] **Gauge charts** : KPIs avec seuils
- [ ] **Sankey diagram** : Flux financiers

**Intégration Streamlit** :
- [ ] Onglets par perspective
- [ ] Graphiques interactifs (zoom, hover)
- [ ] Téléchargement graphiques (PNG, SVG)

---

### 4. Dashboards Spécialisés (Priorité 2)

**Fichier à créer** :
- `src/visualization/dashboards.py`

#### BankerDashboard
- [ ] Section "Vue d'ensemble" : DSCR, ICR, Gearing, Dette/EBITDA
- [ ] Section "Couverture de la dette" : Waterfall DSCR
- [ ] Section "Stress tests" : -10%, -20% CA, +100bps taux
- [ ] Section "Ratios détaillés" : Tableau complet avec interprétations
- [ ] Section "Historique" : Évolution sur 3-5 ans si disponible

#### EntrepreneurDashboard
- [ ] Section "Rentabilité" : ROE, TRI, Multiple
- [ ] Section "Création de valeur" : Graph évolution valeur
- [ ] Section "Retour sur investissement" : Payback, VAN, TRIM
- [ ] Section "Scénarios de sortie" : Multiples selon hypothèses
- [ ] Section "Comparaison" : vs. autres placements

---

### 5. Export PDF Professionnel (Priorité 3)

**Fichiers à créer** :
- `src/reporting/generator.py` : Générateur PDF
- `src/reporting/formatters.py` : Formatage données
- `src/reporting/templates/banker_report.html` : Template Jinja2
- `src/reporting/templates/entrepreneur_report.html` : Template Jinja2

**Contenu du rapport** :
- [ ] Page de garde (logo, entreprise, date)
- [ ] Synthèse exécutive (1 page)
- [ ] Dashboard perspective choisie
- [ ] Graphiques embarqués (base64)
- [ ] Tableaux détaillés
- [ ] Annexes (méthodologie, benchmarks)

**Technologie** :
- Jinja2 pour templates HTML
- WeasyPrint pour conversion HTML → PDF
- Matplotlib/Plotly pour graphiques statiques

---

### 6. Tests Unitaires (Priorité 3)

**Fichiers à créer** :
- `tests/test_calculations/test_banker_metrics.py`
- `tests/test_calculations/test_entrepreneur_metrics.py`
- `tests/test_calculations/test_standard_metrics.py`
- `tests/test_calculations/test_determinism.py`
- `tests/test_scenarios/test_engine.py`
- `tests/test_extraction/test_pdf_parser.py`
- `tests/fixtures/sample_data.py`

**Tests à écrire** :
- [ ] Test chaque formule avec valeurs connues
- [ ] Test déterminisme (même input = même output)
- [ ] Test cas edge (division par 0, valeurs négatives)
- [ ] Test validation des données
- [ ] Test moteur de scénarios
- [ ] Test extraction PDF (avec PDFs réels)

**Objectif** : >80% code coverage

---

### 7. Multi-exercices & Tendances (Priorité 3)

**Fichiers à créer** :
- `src/calculations/trends/analyzer.py`

**Fonctionnalités** :
- [ ] Import de plusieurs exercices pour une même entreprise
- [ ] Calcul CAGR automatique (CA, EBITDA, etc.)
- [ ] Détection de tendances (croissance, décroissance)
- [ ] Volatilité des métriques
- [ ] Prédictions simples (régression linéaire)
- [ ] Graphiques d'évolution temporelle

---

## 🗓️ Planning Phase 2

### Semaine 1 : Extraction PDF + Métriques Banquier
- Jours 1-2 : Module extraction PDF complet
- Jours 3-5 : 13 nouvelles métriques Banquier

### Semaine 2 : Métriques Entrepreneur + Standard
- Jours 1-3 : 10 métriques Entrepreneur
- Jours 4-5 : Métriques Activité + Solvabilité (16 métriques)

### Semaine 3 : Visualisations + Dashboards
- Jours 1-2 : Factory de graphiques Plotly
- Jours 3-4 : BankerDashboard + EntrepreneurDashboard
- Jour 5 : Intégration Streamlit

### Semaine 4 : Export PDF + Tests
- Jours 1-2 : Générateur de rapports PDF
- Jours 3-5 : Tests unitaires complets

---

## 📊 Métriques de Succès Phase 2

| Critère | Objectif | Mesure |
|---------|----------|--------|
| Métriques | 60+ | Count du Registry |
| Extraction PDF | >95% précision | Tests sur vraies liasses |
| Visualisations | 7+ types | Plotly charts |
| Coverage tests | >80% | pytest-cov |
| Documentation | Complète | Toutes formules documentées |
| Performance | <1s par métrique | Benchmark |

---

## 💰 Coût Estimé Phase 2

**Développement** :
- Temps développeur : 3-4 semaines
- IA (Claude Opus 4.5) : Gratuit (même utilisation que Phase 1)

**Utilisation** :
- Extraction PDF (Claude API) : $0.10-0.50 par liasse (optionnel)
- Calculs : $0 (Python pur)
- Export PDF : $0 (local)

**Total** : Quasi-gratuit en utilisation

---

## 🚀 Démarrage Phase 2

### Prérequis
1. Phase 1 testée et validée
2. Accès à des liasses fiscales réelles pour tests
3. Environnement virtuel configuré

### Première tâche
```bash
# Créer la branche Phase 2
cd "Analyse Financiere"
git init
git checkout -b phase-2

# Commencer par l'extraction PDF
# (fichier le plus critique)
touch src/extraction/pdf_parser.py
```

### Commande pour générer les métriques manquantes
```python
# Utiliser un agent IA (Opus 4.5) pour générer automatiquement
# les 50+ métriques en batch avec le pattern établi
```

---

## 📚 Ressources

### Documentation de référence
- Liasses fiscales DGFiP : https://www.impots.gouv.fr/formulaire/2050-liasse
- Ratios financiers standard : https://www.banque-france.fr/
- Extraction PDF Python : https://github.com/jsvine/pdfplumber

### Bibliothèques à maîtriser
- pdfplumber : Extraction PDF
- camelot-py : Tableaux PDF
- plotly : Visualisations
- weasyprint : Export PDF
- pytest : Tests

---

## ✅ Checklist Phase 2

### Extraction PDF
- [ ] pdfplumber configuré
- [ ] Reconnaissance formulaires 2033/2050
- [ ] Mapping JSON complet
- [ ] Validation checksums
- [ ] Interface upload Streamlit
- [ ] Tests avec vraies liasses

### Métriques
- [ ] 58 nouvelles métriques implémentées
- [ ] Toutes enregistrées dans Registry
- [ ] Documentation formulas.md mise à jour
- [ ] Tests unitaires pour chaque métrique

### Visualisations
- [ ] 7+ types de graphiques Plotly
- [ ] Dashboards Banquier/Entrepreneur
- [ ] Intégration Streamlit multi-onglets
- [ ] Export graphiques PNG/SVG

### Export PDF
- [ ] Templates Jinja2 créés
- [ ] WeasyPrint configuré
- [ ] Graphiques embarqués
- [ ] Style professionnel

### Tests
- [ ] >80% coverage
- [ ] Tests déterminisme
- [ ] Tests cas edge
- [ ] CI/CD optionnel

---

**Prêt pour Phase 2 ?** 🚀

Commence par tester la Phase 1 avec de vraies données, puis lance-toi dans l'extraction PDF !
