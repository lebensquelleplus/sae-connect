"""
import streamlit as st

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
"""

"""
Gmail Cancellation Tracker - Hauptanwendung
Moderne Streamlit App zum Durchsuchen von Gmail nach Stornierungsanfragen
"""

import streamlit as st
import sys
from pathlib import Path

# Projektpfad hinzufügen
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from dsrc.gmail_client import GmailClient
from dsrc.email_analyzer import EmailAnalyzer
from dsrc.ui_components import UIComponents
#from config import AppConfig
from config.app_config import AppConfig

def load_custom_css():
    """Lade custom CSS Styles"""
    css_file = project_root / "assets" / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def initialize_session_state():
    """Initialisiere Session State Variablen"""
    # Basis-Variablen mit sicheren Defaults
    default_values = {
        'authenticated': False,
        'gmail_client': None,
        'search_results': None,
        'theme': 'dark',
        'search_params': {
            'days': AppConfig.DEFAULT_SEARCH_DAYS,
            'max_emails': AppConfig.DEFAULT_MAX_EMAILS,
            'sender': '',
            'subject': '',
            'priority_only': False
        },
        'search_options': {
            'filter_amazon': True,
            'filter_recent': False,
            'export_format': 'csv'
        },
        'custom_keywords': [],
        'ui_settings': {
            'theme': 'dark',
            'font_size': 14,
            'compact_mode': False,
            'animations': True
        },
        'search_settings': {
            'default_days': 30,
            'max_emails': 100,
            'auto_refresh': False
        },
        'security_settings': {
            'session_timeout': 60,
            'save_data': False,
            'enable_logging': False
        }
    }
    
    # Setze nur fehlende Werte
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

def main():
    """Hauptfunktion der Anwendung"""
    
    # App Konfiguration
    st.set_page_config(
        page_title=AppConfig.APP_NAME,
        page_icon="📧",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/your-repo',
            'Report a bug': 'https://github.com/your-repo/issues',
            'About': f'{AppConfig.APP_NAME} v{AppConfig.VERSION}'
        }
    )
    
    # CSS und Session State laden
    load_custom_css()
    initialize_session_state()
    
    # UI Komponenten initialisieren
    ui = UIComponents()
    
    # Header mit modernem Design
    ui.render_header()
    
    # Sidebar für Navigation und Einstellungen
    with st.sidebar:
        ui.render_sidebar()
    
    # Hauptinhalt basierend auf aktuellem State
    if not st.session_state.authenticated:
        render_login_page(ui)
    else:
        render_dashboard(ui)

def render_login_page(ui):
    """Render Login/Authentication Seite"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        ui.render_login_card()

def render_dashboard(ui):
    """Render Haupt-Dashboard"""
    
    # Top Metrics
    ui.render_metrics_row()
    
    # Hauptinhalt in Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 E-Mail Suche", 
        "📊 Dashboard", 
        "📋 Ergebnisse", 
        "⚙️ Einstellungen"
    ])
    
    with tab1:
        render_search_tab(ui)
    
    with tab2:
        render_analytics_tab(ui)
    
    with tab3:
        render_results_tab(ui)
    
    with tab4:
        render_settings_tab(ui)

def render_search_tab(ui):
    """Render E-Mail Suche Tab"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ui.render_search_form()
    
    with col2:
        ui.render_search_options()
    
    # Suche ausführen
    if st.button("🔍 Suche starten", type="primary", use_container_width=True):
        execute_search(ui)

def render_analytics_tab(ui):
    """Render Analytics Dashboard"""
    
    if st.session_state.search_results:
        ui.render_analytics_dashboard(st.session_state.search_results)
    else:
        ui.render_empty_state("Führen Sie zuerst eine Suche durch, um Analytics zu sehen.")

def render_results_tab(ui):
    """Render Suchergebnisse Tab"""
    
    if st.session_state.search_results:
        ui.render_results_table(st.session_state.search_results)
        ui.render_export_options(st.session_state.search_results)
    else:
        ui.render_empty_state("Keine Suchergebnisse vorhanden.")

def render_settings_tab(ui):
    """Render Einstellungen Tab"""
    
    ui.render_settings_page()

def execute_search(ui):
    """Führe E-Mail Suche durch"""
    
    try:
        with st.spinner("🔄 Verbinde mit Gmail..."):
            gmail_client = st.session_state.gmail_client
            
            if not gmail_client or not gmail_client.is_connected():
                st.error("❌ Keine aktive Gmail-Verbindung.")
                return
        
        # Suchparameter aus UI holen
        search_params = ui.get_search_parameters()
        
        with st.spinner(f"📧 Suche E-Mails der letzten {search_params['days']} Tage..."):
            # E-Mails abrufen
            emails = gmail_client.search_emails(
                days_back=search_params['days'],
                max_emails=search_params['max_emails']
            )
            
            if not emails:
                st.warning("⚠️ Keine E-Mails im angegebenen Zeitraum gefunden.")
                return
        
        with st.spinner("🔍 Analysiere E-Mails auf Stornierungsanfragen..."):
            # E-Mail Analyse
            analyzer = EmailAnalyzer()
            results = analyzer.analyze_cancellation_requests(emails)
            
            # Ergebnisse in Session State speichern
            st.session_state.search_results = results
        
        # Erfolg anzeigen
        if results['cancellation_emails']:
            st.success(f"✅ {len(results['cancellation_emails'])} Stornierungsanfragen gefunden!")
        else:
            st.info("ℹ️ Keine Stornierungsanfragen gefunden.")
            
        # Auto-switch zu Results Tab
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Fehler bei der Suche: {str(e)}")
        st.session_state.authenticated = False

if __name__ == "__main__":
    main()
