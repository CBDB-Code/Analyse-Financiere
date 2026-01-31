"""
Page Streamlit pour la comparaison multi-entreprises.

Cette page permet de:
- Selectionner plusieurs entreprises (2 a 5)
- Comparer leurs metriques financieres
- Visualiser avec des graphiques comparatifs (radar, barres)
- Calculer un score composite et classement

Accessible via: streamlit run app.py -> Page Comparaison
"""

import sys
from pathlib import Path

# Ajouter le repertoire racine au path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots

# Imports du projet
try:
    from src.visualization.charts import ChartFactory, COLORS
except ImportError as e:
    st.error(f"Erreur d'import: {e}")
    st.stop()


# =============================================================================
# CONFIGURATION DE LA PAGE
# =============================================================================

st.set_page_config(
    page_title="Comparaison Multi-Entreprises",
    page_icon="",
    layout="wide"
)


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def create_demo_companies() -> List[Dict[str, Any]]:
    """
    Cree des donnees de demonstration pour plusieurs entreprises.

    Returns:
        Liste d'entreprises avec leurs metriques
    """
    return [
        {
            "id": 1,
            "name": "TechCorp SA",
            "sector": "Technologie",
            "year": 2023,
            "revenues": 5_200_000,
            "ebitda": 1_040_000,
            "net_income": 520_000,
            "total_assets": 4_000_000,
            "equity": 2_500_000,
            "total_debt": 1_200_000,
            "ebitda_margin": 0.20,
            "net_margin": 0.10,
            "roe": 0.208,
            "roa": 0.13,
            "debt_to_equity": 0.48,
            "debt_to_ebitda": 1.15,
            "current_ratio": 2.1,
            "quick_ratio": 1.8,
            "dscr": 1.85,
            "icr": 4.2,
            "growth_cagr": 0.12
        },
        {
            "id": 2,
            "name": "IndustriePlus",
            "sector": "Industrie",
            "year": 2023,
            "revenues": 8_500_000,
            "ebitda": 1_275_000,
            "net_income": 425_000,
            "total_assets": 7_000_000,
            "equity": 3_500_000,
            "total_debt": 2_800_000,
            "ebitda_margin": 0.15,
            "net_margin": 0.05,
            "roe": 0.121,
            "roa": 0.061,
            "debt_to_equity": 0.80,
            "debt_to_ebitda": 2.20,
            "current_ratio": 1.4,
            "quick_ratio": 0.9,
            "dscr": 1.25,
            "icr": 2.8,
            "growth_cagr": 0.05
        },
        {
            "id": 3,
            "name": "ServicesPro SARL",
            "sector": "Services",
            "year": 2023,
            "revenues": 3_200_000,
            "ebitda": 800_000,
            "net_income": 480_000,
            "total_assets": 2_200_000,
            "equity": 1_600_000,
            "total_debt": 400_000,
            "ebitda_margin": 0.25,
            "net_margin": 0.15,
            "roe": 0.30,
            "roa": 0.218,
            "debt_to_equity": 0.25,
            "debt_to_ebitda": 0.50,
            "current_ratio": 2.8,
            "quick_ratio": 2.5,
            "dscr": 2.5,
            "icr": 8.0,
            "growth_cagr": 0.18
        },
        {
            "id": 4,
            "name": "Commerce Express",
            "sector": "Commerce",
            "year": 2023,
            "revenues": 12_000_000,
            "ebitda": 960_000,
            "net_income": 360_000,
            "total_assets": 5_500_000,
            "equity": 2_200_000,
            "total_debt": 2_500_000,
            "ebitda_margin": 0.08,
            "net_margin": 0.03,
            "roe": 0.164,
            "roa": 0.065,
            "debt_to_equity": 1.14,
            "debt_to_ebitda": 2.60,
            "current_ratio": 1.2,
            "quick_ratio": 0.6,
            "dscr": 1.10,
            "icr": 2.2,
            "growth_cagr": 0.08
        },
        {
            "id": 5,
            "name": "BioTech Innovation",
            "sector": "Biotechnologie",
            "year": 2023,
            "revenues": 2_100_000,
            "ebitda": 630_000,
            "net_income": 315_000,
            "total_assets": 3_500_000,
            "equity": 2_800_000,
            "total_debt": 500_000,
            "ebitda_margin": 0.30,
            "net_margin": 0.15,
            "roe": 0.1125,
            "roa": 0.09,
            "debt_to_equity": 0.18,
            "debt_to_ebitda": 0.79,
            "current_ratio": 3.5,
            "quick_ratio": 3.0,
            "dscr": 3.2,
            "icr": 12.0,
            "growth_cagr": 0.25
        }
    ]


# Metriques disponibles pour la comparaison
COMPARISON_METRICS = {
    "revenues": {"label": "Chiffre d'affaires", "format": "money", "higher_better": True},
    "ebitda": {"label": "EBITDA", "format": "money", "higher_better": True},
    "net_income": {"label": "Resultat net", "format": "money", "higher_better": True},
    "ebitda_margin": {"label": "Marge EBITDA", "format": "pct", "higher_better": True},
    "net_margin": {"label": "Marge nette", "format": "pct", "higher_better": True},
    "roe": {"label": "ROE", "format": "pct", "higher_better": True},
    "roa": {"label": "ROA", "format": "pct", "higher_better": True},
    "debt_to_equity": {"label": "Dette/Capitaux propres", "format": "ratio", "higher_better": False},
    "debt_to_ebitda": {"label": "Dette/EBITDA", "format": "ratio", "higher_better": False},
    "current_ratio": {"label": "Ratio de liquidite", "format": "ratio", "higher_better": True},
    "quick_ratio": {"label": "Ratio de liquidite immediate", "format": "ratio", "higher_better": True},
    "dscr": {"label": "DSCR", "format": "ratio", "higher_better": True},
    "icr": {"label": "ICR", "format": "ratio", "higher_better": True},
    "growth_cagr": {"label": "CAGR Croissance", "format": "pct", "higher_better": True}
}


# Poids par defaut pour le score composite
DEFAULT_WEIGHTS = {
    "dscr": 0.15,
    "roe": 0.15,
    "ebitda_margin": 0.15,
    "debt_to_ebitda": 0.15,
    "current_ratio": 0.10,
    "growth_cagr": 0.15,
    "net_margin": 0.15
}


def format_metric_value(value: float, format_type: str) -> str:
    """
    Formate une valeur selon son type.

    Args:
        value: Valeur a formater
        format_type: Type de format (money, pct, ratio)

    Returns:
        Valeur formatee
    """
    if value is None:
        return "N/A"

    if format_type == "money":
        if value >= 1_000_000:
            return f"{value/1_000_000:.2f}M EUR"
        elif value >= 1_000:
            return f"{value/1_000:.1f}k EUR"
        else:
            return f"{value:.0f} EUR"
    elif format_type == "pct":
        return f"{value:.1%}"
    elif format_type == "ratio":
        return f"{value:.2f}x"
    else:
        return f"{value:.2f}"


def calculate_composite_score(
    companies: List[Dict[str, Any]],
    weights: Dict[str, float]
) -> pd.DataFrame:
    """
    Calcule un score composite pour chaque entreprise.

    Le score est base sur la normalisation des metriques et leur
    ponderation selon les poids fournis.

    Args:
        companies: Liste des entreprises avec leurs metriques
        weights: Dictionnaire des poids par metrique

    Returns:
        DataFrame avec les scores
    """
    if not companies:
        return pd.DataFrame()

    # Creer un DataFrame
    df = pd.DataFrame(companies)

    # Calculer les scores normalises pour chaque metrique
    scores = {}

    for metric, weight in weights.items():
        if metric not in df.columns:
            continue

        values = df[metric].values
        metric_info = COMPARISON_METRICS.get(metric, {})

        # Normaliser entre 0 et 100
        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            normalized = [50] * len(values)
        else:
            if metric_info.get("higher_better", True):
                normalized = [(v - min_val) / (max_val - min_val) * 100 for v in values]
            else:
                # Inverser pour les metriques ou plus bas = mieux
                normalized = [(max_val - v) / (max_val - min_val) * 100 for v in values]

        scores[metric] = [n * weight for n in normalized]

    # Calculer le score total
    total_scores = [0] * len(companies)
    for metric_scores in scores.values():
        for i, s in enumerate(metric_scores):
            total_scores[i] += s

    # Normaliser sur 100
    max_possible = sum(weights.values()) * 100
    total_scores = [s / max_possible * 100 for s in total_scores]

    # Creer le DataFrame de resultats
    result = pd.DataFrame({
        "Entreprise": df["name"],
        "Secteur": df["sector"],
        "Score": total_scores
    })

    # Ajouter le rang
    result["Rang"] = result["Score"].rank(ascending=False).astype(int)

    return result.sort_values("Score", ascending=False)


def create_radar_chart(
    companies: List[Dict[str, Any]],
    metrics: List[str]
) -> go.Figure:
    """
    Cree un radar chart pour comparer les entreprises.

    Args:
        companies: Liste des entreprises
        metrics: Liste des metriques a comparer

    Returns:
        Figure Plotly
    """
    fig = go.Figure()

    colors = COLORS.scenario_colors

    for idx, company in enumerate(companies):
        # Normaliser les valeurs pour le radar (0-100)
        values = []
        labels = []

        for metric in metrics:
            if metric in company:
                metric_info = COMPARISON_METRICS.get(metric, {})
                labels.append(metric_info.get("label", metric))

                # Normalisation simple pour la visualisation
                raw_value = company[metric]

                # Ajuster selon le type de metrique
                if metric_info.get("format") == "pct":
                    values.append(raw_value * 100)  # Convertir en %
                elif metric_info.get("format") == "ratio":
                    # Limiter les ratios pour la visualisation
                    values.append(min(raw_value * 20, 100))
                else:
                    # Normaliser les valeurs monetaires
                    values.append(50)  # Valeur par defaut

        # Fermer le polygone
        values.append(values[0] if values else 0)
        labels.append(labels[0] if labels else "")

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=labels,
            fill='toself',
            name=company["name"],
            line=dict(color=colors[idx % len(colors)]),
            fillcolor=f"rgba{tuple(list(int(colors[idx % len(colors)][i:i+2], 16) for i in (1, 3, 5)) + [0.2])}"
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="Comparaison 360",
        showlegend=True,
        legend=dict(orientation="h", y=-0.1),
        height=500
    )

    return fig


def create_grouped_bar_chart(
    companies: List[Dict[str, Any]],
    metrics: List[str]
) -> go.Figure:
    """
    Cree un graphique a barres groupees.

    Args:
        companies: Liste des entreprises
        metrics: Liste des metriques

    Returns:
        Figure Plotly
    """
    fig = go.Figure()

    colors = COLORS.scenario_colors
    company_names = [c["name"] for c in companies]

    for idx, metric in enumerate(metrics):
        metric_info = COMPARISON_METRICS.get(metric, {})
        values = [c.get(metric, 0) for c in companies]

        # Formater les valeurs pour l'affichage
        if metric_info.get("format") == "pct":
            text_values = [f"{v:.1%}" for v in values]
            values = [v * 100 for v in values]  # Convertir en %
        elif metric_info.get("format") == "ratio":
            text_values = [f"{v:.2f}x" for v in values]
        else:
            text_values = [format_metric_value(v, metric_info.get("format", "")) for v in values]

        fig.add_trace(go.Bar(
            name=metric_info.get("label", metric),
            x=company_names,
            y=values,
            text=text_values,
            textposition="outside",
            marker_color=colors[idx % len(colors)]
        ))

    fig.update_layout(
        barmode="group",
        title="Comparaison des metriques",
        xaxis_title="Entreprise",
        yaxis_title="Valeur",
        height=450,
        legend=dict(orientation="h", y=1.1)
    )

    return fig


def create_heatmap(
    companies: List[Dict[str, Any]],
    metrics: List[str]
) -> go.Figure:
    """
    Cree une heatmap des metriques.

    Args:
        companies: Liste des entreprises
        metrics: Liste des metriques

    Returns:
        Figure Plotly
    """
    # Preparer la matrice
    company_names = [c["name"] for c in companies]
    metric_labels = [COMPARISON_METRICS.get(m, {}).get("label", m) for m in metrics]

    # Normaliser les valeurs entre 0 et 1
    z_values = []
    text_values = []

    for metric in metrics:
        metric_info = COMPARISON_METRICS.get(metric, {})
        values = [c.get(metric, 0) for c in companies]

        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            normalized = [0.5] * len(values)
        else:
            if metric_info.get("higher_better", True):
                normalized = [(v - min_val) / (max_val - min_val) for v in values]
            else:
                normalized = [(max_val - v) / (max_val - min_val) for v in values]

        z_values.append(normalized)

        # Texte a afficher
        row_text = []
        for v in values:
            if metric_info.get("format") == "pct":
                row_text.append(f"{v:.1%}")
            elif metric_info.get("format") == "ratio":
                row_text.append(f"{v:.2f}x")
            elif metric_info.get("format") == "money":
                row_text.append(format_metric_value(v, "money"))
            else:
                row_text.append(f"{v:.2f}")
        text_values.append(row_text)

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=company_names,
        y=metric_labels,
        text=text_values,
        texttemplate="%{text}",
        colorscale="RdYlGn",
        showscale=True,
        colorbar=dict(title="Score")
    ))

    fig.update_layout(
        title="Heatmap des performances",
        height=50 + len(metrics) * 40,
        xaxis_title="Entreprise",
        yaxis=dict(autorange="reversed")
    )

    return fig


# =============================================================================
# PAGE PRINCIPALE
# =============================================================================

st.title("Comparaison Multi-Entreprises")

st.markdown("""
Comparez les performances financieres de plusieurs entreprises cote a cote.
Selectionnez 2 a 5 entreprises et choisissez les metriques a comparer.
""")

st.divider()

# =============================================================================
# SECTION 1: SELECTION DES ENTREPRISES
# =============================================================================

st.header("Selection des entreprises")

# Charger les donnees de demonstration
if "comparison_companies" not in st.session_state:
    st.session_state["comparison_companies"] = create_demo_companies()

all_companies = st.session_state["comparison_companies"]

# Multiselect pour choisir les entreprises
company_names = [c["name"] for c in all_companies]

selected_names = st.multiselect(
    "Selectionnez les entreprises a comparer (2 a 5)",
    options=company_names,
    default=company_names[:3],
    max_selections=5,
    help="Selectionnez entre 2 et 5 entreprises pour la comparaison"
)

# Filtrer les entreprises selectionnees
selected_companies = [c for c in all_companies if c["name"] in selected_names]

if len(selected_companies) < 2:
    st.warning("Veuillez selectionner au moins 2 entreprises pour effectuer une comparaison.")
    st.stop()

st.divider()

# =============================================================================
# SECTION 2: TABLE COMPARATIVE
# =============================================================================

st.header("Table comparative")

# Selecteur de metriques a afficher
available_metrics = list(COMPARISON_METRICS.keys())
default_metrics = ["revenues", "ebitda", "ebitda_margin", "roe", "debt_to_equity", "dscr"]

selected_metrics = st.multiselect(
    "Metriques a afficher",
    options=available_metrics,
    default=default_metrics,
    format_func=lambda x: COMPARISON_METRICS[x]["label"]
)

if selected_metrics:
    # Creer le DataFrame de comparaison
    comparison_data = []

    for company in selected_companies:
        row = {
            "Entreprise": company["name"],
            "Secteur": company["sector"]
        }

        for metric in selected_metrics:
            metric_info = COMPARISON_METRICS.get(metric, {})
            value = company.get(metric, None)
            row[metric_info["label"]] = format_metric_value(value, metric_info.get("format", ""))

        comparison_data.append(row)

    df_comparison = pd.DataFrame(comparison_data)

    # Afficher avec style
    st.dataframe(df_comparison, use_container_width=True, hide_index=True)

st.divider()

# =============================================================================
# SECTION 3: VISUALISATIONS COMPARATIVES
# =============================================================================

st.header("Visualisations comparatives")

tab_radar, tab_bars, tab_heatmap = st.tabs([
    "Radar Chart 360",
    "Barres groupees",
    "Heatmap"
])

with tab_radar:
    st.subheader("Analyse 360")

    # Metriques pour le radar (max 8)
    radar_metrics = st.multiselect(
        "Metriques pour le radar (max 8)",
        options=available_metrics,
        default=["roe", "ebitda_margin", "dscr", "current_ratio", "debt_to_equity", "growth_cagr"],
        max_selections=8,
        format_func=lambda x: COMPARISON_METRICS[x]["label"],
        key="radar_metrics"
    )

    if radar_metrics and len(radar_metrics) >= 3:
        fig_radar = create_radar_chart(selected_companies, radar_metrics)
        st.plotly_chart(fig_radar, use_container_width=True)

        # Ajouter bouton d'export
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.download_button(
                "Exporter PNG",
                data=fig_radar.to_image(format="png"),
                file_name="radar_comparison.png",
                mime="image/png",
                key="download_radar"
            )
    else:
        st.info("Selectionnez au moins 3 metriques pour le radar chart.")

with tab_bars:
    st.subheader("Comparaison par barres")

    # Metriques pour les barres
    bar_metrics = st.multiselect(
        "Metriques a comparer",
        options=available_metrics,
        default=["ebitda_margin", "roe", "dscr"],
        max_selections=5,
        format_func=lambda x: COMPARISON_METRICS[x]["label"],
        key="bar_metrics"
    )

    if bar_metrics:
        fig_bars = create_grouped_bar_chart(selected_companies, bar_metrics)
        st.plotly_chart(fig_bars, use_container_width=True)

with tab_heatmap:
    st.subheader("Heatmap des performances")

    st.info(
        "La heatmap montre les performances relatives. "
        "Vert = meilleure performance, Rouge = moins bonne performance."
    )

    # Metriques pour la heatmap
    heatmap_metrics = st.multiselect(
        "Metriques pour la heatmap",
        options=available_metrics,
        default=["roe", "ebitda_margin", "net_margin", "dscr", "current_ratio", "debt_to_equity"],
        format_func=lambda x: COMPARISON_METRICS[x]["label"],
        key="heatmap_metrics"
    )

    if heatmap_metrics:
        fig_heatmap = create_heatmap(selected_companies, heatmap_metrics)
        st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# =============================================================================
# SECTION 4: RANKING AUTOMATIQUE
# =============================================================================

st.header("Classement composite")

st.markdown("""
Le score composite est calcule en normalisant et ponderant les metriques selectionnees.
Ajustez les poids selon votre analyse.
""")

# Afficher les poids actuels et permettre l'ajustement
with st.expander("Configurer les poids des metriques"):
    st.markdown("Ajustez les poids pour chaque metrique (total = 100%):")

    cols = st.columns(4)
    custom_weights = {}

    for idx, (metric, weight) in enumerate(DEFAULT_WEIGHTS.items()):
        metric_info = COMPARISON_METRICS.get(metric, {})
        with cols[idx % 4]:
            custom_weights[metric] = st.slider(
                metric_info.get("label", metric),
                min_value=0.0,
                max_value=0.5,
                value=weight,
                step=0.05,
                format="%.0f%%",
                key=f"weight_{metric}"
            )

    # Normaliser les poids
    total_weight = sum(custom_weights.values())
    if total_weight > 0:
        custom_weights = {k: v / total_weight for k, v in custom_weights.items()}

    st.caption(f"Total des poids: {sum(custom_weights.values()):.0%}")

# Calculer et afficher le classement
df_ranking = calculate_composite_score(selected_companies, custom_weights)

if not df_ranking.empty:
    # Afficher le podium
    col1, col2, col3 = st.columns(3)

    if len(df_ranking) >= 1:
        with col1:
            first = df_ranking.iloc[0]
            st.metric(
                label="1er",
                value=first["Entreprise"],
                delta=f"Score: {first['Score']:.1f}/100"
            )

    if len(df_ranking) >= 2:
        with col2:
            second = df_ranking.iloc[1]
            st.metric(
                label="2e",
                value=second["Entreprise"],
                delta=f"Score: {second['Score']:.1f}/100"
            )

    if len(df_ranking) >= 3:
        with col3:
            third = df_ranking.iloc[2]
            st.metric(
                label="3e",
                value=third["Entreprise"],
                delta=f"Score: {third['Score']:.1f}/100"
            )

    st.divider()

    # Tableau complet du classement
    st.subheader("Classement detaille")

    df_display = df_ranking.copy()
    df_display["Score"] = df_display["Score"].apply(lambda x: f"{x:.1f}/100")

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rang": st.column_config.NumberColumn("Rang", format="%d"),
            "Score": st.column_config.TextColumn("Score composite")
        }
    )

    # Graphique du classement
    fig_ranking = go.Figure(go.Bar(
        x=df_ranking["Entreprise"],
        y=df_ranking["Score"].values,
        text=[f"{s:.1f}" for s in df_ranking["Score"].values],
        textposition="outside",
        marker_color=[
            COLORS.success if i == 0 else
            COLORS.secondary if i == 1 else
            COLORS.warning if i == 2 else
            COLORS.primary
            for i in range(len(df_ranking))
        ]
    ))

    fig_ranking.update_layout(
        title="Classement par score composite",
        xaxis_title="Entreprise",
        yaxis_title="Score",
        height=400,
        yaxis=dict(range=[0, 105])
    )

    st.plotly_chart(fig_ranking, use_container_width=True)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.header("A propos")

    st.markdown("""
    **Comparaison Multi-Entreprises**

    Cette page permet de comparer jusqu'a 5 entreprises
    sur diverses metriques financieres.

    **Visualisations:**
    - **Radar**: Vue 360 des performances
    - **Barres**: Comparaison directe
    - **Heatmap**: Performance relative

    **Score composite:**
    Le classement est base sur des metriques
    ponderees et normalisees.
    """)

    st.divider()

    if selected_companies:
        st.subheader("Resume")
        st.write(f"Entreprises: {len(selected_companies)}")
        st.write(f"Metriques: {len(selected_metrics)}")

        # Meilleure et pire entreprise
        if not df_ranking.empty:
            best = df_ranking.iloc[0]
            st.success(f"Meilleur: {best['Entreprise']}")
