# 💰 Analyse LBO Professionnelle

Application web complète d'analyse financière pour montages LBO (Leveraged Buy-Out).

## 🎯 Deux Versions Disponibles

### 📊 Version Complète (`app.py`)
**Pour analystes financiers et professionnels**

Architecture 5 TABS + fonctionnalités avancées:
- **Tab 1**: Import & Normalisation données (banquier vs equity)
- **Tab 2**: Montage LBO avec sliders visuels
- **Tab 3**: Stress tests + Décision + Export Excel
- **Tab 4**: Export PDF professionnel + Gestion variantes
- **Tab 5**: Dashboard comparaison multi-dossiers (2-10 deals)

**Fonctionnalités:**
- ✅ Normalisation EBITDA (banquier vs equity)
- ✅ 7 scénarios de stress tests
- ✅ Export PDF (rapport banquier + investisseur)
- ✅ Sauvegarde/chargement variantes LBO
- ✅ Dashboard comparatif multi-dossiers
- ✅ Graphiques Plotly interactifs
- ✅ Export Excel avec 4 feuilles

### 🚀 Version Simplifiée (`app_simple.py`)
**Pour utilisateurs débutants - Interface épurée**

1 page, 1 formulaire, résultat immédiat:
- **Étape 1**: Données entreprise (CA, EBITDA, retraitements)
- **Étape 2**: Montage LBO (prix, equity, taux, durée)
- **Étape 3**: Résultat (DSCR, décision GO/WATCH/NO-GO)

**Avantages:**
- ✅ 10 champs essentiels uniquement
- ✅ Workflow 3 étapes clair
- ✅ Calculs automatiques
- ✅ Recommandations personnalisées
- ✅ Simulation rapide intégrée

## 🚀 Déploiement Streamlit Cloud

### Version Complète (Recommandée pour pro)
```
Repository: CBDB-Code/Analyse-Financiere
Branch: main
Main file: app.py
```

### Version Simplifiée (Recommandée pour débutants)
```
Repository: CBDB-Code/Analyse-Financiere
Branch: main
Main file: app_simple.py
```

## 📊 Critères de Décision (Communs aux 2 versions)

| Métrique | 🟢 GO | 🟡 WATCH | 🔴 NO-GO |
|----------|-------|----------|----------|
| **DSCR** | ≥ 1.25 | 1.0 - 1.25 | < 1.0 |
| **Dette/EBITDA** | ≤ 4.0x | 4.0 - 5.0x | > 5.0x |
| **Equity %** | ≥ 30% | 20 - 30% | < 20% |

**DSCR** (Debt Service Coverage Ratio) = EBITDA / (Intérêts + Amortissement)
- Capacité à rembourser la dette

**Dette/EBITDA** (Leverage) = Dette Totale / EBITDA Normalisé
- Niveau d'endettement

## 🛠️ Installation Locale

### Version Complète
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Version Simplifiée
```bash
pip install streamlit
streamlit run app_simple.py
```

## 📚 Documentation Détaillée

- `README_PHASE3.md` - Architecture version complète
- `README_PHASE3.5.md` - Améliorations UX & Performance
- `README_PHASE3.6.md` - Export PDF professionnel
- `README_PHASE3.7.md` - Système variantes LBO
- `README_PHASE3.8.md` - Dashboard multi-dossiers
- `docs/FORMULAS_DSCR.md` - Formules détaillées

## 💡 Exemple d'Utilisation

### Données
- CA: 8,5 M€
- EBITDA: 1,0 M€
- Retraitements: +50 k€
- **→ EBITDA Normalisé: 1,05 M€**

### Montage
- Prix: 5,0 M€ (4.8x EBITDA)
- Equity: 1,5 M€ (30%)
- Dette: 3,5 M€ (70%)
- Taux: 4.5% sur 7 ans

### Résultat
- **DSCR: 1,60** ✅
- **Dette/EBITDA: 3,3x** ✅
- **Décision: 🟢 GO** - Dossier viable

## 🎓 Technologies

- **Streamlit** - Framework web
- **Plotly** - Graphiques interactifs (version complète)
- **ReportLab** - Export PDF (version complète)
- **Openpyxl** - Export Excel (version complète)
- **Python 3.10+**

## 📈 Phases de Développement

- ✅ **Phase 3.0** - Base 4 tabs
- ✅ **Phase 3.5** - UX & Performance (caching, sliders visuels)
- ✅ **Phase 3.6** - Export PDF professionnel
- ✅ **Phase 3.7** - Sauvegarde/chargement variantes
- ✅ **Phase 3.8** - Dashboard comparaison multi-dossiers
- ✅ **Version Simple** - Interface épurée débutants

## 🔗 Liens Utiles

- **GitHub**: https://github.com/CBDB-Code/Analyse-Financiere
- **Streamlit Cloud**: https://share.streamlit.io/

---

**Développé avec Claude Sonnet 4.5** - Février 2026

*Choisissez la version adaptée à votre niveau et vos besoins !*
