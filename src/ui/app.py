"""
Redirection automatique vers app_v3.py (Phase 3)

Ce fichier redirige vers la nouvelle version de l'application (Phase 3)
pour maintenir la compatibilité avec Streamlit Cloud sans reconfiguration.

Pour exécuter directement la version 3.0 :
    streamlit run src/ui/app_v3.py
"""

import sys
from pathlib import Path

# Configuration du chemin
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import et exécution de app_v3
from src.ui import app_v3

# Note: Streamlit exécutera automatiquement le module app_v3
# car il est importé ici. Le code principal de app_v3.py sera exécuté.
