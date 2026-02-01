"""
Application Streamlit Phase 3+ - LBO Professionnel.

Architecture 1 PAGE 5 TABS + Dashboard:
- Tab 1: Données (Import & Normalisation)
- Tab 2: Montage LBO (Sliders + Impact temps réel + Zones visuelles)
- Tab 3: Viabilité (Stress tests + Décision + Export Excel)
- Tab 4: Synthèse (Export PDF + Gestion Variantes)
- Tab 5: Dashboard Multi-Dossiers (Comparaison)

Phases intégrées:
- Phase 3.0: Base (4 tabs)
- Phase 3.5: UX & Performance (sliders visuels, caching, Excel)
- Phase 3.6: Export PDF professionnel
- Phase 3.7: Sauvegarde/chargement variantes
- Phase 3.8: Dashboard comparaison multi-dossiers

Version: 3.8+
Date: Février 2026
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import streamlit as st
import plotly.graph_objects as go
from typing import Dict, List, Optional

# Imports modèles
from src.core.models_v3 import (
    NormalizationData,
    Adjustment,
    AdjustmentCategory,
    LBOStructure,
    DebtLayer,
    AmortizationType,
    OperatingAssumptions,
)

# Imports normalisation
from src.normalization.normalizer import DataNormalizer

# Imports formatage
from src.ui.utils.formatting import (
    format_number,
    format_percentage,
    format_ratio,
    format_currency_compact,
)

# Imports Tab 3
from src.scenarios.stress_tester import StressTester
from src.calculations.covenant_tracker import CovenantTracker, CovenantDefinition
from src.decision.decision_engine import DecisionEngine
from src.core.models_v3 import Decision

# Imports Phase 3.5-3.8 (nouvelles fonctionnalités)
try:
    from src.ui.tab4_complete import render_tab4_complete
    TAB4_ENHANCED = True
except ImportError:
    TAB4_ENHANCED = False

try:
    from src.ui.variant_ui import render_variant_manager
    VARIANT_MANAGER = True
except ImportError:
    VARIANT_MANAGER = False

try:
    from src.ui.multi_deal_dashboard import render_multi_deal_dashboard
    MULTI_DEAL = True
except ImportError:
    MULTI_DEAL = False

# =============================================================================
# CONFIGURATION PAGE
# =============================================================================

st.set_page_config(
    page_title="Analyse LBO Professionnelle",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"  # Sidebar pour navigation améliorée
)

# =============================================================================
# STATE MANAGEMENT
# =============================================================================

def init_session_state():
    """Initialise le state de session."""
    if "financial_data" not in st.session_state:
        st.session_state.financial_data = None

    if "normalization_data" not in st.session_state:
        st.session_state.normalization_data = None

    if "lbo_structure" not in st.session_state:
        st.session_state.lbo_structure = None

    if "operating_assumptions" not in st.session_state:
        st.session_state.operating_assumptions = None

    if "metrics_results" not in st.session_state:
        st.session_state.metrics_results = {}

    if "current_tab" not in st.session_state:
        st.session_state.current_tab = 0

    # Pour détecter changements
    if "previous_params" not in st.session_state:
        st.session_state.previous_params = {}


init_session_state()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_sample_financial_data() -> Dict:
    """Crée des données financières de test."""
    return {
        "metadata": {
            "company_name": "ACME SARL",
            "siren": "123456789",
            "fiscal_year_end": "2025-12-31"
        },
        "balance_sheet": {
            "assets": {
                "fixed_assets": {"total": 1_200_000},
                "current_assets": {
                    "inventory": 400_000,
                    "trade_receivables": 950_000,
                    "cash": 350_000,
                    "total": 1_700_000
                },
                "total_assets": 2_900_000
            },
            "liabilities": {
                "equity": {"total": 1_100_000, "net_income": 320_000},
                "debt": {"total_financial_debt": 800_000},
                "operating_liabilities": {"total": 1_000_000},
                "total_liabilities": 2_900_000
            }
        },
        "income_statement": {
            "revenues": {"net_revenue": 8_500_000, "total": 8_500_000},
            "operating_expenses": {
                "purchases_of_goods": 2_000_000,
                "purchases_of_raw_materials": 1_500_000,
                "inventory_variation": -50_000,
                "external_charges": 1_200_000,
                "taxes_and_duties": 150_000,
                "wages_and_salaries": 2_000_000,
                "social_charges": 800_000,
                "depreciation": 200_000,
                "total": 7_800_000
            },
            "operating_income": 700_000,
            "financial_result": {
                "interest_expense": 60_000,
                "net_financial_result": -60_000
            },
            "income_tax_expense": 160_000,
            "net_income": 320_000
        }
    }


def get_status_icon(score: int) -> str:
    """Retourne l'icône selon le score."""
    if score >= 80:
        return "🟢"
    elif score >= 50:
        return "🟡"
    else:
        return "🔴"


# =============================================================================
# HEADER
# =============================================================================

st.title("💰 Analyse Financière - Acquisition LBO")
st.markdown("""
**Application professionnelle pour l'analyse d'acquisitions de PME (2-20M€)**
Workflow complet: Import → Normalisation → Montage → Viabilité → Décision
""")

st.divider()

# =============================================================================
# TABS NAVIGATION
# =============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 1. Données",
    "🔧 2. Montage LBO",
    "✅ 3. Viabilité",
    "📄 4. Synthèse",
    "🏆 5. Multi-Dossiers"
])

# =============================================================================
# TAB 1: DONNÉES (Import & Normalisation)
# =============================================================================

with tab1:
    st.header("📊 Import & Normalisation des Données")

    st.markdown("""
    ### Workflow de normalisation
    1. **Import** : Chargez votre liasse fiscale
    2. **Data Quality** : Vérification automatique
    3. **Normalisation** : EBE → EBITDA banque → EBITDA equity
    4. **Validation** : Confirmez les données normalisées
    """)

    st.divider()

    # Section 1: Import
    st.subheader("1️⃣ Import Liasse Fiscale")

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("📥 Charger Données de Test", type="primary", use_container_width=True):
            st.session_state.financial_data = create_sample_financial_data()
            st.success("✅ Données de test chargées!")
            st.rerun()

    with col2:
        if st.session_state.financial_data:
            company_name = st.session_state.financial_data.get("metadata", {}).get("company_name", "N/A")
            ca = st.session_state.financial_data.get("income_statement", {}).get("revenues", {}).get("net_revenue", 0)
            st.info(f"**Entreprise**: {company_name} | **CA**: {format_number(ca)}")

    # Section 2: Data Quality Center
    if st.session_state.financial_data:
        st.divider()
        st.subheader("2️⃣ Data Quality Center")

        # Checklist qualité
        data = st.session_state.financial_data
        balance = data.get("balance_sheet", {})
        income = data.get("income_statement", {})

        total_assets = balance.get("assets", {}).get("total_assets", 0)
        total_liabilities = balance.get("liabilities", {}).get("total_liabilities", 0)
        ca = income.get("revenues", {}).get("net_revenue", 0)
        net_income_income = income.get("net_income", 0)
        net_income_balance = balance.get("liabilities", {}).get("equity", {}).get("net_income", 0)

        checks = []

        # Check 1: Bilan équilibré
        balance_ok = abs(total_assets - total_liabilities) <= 1
        checks.append(("✅" if balance_ok else "❌", "Bilan équilibré (Actif = Passif)", balance_ok))

        # Check 2: Résultat cohérent
        result_ok = abs(net_income_income - net_income_balance) <= 1
        checks.append(("✅" if result_ok else "⚠️", "Résultat cohérent (Bilan = Compte de résultat)", result_ok))

        # Check 3: CA dans cible
        ca_ok = 2_000_000 <= ca <= 20_000_000
        checks.append(("✅" if ca_ok else "⚠️", f"CA dans cible 2-20M€ (actuel: {format_currency_compact(ca)})", ca_ok))

        # Check 4: EBE positif
        normalizer = DataNormalizer()
        ebe = normalizer.calculate_ebe(data)
        ebe_ok = ebe > 0
        checks.append(("✅" if ebe_ok else "🔴", f"EBE positif ({format_number(ebe)})", ebe_ok))

        # Affichage checklist
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("**Statut**")
        with col2:
            st.markdown("**Critère**")

        for icon, label, status in checks:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(icon)
            with col2:
                st.markdown(label)

        # Section 3: Normalisation
        st.divider()
        st.subheader("3️⃣ Normalisation Comptable")

        # Affichage EBE
        st.metric(
            label="EBE (Excédent Brut d'Exploitation)",
            value=format_number(ebe),
            help="CA - Charges d'exploitation (hors amortissements)"
        )

        st.markdown("#### Retraitements")
        st.markdown("Ajoutez des retraitements pour normaliser l'EBITDA:")

        # Initialiser normalisation si nécessaire
        if st.session_state.normalization_data is None:
            st.session_state.normalization_data = normalizer.create_normalization_data(data)

        norm_data = st.session_state.normalization_data

        # Suggestions automatiques
        with st.expander("💡 Suggestions Automatiques"):
            suggestions = normalizer.suggest_adjustments(data)
            if suggestions:
                for sug in suggestions:
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"**{sug.name}**")
                        st.caption(sug.description)
                    with col2:
                        st.write(format_number(sug.amount))
                    with col3:
                        if st.button("➕ Ajouter", key=f"add_{sug.name}"):
                            norm_data.adjustments.append(sug)
                            st.rerun()
            else:
                st.info("Aucune suggestion automatique détectée")

        # Ajout manuel d'ajustements
        with st.expander("➕ Ajouter Retraitement Manuel", expanded=len(norm_data.adjustments) == 0):
            adj_name = st.text_input("Nom du retraitement", value="Loyers crédit-bail")
            adj_amount = st.number_input(
                "Montant (€)",
                min_value=-10_000_000,
                max_value=10_000_000,
                value=150_000,
                step=10_000,
                help="Positif = augmente EBITDA, Négatif = diminue EBITDA"
            )
            adj_category = st.selectbox(
                "Catégorie",
                options=[cat.value for cat in AdjustmentCategory],
                format_func=lambda x: x.capitalize()
            )
            adj_desc = st.text_area("Description", value="Retraitement loyers crédit-bail")

            if st.button("✅ Ajouter ce retraitement"):
                new_adj = Adjustment(
                    name=adj_name,
                    amount=adj_amount,
                    category=AdjustmentCategory(adj_category),
                    description=adj_desc
                )
                norm_data.adjustments.append(new_adj)
                st.success(f"✅ Ajouté: {adj_name}")
                st.rerun()

        # Liste des ajustements
        if norm_data.adjustments:
            st.markdown("#### Retraitements Appliqués")
            for idx, adj in enumerate(norm_data.adjustments):
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                with col1:
                    st.write(f"**{adj.name}**")
                with col2:
                    sign = "+" if adj.amount >= 0 else ""
                    st.write(f"{sign}{format_number(adj.amount)}")
                with col3:
                    st.caption(adj.category.value)
                with col4:
                    if st.button("🗑️", key=f"del_{idx}"):
                        norm_data.adjustments.pop(idx)
                        st.rerun()

        # Calcul EBITDA banque
        st.divider()

        # Recalcul
        norm_data.calculate_ebitda_bank()

        # Waterfall chart simplifié
        st.markdown("#### 📊 Waterfall: EBE → EBITDA banque")

        waterfall_fig = go.Figure()

        # EBE initial
        waterfall_fig.add_trace(go.Waterfall(
            name="",
            orientation="v",
            measure=["absolute"] + ["relative"] * len(norm_data.adjustments) + ["total"],
            x=["EBE"] + [adj.name for adj in norm_data.adjustments] + ["EBITDA banque"],
            y=[norm_data.ebe] + [adj.amount for adj in norm_data.adjustments] + [0],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))

        waterfall_fig.update_layout(
            title="Waterfall: Normalisation EBITDA",
            showlegend=False,
            height=400
        )

        st.plotly_chart(waterfall_fig, use_container_width=True)

        # Résultats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("EBE initial", format_number(norm_data.ebe))
        with col2:
            total_adj = sum(adj.amount for adj in norm_data.adjustments)
            st.metric("Total retraitements", format_number(total_adj))
        with col3:
            st.metric("✨ EBITDA banque", format_number(norm_data.ebitda_bank))

        # Section 4: EBITDA equity
        st.divider()
        st.subheader("4️⃣ EBITDA Equity (Disponible Entrepreneurs)")

        col1, col2 = st.columns(2)
        with col1:
            tax_rate = st.slider(
                "Taux IS effectif",
                min_value=0.0,
                max_value=0.50,
                value=0.25,
                step=0.01,
                format="%.0f%%",
                help="Taux d'impôt sur les sociétés"
            ) * 100 / 100  # Convertir en décimal

        with col2:
            capex_maint = st.number_input(
                "Capex maintenance annuel (€)",
                min_value=0,
                max_value=5_000_000,
                value=250_000,
                step=50_000
            )

        # Calcul EBITDA equity
        norm_data.calculate_ebitda_equity(tax_rate, capex_maint)

        # Affichage
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("EBITDA banque", format_number(norm_data.ebitda_bank))
        with col2:
            is_cash = norm_data.ebitda_bank * tax_rate
            st.metric("- IS cash", format_number(is_cash), delta=None, delta_color="inverse")
        with col3:
            st.metric("- Capex maint.", format_number(capex_maint), delta=None, delta_color="inverse")
        with col4:
            st.metric("= EBITDA equity", format_number(norm_data.ebitda_equity))

        # Validation
        st.divider()
        if st.button("✅ Valider les Données Normalisées", type="primary", use_container_width=True):
            norm_data.validate(user="Utilisateur")
            st.success("✅ Données normalisées validées! Passez à l'onglet 2: Montage LBO →")
            st.session_state.current_tab = 1

# =============================================================================
# TAB 2: MONTAGE LBO
# =============================================================================

with tab2:
    st.header("🔧 Montage LBO - Plan de Financement")

    if st.session_state.normalization_data is None:
        st.warning("⚠️ Veuillez d'abord compléter l'onglet 1: Données")
    else:
        norm_data = st.session_state.normalization_data

        st.markdown(f"""
        **EBITDA normalisé**: {format_number(norm_data.ebitda_bank)}
        Construisez votre plan de financement et visualisez l'impact en temps réel.
        """)

        st.divider()

        # Layout 3 colonnes
        col_params, col_viz, col_kpis = st.columns([2, 3, 2])

        # =====================================================================
        # COLONNE 1: PARAMÈTRES
        # =====================================================================
        with col_params:
            st.subheader("Paramètres")

            # Prix d'acquisition
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

            # Dette senior
            st.markdown("**Dette Senior**")
            dette_senior_pct = st.slider(
                "% du prix",
                min_value=0,
                max_value=100,
                value=60,
                step=5,
                key="dette_senior_pct"
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
                key="taux_senior"
            )

            duree_senior = st.slider(
                "Durée senior",
                min_value=3,
                max_value=15,
                value=7,
                step=1,
                format="%d ans",
                key="duree_senior"
            )

            st.divider()

            # Bpifrance
            use_bpifrance = st.checkbox("Activer Bpifrance", value=True)
            if use_bpifrance:
                dette_bpi_pct = st.slider(
                    "Bpifrance (%)",
                    min_value=0,
                    max_value=20,
                    value=10,
                    step=5
                )
                dette_bpi = acquisition_price * dette_bpi_pct / 100
                st.caption(f"Montant: {format_number(dette_bpi)}")

                taux_bpi = st.slider(
                    "Taux Bpifrance",
                    min_value=1.0,
                    max_value=7.0,
                    value=3.0,
                    step=0.1,
                    format="%.1f%%"
                )
            else:
                dette_bpi = 0
                dette_bpi_pct = 0
                taux_bpi = 0

            st.divider()

            # Crédit vendeur
            use_vendor = st.checkbox("Activer Crédit Vendeur", value=True)
            if use_vendor:
                dette_vendor_pct = st.slider(
                    "Crédit vendeur (%)",
                    min_value=0,
                    max_value=30,
                    value=15,
                    step=5
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
            st.caption(f"{equity_pct:.1f}% du prix")

            entrepreneur_pct = st.slider(
                "Part entrepreneur (%)",
                min_value=0,
                max_value=100,
                value=70,
                step=5
            )

        # =====================================================================
        # COLONNE 2: VISUALISATIONS
        # =====================================================================
        with col_viz:
            st.subheader("Visualisations")

            # Graphique structure (Donut)
            structure_fig = go.Figure(data=[go.Pie(
                labels=["Dette senior", "Bpifrance", "Crédit vendeur", "Equity"],
                values=[dette_senior, dette_bpi, dette_vendor, equity],
                hole=0.4,
                marker=dict(colors=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"])
            )])

            structure_fig.update_layout(
                title="Structure de Financement",
                height=300
            )

            st.plotly_chart(structure_fig, use_container_width=True)

            # Métriques structure
            st.markdown("**Ratios de Structure**")
            col1, col2, col3 = st.columns(3)
            with col1:
                leverage = (total_dette / acquisition_price) if acquisition_price > 0 else 0
                st.metric("Levier total", format_percentage(leverage * 100))
            with col2:
                debt_to_equity_ratio = (total_dette / equity) if equity > 0 else float('inf')
                st.metric("Dette/Equity", format_ratio(debt_to_equity_ratio))
            with col3:
                multiple_acq = (acquisition_price / norm_data.ebitda_bank) if norm_data.ebitda_bank > 0 else 0
                st.metric("Multiple acq.", format_ratio(multiple_acq) + "x")

        # =====================================================================
        # COLONNE 3: KPIs
        # =====================================================================
        with col_kpis:
            st.subheader("KPIs Temps Réel")

            # Calculs rapides (simplifiés pour MVP)
            # DSCR simplifié
            annual_service = (dette_senior + dette_bpi) * 0.15  # Approximation 15% service annuel
            dscr_approx = (norm_data.ebitda_bank / annual_service) if annual_service > 0 else float('inf')

            # Dette/EBITDA
            dette_ebitda = (total_dette / norm_data.ebitda_bank) if norm_data.ebitda_bank > 0 else 0

            # Affichage KPIs
            st.markdown("**🎯 Métriques Décisives**")

            # DSCR
            dscr_icon = "🟢" if dscr_approx > 1.5 else "🟡" if dscr_approx > 1.25 else "🔴"
            st.metric(
                f"{dscr_icon} DSCR (approx)",
                format_ratio(dscr_approx),
                help="Seuil: >1.25"
            )

            # Dette/EBITDA
            dette_icon = "🟢" if dette_ebitda < 3.5 else "🟡" if dette_ebitda < 4.5 else "🔴"
            st.metric(
                f"{dette_icon} Dette/EBITDA",
                format_ratio(dette_ebitda) + "x",
                help="Seuil: <4x"
            )

            # Marge EBITDA
            ca = st.session_state.financial_data.get("income_statement", {}).get("revenues", {}).get("net_revenue", 1)
            marge = (norm_data.ebitda_bank / ca * 100) if ca > 0 else 0
            marge_icon = "🟢" if marge > 15 else "🟡" if marge > 10 else "🔴"
            st.metric(
                f"{marge_icon} Marge EBITDA",
                format_percentage(marge),
                help="Seuil: >15%"
            )

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

            st.markdown(f"### Décision Préliminaire")
            st.markdown(f"## :{decision_color}[{decision_prelim}]")
            st.caption(f"Score: {score}/100")

            st.divider()

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

# =============================================================================
# TAB 3: VIABILITÉ
# =============================================================================

with tab3:
    st.header("✅ Viabilité & Décision")

    if st.session_state.lbo_structure is None or st.session_state.normalization_data is None:
        st.warning("⚠️ Veuillez d'abord compléter les onglets 1 et 2")
    else:
        lbo = st.session_state.lbo_structure
        norm_data = st.session_state.normalization_data

        st.markdown(f"""
        **Prix acquisition**: {format_number(lbo.acquisition_price)}
        **Dette totale**: {format_number(lbo.total_debt)}
        **Equity**: {format_number(lbo.equity_amount)}
        """)

        st.divider()

        # =====================================================================
        # SECTION 1: STRESS TESTS
        # =====================================================================
        st.subheader("🔬 1. Stress Tests")

        st.markdown("Test de robustesse du montage sous différents scénarios de crise:")

        # Convertir LBOStructure en dict pour stress_tester
        lbo_dict = {
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

        # Exécuter stress tests
        stress_results = StressTester.run_all_scenarios(
            st.session_state.financial_data,
            lbo_dict,
            norm_dict
        )

        # Afficher tableau résultats
        st.markdown("#### Résultats Stress Tests")

        # En-têtes
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
        with col1:
            st.markdown("**Scénario**")
        with col2:
            st.markdown("**DSCR min**")
        with col3:
            st.markdown("**Dette/EB**")
        with col4:
            st.markdown("**FCF an 3**")
        with col5:
            st.markdown("**Statut**")

        st.divider()

        # Lignes
        for result in stress_results:
            scenario = result["scenario"]
            metrics = result["metrics"]
            status = StressTester.get_status_from_metrics(metrics)

            # Icône selon statut
            if status == "GO":
                status_icon = "🟢"
                status_color = "green"
            elif status == "WATCH":
                status_icon = "🟡"
                status_color = "orange"
            else:
                status_icon = "🔴"
                status_color = "red"

            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])

            with col1:
                # Icône selon type
                if scenario.scenario_type.value == "nominal":
                    icon = "✅"
                else:
                    icon = "⚠️"
                st.write(f"{icon} {scenario.name}")

            with col2:
                dscr = metrics.get("dscr_min", 0)
                st.metric("", format_ratio(dscr), label_visibility="collapsed")

            with col3:
                leverage = metrics.get("leverage", 0)
                st.metric("", format_ratio(leverage) + "x", label_visibility="collapsed")

            with col4:
                fcf = metrics.get("fcf_year3", 0)
                st.metric("", format_currency_compact(fcf), label_visibility="collapsed")

            with col5:
                st.markdown(f":{status_color}[{status_icon} {status}]")

        # Analyse stress tests
        st.divider()

        failed_scenarios = [
            r for r in stress_results
            if StressTester.get_status_from_metrics(r["metrics"]) == "NO-GO"
        ]

        if failed_scenarios:
            st.error(f"⚠️ **{len(failed_scenarios)} scénario(s) en échec**: Dossier sensible aux chocs")
            for result in failed_scenarios:
                st.caption(f"  • {result['scenario'].name}: {result['scenario'].description}")
        else:
            st.success("✅ **Dossier robuste**: Tous les scénarios passent")

        # =====================================================================
        # SECTION 2: MATRICE SENSIBILITÉ
        # =====================================================================
        st.divider()
        st.subheader("📊 2. Analyse de Sensibilité")

        st.markdown("Impact croisé CA × Marge sur le DSCR:")

        # Générer matrice
        sensitivity = StressTester.generate_sensitivity_matrix(
            st.session_state.financial_data,
            lbo_dict,
            norm_dict,
            metric="dscr_min"
        )

        # Heatmap Plotly
        heatmap_fig = go.Figure(data=go.Heatmap(
            z=sensitivity["matrix"],
            x=sensitivity["ca_labels"],
            y=sensitivity["margin_labels"],
            colorscale=[
                [0, "red"],
                [0.5, "orange"],
                [0.7, "yellow"],
                [1, "green"]
            ],
            text=[[f"{val:.2f}" for val in row] for row in sensitivity["matrix"]],
            texttemplate="%{text}",
            textfont={"size": 10},
            colorbar=dict(title="DSCR")
        ))

        heatmap_fig.update_layout(
            title="Heatmap Sensibilité: CA × Marge → DSCR",
            xaxis_title="Variation CA",
            yaxis_title="Variation Marge EBITDA",
            height=400
        )

        st.plotly_chart(heatmap_fig, use_container_width=True)

        # =====================================================================
        # SECTION 3: COVENANT TRACKING
        # =====================================================================
        st.divider()
        st.subheader("📈 3. Covenant Tracking (7 ans)")

        # Préparer assumptions pour projections
        assumptions_dict = {
            "revenue_growth_rate": [0.05, 0.05, 0.03, 0.03, 0.02, 0.02, 0.02],
            "ebitda_margin_evolution": [0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
            "tax_rate": 0.25,
            "bfr_percentage_of_revenue": 18.0,
            "capex_maintenance_pct": 3.0
        }

        # Générer projections
        projections = CovenantTracker.generate_projections(
            st.session_state.financial_data,
            lbo_dict,
            norm_dict,
            assumptions_dict,
            projection_years=7
        )

        # Créer tracker
        tracker = CovenantTracker()

        # Projeter covenants
        covenant_results = tracker.project_all_covenants(projections)

        # Graphiques covenant par covenant
        for cov_result in covenant_results:
            covenant = cov_result["covenant"]
            years = cov_result["years"]
            values = cov_result["values"]
            threshold = cov_result["threshold"]
            violations = cov_result["violations"]

            # Graphique ligne
            fig = go.Figure()

            # Ligne seuil
            fig.add_hline(
                y=threshold,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Seuil: {covenant.comparison} {threshold}",
                annotation_position="right"
            )

            # Ligne valeurs
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                mode="lines+markers",
                name=covenant.name,
                line=dict(width=3),
                marker=dict(size=8)
            ))

            # Zone verte/rouge selon covenant
            if covenant.comparison in [">=", ">"]:
                # DSCR: au-dessus = bon
                fig.add_hrect(
                    y0=threshold, y1=max(values + [threshold]) * 1.2,
                    fillcolor="green", opacity=0.1,
                    line_width=0
                )
                fig.add_hrect(
                    y0=0, y1=threshold,
                    fillcolor="red", opacity=0.1,
                    line_width=0
                )
            else:
                # Dette/EBITDA: en-dessous = bon
                fig.add_hrect(
                    y0=0, y1=threshold,
                    fillcolor="green", opacity=0.1,
                    line_width=0
                )
                fig.add_hrect(
                    y0=threshold, y1=max(values + [threshold]) * 1.2,
                    fillcolor="red", opacity=0.1,
                    line_width=0
                )

            fig.update_layout(
                title=f"{covenant.name} - Projection 7 ans",
                xaxis_title="Année",
                yaxis_title=covenant.name,
                height=300,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # Statut
            if violations:
                st.error(f"❌ **Violations détectées**: Années {violations}")
            else:
                st.success(f"✅ **Aucune violation** sur 7 ans")

        # Résumé covenants
        summary = tracker.get_summary(projections)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Covenants au vert", summary["pass_count"])
        with col2:
            st.metric("Covenants en warning", summary["warning_count"])
        with col3:
            st.metric("Violations", summary["violated_count"])

        # =====================================================================
        # SECTION 4: DÉCISION FINALE
        # =====================================================================
        st.divider()
        st.subheader("🎯 4. Décision d'Acquisition")

        # Prendre décision
        decision = DecisionEngine.make_decision(
            projections,
            norm_dict,
            st.session_state.financial_data,
            scenario_id="main_scenario"
        )

        # Affichage décision
        decision_icon = DecisionEngine.get_decision_icon(decision.decision)
        decision_color = DecisionEngine.get_decision_color(decision.decision)

        st.markdown(f"## :{decision_color}[{decision_icon} {decision.decision.value.upper()}]")
        st.markdown(f"**Score global**: {decision.overall_score}/100")

        st.divider()

        # Critères évalués
        st.markdown("#### 📊 Critères Décisifs")

        for criterion in decision.criteria:
            icon = "🟢" if criterion.status == "PASS" else "🟡" if criterion.status == "WARNING" else "🔴"

            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            with col1:
                st.write(f"{icon} {criterion.name}")
            with col2:
                st.write(f"{criterion.actual_value:.2f}")
            with col3:
                st.write(f"Seuil: {criterion.threshold_good:.2f}")
            with col4:
                st.write(f"{criterion.score}/100")

        # Deal breakers
        if decision.deal_breakers:
            st.divider()
            st.error("❌ **Problèmes Bloquants**")
            for db in decision.deal_breakers:
                st.markdown(f"  {db}")

        # Warnings
        if decision.warnings:
            st.divider()
            st.warning("⚠️ **Points d'Attention**")
            for warning in decision.warnings:
                st.markdown(f"  {warning}")

        # Recommandations
        if decision.recommendations:
            st.divider()
            st.info("💡 **Recommandations**")
            for rec in decision.recommendations:
                st.markdown(f"  {rec}")

        st.divider()

        # Sauvegarder décision
        st.session_state.acquisition_decision = decision

        if st.button("✅ Valider Décision", type="primary", use_container_width=True):
            st.success("✅ Décision validée! Passez à l'onglet 4: Synthèse →")

# =============================================================================
# TAB 4: SYNTHÈSE
# =============================================================================

with tab4:
    st.header("📄 Synthèse & Export")

    # Vérifier données disponibles
    if st.session_state.get('acquisition_decision') is None:
        st.warning("⚠️ Veuillez d'abord compléter l'onglet 3: Viabilité pour générer la décision")
    elif TAB4_ENHANCED:
        # Utiliser version améliorée Phase 3.6
        try:
            # Préparer projections si pas déjà calculées
            if 'projections' not in st.session_state and st.session_state.get('lbo_structure'):
                from src.calculations.covenant_tracker import CovenantTracker
                tracker = CovenantTracker()

                # Convertir en dict si nécessaire
                lbo_dict = st.session_state.lbo_structure
                if hasattr(lbo_dict, '__dict__'):
                    lbo_dict = {
                        'acquisition_price': lbo_dict.acquisition_price,
                        'total_debt': lbo_dict.total_debt,
                        'equity_amount': lbo_dict.equity_amount,
                        'debt_layers': [
                            {
                                'name': layer.name,
                                'amount': layer.amount,
                                'interest_rate': layer.interest_rate,
                                'duration_years': layer.duration_years
                            }
                            for layer in lbo_dict.debt_layers
                        ]
                    }

                norm_dict = st.session_state.normalization_data
                if hasattr(norm_dict, '__dict__'):
                    norm_dict = {
                        'ebitda_bank': norm_dict.ebitda_bank,
                        'ebitda_equity': norm_dict.ebitda_equity
                    }

                st.session_state.projections = tracker.generate_projections(
                    lbo_dict,
                    norm_dict,
                    st.session_state.financial_data
                )

            render_tab4_complete(
                financial_data=st.session_state.get('financial_data', {}),
                lbo=st.session_state.lbo_structure,
                norm_data=st.session_state.normalization_data,
                stress_results=st.session_state.get('stress_results', []),
                decision=st.session_state.acquisition_decision,
                projections=st.session_state.get('projections', [])
            )
        except Exception as e:
            st.error(f"❌ Erreur Tab 4: {str(e)}")
            st.info("Utilisez Tab 4 basique")
    else:
        # Fallback: version basique
        st.info("🚧 Version basique - Installez les modules Phase 3.6 pour export PDF")

        if st.session_state.get('acquisition_decision'):
            decision = st.session_state.acquisition_decision
            st.success(f"**Décision**: {decision.decision.value} ({decision.overall_score}/100)")

    # Section Gestion Variantes (Phase 3.7)
    if VARIANT_MANAGER:
        st.divider()
        with st.expander("📚 Gestion Variantes LBO", expanded=False):
            render_variant_manager()

# =============================================================================
# TAB 5: DASHBOARD MULTI-DOSSIERS (Phase 3.8)
# =============================================================================

with tab5:
    if MULTI_DEAL:
        render_multi_deal_dashboard()
    else:
        st.info("🚧 Dashboard Multi-Dossiers en développement")
        st.markdown("""
        ### Fonctionnalités à venir:
        - 🏆 Comparaison 2-10 dossiers LBO
        - 📊 Tableau métriques comparatif
        - 📈 Graphiques radar, barres empilées
        - 🎯 Podium top 3 automatique
        - 🔍 Filtres statut + entreprise
        """)

# =============================================================================
# SIDEBAR: NAVIGATION & INFO
# =============================================================================

with st.sidebar:
    st.markdown("## 💰 Analyse LBO Pro")
    st.markdown("**Version**: 3.8+")
    st.markdown("**Date**: Février 2026")

    st.divider()

    st.markdown("### 📚 Phases Intégrées")
    st.success("✅ Phase 3.0: Base (4 tabs)")
    st.success("✅ Phase 3.5: UX & Performance")
    st.success("✅ Phase 3.6: Export PDF")
    st.success("✅ Phase 3.7: Variantes LBO")
    st.success("✅ Phase 3.8: Multi-Dossiers")

    st.divider()

    st.markdown("### 📖 Documentation")
    st.markdown("- [README Phase 3](README_PHASE3.md)")
    st.markdown("- [Formules DSCR](docs/FORMULAS_DSCR.md)")

    st.divider()

    st.caption("Développé avec Claude Sonnet 4.5")

# =============================================================================
# FOOTER
# =============================================================================

st.divider()
st.caption("Analyse Financière LBO v3.8+ - Février 2026 | Phases 3.0-3.8 intégrées")
