"""
Interface Streamlit pour gestion des variantes LBO.

Fonctionnalités:
- Sauvegarde variante en cours
- Chargement variante sauvegardée
- Comparaison côte à côte
- Gestion (liste, suppression, tags)
"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime

from src.persistence.variant_manager import (
    VariantManager,
    VariantStatus,
    LBOVariant
)
from src.ui.utils.formatting import (
    format_number,
    format_percentage,
    format_ratio
)


def render_save_variant_section(
    company_name: str,
    lbo_structure,
    norm_data,
    financial_data: Dict,
    metrics: Dict,
    decision = None
) -> None:
    """
    Section pour sauvegarder la variante en cours.

    Args:
        company_name: Nom entreprise
        lbo_structure: Structure LBO actuelle
        norm_data: Données normalisées
        financial_data: Données financières
        metrics: Métriques calculées
        decision: Décision finale
    """
    st.subheader("💾 Sauvegarder Variante")

    with st.form("save_variant_form"):
        col1, col2 = st.columns(2)

        with col1:
            variant_name = st.text_input(
                "Nom de la variante *",
                placeholder="Ex: Montage 70% dette",
                help="Nom descriptif pour identifier cette variante"
            )

        with col2:
            status = st.selectbox(
                "Statut",
                options=[s.value for s in VariantStatus],
                format_func=lambda x: {
                    "draft": "🟡 Brouillon",
                    "validated": "🟢 Validé",
                    "rejected": "🔴 Rejeté",
                    "archived": "⚫ Archivé"
                }[x]
            )

        description = st.text_area(
            "Description (optionnel)",
            placeholder="Montage avec 70% dette senior, equity 30%...",
            height=100
        )

        tags_input = st.text_input(
            "Tags (séparés par virgules)",
            placeholder="Ex: 70pct_dette, senior, baseline",
            help="Tags pour filtrer et retrouver facilement"
        )

        submitted = st.form_submit_button("💾 Sauvegarder", use_container_width=True)

        if submitted:
            if not variant_name:
                st.error("❌ Le nom de la variante est obligatoire")
                return

            # Parser tags
            tags = [t.strip() for t in tags_input.split(",") if t.strip()]

            # Convertir structures en dict
            lbo_dict = _convert_lbo_to_dict(lbo_structure)
            norm_dict = _convert_norm_to_dict(norm_data)
            decision_dict = _convert_decision_to_dict(decision) if decision else None

            # Sauvegarder
            try:
                manager = VariantManager()
                variant = manager.save_variant(
                    name=variant_name,
                    company_name=company_name,
                    lbo_structure=lbo_dict,
                    norm_data=norm_dict,
                    financial_data=financial_data,
                    metrics=metrics,
                    description=description,
                    status=VariantStatus(status),
                    decision=decision_dict,
                    tags=tags
                )

                st.success(f"✅ Variante '{variant_name}' sauvegardée!")
                st.session_state.last_saved_variant = variant.id

            except Exception as e:
                st.error(f"❌ Erreur sauvegarde: {str(e)}")


def render_load_variant_section(company_name: Optional[str] = None) -> Optional[str]:
    """
    Section pour charger une variante sauvegardée.

    Args:
        company_name: Nom entreprise (pour filtrer)

    Returns:
        ID de la variante sélectionnée ou None
    """
    st.subheader("📂 Charger Variante")

    manager = VariantManager()

    # Filtres
    col1, col2 = st.columns(2)

    with col1:
        filter_status = st.selectbox(
            "Filtrer par statut",
            options=["Tous"] + [s.value for s in VariantStatus],
            format_func=lambda x: {
                "Tous": "Tous",
                "draft": "🟡 Brouillon",
                "validated": "🟢 Validé",
                "rejected": "🔴 Rejeté",
                "archived": "⚫ Archivé"
            }.get(x, x)
        )

    with col2:
        filter_tags = st.text_input(
            "Filtrer par tags (séparés par virgules)",
            placeholder="Ex: 70pct_dette, optimisé"
        )

    # Appliquer filtres
    status_filter = VariantStatus(filter_status) if filter_status != "Tous" else None
    tags_filter = [t.strip() for t in filter_tags.split(",") if t.strip()] if filter_tags else None

    # Charger variantes
    variants = manager.list_variants(
        company_name=company_name,
        status=status_filter,
        tags=tags_filter
    )

    if not variants:
        st.info("ℹ️ Aucune variante sauvegardée")
        return None

    # Afficher liste
    st.markdown(f"**{len(variants)} variante(s) trouvée(s)**")

    for variant in variants:
        with st.expander(
            f"{_get_status_icon(variant.status)} {variant.name} - {variant.company_name}",
            expanded=False
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Informations**")
                st.caption(f"Créée: {_format_datetime(variant.created_at)}")
                st.caption(f"Modifiée: {_format_datetime(variant.modified_at)}")
                if variant.tags:
                    st.caption(f"Tags: {', '.join(variant.tags)}")

            with col2:
                st.markdown("**Métriques clés**")
                st.caption(f"DSCR: {format_ratio(variant.metrics.get('dscr_min', 0))}")
                st.caption(f"Dette/EBITDA: {format_ratio(variant.metrics.get('leverage', 0))}x")
                st.caption(f"Equity: {format_percentage(variant.metrics.get('equity_pct', 0))}")

            with col3:
                st.markdown("**Décision**")
                if variant.decision:
                    decision_val = variant.decision.get("decision", {}).get("value", "N/A")
                    score = variant.decision.get("overall_score", 0)
                    st.caption(f"{decision_val} ({score}/100)")

            if variant.description:
                st.markdown(f"_{variant.description}_")

            # Actions
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(f"📥 Charger", key=f"load_{variant.id}", use_container_width=True):
                    return variant.id

            with col2:
                if st.button(f"🗑️ Supprimer", key=f"delete_{variant.id}", use_container_width=True):
                    if manager.delete_variant(variant.id):
                        st.success(f"✅ Variante supprimée")
                        st.rerun()
                    else:
                        st.error("❌ Erreur suppression")

            with col3:
                # Bouton export individuel
                if st.button(f"💾 Exporter", key=f"export_{variant.id}", use_container_width=True):
                    st.session_state.variant_to_export = variant.id

    return None


def render_comparison_section(company_name: Optional[str] = None) -> None:
    """
    Section pour comparer plusieurs variantes.

    Args:
        company_name: Nom entreprise (pour filtrer)
    """
    st.subheader("🔍 Comparer Variantes")

    manager = VariantManager()
    variants = manager.list_variants(company_name=company_name)

    if len(variants) < 2:
        st.info("ℹ️ Au moins 2 variantes nécessaires pour comparaison")
        return

    # Sélection variantes
    variant_options = {
        f"{v.name} ({_format_datetime(v.modified_at)})": v.id
        for v in variants
    }

    selected_names = st.multiselect(
        "Sélectionner variantes à comparer (2-5)",
        options=list(variant_options.keys()),
        max_selections=5
    )

    if len(selected_names) < 2:
        st.info("ℹ️ Sélectionnez au moins 2 variantes")
        return

    # IDs sélectionnés
    selected_ids = [variant_options[name] for name in selected_names]

    # Générer comparaison
    comparison = manager.compare_variants(selected_ids)

    if "error" in comparison:
        st.error(comparison["error"])
        return

    # Afficher comparaison
    st.divider()

    # Tableau résumé variantes
    st.markdown("### 📋 Variantes Sélectionnées")

    variant_data = []
    for v_info in comparison["variants"]:
        variant_data.append({
            "Nom": v_info["name"],
            "Statut": _get_status_icon(VariantStatus(v_info["status"])),
            "Modifiée": _format_datetime(v_info["modified_at"])
        })

    st.table(variant_data)

    # Comparaison métriques
    st.markdown("### 📊 Comparaison Métriques")

    metrics_comp = comparison["metrics_comparison"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "DSCR minimum",
            f"{max(metrics_comp['dscr_min']):.2f}",
            delta=f"Écart: {max(metrics_comp['dscr_min']) - min(metrics_comp['dscr_min']):.2f}",
            help="Plus élevé = meilleur"
        )

    with col2:
        st.metric(
            "Dette/EBITDA",
            f"{min(metrics_comp['leverage']):.2f}x",
            delta=f"Écart: {max(metrics_comp['leverage']) - min(metrics_comp['leverage']):.2f}x",
            help="Plus bas = meilleur"
        )

    with col3:
        st.metric(
            "Equity %",
            f"{max(metrics_comp['equity_pct']):.1f}%",
            delta=f"Écart: {max(metrics_comp['equity_pct']) - min(metrics_comp['equity_pct']):.1f}%",
            help="Plus élevé = moins de risque"
        )

    # Tableau détaillé
    st.markdown("### 📈 Détail Comparaison")

    comparison_table = []

    for i, name in enumerate(selected_names):
        row = {
            "Variante": name,
            "DSCR": format_ratio(metrics_comp["dscr_min"][i]),
            "Dette/EBITDA": f"{metrics_comp['leverage'][i]:.2f}x",
            "Marge": f"{metrics_comp['margin'][i]:.1f}%",
            "Equity %": f"{metrics_comp['equity_pct'][i]:.1f}%"
        }
        comparison_table.append(row)

    st.table(comparison_table)

    # Comparaison structure
    st.markdown("### 🏗️ Structure Financement")

    struct_comp = comparison["structure_comparison"]

    structure_table = []
    for i, name in enumerate(selected_names):
        row = {
            "Variante": name,
            "Prix": format_number(struct_comp["acquisition_price"][i]),
            "Dette": format_number(struct_comp["total_debt"][i]),
            "Equity": format_number(struct_comp["equity_amount"][i]),
            "% Dette Senior": f"{struct_comp['senior_debt_pct'][i]:.1f}%"
        }
        structure_table.append(row)

    st.table(structure_table)

    # Décisions
    st.markdown("### ✅ Décisions")

    decision_comp = comparison["decision_comparison"]

    decision_table = []
    for i, name in enumerate(selected_names):
        row = {
            "Variante": name,
            "Décision": decision_comp["decisions"][i],
            "Score": f"{decision_comp['scores'][i]}/100",
            "Deal Breakers": decision_comp["deal_breakers_count"][i],
            "Warnings": decision_comp["warnings_count"][i]
        }
        decision_table.append(row)

    st.table(decision_table)


def render_variant_manager() -> None:
    """
    Interface complète de gestion des variantes.

    À intégrer dans Tab 4 ou page dédiée.
    """
    st.header("📚 Gestion Variantes LBO")

    # Récupérer entreprise en cours
    financial_data = st.session_state.get('financial_data', {})
    company_name = financial_data.get("metadata", {}).get("company_name", None)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["💾 Sauvegarder", "📂 Charger", "🔍 Comparer"])

    with tab1:
        # Vérifier données disponibles
        if not st.session_state.get('lbo_structure'):
            st.warning("⚠️ Veuillez d'abord créer un montage LBO (Tab 2)")
            return

        render_save_variant_section(
            company_name=company_name or "Entreprise",
            lbo_structure=st.session_state.lbo_structure,
            norm_data=st.session_state.get('normalization_data'),
            financial_data=financial_data,
            metrics=st.session_state.get('metrics', {}),
            decision=st.session_state.get('acquisition_decision')
        )

    with tab2:
        variant_id = render_load_variant_section(company_name)

        if variant_id:
            # Charger variante dans session
            manager = VariantManager()
            variant = manager.load_variant(variant_id)

            if variant:
                st.session_state.lbo_structure = variant.lbo_structure
                st.session_state.normalization_data = variant.norm_data
                st.session_state.financial_data = variant.financial_data
                st.session_state.metrics = variant.metrics
                st.session_state.acquisition_decision = variant.decision

                st.success(f"✅ Variante '{variant.name}' chargée!")
                st.info("🔄 Retournez aux onglets précédents pour voir les données chargées")

    with tab3:
        render_comparison_section(company_name)


# Fonctions utilitaires

def _convert_lbo_to_dict(lbo) -> Dict:
    """Convertir structure LBO en dict."""
    if isinstance(lbo, dict):
        return lbo

    # Si c'est un objet Pydantic
    return {
        "acquisition_price": lbo.acquisition_price,
        "total_debt": lbo.total_debt,
        "equity_amount": lbo.equity_amount,
        "debt_layers": [
            {
                "name": layer.name,
                "amount": layer.amount,
                "interest_rate": layer.interest_rate,
                "duration_years": layer.duration_years,
                "grace_period": getattr(layer, 'grace_period', 0)
            }
            for layer in lbo.debt_layers
        ]
    }


def _convert_norm_to_dict(norm_data) -> Dict:
    """Convertir données normalisation en dict."""
    if isinstance(norm_data, dict):
        return norm_data

    # Si c'est un objet Pydantic
    return {
        "ebitda_bank": norm_data.ebitda_bank,
        "ebitda_equity": norm_data.ebitda_equity,
        "adjustments": [
            {
                "description": adj.description,
                "amount": adj.amount,
                "impact_bank": adj.impact_bank,
                "impact_equity": adj.impact_equity
            }
            for adj in getattr(norm_data, 'adjustments', [])
        ]
    }


def _convert_decision_to_dict(decision) -> Dict:
    """Convertir décision en dict."""
    if isinstance(decision, dict):
        return decision

    # Si c'est un objet Pydantic
    return {
        "decision": {"value": decision.decision.value},
        "overall_score": decision.overall_score,
        "deal_breakers": decision.deal_breakers,
        "warnings": decision.warnings,
        "recommendations": decision.recommendations
    }


def _get_status_icon(status: VariantStatus) -> str:
    """Obtenir icône selon statut."""
    icons = {
        VariantStatus.DRAFT: "🟡",
        VariantStatus.VALIDATED: "🟢",
        VariantStatus.REJECTED: "🔴",
        VariantStatus.ARCHIVED: "⚫"
    }
    return icons.get(status, "❓")


def _format_datetime(dt_str: str) -> str:
    """Formater datetime ISO en français."""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return dt_str
