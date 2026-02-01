"""
Tab 4 Complete - Synthèse & Export PDF.

Fonctionnalités:
- Executive summary automatique
- Export PDF banquier (focus risque)
- Export PDF investisseur (focus ROI)
- Prévisualisation rapports
"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime

from src.ui.utils.formatting import (
    format_number,
    format_percentage,
    format_ratio,
)

# Import conditionnel du générateur PDF
try:
    from src.reporting.pdf_generator import PDFGenerator, REPORTLAB_AVAILABLE
except ImportError:
    REPORTLAB_AVAILABLE = False


def render_executive_summary(
    company_name: str,
    lbo,
    norm_data,
    decision,
    projections: List[Dict]
) -> None:
    """
    Afficher executive summary interactif.

    Args:
        company_name: Nom entreprise
        lbo: Structure LBO
        norm_data: Données normalisées
        decision: Décision finale
        projections: Projections 7 ans
    """
    st.subheader("📊 Executive Summary")

    # Décision principale
    decision_icon = "🟢" if decision.decision.value == "GO" else "🟡" if decision.decision.value == "WATCH" else "🔴"
    decision_color = "green" if decision.decision.value == "GO" else "orange" if decision.decision.value == "WATCH" else "red"

    st.markdown(f"## :{decision_color}[{decision_icon} {decision.decision.value.upper()}]")
    st.markdown(f"**Score global**: {decision.overall_score}/100")

    st.divider()

    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Prix acquisition",
            format_number(lbo.acquisition_price)
        )

    with col2:
        st.metric(
            "Dette totale",
            format_number(lbo.total_debt)
        )

    with col3:
        st.metric(
            "Equity",
            format_number(lbo.equity_amount),
            delta=f"{(lbo.equity_amount / lbo.acquisition_price * 100):.1f}%"
        )

    with col4:
        st.metric(
            "EBITDA normalisé",
            format_number(norm_data.ebitda_bank)
        )

    st.divider()

    # Métriques de risque
    st.markdown("### 🎯 Métriques Clés")

    col1, col2, col3 = st.columns(3)

    # DSCR minimum
    dscr_min = min([p.get('dscr', 999) for p in projections]) if projections else 0

    with col1:
        dscr_icon = "🟢" if dscr_min > 1.5 else "🟡" if dscr_min > 1.25 else "🔴"
        st.metric(
            f"{dscr_icon} DSCR minimum (7 ans)",
            format_ratio(dscr_min),
            help="Seuil: >1.25"
        )

    # Dette/EBITDA
    leverage = lbo.total_debt / norm_data.ebitda_bank if norm_data.ebitda_bank > 0 else 0

    with col2:
        leverage_icon = "🟢" if leverage < 3.5 else "🟡" if leverage < 4.5 else "🔴"
        st.metric(
            f"{leverage_icon} Dette/EBITDA",
            format_ratio(leverage) + "x",
            help="Seuil: <4x"
        )

    # Multiple acquisition
    multiple_acq = lbo.acquisition_price / norm_data.ebitda_bank if norm_data.ebitda_bank > 0 else 0

    with col3:
        st.metric(
            "Multiple acquisition",
            format_ratio(multiple_acq) + "x"
        )

    st.divider()

    # Points clés
    st.markdown("### 💡 Points Clés")

    col1, col2 = st.columns(2)

    with col1:
        if decision.deal_breakers:
            st.error("**❌ Problèmes Bloquants**")
            for db in decision.deal_breakers[:3]:  # Top 3
                st.markdown(f"• {db}")
        elif decision.warnings:
            st.warning("**⚠️ Points d'Attention**")
            for warning in decision.warnings[:3]:  # Top 3
                st.markdown(f"• {warning}")
        else:
            st.success("**✅ Aucun problème bloquant**")

    with col2:
        if decision.recommendations:
            st.info("**💡 Recommandations**")
            for rec in decision.recommendations[:3]:  # Top 3
                st.markdown(f"• {rec}")


def render_export_section(
    company_name: str,
    financial_data: Dict,
    lbo,
    norm_data,
    stress_results: List[Dict],
    decision,
    projections: List[Dict]
) -> None:
    """
    Afficher section export PDF.

    Args:
        company_name: Nom entreprise
        financial_data: Données financières
        lbo: Structure LBO
        norm_data: Données normalisées
        stress_results: Résultats stress tests
        decision: Décision finale
        projections: Projections 7 ans
    """
    st.subheader("📄 Export Rapports PDF")

    if not REPORTLAB_AVAILABLE:
        st.error("""
        ⚠️ **ReportLab non installé**

        Pour activer l'export PDF, installez ReportLab:
        ```
        pip install reportlab
        ```

        Puis redémarrez l'application.
        """)
        return

    st.markdown("""
    Générez des rapports PDF professionnels selon votre audience:
    - **Rapport Banquier**: Focus sur le risque, DSCR, covenant tracking
    - **Rapport Investisseur**: Focus sur ROI, TRI, création de valeur
    """)

    st.divider()

    col1, col2 = st.columns(2)

    # Préparer données pour export
    lbo_dict = {
        "acquisition_price": lbo.acquisition_price,
        "total_debt": lbo.total_debt,
        "equity_amount": lbo.equity_amount,
        "debt_layers": [
            {
                "name": layer.name,
                "amount": layer.amount,
                "interest_rate": layer.interest_rate,
                "duration_years": layer.duration_years
            }
            for layer in lbo.debt_layers
        ]
    }

    norm_dict = {
        "ebitda_bank": norm_data.ebitda_bank,
        "ebitda_equity": norm_data.ebitda_equity
    }

    decision_dict = {
        "decision": {"value": decision.decision.value},
        "overall_score": decision.overall_score,
        "deal_breakers": decision.deal_breakers,
        "warnings": decision.warnings,
        "recommendations": decision.recommendations
    }

    date_str = datetime.now().strftime("%Y%m%d")

    # RAPPORT BANQUIER
    with col1:
        st.markdown("### 🏦 Rapport Banquier")
        st.markdown("""
        **Contenu:**
        - Executive summary
        - Structure financement
        - Métriques de risque
        - Stress tests (7 scénarios)
        - Covenant tracking (7 ans)
        - Décision et recommandations
        """)

        if st.button("📊 Générer Rapport Banquier", use_container_width=True):
            with st.spinner("Génération du rapport banquier..."):
                try:
                    generator = PDFGenerator()
                    pdf_buffer = generator.create_banker_report(
                        company_name,
                        financial_data,
                        lbo_dict,
                        norm_dict,
                        stress_results,
                        decision_dict,
                        projections
                    )

                    st.session_state.pdf_banker = pdf_buffer
                    st.success("✅ Rapport banquier généré!")
                except Exception as e:
                    st.error(f"❌ Erreur génération: {str(e)}")

        if "pdf_banker" in st.session_state:
            st.download_button(
                label="💾 Télécharger Rapport Banquier",
                data=st.session_state.pdf_banker,
                file_name=f"rapport_banquier_{company_name}_{date_str}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

    # RAPPORT INVESTISSEUR
    with col2:
        st.markdown("### 💼 Rapport Investisseur")
        st.markdown("""
        **Contenu:**
        - Executive summary
        - Multiple argent et TRI
        - Création de valeur (7 ans)
        - Projections CA/EBITDA/FCF
        - Décision et opportunités
        """)

        if st.button("📊 Générer Rapport Investisseur", use_container_width=True):
            with st.spinner("Génération du rapport investisseur..."):
                try:
                    generator = PDFGenerator()
                    pdf_buffer = generator.create_investor_report(
                        company_name,
                        financial_data,
                        lbo_dict,
                        norm_dict,
                        decision_dict,
                        projections
                    )

                    st.session_state.pdf_investor = pdf_buffer
                    st.success("✅ Rapport investisseur généré!")
                except Exception as e:
                    st.error(f"❌ Erreur génération: {str(e)}")

        if "pdf_investor" in st.session_state:
            st.download_button(
                label="💾 Télécharger Rapport Investisseur",
                data=st.session_state.pdf_investor,
                file_name=f"rapport_investisseur_{company_name}_{date_str}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )


def render_tab4_complete(
    financial_data: Dict,
    lbo,
    norm_data,
    stress_results: List[Dict],
    decision,
    projections: List[Dict]
) -> None:
    """
    Render Tab 4 complet avec executive summary et export PDF.

    Args:
        financial_data: Données financières
        lbo: Structure LBO
        norm_data: Données normalisées
        stress_results: Résultats stress tests
        decision: Décision finale
        projections: Projections 7 ans
    """
    st.header("📄 Synthèse & Export")

    # Vérifier données disponibles
    if decision is None:
        st.warning("⚠️ Veuillez d'abord compléter l'onglet 3: Viabilité pour générer la décision")
        return

    company_name = financial_data.get("metadata", {}).get("company_name", "Entreprise")

    # SECTION 1: EXECUTIVE SUMMARY
    render_executive_summary(
        company_name,
        lbo,
        norm_data,
        decision,
        projections
    )

    st.divider()

    # SECTION 2: EXPORT PDF
    render_export_section(
        company_name,
        financial_data,
        lbo,
        norm_data,
        stress_results,
        decision,
        projections
    )

    st.divider()

    # SECTION 3: ACTIONS RAPIDES
    st.subheader("⚡ Actions Rapides")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Nouvelle Analyse", use_container_width=True):
            # Réinitialiser session
            for key in ['financial_data', 'normalization_data', 'lbo_structure', 'acquisition_decision']:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("✅ Session réinitialisée! Retournez à l'onglet 1.")

    with col2:
        if st.button("📧 Partager (Simulé)", use_container_width=True, disabled=True):
            st.info("🚧 Fonctionnalité en développement")

    with col3:
        if st.button("💾 Sauvegarder Variante", use_container_width=True, disabled=True):
            st.info("🚧 Fonctionnalité en développement (Phase 3.7)")

    st.divider()

    # Footer
    st.caption(f"""
    **Analyse générée le**: {datetime.now().strftime("%d/%m/%Y à %H:%M")}
    **Entreprise**: {company_name}
    **Décision**: {decision.decision.value} ({decision.overall_score}/100)
    """)

    st.success("🎉 **Analyse LBO complète!** Vous pouvez maintenant télécharger les rapports PDF.")
