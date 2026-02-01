"""
Dashboard de comparaison multi-dossiers.

Permet de comparer plusieurs entreprises/deals analysés côte à côte
pour faciliter la sélection d'opportunités d'investissement.
"""

import streamlit as st
from typing import Dict, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from src.persistence.variant_manager import VariantManager, VariantStatus
from src.ui.utils.formatting import (
    format_number,
    format_percentage,
    format_ratio
)


def render_multi_deal_selector() -> List[str]:
    """
    Sélecteur de dossiers à comparer.

    Returns:
        Liste IDs variantes sélectionnées
    """
    st.subheader("📂 Sélection Dossiers")

    manager = VariantManager()

    # Filtres
    col1, col2 = st.columns(2)

    with col1:
        filter_status = st.multiselect(
            "Statuts",
            options=[s.value for s in VariantStatus],
            default=[VariantStatus.VALIDATED.value],
            format_func=lambda x: {
                "draft": "🟡 Brouillon",
                "validated": "🟢 Validé",
                "rejected": "🔴 Rejeté",
                "archived": "⚫ Archivé"
            }[x]
        )

    with col2:
        # Liste entreprises uniques
        all_variants = manager.list_variants()
        companies = list(set(v.company_name for v in all_variants))
        companies.sort()

        filter_companies = st.multiselect(
            "Entreprises",
            options=companies,
            default=companies[:min(3, len(companies))]
        )

    # Charger variantes filtrées
    variants = []
    for company in filter_companies:
        for status in filter_status:
            variants.extend(
                manager.list_variants(
                    company_name=company,
                    status=VariantStatus(status)
                )
            )

    if not variants:
        st.info("ℹ️ Aucun dossier correspondant aux filtres")
        return []

    # Sélection variantes
    st.markdown(f"**{len(variants)} dossier(s) disponible(s)**")

    selected_ids = []

    for variant in variants[:10]:  # Limiter à 10 pour performance
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.markdown(f"**{variant.company_name}**")
            st.caption(variant.name)

        with col2:
            decision_val = "N/A"
            score = 0
            if variant.decision:
                decision_val = variant.decision.get("decision", {}).get("value", "N/A")
                score = variant.decision.get("overall_score", 0)

            decision_icon = {"GO": "🟢", "WATCH": "🟡", "NO-GO": "🔴"}.get(decision_val, "⚪")
            st.caption(f"{decision_icon} {decision_val} ({score}/100)")

        with col3:
            dscr = variant.metrics.get("dscr_min", 0)
            st.caption(f"DSCR: {format_ratio(dscr)}")

        with col4:
            if st.checkbox("", key=f"select_{variant.id}", value=(len(selected_ids) < 5)):
                selected_ids.append(variant.id)

    if len(selected_ids) > 10:
        st.warning("⚠️ Maximum 10 dossiers sélectionnables")
        selected_ids = selected_ids[:10]

    st.info(f"📊 {len(selected_ids)} dossier(s) sélectionné(s)")

    return selected_ids


def render_metrics_comparison(variant_ids: List[str]) -> None:
    """
    Afficher tableau comparatif des métriques.

    Args:
        variant_ids: IDs des variantes à comparer
    """
    st.subheader("📊 Comparaison Métriques Clés")

    manager = VariantManager()

    # Charger variantes
    variants = [manager.load_variant(vid) for vid in variant_ids]
    variants = [v for v in variants if v is not None]

    if not variants:
        st.error("❌ Aucun dossier chargé")
        return

    # Préparer données tableau
    table_data = []

    for variant in variants:
        metrics = variant.metrics
        decision = variant.decision or {}

        row = {
            "Entreprise": variant.company_name,
            "Variante": variant.name,
            "Décision": decision.get("decision", {}).get("value", "N/A"),
            "Score": f"{decision.get('overall_score', 0)}/100",
            "DSCR": format_ratio(metrics.get("dscr_min", 0)),
            "Dette/EBITDA": f"{metrics.get('leverage', 0):.2f}x",
            "Marge %": f"{metrics.get('margin', 0):.1f}%",
            "Equity %": f"{metrics.get('equity_pct', 0):.1f}%",
            "FCF Y3": format_number(metrics.get("fcf_year3", 0))
        }
        table_data.append(row)

    # Afficher tableau
    st.table(table_data)

    # Métriques agrégées
    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    dscr_values = [v.metrics.get("dscr_min", 0) for v in variants]
    leverage_values = [v.metrics.get("leverage", 0) for v in variants]
    margin_values = [v.metrics.get("margin", 0) for v in variants]
    scores = [v.decision.get("overall_score", 0) if v.decision else 0 for v in variants]

    with col1:
        st.metric(
            "DSCR Moyen",
            f"{sum(dscr_values)/len(dscr_values):.2f}",
            delta=f"Max: {max(dscr_values):.2f}",
            help="Plus élevé = meilleur"
        )

    with col2:
        st.metric(
            "Leverage Moyen",
            f"{sum(leverage_values)/len(leverage_values):.2f}x",
            delta=f"Min: {min(leverage_values):.2f}x",
            help="Plus bas = moins de risque"
        )

    with col3:
        st.metric(
            "Marge Moyenne",
            f"{sum(margin_values)/len(margin_values):.1f}%",
            delta=f"Max: {max(margin_values):.1f}%",
            help="Plus élevée = meilleure rentabilité"
        )

    with col4:
        st.metric(
            "Score Moyen",
            f"{sum(scores)/len(scores):.0f}/100",
            delta=f"Max: {max(scores)}/100",
            help="Score global de viabilité"
        )


def render_visual_comparison(variant_ids: List[str]) -> None:
    """
    Graphiques visuels de comparaison.

    Args:
        variant_ids: IDs des variantes à comparer
    """
    st.subheader("📈 Visualisations Comparatives")

    manager = VariantManager()
    variants = [manager.load_variant(vid) for vid in variant_ids]
    variants = [v for v in variants if v is not None]

    if not variants:
        return

    # Préparer labels
    labels = [f"{v.company_name[:15]}\n{v.name[:15]}" for v in variants]

    tab1, tab2, tab3 = st.tabs(["🎯 Métriques Clés", "💰 Structure Financement", "⚡ Performance"])

    with tab1:
        # Graphique radar métriques clés
        fig = create_radar_chart(variants, labels)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Graphique waterfall structure financement
        fig = create_financing_structure_chart(variants, labels)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # Graphique barres performance
        fig = create_performance_bars(variants, labels)
        st.plotly_chart(fig, use_container_width=True)


def create_radar_chart(variants: List, labels: List[str]) -> go.Figure:
    """
    Créer graphique radar pour comparaison métriques.

    Returns:
        Figure Plotly
    """
    categories = ["DSCR", "Marge %", "Score", "Conversion FCF"]

    fig = go.Figure()

    for i, variant in enumerate(variants):
        metrics = variant.metrics
        decision = variant.decision or {}

        # Normaliser métriques sur échelle 0-100
        dscr_norm = min(100, (metrics.get("dscr_min", 0) / 2.0) * 100)
        margin_norm = min(100, (metrics.get("margin", 0) / 20) * 100)
        score_norm = decision.get("overall_score", 0)
        fcf_conv_norm = min(100, (metrics.get("equity_pct", 0) / 50) * 100)

        values = [dscr_norm, margin_norm, score_norm, fcf_conv_norm]

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=labels[i]
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title="Comparaison Métriques Clés (normalisé 0-100)"
    )

    return fig


def create_financing_structure_chart(variants: List, labels: List[str]) -> go.Figure:
    """
    Créer graphique structure financement.

    Returns:
        Figure Plotly
    """
    fig = go.Figure()

    # Préparer données
    debt_amounts = []
    equity_amounts = []
    total_prices = []

    for variant in variants:
        lbo = variant.lbo_structure
        debt_amounts.append(lbo.get("total_debt", 0) / 1_000_000)  # En millions
        equity_amounts.append(lbo.get("equity_amount", 0) / 1_000_000)
        total_prices.append(lbo.get("acquisition_price", 0) / 1_000_000)

    # Barres empilées
    fig.add_trace(go.Bar(
        name='Dette',
        x=labels,
        y=debt_amounts,
        marker_color='indianred'
    ))

    fig.add_trace(go.Bar(
        name='Equity',
        x=labels,
        y=equity_amounts,
        marker_color='lightseagreen'
    ))

    fig.update_layout(
        barmode='stack',
        title="Structure de Financement (M€)",
        yaxis_title="Montant (M€)",
        xaxis_title="Dossiers",
        showlegend=True
    )

    return fig


def create_performance_bars(variants: List, labels: List[str]) -> go.Figure:
    """
    Créer graphique barres performance.

    Returns:
        Figure Plotly
    """
    # Préparer données
    dscr_values = [v.metrics.get("dscr_min", 0) for v in variants]
    leverage_values = [v.metrics.get("leverage", 0) for v in variants]
    scores = [v.decision.get("overall_score", 0) if v.decision else 0 for v in variants]

    # Créer subplots
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("DSCR Minimum", "Dette/EBITDA", "Score Global"),
        specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
    )

    # DSCR
    fig.add_trace(
        go.Bar(
            x=labels,
            y=dscr_values,
            name="DSCR",
            marker_color=['green' if v >= 1.25 else 'orange' if v >= 1.0 else 'red' for v in dscr_values],
            showlegend=False
        ),
        row=1, col=1
    )

    # Leverage
    fig.add_trace(
        go.Bar(
            x=labels,
            y=leverage_values,
            name="Leverage",
            marker_color=['green' if v <= 4.0 else 'orange' if v <= 5.0 else 'red' for v in leverage_values],
            showlegend=False
        ),
        row=1, col=2
    )

    # Score
    fig.add_trace(
        go.Bar(
            x=labels,
            y=scores,
            name="Score",
            marker_color=['green' if v >= 80 else 'orange' if v >= 70 else 'red' for v in scores],
            showlegend=False
        ),
        row=1, col=3
    )

    # Lignes seuils
    fig.add_hline(y=1.25, line_dash="dash", line_color="gray", row=1, col=1, annotation_text="Seuil 1.25")
    fig.add_hline(y=4.0, line_dash="dash", line_color="gray", row=1, col=2, annotation_text="Seuil 4.0x")
    fig.add_hline(y=70, line_dash="dash", line_color="gray", row=1, col=3, annotation_text="Seuil 70")

    fig.update_layout(
        title_text="Indicateurs de Performance",
        showlegend=False,
        height=400
    )

    return fig


def render_decision_matrix(variant_ids: List[str]) -> None:
    """
    Matrice de décision avec recommandations.

    Args:
        variant_ids: IDs des variantes à comparer
    """
    st.subheader("🎯 Matrice de Décision")

    manager = VariantManager()
    variants = [manager.load_variant(vid) for vid in variant_ids]
    variants = [v for v in variants if v is not None]

    if not variants:
        return

    # Trier par score décroissant
    variants_sorted = sorted(
        variants,
        key=lambda v: v.decision.get("overall_score", 0) if v.decision else 0,
        reverse=True
    )

    # Podium
    col1, col2, col3 = st.columns(3)

    if len(variants_sorted) >= 1:
        with col1:
            v = variants_sorted[0]
            score = v.decision.get("overall_score", 0) if v.decision else 0
            st.success(f"🥇 **1er**: {v.company_name}")
            st.metric("Score", f"{score}/100")

    if len(variants_sorted) >= 2:
        with col2:
            v = variants_sorted[1]
            score = v.decision.get("overall_score", 0) if v.decision else 0
            st.info(f"🥈 **2ème**: {v.company_name}")
            st.metric("Score", f"{score}/100")

    if len(variants_sorted) >= 3:
        with col3:
            v = variants_sorted[2]
            score = v.decision.get("overall_score", 0) if v.decision else 0
            st.warning(f"🥉 **3ème**: {v.company_name}")
            st.metric("Score", f"{score}/100")

    st.divider()

    # Tableau décision détaillé
    st.markdown("### 📋 Analyse Détaillée")

    for rank, variant in enumerate(variants_sorted, 1):
        decision = variant.decision or {}
        decision_val = decision.get("decision", {}).get("value", "N/A")
        score = decision.get("overall_score", 0)
        deal_breakers = decision.get("deal_breakers", [])
        warnings = decision.get("warnings", [])
        recommendations = decision.get("recommendations", [])

        # Icône et couleur selon décision
        if decision_val == "GO":
            icon = "🟢"
            color = "green"
        elif decision_val == "WATCH":
            icon = "🟡"
            color = "orange"
        else:
            icon = "🔴"
            color = "red"

        with st.expander(
            f"#{rank} - {icon} {variant.company_name} - {variant.name} ({score}/100)",
            expanded=(rank == 1)
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Métriques**")
                st.caption(f"DSCR: {format_ratio(variant.metrics.get('dscr_min', 0))}")
                st.caption(f"Dette/EBITDA: {variant.metrics.get('leverage', 0):.2f}x")
                st.caption(f"Marge: {variant.metrics.get('margin', 0):.1f}%")
                st.caption(f"Equity: {variant.metrics.get('equity_pct', 0):.1f}%")

            with col2:
                st.markdown("**Structure**")
                lbo = variant.lbo_structure
                st.caption(f"Prix: {format_number(lbo.get('acquisition_price', 0))}")
                st.caption(f"Dette: {format_number(lbo.get('total_debt', 0))}")
                st.caption(f"Equity: {format_number(lbo.get('equity_amount', 0))}")

            if deal_breakers:
                st.error("**❌ Deal Breakers**")
                for db in deal_breakers:
                    st.markdown(f"• {db}")

            if warnings:
                st.warning("**⚠️ Points d'Attention**")
                for w in warnings[:3]:
                    st.markdown(f"• {w}")

            if recommendations:
                st.info("**💡 Recommandations**")
                for r in recommendations[:3]:
                    st.markdown(f"• {r}")


def render_multi_deal_dashboard() -> None:
    """
    Dashboard complet de comparaison multi-dossiers.

    Page dédiée ou section Tab 4.
    """
    st.header("🏆 Dashboard Comparaison Multi-Dossiers")

    st.markdown("""
    Comparez plusieurs opportunités d'investissement LBO côte à côte
    pour identifier les meilleurs dossiers.
    """)

    st.divider()

    # Sélection dossiers
    selected_ids = render_multi_deal_selector()

    if not selected_ids:
        st.info("👆 Sélectionnez au moins 1 dossier pour commencer")
        return

    if len(selected_ids) == 1:
        st.info("ℹ️ Sélectionnez au moins 2 dossiers pour une comparaison")

    st.divider()

    # Comparaison métriques
    render_metrics_comparison(selected_ids)

    st.divider()

    # Visualisations
    if len(selected_ids) >= 2:
        render_visual_comparison(selected_ids)

        st.divider()

        # Matrice décision
        render_decision_matrix(selected_ids)

    st.divider()

    # Actions
    st.subheader("⚡ Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Exporter Comparaison (CSV)", use_container_width=True):
            st.info("🚧 Fonctionnalité en développement")

    with col2:
        if st.button("📄 Générer Rapport Comparatif", use_container_width=True):
            st.info("🚧 Fonctionnalité en développement (Phase 3.9)")

    with col3:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.rerun()
