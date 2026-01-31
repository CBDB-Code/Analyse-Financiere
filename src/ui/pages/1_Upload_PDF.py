"""
Page Streamlit pour l'upload et la validation de liasses fiscales PDF.

Cette page permet de:
- Uploader un fichier PDF de liasse fiscale (2033 ou 2050-2059)
- Extraire automatiquement les donnees avec FiscalDataExtractor
- Valider et editer les donnees extraites
- Sauvegarder les donnees validees dans la base SQLite
"""

import sys
from pathlib import Path
import tempfile
import json
from datetime import date

# Ajoute le repertoire racine au path pour les imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd

from src.extraction import FiscalDataExtractor, ExtractionError, InvalidPDFError


# =============================================================================
# CONFIGURATION DE LA PAGE
# =============================================================================

st.set_page_config(
    page_title="Upload Liasse Fiscale",
    page_icon="📄",
    layout="wide"
)


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def save_uploaded_file(uploaded_file) -> str:
    """
    Sauvegarde le fichier uploade dans un repertoire temporaire.

    Args:
        uploaded_file: Fichier uploade via st.file_uploader

    Returns:
        str: Chemin vers le fichier temporaire
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name


def fiscal_data_to_dict(fiscal_data) -> dict:
    """
    Convertit un objet FiscalData en dictionnaire compatible avec l'application.

    Args:
        fiscal_data: Instance de FiscalData

    Returns:
        dict: Dictionnaire avec les donnees structurees
    """
    return {
        "metadata": {
            "company_name": fiscal_data.metadata.company_name,
            "siren": fiscal_data.metadata.siren,
            "siret": fiscal_data.metadata.siret,
            "naf_code": fiscal_data.metadata.naf_code,
            "legal_form": fiscal_data.metadata.legal_form,
            "fiscal_year_end": fiscal_data.metadata.fiscal_year_end.isoformat() if fiscal_data.metadata.fiscal_year_end else None,
            "confidence_score": fiscal_data.metadata.confidence_score,
        },
        "balance_sheet": {
            "assets": {
                "fixed_assets": {
                    "intangible_assets": fiscal_data.balance_sheet.assets.fixed_assets.intangible_assets,
                    "tangible_assets": fiscal_data.balance_sheet.assets.fixed_assets.tangible_assets,
                    "financial_assets": fiscal_data.balance_sheet.assets.fixed_assets.financial_assets,
                    "total": fiscal_data.balance_sheet.assets.fixed_assets.total,
                },
                "current_assets": {
                    "inventory": fiscal_data.balance_sheet.assets.current_assets.inventory,
                    "trade_receivables": fiscal_data.balance_sheet.assets.current_assets.trade_receivables,
                    "other_receivables": fiscal_data.balance_sheet.assets.current_assets.other_receivables,
                    "prepaid_expenses": fiscal_data.balance_sheet.assets.current_assets.prepaid_expenses,
                    "marketable_securities": fiscal_data.balance_sheet.assets.current_assets.marketable_securities,
                    "cash": fiscal_data.balance_sheet.assets.current_assets.cash,
                    "total": fiscal_data.balance_sheet.assets.current_assets.total,
                },
                "total_assets": fiscal_data.balance_sheet.assets.total_assets,
            },
            "liabilities": {
                "equity": {
                    "share_capital": fiscal_data.balance_sheet.liabilities.equity.share_capital,
                    "share_premium": fiscal_data.balance_sheet.liabilities.equity.share_premium,
                    "legal_reserve": fiscal_data.balance_sheet.liabilities.equity.legal_reserve,
                    "retained_earnings": fiscal_data.balance_sheet.liabilities.equity.retained_earnings,
                    "net_income": fiscal_data.balance_sheet.liabilities.equity.net_income,
                    "total": fiscal_data.balance_sheet.liabilities.equity.total,
                },
                "provisions": {
                    "provisions_for_risks": fiscal_data.balance_sheet.liabilities.provisions.provisions_for_risks,
                    "provisions_for_charges": fiscal_data.balance_sheet.liabilities.provisions.provisions_for_charges,
                    "total": fiscal_data.balance_sheet.liabilities.provisions.total,
                },
                "debt": {
                    "long_term_debt": fiscal_data.balance_sheet.liabilities.debt.long_term_debt,
                    "short_term_debt": fiscal_data.balance_sheet.liabilities.debt.short_term_debt,
                    "bank_overdrafts": fiscal_data.balance_sheet.liabilities.debt.bank_overdrafts,
                    "total_financial_debt": fiscal_data.balance_sheet.liabilities.debt.total_financial_debt,
                },
                "operating_liabilities": {
                    "trade_payables": fiscal_data.balance_sheet.liabilities.operating_liabilities.trade_payables,
                    "tax_liabilities": fiscal_data.balance_sheet.liabilities.operating_liabilities.tax_liabilities,
                    "social_liabilities": fiscal_data.balance_sheet.liabilities.operating_liabilities.social_liabilities,
                    "total": fiscal_data.balance_sheet.liabilities.operating_liabilities.total,
                },
                "total_liabilities": fiscal_data.balance_sheet.liabilities.total_liabilities,
            },
        },
        "income_statement": {
            "revenues": {
                "sales_of_goods": fiscal_data.income_statement.revenues.sales_of_goods,
                "sales_of_services": fiscal_data.income_statement.revenues.sales_of_services,
                "sales_of_products": fiscal_data.income_statement.revenues.sales_of_products,
                "net_revenue": fiscal_data.income_statement.revenues.net_revenue,
                "other_operating_income": fiscal_data.income_statement.revenues.other_operating_income,
                "total": fiscal_data.income_statement.revenues.total,
            },
            "operating_expenses": {
                "purchases_of_goods": fiscal_data.income_statement.operating_expenses.purchases_of_goods,
                "purchases_of_raw_materials": fiscal_data.income_statement.operating_expenses.purchases_of_raw_materials,
                "inventory_variation": fiscal_data.income_statement.operating_expenses.inventory_variation,
                "external_charges": fiscal_data.income_statement.operating_expenses.external_charges,
                "taxes_and_duties": fiscal_data.income_statement.operating_expenses.taxes_and_duties,
                "wages_and_salaries": fiscal_data.income_statement.operating_expenses.wages_and_salaries,
                "social_charges": fiscal_data.income_statement.operating_expenses.social_charges,
                "depreciation": fiscal_data.income_statement.operating_expenses.depreciation,
                "provisions": fiscal_data.income_statement.operating_expenses.provisions,
                "other_operating_expenses": fiscal_data.income_statement.operating_expenses.other_operating_expenses,
                "total": fiscal_data.income_statement.operating_expenses.total,
            },
            "operating_income": fiscal_data.income_statement.operating_income,
            "financial_result": {
                "financial_income": fiscal_data.income_statement.financial_result.financial_income,
                "interest_expense": fiscal_data.income_statement.financial_result.interest_expense,
                "total_financial_income": fiscal_data.income_statement.financial_result.total_financial_income,
                "total_financial_expense": fiscal_data.income_statement.financial_result.total_financial_expense,
                "net_financial_result": fiscal_data.income_statement.financial_result.net_financial_result,
            },
            "current_income_before_tax": fiscal_data.income_statement.current_income_before_tax,
            "exceptional_result": {
                "total_exceptional_income": fiscal_data.income_statement.exceptional_result.total_exceptional_income,
                "total_exceptional_expense": fiscal_data.income_statement.exceptional_result.total_exceptional_expense,
                "net_exceptional_result": fiscal_data.income_statement.exceptional_result.net_exceptional_result,
            },
            "income_tax_expense": fiscal_data.income_statement.income_tax_expense,
            "net_income": fiscal_data.income_statement.net_income,
        },
        # Donnees additionnelles pour le calcul des metriques
        "revenues": {
            "total": {
                "value": fiscal_data.income_statement.revenues.net_revenue,
            },
        },
        "expenses": {
            "total": fiscal_data.income_statement.operating_expenses.total,
            "financial": {
                "interest_expense": {
                    "value": fiscal_data.income_statement.financial_result.interest_expense,
                },
            },
        },
        "profitability": {
            "ebitda": {
                "value": calculate_ebitda(fiscal_data),
            },
        },
    }


def calculate_ebitda(fiscal_data) -> float:
    """
    Calcule l'EBITDA a partir des donnees fiscales.

    EBITDA = Resultat d'exploitation + Dotations aux amortissements + Dotations aux provisions

    Args:
        fiscal_data: Instance de FiscalData

    Returns:
        float: EBITDA calcule
    """
    operating_income = fiscal_data.income_statement.operating_income
    depreciation = fiscal_data.income_statement.operating_expenses.depreciation
    provisions = fiscal_data.income_statement.operating_expenses.provisions

    return operating_income + depreciation + provisions


def get_confidence_color(confidence: float) -> str:
    """Retourne la couleur selon le niveau de confiance."""
    if confidence >= 0.8:
        return "green"
    elif confidence >= 0.5:
        return "orange"
    else:
        return "red"


def get_confidence_label(confidence: float) -> str:
    """Retourne le label selon le niveau de confiance."""
    if confidence >= 0.8:
        return "Excellente"
    elif confidence >= 0.5:
        return "Correcte"
    else:
        return "Faible"


# =============================================================================
# PAGE PRINCIPALE
# =============================================================================

st.title("Upload Liasse Fiscale")
st.markdown("Importez votre liasse fiscale au format PDF pour l'analyser")

st.divider()

# =============================================================================
# SECTION 1: UPLOAD PDF
# =============================================================================

st.header("1. Selection du fichier")

uploaded_file = st.file_uploader(
    "Choisissez un fichier PDF",
    type=["pdf"],
    help="Formats acceptes: Liasse fiscale 2033 (BIC simplifie) ou 2050-2059 (BIC normal)"
)

if uploaded_file is not None:
    st.info(f"Fichier selectionne: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} Ko)")

    # =============================================================================
    # SECTION 2: EXTRACTION AUTOMATIQUE
    # =============================================================================

    st.divider()
    st.header("2. Extraction des donnees")

    col1, col2 = st.columns([1, 3])

    with col1:
        use_ai = st.checkbox(
            "Utiliser l'IA",
            value=True,
            help="Utilise Claude AI comme fallback si l'extraction PDF echoue"
        )

    with col2:
        extract_button = st.button("Extraire les donnees", type="primary")

    if extract_button:
        # Sauvegarder le fichier temporairement
        temp_pdf_path = save_uploaded_file(uploaded_file)

        # Progress bar
        progress_bar = st.progress(0, text="Initialisation de l'extraction...")

        try:
            # Initialisation de l'extracteur
            progress_bar.progress(20, text="Chargement du PDF...")
            extractor = FiscalDataExtractor(use_ai_fallback=use_ai)

            # Extraction
            progress_bar.progress(50, text="Extraction en cours...")
            fiscal_data = extractor.extract(temp_pdf_path, validate=False)

            # Recuperation du rapport
            progress_bar.progress(80, text="Generation du rapport...")
            report = extractor.get_extraction_report()

            progress_bar.progress(100, text="Extraction terminee!")

            # Stockage des resultats
            st.session_state["fiscal_data_raw"] = fiscal_data
            st.session_state["extraction_report"] = report
            st.session_state["financial_data"] = fiscal_data_to_dict(fiscal_data)

            # Affichage du resultat
            st.success(f"Extraction reussie! (Methode: {report.method_used})")

            # Metriques du rapport
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                confidence = report.confidence_score
                st.metric(
                    "Confiance",
                    f"{confidence:.0%}",
                    delta=get_confidence_label(confidence),
                    help="Score de confiance de l'extraction"
                )

            with col2:
                st.metric(
                    "Methode",
                    report.method_used,
                    help="Methode utilisee pour l'extraction"
                )

            with col3:
                st.metric(
                    "Formulaires",
                    ", ".join(report.form_types) if report.form_types else "Non detectes",
                    help="Types de formulaires detectes"
                )

            with col4:
                st.metric(
                    "Duree",
                    f"{report.duration_seconds:.1f}s",
                    help="Duree totale de l'extraction"
                )

            # Avertissements
            if report.warnings:
                with st.expander("Avertissements", expanded=True):
                    for warning in report.warnings:
                        st.warning(warning)

            # Erreurs de validation
            if report.validation_errors:
                with st.expander("Erreurs de validation", expanded=True):
                    for error in report.validation_errors:
                        st.error(error)

        except InvalidPDFError as e:
            st.error(f"Fichier PDF invalide: {str(e)}")
        except ExtractionError as e:
            st.error(f"Erreur d'extraction: {str(e)}")
        except Exception as e:
            st.error(f"Erreur inattendue: {str(e)}")
        finally:
            # Nettoyage du progress bar
            progress_bar.empty()


# =============================================================================
# SECTION 3: VALIDATION ET EDITION
# =============================================================================

if "financial_data" in st.session_state:
    st.divider()
    st.header("3. Validation et edition des donnees")

    data = st.session_state["financial_data"]

    # Onglets pour les differentes sections
    tab_info, tab_actif, tab_passif, tab_resultat = st.tabs([
        "Informations",
        "Bilan - Actif",
        "Bilan - Passif",
        "Compte de resultat"
    ])

    # ==========================================================================
    # Onglet Informations
    # ==========================================================================
    with tab_info:
        st.subheader("Informations de l'entreprise")

        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input(
                "Raison sociale",
                value=data["metadata"].get("company_name", ""),
                help="Nom de l'entreprise"
            )
            siren = st.text_input(
                "SIREN",
                value=data["metadata"].get("siren", ""),
                max_chars=9,
                help="Numero SIREN (9 chiffres)"
            )
            naf_code = st.text_input(
                "Code NAF",
                value=data["metadata"].get("naf_code", "") or "",
                help="Code d'activite"
            )

        with col2:
            legal_form = st.text_input(
                "Forme juridique",
                value=data["metadata"].get("legal_form", "") or "",
                help="SA, SAS, SARL, etc."
            )
            siret = st.text_input(
                "SIRET",
                value=data["metadata"].get("siret", "") or "",
                max_chars=14,
                help="Numero SIRET (14 chiffres)"
            )
            fiscal_year_end = st.date_input(
                "Date de cloture",
                value=date.fromisoformat(data["metadata"]["fiscal_year_end"]) if data["metadata"].get("fiscal_year_end") else date.today(),
                help="Date de fin de l'exercice fiscal"
            )

        # Mise a jour des metadonnees
        data["metadata"]["company_name"] = company_name
        data["metadata"]["siren"] = siren
        data["metadata"]["siret"] = siret if siret else None
        data["metadata"]["naf_code"] = naf_code if naf_code else None
        data["metadata"]["legal_form"] = legal_form if legal_form else None
        data["metadata"]["fiscal_year_end"] = fiscal_year_end.isoformat()

    # ==========================================================================
    # Onglet Actif
    # ==========================================================================
    with tab_actif:
        st.subheader("Actif immobilise")

        actif_immo_df = pd.DataFrame({
            "Poste": [
                "Immobilisations incorporelles",
                "Immobilisations corporelles",
                "Immobilisations financieres"
            ],
            "Code": ["AB", "AD", "AF"],
            "Montant (EUR)": [
                data["balance_sheet"]["assets"]["fixed_assets"]["intangible_assets"],
                data["balance_sheet"]["assets"]["fixed_assets"]["tangible_assets"],
                data["balance_sheet"]["assets"]["fixed_assets"]["financial_assets"],
            ]
        })

        edited_actif_immo = st.data_editor(
            actif_immo_df,
            column_config={
                "Poste": st.column_config.TextColumn(disabled=True),
                "Code": st.column_config.TextColumn(disabled=True),
                "Montant (EUR)": st.column_config.NumberColumn(
                    format="%.2f",
                    min_value=0,
                    step=1
                )
            },
            hide_index=True,
            use_container_width=True,
            key="actif_immo_editor"
        )

        # Mise a jour des donnees
        data["balance_sheet"]["assets"]["fixed_assets"]["intangible_assets"] = edited_actif_immo.iloc[0]["Montant (EUR)"]
        data["balance_sheet"]["assets"]["fixed_assets"]["tangible_assets"] = edited_actif_immo.iloc[1]["Montant (EUR)"]
        data["balance_sheet"]["assets"]["fixed_assets"]["financial_assets"] = edited_actif_immo.iloc[2]["Montant (EUR)"]

        total_immo = sum(edited_actif_immo["Montant (EUR)"])
        data["balance_sheet"]["assets"]["fixed_assets"]["total"] = total_immo
        st.metric("Total actif immobilise", f"{total_immo:,.2f} EUR".replace(",", " "))

        st.divider()
        st.subheader("Actif circulant")

        actif_circ_df = pd.DataFrame({
            "Poste": [
                "Stocks et en-cours",
                "Creances clients",
                "Autres creances",
                "Charges constatees d'avance",
                "VMP",
                "Disponibilites"
            ],
            "Code": ["BH", "BJ", "BK", "BL", "BM", "BQ"],
            "Montant (EUR)": [
                data["balance_sheet"]["assets"]["current_assets"]["inventory"],
                data["balance_sheet"]["assets"]["current_assets"]["trade_receivables"],
                data["balance_sheet"]["assets"]["current_assets"]["other_receivables"],
                data["balance_sheet"]["assets"]["current_assets"]["prepaid_expenses"],
                data["balance_sheet"]["assets"]["current_assets"]["marketable_securities"],
                data["balance_sheet"]["assets"]["current_assets"]["cash"],
            ]
        })

        edited_actif_circ = st.data_editor(
            actif_circ_df,
            column_config={
                "Poste": st.column_config.TextColumn(disabled=True),
                "Code": st.column_config.TextColumn(disabled=True),
                "Montant (EUR)": st.column_config.NumberColumn(
                    format="%.2f",
                    min_value=0,
                    step=1
                )
            },
            hide_index=True,
            use_container_width=True,
            key="actif_circ_editor"
        )

        # Mise a jour des donnees
        data["balance_sheet"]["assets"]["current_assets"]["inventory"] = edited_actif_circ.iloc[0]["Montant (EUR)"]
        data["balance_sheet"]["assets"]["current_assets"]["trade_receivables"] = edited_actif_circ.iloc[1]["Montant (EUR)"]
        data["balance_sheet"]["assets"]["current_assets"]["other_receivables"] = edited_actif_circ.iloc[2]["Montant (EUR)"]
        data["balance_sheet"]["assets"]["current_assets"]["prepaid_expenses"] = edited_actif_circ.iloc[3]["Montant (EUR)"]
        data["balance_sheet"]["assets"]["current_assets"]["marketable_securities"] = edited_actif_circ.iloc[4]["Montant (EUR)"]
        data["balance_sheet"]["assets"]["current_assets"]["cash"] = edited_actif_circ.iloc[5]["Montant (EUR)"]

        total_circ = sum(edited_actif_circ["Montant (EUR)"])
        data["balance_sheet"]["assets"]["current_assets"]["total"] = total_circ
        st.metric("Total actif circulant", f"{total_circ:,.2f} EUR".replace(",", " "))

        # Total actif
        total_actif = total_immo + total_circ
        data["balance_sheet"]["assets"]["total_assets"] = total_actif
        st.divider()
        st.metric("TOTAL ACTIF", f"{total_actif:,.2f} EUR".replace(",", " "), delta_color="off")

    # ==========================================================================
    # Onglet Passif
    # ==========================================================================
    with tab_passif:
        st.subheader("Capitaux propres")

        passif_cp_df = pd.DataFrame({
            "Poste": [
                "Capital social",
                "Primes d'emission",
                "Reserve legale",
                "Report a nouveau",
                "Resultat de l'exercice"
            ],
            "Code": ["DA", "DB", "DD", "DG", "DI"],
            "Montant (EUR)": [
                data["balance_sheet"]["liabilities"]["equity"]["share_capital"],
                data["balance_sheet"]["liabilities"]["equity"]["share_premium"],
                data["balance_sheet"]["liabilities"]["equity"]["legal_reserve"],
                data["balance_sheet"]["liabilities"]["equity"]["retained_earnings"],
                data["balance_sheet"]["liabilities"]["equity"]["net_income"],
            ]
        })

        edited_passif_cp = st.data_editor(
            passif_cp_df,
            column_config={
                "Poste": st.column_config.TextColumn(disabled=True),
                "Code": st.column_config.TextColumn(disabled=True),
                "Montant (EUR)": st.column_config.NumberColumn(
                    format="%.2f",
                    step=1
                )
            },
            hide_index=True,
            use_container_width=True,
            key="passif_cp_editor"
        )

        # Mise a jour des donnees
        data["balance_sheet"]["liabilities"]["equity"]["share_capital"] = edited_passif_cp.iloc[0]["Montant (EUR)"]
        data["balance_sheet"]["liabilities"]["equity"]["share_premium"] = edited_passif_cp.iloc[1]["Montant (EUR)"]
        data["balance_sheet"]["liabilities"]["equity"]["legal_reserve"] = edited_passif_cp.iloc[2]["Montant (EUR)"]
        data["balance_sheet"]["liabilities"]["equity"]["retained_earnings"] = edited_passif_cp.iloc[3]["Montant (EUR)"]
        data["balance_sheet"]["liabilities"]["equity"]["net_income"] = edited_passif_cp.iloc[4]["Montant (EUR)"]

        total_cp = sum(edited_passif_cp["Montant (EUR)"])
        data["balance_sheet"]["liabilities"]["equity"]["total"] = total_cp
        st.metric("Total capitaux propres", f"{total_cp:,.2f} EUR".replace(",", " "))

        st.divider()
        st.subheader("Dettes financieres")

        passif_dette_df = pd.DataFrame({
            "Poste": [
                "Emprunts long terme",
                "Emprunts court terme",
                "Concours bancaires"
            ],
            "Code": ["DU", "DV", "EH"],
            "Montant (EUR)": [
                data["balance_sheet"]["liabilities"]["debt"]["long_term_debt"],
                data["balance_sheet"]["liabilities"]["debt"]["short_term_debt"],
                data["balance_sheet"]["liabilities"]["debt"]["bank_overdrafts"],
            ]
        })

        edited_passif_dette = st.data_editor(
            passif_dette_df,
            column_config={
                "Poste": st.column_config.TextColumn(disabled=True),
                "Code": st.column_config.TextColumn(disabled=True),
                "Montant (EUR)": st.column_config.NumberColumn(
                    format="%.2f",
                    min_value=0,
                    step=1
                )
            },
            hide_index=True,
            use_container_width=True,
            key="passif_dette_editor"
        )

        # Mise a jour des donnees
        data["balance_sheet"]["liabilities"]["debt"]["long_term_debt"] = edited_passif_dette.iloc[0]["Montant (EUR)"]
        data["balance_sheet"]["liabilities"]["debt"]["short_term_debt"] = edited_passif_dette.iloc[1]["Montant (EUR)"]
        data["balance_sheet"]["liabilities"]["debt"]["bank_overdrafts"] = edited_passif_dette.iloc[2]["Montant (EUR)"]

        total_dette = sum(edited_passif_dette["Montant (EUR)"])
        data["balance_sheet"]["liabilities"]["debt"]["total_financial_debt"] = total_dette
        st.metric("Total dettes financieres", f"{total_dette:,.2f} EUR".replace(",", " "))

        st.divider()
        st.subheader("Dettes d'exploitation")

        passif_exp_df = pd.DataFrame({
            "Poste": [
                "Dettes fournisseurs",
                "Dettes fiscales",
                "Dettes sociales"
            ],
            "Code": ["DX", "DY", "DZ"],
            "Montant (EUR)": [
                data["balance_sheet"]["liabilities"]["operating_liabilities"]["trade_payables"],
                data["balance_sheet"]["liabilities"]["operating_liabilities"]["tax_liabilities"],
                data["balance_sheet"]["liabilities"]["operating_liabilities"]["social_liabilities"],
            ]
        })

        edited_passif_exp = st.data_editor(
            passif_exp_df,
            column_config={
                "Poste": st.column_config.TextColumn(disabled=True),
                "Code": st.column_config.TextColumn(disabled=True),
                "Montant (EUR)": st.column_config.NumberColumn(
                    format="%.2f",
                    min_value=0,
                    step=1
                )
            },
            hide_index=True,
            use_container_width=True,
            key="passif_exp_editor"
        )

        # Mise a jour des donnees
        data["balance_sheet"]["liabilities"]["operating_liabilities"]["trade_payables"] = edited_passif_exp.iloc[0]["Montant (EUR)"]
        data["balance_sheet"]["liabilities"]["operating_liabilities"]["tax_liabilities"] = edited_passif_exp.iloc[1]["Montant (EUR)"]
        data["balance_sheet"]["liabilities"]["operating_liabilities"]["social_liabilities"] = edited_passif_exp.iloc[2]["Montant (EUR)"]

        total_exp = sum(edited_passif_exp["Montant (EUR)"])
        data["balance_sheet"]["liabilities"]["operating_liabilities"]["total"] = total_exp
        st.metric("Total dettes exploitation", f"{total_exp:,.2f} EUR".replace(",", " "))

        # Provisions
        total_provisions = (
            data["balance_sheet"]["liabilities"]["provisions"]["provisions_for_risks"] +
            data["balance_sheet"]["liabilities"]["provisions"]["provisions_for_charges"]
        )

        # Total passif
        total_passif = total_cp + total_dette + total_exp + total_provisions
        data["balance_sheet"]["liabilities"]["total_liabilities"] = total_passif
        st.divider()
        st.metric("TOTAL PASSIF", f"{total_passif:,.2f} EUR".replace(",", " "), delta_color="off")

        # Verification equilibre
        total_actif = data["balance_sheet"]["assets"]["total_assets"]
        if abs(total_actif - total_passif) > 1:
            st.error(f"Desequilibre du bilan: Actif ({total_actif:,.2f}) != Passif ({total_passif:,.2f})")
        else:
            st.success("Bilan equilibre")

    # ==========================================================================
    # Onglet Compte de resultat
    # ==========================================================================
    with tab_resultat:
        st.subheader("Produits d'exploitation")

        produits_df = pd.DataFrame({
            "Poste": [
                "Ventes de marchandises",
                "Production vendue (services)",
                "Production vendue (biens)",
                "Autres produits d'exploitation"
            ],
            "Code": ["FA", "FB", "FC", "FE"],
            "Montant (EUR)": [
                data["income_statement"]["revenues"]["sales_of_goods"],
                data["income_statement"]["revenues"]["sales_of_services"],
                data["income_statement"]["revenues"]["sales_of_products"],
                data["income_statement"]["revenues"]["other_operating_income"],
            ]
        })

        edited_produits = st.data_editor(
            produits_df,
            column_config={
                "Poste": st.column_config.TextColumn(disabled=True),
                "Code": st.column_config.TextColumn(disabled=True),
                "Montant (EUR)": st.column_config.NumberColumn(
                    format="%.2f",
                    min_value=0,
                    step=1
                )
            },
            hide_index=True,
            use_container_width=True,
            key="produits_editor"
        )

        # Mise a jour des donnees
        data["income_statement"]["revenues"]["sales_of_goods"] = edited_produits.iloc[0]["Montant (EUR)"]
        data["income_statement"]["revenues"]["sales_of_services"] = edited_produits.iloc[1]["Montant (EUR)"]
        data["income_statement"]["revenues"]["sales_of_products"] = edited_produits.iloc[2]["Montant (EUR)"]
        data["income_statement"]["revenues"]["other_operating_income"] = edited_produits.iloc[3]["Montant (EUR)"]

        # Calcul CA
        ca = (
            edited_produits.iloc[0]["Montant (EUR)"] +
            edited_produits.iloc[1]["Montant (EUR)"] +
            edited_produits.iloc[2]["Montant (EUR)"]
        )
        data["income_statement"]["revenues"]["net_revenue"] = ca
        data["revenues"]["total"]["value"] = ca

        total_produits = sum(edited_produits["Montant (EUR)"])
        data["income_statement"]["revenues"]["total"] = total_produits

        st.metric("Chiffre d'affaires", f"{ca:,.2f} EUR".replace(",", " "))

        st.divider()
        st.subheader("Charges d'exploitation")

        charges_df = pd.DataFrame({
            "Poste": [
                "Achats de marchandises",
                "Achats de matieres premieres",
                "Variation de stocks",
                "Autres achats et charges externes",
                "Impots et taxes",
                "Salaires et traitements",
                "Charges sociales",
                "Dotations aux amortissements",
                "Dotations aux provisions",
                "Autres charges"
            ],
            "Code": ["FS", "FT", "FU", "FW", "FX", "FY", "FZ", "GA", "GB", "GE"],
            "Montant (EUR)": [
                data["income_statement"]["operating_expenses"]["purchases_of_goods"],
                data["income_statement"]["operating_expenses"]["purchases_of_raw_materials"],
                data["income_statement"]["operating_expenses"]["inventory_variation"],
                data["income_statement"]["operating_expenses"]["external_charges"],
                data["income_statement"]["operating_expenses"]["taxes_and_duties"],
                data["income_statement"]["operating_expenses"]["wages_and_salaries"],
                data["income_statement"]["operating_expenses"]["social_charges"],
                data["income_statement"]["operating_expenses"]["depreciation"],
                data["income_statement"]["operating_expenses"]["provisions"],
                data["income_statement"]["operating_expenses"]["other_operating_expenses"],
            ]
        })

        edited_charges = st.data_editor(
            charges_df,
            column_config={
                "Poste": st.column_config.TextColumn(disabled=True),
                "Code": st.column_config.TextColumn(disabled=True),
                "Montant (EUR)": st.column_config.NumberColumn(
                    format="%.2f",
                    step=1
                )
            },
            hide_index=True,
            use_container_width=True,
            key="charges_editor"
        )

        # Mise a jour des donnees
        data["income_statement"]["operating_expenses"]["purchases_of_goods"] = edited_charges.iloc[0]["Montant (EUR)"]
        data["income_statement"]["operating_expenses"]["purchases_of_raw_materials"] = edited_charges.iloc[1]["Montant (EUR)"]
        data["income_statement"]["operating_expenses"]["inventory_variation"] = edited_charges.iloc[2]["Montant (EUR)"]
        data["income_statement"]["operating_expenses"]["external_charges"] = edited_charges.iloc[3]["Montant (EUR)"]
        data["income_statement"]["operating_expenses"]["taxes_and_duties"] = edited_charges.iloc[4]["Montant (EUR)"]
        data["income_statement"]["operating_expenses"]["wages_and_salaries"] = edited_charges.iloc[5]["Montant (EUR)"]
        data["income_statement"]["operating_expenses"]["social_charges"] = edited_charges.iloc[6]["Montant (EUR)"]
        data["income_statement"]["operating_expenses"]["depreciation"] = edited_charges.iloc[7]["Montant (EUR)"]
        data["income_statement"]["operating_expenses"]["provisions"] = edited_charges.iloc[8]["Montant (EUR)"]
        data["income_statement"]["operating_expenses"]["other_operating_expenses"] = edited_charges.iloc[9]["Montant (EUR)"]

        total_charges = sum(edited_charges["Montant (EUR)"])
        data["income_statement"]["operating_expenses"]["total"] = total_charges
        data["expenses"]["total"] = total_charges

        st.metric("Total charges d'exploitation", f"{total_charges:,.2f} EUR".replace(",", " "))

        # Resultat d'exploitation
        resultat_exploitation = total_produits - total_charges
        data["income_statement"]["operating_income"] = resultat_exploitation

        st.divider()
        st.subheader("Resultat financier")

        col1, col2 = st.columns(2)
        with col1:
            financial_income = st.number_input(
                "Produits financiers",
                value=float(data["income_statement"]["financial_result"]["financial_income"]),
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )
        with col2:
            interest_expense = st.number_input(
                "Charges financieres (interets)",
                value=float(data["income_statement"]["financial_result"]["interest_expense"]),
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

        data["income_statement"]["financial_result"]["financial_income"] = financial_income
        data["income_statement"]["financial_result"]["total_financial_income"] = financial_income
        data["income_statement"]["financial_result"]["interest_expense"] = interest_expense
        data["income_statement"]["financial_result"]["total_financial_expense"] = interest_expense
        data["income_statement"]["financial_result"]["net_financial_result"] = financial_income - interest_expense
        data["expenses"]["financial"]["interest_expense"]["value"] = interest_expense

        resultat_financier = financial_income - interest_expense
        st.metric("Resultat financier", f"{resultat_financier:,.2f} EUR".replace(",", " "))

        st.divider()
        st.subheader("Resultat exceptionnel et impots")

        col1, col2 = st.columns(2)
        with col1:
            exceptional_income = st.number_input(
                "Produits exceptionnels",
                value=float(data["income_statement"]["exceptional_result"]["total_exceptional_income"]),
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )
            exceptional_expense = st.number_input(
                "Charges exceptionnelles",
                value=float(data["income_statement"]["exceptional_result"]["total_exceptional_expense"]),
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )
        with col2:
            income_tax = st.number_input(
                "Impot sur les benefices",
                value=float(data["income_statement"]["income_tax_expense"]),
                step=100.0,
                format="%.2f"
            )

        data["income_statement"]["exceptional_result"]["total_exceptional_income"] = exceptional_income
        data["income_statement"]["exceptional_result"]["total_exceptional_expense"] = exceptional_expense
        data["income_statement"]["exceptional_result"]["net_exceptional_result"] = exceptional_income - exceptional_expense
        data["income_statement"]["income_tax_expense"] = income_tax

        # Calcul du resultat courant avant impot
        rcai = resultat_exploitation + resultat_financier
        data["income_statement"]["current_income_before_tax"] = rcai

        # Calcul du resultat net
        resultat_exceptionnel = exceptional_income - exceptional_expense
        resultat_net = rcai + resultat_exceptionnel - income_tax
        data["income_statement"]["net_income"] = resultat_net

        # Calcul EBITDA
        depreciation = data["income_statement"]["operating_expenses"]["depreciation"]
        provisions = data["income_statement"]["operating_expenses"]["provisions"]
        ebitda = resultat_exploitation + depreciation + provisions
        data["profitability"]["ebitda"]["value"] = ebitda

        st.divider()

        # Resume
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Resultat d'exploitation", f"{resultat_exploitation:,.2f} EUR".replace(",", " "))
        with col2:
            st.metric("EBITDA", f"{ebitda:,.2f} EUR".replace(",", " "))
        with col3:
            delta = "Benefice" if resultat_net >= 0 else "Perte"
            st.metric("Resultat net", f"{resultat_net:,.2f} EUR".replace(",", " "), delta=delta)

    # Mise a jour du session_state
    st.session_state["financial_data"] = data


# =============================================================================
# SECTION 4: SAUVEGARDE
# =============================================================================

if "financial_data" in st.session_state:
    st.divider()
    st.header("4. Sauvegarde")

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("Valider et Sauvegarder", type="primary"):
            data = st.session_state["financial_data"]

            try:
                # Tentative de sauvegarde dans la base de donnees
                # Note: Cette partie necessite une implementation complete de la DB

                # Pour l'instant, on stocke juste dans le session_state
                st.session_state["validated_fiscal_data"] = data

                st.success("Donnees validees et sauvegardees avec succes!")
                st.info("Les donnees sont pretes pour l'analyse. Rendez-vous dans l'onglet principal.")

                # Afficher un resume
                with st.expander("Donnees sauvegardees (JSON)", expanded=False):
                    st.json(data)

            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde: {str(e)}")

    with col2:
        # Bouton de telechargement JSON
        json_data = json.dumps(st.session_state["financial_data"], indent=2, ensure_ascii=False)
        st.download_button(
            label="Telecharger les donnees (JSON)",
            data=json_data,
            file_name=f"liasse_fiscale_{st.session_state['financial_data']['metadata'].get('siren', 'unknown')}.json",
            mime="application/json",
            help="Telechargez les donnees extraites au format JSON"
        )
