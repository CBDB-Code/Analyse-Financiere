# 💰 Analyse Financière - Application d'Acquisition d'Entreprises

Application web locale en Python pour analyser la viabilité financière d'entreprises à racheter, à partir de leurs liasses fiscales françaises (PDF).

## 🎯 Objectif

Calculer **60+ métriques financières** de manière **déterministe** et **robuste** pour :
- **Banquiers** : DSCR, ratios de couverture, stress tests
- **Entrepreneurs** : ROE, TRI, création de valeur, payback

## ✨ Fonctionnalités (MVP Phase 1)

- ✅ **10 métriques essentielles** calculées automatiquement
- ✅ **Scénarios interactifs** avec sliders (dette, equity, croissance)
- ✅ **Double perspective** : Banquier vs Entrepreneur
- ✅ **Base de données SQLite** pour historique
- ✅ **Interface Streamlit** intuitive
- ✅ **Architecture extensible** pour ajouter facilement de nouvelles métriques

## 📊 Métriques Implémentées

### Perspective Banquier (2)
- **DSCR** (Debt Service Coverage Ratio) - Capacité de remboursement
- **ICR** (Interest Coverage Ratio) - Couverture des intérêts

### Perspective Entrepreneur (2)
- **ROE** (Return on Equity) - Rentabilité des capitaux propres
- **Payback Period** - Délai de récupération de l'investissement

### Liquidité (2)
- **Fonds de Roulement (FR)** - Équilibre financier
- **BFR** (Besoin en Fonds de Roulement) - Besoin de financement cyclique

### Rentabilité (4)
- **EBITDA** - Résultat avant intérêts, impôts et amortissements
- **Marge Brute** - Profitabilité sur achats
- **Marge d'Exploitation** - Rentabilité opérationnelle
- **Marge Nette** - Rentabilité finale

## 🚀 Installation

### Prérequis
- Python 3.11+
- pip ou uv

### Étapes

1. **Cloner le projet** (ou télécharger le dossier)

2. **Créer un environnement virtuel** :
```bash
python -m venv venv
source venv/bin/activate  # Sur macOS/Linux
# OU
venv\Scripts\activate  # Sur Windows
```

3. **Installer les dépendances** :
```bash
pip install -e .
# OU avec les dépendances de développement :
pip install -e ".[dev]"
```

4. **Initialiser la base de données** :
```bash
python scripts/init_db.py
```

## 🎮 Utilisation

### Lancer l'application

```bash
streamlit run src/ui/app.py
```

L'application s'ouvre automatiquement dans votre navigateur à `http://localhost:8501`

### Workflow

1. **Charger des données de test** : Cliquez sur "Charger exemple de données"
2. **Configurer le scénario** : Ajustez les sliders (dette, equity, croissance)
3. **Choisir la perspective** : Banquier, Entrepreneur ou Complète (sidebar)
4. **Calculer** : Cliquez sur "Calculer les métriques"
5. **Analyser** : Consultez les résultats avec interprétations automatiques

## 📁 Structure du Projet

```
Analyse Financiere/
├── src/
│   ├── core/
│   │   └── models.py              # Modèles Pydantic (liasses fiscales)
│   ├── calculations/
│   │   ├── base.py                # Système de Registry
│   │   ├── banker/                # Métriques banquier
│   │   ├── entrepreneur/          # Métriques entrepreneur
│   │   └── standard/              # Métriques standard (liquidité, rentabilité)
│   ├── scenarios/
│   │   ├── parameters.py          # Paramètres de scénarios
│   │   └── engine.py              # Moteur de simulation
│   ├── database/
│   │   └── models.py              # Modèles SQLAlchemy
│   └── ui/
│       └── app.py                 # Application Streamlit
├── data/
│   ├── raw/                       # PDFs uploadés (future)
│   ├── processed/                 # JSON extraits (future)
│   └── database/
│       └── financials.db          # Base SQLite
├── scripts/
│   └── init_db.py                 # Initialisation BDD
├── tests/                         # Tests unitaires (à venir)
├── pyproject.toml                 # Configuration du projet
└── README.md
```

## 🏗️ Architecture

### Pattern Registry

Toutes les métriques s'auto-enregistrent dans un registre central :

```python
from src.calculations.base import FinancialMetric, MetricMetadata, register_metric

@register_metric
class MaMetrique(FinancialMetric):
    metadata = MetricMetadata(
        name="ma_metrique",
        formula_latex=r"\frac{A}{B}",
        category=MetricCategory.PROFITABILITY,
        # ...
    )

    def calculate(self, financial_data: dict) -> float:
        return financial_data["A"] / financial_data["B"]
```

**Avantages** :
- Aucune modification de code existant pour ajouter une métrique
- Documentation automatique
- Tests unitaires centralisés

### Déterminisme

- **Zéro IA** pour les calculs financiers
- Formules mathématiques pures (Python)
- Reproductible à 100%
- Auditable

### Token-économe

- IA utilisée uniquement pour extraction PDF (Phase 2)
- Tous les calculs gratuits (Python pur)
- Coût estimé : ~$0.10-0.50 par entreprise

## 🧪 Tests (À venir en Phase 2)

```bash
pytest
pytest --cov=src --cov-report=html
```

## 📚 Phases de Développement

### ✅ Phase 1 : MVP (ACTUELLE)
- Structure projet complète
- 10 métriques essentielles
- Scénarios interactifs
- Interface Streamlit basique

### 🔄 Phase 2 : Core Features (Prochaine)
- [ ] Extraction PDF automatique (pdfplumber + Claude API)
- [ ] 60+ métriques complètes
- [ ] Dashboards avancés (Plotly)
- [ ] Comparaison multi-scénarios
- [ ] Stress tests automatiques

### 📅 Phase 3 : Advanced
- [ ] Multi-exercices (tendances 3-5 ans)
- [ ] Comparaison multi-entreprises
- [ ] Export PDF professionnel
- [ ] Tests complets (>80% coverage)

## 🎓 Métriques Détaillées

### DSCR (Debt Service Coverage Ratio)

**Formule** : `EBITDA / Service annuel de la dette`

**Interprétation** :
- **> 1.5** : Excellente couverture
- **1.25 - 1.5** : Bonne couverture
- **1.0 - 1.25** : Acceptable
- **< 1.0** : Risque de défaut

**Utilité** : Mesure la capacité d'une entreprise à rembourser sa dette avec son cash-flow opérationnel.

### ROE (Return on Equity)

**Formule** : `(Résultat net / Capitaux propres) × 100`

**Interprétation** :
- **> 20%** : Excellente rentabilité
- **15% - 20%** : Bonne rentabilité
- **10% - 15%** : Acceptable
- **< 10%** : Faible

**Utilité** : Mesure le retour sur investissement pour les actionnaires.

### Fonds de Roulement (FR)

**Formule** : `(Capitaux propres + Dettes LT) - Immobilisations`

**Interprétation** :
- **FR > 0** : Équilibre financier sain
- **FR < 0** : Risque de liquidité

**Utilité** : Indique si l'entreprise finance ses immobilisations avec des ressources stables.

### BFR (Besoin en Fonds de Roulement)

**Formule** : `(Stocks + Créances) - (Fournisseurs + Dettes fiscales/sociales)`

**Interprétation** :
- **BFR positif** : Besoin de financement du cycle d'exploitation
- **BFR négatif** : Ressource (clients paient avant de payer les fournisseurs)

**Utilité** : Mesure le besoin de financement du cycle d'exploitation.

## 💡 Scénarios Prédéfinis

L'application propose 4 scénarios types :

| Scénario | Dette/Equity | LTV | Croissance CA | Taux |
|----------|--------------|-----|---------------|------|
| **Conservateur** | 0.25 | 20% | 2% | 4% |
| **Équilibré** | 1.00 | 50% | 5% | 5% |
| **Avec levier** | 2.33 | 70% | 8% | 6% |
| **Agressif** | 5.67 | 85% | 12% | 7% |

## 🤝 Contribution

Pour ajouter une nouvelle métrique :

1. Créer une classe dans `src/calculations/[categorie]/`
2. Hériter de `FinancialMetric`
3. Utiliser le décorateur `@register_metric`
4. Définir les `metadata`
5. Implémenter `calculate()`

Exemple complet dans `src/calculations/standard/profitability.py`

## 📝 License

Privé - Usage interne uniquement

## 👨‍💻 Auteur

Christophe Berly

---

**Note** : Cette application est en développement actif. Les fonctionnalités d'extraction PDF et les 50+ métriques supplémentaires seront ajoutées en Phase 2.
