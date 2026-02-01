"""
Générateur de rapports PDF professionnels pour analyses LBO.

Supporte 2 templates:
- Template Banquier (focus risque/DSCR)
- Template Investisseur (focus ROI/TRI)
"""

from typing import Dict, List, Optional
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        Image
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFGenerator:
    """
    Générateur de rapports PDF professionnels.

    Utilise ReportLab pour créer des PDFs formatés avec:
    - Page de garde professionnelle
    - Executive summary
    - Métriques clés
    - Graphiques (si disponibles)
    - Recommandations
    """

    def __init__(self):
        """Initialise le générateur PDF."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "ReportLab n'est pas installé. "
                "Installez-le avec: pip install reportlab"
            )

        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configure les styles personnalisés."""
        # Titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Sous-titre
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#7F8C8D'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))

        # Heading custom
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2980B9'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Status (GO/WATCH/NO-GO)
        self.styles.add(ParagraphStyle(
            name='StatusGO',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#27AE60'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='StatusWATCH',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#F39C12'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='StatusNOGO',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#E74C3C'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))

    def create_banker_report(
        self,
        company_name: str,
        financial_data: Dict,
        lbo_structure: Dict,
        norm_data: Dict,
        stress_results: List[Dict],
        decision: Dict,
        projections: List[Dict]
    ) -> BytesIO:
        """
        Créer rapport banquier (focus risque).

        Args:
            company_name: Nom entreprise
            financial_data: Données financières
            lbo_structure: Structure LBO
            norm_data: Données normalisées
            stress_results: Résultats stress tests
            decision: Décision finale
            projections: Projections 7 ans

        Returns:
            BytesIO avec PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        story = []

        # PAGE DE GARDE
        story.extend(self._create_cover_page(
            company_name,
            "Analyse de Risque LBO",
            "Perspective Banquier"
        ))

        story.append(PageBreak())

        # EXECUTIVE SUMMARY
        story.extend(self._create_executive_summary_banker(
            company_name,
            lbo_structure,
            norm_data,
            decision
        ))

        story.append(PageBreak())

        # STRUCTURE FINANCEMENT
        story.extend(self._create_financing_structure(lbo_structure, norm_data))

        # MÉTRIQUES DE RISQUE
        story.append(Paragraph("2. Métriques de Risque", self.styles['CustomHeading']))
        story.extend(self._create_risk_metrics_table(lbo_structure, norm_data, projections))

        story.append(Spacer(1, 0.2*inch))

        # STRESS TESTS
        story.append(Paragraph("3. Stress Tests", self.styles['CustomHeading']))
        story.extend(self._create_stress_tests_table(stress_results))

        story.append(PageBreak())

        # COVENANT TRACKING
        story.append(Paragraph("4. Covenant Tracking (7 ans)", self.styles['CustomHeading']))
        story.extend(self._create_covenant_table(projections))

        # DÉCISION & RECOMMANDATIONS
        story.append(PageBreak())
        story.extend(self._create_decision_section(decision, perspective="banker"))

        # Build PDF
        doc.build(story)

        buffer.seek(0)
        return buffer

    def create_investor_report(
        self,
        company_name: str,
        financial_data: Dict,
        lbo_structure: Dict,
        norm_data: Dict,
        decision: Dict,
        projections: List[Dict]
    ) -> BytesIO:
        """
        Créer rapport investisseur (focus ROI).

        Args:
            company_name: Nom entreprise
            financial_data: Données financières
            lbo_structure: Structure LBO
            norm_data: Données normalisées
            decision: Décision finale
            projections: Projections 7 ans

        Returns:
            BytesIO avec PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        story = []

        # PAGE DE GARDE
        story.extend(self._create_cover_page(
            company_name,
            "Analyse d'Investissement LBO",
            "Perspective Investisseur"
        ))

        story.append(PageBreak())

        # EXECUTIVE SUMMARY
        story.extend(self._create_executive_summary_investor(
            company_name,
            lbo_structure,
            norm_data,
            decision,
            projections
        ))

        story.append(PageBreak())

        # CRÉATION DE VALEUR
        story.extend(self._create_value_creation_section(
            lbo_structure,
            norm_data,
            projections
        ))

        # Build PDF
        doc.build(story)

        buffer.seek(0)
        return buffer

    def _create_cover_page(
        self,
        company_name: str,
        title: str,
        subtitle: str
    ) -> List:
        """Créer page de garde."""
        elements = []

        elements.append(Spacer(1, 2*inch))

        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Paragraph(company_name, self.styles['Subtitle']))
        elements.append(Paragraph(subtitle, self.styles['Normal']))

        elements.append(Spacer(1, 1*inch))

        date_str = datetime.now().strftime("%d %B %Y")
        elements.append(Paragraph(
            f"Date: {date_str}",
            self.styles['Normal']
        ))

        elements.append(Spacer(1, 2*inch))

        elements.append(Paragraph(
            "CONFIDENTIEL",
            self.styles['CustomTitle']
        ))

        return elements

    def _create_executive_summary_banker(
        self,
        company_name: str,
        lbo_structure: Dict,
        norm_data: Dict,
        decision: Dict
    ) -> List:
        """Créer executive summary banquier."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['CustomTitle']))

        elements.append(Spacer(1, 0.2*inch))

        # Décision
        decision_value = decision.get("decision", {}).get("value", "N/A")
        score = decision.get("overall_score", 0)

        if decision_value == "GO":
            style = self.styles['StatusGO']
            icon = "✓"
        elif decision_value == "WATCH":
            style = self.styles['StatusWATCH']
            icon = "⚠"
        else:
            style = self.styles['StatusNOGO']
            icon = "✗"

        elements.append(Paragraph(
            f"{icon} DÉCISION: {decision_value}",
            style
        ))

        elements.append(Paragraph(
            f"Score global: {score}/100",
            self.styles['Normal']
        ))

        elements.append(Spacer(1, 0.3*inch))

        # Tableau synthèse
        data = [
            ['Métrique', 'Valeur'],
            ['Prix d\'acquisition', f"{lbo_structure.get('acquisition_price', 0):,.0f} €"],
            ['Dette totale', f"{lbo_structure.get('total_debt', 0):,.0f} €"],
            ['Equity', f"{lbo_structure.get('equity_amount', 0):,.0f} €"],
            ['EBITDA normalisé', f"{norm_data.get('ebitda_bank', 0):,.0f} €"],
            ['Multiple acquisition', f"{lbo_structure.get('acquisition_price', 0) / norm_data.get('ebitda_bank', 1):.1f}x"],
        ]

        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))

        elements.append(table)

        return elements

    def _create_executive_summary_investor(
        self,
        company_name: str,
        lbo_structure: Dict,
        norm_data: Dict,
        decision: Dict,
        projections: List[Dict]
    ) -> List:
        """Créer executive summary investisseur."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['CustomTitle']))

        # Calculs ROI approximatifs
        equity = lbo_structure.get('equity_amount', 1)
        exit_year = min(5, len(projections) - 1)

        if exit_year > 0:
            exit_ebitda = projections[exit_year].get('ebitda', norm_data.get('ebitda_bank', 0))
            exit_multiple = 6.0  # Hypothèse conservative
            exit_value = exit_ebitda * exit_multiple

            # Dette résiduelle (approximation)
            debt_paid = lbo_structure.get('total_debt', 0) * 0.6  # 60% remboursé
            remaining_debt = lbo_structure.get('total_debt', 0) - debt_paid

            proceeds_to_equity = exit_value - remaining_debt
            multiple_money = proceeds_to_equity / equity if equity > 0 else 0
            irr_approx = (multiple_money ** (1/exit_year) - 1) * 100
        else:
            multiple_money = 0
            irr_approx = 0

        # Tableau
        data = [
            ['Métrique', 'Valeur'],
            ['Equity investi', f"{equity:,.0f} €"],
            ['Multiple argent (Y5)', f"{multiple_money:.1f}x"],
            ['TRI estimé', f"{irr_approx:.1f}%"],
            ['Décision', decision.get("decision", {}).get("value", "N/A")],
        ]

        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980B9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#EBF5FB')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))

        elements.append(table)

        return elements

    def _create_financing_structure(
        self,
        lbo_structure: Dict,
        norm_data: Dict
    ) -> List:
        """Créer section structure financement."""
        elements = []

        elements.append(Paragraph("1. Structure de Financement", self.styles['CustomHeading']))

        # Tableau tranches dette
        data = [['Tranche', 'Montant', 'Taux', 'Durée']]

        for layer in lbo_structure.get('debt_layers', []):
            data.append([
                layer.get('name', ''),
                f"{layer.get('amount', 0):,.0f} €",
                f"{layer.get('interest_rate', 0) * 100:.1f}%",
                f"{layer.get('duration_years', 0)} ans"
            ])

        # Equity
        data.append([
            'Equity',
            f"{lbo_structure.get('equity_amount', 0):,.0f} €",
            '-',
            '-'
        ])

        table = Table(data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _create_risk_metrics_table(
        self,
        lbo_structure: Dict,
        norm_data: Dict,
        projections: List[Dict]
    ) -> List:
        """Créer tableau métriques de risque."""
        elements = []

        # Extraire métriques
        dscr_min = min([p.get('dscr', 999) for p in projections]) if projections else 0
        leverage = lbo_structure.get('total_debt', 0) / norm_data.get('ebitda_bank', 1)

        data = [
            ['Métrique', 'Valeur', 'Seuil', 'Statut'],
            ['DSCR minimum (7 ans)', f"{dscr_min:.2f}", '> 1.25', '✓' if dscr_min > 1.25 else '✗'],
            ['Dette/EBITDA', f"{leverage:.2f}x", '< 4.0x', '✓' if leverage < 4.0 else '✗'],
        ]

        table = Table(data, colWidths=[2.5*inch, 1.2*inch, 1*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E74C3C')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))

        elements.append(table)

        return elements

    def _create_stress_tests_table(self, stress_results: List[Dict]) -> List:
        """Créer tableau stress tests."""
        elements = []

        data = [['Scénario', 'DSCR', 'Dette/EBITDA', 'Statut']]

        for result in stress_results[:7]:  # Top 7
            scenario = result["scenario"]
            metrics = result["metrics"]

            from src.scenarios.stress_tester import StressTester
            status = StressTester.get_status_from_metrics(metrics)

            data.append([
                scenario.name,
                f"{metrics.get('dscr_min', 0):.2f}",
                f"{metrics.get('leverage', 0):.2f}x",
                status
            ])

        table = Table(data, colWidths=[2*inch, 1.2*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))

        elements.append(table)

        return elements

    def _create_covenant_table(self, projections: List[Dict]) -> List:
        """Créer tableau covenant tracking."""
        elements = []

        data = [['Année', 'DSCR', 'Dette/EBITDA', 'Covenant OK']]

        for i, proj in enumerate(projections):
            dscr = proj.get('dscr', 0)
            leverage = proj.get('net_debt_to_ebitda', 0)
            covenant_ok = dscr > 1.25 and leverage < 4.0

            data.append([
                f"Y{i+1}",
                f"{dscr:.2f}",
                f"{leverage:.2f}x",
                '✓' if covenant_ok else '✗'
            ])

        table = Table(data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980B9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))

        elements.append(table)

        return elements

    def _create_decision_section(self, decision: Dict, perspective: str = "banker") -> List:
        """Créer section décision et recommandations."""
        elements = []

        elements.append(Paragraph("5. Décision & Recommandations", self.styles['CustomHeading']))

        # Warnings
        if decision.get('warnings'):
            elements.append(Paragraph("Points d'Attention:", self.styles['Heading3']))
            for warning in decision.get('warnings', []):
                elements.append(Paragraph(f"• {warning}", self.styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))

        # Recommandations
        if decision.get('recommendations'):
            elements.append(Paragraph("Recommandations:", self.styles['Heading3']))
            for rec in decision.get('recommendations', []):
                elements.append(Paragraph(f"• {rec}", self.styles['Normal']))

        return elements

    def _create_value_creation_section(
        self,
        lbo_structure: Dict,
        norm_data: Dict,
        projections: List[Dict]
    ) -> List:
        """Créer section création de valeur (investisseur)."""
        elements = []

        elements.append(Paragraph("Création de Valeur", self.styles['CustomHeading']))

        # Tableau projections
        data = [['Année', 'CA (M€)', 'EBITDA (M€)', 'FCF (k€)']]

        for i, proj in enumerate(projections):
            data.append([
                f"Y{i+1}",
                f"{proj.get('revenue', 0) / 1_000_000:.1f}",
                f"{proj.get('ebitda', 0) / 1_000_000:.1f}",
                f"{proj.get('fcf', 0) / 1_000:.0f}"
            ])

        table = Table(data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))

        elements.append(table)

        return elements


# Test du module
if __name__ == "__main__":
    print("✅ Module pdf_generator.py chargé avec succès")

    if REPORTLAB_AVAILABLE:
        print("✅ ReportLab disponible - Export PDF fonctionnel")
    else:
        print("⚠️ ReportLab non installé - pip install reportlab")
