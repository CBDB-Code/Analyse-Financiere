"""
Tab 2 Enhanced - Montage LBO avec visualisations avancées.

Nouvelles fonctionnalités:
- Indicateurs visuels de risque sur les sliders
- Graphique projection DSCR 7 ans
- Panneau impact changements
- Tooltips contextuels
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Tuple

from src.ui.utils.formatting import (
    format_number,
    format_percentage,
    format_ratio,
    format_currency_compact,
)
from src.core.models_v3 import DebtLayer, LBOStructure
from src.calculations.covenant_tracker import CovenantTracker


def create_risk_zone_indicator(value_pct: float, thresholds: Dict[str, Tuple[float, float]]) -> str:
    """
    Créer indicateur visuel de zone de risque.

    Args:
        value_pct: Valeur actuelle en %
        thresholds: Dict{"zone_name": (min, max)}

    Returns:
        HTML avec indicateur coloré
    """
    if "green" in thresholds and thresholds["green"][0] <= value_pct <= thresholds["green"][1]:
        color = "#28a745"
        zone = "Zone sûre"
    elif "orange" in thresholds and thresholds["orange"][0] <= value_pct <= thresholds["orange"][1]:
        color = "#ffc107"
        zone = "Attention"
    else:
        color = "#dc3545"
        zone = "Risque élevé"

    return f'<span style="color: {color}; font-weight: bold;">● {zone}</span>'


def render_slider_with_zones(
    label: str,
    value: float,
    min_val: float,
    max_val: float,
    key: str,
    thresholds: Dict[str, Tuple[float, float]],
    help_text: str = None
) -> float:
    """
    Render slider avec zones colorées visuelles.

    Args:
        label: Label du slider
        value: Valeur par défaut
        min_val: Min
        max_val: Max
        key: Clé unique
        thresholds: Zones de risque
        help_text: Texte d'aide

    Returns:
        Valeur sélectionnée
    """
    # Slider standard
    selected_value = st.slider(
        label,
        min_value=int(min_val),
        max_value=int(max_val),
        value=int(value),
        step=5,
        key=key,
        help=help_text
    )

    # Indicateur zone
    risk_html = create_risk_zone_indicator(selected_value, thresholds)
    st.markdown(risk_html, unsafe_allow_html=True)

    return selected_value


def create_dscr_projection_chart(
    lbo_structure: Dict,
    norm_data: Dict,
    financial_data: Dict
) -> go.Figure:
    """
    Créer graphique projection DSCR sur 7 ans avec zones colorées.

    Args:
        lbo_structure: Structure LBO
        norm_data: Données normalisées
        financial_data: Données financières

    Returns:
        Figure Plotly
    """
    # Hypothèses projection
    assumptions_dict = {
        "revenue_growth_rate": [0.05, 0.05, 0.03, 0.03, 0.02, 0.02, 0.02],
        "ebitda_margin_evolution": [0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
        "tax_rate": 0.25,
        "bfr_percentage_of_revenue": 18.0,
        "capex_maintenance_pct": 3.0
    }

    # Générer projections
    projections = CovenantTracker.generate_projections(
        financial_data,
        lbo_structure,
        norm_data,
        assumptions_dict,
        projection_years=7
    )

    # Extraire DSCR par année
    years = [f"Y{i+1}" for i in range(7)]
    dscr_values = [proj.get("dscr", 0) for proj in projections]

    # Créer figure
    fig = go.Figure()

    # Zone rouge (< 1.25)
    fig.add_hrect(
        y0=0, y1=1.25,
        fillcolor="red", opacity=0.1,
        line_width=0,
        annotation_text="Risque",
        annotation_position="left"
    )

    # Zone orange (1.25 - 1.5)
    fig.add_hrect(
        y0=1.25, y1=1.5,
        fillcolor="orange", opacity=0.1,
        line_width=0,
        annotation_text="Attention",
        annotation_position="left"
    )

    # Zone verte (> 1.5)
    fig.add_hrect(
        y0=1.5, y1=max(dscr_values + [2.0]) * 1.1,
        fillcolor="green", opacity=0.1,
        line_width=0,
        annotation_text="Sûr",
        annotation_position="left"
    )

    # Ligne covenant minimum
    fig.add_hline(
        y=1.25,
        line_dash="dash",
        line_color="red",
        annotation_text="Covenant min (1.25)",
        annotation_position="top right"
    )

    # Ligne DSCR projetée
    fig.add_trace(go.Scatter(
        x=years,
        y=dscr_values,
        mode="lines+markers",
        name="DSCR projeté",
        line=dict(width=3, color="#2E86DE"),
        marker=dict(size=10, color="#2E86DE"),
        hovertemplate="Année %{x}<br>DSCR: %{y:.2f}<extra></extra>"
    ))

    fig.update_layout(
        title="Projection DSCR sur 7 ans",
        xaxis_title="Année",
        yaxis_title="DSCR",
        height=350,
        showlegend=False,
        hovermode="x unified"
    )

    return fig


def create_impact_panel(
    current_params: Dict,
    previous_params: Dict
) -> None:
    """
    Panneau montrant l'impact des changements de paramètres.

    Args:
        current_params: Paramètres actuels
        previous_params: Paramètres précédents
    """
    st.markdown("### 📊 Impact Changements")

    # Détecter changements
    changes = []

    for key in current_params:
        if key in previous_params and current_params[key] != previous_params[key]:
            changes.append({
                "param": key,
                "avant": previous_params[key],
                "après": current_params[key],
                "delta": current_params[key] - previous_params[key]
            })

    if not changes:
        st.info("Aucun changement détecté")
        return

    # Afficher tableau changements
    for change in changes:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

        with col1:
            st.write(f"**{change['param']}**")
        with col2:
            st.write(f"{change['avant']:.1f}")
        with col3:
            delta_sign = "+" if change['delta'] >= 0 else ""
            st.write(f"→ {change['après']:.1f} ({delta_sign}{change['delta']:.1f})")
        with col4:
            if abs(change['delta']) > 10:
                st.markdown("🔴")
            elif abs(change['delta']) > 5:
                st.markdown("🟡")
            else:
                st.markdown("🟢")


def render_tab2_enhanced(
    norm_data,
    financial_data: Dict
) -> None:
    """
    Render Tab 2 avec fonctionnalités avancées.

    Args:
        norm_data: Données normalisées
        financial_data: Données financières
    """
    st.header("🔧 Montage LBO - Plan de Financement")

    st.markdown(f"""
    **EBITDA normalisé**: {format_number(norm_data.ebitda_bank)}
    Construisez votre plan de financement et visualisez l'impact en temps réel.
    """)

    st.divider()

    # Layout principal
    col_left, col_right = st.columns([1, 1])

    # =========================================================================
    # COLONNE GAUCHE: PARAMÈTRES AVEC ZONES VISUELLES
    # =========================================================================
    with col_left:
        st.subheader("⚙️ Paramètres")

        # Prix acquisition
        acquisition_price = st.number_input(
            "💰 Prix d'acquisition",
            min_value=1_000_000,
            max_value=20_000_000,
            value=5_000_000,
            step=100_000,
            help="Prix d'achat de l'entreprise"
        )
        st.caption(f"**{format_number(acquisition_price)}**")

        st.divider()

        # Dette senior avec zones
        st.markdown("**Dette Senior**")

        dette_senior_pct = render_slider_with_zones(
            label="% du prix",
            value=60,
            min_val=0,
            max_val=100,
            key="dette_senior_pct_v2",
            thresholds={
                "green": (40, 60),
                "orange": (60, 70),
                "red": (70, 100)
            },
            help_text="Zone verte: 40-60% | Zone orange: 60-70% | Zone rouge: >70%"
        )

        dette_senior = acquisition_price * dette_senior_pct / 100
        st.caption(f"Montant: {format_number(dette_senior)}")

        taux_senior = st.slider(
            "Taux senior",
            min_value=1.0,
            max_value=10.0,
            value=4.5,
            step=0.1,
            format="%.1f%%",
            key="taux_senior_v2"
        )

        duree_senior = st.slider(
            "Durée senior",
            min_value=3,
            max_value=15,
            value=7,
            step=1,
            format="%d ans",
            key="duree_senior_v2"
        )

        st.divider()

        # Bpifrance
        use_bpifrance = st.checkbox("Activer Bpifrance", value=True, key="use_bpi_v2")
        if use_bpifrance:
            dette_bpi_pct = st.slider(
                "Bpifrance (%)",
                min_value=0,
                max_value=20,
                value=10,
                step=5,
                key="bpi_pct_v2"
            )
            dette_bpi = acquisition_price * dette_bpi_pct / 100
            st.caption(f"Montant: {format_number(dette_bpi)}")

            taux_bpi = st.slider(
                "Taux Bpifrance",
                min_value=1.0,
                max_value=7.0,
                value=3.0,
                step=0.1,
                format="%.1f%%",
                key="taux_bpi_v2"
            )
        else:
            dette_bpi = 0
            dette_bpi_pct = 0
            taux_bpi = 0

        st.divider()

        # Crédit vendeur
        use_vendor = st.checkbox("Activer Crédit Vendeur", value=True, key="use_vendor_v2")
        if use_vendor:
            dette_vendor_pct = st.slider(
                "Crédit vendeur (%)",
                min_value=0,
                max_value=30,
                value=15,
                step=5,
                key="vendor_pct_v2"
            )
            dette_vendor = acquisition_price * dette_vendor_pct / 100
            st.caption(f"Montant: {format_number(dette_vendor)}")
        else:
            dette_vendor = 0
            dette_vendor_pct = 0

        st.divider()

        # Equity
        total_dette = dette_senior + dette_bpi + dette_vendor
        equity = acquisition_price - total_dette

        st.markdown("**💼 Equity**")
        st.metric("Montant equity", format_number(equity))
        equity_pct = (equity / acquisition_price * 100) if acquisition_price > 0 else 0

        # Indicateur equity
        if equity_pct >= 30:
            equity_color = "green"
            equity_status = "🟢 Fort"
        elif equity_pct >= 20:
            equity_color = "orange"
            equity_status = "🟡 Standard"
        else:
            equity_color = "red"
            equity_status = "🔴 Faible"

        st.markdown(f":{equity_color}[{equity_pct:.1f}% du prix - {equity_status}]")

        entrepreneur_pct = st.slider(
            "Part entrepreneur (%)",
            min_value=0,
            max_value=100,
            value=70,
            step=5,
            key="entrepreneur_v2"
        )

    # =========================================================================
    # COLONNE DROITE: VISUALISATIONS AVANCÉES
    # =========================================================================
    with col_right:
        st.subheader("📈 Visualisations")

        # Structure financement (Donut amélioré)
        structure_fig = go.Figure(data=[go.Pie(
            labels=["Dette senior", "Bpifrance", "Crédit vendeur", "Equity"],
            values=[dette_senior, dette_bpi, dette_vendor, equity],
            hole=0.5,
            marker=dict(colors=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]),
            textinfo='label+percent',
            textfont_size=12
        )])

        structure_fig.update_layout(
            title="Structure de Financement",
            height=300,
            showlegend=False
        )

        st.plotly_chart(structure_fig, use_container_width=True)

        # KPIs principaux
        st.markdown("**🎯 Métriques Clés**")

        # Calculs
        annual_service = (dette_senior + dette_bpi) * 0.15
        dscr_approx = (norm_data.ebitda_bank / annual_service) if annual_service > 0 else float('inf')
        dette_ebitda = (total_dette / norm_data.ebitda_bank) if norm_data.ebitda_bank > 0 else 0
        ca = financial_data.get("income_statement", {}).get("revenues", {}).get("net_revenue", 1)
        marge = (norm_data.ebitda_bank / ca * 100) if ca > 0 else 0

        col1, col2, col3 = st.columns(3)

        with col1:
            dscr_icon = "🟢" if dscr_approx > 1.5 else "🟡" if dscr_approx > 1.25 else "🔴"
            st.metric(
                f"{dscr_icon} DSCR",
                format_ratio(dscr_approx),
                help="Seuil: >1.25"
            )

        with col2:
            dette_icon = "🟢" if dette_ebitda < 3.5 else "🟡" if dette_ebitda < 4.5 else "🔴"
            st.metric(
                f"{dette_icon} Dette/EBITDA",
                format_ratio(dette_ebitda) + "x",
                help="Seuil: <4x"
            )

        with col3:
            marge_icon = "🟢" if marge > 15 else "🟡" if marge > 10 else "🔴"
            st.metric(
                f"{marge_icon} Marge",
                format_percentage(marge),
                help="Seuil: >15%"
            )

    # =========================================================================
    # SECTION PROJECTION DSCR (PLEINE LARGEUR)
    # =========================================================================
    st.divider()
    st.subheader("📊 Projection DSCR 7 ans")

    # Préparer structure LBO pour projection
    lbo_dict = {
        "debt_layers": [
            {
                "name": "Dette senior",
                "amount": dette_senior,
                "interest_rate": taux_senior / 100,
                "duration_years": duree_senior
            }
        ]
    }

    if use_bpifrance and dette_bpi > 0:
        lbo_dict["debt_layers"].append({
            "name": "Bpifrance",
            "amount": dette_bpi,
            "interest_rate": taux_bpi / 100,
            "duration_years": 8
        })

    norm_dict = {
        "ebitda_bank": norm_data.ebitda_bank,
        "ebitda_equity": norm_data.ebitda_equity
    }

    # Générer et afficher projection
    dscr_fig = create_dscr_projection_chart(lbo_dict, norm_dict, financial_data)
    st.plotly_chart(dscr_fig, use_container_width=True)

    # =========================================================================
    # PANNEAU IMPACT CHANGEMENTS
    # =========================================================================
    with st.expander("📊 Impact des Changements", expanded=False):
        current_params = {
            "Dette senior (%)": dette_senior_pct,
            "Taux senior (%)": taux_senior,
            "Bpifrance (%)": dette_bpi_pct if use_bpifrance else 0,
            "Crédit vendeur (%)": dette_vendor_pct if use_vendor else 0,
            "DSCR": dscr_approx,
            "Dette/EBITDA": dette_ebitda
        }

        if "previous_params_tab2" not in st.session_state:
            st.session_state.previous_params_tab2 = current_params

        create_impact_panel(current_params, st.session_state.previous_params_tab2)

        if st.button("📌 Enregistrer État Actuel"):
            st.session_state.previous_params_tab2 = current_params.copy()
            st.success("✅ État enregistré!")

    # =========================================================================
    # VALIDATION
    # =========================================================================
    st.divider()

    # Décision préliminaire
    score = 0
    if dscr_approx > 1.5:
        score += 25
    elif dscr_approx > 1.25:
        score += 15

    if dette_ebitda < 3.5:
        score += 25
    elif dette_ebitda < 4.5:
        score += 15

    if marge > 15:
        score += 25
    elif marge > 10:
        score += 15

    if equity_pct > 25:
        score += 25
    elif equity_pct > 15:
        score += 15

    if score >= 80:
        decision_prelim = "🟢 GO"
        decision_color = "green"
    elif score >= 60:
        decision_prelim = "🟡 WATCH"
        decision_color = "orange"
    else:
        decision_prelim = "🔴 NO-GO"
        decision_color = "red"

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"### Décision Préliminaire")
        st.markdown(f"## :{decision_color}[{decision_prelim}]")
        st.caption(f"Score: {score}/100")

    with col2:
        if st.button("✅ Valider Montage", type="primary", use_container_width=True):
            # Sauvegarder structure LBO
            debt_layers = [
                DebtLayer(
                    name="Dette senior",
                    amount=dette_senior,
                    interest_rate=taux_senior / 100,
                    duration_years=duree_senior
                )
            ]
            if use_bpifrance and dette_bpi > 0:
                debt_layers.append(
                    DebtLayer(
                        name="Bpifrance",
                        amount=dette_bpi,
                        interest_rate=taux_bpi / 100,
                        duration_years=8
                    )
                )
            if use_vendor and dette_vendor > 0:
                debt_layers.append(
                    DebtLayer(
                        name="Crédit vendeur",
                        amount=dette_vendor,
                        interest_rate=0.0,
                        duration_years=5,
                        grace_period=2
                    )
                )

            lbo = LBOStructure(
                acquisition_price=acquisition_price,
                debt_layers=debt_layers,
                equity_amount=equity,
                equity_split={"entrepreneur": entrepreneur_pct / 100, "investors": (100 - entrepreneur_pct) / 100}
            )

            st.session_state.lbo_structure = lbo
            st.success("✅ Montage LBO validé! Passez à l'onglet 3: Viabilité →")
            st.toast("🎉 Montage enregistré!", icon="✅")
