# 📐 Documentation des Formules Financières

Cette documentation liste toutes les métriques financières implémentées avec leurs formules, interprétations et benchmarks.

## Table des Matières

- [Métriques Banquier](#métriques-banquier)
- [Métriques Entrepreneur](#métriques-entrepreneur)
- [Métriques de Liquidité](#métriques-de-liquidité)
- [Métriques de Rentabilité](#métriques-de-rentabilité)

---

## Métriques Banquier

### DSCR (Debt Service Coverage Ratio)

**Catégorie** : Banquier
**Unité** : Ratio

**Formule** :
```
DSCR = EBITDA / Service annuel de la dette
```

**Formule LaTeX** :
```latex
\frac{EBITDA}{Service\ annuel\ de\ la\ dette}
```

**Calcul détaillé** :
```python
EBITDA = Résultat d'exploitation + Dotations aux amortissements
Service de dette = Capital remboursé + Intérêts annuels
DSCR = EBITDA / Service de dette
```

**Champs sources** :
- `income_statement.operating_income.value`
- `income_statement.operating_expenses.depreciation.value`
- `scenario.annual_debt_service`

**Interprétation** :
- **> 1.5** : Excellente couverture - L'entreprise génère 50%+ de cash excédentaire
- **1.25 - 1.5** : Bonne couverture - Marge de sécurité confortable
- **1.0 - 1.25** : Acceptable - Couverture juste suffisante
- **< 1.0** : Risque de défaut - L'entreprise ne peut pas rembourser sa dette

**Benchmarks** :
```python
{
    "excellent": 1.5,
    "good": 1.25,
    "acceptable": 1.0,
    "risky": 0.8
}
```

**Utilité pour le banquier** :
Le DSCR est la métrique #1 pour évaluer la capacité de remboursement. Un DSCR < 1.0 signifie que l'entreprise ne génère pas assez de cash pour rembourser sa dette → refus de crédit quasi-systématique.

---

### ICR (Interest Coverage Ratio)

**Catégorie** : Banquier
**Unité** : Ratio (fois)

**Formule** :
```
ICR = EBIT / Charges financières
```

**Formule LaTeX** :
```latex
\frac{EBIT}{Charges\ financières}
```

**Calcul détaillé** :
```python
EBIT = Résultat d'exploitation (avant intérêts et impôts)
Charges financières = Intérêts débiteurs
ICR = EBIT / Charges financières
```

**Champs sources** :
- `income_statement.operating_income.value`
- `income_statement.financial_result.interest_expense.value`

**Interprétation** :
- **> 5** : Excellente - L'entreprise peut payer ses intérêts 5x
- **3 - 5** : Bonne - Marge de sécurité confortable
- **1.5 - 3** : Acceptable - Situation correcte mais sensible
- **< 1.5** : Risque - Difficulté à couvrir les intérêts

**Benchmarks** :
```python
{
    "excellent": 5.0,
    "good": 3.0,
    "acceptable": 1.5,
    "risky": 1.0
}
```

**Utilité pour le banquier** :
L'ICR mesure la capacité à payer uniquement les intérêts (sans le capital). Un ICR < 1.0 signifie que l'entreprise perd de l'argent sur son exploitation → insoutenable.

---

## Métriques Entrepreneur

### ROE (Return on Equity)

**Catégorie** : Entrepreneur
**Unité** : %

**Formule** :
```
ROE = (Résultat net / Capitaux propres) × 100
```

**Formule LaTeX** :
```latex
\frac{Résultat\ net}{Capitaux\ propres} \times 100
```

**Calcul détaillé** :
```python
Résultat net = Bénéfice après impôts
Capitaux propres = Equity total (capital + réserves + résultat)
ROE = (Résultat net / Capitaux propres) × 100
```

**Champs sources** :
- `income_statement.net_income.value`
- `balance_sheet.liabilities.equity.total.value`

**Interprétation** :
- **> 20%** : Excellente rentabilité - Très performant
- **15% - 20%** : Bonne rentabilité - Au-dessus de la moyenne
- **10% - 15%** : Acceptable - Rentabilité correcte
- **< 10%** : Faible - Sous-performance

**Benchmarks** :
```python
{
    "excellent": 20.0,
    "good": 15.0,
    "acceptable": 10.0,
    "risky": 5.0
}
```

**Utilité pour l'entrepreneur** :
Le ROE est LA métrique clé pour un acquéreur. Elle indique le rendement annuel sur les capitaux propres investis. Un ROE de 15% signifie : "Chaque euro investi rapporte 15 centimes par an".

**Comparaison** :
- Livret A : ~3% sans risque
- Actions CAC 40 : ~8% moyen historique
- Private Equity : 15-25% cible

---

### Payback Period

**Catégorie** : Entrepreneur
**Unité** : Années

**Formule** :
```
Payback = Investissement initial / Cash-flow annuel moyen
```

**Formule LaTeX** :
```latex
\frac{Investissement\ initial}{Cash\ flow\ annuel\ moyen}
```

**Calcul détaillé (simplifié MVP)** :
```python
Investissement = Montant des capitaux propres apportés
Cash-flow annuel = EBITDA (simplifié)
Payback = Investissement / Cash-flow
```

**Champs sources** :
- `scenario.equity_amount`
- `income_statement.operating_income.value`
- `income_statement.operating_expenses.depreciation.value`

**Interprétation** :
- **< 3 ans** : Excellent - Récupération très rapide
- **3 - 5 ans** : Bon - Récupération rapide
- **5 - 7 ans** : Acceptable - Récupération standard
- **> 10 ans** : Risqué - Trop long

**Benchmarks** :
```python
{
    "excellent": 3.0,
    "good": 5.0,
    "acceptable": 7.0,
    "risky": 10.0
}
```

**Utilité pour l'entrepreneur** :
Le Payback indique en combien d'années vous récupérez votre mise initiale. Plus c'est court, moins le risque est élevé.

**Note** : Dans les phases suivantes, le calcul sera affiné avec :
- Cash-flow réel (EBITDA - CapEx - Δ BFR - Impôts)
- Valeur actualisée (TVM)
- Scénarios de croissance

---

## Métriques de Liquidité

### Fonds de Roulement (FR)

**Catégorie** : Liquidité
**Unité** : €

**Formule** :
```
FR = Capitaux permanents - Actif immobilisé
```

**Formule détaillée** :
```
FR = (Capitaux propres + Dettes long terme) - Immobilisations totales
```

**Formule LaTeX** :
```latex
(Capitaux\ propres + Dettes\ LT) - Actif\ immobilisé
```

**Calcul détaillé** :
```python
Capitaux permanents = Equity + Dettes > 1 an
Actif immobilisé = Immobilisations incorporelles + corporelles + financières
FR = Capitaux permanents - Actif immobilisé
```

**Champs sources** :
- `balance_sheet.liabilities.equity.total.value`
- `balance_sheet.liabilities.debt.long_term_debt.value`
- `balance_sheet.assets.fixed_assets.total.value`

**Interprétation** :
- **FR > 0** : Équilibre financier sain - Excédent de ressources stables
- **FR = 0** : Limite - Aucune marge
- **FR < 0** : Déséquilibre - Risque de liquidité

**Utilité** :
Le FR indique si l'entreprise finance ses investissements long terme (machines, locaux) avec des ressources stables (capital, emprunts LT) ou avec des ressources court terme (dangereux).

**Règle d'or** : FR doit être > BFR pour avoir une trésorerie positive.

---

### BFR (Besoin en Fonds de Roulement)

**Catégorie** : Liquidité
**Unité** : €

**Formule** :
```
BFR = (Stocks + Créances) - Dettes d'exploitation CT
```

**Formule détaillée** :
```
BFR = (Stocks + Créances clients) - (Fournisseurs + Dettes fiscales/sociales)
```

**Formule LaTeX** :
```latex
(Stocks + Créances) - Dettes\ court\ terme\ d'exploitation
```

**Calcul détaillé** :
```python
Emplois cycliques = Stocks + Créances clients
Ressources cycliques = Dettes fournisseurs + Dettes fiscales + Dettes sociales
BFR = Emplois - Ressources
```

**Champs sources** :
- `balance_sheet.assets.current_assets.inventory.value`
- `balance_sheet.assets.current_assets.accounts_receivable.value`
- `balance_sheet.liabilities.operating_liabilities.accounts_payable.value`
- `balance_sheet.liabilities.operating_liabilities.tax_liabilities.value`

**Interprétation** :
- **BFR > 0** : Besoin de financement - L'entreprise finance le décalage de trésorerie
- **BFR = 0** : Équilibre parfait (rare)
- **BFR < 0** : Ressource - Les clients paient avant de payer les fournisseurs (ex: grande distribution)

**Utilité** :
Le BFR mesure l'argent "immobilisé" dans le cycle d'exploitation :
- Stocks qui attendent d'être vendus
- Clients qui n'ont pas encore payé
- Moins : fournisseurs pas encore payés

**Exemple** :
- BFR = 100k€ → Il faut financer 100k€ en permanence pour tourner
- BFR = -50k€ → L'activité génère 50k€ de cash (ex: Amazon collecte l'argent des clients avant de payer les fournisseurs)

---

## Métriques de Rentabilité

### EBITDA

**Catégorie** : Rentabilité
**Unité** : €

**Formule** :
```
EBITDA = Résultat d'exploitation + Dotations aux amortissements + Provisions
```

**Formule LaTeX** :
```latex
Résultat\ d'exploitation + Dotations\ aux\ amortissements + Provisions
```

**Calcul détaillé** :
```python
EBITDA = Operating Income + Depreciation + Provisions
```

**Champs sources** :
- `income_statement.operating_income.value`
- `income_statement.operating_expenses.depreciation.value`
- `income_statement.operating_expenses.provisions.value`

**Interprétation** :
L'EBITDA est le **cash-flow opérationnel brut** avant :
- Intérêts (choix de financement)
- Impôts (fiscalité)
- Amortissements (comptable, pas de sortie de cash)

**Utilité** :
- Mesure la performance opérationnelle pure
- Comparable entre entreprises (neutralise structure financière et fiscale)
- Base de calcul des multiples de valorisation (EV/EBITDA)

---

### Marge Brute

**Catégorie** : Rentabilité
**Unité** : %

**Formule** :
```
Marge Brute = ((CA - Achats) / CA) × 100
```

**Formule LaTeX** :
```latex
\frac{CA - Achats}{CA} \times 100
```

**Calcul détaillé** :
```python
CA = Chiffre d'affaires (revenues)
Achats = Achats de marchandises + matières premières
Marge Brute = ((CA - Achats) / CA) × 100
```

**Champs sources** :
- `income_statement.revenues.total.value`
- `income_statement.operating_expenses.purchases.value`

**Interprétation** :
- **> 50%** : Excellent (services, SaaS, luxe)
- **30% - 50%** : Bon (industrie à forte valeur ajoutée)
- **15% - 30%** : Acceptable (commerce, distribution)
- **< 15%** : Faible (commerce de gros)

**Benchmarks** :
```python
{
    "excellent": 50.0,
    "good": 30.0,
    "acceptable": 15.0,
    "risky": 5.0
}
```

**Utilité** :
La marge brute indique le "mark-up" sur les achats. Plus elle est élevée, plus l'entreprise a de pouvoir de pricing.

---

### Marge d'Exploitation

**Catégorie** : Rentabilité
**Unité** : %

**Formule** :
```
Marge Exploitation = (Résultat d'exploitation / CA) × 100
```

**Formule LaTeX** :
```latex
\frac{Résultat\ d'exploitation}{CA} \times 100
```

**Calcul détaillé** :
```python
Résultat d'exploitation = EBIT
CA = Chiffre d'affaires
Marge = (EBIT / CA) × 100
```

**Champs sources** :
- `income_statement.operating_income.value`
- `income_statement.revenues.total.value`

**Interprétation** :
- **> 15%** : Excellente - Très rentable
- **10% - 15%** : Bonne - Rentabilité solide
- **5% - 10%** : Acceptable - Rentabilité correcte
- **< 5%** : Faible - Peu rentable

**Benchmarks** :
```python
{
    "excellent": 15.0,
    "good": 10.0,
    "acceptable": 5.0,
    "risky": 0.0
}
```

**Utilité** :
La marge d'exploitation mesure la rentabilité après TOUTES les charges opérationnelles (achats, salaires, loyers, etc.) mais avant la dette et les impôts.

---

### Marge Nette

**Catégorie** : Rentabilité
**Unité** : %

**Formule** :
```
Marge Nette = (Résultat net / CA) × 100
```

**Formule LaTeX** :
```latex
\frac{Résultat\ net}{CA} \times 100
```

**Calcul détaillé** :
```python
Résultat net = Bénéfice après impôts
CA = Chiffre d'affaires
Marge Nette = (Résultat net / CA) × 100
```

**Champs sources** :
- `income_statement.net_income.value`
- `income_statement.revenues.total.value`

**Interprétation** :
- **> 10%** : Excellente - Très profitable
- **5% - 10%** : Bonne - Profitable
- **2% - 5%** : Acceptable - Profit correct
- **< 2%** : Faible - Peu profitable

**Benchmarks** :
```python
{
    "excellent": 10.0,
    "good": 5.0,
    "acceptable": 2.0,
    "risky": 0.0
}
```

**Utilité** :
La marge nette est la rentabilité finale, ce qui reste VRAIMENT dans la poche après tout (charges, intérêts, impôts).

**Exemples sectoriels** :
- Apple : ~25%
- Amazon : ~5%
- Grande distribution : ~2%

---

## Notes Méthodologiques

### Gestion des cas edge

Toutes les métriques gèrent :
- **Division par zéro** : Retourne `inf` ou `0` selon le cas
- **Valeurs manquantes** : Retourne `0` par défaut
- **Valeurs négatives** : Gestion spécifique par métrique

### Source des données

Les données proviennent des liasses fiscales françaises (formulaires 2033 pour régime simplifié, 2050-2059 pour régime réel normal).

### Validation

Chaque métrique inclut une validation automatique des champs sources avant calcul via la méthode `validate_inputs()`.

---

**Dernière mise à jour** : Phase 1 MVP - 10 métriques
**Prochaine mise à jour** : Phase 2 - 60+ métriques complètes
