"""
Page Streamlit pour l'analyse multi-exercices et les tendances.

Cette page permet de:
- Selectionner une entreprise et ses exercices
- Visualiser l'evolution des metriques sur plusieurs annees
- Analyser les tendances (CAGR, volatilite)
- Detecter les anomalies
- Generer des predictions

Accessible via: streamlit run app.py -> Page Tendances
"""

import sys
from pathlib import Path

# Ajouter le repertoire racine au path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
import json

# Imports du projet
try:
    from src.calculations.trends import (
        TrendAnalyzer,
        calculate_yoy_growth,
        format_trend_label,
        get_trend_color,
    )
    from src.visualization.charts import ChartFactory
except ImportError as e:
    st.error(f"Erreur d'import: {e}")
    st.stop()


# =============================================================================
# CONFIGURATION DE LA PAGE
# =============================================================================

st.set_page_config(
    page_title="Tendances Multi-Exercices",
    page_icon="",
    layout="wide"
)


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def create_demo_fiscal_data() -> List[Dict[str, Any]]:
    """
    Cree des donnees de demonstration pour plusieurs exercices.

    Returns:
        Liste de donnees fiscales sur 5 ans
    """
    base_revenues = 1_000_000
    base_ebitda = 200_000
    base_net_income = 80_000
    base_assets = 800_000
    base_equity = 400_000
    base_debt = 250_000

    data = []

    for i, year in enumerate(range(2019, 2024)):
        # Simuler une croissance avec des variations
        growth_factor = 1 + (0.08 + (i % 2) * 0.05)  # 8-13% de croissance

        revenues = base_revenues * (growth_factor ** i)
        ebitda = base_ebitda * (growth_factor ** i) * (1 + (i % 3 - 1) * 0.1)
        net_income = base_net_income * (growth_factor ** i) * (1 + (i % 2 - 0.5) * 0.15)

        # Ajout d'une anomalie en 2021
        if year == 2021:
            revenues *= 0.75  # Baisse de 25%
            ebitda *= 0.6
            net_income *= 0.4

        data.append({
            "year": year,
            "year_end": f"{year}-12-31",
            "revenues": revenues,
            "ebitda": ebitda,
            "net_income": net_income,
            "total_assets": base_assets * (1.05 ** i),
            "equity": base_equity * (1.04 ** i) + net_income * 0.5,
            "total_debt": base_debt * (1.02 ** i),
            "operating_cash_flow": ebitda * 0.85,
            "ebitda_margin": ebitda / revenues if revenues > 0 else 0,
            "net_margin": net_income / revenues if revenues > 0 else 0,
            "roe": net_income / (base_equity * (1.04 ** i)) if base_equity > 0 else 0,
            "debt_to_equity": (base_debt * (1.02 ** i)) / (base_equity * (1.04 ** i)),
            "current_ratio": 1.5 + (i % 3 - 1) * 0.2
        })

    return data


def get_company_list() -> List[Dict[str, Any]]:
    """
    Recupere la liste des entreprises disponibles.

    Pour l'instant, utilise des donnees de demonstration.
    A remplacer par une requete a la base de donnees.

    Returns:
        Liste des entreprises
    """
    # TODO: Connecter a la base de donnees
    # from src.database.models import Company
    # Session.query(Company).all()

    return [
        {"id": 1, "name": "Entreprise Demo", "siren": "123456789"},
        {"id": 2, "name": "Societe Test", "siren": "987654321"},
    ]


def get_fiscal_years_for_company(company_id: int) -> List[Dict[str, Any]]:
    """
    Recupere les exercices fiscaux d'une entreprise.

    Args:
        company_id: ID de l'entreprise

    Returns:
        Liste des exercices fiscaux
    """
    # TODO: Connecter a la base de donnees
    # Pour la demo, retourne des donnees simulees
    return create_demo_fiscal_data()


def format_value(value: float, metric_name: str) -> str:
    """
    Formate une valeur selon le type de metrique.

    Args:
        value: Valeur a formater
        metric_name: Nom de la metrique

    Returns:
        Valeur formatee
    """
    if value is None:
        return "N/A"

    # Metriques en pourcentage
    pct_metrics = ["ebitda_margin", "net_margin", "roe"]
    if metric_name in pct_metrics:
        return f"{value:.1%}"

    # Metriques en ratio
    ratio_metrics = ["debt_to_equity", "current_ratio"]
    if metric_name in ratio_metrics:
        return f"{value:.2f}x"

    # Metriques monetaires
    if value >= 1_000_000:
        return f"{value/1_000_000:.2f}M EUR"
    elif value >= 1_000:
        return f"{value/1_000:.1f}k EUR"
    else:
        return f"{value:.0f} EUR"


# =============================================================================
# PAGE PRINCIPALE
# =============================================================================

st.title("Analyse Multi-Exercices")

st.markdown("""
Cette page permet d'analyser les tendances financieres sur plusieurs exercices.
Selectionnez une entreprise et les exercices a analyser pour visualiser l'evolution
des metriques cles, detecter les anomalies et generer des predictions.
""")

st.divider()

# =============================================================================
# SECTION 1: SELECTION DES EXERCICES
# =============================================================================

st.header("Selection des donnees")

col_company, col_years = st.columns([1, 2])

with col_company:
    # Liste des entreprises
    companies = get_company_list()
    company_names = [c["name"] for c in companies]

    selected_company_name = st.selectbox(
        "Entreprise",
        options=company_names,
        index=0,
        help="Selectionnez l'entreprise a analyser"
    )

    # Recuperer l'ID de l'entreprise
    selected_company = next(
        (c for c in companies if c["name"] == selected_company_name),
        None
    )

with col_years:
    if selected_company:
        # Recuperer les exercices disponibles
        fiscal_years = get_fiscal_years_for_company(selected_company["id"])

        available_years = [fy["year"] for fy in fiscal_years]

        selected_years = st.multiselect(
            "Exercices a analyser",
            options=available_years,
            default=available_years,
            help="Selectionnez au moins 2 exercices pour l'analyse de tendances"
        )

        if len(selected_years) < 2:
            st.warning("Selectionnez au moins 2 exercices pour l'analyse de tendances.")

# Bouton pour charger les donnees de demo
st.divider()
col_demo, col_info = st.columns([1, 3])

with col_demo:
    if st.button("Charger donnees de demonstration", type="secondary"):
        demo_data = create_demo_fiscal_data()
        st.session_state["fiscal_years_data"] = demo_data
        st.session_state["selected_company_name"] = "Entreprise Demo"
        st.success("Donnees de demonstration chargees!")
        st.rerun()

with col_info:
    if "fiscal_years_data" in st.session_state:
        n_years = len(st.session_state["fiscal_years_data"])
        st.info(f"Donnees chargees: {n_years} exercices pour {st.session_state.get('selected_company_name', 'N/A')}")

st.divider()

# =============================================================================
# SECTION 2: ANALYSE DES TENDANCES
# =============================================================================

# Utiliser les donnees en session ou les donnees selectionnees
if "fiscal_years_data" in st.session_state:
    fiscal_data = st.session_state["fiscal_years_data"]
elif selected_company and len(selected_years) >= 2:
    # Filtrer les exercices selectionnes
    fiscal_data = [
        fy for fy in fiscal_years
        if fy["year"] in selected_years
    ]
else:
    fiscal_data = None

if fiscal_data and len(fiscal_data) >= 2:
    try:
        # Initialiser l'analyseur
        analyzer = TrendAnalyzer(fiscal_data)

        # Recuperer les tendances
        all_trends = analyzer.get_all_trends()

        # =================================================================
        # ONGLETS DE VISUALISATION
        # =================================================================

        tab1, tab2, tab3, tab4 = st.tabs([
            "Vue d'ensemble",
            "Metriques detaillees",
            "Predictions",
            "Anomalies"
        ])

        # =============================================================
        # ONGLET 1: VUE D'ENSEMBLE
        # =============================================================

        with tab1:
            st.subheader("Indicateurs de tendance")

            # KPIs globaux
            col1, col2, col3, col4 = st.columns(4)

            # CAGR Chiffre d'affaires
            with col1:
                if "revenues" in all_trends:
                    cagr_ca = all_trends["revenues"]["cagr"]
                    trend_ca = all_trends["revenues"]["trend"]
                    st.metric(
                        label="CAGR CA",
                        value=f"{cagr_ca:.1%}",
                        delta=format_trend_label(trend_ca),
                        help="Taux de croissance annuel compose du chiffre d'affaires"
                    )
                else:
                    st.metric(label="CAGR CA", value="N/A")

            # CAGR EBITDA
            with col2:
                if "ebitda" in all_trends:
                    cagr_ebitda = all_trends["ebitda"]["cagr"]
                    trend_ebitda = all_trends["ebitda"]["trend"]
                    st.metric(
                        label="CAGR EBITDA",
                        value=f"{cagr_ebitda:.1%}",
                        delta=format_trend_label(trend_ebitda),
                        help="Taux de croissance annuel compose de l'EBITDA"
                    )
                else:
                    st.metric(label="CAGR EBITDA", value="N/A")

            # CAGR Resultat net
            with col3:
                if "net_income" in all_trends:
                    cagr_ni = all_trends["net_income"]["cagr"]
                    trend_ni = all_trends["net_income"]["trend"]
                    st.metric(
                        label="CAGR Resultat Net",
                        value=f"{cagr_ni:.1%}",
                        delta=format_trend_label(trend_ni),
                        help="Taux de croissance annuel compose du resultat net"
                    )
                else:
                    st.metric(label="CAGR Resultat Net", value="N/A")

            # Volatilite moyenne
            with col4:
                volatilities = [t["volatility"] for t in all_trends.values() if "volatility" in t]
                avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 0
                st.metric(
                    label="Volatilite moyenne",
                    value=f"{avg_volatility:.1%}",
                    help="Coefficient de variation moyen des metriques"
                )

            st.divider()

            # Graphique d'evolution principal
            st.subheader("Evolution des metriques principales")

            chart_factory = ChartFactory()

            # Preparer les donnees pour le graphique
            years = analyzer.get_years()

            metrics_to_plot = {
                "CA (k EUR)": [v / 1000 for v in all_trends.get("revenues", {}).get("values", [])],
                "EBITDA (k EUR)": [v / 1000 for v in all_trends.get("ebitda", {}).get("values", [])],
                "Resultat Net (k EUR)": [v / 1000 for v in all_trends.get("net_income", {}).get("values", [])],
            }

            # Filtrer les metriques vides
            metrics_to_plot = {k: v for k, v in metrics_to_plot.items() if v and any(x != 0 for x in v)}

            if metrics_to_plot:
                fig_evolution = chart_factory.create_evolution_chart(
                    years=years,
                    metrics=metrics_to_plot,
                    title="Evolution du CA, EBITDA et Resultat Net",
                    show_markers=True
                )
                st.plotly_chart(fig_evolution, use_container_width=True)

            # Resume des tendances en tableau
            st.subheader("Resume des tendances")

            summary_data = []
            for metric_name, trend_data in all_trends.items():
                metric_label = TrendAnalyzer.METRIC_LABELS.get(metric_name, metric_name)
                summary_data.append({
                    "Metrique": metric_label,
                    "Tendance": format_trend_label(trend_data["trend"]),
                    "CAGR": f"{trend_data['cagr']:.1%}",
                    "Volatilite": f"{trend_data['volatility']:.1%}",
                    "Derniere valeur": format_value(trend_data["values"][-1], metric_name)
                })

            df_summary = pd.DataFrame(summary_data)
            st.dataframe(df_summary, use_container_width=True, hide_index=True)

        # =============================================================
        # ONGLET 2: METRIQUES DETAILLEES
        # =============================================================

        with tab2:
            st.subheader("Analyse detaillee par metrique")

            # Selecteur de metrique
            available_metrics = list(all_trends.keys())
            metric_labels = {m: TrendAnalyzer.METRIC_LABELS.get(m, m) for m in available_metrics}

            selected_metric = st.selectbox(
                "Selectionnez une metrique",
                options=available_metrics,
                format_func=lambda x: metric_labels[x],
                help="Choisissez la metrique a analyser en detail"
            )

            if selected_metric:
                evolution = all_trends[selected_metric]

                # Afficher les KPIs de la metrique
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "CAGR",
                        f"{evolution['cagr']:.1%}",
                        help="Taux de croissance annuel compose"
                    )

                with col2:
                    st.metric(
                        "Volatilite",
                        f"{evolution['volatility']:.1%}",
                        help="Coefficient de variation"
                    )

                with col3:
                    st.metric(
                        "Tendance",
                        format_trend_label(evolution['trend'])
                    )

                with col4:
                    first_val = evolution['values'][0]
                    last_val = evolution['values'][-1]
                    total_change = (last_val - first_val) / first_val if first_val != 0 else 0
                    st.metric(
                        "Evolution totale",
                        f"{total_change:.1%}"
                    )

                # Graphique de la metrique
                st.divider()

                metric_data = {metric_labels[selected_metric]: evolution["values"]}
                fig_metric = chart_factory.create_evolution_chart(
                    years=years,
                    metrics=metric_data,
                    title=f"Evolution: {metric_labels[selected_metric]}",
                    show_markers=True
                )
                st.plotly_chart(fig_metric, use_container_width=True)

                # Tableau des variations annuelles
                st.subheader("Variations annuelles")

                variations_data = []
                for i, year in enumerate(evolution["years"]):
                    yoy = evolution["yoy_changes"][i]
                    variations_data.append({
                        "Annee": year,
                        "Valeur": format_value(evolution["values"][i], selected_metric),
                        "Variation YoY": f"{yoy:.1%}" if yoy is not None else "-"
                    })

                df_variations = pd.DataFrame(variations_data)
                st.dataframe(df_variations, use_container_width=True, hide_index=True)

        # =============================================================
        # ONGLET 3: PREDICTIONS
        # =============================================================

        with tab3:
            st.subheader("Projections N+1")

            st.info(
                "Les predictions sont basees sur une regression lineaire simple "
                "a partir des donnees historiques. Ces projections sont indicatives "
                "et doivent etre utilisees avec prudence."
            )

            # Calculer les predictions
            predictions = analyzer.predict_all_metrics()

            if predictions:
                # Afficher sous forme de tableau comparatif
                next_year = max(years) + 1

                prediction_data = []
                for metric_name, pred_value in predictions.items():
                    if metric_name in all_trends:
                        last_value = all_trends[metric_name]["values"][-1]
                        change = (pred_value - last_value) / last_value if last_value != 0 else 0

                        prediction_data.append({
                            "Metrique": TrendAnalyzer.METRIC_LABELS.get(metric_name, metric_name),
                            f"Valeur {years[-1]}": format_value(last_value, metric_name),
                            f"Prediction {next_year}": format_value(pred_value, metric_name),
                            "Variation prevue": f"{change:.1%}"
                        })

                df_predictions = pd.DataFrame(prediction_data)
                st.dataframe(df_predictions, use_container_width=True, hide_index=True)

                # Graphique des predictions
                st.divider()
                st.subheader("Visualisation des projections")

                # Preparer les donnees avec prediction
                pred_metrics = ["revenues", "ebitda", "net_income"]
                pred_years = years + [next_year]

                for metric in pred_metrics:
                    if metric in all_trends and metric in predictions:
                        metric_label = TrendAnalyzer.METRIC_LABELS.get(metric, metric)

                        values = all_trends[metric]["values"] + [predictions[metric]]
                        values_k = [v / 1000 for v in values]

                        # Creer un graphique avec distinction prediction
                        import plotly.graph_objects as go

                        fig = go.Figure()

                        # Valeurs historiques
                        fig.add_trace(go.Scatter(
                            x=years,
                            y=[v / 1000 for v in all_trends[metric]["values"]],
                            mode="lines+markers",
                            name="Historique",
                            line=dict(color="#1f77b4", width=2),
                            marker=dict(size=8)
                        ))

                        # Prediction
                        fig.add_trace(go.Scatter(
                            x=[years[-1], next_year],
                            y=[all_trends[metric]["values"][-1] / 1000, predictions[metric] / 1000],
                            mode="lines+markers",
                            name="Prediction",
                            line=dict(color="#ff7f0e", width=2, dash="dash"),
                            marker=dict(size=8, symbol="diamond")
                        ))

                        fig.update_layout(
                            title=f"Projection {metric_label}",
                            xaxis_title="Annee",
                            yaxis_title="Valeur (k EUR)",
                            height=350,
                            showlegend=True,
                            legend=dict(orientation="h", y=1.1)
                        )

                        st.plotly_chart(fig, use_container_width=True)

            else:
                st.warning("Aucune prediction disponible.")

        # =============================================================
        # ONGLET 4: ANOMALIES
        # =============================================================

        with tab4:
            st.subheader("Detection des anomalies")

            # Curseur pour le seuil
            threshold = st.slider(
                "Seuil de detection",
                min_value=0.1,
                max_value=0.5,
                value=0.3,
                step=0.05,
                format="%.0f%%",
                help="Variations superieures a ce seuil seront signalees comme anomalies"
            )

            # Detecter les anomalies
            all_anomalies = analyzer.get_all_anomalies(threshold=threshold)

            if all_anomalies:
                total_anomalies = sum(len(a) for a in all_anomalies.values())
                st.warning(f"**{total_anomalies} anomalie(s) detectee(s)**")

                for metric_name, anomalies in all_anomalies.items():
                    metric_label = TrendAnalyzer.METRIC_LABELS.get(metric_name, metric_name)

                    for anomaly in anomalies:
                        severity = anomaly["severity"]

                        if severity == "critical":
                            st.error(f"**{anomaly['year']}**: {anomaly['message']}")
                        else:
                            st.warning(f"**{anomaly['year']}**: {anomaly['message']}")

                # Resume en tableau
                st.divider()
                st.subheader("Detail des anomalies")

                anomaly_data = []
                for metric_name, anomalies in all_anomalies.items():
                    for anomaly in anomalies:
                        anomaly_data.append({
                            "Metrique": TrendAnalyzer.METRIC_LABELS.get(metric_name, metric_name),
                            "Annee": anomaly["year"],
                            "Variation": f"{anomaly['variation']:.1%}",
                            "Severite": anomaly["severity"].capitalize(),
                            "Description": anomaly["message"]
                        })

                df_anomalies = pd.DataFrame(anomaly_data)
                st.dataframe(df_anomalies, use_container_width=True, hide_index=True)

            else:
                st.success(f"Aucune anomalie detectee avec un seuil de {threshold:.0%}")

    except ValueError as e:
        st.error(f"Erreur lors de l'analyse: {str(e)}")
    except Exception as e:
        st.error(f"Erreur inattendue: {str(e)}")

else:
    st.info(
        "Veuillez selectionner au moins 2 exercices ou charger les donnees de demonstration "
        "pour commencer l'analyse des tendances."
    )

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.header("A propos")

    st.markdown("""
    **Analyse Multi-Exercices**

    Cette page analyse les tendances financieres sur plusieurs exercices:

    - **CAGR**: Taux de croissance annuel compose
    - **Volatilite**: Mesure de la stabilite
    - **Tendance**: Direction generale (croissance, stable, decroissance)
    - **Anomalies**: Variations exceptionnelles

    Les predictions utilisent une regression lineaire simple
    et sont purement indicatives.
    """)

    st.divider()

    if "fiscal_years_data" in st.session_state:
        summary = analyzer.get_summary() if 'analyzer' in dir() else {}
        if summary:
            st.subheader("Resume")
            st.write(f"Annees: {summary.get('n_years', 0)}")
            st.write(f"Metriques: {summary.get('n_metrics', 0)}")
            st.write(f"Anomalies: {summary.get('total_anomalies', 0)}")
