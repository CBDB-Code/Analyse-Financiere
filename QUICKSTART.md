# 🚀 Guide de Démarrage Rapide

## Installation en 5 minutes

### 1. Créer l'environnement virtuel

```bash
cd "/Users/berlychristophe/Desktop/Marketing Skills/Analyse Financiere"
python3 -m venv venv
source venv/bin/activate
```

### 2. Installer les dépendances

```bash
pip install --upgrade pip
pip install -e .
```

**Note** : L'installation peut prendre 2-3 minutes (compilation de certaines dépendances).

### 3. Initialiser la base de données

```bash
python scripts/init_db.py
```

Vous devriez voir :
```
✅ Base de données créée : data/database/financials.db
Tables créées : companies, fiscal_years, analyses, scenarios, calculated_metrics, comparisons, comparison_items
✅ Données d'exemple ajoutées avec succès
```

### 4. Lancer l'application

```bash
streamlit run src/ui/app.py
```

L'application s'ouvre automatiquement à `http://localhost:8501` 🎉

## Premier Test

1. **Cliquez sur "Charger exemple de données"** dans la section bleue
2. **Ajustez les sliders** dans "Paramètres du scénario" :
   - Montant dette : 500 000 €
   - Taux d'intérêt : 5%
   - Durée : 7 ans
   - Montant equity : 300 000 €
3. **Cliquez sur "💰 Calculer les métriques"**
4. **Consultez les résultats** :
   - DSCR, ICR (perspective Banquier)
   - ROE, Payback (perspective Entrepreneur)
   - FR, BFR (Liquidité)
   - EBITDA, Marges (Rentabilité)

## Changer de Perspective

Dans la **sidebar** (menu latéral gauche) :
- Sélectionnez "Banquier" pour voir uniquement les métriques bancaires
- Sélectionnez "Entrepreneur" pour les métriques d'investissement
- Sélectionnez "Complète" pour tout voir

## Problèmes Courants

### `ModuleNotFoundError`
```bash
# Assurez-vous d'être dans l'environnement virtuel
source venv/bin/activate
pip install -e .
```

### L'application ne se lance pas
```bash
# Vérifiez que Streamlit est installé
pip list | grep streamlit

# Réinstaller si nécessaire
pip install streamlit
```

### Base de données non trouvée
```bash
# Réinitialiser la BDD
rm -f data/database/financials.db
python scripts/init_db.py
```

## Prochaines Étapes

✅ **Phase 1 - MVP (Actuelle)** : 10 métriques, scénarios interactifs
🔄 **Phase 2 - En cours** : 60+ métriques, extraction PDF, graphiques avancés
📅 **Phase 3 - À venir** : Multi-exercices, comparaisons, export PDF

## Support

Pour toute question, consultez le [README.md](README.md) complet.
