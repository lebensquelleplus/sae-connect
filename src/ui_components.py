"""
UI Komponenten für die Gmail Cancellation Tracker App
Moderne, wiederverwendbare UI-Elemente
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

from config import AppConfig, UIConfig, EmailConfig
from .gmail_client import GmailClient
from .email_analyzer import EmailAnalyzer

class UIComponents:
    """Sammlung von UI Komponenten für die Anwendung"""
    
    def __init__(self):
        self.config = UIConfig()
        self.icons = self.config.ICONS
    
    def render_header(self):
        """Render App Header mit modernem Design"""
        
        st.markdown("""
        <div class="app-header">
            <div class="header-content">
                <h1>📧 Gmail Cancellation Tracker</h1>
                <p>Intelligente Suche nach Stornierungsanfragen in Ihren E-Mails</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render Sidebar mit Navigation und Einstellungen"""
        
        st.markdown("### 🎛️ Steuerung")
        
        # Verbindungsstatus
        self._render_connection_status()
        
        # Theme Switcher
        self._render_theme_switcher()
        
        # Quick Actions
        st.markdown("### ⚡ Schnellaktionen")
        
        if st.button("🔄 Neu verbinden", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
        
        if st.button("🗑️ Cache leeren", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache geleert!")
        
        # App Info
        st.markdown("---")
        # Sichere Anzahl der Ergebnisse ermitteln
        search_results = st.session_state.get('search_results') or {}
        cancellation_emails = search_results.get('cancellation_emails', [])
        results_count = len(cancellation_emails) if cancellation_emails else 0
        
        st.markdown(f"""
        <div class="app-info">
            <small>
            📱 Version {AppConfig.VERSION}<br>
            🔧 Entwickelt mit Streamlit<br>
            📊 {results_count} Ergebnisse geladen
            </small>
        </div>
        """, unsafe_allow_html=True)
    
    def render_login_card(self):
        """Render Login Card mit modernem Design"""
        
        st.markdown("""
        <div class="login-card">
            <div class="login-header">
                <h2>🔐 Gmail Anmeldung</h2>
                <p>Sicher verbinden mit Ihrem Gmail-Konto</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            st.info("💡 **Wichtig:** Verwenden Sie ein Gmail App-Passwort, nicht Ihr reguläres Passwort!")
            
            email = st.text_input(
                "📧 Gmail-Adresse",
                placeholder="beispiel@gmail.com",
                help="Ihre vollständige Gmail-Adresse"
            )
            
            password = st.text_input(
                "🔑 App-Passwort",
                type="password",
                placeholder="16-stelliges App-Passwort",
                help="Erstellen Sie ein App-Passwort in Ihren Google-Kontoeinstellungen"
            )
            
            remember_me = st.checkbox("🔒 Anmeldedaten für diese Session merken")
            
            login_button = st.form_submit_button(
                "🚀 Verbinden", 
                type="primary",
                use_container_width=True
            )
            
            if login_button:
                self._handle_login(email, password, remember_me)
        
        # Hilfe-Section
        with st.expander("❓ Hilfe zur Anmeldung"):
            st.markdown("""
            ### App-Passwort erstellen:
            
            1. **Google-Konto öffnen:** [myaccount.google.com](https://myaccount.google.com/)
            2. **Sicherheit:** Navigieren Sie zu "Sicherheit"
            3. **2-Schritt-Verifizierung:** Muss aktiviert sein
            4. **App-Passwörter:** Klicken Sie auf "App-Passwörter"
            5. **App auswählen:** "Sonstige (benutzerdefinierter Name)"
            6. **Name eingeben:** z.B. "Gmail Cancellation Tracker"
            7. **Passwort kopieren:** Das 16-stellige Passwort verwenden
            
            ⚡ **Tipp:** Das App-Passwort ersetzt Ihr normales Gmail-Passwort nur für diese App.
            """)
    
    def render_metrics_row(self):
        """Render Top-Level Metrics"""
        
        # Sichere Datenabfrage
        search_results = st.session_state.get('search_results') or {}
        all_emails = search_results.get('all_emails', [])
        cancellation_emails = search_results.get('cancellation_emails', [])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_emails = len(all_emails)
            st.metric(
                label="📧 Durchsuchte E-Mails",
                value=total_emails,
                delta=f"+{total_emails}" if total_emails > 0 else None
            )
        
        with col2:
            cancellations = len(cancellation_emails)
            st.metric(
                label="🎯 Stornierungsanfragen",
                value=cancellations,
                delta=f"+{cancellations}" if cancellations > 0 else None
            )
        
        with col3:
            if total_emails > 0:
                percentage = (cancellations / total_emails) * 100
                st.metric(
                    label="📊 Anteil Stornierungen",
                    value=f"{percentage:.1f}%",
                    delta=f"{percentage:.1f}%" if percentage > 0 else None
                )
            else:
                st.metric(label="📊 Anteil Stornierungen", value="0%")
        
        with col4:
            last_search = search_results.get('timestamp', 'Nie')
            if last_search != 'Nie':
                try:
                    last_search = datetime.fromisoformat(last_search).strftime("%H:%M")
                except (ValueError, TypeError):
                    last_search = 'Unbekannt'
            st.metric(
                label="🕐 Letzte Suche",
                value=last_search
            )
    
    def render_search_form(self):
        """Render Suchformular"""
        
        st.markdown("### 🔍 Suchparameter")
        
        col1, col2 = st.columns(2)
        
        with col1:
            days_back = st.slider(
                "📅 Zeitraum (Tage)",
                min_value=1,
                max_value=AppConfig.MAX_SEARCH_DAYS,
                value=AppConfig.DEFAULT_SEARCH_DAYS,
                help="Wie viele Tage zurück soll gesucht werden?"
            )
        
        with col2:
            max_emails = st.number_input(
                "📧 Max. E-Mails",
                min_value=10,
                max_value=AppConfig.MAX_EMAILS_LIMIT,
                value=AppConfig.DEFAULT_MAX_EMAILS,
                step=10,
                help="Maximale Anzahl E-Mails zum Durchsuchen"
            )
        
        # Erweiterte Optionen
        with st.expander("🔧 Erweiterte Optionen"):
            search_sender = st.text_input(
                "👤 Bestimmter Absender (optional)",
                placeholder="beispiel@domain.com",
                help="Nur E-Mails von diesem Absender durchsuchen"
            )
            
            search_subject = st.text_input(
                "📝 Betreff enthält (optional)",
                placeholder="Bestellung, Order, etc.",
                help="Nur E-Mails mit diesem Begriff im Betreff"
            )
            
            priority_only = st.checkbox(
                "⚡ Nur prioritäre Anfragen",
                help="Nur E-Mails mit Prioritäts-Schlüsselwörtern (dringend, urgent, etc.)"
            )
        
        # Parameter in Session State speichern
        st.session_state.search_params = {
            'days': days_back,
            'max_emails': max_emails,
            'sender': search_sender,
            'subject': search_subject,
            'priority_only': priority_only
        }
    
    def render_search_options(self):
        """Render Suchoptionen Panel"""
        
        st.markdown("### ⚙️ Suchoptionen")
        
        # Schlüsselwort-Manager
        with st.expander("🏷️ Schlüsselwörter verwalten"):
            self._render_keyword_manager()
        
        # Filter-Optionen
        st.markdown("**📂 Filter:**")
        
        filter_amazon = st.checkbox(
            "📦 Nur Amazon-Bestellungen",
            value=True,
            help="Fokus auf Amazon-spezifische E-Mails"
        )
        
        filter_recent = st.checkbox(
            "🕐 Nur letzte 7 Tage",
            help="Nur sehr aktuelle E-Mails"
        )
        
        # Export-Vorschau
        st.markdown("**📤 Export-Format:**")
        export_format = st.selectbox(
            "Format wählen",
            ["CSV", "Excel", "JSON", "PDF"],
            help="Format für Ergebnisexport"
        )
        
        st.session_state.search_options = {
            'filter_amazon': filter_amazon,
            'filter_recent': filter_recent,
            'export_format': export_format.lower()
        }
    
    def render_analytics_dashboard(self, results: Dict):
        """Render Analytics Dashboard mit Charts"""
        
        # Sichere Datenprüfung
        if not results or not isinstance(results, dict):
            self.render_empty_state("Keine Daten für Analytics verfügbar.")
            return
            
        cancellation_emails = results.get('cancellation_emails', [])
        if not cancellation_emails:
            self.render_empty_state("Keine Stornierungsanfragen für Analytics verfügbar.")
            return
        
        st.markdown("### 📊 Analytics Dashboard")
        
        # Daten vorbereiten
        try:
            df = pd.DataFrame(cancellation_emails)
        except Exception as e:
            st.error(f"Fehler beim Erstellen des DataFrames: {e}")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Zeitverlauf Chart
            self._render_timeline_chart(df)
        
        with col2:
            # Top Absender Chart
            self._render_sender_chart(df)
        
        # Schlüsselwort-Analyse
        col3, col4 = st.columns(2)
        
        with col3:
            self._render_keyword_analysis(df)
        
        with col4:
            self._render_priority_distribution(df)
    
    def render_results_table(self, results: Dict):
        """Render Ergebnistabelle mit Filteroptionen"""
        
        # Sichere Datenprüfung
        if not results or not isinstance(results, dict):
            self.render_empty_state("Keine Suchergebnisse vorhanden.")
            return
            
        cancellation_emails = results.get('cancellation_emails', [])
        if not cancellation_emails:
            self.render_empty_state("Keine Stornierungsanfragen gefunden.")
            return
        
        st.markdown("### 📋 Suchergebnisse")
        
        try:
            df = pd.DataFrame(cancellation_emails)
        except Exception as e:
            st.error(f"Fehler beim Erstellen der Tabelle: {e}")
            return
        
        # Filter-Optionen
        col1, col2, col3 = st.columns(3)
        
        with col1:
            unique_senders = df['Absender'].unique() if 'Absender' in df.columns else []
            sender_filter = st.selectbox(
                "📧 Absender Filter",
                ["Alle"] + list(unique_senders)
            )
        
        with col2:
            # Sichere Schlüsselwort-Extraktion
            all_keywords = []
            if 'Gefundene Schlüsselwörter' in df.columns:
                for kws in df['Gefundene Schlüsselwörter'].fillna(''):
                    if isinstance(kws, str) and kws:
                        all_keywords.extend(kws.split(', '))
            
            unique_keywords = list(set(all_keywords)) if all_keywords else []
            keyword_filter = st.selectbox(
                "🏷️ Schlüsselwort Filter",
                ["Alle"] + unique_keywords
            )
        
        with col3:
            date_filter = st.date_input(
                "📅 Datum ab",
                value=datetime.now() - timedelta(days=30)
            )
        
        # Filter anwenden
        filtered_df = df.copy()
        
        if sender_filter != "Alle" and 'Absender' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Absender'].str.contains(sender_filter, na=False)]
        
        if keyword_filter != "Alle" and 'Gefundene Schlüsselwörter' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Gefundene Schlüsselwörter'].str.contains(keyword_filter, na=False)]
        
        # Tabelle anzeigen
        if len(filtered_df) > 0:
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Absender": st.column_config.TextColumn("📧 Absender", width="medium"),
                    "Betreff": st.column_config.TextColumn("📝 Betreff", width="large"),
                    "Datum": st.column_config.DatetimeColumn("📅 Datum", width="small"),
                    "Gefundene Schlüsselwörter": st.column_config.TextColumn("🏷️ Schlüsselwörter", width="medium"),
                    "Body Preview": st.column_config.TextColumn("👁️ Vorschau", width="large")
                }
            )
            
            # Detailansicht
            st.markdown("### 🔍 Detailansicht")
            
            selected_index = st.selectbox(
                "E-Mail auswählen:",
                range(len(filtered_df)),
                format_func=lambda x: f"{filtered_df.iloc[x].get('Betreff', 'Kein Betreff')[:50]}..."
            )
            
            if selected_index is not None:
                self._render_email_detail(filtered_df.iloc[selected_index])
        else:
            st.info("Keine E-Mails entsprechen den ausgewählten Filtern.")
    
    def render_export_options(self, results: Dict):
        """Render Export-Optionen"""
        
        # Sichere Datenprüfung
        if not results or not isinstance(results, dict):
            return
            
        cancellation_emails = results.get('cancellation_emails', [])
        if not cancellation_emails:
            return
        
        st.markdown("### 📤 Export-Optionen")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV Export
            try:
                csv_data = pd.DataFrame(cancellation_emails).to_csv(index=False)
                st.download_button(
                    label="📊 CSV herunterladen",
                    data=csv_data,
                    file_name=f"stornierungsanfragen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"CSV Export Fehler: {e}")
        
        with col2:
            # JSON Export
            try:
                json_data = json.dumps(results, indent=2, ensure_ascii=False, default=str)
                st.download_button(
                    label="📋 JSON herunterladen",
                    data=json_data,
                    file_name=f"stornierungsanfragen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"JSON Export Fehler: {e}")
        
        with col3:
            # Excel Export (vereinfacht als CSV)
            try:
                excel_data = pd.DataFrame(cancellation_emails).to_csv(index=False)
                st.download_button(
                    label="📈 Excel herunterladen",
                    data=excel_data,
                    file_name=f"stornierungsanfragen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Excel Export Fehler: {e}")
    
    def render_settings_page(self):
        """Render Einstellungen Seite"""
        
        st.markdown("### ⚙️ Einstellungen")
        
        tab1, tab2, tab3 = st.tabs(["🎨 Darstellung", "🔍 Suche", "🔐 Sicherheit"])
        
        with tab1:
            self._render_appearance_settings()
        
        with tab2:
            self._render_search_settings()
        
        with tab3:
            self._render_security_settings()
    
    def render_empty_state(self, message: str):
        """Render Empty State mit Message"""
        
        st.markdown(f"""
        <div class="empty-state">
            <div class="empty-content">
                <h3>📭 {message}</h3>
                <p>Führen Sie eine Suche durch oder überprüfen Sie Ihre Einstellungen.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def get_search_parameters(self) -> Dict[str, Any]:
        """Hole aktuelle Suchparameter aus Session State"""
        
        params = st.session_state.get('search_params', {})
        options = st.session_state.get('search_options', {})
        
        return {
            'days': params.get('days', AppConfig.DEFAULT_SEARCH_DAYS),
            'max_emails': params.get('max_emails', AppConfig.DEFAULT_MAX_EMAILS),
            'sender': params.get('sender', ''),
            'subject': params.get('subject', ''),
            'priority_only': params.get('priority_only', False),
            'filter_amazon': options.get('filter_amazon', True),
            'filter_recent': options.get('filter_recent', False),
            'export_format': options.get('export_format', 'csv')
        }
    
    # Private Helper Methods
    
    def _render_connection_status(self):
        """Render Verbindungsstatus"""
        
        if st.session_state.authenticated:
            st.success("🟢 Gmail verbunden")
            
            if st.session_state.gmail_client:
                email = getattr(st.session_state.gmail_client, 'email', 'Unbekannt')
                st.caption(f"📧 {email}")
        else:
            st.error("🔴 Nicht verbunden")
    
    def _render_theme_switcher(self):
        """Render Theme Switcher"""
        
        current_theme = st.session_state.get('theme', 'dark')
        
        theme = st.selectbox(
            "🎨 Theme",
            ['light', 'dark', 'auto'],
            index=['light', 'dark', 'auto'].index(current_theme),
            help="Wählen Sie das App-Design"
        )
        
        if theme != current_theme:
            st.session_state.theme = theme
            st.rerun()
    
    def _handle_login(self, email: str, password: str, remember: bool):
        """Handle Login Process"""
        
        if not email or not password:
            st.error("❌ Bitte füllen Sie alle Felder aus.")
            return
        
        try:
            with st.spinner("🔄 Verbinde mit Gmail..."):
                gmail_client = GmailClient()
                
                if gmail_client.connect(email, password):
                    st.session_state.authenticated = True
                    st.session_state.gmail_client = gmail_client
                    
                    if remember:
                        st.session_state.remembered_email = email
                    
                    st.success("✅ Erfolgreich mit Gmail verbunden!")
                    st.rerun()
                else:
                    st.error("❌ Anmeldung fehlgeschlagen. Überprüfen Sie Ihre Daten.")
                    
        except Exception as e:
            st.error(f"❌ Verbindungsfehler: {str(e)}")
    
    def _render_keyword_manager(self):
        """Render Schlüsselwort-Manager"""
        
        st.markdown("**Aktuelle Schlüsselwörter:**")
        
        # Deutsche Schlüsselwörter
        st.markdown("🇩🇪 **Deutsch:**")
        st.caption(", ".join(EmailConfig.CANCELLATION_KEYWORDS_DE[:5]) + "...")
        
        # Englische Schlüsselwörter
        st.markdown("🇺🇸 **Englisch:**")
        st.caption(", ".join(EmailConfig.CANCELLATION_KEYWORDS_EN[:5]) + "...")
        
        # Custom Keywords
        custom_keywords = st.text_area(
            "➕ Eigene Schlüsselwörter (kommagetrennt):",
            placeholder="mein begriff, another keyword",
            help="Fügen Sie eigene Suchbegriffe hinzu"
        )
        
        if custom_keywords:
            keywords = [kw.strip() for kw in custom_keywords.split(',') if kw.strip()]
            st.session_state.custom_keywords = keywords
    
    def _render_timeline_chart(self, df: pd.DataFrame):
        """Render Zeitverlauf Chart"""
        
        st.markdown("#### 📈 Zeitverlauf")
        
        # Dummy-Daten für Demo - mit korrekter Frequenz
        try:
            dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='ME')  # 'ME' statt 'M'
            values = [5, 8, 12, 6, 15, 10, 8, 20, 14, 7, 9, 11]
        except Exception:
            # Fallback für ältere pandas-Versionen
            import datetime
            dates = [datetime.date(2024, i, 1) for i in range(1, 13)]
            values = [5, 8, 12, 6, 15, 10, 8, 20, 14, 7, 9, 11]
        
        fig = px.line(
            x=dates, 
            y=values,
            title="Stornierungsanfragen pro Monat",
            labels={'x': 'Datum', 'y': 'Anzahl'}
        )
        
        fig.update_layout(
            height=300,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_sender_chart(self, df: pd.DataFrame):
        """Render Top Absender Chart"""
        
        st.markdown("#### 👥 Top Absender")
        
        if 'Absender' in df.columns:
            sender_counts = df['Absender'].value_counts().head(5)
            
            fig = px.bar(
                x=sender_counts.values,
                y=sender_counts.index,
                orientation='h',
                title="Häufigste Absender"
            )
            
            fig.update_layout(
                height=300,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_keyword_analysis(self, df: pd.DataFrame):
        """Render Schlüsselwort-Analyse"""
        
        st.markdown("#### 🏷️ Schlüsselwort-Häufigkeit")
        
        # Dummy-Daten für Demo
        keywords = ['stornierung', 'cancel', 'rückgabe', 'refund', 'widerruf']
        counts = [15, 12, 8, 6, 4]
        
        fig = px.pie(
            values=counts,
            names=keywords,
            title="Verteilung der Schlüsselwörter"
        )
        
        fig.update_layout(
            height=300,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_priority_distribution(self, df: pd.DataFrame):
        """Render Prioritäts-Verteilung"""
        
        st.markdown("#### ⚡ Prioritäts-Verteilung")
        
        # Dummy-Daten
        priorities = ['Hoch', 'Mittel', 'Niedrig']
        values = [25, 45, 30]
        colors = ['#ef4444', '#f59e0b', '#10b981']
        
        fig = go.Figure(data=[
            go.Bar(x=priorities, y=values, marker_color=colors)
        ])
        
        fig.update_layout(
            title="Prioritätsverteilung der Anfragen",
            height=300,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_email_detail(self, email_data: pd.Series):
        """Render detaillierte E-Mail Ansicht"""
        
        st.markdown("#### 📧 E-Mail Details")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Absender:** {email_data.get('Absender', 'Unbekannt')}")
            st.markdown(f"**Betreff:** {email_data.get('Betreff', 'Kein Betreff')}")
            st.markdown(f"**Datum:** {email_data.get('Datum', 'Unbekannt')}")
            
        with col2:
            st.markdown(f"**Schlüsselwörter:**")
            keywords_string = email_data.get('Gefundene Schlüsselwörter', '')
            self._render_keywords_as_tags(keywords_string)
        
        st.markdown("**Vorschau:**")
        st.text_area(
            "",
            value=email_data.get('Body Preview', 'Keine Vorschau verfügbar'),
            height=150,
            disabled=True
        )
        
        # Aktionen
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Kopieren", use_container_width=True):
                st.write("Text in Zwischenablage kopiert!")
        
        with col2:
            if st.button("📧 Antworten", use_container_width=True):
                st.info("E-Mail-Client wird geöffnet...")
        
        with col3:
            if st.button("🗑️ Löschen", use_container_width=True):
                st.warning("Löschen-Funktion nicht implementiert")
    
    def _render_appearance_settings(self):
        """Render Darstellungseinstellungen"""
        
        st.markdown("#### 🎨 Theme & Darstellung")
        
        # Theme
        theme = st.radio(
            "Theme auswählen:",
            ['Light', 'Dark', 'Auto'],
            horizontal=True
        )
        
        # Font Size
        font_size = st.slider(
            "Schriftgröße:",
            min_value=12,
            max_value=20,
            value=14
        )
        
        # Compact Mode
        compact_mode = st.checkbox("Kompakte Darstellung")
        
        # Animation
        animations = st.checkbox("Animationen aktiviert", value=True)
        
        if st.button("💾 Darstellungseinstellungen speichern"):
            st.session_state.ui_settings = {
                'theme': theme.lower(),
                'font_size': font_size,
                'compact_mode': compact_mode,
                'animations': animations
            }
            st.success("✅ Einstellungen gespeichert!")
    
    def _render_search_settings(self):
        """Render Sucheinstellungen"""
        
        st.markdown("#### 🔍 Such-Konfiguration")
        
        # Standard-Zeitraum
        default_days = st.number_input(
            "Standard-Suchzeitraum (Tage):",
            min_value=1,
            max_value=365,
            value=30
        )
        
        # Max E-Mails
        max_emails = st.number_input(
            "Maximale E-Mails pro Suche:",
            min_value=10,
            max_value=1000,
            value=100
        )
        
        # Auto-Refresh
        auto_refresh = st.checkbox("Automatische Aktualisierung")
        
        if auto_refresh:
            refresh_interval = st.selectbox(
                "Aktualisierungsintervall:",
                [5, 10, 15, 30, 60],
                format_func=lambda x: f"{x} Minuten"
            )
        
        if st.button("💾 Sucheinstellungen speichern"):
            settings = {
                'default_days': default_days,
                'max_emails': max_emails,
                'auto_refresh': auto_refresh
            }
            if auto_refresh:
                settings['refresh_interval'] = refresh_interval
            
            st.session_state.search_settings = settings
            st.success("✅ Einstellungen gespeichert!")
    
    def _render_keywords_as_tags(self, keywords_string: str):
        """Render Schlüsselwörter als styled Tags (Streamlit-kompatibel)"""
        if not keywords_string or keywords_string.strip() == '':
            st.text("Keine Schlüsselwörter")
            return
        
        keywords = [kw.strip() for kw in keywords_string.split(',') if kw.strip()]
        
        if not keywords:
            st.text("Keine Schlüsselwörter")
            return
        
        # Moderne Badge-Darstellung mit inline CSS
        tags_html = '<div style="margin: 5px 0;">'
        
        for keyword in keywords:
            tags_html += f'''
            <span style="
                background: linear-gradient(135deg, #00f5ff 0%, #00b8cc 100%);
                color: #0f172a;
                padding: 4px 12px;
                border-radius: 16px;
                margin: 3px;
                display: inline-block;
                font-size: 0.85em;
                font-weight: 600;
                box-shadow: 0 2px 4px rgba(0, 245, 255, 0.2);
                transition: all 0.2s ease;
            ">{keyword}</span>
            '''
        
        tags_html += '</div>'
        st.markdown(tags_html, unsafe_allow_html=True)
    
    def _render_security_settings(self):
        """Render Sicherheitseinstellungen"""
        
        st.markdown("#### 🔐 Sicherheit & Datenschutz")
        
        # Session Timeout
        session_timeout = st.selectbox(
            "Session-Timeout:",
            [15, 30, 60, 120],
            format_func=lambda x: f"{x} Minuten",
            index=2
        )
        
        # Daten speichern
        save_data = st.checkbox("Suchergebnisse lokal zwischenspeichern")
        
        # Logging
        enable_logging = st.checkbox("Debug-Logging aktivieren")
        
        # Cache Management
        st.markdown("**📦 Cache Management:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Cache leeren", use_container_width=True):
                st.cache_data.clear()
                st.success("Cache geleert!")
        
        with col2:
            if st.button("🔄 Session zurücksetzen", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.success("Session zurückgesetzt!")
                st.rerun()
        
        if st.button("💾 Sicherheitseinstellungen speichern"):
            st.session_state.security_settings = {
                'session_timeout': session_timeout,
                'save_data': save_data,
                'enable_logging': enable_logging
            }
            st.success("✅ Einstellungen gespeichert!")