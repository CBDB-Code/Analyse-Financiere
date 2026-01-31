"""
Application Streamlit principale pour l'analyse financiere.

Cette application permet de:
- Charger des donnees financieres de test
- Configurer des parametres de scenario (dette, equity, croissance)
- Calculer et visualiser les metriques financieres
- Analyser selon differentes perspectives (Banquier, Entrepreneur, Complete)

Version mise a jour avec dashboards interactifs Plotly.
"""

import sys
from pathlib import Path

# Ajoute le repertoire racine au path pour les imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from typing import Optional

# Imports des modules du projet
from src.scenarios.parameters import (
    ScenarioParameters,
    DebtParameters,
    EquityParameters,
    GrowthAssumptions,
)
from src.scenarios.engine import ScenarioEngine

# Import des metriques pour les enregistrer dans le registry
from src.calculations.banker.debt_coverage import DSCR, ICR
from src.calculations.entrepreneur.equity_returns import ROE, PaybackPeriod
from src.calculations.standard.liquidity import FondsDeRoulement, BFR
from src.calculations.standard.profitability import (
    EBITDA,
    MargeBrute,
    MargeExploitation,
    MargeNette,
)
from src.calculations.base import MetricRegistry

# Import des dashboards visualisation
from src.visualization.dashboards import (
    BankerDashboard,
    EntrepreneurDashboard,
    CompleteDashboard,
)
from src.visualization.charts import ChartFactory


# =============================================================================
# CONFIGURATION DE LA PAGE
# =============================================================================

st.set_page_config(
    page_title="Analyse Financiere",
    page_icon="💰",
    layout="wide"
)


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.title("📊 Analyse Financiere")

    st.divider()

    # Selecteur de perspective
    perspective = st.selectbox(
        "Perspective d'analyse",
        options=["Banquier", "Entrepreneur", "Complete"],
        index=2,
        help="Choisissez la perspective selon laquelle analyser les donnees"
    )

    st.divider()

    # Section A propos
    st.subheader("A propos")
    st.markdown("""
    Application d'analyse financiere permettant d'evaluer
    la sante financiere d'une entreprise selon differentes
    perspectives: banquier (risque), entrepreneur (rentabilite)
    ou analyse complete.
    """)

    st.markdown("---")
    st.caption("v1.2 - Multi-exercices & Comparaison")

    # Option pour activer les graphiques avances
    st.divider()
    use_advanced_charts = st.checkbox(
        "Graphiques avances",
        value=True,
        help="Utiliser les dashboards Plotly interactifs"
    )

    # Section Analyses Avancees
    st.divider()
    st.subheader("Analyses Avancees")

    st.page_link(
        "pages/2_Tendances.py",
        label="Tendances Multi-Exercices",
        icon="📈",
        help="Analysez les tendances sur plusieurs exercices fiscaux"
    )

    st.page_link(
        "pages/3_Comparaison.py",
        label="Comparaison Entreprises",
        icon="⚖️",
        help="Comparez plusieurs entreprises cote a cote"
    )


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def create_sample_data() -> dict:
    """
    Cree un jeu de donnees financieres factices pour les tests.

    Returns:
        dict: Dictionnaire contenant les donnees financieres de test
    """
    return {
        # Bilan - Actif
        "balance_sheet": {
            "assets": {
                "fixed_assets": {
                    "intangible_assets": 50000,
                    "tangible_assets": 300000,
                    "financial_assets": 20000,
                    "total": 370000,
                },
                "current_assets": {
                    "inventory": 150000,
                    "trade_receivables": 200000,
                    "other_receivables": 30000,
                    "prepaid_expenses": 10000,
                    "marketable_securities": 25000,
                    "cash": 100000,
                    "total": 515000,
                },
                "total_assets": 885000,
            },
            # Bilan - Passif
            "liabilities": {
                "equity": {
                    "share_capital": 200000,
                    "share_premium": 50000,
                    "legal_reserve": 20000,
                    "retained_earnings": 80000,
                    "net_income": 75000,
                    "total": 425000,
                },
                "provisions": {
                    "provisions_for_risks": 15000,
                    "provisions_for_charges": 10000,
                    "total": 25000,
                },
                "debt": {
                    "long_term_debt": 200000,
                    "short_term_debt": 50000,
                    "bank_overdrafts": 10000,
                    "total_financial_debt": 260000,
                },
                "operating_liabilities": {
                    "trade_payables": 120000,
                    "tax_liabilities": 25000,
                    "social_liabilities": 30000,
                    "advances_received": 0,
                    "deferred_revenue": 0,
                    "total": 175000,
                },
                "total_liabilities": 885000,
            },
        },
        # Compte de resultat
        "income_statement": {
            "revenues": {
                "sales_of_goods": 500000,
                "sales_of_services": 700000,
                "sales_of_products": 0,
                "net_revenue": 1200000,
                "other_operating_income": 20000,
                "total": 1220000,
            },
            "operating_expenses": {
                "purchases_of_goods": 300000,
                "purchases_of_raw_materials": 100000,
                "inventory_variation": -10000,
                "external_charges": 150000,
                "taxes_and_duties": 30000,
                "wages_and_salaries": 250000,
                "social_charges": 100000,
                "depreciation": 50000,
                "provisions": 10000,
                "other_operating_expenses": 20000,
                "total": 1000000,
            },
            "operating_income": 220000,
            "financial_result": {
                "financial_income": 5000,
                "interest_expense": 25000,
                "total_financial_income": 5000,
                "total_financial_expense": 25000,
                "net_financial_result": -20000,
            },
            "current_income_before_tax": 200000,
            "exceptional_result": {
                "total_exceptional_income": 5000,
                "total_exceptional_expense": 10000,
                "net_exceptional_result": -5000,
            },
            "income_tax_expense": 45000,
            "net_income": 75000,
        },
        # Donnees additionnelles pour le calcul des metriques
        "revenues": {
            "total": {
                "value": 1200000,
            },
        },
        "expenses": {
            "total": 1000000,
            "financial": {
                "interest_expense": {
                    "value": 25000,
                },
            },
        },
        "profitability": {
            "ebitda": {
                "value": 280000,
            },
        },
    }


def format_metric_value(value: float, unit: str) -> str:
    """
    Formate une valeur de metrique selon son unite.

    Args:
        value: La valeur a formater
        unit: L'unite de la metrique (%, euro, ratio, etc.)

    Returns:
        str: Valeur formatee
    """
    if value is None:
        return "N/A"

    if value == float("inf"):
        return "∞"

    if value == float("-inf"):
        return "-∞"

    unit_lower = unit.lower()

    if unit_lower == "%":
        return f"{value:.2f} %"
    elif unit_lower in ("euro", "eur", "euros"):
        # Format avec separateur de milliers
        formatted = f"{value:,.0f}".replace(",", " ")
        return f"{formatted} EUR"
    elif unit_lower == "ratio":
        return f"{value:.2f}"
    elif unit_lower in ("jours", "jour", "days"):
        return f"{int(round(value))} jours"
    elif unit_lower in ("fois", "x", "times"):
        return f"{value:.1f}x"
    elif unit_lower in ("annees", "ans", "years"):
        return f"{value:.1f} ans"
    else:
        return f"{value:.2f}"


def get_delta_color(value: float, benchmark_ranges: Optional[dict]) -> str:
    """
    Determine la couleur du delta selon les benchmarks.

    Args:
        value: La valeur calculee
        benchmark_ranges: Les seuils de benchmark

    Returns:
        str: 'normal', 'inverse', ou 'off' pour la couleur du delta
    """
    if benchmark_ranges is None:
        return "off"

    excellent = benchmark_ranges.get("excellent", float("inf"))
    good = benchmark_ranges.get("good", float("inf"))
    acceptable = benchmark_ranges.get("acceptable", float("inf"))
    risky = benchmark_ranges.get("risky", float("-inf"))

    # Determine si plus haut = mieux
    higher_is_better = excellent >= risky

    if higher_is_better:
        if value >= good:
            return "normal"  # Vert
        elif value >= acceptable:
            return "off"     # Neutre
        else:
            return "inverse"  # Rouge
    else:
        # Plus bas = mieux (ex: payback period)
        if value <= good:
            return "normal"
        elif value <= acceptable:
            return "off"
        else:
            return "inverse"


def get_rating_emoji(value: float, benchmark_ranges: Optional[dict]) -> str:
    """
    Retourne un emoji selon le rating.

    Args:
        value: La valeur calculee
        benchmark_ranges: Les seuils de benchmark

    Returns:
        str: Emoji correspondant au rating
    """
    if benchmark_ranges is None:
        return ""

    excellent = benchmark_ranges.get("excellent", float("inf"))
    good = benchmark_ranges.get("good", float("inf"))
    acceptable = benchmark_ranges.get("acceptable", float("inf"))
    risky = benchmark_ranges.get("risky", float("-inf"))

    higher_is_better = excellent >= risky

    if higher_is_better:
        if value >= excellent:
            return "🟢"
        elif value >= good:
            return "🟡"
        elif value >= acceptable:
            return "🟠"
        else:
            return "🔴"
    else:
        if value <= excellent:
            return "🟢"
        elif value <= good:
            return "🟡"
        elif value <= acceptable:
            return "🟠"
        else:
            return "🔴"


# =============================================================================
# PAGE PRINCIPALE
# =============================================================================

st.title("Analyse Financiere")
st.markdown("""
Bienvenue dans l'outil d'analyse financiere. Cette application vous permet d'evaluer
la sante financiere d'une entreprise en calculant des metriques cles selon la perspective
choisie (Banquier, Entrepreneur ou Complete).
""")

st.divider()

# =============================================================================
# SECTION: DONNEES DE TEST
# =============================================================================

st.header("📁 Donnees de test")

col1, col2 = st.columns([1, 3])

with col1:
    if st.button("Charger exemple de donnees", type="primary"):
        st.session_state["financial_data"] = create_sample_data()
        st.success("Donnees de test chargees avec succes!")

with col2:
    if "financial_data" in st.session_state:
        st.info("Donnees financieres chargees et pretes pour l'analyse.")
    else:
        st.warning("Aucune donnee chargee. Cliquez sur le bouton pour charger les donnees de test.")

# Affichage des donnees chargees (optionnel)
if "financial_data" in st.session_state:
    with st.expander("Voir les donnees chargees"):
        st.json(st.session_state["financial_data"])

st.divider()

# =============================================================================
# SECTION: PARAMETRES DU SCENARIO
# =============================================================================

st.header("⚙️ Parametres du scenario")

col_debt, col_equity, col_growth = st.columns(3)

with col_debt:
    st.subheader("Dette")

    debt_amount = st.slider(
        "Montant dette",
        min_value=0,
        max_value=10_000_000,
        value=500_000,
        step=100_000,
        format="%d EUR",
        help="Montant total de la dette a contracter"
    )

    interest_rate = st.slider(
        "Taux d'interet",
        min_value=1.0,
        max_value=15.0,
        value=5.0,
        step=0.1,
        format="%.1f%%",
        help="Taux d'interet annuel de la dette"
    )

    loan_duration = st.slider(
        "Duree pret",
        min_value=1,
        max_value=30,
        value=7,
        step=1,
        format="%d ans",
        help="Duree du pret en annees"
    )

with col_equity:
    st.subheader("Equity")

    equity_amount = st.slider(
        "Montant equity",
        min_value=0,
        max_value=10_000_000,
        value=500_000,
        step=100_000,
        format="%d EUR",
        help="Montant des capitaux propres investis"
    )

    target_roe = st.slider(
        "ROE cible",
        min_value=5.0,
        max_value=30.0,
        value=12.0,
        step=0.5,
        format="%.1f%%",
        help="Rendement des capitaux propres cible"
    )

with col_growth:
    st.subheader("Croissance")

    revenue_growth = st.slider(
        "Croissance CA annuelle",
        min_value=-20,
        max_value=50,
        value=5,
        step=1,
        format="%d%%",
        help="Taux de croissance annuel du chiffre d'affaires"
    )

    ebitda_margin_evolution = st.slider(
        "Evolution marge EBITDA",
        min_value=-10,
        max_value=10,
        value=0,
        step=1,
        format="%d pts",
        help="Evolution annuelle de la marge EBITDA en points"
    )

st.divider()

# =============================================================================
# SECTION: CALCUL DES METRIQUES
# =============================================================================

st.header("📊 Calcul des metriques")

if "financial_data" not in st.session_state:
    st.warning("Veuillez d'abord charger des donnees financieres.")
else:
    if st.button("Calculer les metriques", type="primary"):
        try:
            # Creation des parametres du scenario
            scenario_params = ScenarioParameters(
                name="Scenario personnalise",
                debt=DebtParameters(
                    debt_amount=float(debt_amount),
                    interest_rate=interest_rate / 100,  # Conversion en decimal
                    loan_duration=loan_duration,
                    grace_period=0,
                    amortization_type="constant"
                ),
                equity=EquityParameters(
                    equity_amount=float(equity_amount),
                    target_roe=target_roe / 100,  # Conversion en decimal
                    exit_multiple=6.0,
                    holding_period=5
                ),
                growth=GrowthAssumptions(
                    revenue_growth=revenue_growth / 100,  # Conversion en decimal
                    ebitda_margin_evolution=ebitda_margin_evolution / 100,
                    capex_percentage=0.03,
                    inflation_rate=0.02
                )
            )

            # Initialisation du moteur de scenario
            engine = ScenarioEngine(st.session_state["financial_data"])

            # Application du scenario
            scenario_data = engine.apply_scenario(scenario_params)

            # Calcul de toutes les metriques
            metrics_results = engine.calculate_all_metrics(scenario_data)

            # Stockage des resultats en session
            st.session_state["scenario_data"] = scenario_data
            st.session_state["metrics_results"] = metrics_results

            st.success("Metriques calculees avec succes!")

        except Exception as e:
            st.error(f"Erreur lors du calcul: {str(e)}")

# =============================================================================
# SECTION: AFFICHAGE DES RESULTATS
# =============================================================================

if "metrics_results" in st.session_state:
    st.divider()
    st.header("Resultats de l'analyse")

    metrics_results = st.session_state["metrics_results"]
    scenario_data = st.session_state["scenario_data"]

    # Verifier si on utilise les graphiques avances
    if use_advanced_charts:
        # =====================================================================
        # MODE DASHBOARD AVANCE (Plotly)
        # =====================================================================

        # Affichage selon la perspective avec dashboards
        if perspective == "Banquier":
            dashboard = BankerDashboard()
            dashboard.render(scenario_data, metrics_results)

        elif perspective == "Entrepreneur":
            dashboard = EntrepreneurDashboard()
            dashboard.render(scenario_data, metrics_results)

        else:  # Complete
            dashboard = CompleteDashboard()
            dashboard.render(scenario_data, metrics_results)

    else:
        # =====================================================================
        # MODE CLASSIQUE (Metriques simples)
        # =====================================================================

        # Recuperation de toutes les metriques enregistrees
        all_metrics = MetricRegistry.get_all_metrics()

        # Classification des metriques par categorie
        banker_metrics = []
        entrepreneur_metrics = []
        standard_metrics = []

        for metric_class in all_metrics:
            try:
                metric_instance = metric_class()
                category = metric_instance.metadata.category.value

                if category == "banker":
                    banker_metrics.append(metric_instance)
                elif category == "entrepreneur":
                    entrepreneur_metrics.append(metric_instance)
                else:
                    standard_metrics.append(metric_instance)
            except Exception:
                continue

        # Affichage selon la perspective
        if perspective == "Banquier":
            st.subheader("Perspective Banquier")

            if banker_metrics:
                cols = st.columns(len(banker_metrics))
                for idx, metric in enumerate(banker_metrics):
                    with cols[idx]:
                        metric_name = metric.metadata.name
                        value = metrics_results.get(metric_name, None)
                        formatted_value = format_metric_value(value, metric.metadata.unit)
                        interpretation = metric.get_interpretation(value) if value is not None else ""

                        # Emoji selon le rating
                        emoji = get_rating_emoji(value, metric.metadata.benchmark_ranges) if value else ""

                        st.metric(
                            label=f"{emoji} {metric.metadata.description[:30]}...",
                            value=formatted_value,
                            help=interpretation
                        )

            # Afficher aussi les metriques standard
            st.subheader("Metriques standard")
            if standard_metrics:
                cols = st.columns(min(4, len(standard_metrics)))
                for idx, metric in enumerate(standard_metrics):
                    with cols[idx % len(cols)]:
                        metric_name = metric.metadata.name
                        value = metrics_results.get(metric_name, None)
                        formatted_value = format_metric_value(value, metric.metadata.unit)

                        emoji = get_rating_emoji(value, metric.metadata.benchmark_ranges) if value else ""

                        st.metric(
                            label=f"{emoji} {metric.metadata.description[:25]}...",
                            value=formatted_value,
                            help=metric.metadata.interpretation
                        )

        elif perspective == "Entrepreneur":
            st.subheader("Perspective Entrepreneur")

            if entrepreneur_metrics:
                cols = st.columns(len(entrepreneur_metrics))
                for idx, metric in enumerate(entrepreneur_metrics):
                    with cols[idx]:
                        metric_name = metric.metadata.name
                        value = metrics_results.get(metric_name, None)
                        formatted_value = format_metric_value(value, metric.metadata.unit)
                        interpretation = metric.get_interpretation(value) if value is not None else ""

                        emoji = get_rating_emoji(value, metric.metadata.benchmark_ranges) if value else ""

                        st.metric(
                            label=f"{emoji} {metric.metadata.description[:30]}...",
                            value=formatted_value,
                            help=interpretation
                        )

            # Afficher aussi les metriques standard
            st.subheader("Metriques standard")
            if standard_metrics:
                cols = st.columns(min(4, len(standard_metrics)))
                for idx, metric in enumerate(standard_metrics):
                    with cols[idx % len(cols)]:
                        metric_name = metric.metadata.name
                        value = metrics_results.get(metric_name, None)
                        formatted_value = format_metric_value(value, metric.metadata.unit)

                        emoji = get_rating_emoji(value, metric.metadata.benchmark_ranges) if value else ""

                        st.metric(
                            label=f"{emoji} {metric.metadata.description[:25]}...",
                            value=formatted_value,
                            help=metric.metadata.interpretation
                        )

        else:  # Complete
            st.subheader("Perspective Banquier")
            if banker_metrics:
                cols = st.columns(len(banker_metrics))
                for idx, metric in enumerate(banker_metrics):
                    with cols[idx]:
                        metric_name = metric.metadata.name
                        value = metrics_results.get(metric_name, None)
                        formatted_value = format_metric_value(value, metric.metadata.unit)
                        interpretation = metric.get_interpretation(value) if value is not None else ""

                        emoji = get_rating_emoji(value, metric.metadata.benchmark_ranges) if value else ""

                        st.metric(
                            label=f"{emoji} {metric.metadata.description[:30]}...",
                            value=formatted_value,
                            help=interpretation
                        )

            st.subheader("Perspective Entrepreneur")
            if entrepreneur_metrics:
                cols = st.columns(len(entrepreneur_metrics))
                for idx, metric in enumerate(entrepreneur_metrics):
                    with cols[idx]:
                        metric_name = metric.metadata.name
                        value = metrics_results.get(metric_name, None)
                        formatted_value = format_metric_value(value, metric.metadata.unit)
                        interpretation = metric.get_interpretation(value) if value is not None else ""

                        emoji = get_rating_emoji(value, metric.metadata.benchmark_ranges) if value else ""

                        st.metric(
                            label=f"{emoji} {metric.metadata.description[:30]}...",
                            value=formatted_value,
                            help=interpretation
                        )

            st.subheader("Metriques standard")
            if standard_metrics:
                cols = st.columns(min(4, len(standard_metrics)))
                for idx, metric in enumerate(standard_metrics):
                    with cols[idx % len(cols)]:
                        metric_name = metric.metadata.name
                        value = metrics_results.get(metric_name, None)
                        formatted_value = format_metric_value(value, metric.metadata.unit)

                        emoji = get_rating_emoji(value, metric.metadata.benchmark_ranges) if value else ""

                        st.metric(
                            label=f"{emoji} {metric.metadata.description[:25]}...",
                            value=formatted_value,
                            help=metric.metadata.interpretation
                        )

    # =========================================================================
    # RESUME DU SCENARIO (commun aux deux modes)
    # =========================================================================
    st.divider()
    st.subheader("Resume du scenario")

    scenario_info = scenario_data.get("scenario", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Financement total",
            value=f"{scenario_info.get('total_financing', 0):,.0f} EUR".replace(",", " ")
        )

    with col2:
        leverage = scenario_info.get('leverage_ratio', 0)
        st.metric(
            label="Ratio de levier",
            value=f"{leverage:.1%}"
        )

    with col3:
        d_to_e = scenario_info.get('debt_to_equity', 0)
        if d_to_e == float('inf'):
            d_to_e_str = "inf"
        else:
            d_to_e_str = f"{d_to_e:.2f}"
        st.metric(
            label="Ratio D/E",
            value=d_to_e_str
        )

    with col4:
        annual_service = scenario_info.get('annual_debt_service', 0)
        st.metric(
            label="Service dette annuel",
            value=f"{annual_service:,.0f} EUR".replace(",", " ")
        )

    # =========================================================================
    # SECTION GRAPHIQUES SUPPLEMENTAIRES (si mode avance)
    # =========================================================================
    if use_advanced_charts:
        st.divider()
        st.subheader("Visualisations Avancees")

        chart_factory = ChartFactory()

        # Onglets pour differents graphiques
        tab_sensitivity, tab_evolution = st.tabs([
            "Analyse de Sensibilite",
            "Evolution (simulation)"
        ])

        with tab_sensitivity:
            st.markdown("**Impact du taux d'interet sur le DSCR**")

            # Simuler une analyse de sensibilite
            interest_rates = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
            base_dscr = metrics_results.get("DSCR", 1.5)

            if base_dscr and base_dscr != float('inf'):
                # Simulation simplifiee
                dscr_values = [base_dscr * (1 + (5 - r) * 0.05) for r in interest_rates]
                icr_values = [base_dscr * (1 + (5 - r) * 0.08) for r in interest_rates]

                fig = chart_factory.create_sensitivity_analysis(
                    param_name="Taux d'interet (%)",
                    param_range=interest_rates,
                    metric_results={
                        "DSCR": dscr_values,
                        "ICR (simule)": icr_values
                    },
                    base_value=interest_rate,
                    title="Sensibilite au Taux d'Interet"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("DSCR non disponible pour l'analyse de sensibilite")

        with tab_evolution:
            st.markdown("**Projection sur 5 ans (simulation)**")

            # Simuler une evolution
            years = ["N", "N+1", "N+2", "N+3", "N+4"]
            ca_base = scenario_data.get("revenues", {}).get("total", {}).get("value", 1000000)

            if ca_base:
                growth = revenue_growth / 100
                ca_values = [ca_base * (1 + growth) ** i / 1000000 for i in range(5)]
                ebitda_base = scenario_data.get("profitability", {}).get("ebitda", {}).get("value", 200000)
                ebitda_values = [ebitda_base * (1 + growth * 0.8) ** i / 1000 for i in range(5)]

                fig = chart_factory.create_evolution_chart(
                    years=years,
                    metrics={
                        "CA (M EUR)": ca_values,
                        "EBITDA (k EUR)": ebitda_values
                    },
                    title="Projection Financiere",
                    show_markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Donnees insuffisantes pour la projection")
