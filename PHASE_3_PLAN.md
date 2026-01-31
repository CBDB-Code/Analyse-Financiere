# 🎯 Plan Phase 3 - Application LBO Professionnelle

**Date** : Janvier 2026
**Version** : 3.0 (Refonte complète basée sur référentiel business)
**Objectif** : Transformer l'application en outil professionnel pour acquisitions LBO 2-20M€

---

## 📋 Résumé Exécutif

### Problèmes Actuels (Phase 2)
❌ **Formule DSCR incorrecte** : Utilise EBITDA simple au lieu de CFADS (EBITDA - IS cash ± ΔBFR - Capex maintenance)
❌ **Pas de normalisation** : Aucun workflow EBE → EBITDA banque → EBITDA equity
❌ **Structure désorganisée** : 6 pages dispersées au lieu d'un workflow cohérent
❌ **Pas de décision finale** : Aucun système GO/WATCH/NO-GO
❌ **Mauvaise UX** : Saisie sans séparateurs de milliers, pas d'impact temps réel
❌ **Métriques incorrectes** : Hiérarchie non respectée (DSCR devrait être #1)

### Transformation Phase 3
✅ **Formules bancaires françaises** : DSCR selon standard Bpifrance/banques françaises
✅ **Workflow de normalisation** : 3 étapes (Import → Normalisation → Montage LBO)
✅ **Architecture 1 PAGE 4 TABS** : Données → Montage → Viabilité → Synthèse
✅ **Décision automatique** : Algorithme GO/WATCH/NO-GO basé sur 5 métriques clés
✅ **UX interactive** : Sliders avec zones colorées, impact temps réel, formatage milliers
✅ **5 métriques décisives** : DSCR, Dette nette/EBITDA, Marge EBITDA, Conversion EBITDA→FCF, FCF positif

---

## 🏗️ Architecture Cible Phase 3

### Mode Unique : "Analyser une Acquisition"

**1 PAGE - 4 TABS (workflow séquentiel)** :

```
┌─────────────────────────────────────────────────────────────────┐
│  💰 Analyse Financière - Acquisition LBO                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [📊 Données]  [🔧 Montage]  [✅ Viabilité]  [📄 Synthèse]     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Tab 1 : 📊 Données (Import & Normalisation)

**Objectif** : Obtenir des données normalisées "banque-ready"

**Sections** :
1. **Import Liasse Fiscale**
   - Upload PDF ou saisie manuelle
   - Détection automatique qualité (PDF natif vs scanné)
   - Extraction automatique
   - **Affichage avec formatage milliers** : "1 200 000 €" au lieu de "1200000"

2. **Data Quality Center** (NOUVEAU)
   - Checklist qualité automatique :
     ```
     ✅ Bilan équilibré (Actif = Passif)
     ✅ Résultat cohérent (Bilan = Compte de résultat)
     ⚠️ CA > 2M€ et < 20M€ (hors cible si non)
     ✅ EBE positif
     ⚠️ BFR > 25% CA (point de vigilance)
     ```
   - Détection anomalies :
     - Croissance CA > 100% ou < -50% (à vérifier)
     - Marge EBITDA < 5% (activité peu profitable)
     - Dette existante > 5x EBITDA (overleveraged)

3. **Normalisation / Retraitements** (NOUVEAU - KILLER FEATURE)
   - **Étape 1 : EBE (Excédent Brut d'Exploitation)**
     ```
     EBE = CA - Achats consommés - Charges externes - Impôts & taxes - Charges personnel
     ```
     Affichage : "EBE initial : 850 000 €"

   - **Étape 2 : Retraitements → EBITDA banque**
     Interface avec **4 ajustements prédéfinis + custom** :
     ```
     [+] Loyers retraités (crédit-bail)      [Input: _________] €
     [+] Rémunération dirigeant excessive     [Input: _________] €
     [+] Charges exceptionnelles              [Input: _________] €
     [-] Subventions non récurrentes          [Input: _________] €
     [+] Ajustement personnalisé              [Input: _________] €
     ```
     → **Waterfall chart temps réel** :
     ```
     850k (EBE) +150k (loyers) +80k (rémun.) -30k (subv.) = 1 050k (EBITDA banque)
     ```

   - **Étape 3 : EBITDA banque → EBITDA equity**
     ```
     - IS cash théorique (taux effectif)
     - Capex maintenance (% CA ou montant fixe)
     = EBITDA equity
     ```

   - **Stockage** :
     ```python
     NormalizationData:
       - ebe: float
       - adjustments: List[Adjustment]
       - ebitda_bank: float
       - ebitda_equity: float
       - audit_log: List[str]  # Traçabilité
     ```

4. **Validation Finale**
   - Bouton "✅ Valider les données normalisées"
   - Passage automatique à Tab 2 si validé

---

#### Tab 2 : 🔧 Montage LBO (CORE FEATURE)

**Objectif** : Construire le plan de financement et voir impact temps réel sur viabilité

**Layout 3 colonnes** :

```
┌──────────────────┬──────────────────────┬──────────────────┐
│  PARAMÈTRES      │  VISUALISATION       │  IMPACT & KPIs   │
│  (sliders)       │  (graphiques)        │  (métriques)     │
│                  │                      │                  │
│  [Sliders...]    │  [DSCR Zone Chart]   │  🟢 DSCR: 1.8   │
│                  │                      │  🟢 Dette/EBITDA │
│                  │  [Structure Chart]   │  🟡 Marge        │
│                  │                      │  🔴 FCF          │
└──────────────────┴──────────────────────┴──────────────────┘
```

##### Colonne 1 : Paramètres du Montage (Sliders Améliorés)

**A. Structure de Financement**

1. **Prix d'Acquisition**
   ```
   Prix : [========|===] 5 000 000 €
          2M        10M       20M
   ```
   - Formatage avec espaces : "5 000 000 €"
   - Zone verte : 2-10M€, zone orange : 10-15M€, zone rouge : >15M€

2. **Dette Senior** (Slider avec zones colorées)
   ```
   Dette senior : [====|========] 60 %
                  0%   50%   70%   100%
                  🟢    🟡    🔴

   Montant : 3 000 000 €
   Taux : [===|=] 4.5 %
          2%  5%   8%
   Durée : [======|] 7 ans
           3      10    15
   ```
   - **Zone verte** : 40-60% du prix (levier sain)
   - **Zone orange** : 60-70% (acceptable)
   - **Zone rouge** : >70% (risqué)

3. **Dette Bpifrance** (optionnel)
   ```
   [☐] Activer Bpifrance

   Si activé :
   Montant : [====|] 500 000 €
             0   1M     2M
   Taux : [==|=] 3.0 %
          1%  4%   7%
   Durée : [=======|] 8 ans
   ```

4. **Crédit Vendeur** (optionnel)
   ```
   [☐] Activer crédit vendeur

   Si activé :
   Montant : [===|] 750 000 €
             0   1M    2M
   Différé : [==|] 2 ans
             0   3    5
   ```

5. **Equity**
   ```
   Equity : [====|] 1 750 000 €  (auto-calculé)

   Répartition :
   - Entrepreneur : [======|] 70 %
   - Investisseurs : 30 % (auto)
   ```

**B. Hypothèses Exploitation**

6. **Croissance CA**
   ```
   Croissance an 1-3 : [==|==] +5 %/an
                       -10% 0  +15%

   Scénarios préréglés :
   [Conservateur: +3%] [Médian: +5%] [Optimiste: +10%]
   ```

7. **Marge EBITDA**
   ```
   Évolution marge : [=|==] +0.5 pts/an
                     -2  0   +3
   ```

8. **BFR**
   ```
   BFR : [===|=] 18 % du CA
         10%  25%  40%
   ```

9. **Capex Maintenance**
   ```
   Capex : [==|=] 3 % du CA
           1%  5%  10%
   ```

##### Colonne 2 : Visualisations Temps Réel

**Graphique 1 : DSCR Zone Chart** (PRIORITÉ #1)

```
┌─────────────────────────────────────────┐
│  DSCR sur 7 ans                         │
│                                         │
│  2.5  ┌──────────────┐ Zone Excellence │
│       │   🟢 ZONE    │ (>1.5)          │
│  1.5  ├──────────────┤                 │
│       │   🟡 ZONE    │ Zone Acceptable │
│  1.25 ├──────────────┤ (1.25-1.5)      │
│       │              │                 │
│  1.0  ├──────────────┤ Seuil Minimum   │
│       │   🔴 ZONE    │                 │
│  0.5  └──────────────┘                 │
│       Y1  Y2  Y3  Y4  Y5  Y6  Y7      │
│                                         │
│  Courbe DSCR : [Line montrant évolution]│
└─────────────────────────────────────────┘
```

Interaction :
- Hover sur courbe → "Année 3: DSCR = 1.65 (Bon)"
- **Zones colorées en arrière-plan** (gradient)
- Point minimum identifié automatiquement

**Graphique 2 : Structure de Financement (Donut)**

```
┌─────────────────────────────┐
│  Structure Capitalistique   │
│                             │
│         ┌─────┐            │
│         │ 60% │ Dette senior│
│         ├─────┤            │
│         │ 10% │ Bpifrance  │
│         ├─────┤            │
│         │ 15% │ Crédit V.  │
│         ├─────┤            │
│         │ 35% │ Equity     │
│         └─────┘            │
│                             │
│  Levier total : 2.5x       │
└─────────────────────────────┘
```

**Graphique 3 : Waterfall CFADS → Service Dette**

```
┌──────────────────────────────────────┐
│  Décomposition DSCR Année 1          │
│                                      │
│  EBITDA    IS cash   ΔBFR   Capex   │
│  1 050 k   -100k    -50k    -80k    │
│  ████      ▼▼       ▼▼      ▼▼      │
│           = CFADS : 820 k            │
│                     ████             │
│           Service dette : 450 k      │
│                     ████             │
│           = DSCR : 1.82              │
│                    ████              │
└──────────────────────────────────────┘
```

##### Colonne 3 : Impact & KPIs Temps Réel

**Carte KPI avec couleurs dynamiques** :

```
┌─────────────────────────────────────┐
│  🎯 MÉTRIQUES DÉCISIVES             │
├─────────────────────────────────────┤
│                                     │
│  🟢 DSCR min (7 ans)     1.45      │
│     Seuil : >1.25                   │
│     Zone : Bon ✓                    │
│                                     │
│  🟢 Dette nette/EBITDA   3.2x      │
│     Seuil : <4x                     │
│     Zone : Acceptable ✓             │
│                                     │
│  🟡 Marge EBITDA         12.5 %    │
│     Seuil : >15%                    │
│     Zone : Limite ⚠                 │
│                                     │
│  🟢 Conversion EBITDA→FCF 45 %     │
│     Seuil : >30%                    │
│     Zone : Bon ✓                    │
│                                     │
│  🔴 FCF positif dès...   Année 3   │
│     Objectif : Année 2              │
│     Zone : Retard ✗                 │
│                                     │
├─────────────────────────────────────┤
│  DÉCISION PRÉLIMINAIRE              │
│                                     │
│  🟡 WATCH                           │
│     → Marge faible                  │
│     → FCF tardif                    │
│                                     │
│  [Voir détails Tab 3 →]            │
└─────────────────────────────────────┘
```

**Section "Impact des Changements"** (sous KPIs)

Lorsque l'utilisateur bouge un slider :

```
┌─────────────────────────────────────┐
│  📊 DERNIÈRE MODIFICATION           │
├─────────────────────────────────────┤
│  Dette senior : 60% → 65%           │
│                                     │
│  Impacts :                          │
│  • DSCR min : 1.45 → 1.32  🔻      │
│  • Dette/EBITDA : 3.2x → 3.5x 🔻   │
│  • Equity requis : -250k    🟢     │
│  • Statut : WATCH → WATCH   ⚠      │
│                                     │
│  [Annuler] [Valider]                │
└─────────────────────────────────────┘
```

**Boutons d'Action** :

```
[💾 Sauvegarder Scénario]  [📋 Comparer Scénarios]  [✅ Valider Montage →]
```

---

#### Tab 3 : ✅ Viabilité (Stress Tests & Décision)

**Objectif** : Valider la robustesse du montage et prendre décision GO/WATCH/NO-GO

##### Section 1 : Stress Tests Automatiques

**Tableau de stress tests** :

```
┌────────────────────────────────────────────────────────────────┐
│  🔬 STRESS TESTS                                                │
├─────────────────┬──────────┬──────────┬──────────┬─────────────┤
│  Scénario       │ DSCR min │ Dette/EB │ FCF an 3 │ Statut      │
├─────────────────┼──────────┼──────────┼──────────┼─────────────┤
│  ✅ Nominal     │  1.45    │  3.2x    │  +180k   │  🟡 WATCH   │
│  ⚠️ CA -10%     │  1.18    │  3.8x    │  -50k    │  🔴 NO-GO   │
│  ⚠️ CA -20%     │  0.85    │  4.5x    │  -220k   │  🔴 NO-GO   │
│  ⚠️ Marge -2pts │  1.28    │  3.4x    │  +90k    │  🟡 WATCH   │
│  ⚠️ Taux +200bp │  1.22    │  3.2x    │  +120k   │  🟡 WATCH   │
│  ⚠️ BFR +5pts   │  1.35    │  3.3x    │  +140k   │  🟡 WATCH   │
├─────────────────┴──────────┴──────────┴──────────┴─────────────┤
│  Résultat : ⚠️ Dossier sensible aux chocs CA                   │
│  → Recommandation : Négocier garanties supplémentaires         │
└────────────────────────────────────────────────────────────────┘
```

##### Section 2 : Analyse de Sensibilité (Heatmap)

**Heatmap interactive** : Impact croisé CA vs Marge sur DSCR

```
         Marge EBITDA
         8%   10%  12%  14%  16%
CA    ┌────────────────────────┐
 -20% │ 🔴  🔴  🔴  🟡  🟢   │
 -10% │ 🔴  🟡  🟡  🟢  🟢   │
   0% │ 🟡  🟡  🟢  🟢  🟢   │
 +10% │ 🟡  🟢  🟢  🟢  🟢   │
 +20% │ 🟢  🟢  🟢  🟢  🟢   │
      └────────────────────────┘

Légende :
🟢 DSCR > 1.5   (GO)
🟡 1.25-1.5     (WATCH)
🔴 < 1.25       (NO-GO)
```

##### Section 3 : Covenant Tracking (NOUVEAU)

**Timeline des covenants bancaires** :

```
┌──────────────────────────────────────────────────────────────┐
│  📊 COVENANTS BANCAIRES (tracking sur 7 ans)                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Dette nette / EBITDA  (seuil : <4x)                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 4.0 ┬───────────────────────────────────────────   │    │
│  │ 3.5 │   🔴seuil                                     │    │
│  │ 3.0 ├───●───●───●───●───●───●───●  ✓ OK            │    │
│  │ 2.5 │                                               │    │
│  │     └───────────────────────────────────────────   │    │
│  │         Y1  Y2  Y3  Y4  Y5  Y6  Y7                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  DSCR  (seuil : >1.25)                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 2.0 ┬───────────────────────────────────────────   │    │
│  │ 1.5 │   ●───●───●───●───●───●───●  ✓ OK            │    │
│  │ 1.25├───🔴seuil                                     │    │
│  │ 1.0 │                                               │    │
│  │     └───────────────────────────────────────────   │    │
│  │         Y1  Y2  Y3  Y4  Y5  Y6  Y7                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ✅ Aucune violation de covenant projetée                   │
└──────────────────────────────────────────────────────────────┘
```

##### Section 4 : Décision Automatique (Algorithme)

**Carte de décision finale** :

```
┌──────────────────────────────────────────────────────────────┐
│  🎯 DÉCISION D'ACQUISITION                                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Statut : 🟡 WATCH - Dossier À Renforcer                    │
│                                                              │
│  ╔════════════════════════════════════════════════════════╗ │
│  ║  CRITÈRES DE DÉCISION                                   ║ │
│  ╠════════════════════════════════════════════════════════╣ │
│  ║  ✅ DSCR min > 1.25                      Score : 100/100║ │
│  ║  ✅ Dette nette/EBITDA < 4x              Score : 100/100║ │
│  ║  ⚠️ Marge EBITDA > 15%                   Score : 60/100 ║ │
│  ║  ✅ Conversion EBITDA→FCF > 30%          Score : 100/100║ │
│  ║  ⚠️ FCF positif dès année 2              Score : 50/100 ║ │
│  ╠════════════════════════════════════════════════════════╣ │
│  ║  SCORE GLOBAL :  82 / 100                               ║ │
│  ╚════════════════════════════════════════════════════════╝ │
│                                                              │
│  📋 RECOMMANDATIONS                                          │
│  • ⚠️ Marge faible (12.5%) : Négocier prix ou améliorer mix │
│  • ⚠️ FCF tardif : Prévoir covenant additionnel année 1-2   │
│  • ✅ Levier acceptable : Structure de dette saine           │
│  • 💡 Suggestion : Augmenter equity de 10% pour sécuriser   │
│                                                              │
│  [📥 Exporter Rapport PDF]  [📧 Partager]  [✏️ Modifier]    │
└──────────────────────────────────────────────────────────────┘
```

**Algorithme de décision** :

```python
def calculate_decision(metrics: Dict) -> Decision:
    """
    GO : Score >= 90 ET tous critères >= 80
    WATCH : Score 70-89 OU 1-2 critères < 80
    NO-GO : Score < 70 OU 1 critère < 50
    """
    criteria_scores = {
        "dscr": 100 if dscr_min > 1.5 else 80 if dscr_min > 1.25 else 0,
        "leverage": 100 if leverage < 3.5 else 80 if leverage < 4 else 50 if leverage < 5 else 0,
        "margin": 100 if margin > 15 else 60 if margin > 10 else 30 if margin > 5 else 0,
        "conversion": 100 if conversion > 40 else 80 if conversion > 30 else 50,
        "fcf_timing": 100 if fcf_year <= 2 else 50 if fcf_year <= 3 else 20
    }

    total_score = sum(criteria_scores.values()) / len(criteria_scores)
    min_score = min(criteria_scores.values())

    if total_score >= 90 and min_score >= 80:
        return Decision.GO
    elif total_score >= 70 and min_score >= 50:
        return Decision.WATCH
    else:
        return Decision.NO_GO
```

---

#### Tab 4 : 📄 Synthèse (Export & Rapport)

**Objectif** : Générer rapport professionnel pour présentation banque/investisseurs

##### Section 1 : Executive Summary

**Carte synthétique** :

```
┌──────────────────────────────────────────────────────────────┐
│  📊 SYNTHÈSE EXÉCUTIVE                                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Entreprise : ACME SARL                                      │
│  Secteur : Services B2B                                      │
│  CA 2025 : 8 500 000 €                                       │
│  EBITDA normalisé : 1 050 000 € (12.4%)                     │
│                                                              │
│  ╔════════════════════════════════════════════════════════╗ │
│  ║  MONTAGE LBO PROPOSÉ                                    ║ │
│  ╠════════════════════════════════════════════════════════╣ │
│  ║  Prix d'acquisition :        5 000 000 €                ║ │
│  ║  Dette senior (60%) :        3 000 000 €                ║ │
│  ║  Dette Bpifrance (10%) :       500 000 €                ║ │
│  ║  Crédit vendeur (15%) :        750 000 €                ║ │
│  ║  Equity (35%) :              1 750 000 €                ║ │
│  ║                                                          ║ │
│  ║  Multiple acquisition :       4.8x EBITDA               ║ │
│  ║  Levier total :               3.2x Dette/EBITDA         ║ │
│  ╚════════════════════════════════════════════════════════╝ │
│                                                              │
│  🎯 DÉCISION : 🟡 WATCH (Score 82/100)                      │
│                                                              │
│  Conditions recommandées :                                   │
│  • Négocier -10% sur prix OU augmenter equity               │
│  • Covenant DSCR trimestriel année 1-2                      │
│  • Garantie dirigeant 20% pendant 3 ans                     │
└──────────────────────────────────────────────────────────────┘
```

##### Section 2 : Sélecteur de Rapport

```
┌─────────────────────────────────────────────────────┐
│  📄 GÉNÉRATION DE RAPPORT                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Type de rapport :                                  │
│  ○ Rapport Banquier (focus risque/DSCR)            │
│  ● Rapport Investisseur (focus ROI/TRI)            │
│  ○ Rapport Complet (tout)                          │
│                                                     │
│  Sections à inclure :                               │
│  ☑ Executive summary                                │
│  ☑ Données normalisées (waterfall)                 │
│  ☑ Structure de financement                         │
│  ☑ Métriques clés (5 décisives)                    │
│  ☑ Stress tests & sensibilité                      │
│  ☑ Covenant tracking                                │
│  ☑ Décision & recommandations                       │
│  ☐ Annexes (détails calculs)                       │
│                                                     │
│  Format :                                           │
│  ● PDF    ○ PowerPoint    ○ Excel                  │
│                                                     │
│  [🎨 Prévisualiser]  [📥 Télécharger]              │
└─────────────────────────────────────────────────────┘
```

##### Section 3 : Prévisualisation Rapport

**Aperçu du PDF généré** (miniatures des pages)

```
┌──────────────────────────────────────────────────────────────┐
│  📄 PRÉVISUALISATION (6 pages)                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  [Page 1]     [Page 2]     [Page 3]     [Page 4]           │
│   Cover     Executive    Montage LBO   Métriques            │
│   ┌────┐     ┌────┐       ┌────┐       ┌────┐             │
│   │Logo│     │📊  │       │💰  │       │📈  │             │
│   │    │     │    │       │    │       │    │             │
│   └────┘     └────┘       └────┘       └────┘             │
│                                                              │
│  [Page 5]     [Page 6]                                      │
│  Stress      Décision                                        │
│   ┌────┐     ┌────┐                                         │
│   │🔬  │     │✅  │                                         │
│   │    │     │    │                                         │
│   └────┘     └────┘                                         │
│                                                              │
│  [📥 Télécharger PDF]                                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔢 Formules Financières Corrigées (Normes Françaises)

### 1. DSCR (Debt Service Coverage Ratio) - VERSION CORRECTE

**Formule française standard** :

```
DSCR = CFADS / Service annuel de la dette

Où :
CFADS (Cash-Flow Available for Debt Service) =
    EBITDA normalisé
    - IS cash (impôt société décaissé)
    ± ΔBFR (variation BFR, négatif si augmentation)
    - Capex maintenance

Service annuel de la dette =
    Remboursement capital + Intérêts
```

**Implémentation Python** :

```python
@register_metric
class DSCR_French(FinancialMetric):
    """
    DSCR selon normes bancaires françaises.
    Utilise CFADS (EBITDA - IS - ΔBFR - Capex) et non EBITDA brut.
    """

    _metadata = MetricMetadata(
        name="dscr_french",
        formula_latex=r"\frac{EBITDA - IS_{cash} \pm \Delta BFR - Capex_{maint}}{Remb.\ capital + Intérêts}",
        description="DSCR (norme bancaire française) - Capacité de remboursement",
        unit="ratio",
        category=MetricCategory.BANKER,
        benchmark_ranges={
            "excellent": 1.5,
            "good": 1.25,
            "acceptable": 1.1,
            "risky": 1.0,
        },
    )

    def calculate(self, financial_data: dict) -> float:
        # 1. EBITDA normalisé (banque)
        ebitda_bank = financial_data.get("normalization", {}).get("ebitda_bank", 0)

        # 2. IS cash (taux effectif appliqué)
        effective_tax_rate = financial_data.get("assumptions", {}).get("tax_rate", 0.25)
        is_cash = ebitda_bank * effective_tax_rate

        # 3. ΔBFR (variation)
        bfr_current = financial_data.get("working_capital", {}).get("bfr", 0)
        bfr_previous = financial_data.get("working_capital", {}).get("bfr_previous", bfr_current)
        delta_bfr = bfr_current - bfr_previous  # Positif = augmentation = consommation cash

        # 4. Capex maintenance
        capex_maint = financial_data.get("assumptions", {}).get("capex_maintenance", 0)

        # 5. CFADS
        cfads = ebitda_bank - is_cash - delta_bfr - capex_maint

        # 6. Service de dette
        debt_service = financial_data.get("scenario", {}).get("annual_debt_service", 0)

        if debt_service == 0:
            return float("inf")

        return cfads / debt_service
```

### 2. Dette Nette / EBITDA

**Formule** :

```
Dette nette / EBITDA = (Dette financière totale - Trésorerie) / EBITDA normalisé banque

Où :
Dette financière totale = Dette senior + Bpifrance + Crédit vendeur + Dette existante
EBITDA normalisé banque = Issu du workflow de normalisation
```

### 3. Marge EBITDA

```
Marge EBITDA = (EBITDA normalisé banque / CA) × 100
```

### 4. Conversion EBITDA → FCF (Free Cash Flow)

```
Conversion = (FCF / EBITDA) × 100

Où :
FCF = EBITDA - IS cash - ΔBFR - Capex total - Service dette
```

### 5. TRI (Taux de Rendement Interne)

**Formule complète** (non simplifiée) :

```
TRI = Taux tel que VAN = 0

Avec flux :
- Année 0 : -Equity investi
- Années 1-N : Dividendes distribués (si FCF > 0)
- Année N : Valeur de sortie - Dette restante

Valeur de sortie = EBITDA année N × Multiple de sortie
```

---

## 🗄️ Modèle de Données Phase 3

### Nouveaux Modèles Pydantic

```python
# 1. Normalisation
class Adjustment(BaseModel):
    """Retraitement comptable."""
    name: str
    amount: float
    category: AdjustmentCategory  # PERSONNEL | RENT | EXCEPTIONAL | OTHER
    description: str
    impact_on_ebitda: float  # Positif = augmente EBITDA

class NormalizationData(BaseModel):
    """Données normalisées."""
    ebe: float  # Excédent Brut d'Exploitation
    adjustments: List[Adjustment]
    ebitda_bank: float  # EBITDA normalisé banque
    ebitda_equity: float  # EBITDA equity (après IS & capex)
    audit_log: List[str]  # Traçabilité
    validated_at: Optional[datetime]
    validated_by: Optional[str]

# 2. Structure LBO
class DebtLayer(BaseModel):
    """Tranche de dette."""
    name: str  # "Dette senior", "Bpifrance", "Crédit vendeur"
    amount: float
    interest_rate: float
    duration_years: int
    grace_period: int = 0
    amortization_type: str = "constant"  # constant | linear | bullet

class LBOStructure(BaseModel):
    """Structure de financement LBO."""
    acquisition_price: float
    debt_layers: List[DebtLayer]
    equity_amount: float
    equity_split: Dict[str, float]  # {"entrepreneur": 0.7, "investors": 0.3}

    @property
    def total_debt(self) -> float:
        return sum(d.amount for d in self.debt_layers)

    @property
    def leverage_ratio(self) -> float:
        return self.total_debt / (self.total_debt + self.equity_amount)

# 3. Hypothèses Exploitation
class OperatingAssumptions(BaseModel):
    """Hypothèses d'exploitation."""
    revenue_growth_rate: List[float]  # Par année [0.05, 0.05, 0.03, ...]
    ebitda_margin_evolution: List[float]  # Évolution pts [0.5, 0.5, 0, ...]
    bfr_percentage_of_revenue: float = 0.18
    capex_maintenance_pct: float = 0.03
    capex_development: List[float] = []  # Capex additionnel par année
    tax_rate: float = 0.25

# 4. Covenant
class Covenant(BaseModel):
    """Covenant bancaire."""
    name: str  # "DSCR", "Dette nette/EBITDA"
    metric_name: str  # Nom métrique dans le registre
    threshold: float
    comparison: str  # ">" | "<" | ">=" | "<="
    applicable_years: List[int]  # [1, 2, 3, ...] ou [] pour toutes

    def is_violated(self, actual_value: float) -> bool:
        """Vérifie si covenant violé."""
        if self.comparison == ">":
            return actual_value <= self.threshold
        elif self.comparison == "<":
            return actual_value >= self.threshold
        # etc.

# 5. Décision
class Decision(Enum):
    GO = "go"
    WATCH = "watch"
    NO_GO = "no_go"

class DecisionCriteria(BaseModel):
    """Critère de décision."""
    name: str
    actual_value: float
    threshold: float
    score: int  # 0-100
    weight: float = 1.0
    status: str  # "PASS" | "WARNING" | "FAIL"

class AcquisitionDecision(BaseModel):
    """Décision d'acquisition."""
    decision: Decision
    overall_score: int  # 0-100
    criteria: List[DecisionCriteria]
    recommendations: List[str]
    warnings: List[str]
    deal_breakers: List[str]

    timestamp: datetime
    scenario_id: str
```

### Schéma BDD SQLite (Ajouts)

```sql
-- Table normalization
CREATE TABLE normalization (
    id INTEGER PRIMARY KEY,
    fiscal_year_id INTEGER,
    ebe REAL,
    ebitda_bank REAL,
    ebitda_equity REAL,
    validated_at TIMESTAMP,
    FOREIGN KEY (fiscal_year_id) REFERENCES fiscal_years(id)
);

-- Table adjustments
CREATE TABLE adjustments (
    id INTEGER PRIMARY KEY,
    normalization_id INTEGER,
    name TEXT,
    amount REAL,
    category TEXT,
    description TEXT,
    FOREIGN KEY (normalization_id) REFERENCES normalization(id)
);

-- Table lbo_structures
CREATE TABLE lbo_structures (
    id INTEGER PRIMARY KEY,
    analysis_id INTEGER,
    acquisition_price REAL,
    equity_amount REAL,
    total_debt REAL,
    created_at TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Table debt_layers
CREATE TABLE debt_layers (
    id INTEGER PRIMARY KEY,
    lbo_structure_id INTEGER,
    name TEXT,
    amount REAL,
    interest_rate REAL,
    duration_years INTEGER,
    FOREIGN KEY (lbo_structure_id) REFERENCES lbo_structures(id)
);

-- Table covenants
CREATE TABLE covenants (
    id INTEGER PRIMARY KEY,
    lbo_structure_id INTEGER,
    name TEXT,
    metric_name TEXT,
    threshold REAL,
    comparison TEXT,
    FOREIGN KEY (lbo_structure_id) REFERENCES lbo_structures(id)
);

-- Table decisions
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    analysis_id INTEGER,
    decision TEXT,  -- 'go' | 'watch' | 'no_go'
    overall_score INTEGER,
    recommendations TEXT,  -- JSON array
    timestamp TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

---

## 🎨 Améliorations UX Phase 3

### 1. Formatage des Nombres

**Problème actuel** : "1200000" → illisible
**Solution** :

```python
def format_number(value: float, unit: str = "€") -> str:
    """
    Formate avec espaces insécables tous les 3 chiffres.

    Exemples:
    - 1200000 → "1 200 000 €"
    - 1234.56 → "1 234.56 €"
    - 0.05 → "5.0 %"
    """
    if unit == "%":
        return f"{value:.1f} %"
    elif unit in ("€", "EUR", "euro"):
        # Sépare milliers avec espace insécable
        formatted = f"{value:,.0f}".replace(",", " ")
        return f"{formatted} €"
    elif unit == "ratio":
        return f"{value:.2f}"
    else:
        formatted = f"{value:,.0f}".replace(",", " ")
        return formatted

# Usage dans Streamlit
st.number_input(
    "Prix d'acquisition",
    min_value=0,
    max_value=20_000_000,
    value=5_000_000,
    step=100_000,
    format="%d",
    help="Prix d'achat de l'entreprise"
)

# Affichage formaté
st.metric(
    label="Prix",
    value=format_number(5_000_000, "€")
)
```

### 2. Sliders avec Zones Colorées

**Implémentation Streamlit + CSS** :

```python
import streamlit as st
import plotly.graph_objects as go

def create_colored_slider(
    label: str,
    min_val: float,
    max_val: float,
    value: float,
    step: float,
    zones: Dict[str, Tuple[float, float]],
    unit: str = ""
):
    """
    Slider avec zones colorées.

    Args:
        zones: {"green": (40, 60), "orange": (60, 70), "red": (70, 100)}
    """
    # Slider standard
    selected = st.slider(
        label,
        min_value=min_val,
        max_value=max_val,
        value=value,
        step=step,
        format=f"%.1f{unit}"
    )

    # Indicateur visuel des zones
    fig = go.Figure()

    # Zone verte
    fig.add_shape(
        type="rect",
        x0=zones["green"][0], x1=zones["green"][1],
        y0=0, y1=1,
        fillcolor="green", opacity=0.2, line_width=0
    )

    # Zone orange
    fig.add_shape(
        type="rect",
        x0=zones["orange"][0], x1=zones["orange"][1],
        y0=0, y1=1,
        fillcolor="orange", opacity=0.2, line_width=0
    )

    # Zone rouge
    fig.add_shape(
        type="rect",
        x0=zones["red"][0], x1=zones["red"][1],
        y0=0, y1=1,
        fillcolor="red", opacity=0.2, line_width=0
    )

    # Marqueur position actuelle
    fig.add_trace(go.Scatter(
        x=[selected],
        y=[0.5],
        mode="markers",
        marker=dict(size=15, color="black"),
        showlegend=False
    ))

    fig.update_layout(
        height=80,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(range=[min_val, max_val], showgrid=False),
        yaxis=dict(range=[0, 1], showticklabels=False, showgrid=False)
    )

    st.plotly_chart(fig, use_container_width=True)

    return selected

# Usage
dette_pct = create_colored_slider(
    label="Dette senior (%)",
    min_val=0,
    max_val=100,
    value=60,
    step=5,
    zones={
        "green": (40, 60),
        "orange": (60, 70),
        "red": (70, 100)
    },
    unit="%"
)
```

### 3. Impact Temps Réel

**Système de détection de changements** :

```python
# State management
if "previous_params" not in st.session_state:
    st.session_state.previous_params = {}

def detect_changes(current_params: Dict) -> Dict:
    """Détecte quels paramètres ont changé."""
    changes = {}
    prev = st.session_state.previous_params

    for key, value in current_params.items():
        if key not in prev or prev[key] != value:
            changes[key] = {
                "old": prev.get(key),
                "new": value
            }

    return changes

def show_impact_panel(changes: Dict, metrics_before: Dict, metrics_after: Dict):
    """Affiche panneau d'impact des changements."""
    if not changes:
        return

    with st.expander("📊 Impact des Modifications", expanded=True):
        for param, change in changes.items():
            st.write(f"**{param}** : {change['old']} → {change['new']}")

        st.divider()
        st.write("**Impacts sur les métriques** :")

        for metric_name, value_after in metrics_after.items():
            value_before = metrics_before.get(metric_name, 0)
            delta = value_after - value_before
            delta_pct = (delta / value_before * 100) if value_before != 0 else 0

            icon = "🔻" if delta < 0 else "🔺" if delta > 0 else "➖"

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(metric_name)
            with col2:
                st.metric("", f"{value_after:.2f}", delta=f"{delta:.2f}")
            with col3:
                st.write(f"{icon} {delta_pct:+.1f}%")

# Usage dans le workflow
current_params = {
    "dette_senior": dette_pct,
    "taux_interet": taux,
    # ...
}

changes = detect_changes(current_params)

if changes:
    # Recalcul automatique
    metrics_after = calculate_all_metrics(current_params)
    show_impact_panel(changes, st.session_state.metrics_before, metrics_after)

    # Bouton validation
    if st.button("✅ Valider ces changements"):
        st.session_state.previous_params = current_params
        st.session_state.metrics_before = metrics_after
        st.rerun()
```

---

## 📊 Roadmap d'Implémentation Phase 3

### Semaine 1 : Refonte Architecture & Normalisation (Priorité CRITIQUE)

**Jours 1-2 : Nouvelle architecture app.py**
- [ ] Créer `src/ui/app_v3.py` avec structure 1 PAGE 4 TABS
- [ ] Implémenter navigation séquentielle (validation entre tabs)
- [ ] State management global (st.session_state structure)
- [ ] Créer `src/ui/components/` pour composants réutilisables

**Jours 3-5 : Tab 1 - Normalisation**
- [ ] Créer `src/normalization/normalizer.py` :
  - Classe `DataNormalizer` avec méthodes :
    - `calculate_ebe()`
    - `apply_adjustments()`
    - `calculate_ebitda_bank()`
    - `calculate_ebitda_equity()`
- [ ] Créer modèles Pydantic `NormalizationData`, `Adjustment`
- [ ] Interface saisie ajustements avec **waterfall chart temps réel**
- [ ] Data Quality Center avec checklist automatique
- [ ] Tests unitaires normalization

### Semaine 2 : Tab 2 - Montage LBO Interactif (CORE FEATURE)

**Jours 1-2 : Sliders améliorés**
- [ ] Créer `src/ui/components/colored_slider.py`
- [ ] Implémenter formatage milliers partout
- [ ] 9 sliders avec zones colorées (dette, taux, croissance, etc.)
- [ ] Calcul automatique equity (total - dettes)

**Jours 3-4 : Visualisations temps réel**
- [ ] Créer `src/visualization/lbo_charts.py` :
  - `create_dscr_zone_chart()` - PRIORITÉ #1
  - `create_structure_donut()`
  - `create_waterfall_cfads()`
- [ ] Intégration Plotly avec interactions
- [ ] Système de détection changements temps réel

**Jour 5 : Colonne KPIs temps réel**
- [ ] Créer `src/calculations/decisive_metrics.py` (5 métriques clés)
- [ ] Carte KPI avec couleurs dynamiques
- [ ] Panneau impact changements
- [ ] Système validation/annulation

### Semaine 3 : Tab 3 - Viabilité & Décision

**Jours 1-2 : Stress tests**
- [ ] Créer `src/scenarios/stress_tester.py` :
  - `run_stress_tests()` (6 scénarios)
  - `calculate_sensitivity_matrix()`
- [ ] Tableau stress tests avec statuts
- [ ] Heatmap sensibilité interactive

**Jours 3-4 : Covenant tracking**
- [ ] Modèle `Covenant` Pydantic
- [ ] Créer `src/calculations/covenant_tracker.py`
- [ ] Timeline graphiques covenants (dette/EBITDA, DSCR)
- [ ] Détection violations automatique

**Jour 5 : Algorithme de décision**
- [ ] Créer `src/decision/decision_engine.py` :
  - Classe `DecisionEngine`
  - Méthode `calculate_decision()`
  - Scoring critères pondérés
- [ ] Carte décision avec recommandations
- [ ] Modèles `Decision`, `DecisionCriteria` Pydantic

### Semaine 4 : Tab 4 - Synthèse & Export + Formules Correctes

**Jours 1-2 : Formules bancaires françaises**
- [ ] Corriger `DSCR` dans `src/calculations/banker/debt_coverage.py` :
  - Utiliser CFADS (EBITDA - IS - ΔBFR - Capex)
  - Tests unitaires avec cas réels
- [ ] Créer `src/calculations/banker/french_metrics.py` :
  - `CFADS`
  - `NetDebtToEBITDA_Normalized`
  - `EBITDAMargin_Normalized`
  - `EBITDAtoFCF_Conversion`
- [ ] Mettre à jour tous les calculs pour utiliser EBITDA normalisé

**Jours 3-4 : Export PDF**
- [ ] Créer templates Jinja2 dans `src/reporting/templates/` :
  - `lbo_report_banker.html`
  - `lbo_report_investor.html`
- [ ] Créer `src/reporting/pdf_generator.py` :
  - Classe `LBOReportGenerator`
  - Méthodes par section
  - Embedding graphiques Plotly en base64
- [ ] Interface sélection rapport (Tab 4)
- [ ] Prévisualisation avant export

**Jour 5 : Polissage & Tests**
- [ ] Tests end-to-end workflow complet
- [ ] Correction bugs détectés
- [ ] Documentation utilisateur (QUICKSTART_v3.md)
- [ ] Vidéo démo 5min

### Semaine 5 : BDD & Persistance + Déploiement

**Jours 1-2 : Migrations BDD**
- [ ] Créer script `scripts/migrate_to_v3.py` :
  - Ajout tables normalization, adjustments
  - Ajout tables lbo_structures, debt_layers
  - Ajout tables covenants, decisions
- [ ] Créer modèles SQLAlchemy correspondants
- [ ] CRUD pour toutes les nouvelles entités
- [ ] Tests migrations avec données Phase 2

**Jours 3-4 : Features secondaires**
- [ ] Comparaison scénarios (overlay plusieurs montages)
- [ ] Historique versions (tracking modifications)
- [ ] Export Excel (alternative PDF)
- [ ] Partage email (envoi rapport)

**Jour 5 : Déploiement**
- [ ] Mise à jour requirements.txt (WeasyPrint, Jinja2)
- [ ] Test déploiement Streamlit Cloud
- [ ] Migration données production
- [ ] Documentation déploiement

---

## 🎯 Critères de Succès Phase 3

| Critère | Objectif | Validation |
|---------|----------|------------|
| **Formule DSCR correcte** | Utilise CFADS (norme française) | ✅ Tests unitaires passent |
| **Workflow normalisation** | 3 étapes (EBE → EBITDA banque → equity) | ✅ Waterfall chart + traçabilité |
| **Architecture 1 PAGE 4 TABS** | Navigation séquentielle cohérente | ✅ UX fluide validée |
| **Décision automatique** | GO/WATCH/NO-GO basé sur 5 métriques | ✅ Algorithme testé |
| **UX interactive** | Formatage milliers + sliders zones | ✅ Impact temps réel fonctionnel |
| **Stress tests** | 6 scénarios + heatmap sensibilité | ✅ Violations covenant détectées |
| **Export PDF** | Rapport professionnel généré | ✅ Template banker/investor OK |
| **Performance** | Calculs < 500ms | ✅ Benchmark passé |

---

## 🚧 Risques & Mitigations

### Risque 1 : Complexité du workflow normalisation
**Impact** : Utilisateurs perdus
**Mitigation** :
- Tutoriel interactif au 1er lancement
- Vidéo explicative intégrée
- Valeurs par défaut intelligentes
- Aide contextuelle (tooltips)

### Risque 2 : Performance calculs temps réel
**Impact** : Lag interface
**Mitigation** :
- Debouncing sliders (calcul après 500ms inactivité)
- Cache calculs intermédiaires
- Calcul asynchrone si >1s

### Risque 3 : Export PDF lourd (WeasyPrint)
**Impact** : Timeout Streamlit Cloud
**Mitigation** :
- Alternative ReportLab (plus léger)
- Génération asynchrone avec progress bar
- Option export PowerPoint (python-pptx)

### Risque 4 : Migration données Phase 2 → Phase 3
**Impact** : Perte historique
**Mitigation** :
- Script migration automatique
- Backup BDD avant migration
- Mode compatibilité Phase 2 temporaire

---

## 📚 Documentation Phase 3

### Fichiers à créer/mettre à jour

1. **README.md** (mise à jour)
   - Nouvelles fonctionnalités
   - Screenshots Tab 1-4
   - Exemple workflow complet

2. **QUICKSTART_v3.md** (nouveau)
   - Guide pas à pas 1ère utilisation
   - Cas d'usage : "Analyser acquisition PME 5M€"
   - FAQ

3. **FORMULAS_v3.md** (mise à jour)
   - Formule DSCR corrigée avec explications
   - Normalisation EBE → EBITDA détaillée
   - Algorithme décision GO/WATCH/NO-GO

4. **API.md** (nouveau)
   - Documentation classes principales
   - Exemples utilisation DataNormalizer
   - Exemples DecisionEngine

5. **VIDEO_DEMO.md** (script vidéo)
   - Storyboard vidéo 5min
   - Points clés à montrer

---

## ✨ Killer Features Phase 3 (Différenciation)

1. **🔧 Workflow Normalisation Guidé**
   - Seule app à proposer EBE → EBITDA banque → EBITDA equity
   - Waterfall chart temps réel
   - Traçabilité audit complète

2. **📊 DSCR Zone Chart Interactif**
   - Visualisation unique avec zones colorées
   - Identification automatique année critique
   - Projection 7 ans avec covenants

3. **🎯 Décision Automatique Intelligente**
   - Algorithme scoring pondéré
   - Recommandations personnalisées
   - Pas juste des métriques, mais une DÉCISION

4. **⚡ Impact Temps Réel**
   - Chaque slider → recalcul instantané
   - Panneau "Dernière modification"
   - Validation/Annulation changements

5. **📄 Export PDF Professionnel**
   - Template banker vs investor
   - Graphiques embarqués haute qualité
   - Prêt pour présentation banque

---

## 🎓 Cas d'Usage Cible Phase 3

### Cas 1 : Entrepreneur en Recherche d'Acquisition

**Persona** : Marc, 42 ans, ex-cadre industrie, recherche PME à racheter

**Workflow** :
1. Obtient liasse fiscale vendeur
2. Upload PDF → Extraction automatique
3. Tab 1 : Normalise données (détecte rémunération dirigeant excessive)
4. Tab 2 : Construit montage 70% dette / 30% equity
5. Ajuste sliders jusqu'à DSCR > 1.5
6. Tab 3 : Vérifie stress tests (-10% CA OK, -20% KO)
7. Tab 4 : Export PDF pour présenter à banque
8. **Décision** : WATCH → Négocie -10% sur prix

**Temps gagné** : 8 heures analyse Excel → 45 minutes

### Cas 2 : Banquier en Analyse de Crédit LBO

**Persona** : Sophie, analyste crédit Bpifrance

**Workflow** :
1. Reçoit dossier entrepreneur avec liasse + business plan
2. Import liasse → Validation data quality
3. Tab 1 : Vérifie normalisation (contesté 1 ajustement)
4. Tab 2 : Reconstruit montage proposé
5. Tab 3 : Stress tests → Détecte violation covenant si CA -15%
6. Ajuste structure : propose garantie supplémentaire
7. Tab 4 : Export rapport interne
8. **Décision** : WATCH → Demande covenant trimestriel

**Temps gagné** : 2 jours analyse → 3 heures

### Cas 3 : Fonds d'Investissement (Due Diligence)

**Persona** : Cabinet d'audit mandaté par fonds

**Workflow** :
1. Liasses fiscales 3 derniers exercices
2. Upload 3 PDFs → Comparaison tendances
3. Tab 1 : Normalisation cohérente sur 3 ans
4. Détecte anomalie : marge EBITDA en baisse
5. Tab 2 : Teste 3 structures de financement différentes
6. Tab 3 : Analyse sensibilité → Recommande structure conservatrice
7. Tab 4 : Rapport complet investisseurs
8. **Décision** : GO sous conditions

**Temps gagné** : 1 semaine → 1 journée

---

## 💰 Coût Estimé Phase 3

**Développement** :
- Temps : 5 semaines (200h dev)
- IA (Claude) : Gratuit (usage inclus)

**Nouvelles dépendances** :
- WeasyPrint : Gratuit (GPL)
- python-pptx : Gratuit (MIT)
- Jinja2 : Gratuit (BSD)

**Utilisation** :
- Streamlit Cloud : Gratuit (tier Community)
- Extraction PDF : $0.10-0.50/liasse (inchangé)
- Calculs : $0 (Python pur)
- Export PDF : $0 (local)

**Total** : Quasi-gratuit (hors temps dev)

---

## 🚀 Quick Start après Phase 3

### Installation

```bash
cd "Analyse Financiere"
git pull origin main
pip install -r requirements.txt
python scripts/migrate_to_v3.py  # Migration BDD
streamlit run src/ui/app_v3.py
```

### Utilisation Typique

1. **Upload liasse fiscale** (Tab 1)
   - Cliquer "Upload PDF"
   - Vérifier data quality ✅
   - Normaliser : +150k loyers → EBITDA banque = 1 050k€
   - Valider ✅

2. **Construire montage LBO** (Tab 2)
   - Prix : 5 000 000 €
   - Dette senior : 60% (3M€) à 4.5% sur 7 ans
   - Bpifrance : 10% (500k€) à 3% sur 8 ans
   - Equity : 30% (1 500k€)
   - **Observer** : DSCR = 1.65 🟢

3. **Valider viabilité** (Tab 3)
   - Stress tests : ✅ Tous scénarios > 1.25 sauf CA -20%
   - Covenants : ✅ Aucune violation
   - **Décision** : 🟢 GO (Score 92/100)

4. **Exporter rapport** (Tab 4)
   - Sélectionner "Rapport Banquier"
   - Télécharger PDF
   - Envoyer à banque

---

## 📝 Notes Importantes

### Différences vs Phases 1-2

| Aspect | Phase 1-2 | Phase 3 |
|--------|-----------|---------|
| **Pages** | 6 pages dispersées | 1 page 4 tabs séquentiels |
| **DSCR** | EBITDA / Dette service (incorrect) | CFADS / Dette service (correct) |
| **Normalisation** | Aucune | Workflow complet EBE→EBITDA |
| **Décision** | Métriques brutes | GO/WATCH/NO-GO automatique |
| **UX** | Nombres bruts | Formatage milliers + zones |
| **Formules** | 25 métriques génériques | 5 métriques décisives + 20 support |
| **Export** | Aucun | PDF professionnel |

### Philosophie Produit Phase 3

**Avant (Phase 2)** : Outil de calcul financier générique
**Après (Phase 3)** : Plateforme de décision LBO professionnelle

**Avant** : "Voici vos métriques, interprétez-les"
**Après** : "Voici ma recommandation : WATCH car marge faible"

**Avant** : Excel avec formules
**Après** : Conseiller financier IA

---

## ✅ Validation du Plan

### Token-économe ✅
- IA utilisée uniquement pour extraction PDF (inchangé)
- Tous calculs en Python pur déterministe
- Coût : ~$0.10-0.50 par analyse

### Robuste ✅
- Formules bancaires françaises standard
- Tests unitaires pour DSCR, CFADS, normalisation
- Traçabilité audit complète
- Validation données multi-niveaux

### Conforme Référentiel Business ✅
- Deals 2-20M€ PME françaises
- Structure dette : Senior + Bpifrance + Crédit vendeur
- 5 métriques décisives exactes
- Workflow normalisation complet
- Décision GO/WATCH/NO-GO

### UX Professionnelle ✅
- 1 PAGE 4 TABS cohérent
- Formatage milliers partout
- Sliders zones colorées
- Impact temps réel
- Export PDF banque-ready

---

**Phase 3 prête à démarrer** 🚀

Validation requise avant implémentation. Retours souhaités sur :
1. Priorité features (OK ou ajustements ?)
2. Roadmap 5 semaines (faisable ou trop ambitieux ?)
3. Killer features (lesquelles prioriser ?)
4. Risques identifiés (autres ?)
