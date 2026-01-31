"""
Fabrique de graphiques Plotly pour l'analyse financiere.

Ce module fournit la classe ChartFactory qui genere differents types
de visualisations interactives pour les metriques financieres.

Types de graphiques disponibles:
- Gauge charts pour les KPIs
- Waterfall charts pour la decomposition
- Barres groupees pour la comparaison de scenarios
- Lignes pour l'analyse de sensibilite
- Radar charts pour la comparaison 360
- Evolution temporelle multi-metriques
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# =============================================================================
# CONFIGURATION DES COULEURS
# =============================================================================

@dataclass
class ColorPalette:
    """Palette de couleurs pour les graphiques."""
    primary: str = "#1f77b4"
    secondary: str = "#ff7f0e"
    success: str = "#2ca02c"
    warning: str = "#ffbb00"
    danger: str = "#d62728"
    info: str = "#17becf"
    light: str = "#e0e0e0"
    dark: str = "#2c3e50"

    # Couleurs pour les scenarios
    scenario_colors: tuple = (
        "#1f77b4",  # Bleu
        "#ff7f0e",  # Orange
        "#2ca02c",  # Vert
        "#d62728",  # Rouge
        "#9467bd",  # Violet
        "#8c564b",  # Marron
        "#e377c2",  # Rose
        "#7f7f7f",  # Gris
    )

    # Couleurs pour les metriques
    metric_colors: dict = None

    def __post_init__(self):
        if self.metric_colors is None:
            self.metric_colors = {
                "DSCR": "#1f77b4",
                "ICR": "#ff7f0e",
                "ROE": "#2ca02c",
                "ROA": "#d62728",
                "TRI": "#9467bd",
                "VAN": "#8c564b",
            }


COLORS = ColorPalette()


# =============================================================================
# CLASSE PRINCIPALE
# =============================================================================

class ChartFactory:
    """
    Fabrique de graphiques Plotly pour l'analyse financiere.

    Cette classe genere des graphiques interactifs standardises pour
    visualiser les metriques financieres selon differentes perspectives.

    Tous les graphiques sont:
    - Interactifs (zoom, hover, export)
    - Responsifs (s'adaptent au container)
    - Accessibles (tooltips detailles)

    Example:
        >>> factory = ChartFactory()
        >>> gauge_fig = factory.create_metrics_gauge(
        ...     metrics={"DSCR": 1.45, "ICR": 3.2},
        ...     category="banker"
        ... )
        >>> st.plotly_chart(gauge_fig, use_container_width=True)
    """

    def __init__(self, color_palette: Optional[ColorPalette] = None):
        """
        Initialise la fabrique de graphiques.

        Args:
            color_palette: Palette de couleurs personnalisee (optionnel)
        """
        self.colors = color_palette or COLORS

    # =========================================================================
    # METHODE 1: GAUGE CHARTS
    # =========================================================================

    def create_metrics_gauge(
        self,
        metrics: Dict[str, float],
        category: str = "standard",
        benchmarks: Optional[Dict[str, Dict[str, float]]] = None,
        title: Optional[str] = None
    ) -> go.Figure:
        """
        Cree des gauge charts pour les KPIs.

        Chaque metrique est affichee dans un indicateur circulaire avec
        des zones colorees selon les seuils de reference.

        Args:
            metrics: Dictionnaire {nom_metrique: valeur}
            category: Categorie des metriques ("banker", "entrepreneur", "standard")
            benchmarks: Seuils de reference {metrique: {excellent, good, acceptable, risky}}
            title: Titre global du graphique (optionnel)

        Returns:
            go.Figure: Figure Plotly avec les gauges

        Example:
            >>> fig = factory.create_metrics_gauge(
            ...     metrics={"DSCR": 1.45, "ICR": 3.2},
            ...     category="banker",
            ...     benchmarks={
            ...         "DSCR": {"excellent": 2.0, "good": 1.5, "acceptable": 1.2, "risky": 1.0},
            ...         "ICR": {"excellent": 5.0, "good": 3.0, "acceptable": 2.0, "risky": 1.5}
            ...     }
            ... )
        """
        if not metrics:
            return self._create_empty_figure("Aucune metrique disponible")

        n_metrics = len(metrics)
        if n_metrics == 0:
            return self._create_empty_figure("Aucune metrique a afficher")

        # Creer une grille de sous-graphiques
        cols = min(n_metrics, 4)
        rows = (n_metrics + cols - 1) // cols

        fig = make_subplots(
            rows=rows,
            cols=cols,
            specs=[[{"type": "indicator"} for _ in range(cols)] for _ in range(rows)],
            horizontal_spacing=0.1,
            vertical_spacing=0.15
        )

        # Default benchmarks par categorie
        default_benchmarks = self._get_default_benchmarks(category)
        benchmarks = benchmarks or default_benchmarks

        for idx, (metric_name, value) in enumerate(metrics.items()):
            if value is None:
                continue

            row = idx // cols + 1
            col = idx % cols + 1

            # Recuperer les seuils pour cette metrique
            metric_benchmarks = benchmarks.get(metric_name, {})
            max_value = self._calculate_gauge_max(value, metric_benchmarks)

            # Determiner les etapes de couleur
            steps = self._create_gauge_steps(metric_benchmarks, max_value)

            # Determiner le seuil d'alerte
            threshold_value = metric_benchmarks.get("acceptable", max_value * 0.6)

            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=value,
                    title={"text": metric_name, "font": {"size": 14}},
                    number={"font": {"size": 20}, "suffix": self._get_metric_suffix(metric_name)},
                    gauge={
                        "axis": {
                            "range": [0, max_value],
                            "tickwidth": 1,
                            "tickcolor": self.colors.dark
                        },
                        "bar": {"color": self.colors.primary, "thickness": 0.3},
                        "bgcolor": "white",
                        "borderwidth": 2,
                        "bordercolor": self.colors.light,
                        "steps": steps,
                        "threshold": {
                            "line": {"color": self.colors.danger, "width": 3},
                            "thickness": 0.8,
                            "value": threshold_value
                        }
                    }
                ),
                row=row,
                col=col
            )

        # Mise en forme globale
        fig.update_layout(
            title=title or f"Indicateurs {category.capitalize()}",
            height=200 * rows + 50,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor="white",
            font=dict(family="Arial, sans-serif")
        )

        return fig

    # =========================================================================
    # METHODE 2: WATERFALL CHART
    # =========================================================================

    def create_waterfall_chart(
        self,
        metric_name: str,
        components: Dict[str, float],
        title: Optional[str] = None,
        show_total: bool = True
    ) -> go.Figure:
        """
        Cree un waterfall chart pour decomposer une metrique.

        Visualise comment les differentes composantes s'additionnent
        ou se soustraient pour arriver au resultat final.

        Args:
            metric_name: Nom de la metrique finale
            components: Dictionnaire {composante: valeur} (positif = ajout, negatif = soustraction)
            title: Titre du graphique (optionnel)
            show_total: Afficher la barre de total (defaut: True)

        Returns:
            go.Figure: Figure Plotly waterfall

        Example:
            >>> fig = factory.create_waterfall_chart(
            ...     metric_name="DSCR",
            ...     components={
            ...         "EBITDA": 280000,
            ...         "Interets": -25000,
            ...         "Remboursement capital": -50000
            ...     }
            ... )
        """
        if not components:
            return self._create_empty_figure("Aucune composante disponible")

        # Preparer les donnees
        labels = list(components.keys())
        values = list(components.values())

        # Calculer le total
        total = sum(values)

        # Determiner les mesures (relative pour les composantes, total pour le final)
        measures = ["relative"] * len(values)
        if show_total:
            labels.append(metric_name)
            values.append(total)
            measures.append("total")

        # Formater les textes
        text_values = []
        for v in values[:-1] if show_total else values:
            if abs(v) >= 1_000_000:
                text_values.append(f"{v/1_000_000:,.1f}M")
            elif abs(v) >= 1_000:
                text_values.append(f"{v/1_000:,.0f}k")
            else:
                text_values.append(f"{v:,.0f}")

        if show_total:
            if abs(total) >= 1_000_000:
                text_values.append(f"{total/1_000_000:,.1f}M")
            elif abs(total) >= 1_000:
                text_values.append(f"{total/1_000:,.0f}k")
            else:
                text_values.append(f"{total:,.2f}")

        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=measures,
            x=labels,
            y=values,
            text=text_values,
            textposition="outside",
            connector={"line": {"color": self.colors.dark, "width": 1, "dash": "dot"}},
            increasing={"marker": {"color": self.colors.success}},
            decreasing={"marker": {"color": self.colors.danger}},
            totals={"marker": {"color": self.colors.primary}}
        ))

        fig.update_layout(
            title=title or f"Decomposition {metric_name}",
            xaxis_title="Composantes",
            yaxis_title="Valeur (EUR)",
            showlegend=False,
            height=400,
            margin=dict(l=60, r=40, t=60, b=60),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(family="Arial, sans-serif")
        )

        fig.update_yaxes(
            gridcolor=self.colors.light,
            zerolinecolor=self.colors.dark,
            zerolinewidth=2
        )

        return fig

    # =========================================================================
    # METHODE 3: COMPARAISON DE SCENARIOS
    # =========================================================================

    def create_scenario_comparison(
        self,
        scenarios: List[Dict[str, Any]],
        metrics: List[str],
        title: Optional[str] = None
    ) -> go.Figure:
        """
        Cree un graphique a barres groupees pour comparer des scenarios.

        Compare plusieurs scenarios cote a cote sur une selection de metriques.

        Args:
            scenarios: Liste de dictionnaires {name: str, metrics: dict}
            metrics: Liste des noms de metriques a comparer
            title: Titre du graphique (optionnel)

        Returns:
            go.Figure: Figure Plotly avec barres groupees

        Example:
            >>> scenarios = [
            ...     {"name": "Base", "metrics": {"DSCR": 1.2, "ROE": 15.0}},
            ...     {"name": "Optimiste", "metrics": {"DSCR": 1.5, "ROE": 18.0}},
            ...     {"name": "Pessimiste", "metrics": {"DSCR": 0.9, "ROE": 10.0}}
            ... ]
            >>> fig = factory.create_scenario_comparison(
            ...     scenarios=scenarios,
            ...     metrics=["DSCR", "ROE"]
            ... )
        """
        if not scenarios or not metrics:
            return self._create_empty_figure("Donnees de comparaison insuffisantes")

        fig = go.Figure()

        # Ajouter une trace par scenario
        for idx, scenario in enumerate(scenarios):
            scenario_name = scenario.get("name", f"Scenario {idx + 1}")
            scenario_metrics = scenario.get("metrics", {})

            values = [scenario_metrics.get(m, 0) for m in metrics]

            fig.add_trace(go.Bar(
                name=scenario_name,
                x=metrics,
                y=values,
                marker_color=self.colors.scenario_colors[idx % len(self.colors.scenario_colors)],
                text=[f"{v:.2f}" for v in values],
                textposition="outside"
            ))

        fig.update_layout(
            title=title or "Comparaison des Scenarios",
            xaxis_title="Metriques",
            yaxis_title="Valeur",
            barmode="group",
            bargap=0.15,
            bargroupgap=0.1,
            height=450,
            margin=dict(l=60, r=40, t=60, b=60),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(family="Arial, sans-serif"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        fig.update_yaxes(gridcolor=self.colors.light)

        return fig

    # =========================================================================
    # METHODE 4: ANALYSE DE SENSIBILITE
    # =========================================================================

    def create_sensitivity_analysis(
        self,
        param_name: str,
        param_range: List[float],
        metric_results: Dict[str, List[float]],
        title: Optional[str] = None,
        base_value: Optional[float] = None
    ) -> go.Figure:
        """
        Cree un graphique d'analyse de sensibilite.

        Montre comment les metriques evoluent en fonction d'un parametre.

        Args:
            param_name: Nom du parametre teste
            param_range: Liste des valeurs du parametre
            metric_results: Dictionnaire {metrique: liste_valeurs}
            title: Titre du graphique (optionnel)
            base_value: Valeur de base du parametre (pour la ligne verticale)

        Returns:
            go.Figure: Figure Plotly avec lignes de sensibilite

        Example:
            >>> fig = factory.create_sensitivity_analysis(
            ...     param_name="Taux d'interet",
            ...     param_range=[3.0, 4.0, 5.0, 6.0, 7.0],
            ...     metric_results={
            ...         "DSCR": [1.8, 1.5, 1.3, 1.1, 0.9],
            ...         "ICR": [5.0, 4.2, 3.5, 2.9, 2.4]
            ...     },
            ...     base_value=5.0
            ... )
        """
        if not param_range or not metric_results:
            return self._create_empty_figure("Donnees de sensibilite insuffisantes")

        fig = go.Figure()

        # Ajouter une ligne par metrique
        for idx, (metric_name, results) in enumerate(metric_results.items()):
            color = self.colors.scenario_colors[idx % len(self.colors.scenario_colors)]

            fig.add_trace(go.Scatter(
                x=param_range,
                y=results,
                mode="lines+markers",
                name=metric_name,
                line=dict(color=color, width=2),
                marker=dict(size=8, color=color),
                hovertemplate=f"{metric_name}<br>{param_name}: %{{x}}<br>Valeur: %{{y:.2f}}<extra></extra>"
            ))

        # Ajouter une ligne verticale pour la valeur de base
        if base_value is not None:
            fig.add_vline(
                x=base_value,
                line_dash="dash",
                line_color=self.colors.dark,
                annotation_text="Valeur de base",
                annotation_position="top"
            )

        fig.update_layout(
            title=title or f"Analyse de Sensibilite - {param_name}",
            xaxis_title=param_name,
            yaxis_title="Valeur de la metrique",
            height=400,
            margin=dict(l=60, r=40, t=60, b=60),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(family="Arial, sans-serif"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="x unified"
        )

        fig.update_xaxes(gridcolor=self.colors.light)
        fig.update_yaxes(gridcolor=self.colors.light)

        return fig

    # =========================================================================
    # METHODE 5: RADAR CHART
    # =========================================================================

    def create_radar_chart(
        self,
        metrics: Dict[str, float],
        benchmarks: Optional[Dict[str, float]] = None,
        title: Optional[str] = None,
        normalize: bool = True
    ) -> go.Figure:
        """
        Cree un radar chart pour une vue 360 des metriques.

        Compare les valeurs de l'entreprise avec des benchmarks sectoriels.

        Args:
            metrics: Dictionnaire {metrique: valeur} pour l'entreprise
            benchmarks: Dictionnaire {metrique: valeur} pour le benchmark
            title: Titre du graphique (optionnel)
            normalize: Normaliser les valeurs pour une meilleure comparaison

        Returns:
            go.Figure: Figure Plotly radar

        Example:
            >>> fig = factory.create_radar_chart(
            ...     metrics={"DSCR": 1.3, "ICR": 2.8, "ROE": 15, "Liquidite": 1.5, "Levier": 0.6},
            ...     benchmarks={"DSCR": 1.5, "ICR": 3.5, "ROE": 12, "Liquidite": 1.2, "Levier": 0.5}
            ... )
        """
        if not metrics:
            return self._create_empty_figure("Aucune metrique disponible")

        # Preparer les donnees
        categories = list(metrics.keys())
        enterprise_values = list(metrics.values())

        # Normaliser si demande
        if normalize and benchmarks:
            benchmark_values = [benchmarks.get(cat, 1) for cat in categories]
            # Normaliser par rapport aux benchmarks
            enterprise_normalized = [
                (v / b * 100) if b != 0 else 0
                for v, b in zip(enterprise_values, benchmark_values)
            ]
            benchmark_normalized = [100] * len(categories)  # 100% pour le benchmark
        else:
            enterprise_normalized = enterprise_values
            benchmark_normalized = [benchmarks.get(cat, 0) for cat in categories] if benchmarks else None

        fig = go.Figure()

        # Trace pour l'entreprise
        fig.add_trace(go.Scatterpolar(
            r=enterprise_normalized + [enterprise_normalized[0]],  # Fermer le polygone
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor=f"rgba(31, 119, 180, 0.3)",
            line=dict(color=self.colors.primary, width=2),
            name="Entreprise",
            hovertemplate="%{theta}: %{r:.1f}<extra></extra>"
        ))

        # Trace pour le benchmark si disponible
        if benchmark_normalized:
            fig.add_trace(go.Scatterpolar(
                r=benchmark_normalized + [benchmark_normalized[0]],
                theta=categories + [categories[0]],
                fill="toself",
                fillcolor=f"rgba(255, 127, 14, 0.2)",
                line=dict(color=self.colors.secondary, width=2, dash="dash"),
                name="Benchmark",
                hovertemplate="%{theta}: %{r:.1f}<extra></extra>"
            ))

        fig.update_layout(
            title=title or "Analyse 360 - Radar",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(enterprise_normalized) * 1.2] if normalize else None,
                    gridcolor=self.colors.light
                ),
                angularaxis=dict(
                    gridcolor=self.colors.light
                ),
                bgcolor="white"
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            height=450,
            margin=dict(l=80, r=80, t=60, b=80),
            paper_bgcolor="white",
            font=dict(family="Arial, sans-serif")
        )

        return fig

    # =========================================================================
    # METHODE 6: EVOLUTION TEMPORELLE
    # =========================================================================

    def create_evolution_chart(
        self,
        years: List[Union[int, str]],
        metrics: Dict[str, List[float]],
        title: Optional[str] = None,
        show_markers: bool = True,
        secondary_y: Optional[List[str]] = None
    ) -> go.Figure:
        """
        Cree un graphique d'evolution temporelle multi-metriques.

        Visualise l'evolution de plusieurs metriques sur plusieurs annees.

        Args:
            years: Liste des annees/periodes
            metrics: Dictionnaire {metrique: liste_valeurs_par_annee}
            title: Titre du graphique (optionnel)
            show_markers: Afficher les marqueurs sur les lignes
            secondary_y: Liste des metriques a afficher sur l'axe Y secondaire

        Returns:
            go.Figure: Figure Plotly avec evolution temporelle

        Example:
            >>> fig = factory.create_evolution_chart(
            ...     years=[2020, 2021, 2022, 2023],
            ...     metrics={
            ...         "CA (M EUR)": [1.0, 1.2, 1.5, 1.8],
            ...         "EBITDA (k EUR)": [200, 250, 300, 350],
            ...         "Marge (%)": [20, 21, 20, 19]
            ...     },
            ...     secondary_y=["Marge (%)"]
            ... )
        """
        if not years or not metrics:
            return self._create_empty_figure("Donnees d'evolution insuffisantes")

        secondary_y = secondary_y or []

        # Creer le graphique avec axe secondaire si necessaire
        if secondary_y:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
        else:
            fig = go.Figure()

        # Ajouter une trace par metrique
        for idx, (metric_name, values) in enumerate(metrics.items()):
            if len(values) != len(years):
                continue

            color = self.colors.scenario_colors[idx % len(self.colors.scenario_colors)]
            is_secondary = metric_name in secondary_y

            mode = "lines+markers" if show_markers else "lines"

            trace = go.Scatter(
                x=years,
                y=values,
                mode=mode,
                name=metric_name,
                line=dict(color=color, width=2),
                marker=dict(size=8, color=color) if show_markers else None,
                hovertemplate=f"{metric_name}<br>Annee: %{{x}}<br>Valeur: %{{y:,.2f}}<extra></extra>"
            )

            if secondary_y:
                fig.add_trace(trace, secondary_y=is_secondary)
            else:
                fig.add_trace(trace)

        # Configuration du layout
        layout_config = dict(
            title=title or "Evolution Temporelle",
            xaxis_title="Periode",
            height=400,
            margin=dict(l=60, r=60, t=60, b=60),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(family="Arial, sans-serif"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="x unified"
        )

        if secondary_y:
            fig.update_layout(
                **layout_config,
                yaxis_title="Valeur principale",
                yaxis2_title="Valeur secondaire"
            )
            fig.update_yaxes(gridcolor=self.colors.light, secondary_y=False)
            fig.update_yaxes(gridcolor=self.colors.light, secondary_y=True)
        else:
            fig.update_layout(**layout_config, yaxis_title="Valeur")
            fig.update_yaxes(gridcolor=self.colors.light)

        fig.update_xaxes(gridcolor=self.colors.light)

        return fig

    # =========================================================================
    # METHODES UTILITAIRES PRIVEES
    # =========================================================================

    def _create_empty_figure(self, message: str) -> go.Figure:
        """Cree une figure vide avec un message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color=self.colors.dark)
        )
        fig.update_layout(
            height=300,
            paper_bgcolor="white",
            plot_bgcolor="white"
        )
        return fig

    def _get_default_benchmarks(self, category: str) -> Dict[str, Dict[str, float]]:
        """Retourne les benchmarks par defaut selon la categorie."""
        if category == "banker":
            return {
                "DSCR": {"excellent": 2.0, "good": 1.5, "acceptable": 1.2, "risky": 1.0},
                "ICR": {"excellent": 5.0, "good": 3.0, "acceptable": 2.0, "risky": 1.5},
                "Leverage": {"excellent": 0.3, "good": 0.5, "acceptable": 0.7, "risky": 1.0},
            }
        elif category == "entrepreneur":
            return {
                "ROE": {"excellent": 20, "good": 15, "acceptable": 10, "risky": 5},
                "TRI": {"excellent": 25, "good": 18, "acceptable": 12, "risky": 8},
                "Multiple": {"excellent": 3.0, "good": 2.5, "acceptable": 2.0, "risky": 1.5},
            }
        else:
            return {
                "Marge EBITDA": {"excellent": 25, "good": 15, "acceptable": 10, "risky": 5},
                "Liquidite": {"excellent": 2.0, "good": 1.5, "acceptable": 1.0, "risky": 0.8},
            }

    def _calculate_gauge_max(self, value: float, benchmarks: Dict[str, float]) -> float:
        """Calcule la valeur maximale pour un gauge."""
        if benchmarks:
            excellent = benchmarks.get("excellent", value * 1.5)
            return max(value * 1.3, excellent * 1.2)
        return value * 1.5 if value > 0 else 100

    def _create_gauge_steps(
        self,
        benchmarks: Dict[str, float],
        max_value: float
    ) -> List[Dict[str, Any]]:
        """Cree les etapes de couleur pour un gauge."""
        if not benchmarks:
            return [
                {"range": [0, max_value * 0.4], "color": "#ffebee"},  # Rouge clair
                {"range": [max_value * 0.4, max_value * 0.7], "color": "#fff3e0"},  # Orange clair
                {"range": [max_value * 0.7, max_value], "color": "#e8f5e9"},  # Vert clair
            ]

        risky = benchmarks.get("risky", max_value * 0.3)
        acceptable = benchmarks.get("acceptable", max_value * 0.5)
        good = benchmarks.get("good", max_value * 0.7)

        return [
            {"range": [0, risky], "color": "#ffebee"},
            {"range": [risky, acceptable], "color": "#fff3e0"},
            {"range": [acceptable, good], "color": "#fff8e1"},
            {"range": [good, max_value], "color": "#e8f5e9"},
        ]

    def _get_metric_suffix(self, metric_name: str) -> str:
        """Retourne le suffixe approprie pour une metrique."""
        metric_lower = metric_name.lower()

        if any(x in metric_lower for x in ["marge", "roe", "roa", "tri", "taux", "%"]):
            return "%"
        elif "multiple" in metric_lower or "x" in metric_lower:
            return "x"
        elif any(x in metric_lower for x in ["dscr", "icr", "ratio"]):
            return ""
        else:
            return ""


# =============================================================================
# INSTANCE GLOBALE
# =============================================================================

# Instance globale pour usage facile
chart_factory = ChartFactory()


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def create_kpi_card_figure(
    value: float,
    title: str,
    subtitle: Optional[str] = None,
    delta: Optional[float] = None,
    delta_reference: Optional[float] = None,
    color: str = "primary"
) -> go.Figure:
    """
    Cree une figure pour un KPI card simple.

    Args:
        value: Valeur du KPI
        title: Titre du KPI
        subtitle: Sous-titre optionnel
        delta: Variation en valeur absolue
        delta_reference: Valeur de reference pour le delta
        color: Couleur principale ("primary", "success", "danger", etc.)

    Returns:
        go.Figure: Figure Plotly indicator
    """
    color_map = {
        "primary": COLORS.primary,
        "success": COLORS.success,
        "warning": COLORS.warning,
        "danger": COLORS.danger,
        "info": COLORS.info,
    }

    bar_color = color_map.get(color, COLORS.primary)

    fig = go.Figure(go.Indicator(
        mode="number+delta" if delta is not None else "number",
        value=value,
        title={"text": f"{title}<br><span style='font-size:0.7em;color:gray'>{subtitle or ''}</span>"},
        delta={"reference": delta_reference, "relative": True} if delta_reference else None,
        number={"font": {"size": 36, "color": bar_color}},
    ))

    fig.update_layout(
        height=150,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="white"
    )

    return fig
