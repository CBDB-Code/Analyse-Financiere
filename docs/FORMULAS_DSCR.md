# 📐 Formule DSCR Correcte - Normes Bancaires Françaises

## ⚠️ Problème Identifié

### Ancienne Formule (INCORRECTE) ❌

```
DSCR = EBITDA / Service de la dette
```

**Problèmes** :
- Ignore l'impôt sur les sociétés (IS) décaissé
- Ignore la variation du BFR (consommation de cash)
- Ignore les investissements de maintenance (Capex)
- **Surestime la capacité de remboursement de +50% à +150%**

### Nouvelle Formule (CORRECTE) ✅

```
DSCR = CFADS / Service de la dette

Où CFADS (Cash Flow Available for Debt Service) =
    EBITDA normalisé
    - IS cash (impôt société décaissé)
    ± ΔBFR (variation BFR)
    - Capex maintenance
```

**Avantages** :
- Conforme aux normes bancaires françaises (Bpifrance, banques)
- Reflète le cash réellement disponible
- Intègre tous les décaissements obligatoires
- Permet une évaluation réaliste du risque

---

## 📊 Exemple Concret

### Données Entreprise ACME SARL

| Poste | Montant |
|-------|---------|
| **EBITDA normalisé** | 1 050 000 € |
| Taux IS effectif | 25% |
| BFR actuel | 1 530 000 € (18% CA) |
| BFR année précédente | 1 450 000 € |
| Capex maintenance | 250 000 € |
| **Service dette annuel** | 550 000 € |

### Calcul CFADS

```
EBITDA normalisé                 1 050 000 €
- IS cash (25% × 1 050 000)       -262 500 €
- ΔBFR (1 530 000 - 1 450 000)     -80 000 €  (augmentation = consommation)
- Capex maintenance                -250 000 €
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
= CFADS                            457 500 €
```

### Comparaison DSCR

| Formule | Calcul | Résultat | Décision |
|---------|--------|----------|----------|
| **Ancienne** (INCORRECTE) | 1 050 000 / 550 000 | **1.91** | 🟢 **GO** (semble confortable) |
| **Nouvelle** (CORRECTE) | 457 500 / 550 000 | **0.83** | 🔴 **NO-GO** (défaut!) |

### Impact

- **Surestimation** : +129% (plus du double!)
- **Décision** : Complètement inversée (GO → NO-GO)
- **Risque** : Avec l'ancienne formule, on approuverait un dossier qui ne peut pas rembourser sa dette

---

## 🎯 Seuils DSCR (Normes Bancaires)

| DSCR | Statut | Interprétation |
|------|--------|----------------|
| **≥ 1.50** | 🟢 Excellent | Marge confortable, levier élevé possible |
| **1.35 - 1.50** | 🟢 Bon | Standard Bpifrance, structure solide |
| **1.25 - 1.35** | 🟡 Acceptable | Covenant minimum bancaire, peu de marge |
| **1.00 - 1.25** | 🔴 Risqué | Violation covenant, réduire dette |
| **< 1.00** | 🔴 Défaut | Impossibilité de rembourser, montage non viable |

**Covenant standard** : DSCR > 1.25 (certaines banques exigent > 1.30)

---

## 💡 Pourquoi CFADS et pas EBITDA ?

### 1. IS Cash (Impôt Société)

L'EBITDA est **avant impôt**, mais l'IS doit être payé avant de pouvoir rembourser la dette.

```
Exemple:
EBITDA: 1 000 000 €
IS (25%): -250 000 €
→ Cash après IS: 750 000 €
```

❌ Ignorer l'IS = surestime de 33% le cash disponible

### 2. ΔBFR (Variation Besoin en Fonds de Roulement)

Quand le BFR augmente (croissance de l'activité), **le cash est consommé** (créances + stocks).

```
Exemple:
CA année N: 8.5M€ → BFR 18% = 1.53M€
CA année N+1: 9.0M€ → BFR 18% = 1.62M€
→ ΔBFR = +90k€ (consommation de cash)
```

❌ Ignorer ΔBFR = ignore un décaissement réel

### 3. Capex Maintenance

Les investissements de maintenance sont **obligatoires** pour maintenir l'outil de production.

```
Exemple:
Capex maintenance: 3% du CA = 250k€/an
→ Cash immobilisé, non disponible pour dette
```

❌ Ignorer Capex = surestime le cash libre

---

## 🔍 Cas d'Usage Réels

### Cas 1: Montage LBO Classique

**Contexte** :
- Acquisition: 5M€
- Dette: 3.5M€ (70%)
- EBITDA normalisé: 1M€

**Analyse ancienne formule** :
```
Service dette: 600k€/an
DSCR (EBITDA): 1M / 600k = 1.67 → 🟢 GO
```

**Analyse correcte (CFADS)** :
```
EBITDA: 1M€
- IS (25%): -250k€
- ΔBFR (croissance): -100k€
- Capex (3%): -150k€
= CFADS: 500k€

DSCR: 500k / 600k = 0.83 → 🔴 NO-GO
```

**Décision** : Le dossier ne passe PAS. Il faut soit :
- Réduire la dette à 2.5M€ max
- Augmenter l'equity à 2.5M€
- Améliorer l'EBITDA de 20%

### Cas 2: Impact Covenant

**Covenant bancaire** : DSCR > 1.25

**Année 1 - Ancienne formule** :
```
DSCR = 1.40 → ✅ Covenant OK
```

**Année 1 - Formule correcte** :
```
DSCR = 0.95 → ❌ Violation covenant!
```

**Conséquence** : Défaut technique → renégociation forcée ou remboursement anticipé

---

## 📚 Sources & Standards

### Bpifrance
- Covenant DSCR standard : **> 1.30**
- Calcul CFADS obligatoire pour tous dossiers LBO
- Documentation : "Guide Financement LBO PME"

### Banques Françaises
- Covenant DSCR : **> 1.25** (minimum)
- CFADS utilisé systématiquement depuis 2015
- Accord de Bâle III : focus sur cash-flow réel

### Fonds LBO
- DSCR > 1.50 pour obtenir financement optimal
- Stress tests avec CFADS sous scénarios dégradés
- Projections 7 ans avec CFADS annuel

---

## ✅ Implémentation Phase 3

### Nouvelles Métriques

1. **`CFADS`** (`src/calculations/banker/cfads.py`)
   - Calcul CFADS selon norme française
   - Gestion IS, ΔBFR, Capex
   - Interprétations automatiques

2. **`DSCR_French`** (`src/calculations/banker/cfads.py`)
   - Utilise CFADS (pas EBITDA brut)
   - Benchmarks conformes (>1.25)
   - Détection violations covenant

### Mise à Jour Modules

- `covenant_tracker.py` : Utilise DSCR_French
- `stress_tester.py` : Recalcule CFADS sous stress
- `decision_engine.py` : DSCR_French dans métriques décisives

### Tests Unitaires

```python
def test_dscr_vs_old():
    """Compare ancien DSCR vs nouveau DSCR_French."""
    data = {...}

    old_dscr = ebitda / debt_service  # 1.91
    new_dscr = cfads / debt_service    # 0.83

    assert new_dscr < 1.0  # Détecte le problème
    assert old_dscr > 1.5  # Ancienne formule donne faux OK
```

---

## 🎓 Conclusion

### Avant (EBITDA)
❌ Vision optimiste
❌ Ignore décaissements réels
❌ Surestime capacité +50-150%
❌ Risque d'approuver dossiers défaillants

### Après (CFADS)
✅ Vision réaliste
✅ Intègre tous décaissements
✅ Évaluation précise du risque
✅ Conforme normes bancaires françaises

---

**Version** : 3.0
**Date** : Janvier 2026
**Auteur** : Analyse Financière LBO Phase 3
**Référence** : Normes Bpifrance & Banques Françaises
