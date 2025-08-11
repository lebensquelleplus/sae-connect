"""
Gmail IMAP Client für die Cancellation Tracker App
Sichere und effiziente Gmail-Verbindung
"""

import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional, Any
import ssl
from dataclasses import dataclass

# from config import AppConfig, SecurityConfig
from ../config/app_config import AppConfig
from ../config/security_config import SecurityConfig

@dataclass
class EmailData:
    """Datenklasse für E-Mail Informationen"""
    id: str
    subject: str
    sender: str
    date: str
    body: str
    raw_date: datetime
    message_id: str
    
class GmailClient:
    """Gmail IMAP Client mit erweiterten Funktionen"""
    
    def __init__(self):
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.email: Optional[str] = None
        self.is_authenticated = False
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup Logging für den Gmail Client"""
        logger = logging.getLogger(f"{__name__}.GmailClient")
        logger.setLevel(getattr(logging, SecurityConfig.LOG_LEVEL))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def connect(self, email_address: str, app_password: str) -> bool:
        """
        Stelle Verbindung zu Gmail her
        
        Args:
            email_address: Gmail-Adresse
            app_password: Gmail App-Passwort
            
        Returns:
            bool: True wenn Verbindung erfolgreich
        """
        try:
            self.logger.info(f"Versuche Verbindung zu Gmail für {email_address}")
            
            # SSL-Kontext erstellen
            context = ssl.create_default_context()
            
            # IMAP Verbindung aufbauen
            self.connection = imaplib.IMAP4_SSL(
                AppConfig.GMAIL_IMAP_SERVER,
                AppConfig.GMAIL_IMAP_PORT,
                ssl_context=context
            )
            
            # Anmeldung
            self.connection.login(email_address, app_password)
            
            # Posteingang auswählen
            self.connection.select('INBOX')
            
            self.email = email_address
            self.is_authenticated = True
            
            self.logger.info("Gmail-Verbindung erfolgreich hergestellt")
            return True
            
        except imaplib.IMAP4.error as e:
            self.logger.error(f"IMAP Fehler: {e}")
            self._cleanup_connection()
            return False
            
        except Exception as e:
            self.logger.error(f"Verbindungsfehler: {e}")
            self._cleanup_connection()
            return False
    
    def disconnect(self):
        """Verbindung sicher beenden"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                self.logger.info("Gmail-Verbindung beendet")
            except:
                pass  # Fehler beim Trennen ignorieren
            finally:
                self._cleanup_connection()
    
    def is_connected(self) -> bool:
        """Prüfe ob Verbindung aktiv ist"""
        if not self.connection or not self.is_authenticated:
            return False
            
        try:
            # Ping durch NOOP
            self.connection.noop()
            return True
        except:
            self._cleanup_connection()
            return False
    
    def search_emails(
        self, 
        days_back: int = 30,
        max_emails: int = 100,
        sender_filter: str = '',
        subject_filter: str = ''
    ) -> List[EmailData]:
        """
        Suche E-Mails nach Kriterien
        
        Args:
            days_back: Tage zurück suchen
            max_emails: Maximale Anzahl E-Mails
            sender_filter: Filter für Absender
            subject_filter: Filter für Betreff
            
        Returns:
            List[EmailData]: Liste der gefundenen E-Mails
        """
        if not self.is_connected():
            raise ConnectionError("Keine aktive Gmail-Verbindung")
        
        try:
            # Suchdatum berechnen
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # Suchkriterien aufbauen
            search_criteria = [f'SINCE "{since_date}"']
            
            if sender_filter:
                search_criteria.append(f'FROM "{sender_filter}"')
            
            if subject_filter:
                search_criteria.append(f'SUBJECT "{subject_filter}"')
            
            # Suche ausführen
            search_string = ' '.join(search_criteria)
            self.logger.info(f"Suche E-Mails mit Kriterien: {search_string}")
            
            result, data = self.connection.search(None, f'({search_string})')
            
            if result != 'OK':
                raise Exception(f"Suche fehlgeschlagen: {result}")
            
            email_ids = data[0].split()
            
            if not email_ids:
                self.logger.info("Keine E-Mails gefunden")
                return []
            
            # Limitierung anwenden
            email_ids = email_ids[-max_emails:] if len(email_ids) > max_emails else email_ids
            
            self.logger.info(f"Verarbeite {len(email_ids)} E-Mails")
            
            # E-Mails abrufen und verarbeiten
            emails = []
            for email_id in email_ids:
                email_data = self._fetch_email_data(email_id)
                if email_data:
                    emails.append(email_data)
            
            self.logger.info(f"Erfolgreich {len(emails)} E-Mails verarbeitet")
            return emails
            
        except Exception as e:
            self.logger.error(f"Fehler bei E-Mail Suche: {e}")
            raise
    
    def get_email_count(self, days_back: int = 30) -> int:
        """
        Hole Anzahl der E-Mails im Zeitraum
        
        Args:
            days_back: Tage zurück
            
        Returns:
            int: Anzahl E-Mails
        """
        if not self.is_connected():
            return 0
        
        try:
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            result, data = self.connection.search(None, f'SINCE "{since_date}"')
            
            if result == 'OK':
                return len(data[0].split())
            return 0
            
        except Exception as e:
            self.logger.error(f"Fehler beim Zählen der E-Mails: {e}")
            return 0
    
    def _fetch_email_data(self, email_id: bytes) -> Optional[EmailData]:
        """
        Hole E-Mail Daten für eine bestimmte ID
        
        Args:
            email_id: E-Mail ID
            
        Returns:
            Optional[EmailData]: E-Mail Daten oder None bei Fehler
        """
        try:
            # E-Mail abrufen
            result, data = self.connection.fetch(email_id, '(RFC822)')
            
            if result != 'OK':
                return None
            
            # E-Mail parsen
            email_body = data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Header dekodieren
            subject = self._decode_header(email_message.get('Subject', ''))
            sender = self._decode_header(email_message.get('From', ''))
            date_str = email_message.get('Date', '')
            message_id = email_message.get('Message-ID', '')
            
            # Datum parsen mit timezone-sicherer Behandlung
            try:
                raw_date = email.utils.parsedate_to_datetime(date_str)
                # Falls timezone-aware, zu naive konvertieren für Konsistenz
                if raw_date.tzinfo is not None:
                    raw_date = raw_date.replace(tzinfo=None)
            except (ValueError, TypeError):
                raw_date = datetime.now().replace(tzinfo=None)
            
            # Body extrahieren
            body = self._extract_body(email_message)
            
            return EmailData(
                id=email_id.decode(),
                subject=subject,
                sender=sender,
                date=date_str,
                body=body,
                raw_date=raw_date,
                message_id=message_id
            )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der E-Mail {email_id}: {e}")
            return None
    
    def _decode_header(self, header_value: str) -> str:
        """
        Dekodiere MIME-Header
        
        Args:
            header_value: Header-Wert
            
        Returns:
            str: Dekodierter String
        """
        if not header_value:
            return ""
        
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
                    
            return decoded_string.strip()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Dekodieren des Headers: {e}")
            return str(header_value)
    
    def _extract_body(self, email_message: email.message.EmailMessage) -> str:
        """
        Extrahiere E-Mail Body
        
        Args:
            email_message: E-Mail Message Objekt
            
        Returns:
            str: E-Mail Body Text
        """
        body = ""
        
        try:
            if email_message.is_multipart():
                # Multipart E-Mail
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    
                    if content_type == "text/plain":
                        try:
                            part_body = part.get_payload(decode=True)
                            if part_body:
                                body += part_body.decode('utf-8', errors='ignore')
                        except Exception as e:
                            self.logger.warning(f"Fehler beim Dekodieren des E-Mail Parts: {e}")
                            
                    elif content_type == "text/html" and not body:
                        # HTML nur als Fallback verwenden
                        try:
                            part_body = part.get_payload(decode=True)
                            if part_body:
                                # Einfache HTML-zu-Text Konvertierung
                                html_body = part_body.decode('utf-8', errors='ignore')
                                body = self._html_to_text(html_body)
                        except Exception as e:
                            self.logger.warning(f"Fehler beim Verarbeiten von HTML: {e}")
            else:
                # Einfache E-Mail
                try:
                    email_body = email_message.get_payload(decode=True)
                    if email_body:
                        body = email_body.decode('utf-8', errors='ignore')
                except Exception as e:
                    self.logger.warning(f"Fehler beim Dekodieren der einfachen E-Mail: {e}")
                    body = str(email_message.get_payload())
            
            return body.strip()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren des E-Mail Body: {e}")
            return ""
    
    def _html_to_text(self, html: str) -> str:
        """
        Einfache HTML-zu-Text Konvertierung
        
        Args:
            html: HTML String
            
        Returns:
            str: Text ohne HTML-Tags
        """
        import re
        
        # HTML-Tags entfernen
        text = re.sub(r'<[^>]+>', '', html)
        
        # HTML-Entities dekodieren
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # Mehrfache Leerzeichen und Zeilenschaltungen normalisieren
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _cleanup_connection(self):
        """Verbindung zurücksetzen"""
        self.connection = None
        self.email = None
        self.is_authenticated = False
    
    def __del__(self):
        """Destruktor - Verbindung sicher beenden"""
        self.disconnect()