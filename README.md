# 💰 Analyse LBO Simplifiée

Application web pour évaluer rapidement la viabilité d'un montage LBO (Leveraged Buy-Out).

## 🎯 Objectif

Interface claire et intuitive pour calculer instantanément si un montage LBO est viable en fonction du DSCR (Debt Service Coverage Ratio) et du niveau d'endettement.

## ✨ Fonctionnalités

### Workflow en 3 étapes

1. **📊 Données Entreprise**
   - Chiffre d'affaires annuel
   - EBITDA annuel
   - Retraitements (charges et produits exceptionnels)
   - → EBITDA Normalisé calculé automatiquement

2. **💼 Montage LBO**
   - Prix d'acquisition
   - Apport entrepreneur/Equity
   - Dette bancaire (calculée automatiquement)
   - Taux d'intérêt et durée

3. **✅ Résultat Immédiat**
   - DSCR (capacité de remboursement)
   - Dette/EBITDA (niveau d'endettement)
   - Décision : 🟢 GO / 🟡 WATCH / 🔴 NO-GO
   - Recommandations personnalisées
   - Simulation rapide

## 🚀 Utilisation

### En ligne (Streamlit Cloud)

🔗 **https://[votre-app].streamlit.app/**

### Local

```bash
# Installer dépendances
pip install streamlit

# Lancer l'application
streamlit run app.py
```

## 📊 Critères de Décision

| Métrique | 🟢 GO | 🟡 WATCH | 🔴 NO-GO |
|----------|-------|----------|----------|
| **DSCR** | ≥ 1.25 | 1.0 - 1.25 | < 1.0 |
| **Dette/EBITDA** | ≤ 4.0x | 4.0 - 5.0x | > 5.0x |
| **Equity %** | ≥ 30% | 20 - 30% | < 20% |

### Calculs

**DSCR** = EBITDA / (Intérêts + Amortissement)
- Mesure la capacité à rembourser la dette
- Seuil bancaire standard : 1.25

**Dette/EBITDA** = Dette Totale / EBITDA Normalisé
- Mesure le niveau d'endettement
- Seuil bancaire standard : 4.0x

## 💡 Exemple

### Données entreprise
- CA : 8,5 M€
- EBITDA : 1,0 M€
- Charges exceptionnelles : 50 k€
- **→ EBITDA Normalisé : 1,05 M€**

### Montage LBO
- Prix : 5,0 M€ (multiple 4.8x)
- Equity : 1,5 M€ (30%)
- Dette : 3,5 M€ (70%)
- Taux : 4.5%
- Durée : 7 ans

### Résultat
- Service dette : 657 k€/an (intérêts 158k€ + amortissement 500k€)
- **DSCR : 1,60** ✅
- **Dette/EBITDA : 3,3x** ✅
- **Décision : 🟢 GO**

## 🛠️ Technologies

- **Streamlit** : Framework web Python
- **Python 3.10+** : Langage

## 📝 Licence

Développé avec Claude Sonnet 4.5 - Février 2026

---

**Version Simplifiée 1.0** - Interface claire, calculs précis, décision rapide
