"""
Application LBO Simplifiée - Interface Claire et Directe

Workflow:
1. Saisir données essentielles (CA, EBITDA, retraitements)
2. Définir montage (prix, equity, dette, taux)
3. Voir résultat (DSCR, viabilité, décision)

Version: Simple 1.0
Date: Février 2026
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import streamlit as st
from typing import Dict, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Analyse LBO Simple",
    page_icon="💰",
    layout="wide"
)

# =============================================================================
# FONCTIONS DE CALCUL
# =============================================================================

def calculate_normalized_ebitda(
    ebitda_reported: float,
    exceptional_charges: float,
    exceptional_income: float
) -> float:
    """Calculer EBITDA normalisé."""
    return ebitda_reported + exceptional_charges - exceptional_income


def calculate_dscr(
    ebitda: float,
    debt_amount: float,
    interest_rate: float,
    duration_years: int
) -> float:
    """
    Calculer DSCR simplifié.

    DSCR = EBITDA / (Intérêts + Amortissement dette)
    """
    if debt_amount == 0:
        return 999.0

    # Intérêts annuels
    annual_interest = debt_amount * interest_rate

    # Amortissement linéaire
    annual_amortization = debt_amount / duration_years

    # Service de la dette
    debt_service = annual_interest + annual_amortization

    if debt_service == 0:
        return 999.0

    return ebitda / debt_service


def get_decision(dscr: float, leverage: float) -> tuple[str, str, str]:
    """
    Obtenir décision selon DSCR et leverage.

    Returns:
        (decision, color, explanation)
    """
    if dscr >= 1.25 and leverage <= 4.0:
        return "🟢 GO", "green", "Dossier viable - Bonne capacité de remboursement"
    elif dscr >= 1.0 and leverage <= 5.0:
        return "🟡 WATCH", "orange", "Dossier à surveiller - Marges serrées"
    else:
        return "🔴 NO-GO", "red", "Dossier risqué - Capacité de remboursement insuffisante"


# =============================================================================
# SESSION STATE
# =============================================================================

if "results_calculated" not in st.session_state:
    st.session_state.results_calculated = False

# =============================================================================
# HEADER
# =============================================================================

st.title("💰 Analyse LBO Simplifiée")
st.markdown("**Interface claire pour évaluer rapidement la viabilité d'un LBO**")
st.divider()

# =============================================================================
# FORMULAIRE PRINCIPAL
# =============================================================================

with st.form("lbo_form"):
    st.header("📊 Données de l'Entreprise")

    # Nom entreprise
    company_name = st.text_input(
        "Nom de l'entreprise",
        placeholder="Ex: ACME SARL",
        help="Nom de l'entreprise à analyser"
    )

    st.subheader("💰 Chiffres Clés")

    col1, col2 = st.columns(2)

    with col1:
        revenue = st.number_input(
            "Chiffre d'affaires annuel (€)",
            min_value=0.0,
            value=8_500_000.0,
            step=100_000.0,
            format="%.0f",
            help="CA annuel de l'entreprise"
        )

        ebitda_input = st.number_input(
            "EBITDA annuel (€)",
            min_value=0.0,
            value=1_000_000.0,
            step=10_000.0,
            format="%.0f",
            help="EBITDA = Résultat d'exploitation avant amortissements"
        )

        st.caption(f"📊 Marge EBITDA: {(ebitda_input/revenue*100):.1f}%" if revenue > 0 else "")

    with col2:
        exceptional_charges = st.number_input(
            "Charges exceptionnelles à retirer (€)",
            min_value=0.0,
            value=50_000.0,
            step=10_000.0,
            format="%.0f",
            help="Charges non récurrentes à neutraliser (ex: licenciement, provision one-shot)"
        )

        exceptional_income = st.number_input(
            "Produits exceptionnels à retirer (€)",
            min_value=0.0,
            value=0.0,
            step=10_000.0,
            format="%.0f",
            help="Produits non récurrents à neutraliser (ex: vente d'actif, subvention)"
        )

    # EBITDA normalisé
    ebitda_normalized = calculate_normalized_ebitda(
        ebitda_input,
        exceptional_charges,
        exceptional_income
    )

    st.info(f"**✅ EBITDA Normalisé = {ebitda_normalized:,.0f} €**")

    st.divider()

    st.subheader("💼 Montage LBO")

    col1, col2, col3 = st.columns(3)

    with col1:
        acquisition_price = st.number_input(
            "Prix d'acquisition (€)",
            min_value=0.0,
            value=5_000_000.0,
            step=100_000.0,
            format="%.0f",
            help="Prix total d'achat de l'entreprise"
        )

        # Calculer multiple
        if ebitda_normalized > 0:
            multiple = acquisition_price / ebitda_normalized
            st.caption(f"📊 Multiple: {multiple:.1f}x EBITDA")

    with col2:
        equity_amount = st.number_input(
            "Apport entrepreneur/Equity (€)",
            min_value=0.0,
            value=1_500_000.0,
            step=100_000.0,
            format="%.0f",
            help="Capitaux propres apportés (entrepreneur + investisseurs)"
        )

        # Calculer %
        if acquisition_price > 0:
            equity_pct = (equity_amount / acquisition_price) * 100
            st.caption(f"📊 Equity: {equity_pct:.1f}%")

    with col3:
        # Dette calculée automatiquement
        debt_amount = acquisition_price - equity_amount
        st.metric(
            "Dette bancaire nécessaire",
            f"{debt_amount:,.0f} €",
            delta=f"{(debt_amount/acquisition_price*100):.1f}%" if acquisition_price > 0 else None,
            help="Dette = Prix - Equity (calculé automatiquement)"
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        interest_rate = st.slider(
            "Taux d'intérêt dette (%)",
            min_value=1.0,
            max_value=10.0,
            value=4.5,
            step=0.1,
            format="%.1f%%",
            help="Taux d'intérêt annuel de la dette bancaire"
        )

    with col2:
        duration = st.slider(
            "Durée de remboursement (années)",
            min_value=3,
            max_value=10,
            value=7,
            step=1,
            help="Durée d'amortissement de la dette"
        )

    # Bouton validation
    st.divider()
    submitted = st.form_submit_button(
        "✅ CALCULER LA VIABILITÉ",
        use_container_width=True,
        type="primary"
    )

# =============================================================================
# RÉSULTATS
# =============================================================================

if submitted:
    st.session_state.results_calculated = True

    # Stocker données
    st.session_state.data = {
        'company_name': company_name or "Entreprise",
        'revenue': revenue,
        'ebitda_normalized': ebitda_normalized,
        'acquisition_price': acquisition_price,
        'equity_amount': equity_amount,
        'debt_amount': debt_amount,
        'interest_rate': interest_rate / 100,
        'duration': duration
    }

if st.session_state.results_calculated and 'data' in st.session_state:
    data = st.session_state.data

    st.divider()
    st.header("📊 Résultats de l'Analyse")

    # Calculs
    dscr = calculate_dscr(
        data['ebitda_normalized'],
        data['debt_amount'],
        data['interest_rate'],
        data['duration']
    )

    leverage = data['debt_amount'] / data['ebitda_normalized'] if data['ebitda_normalized'] > 0 else 999

    decision, color, explanation = get_decision(dscr, leverage)

    # Affichage décision
    st.markdown(f"### {decision}")
    st.markdown(f"**{explanation}**")

    st.divider()

    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        dscr_delta = "✅ Bon" if dscr >= 1.25 else "⚠️ Limite" if dscr >= 1.0 else "❌ Faible"
        st.metric(
            "DSCR",
            f"{dscr:.2f}",
            delta=dscr_delta,
            help="Debt Service Coverage Ratio - Capacité à rembourser la dette. Seuil: >1.25"
        )

    with col2:
        lev_delta = "✅ Bon" if leverage <= 4.0 else "⚠️ Élevé" if leverage <= 5.0 else "❌ Trop élevé"
        st.metric(
            "Dette/EBITDA",
            f"{leverage:.1f}x",
            delta=lev_delta,
            help="Niveau d'endettement. Seuil: <4.0x"
        )

    with col3:
        st.metric(
            "Service Dette Annuel",
            f"{(data['debt_amount'] * data['interest_rate'] + data['debt_amount']/data['duration']):,.0f} €",
            help="Montant annuel à rembourser (intérêts + capital)"
        )

    with col4:
        equity_pct = (data['equity_amount'] / data['acquisition_price'] * 100) if data['acquisition_price'] > 0 else 0
        eq_delta = "✅ Confortable" if equity_pct >= 30 else "⚠️ Juste" if equity_pct >= 20 else "❌ Faible"
        st.metric(
            "Equity",
            f"{equity_pct:.1f}%",
            delta=eq_delta,
            help="Part de capitaux propres. Recommandé: >30%"
        )

    # Détail calculs
    with st.expander("📋 Détail des Calculs", expanded=False):
        st.markdown("### Calcul DSCR")
        st.code(f"""
EBITDA Normalisé:        {data['ebitda_normalized']:,.0f} €

Intérêts annuels:        {data['debt_amount'] * data['interest_rate']:,.0f} €
  (Dette {data['debt_amount']:,.0f} € × Taux {data['interest_rate']*100:.1f}%)

Amortissement annuel:    {data['debt_amount']/data['duration']:,.0f} €
  (Dette {data['debt_amount']:,.0f} € / {data['duration']} ans)

Service Dette Total:     {data['debt_amount'] * data['interest_rate'] + data['debt_amount']/data['duration']:,.0f} €

DSCR = EBITDA / Service Dette
     = {data['ebitda_normalized']:,.0f} / {data['debt_amount'] * data['interest_rate'] + data['debt_amount']/data['duration']:,.0f}
     = {dscr:.2f}

Interprétation:
  • DSCR ≥ 1.25 : 🟢 Capacité confortable
  • DSCR 1.0-1.25 : 🟡 Capacité juste
  • DSCR < 1.0 : 🔴 Capacité insuffisante
        """)

        st.markdown("### Calcul Dette/EBITDA")
        st.code(f"""
Dette Totale:            {data['debt_amount']:,.0f} €
EBITDA Normalisé:        {data['ebitda_normalized']:,.0f} €

Leverage = Dette / EBITDA
         = {data['debt_amount']:,.0f} / {data['ebitda_normalized']:,.0f}
         = {leverage:.2f}x

Interprétation:
  • Leverage ≤ 4.0x : 🟢 Endettement raisonnable
  • Leverage 4.0-5.0x : 🟡 Endettement élevé
  • Leverage > 5.0x : 🔴 Endettement excessif
        """)

    # Recommandations
    st.divider()
    st.subheader("💡 Recommandations")

    recommendations = []

    if dscr < 1.25:
        recommendations.append("⚠️ **DSCR faible**: Augmenter l'equity ou négocier un meilleur prix")

    if leverage > 4.0:
        recommendations.append("⚠️ **Leverage élevé**: Réduire le prix d'acquisition ou augmenter l'apport")

    if equity_pct < 30:
        recommendations.append("⚠️ **Equity faible**: Augmenter les capitaux propres pour sécuriser le montage")

    if data['interest_rate'] > 0.05:
        recommendations.append("💡 Taux d'intérêt élevé - Négocier avec plusieurs banques pour obtenir de meilleures conditions")

    if not recommendations:
        recommendations.append("✅ Le montage semble équilibré et viable")

    for rec in recommendations:
        st.markdown(f"- {rec}")

    # Simulation rapide
    st.divider()
    st.subheader("🔄 Simulation Rapide")

    st.markdown("**Testez l'impact de changements sur le DSCR:**")

    col1, col2 = st.columns(2)

    with col1:
        test_equity_pct = st.slider(
            "Nouveau % Equity",
            min_value=10,
            max_value=50,
            value=int(equity_pct),
            step=5,
            format="%d%%"
        )

        new_equity = data['acquisition_price'] * (test_equity_pct / 100)
        new_debt = data['acquisition_price'] - new_equity
        new_dscr = calculate_dscr(
            data['ebitda_normalized'],
            new_debt,
            data['interest_rate'],
            data['duration']
        )

        st.metric(
            "DSCR avec nouveau montage",
            f"{new_dscr:.2f}",
            delta=f"{new_dscr - dscr:+.2f}"
        )

    with col2:
        test_price = st.slider(
            "Nouveau Prix (M€)",
            min_value=int(data['acquisition_price'] * 0.7 / 1_000_000),
            max_value=int(data['acquisition_price'] * 1.3 / 1_000_000),
            value=int(data['acquisition_price'] / 1_000_000),
            step=1
        )

        new_price = test_price * 1_000_000
        new_debt_price = new_price - data['equity_amount']
        new_dscr_price = calculate_dscr(
            data['ebitda_normalized'],
            new_debt_price,
            data['interest_rate'],
            data['duration']
        )

        st.metric(
            "DSCR avec nouveau prix",
            f"{new_dscr_price:.2f}",
            delta=f"{new_dscr_price - dscr:+.2f}"
        )

# =============================================================================
# FOOTER
# =============================================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📖 Guide Rapide**")
    st.caption("1. Saisir les données financières")
    st.caption("2. Définir le montage LBO")
    st.caption("3. Analyser la viabilité")

with col2:
    st.markdown("**🎯 Seuils Clés**")
    st.caption("DSCR: >1.25 (bon)")
    st.caption("Dette/EBITDA: <4.0x (bon)")
    st.caption("Equity: >30% (recommandé)")

with col3:
    st.markdown("**💡 Besoin d'aide?**")
    st.caption("DSCR = Capacité de remboursement")
    st.caption("Leverage = Niveau d'endettement")

st.caption("Analyse LBO Simplifiée v1.0 - Février 2026")
