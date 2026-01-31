"""
Dashboards Streamlit pour l'analyse financiere.

Ce module fournit des classes de dashboard specialisees pour
differentes perspectives d'analyse financiere.

Dashboards disponibles:
- BankerDashboard: Perspective risque et solvabilite
- EntrepreneurDashboard: Perspective rentabilite et creation de valeur
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Any, List

import streamlit as st

# Ajoute le repertoire racine au path pour les imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.visualization.charts import ChartFactory, chart_factory


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def format_currency(value: float, precision: int = 0) -> str:
    """Formate une valeur en euros."""
    if value is None:
        return "N/A"
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:,.{precision}f} M EUR".replace(",", " ")
    elif abs(value) >= 1_000:
        return f"{value/1_000:,.{precision}f} k EUR".replace(",", " ")
    else:
        return f"{value:,.{precision}f} EUR".replace(",", " ")


def format_percentage(value: float, precision: int = 1) -> str:
    """Formate une valeur en pourcentage."""
    if value is None:
        return "N/A"
    return f"{value:.{precision}f}%"


def format_ratio(value: float, precision: int = 2) -> str:
    """Formate un ratio."""
    if value is None:
        return "N/A"
    if value == float('inf'):
        return "+"
    if value == float('-inf'):
        return "-"
    return f"{value:.{precision}f}"


def get_rating_color(value: float, thresholds: Dict[str, float], higher_is_better: bool = True) -> str:
    """
    Retourne la couleur selon le rating.

    Args:
        value: Valeur a evaluer
        thresholds: Seuils {excellent, good, acceptable, risky}
        higher_is_better: Si True, une valeur plus haute est meilleure

    Returns:
        str: Nom de la couleur CSS
    """
    if value is None:
        return "gray"

    excellent = thresholds.get("excellent", float('inf') if higher_is_better else float('-inf'))
    good = thresholds.get("good", 0)
    acceptable = thresholds.get("acceptable", 0)

    if higher_is_better:
        if value >= excellent:
            return "green"
        elif value >= good:
            return "lightgreen"
        elif value >= acceptable:
            return "orange"
        else:
            return "red"
    else:
        if value <= excellent:
            return "green"
        elif value <= good:
            return "lightgreen"
        elif value <= acceptable:
            return "orange"
        else:
            return "red"


def get_status_delta(value: float, thresholds: Dict[str, float], higher_is_better: bool = True) -> str:
    """
    Retourne le status pour le delta Streamlit.

    Args:
        value: Valeur a evaluer
        thresholds: Seuils {excellent, good, acceptable, risky}
        higher_is_better: Si True, une valeur plus haute est meilleure

    Returns:
        str: Label de status
    """
    if value is None:
        return "N/A"

    excellent = thresholds.get("excellent", float('inf') if higher_is_better else float('-inf'))
    good = thresholds.get("good", 0)
    acceptable = thresholds.get("acceptable", 0)

    if higher_is_better:
        if value >= excellent:
            return "Excellent"
        elif value >= good:
            return "Bon"
        elif value >= acceptable:
            return "Acceptable"
        else:
            return "Risque"
    else:
        if value <= excellent:
            return "Excellent"
        elif value <= good:
            return "Bon"
        elif value <= acceptable:
            return "Acceptable"
        else:
            return "Risque"


# =============================================================================
# CLASSE BANKER DASHBOARD
# =============================================================================

class BankerDashboard:
    """
    Dashboard oriente perspective Banquier.

    Affiche les metriques cles pour evaluer le risque credit
    et la capacite de remboursement de l'entreprise.

    Metriques principales:
    - DSCR (Debt Service Coverage Ratio)
    - ICR (Interest Coverage Ratio)
    - Ratio de levier
    - Solvabilite

    Example:
        >>> dashboard = BankerDashboard()
        >>> dashboard.render(scenario_data, metrics_results)
    """

    # Seuils de reference pour les metriques banquier
    BENCHMARKS = {
        "DSCR": {"excellent": 2.0, "good": 1.5, "acceptable": 1.2, "risky": 1.0},
        "ICR": {"excellent": 5.0, "good": 3.0, "acceptable": 2.0, "risky": 1.5},
        "Ratio de levier": {"excellent": 0.3, "good": 0.5, "acceptable": 0.7, "risky": 1.0},
        "Solvabilite": {"excellent": 0.4, "good": 0.3, "acceptable": 0.2, "risky": 0.1},
        "Fonds de Roulement": {"excellent": 0, "good": 0, "acceptable": 0, "risky": 0},
        "BFR": {"excellent": 0, "good": 0, "acceptable": 0, "risky": 0},
    }

    def __init__(self, chart_factory_instance: Optional[ChartFactory] = None):
        """
        Initialise le dashboard banquier.

        Args:
            chart_factory_instance: Instance de ChartFactory (optionnel)
        """
        self.charts = chart_factory_instance or chart_factory

    def render(
        self,
        scenario_data: Dict[str, Any],
        metrics: Dict[str, float],
        show_details: bool = True
    ) -> None:
        """
        Affiche le dashboard banquier complet.

        Args:
            scenario_data: Donnees du scenario applique
            metrics: Dictionnaire des metriques calculees
            show_details: Afficher les sections detaillees
        """
        st.header("Dashboard Banquier")
        st.markdown("*Analyse du risque credit et de la capacite de remboursement*")

        # Section 1: KPIs principaux
        self._render_kpis(metrics)

        st.divider()

        # Section 2: Graphiques
        if show_details:
            col1, col2 = st.columns(2)

            with col1:
                self._render_debt_coverage_chart(scenario_data, metrics)

            with col2:
                self._render_solvency_gauges(metrics)

            st.divider()

            # Section 3: Analyse detaillee
            self._render_detailed_analysis(scenario_data, metrics)

    def _render_kpis(self, metrics: Dict[str, float]) -> None:
        """Affiche les KPIs principaux."""
        col1, col2, col3, col4 = st.columns(4)

        # DSCR
        with col1:
            dscr = metrics.get("DSCR")
            if dscr is not None:
                thresholds = self.BENCHMARKS["DSCR"]
                status = get_status_delta(dscr, thresholds)
                st.metric(
                    label="DSCR",
                    value=format_ratio(dscr),
                    delta=status,
                    delta_color="normal" if dscr >= thresholds["acceptable"] else "inverse",
                    help="Debt Service Coverage Ratio - Capacite a couvrir le service de la dette"
                )
            else:
                st.metric(label="DSCR", value="N/A", help="Donnees insuffisantes")

        # ICR
        with col2:
            icr = metrics.get("ICR")
            if icr is not None:
                thresholds = self.BENCHMARKS["ICR"]
                status = get_status_delta(icr, thresholds)
                st.metric(
                    label="ICR",
                    value=format_ratio(icr),
                    delta=status,
                    delta_color="normal" if icr >= thresholds["acceptable"] else "inverse",
                    help="Interest Coverage Ratio - Capacite a couvrir les interets"
                )
            else:
                st.metric(label="ICR", value="N/A", help="Donnees insuffisantes")

        # Ratio de levier
        with col3:
            leverage = metrics.get("Ratio de levier") or metrics.get("Leverage Ratio")
            if leverage is not None:
                thresholds = self.BENCHMARKS["Ratio de levier"]
                status = get_status_delta(leverage, thresholds, higher_is_better=False)
                st.metric(
                    label="Levier (D/E)",
                    value=format_ratio(leverage),
                    delta=status,
                    delta_color="normal" if leverage <= thresholds["acceptable"] else "inverse",
                    help="Ratio dette/capitaux propres"
                )
            else:
                st.metric(label="Levier (D/E)", value="N/A", help="Donnees insuffisantes")

        # Solvabilite
        with col4:
            solvency = metrics.get("Solvabilite") or metrics.get("Autonomie Financiere")
            if solvency is not None:
                # Convertir en pourcentage si necessaire
                if solvency < 1:
                    solvency_pct = solvency * 100
                else:
                    solvency_pct = solvency
                thresholds = {k: v * 100 for k, v in self.BENCHMARKS["Solvabilite"].items()}
                status = get_status_delta(solvency_pct, thresholds)
                st.metric(
                    label="Solvabilite",
                    value=format_percentage(solvency_pct),
                    delta=status,
                    delta_color="normal" if solvency_pct >= thresholds["acceptable"] else "inverse",
                    help="Ratio capitaux propres / total bilan"
                )
            else:
                st.metric(label="Solvabilite", value="N/A", help="Donnees insuffisantes")

    def _render_debt_coverage_chart(
        self,
        scenario_data: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> None:
        """Affiche le waterfall de couverture de dette."""
        st.subheader("Couverture de la Dette")

        # Extraire les composantes
        scenario_info = scenario_data.get("scenario", {})

        ebitda = scenario_data.get("profitability", {}).get("ebitda", {}).get("value", 0)
        interest = scenario_data.get("expenses", {}).get("financial", {}).get("interest_expense", {}).get("value", 0)
        debt_service = scenario_info.get("annual_debt_service", 0)
        principal = max(0, debt_service - interest)

        if ebitda > 0 or debt_service > 0:
            components = {
                "EBITDA": ebitda,
                "- Interets": -interest,
                "- Capital": -principal,
            }

            fig = self.charts.create_waterfall_chart(
                metric_name="Cash disponible",
                components=components,
                title="Decomposition du Service de Dette"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Donnees insuffisantes pour afficher la decomposition")

    def _render_solvency_gauges(self, metrics: Dict[str, float]) -> None:
        """Affiche les gauges de solvabilite."""
        st.subheader("Ratios de Solvabilite")

        # Preparer les metriques pour les gauges
        gauge_metrics = {}

        dscr = metrics.get("DSCR")
        if dscr is not None:
            gauge_metrics["DSCR"] = dscr

        icr = metrics.get("ICR")
        if icr is not None:
            gauge_metrics["ICR"] = min(icr, 10)  # Plafonner a 10 pour la lisibilite

        if gauge_metrics:
            fig = self.charts.create_metrics_gauge(
                metrics=gauge_metrics,
                category="banker",
                benchmarks=self.BENCHMARKS,
                title=""
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune metrique disponible pour les gauges")

    def _render_detailed_analysis(
        self,
        scenario_data: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> None:
        """Affiche l'analyse detaillee."""
        st.subheader("Analyse Detaillee")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Structure Financiere**")

            # Fonds de roulement
            fr = metrics.get("Fonds de Roulement")
            if fr is not None:
                color = "green" if fr >= 0 else "red"
                st.markdown(f"Fonds de Roulement: <span style='color:{color}'>{format_currency(fr)}</span>",
                           unsafe_allow_html=True)

            # BFR
            bfr = metrics.get("BFR")
            if bfr is not None:
                st.markdown(f"Besoin en Fonds de Roulement: {format_currency(bfr)}")

            # Tresorerie nette
            if fr is not None and bfr is not None:
                tresorerie = fr - bfr
                color = "green" if tresorerie >= 0 else "red"
                st.markdown(f"Tresorerie Nette: <span style='color:{color}'>{format_currency(tresorerie)}</span>",
                           unsafe_allow_html=True)

        with col2:
            st.markdown("**Capacite de Remboursement**")

            scenario_info = scenario_data.get("scenario", {})

            # Service de dette annuel
            debt_service = scenario_info.get("annual_debt_service", 0)
            st.markdown(f"Service de dette annuel: {format_currency(debt_service)}")

            # Duree restante
            duration = scenario_info.get("loan_duration")
            if duration:
                st.markdown(f"Duree du pret: {duration} ans")

            # Ratio D/EBITDA
            ebitda = scenario_data.get("profitability", {}).get("ebitda", {}).get("value", 0)
            total_debt = scenario_info.get("debt_amount", 0)
            if ebitda > 0 and total_debt > 0:
                d_ebitda = total_debt / ebitda
                color = "green" if d_ebitda <= 3 else "orange" if d_ebitda <= 5 else "red"
                st.markdown(f"Ratio Dette/EBITDA: <span style='color:{color}'>{d_ebitda:.1f}x</span>",
                           unsafe_allow_html=True)

        # Recommandation
        st.divider()
        st.markdown("**Recommandation**")

        dscr = metrics.get("DSCR", 0)
        icr = metrics.get("ICR", 0)

        if dscr >= 1.5 and icr >= 3.0:
            st.success("Profil de risque FAIBLE - L'entreprise presente une bonne capacite de remboursement.")
        elif dscr >= 1.2 and icr >= 2.0:
            st.warning("Profil de risque MODERE - Capacite de remboursement correcte mais a surveiller.")
        else:
            st.error("Profil de risque ELEVE - Capacite de remboursement insuffisante, risque de defaut.")


# =============================================================================
# CLASSE ENTREPRENEUR DASHBOARD
# =============================================================================

class EntrepreneurDashboard:
    """
    Dashboard oriente perspective Entrepreneur.

    Affiche les metriques cles pour evaluer la rentabilite
    et la creation de valeur pour les investisseurs.

    Metriques principales:
    - TRI (Taux de Rendement Interne)
    - VAN (Valeur Actuelle Nette)
    - ROE (Return on Equity)
    - Multiple sur equity

    Example:
        >>> dashboard = EntrepreneurDashboard()
        >>> dashboard.render(scenario_data, metrics_results)
    """

    # Seuils de reference pour les metriques entrepreneur
    BENCHMARKS = {
        "TRI": {"excellent": 25, "good": 18, "acceptable": 12, "risky": 8},
        "ROE": {"excellent": 20, "good": 15, "acceptable": 10, "risky": 5},
        "Multiple": {"excellent": 3.0, "good": 2.5, "acceptable": 2.0, "risky": 1.5},
        "Payback": {"excellent": 3, "good": 5, "acceptable": 7, "risky": 10},
        "Marge EBITDA": {"excellent": 25, "good": 15, "acceptable": 10, "risky": 5},
        "Marge Nette": {"excellent": 15, "good": 10, "acceptable": 5, "risky": 2},
    }

    def __init__(self, chart_factory_instance: Optional[ChartFactory] = None):
        """
        Initialise le dashboard entrepreneur.

        Args:
            chart_factory_instance: Instance de ChartFactory (optionnel)
        """
        self.charts = chart_factory_instance or chart_factory

    def render(
        self,
        scenario_data: Dict[str, Any],
        metrics: Dict[str, float],
        show_details: bool = True
    ) -> None:
        """
        Affiche le dashboard entrepreneur complet.

        Args:
            scenario_data: Donnees du scenario applique
            metrics: Dictionnaire des metriques calculees
            show_details: Afficher les sections detaillees
        """
        st.header("Dashboard Entrepreneur")
        st.markdown("*Analyse de la rentabilite et de la creation de valeur*")

        # Section 1: KPIs principaux
        self._render_kpis(scenario_data, metrics)

        st.divider()

        # Section 2: Graphiques
        if show_details:
            col1, col2 = st.columns(2)

            with col1:
                self._render_value_creation_chart(scenario_data, metrics)

            with col2:
                self._render_profitability_radar(metrics)

            st.divider()

            # Section 3: Analyse detaillee
            self._render_detailed_analysis(scenario_data, metrics)

    def _render_kpis(
        self,
        scenario_data: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> None:
        """Affiche les KPIs principaux."""
        col1, col2, col3 = st.columns(3)

        scenario_info = scenario_data.get("scenario", {})

        # TRI ou ROE
        with col1:
            roe = metrics.get("ROE")
            if roe is not None:
                # Convertir en pourcentage si necessaire
                if roe < 1:
                    roe_pct = roe * 100
                else:
                    roe_pct = roe
                thresholds = self.BENCHMARKS["ROE"]
                status = get_status_delta(roe_pct, thresholds)
                st.metric(
                    label="ROE",
                    value=format_percentage(roe_pct),
                    delta=status,
                    delta_color="normal" if roe_pct >= thresholds["acceptable"] else "inverse",
                    help="Return on Equity - Rentabilite des capitaux propres"
                )
            else:
                st.metric(label="ROE", value="N/A", help="Donnees insuffisantes")

        # VAN (ou Resultat net)
        with col2:
            net_income = scenario_data.get("income_statement", {}).get("net_income", 0)
            if net_income is None:
                net_income = metrics.get("Resultat Net", 0)

            if net_income:
                status = "Benefice" if net_income >= 0 else "Perte"
                st.metric(
                    label="Resultat Net",
                    value=format_currency(net_income),
                    delta=status,
                    delta_color="normal" if net_income >= 0 else "inverse",
                    help="Resultat net de l'exercice"
                )
            else:
                st.metric(label="Resultat Net", value="N/A", help="Donnees insuffisantes")

        # Multiple ou Payback
        with col3:
            payback = metrics.get("Payback Period") or metrics.get("Payback")
            if payback is not None and payback != float('inf'):
                thresholds = self.BENCHMARKS["Payback"]
                status = get_status_delta(payback, thresholds, higher_is_better=False)
                st.metric(
                    label="Payback Period",
                    value=f"{payback:.1f} ans",
                    delta=status,
                    delta_color="normal" if payback <= thresholds["acceptable"] else "inverse",
                    help="Duree de recuperation de l'investissement"
                )
            else:
                equity_multiple = scenario_info.get("equity_multiple", metrics.get("Multiple"))
                if equity_multiple:
                    thresholds = self.BENCHMARKS["Multiple"]
                    status = get_status_delta(equity_multiple, thresholds)
                    st.metric(
                        label="Multiple Equity",
                        value=f"{equity_multiple:.1f}x",
                        delta=status,
                        delta_color="normal" if equity_multiple >= thresholds["acceptable"] else "inverse",
                        help="Multiple sur l'investissement en equity"
                    )
                else:
                    st.metric(label="Payback / Multiple", value="N/A", help="Donnees insuffisantes")

    def _render_value_creation_chart(
        self,
        scenario_data: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> None:
        """Affiche le waterfall de creation de valeur."""
        st.subheader("Creation de Valeur")

        # Extraire les composantes du compte de resultat
        income_statement = scenario_data.get("income_statement", {})
        revenues = income_statement.get("revenues", {})
        expenses = income_statement.get("operating_expenses", {})

        ca = revenues.get("net_revenue") or revenues.get("total", 0)
        if isinstance(ca, dict):
            ca = ca.get("value", 0)

        achats = expenses.get("purchases_of_goods", 0) + expenses.get("purchases_of_raw_materials", 0)
        charges_ext = expenses.get("external_charges", 0)
        personnel = expenses.get("wages_and_salaries", 0) + expenses.get("social_charges", 0)
        impots = income_statement.get("income_tax_expense", 0)
        resultat_net = income_statement.get("net_income", 0)

        if ca > 0:
            # Simplifier pour le waterfall
            components = {
                "Chiffre d'affaires": ca,
                "- Achats": -achats,
                "- Charges ext.": -charges_ext,
                "- Personnel": -personnel,
                "- Impots": -impots,
            }

            fig = self.charts.create_waterfall_chart(
                metric_name="Resultat Net",
                components=components,
                title="Du CA au Resultat Net"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Donnees insuffisantes pour afficher la creation de valeur")

    def _render_profitability_radar(self, metrics: Dict[str, float]) -> None:
        """Affiche le radar de rentabilite."""
        st.subheader("Profil de Rentabilite")

        # Preparer les metriques pour le radar
        radar_metrics = {}
        radar_benchmarks = {}

        # Marges
        marge_brute = metrics.get("Marge Brute")
        if marge_brute is not None:
            radar_metrics["Marge Brute"] = marge_brute if marge_brute > 1 else marge_brute * 100
            radar_benchmarks["Marge Brute"] = 40

        marge_exploitation = metrics.get("Marge d'Exploitation") or metrics.get("Marge Exploitation")
        if marge_exploitation is not None:
            radar_metrics["Marge Exploitation"] = marge_exploitation if marge_exploitation > 1 else marge_exploitation * 100
            radar_benchmarks["Marge Exploitation"] = 15

        marge_nette = metrics.get("Marge Nette")
        if marge_nette is not None:
            radar_metrics["Marge Nette"] = marge_nette if marge_nette > 1 else marge_nette * 100
            radar_benchmarks["Marge Nette"] = 8

        # ROE
        roe = metrics.get("ROE")
        if roe is not None:
            radar_metrics["ROE"] = roe if roe > 1 else roe * 100
            radar_benchmarks["ROE"] = 15

        # EBITDA
        ebitda_margin = metrics.get("Marge EBITDA")
        if ebitda_margin is not None:
            radar_metrics["Marge EBITDA"] = ebitda_margin if ebitda_margin > 1 else ebitda_margin * 100
            radar_benchmarks["Marge EBITDA"] = 20

        if len(radar_metrics) >= 3:
            fig = self.charts.create_radar_chart(
                metrics=radar_metrics,
                benchmarks=radar_benchmarks,
                title="",
                normalize=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Metriques insuffisantes pour le radar (minimum 3)")

    def _render_detailed_analysis(
        self,
        scenario_data: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> None:
        """Affiche l'analyse detaillee."""
        st.subheader("Analyse Detaillee")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Marges et Rentabilite**")

            # Marge brute
            marge_brute = metrics.get("Marge Brute")
            if marge_brute is not None:
                pct = marge_brute if marge_brute > 1 else marge_brute * 100
                st.markdown(f"Marge Brute: {pct:.1f}%")

            # Marge EBITDA
            ebitda_margin = metrics.get("Marge EBITDA")
            if ebitda_margin is not None:
                pct = ebitda_margin if ebitda_margin > 1 else ebitda_margin * 100
                color = "green" if pct >= 15 else "orange" if pct >= 10 else "red"
                st.markdown(f"Marge EBITDA: <span style='color:{color}'>{pct:.1f}%</span>",
                           unsafe_allow_html=True)

            # Marge nette
            marge_nette = metrics.get("Marge Nette")
            if marge_nette is not None:
                pct = marge_nette if marge_nette > 1 else marge_nette * 100
                color = "green" if pct >= 5 else "orange" if pct >= 2 else "red"
                st.markdown(f"Marge Nette: <span style='color:{color}'>{pct:.1f}%</span>",
                           unsafe_allow_html=True)

        with col2:
            st.markdown("**Structure de l'Investissement**")

            scenario_info = scenario_data.get("scenario", {})

            # Financement total
            total_financing = scenario_info.get("total_financing", 0)
            if total_financing > 0:
                st.markdown(f"Financement total: {format_currency(total_financing)}")

            # Repartition dette/equity
            debt = scenario_info.get("debt_amount", 0)
            equity = scenario_info.get("equity_amount", 0)

            if debt > 0 or equity > 0:
                total = debt + equity
                if total > 0:
                    debt_pct = debt / total * 100
                    equity_pct = equity / total * 100
                    st.markdown(f"Dette: {format_currency(debt)} ({debt_pct:.0f}%)")
                    st.markdown(f"Equity: {format_currency(equity)} ({equity_pct:.0f}%)")

            # Ratio de levier
            leverage = scenario_info.get("leverage_ratio", 0)
            if leverage:
                st.markdown(f"Levier (D/Total): {leverage:.1%}")

        # Recommandation
        st.divider()
        st.markdown("**Recommandation**")

        roe = metrics.get("ROE", 0)
        if roe < 1:
            roe = roe * 100  # Convertir en pourcentage

        marge_nette = metrics.get("Marge Nette", 0)
        if marge_nette < 1:
            marge_nette = marge_nette * 100

        if roe >= 15 and marge_nette >= 5:
            st.success("Profil ATTRACTIF - Bonne rentabilite et marges satisfaisantes pour les investisseurs.")
        elif roe >= 10 and marge_nette >= 3:
            st.warning("Profil CORRECT - Rentabilite acceptable mais potentiel d'amelioration.")
        else:
            st.error("Profil FAIBLE - Rentabilite insuffisante, revision du business plan recommandee.")


# =============================================================================
# CLASSE COMPLETE DASHBOARD
# =============================================================================

class CompleteDashboard:
    """
    Dashboard combinant les perspectives Banquier et Entrepreneur.

    Offre une vue 360 de la situation financiere de l'entreprise.
    """

    def __init__(self, chart_factory_instance: Optional[ChartFactory] = None):
        """Initialise le dashboard complet."""
        self.charts = chart_factory_instance or chart_factory
        self.banker_dashboard = BankerDashboard(chart_factory_instance)
        self.entrepreneur_dashboard = EntrepreneurDashboard(chart_factory_instance)

    def render(
        self,
        scenario_data: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> None:
        """Affiche le dashboard complet."""
        st.header("Analyse Financiere Complete")
        st.markdown("*Vue 360 de la situation financiere*")

        # Resume executif
        self._render_executive_summary(scenario_data, metrics)

        st.divider()

        # Onglets pour les deux perspectives
        tab_banker, tab_entrepreneur = st.tabs([
            "Perspective Banquier",
            "Perspective Entrepreneur"
        ])

        with tab_banker:
            self.banker_dashboard.render(scenario_data, metrics, show_details=True)

        with tab_entrepreneur:
            self.entrepreneur_dashboard.render(scenario_data, metrics, show_details=True)

    def _render_executive_summary(
        self,
        scenario_data: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> None:
        """Affiche le resume executif."""
        st.subheader("Resume Executif")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            ca = scenario_data.get("revenues", {}).get("total", {}).get("value", 0)
            if ca == 0:
                ca = scenario_data.get("income_statement", {}).get("revenues", {}).get("net_revenue", 0)
            st.metric("Chiffre d'Affaires", format_currency(ca))

        with col2:
            ebitda = scenario_data.get("profitability", {}).get("ebitda", {}).get("value", 0)
            st.metric("EBITDA", format_currency(ebitda))

        with col3:
            dscr = metrics.get("DSCR")
            st.metric("DSCR", format_ratio(dscr) if dscr else "N/A")

        with col4:
            roe = metrics.get("ROE")
            if roe is not None:
                roe_pct = roe if roe > 1 else roe * 100
                st.metric("ROE", format_percentage(roe_pct))
            else:
                st.metric("ROE", "N/A")
