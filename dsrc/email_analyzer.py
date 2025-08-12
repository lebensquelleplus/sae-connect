"""
E-Mail Analyzer für Stornierungsanfragen
Intelligente Analyse und Klassifizierung von E-Mails
"""

import re
from datetime import datetime
from typing import List, Dict, Set, Any, Optional
from dataclasses import dataclass
import logging
from collections import Counter

#from config import EmailConfig, SecurityConfig
from ../config.email_config import EmailConfig
from ../config.security_config import SecurityConfig
from .gmail_client import EmailData

@dataclass
class CancellationMatch:
    """Datenklasse für Stornierungsübereinstimmungen"""
    keyword: str
    context: str
    position: int
    confidence: float
    category: str

@dataclass
class AnalysisResult:
    """Ergebnis der E-Mail Analyse"""
    email_data: EmailData
    is_cancellation: bool
    matches: List[CancellationMatch]
    confidence_score: float
    priority_level: str
    amazon_related: bool
    order_numbers: List[str]

class EmailAnalyzer:
    """Intelligenter E-Mail Analyzer für Stornierungsanfragen"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.cancellation_keywords = self._load_keywords()
        self.amazon_patterns = self._compile_amazon_patterns()
        self.order_number_patterns = self._compile_order_patterns()
    
    @staticmethod
    def _normalize_datetime(dt: datetime) -> datetime:
        """Normalisiere datetime zu timezone-naive für sichere Vergleiche"""
        if dt is None:
            return datetime.now().replace(tzinfo=None)
        
        if isinstance(dt, datetime):
            # Wenn timezone-aware, zu naive konvertieren
            if dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt
        
        # Fallback für andere Typen
        return datetime.now().replace(tzinfo=None)
        
    def _setup_logger(self) -> logging.Logger:
        """Setup Logging für den Analyzer"""
        logger = logging.getLogger(f"{__name__}.EmailAnalyzer")
        logger.setLevel(getattr(logging, SecurityConfig.LOG_LEVEL))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _load_keywords(self) -> Dict[str, List[str]]:
        """Lade und kategorisiere Schlüsselwörter"""
        return {
            'primary_de': EmailConfig.CANCELLATION_KEYWORDS_DE,
            'primary_en': EmailConfig.CANCELLATION_KEYWORDS_EN,
            'amazon': EmailConfig.AMAZON_KEYWORDS,
            'priority': EmailConfig.HIGH_PRIORITY_KEYWORDS
        }
    
    def _compile_amazon_patterns(self) -> List[re.Pattern]:
        """Kompiliere Regex-Patterns für Amazon-Erkennung"""
        patterns = [
            re.compile(r'amazon\.de', re.IGNORECASE),
            re.compile(r'amazon\.com', re.IGNORECASE),
            re.compile(r'amazon-.*@amazon\.(de|com)', re.IGNORECASE),
            re.compile(r'bestellung.*amazon', re.IGNORECASE),
            re.compile(r'amazon.*bestellung', re.IGNORECASE),
            re.compile(r'order.*amazon', re.IGNORECASE),
            re.compile(r'amazon.*order', re.IGNORECASE)
        ]
        return patterns
    
    def _compile_order_patterns(self) -> List[re.Pattern]:
        """Kompiliere Patterns für Bestellnummern"""
        patterns = [
            re.compile(r'(\d{3}-\d{7}-\d{7})', re.IGNORECASE),  # Amazon DE
            re.compile(r'(\d{3}-\d{7}-\d{7})', re.IGNORECASE),  # Amazon US
            re.compile(r'bestellnummer[:\s]*([A-Z0-9-]{10,})', re.IGNORECASE),
            re.compile(r'order number[:\s]*([A-Z0-9-]{10,})', re.IGNORECASE),
            re.compile(r'auftragsnummer[:\s]*([A-Z0-9-]{10,})', re.IGNORECASE),
            re.compile(r'ref[:\s]*([A-Z0-9-]{10,})', re.IGNORECASE)
        ]
        return patterns
    
    def analyze_cancellation_requests(self, emails: List[EmailData]) -> Dict[str, Any]:
        """
        Analysiere E-Mails auf Stornierungsanfragen
        
        Args:
            emails: Liste der zu analysierenden E-Mails
            
        Returns:
            Dict: Analyse-Ergebnisse
        """
        self.logger.info(f"Starte Analyse von {len(emails)} E-Mails")
        
        results = []
        cancellation_emails = []
        statistics = {
            'total_emails': len(emails),
            'cancellation_count': 0,
            'amazon_related': 0,
            'high_priority': 0,
            'keyword_distribution': Counter(),
            'sender_distribution': Counter(),
            'date_distribution': Counter()
        }
        
        for email_data in emails:
            try:
                analysis = self._analyze_single_email(email_data)
                results.append(analysis)
                
                # Statistiken aktualisieren
                self._update_statistics(statistics, analysis)
                
                # Stornierungsanfragen sammeln
                if analysis.is_cancellation:
                    cancellation_email = self._format_cancellation_result(analysis)
                    cancellation_emails.append(cancellation_email)
                    
            except Exception as e:
                self.logger.error(f"Fehler bei der Analyse der E-Mail {email_data.id}: {e}")
                continue
        
        # Finale Statistiken
        statistics['cancellation_rate'] = (
            statistics['cancellation_count'] / statistics['total_emails'] * 100
            if statistics['total_emails'] > 0 else 0
        )
        
        self.logger.info(
            f"Analyse abgeschlossen: {statistics['cancellation_count']} Stornierungsanfragen gefunden"
        )
        
        return {
            'cancellation_emails': cancellation_emails,
            'all_emails': [self._format_email_summary(r.email_data) for r in results],
            'statistics': statistics,
            'timestamp': datetime.now().isoformat(),
            'analysis_results': results
        }
    
    def _analyze_single_email(self, email_data: EmailData) -> AnalysisResult:
        """
        Analysiere eine einzelne E-Mail
        
        Args:
            email_data: E-Mail Daten
            
        Returns:
            AnalysisResult: Analyse-Ergebnis
        """
        # Text für Analyse vorbereiten
        full_text = f"{email_data.subject} {email_data.body}".lower()
        
        # Schlüsselwort-Matches finden
        matches = self._find_keyword_matches(full_text, email_data)
        
        # Confidence Score berechnen
        confidence_score = self._calculate_confidence_score(matches, email_data)
        
        # Klassifizierung
        is_cancellation = confidence_score >= 0.3  # Threshold für Stornierung
        
        # Prioritätslevel bestimmen
        priority_level = self._determine_priority_level(matches, confidence_score)
        
        # Amazon-Bezug prüfen
        amazon_related = self._check_amazon_relation(email_data)
        
        # Bestellnummern extrahieren
        order_numbers = self._extract_order_numbers(full_text)
        
        return AnalysisResult(
            email_data=email_data,
            is_cancellation=is_cancellation,
            matches=matches,
            confidence_score=confidence_score,
            priority_level=priority_level,
            amazon_related=amazon_related,
            order_numbers=order_numbers
        )
    
    def _find_keyword_matches(self, text: str, email_data: EmailData) -> List[CancellationMatch]:
        """Finde Schlüsselwort-Übereinstimmungen"""
        matches = []
        
        # Alle Keyword-Kategorien durchgehen
        for category, keywords in self.cancellation_keywords.items():
            for keyword in keywords:
                # Keyword suchen (case-insensitive)
                pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
                
                for match in pattern.finditer(text):
                    # Kontext extrahieren (50 Zeichen vor und nach dem Match)
                    start_pos = max(0, match.start() - 50)
                    end_pos = min(len(text), match.end() + 50)
                    context = text[start_pos:end_pos].strip()
                    
                    # Confidence basierend auf Kategorie und Position
                    confidence = self._calculate_match_confidence(
                        keyword, category, match.start(), email_data
                    )
                    
                    matches.append(CancellationMatch(
                        keyword=keyword,
                        context=context,
                        position=match.start(),
                        confidence=confidence,
                        category=category
                    ))
        
        # Matches nach Confidence sortieren
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return matches
    
    def _calculate_match_confidence(
        self, 
        keyword: str, 
        category: str, 
        position: int, 
        email_data: EmailData
    ) -> float:
        """Berechne Confidence für einen Match"""
        base_confidence = {
            'primary_de': 0.8,
            'primary_en': 0.8,
            'amazon': 0.3,
            'priority': 0.9
        }.get(category, 0.5)
        
        # Bonus für Position im Betreff
        if position < len(email_data.subject):
            base_confidence += 0.2
        
        # Bonus für kurze E-Mails (vermutlich fokussierter)
        if len(email_data.body) < 500:
            base_confidence += 0.1
        
        # Bonus für bestimmte Absender-Patterns
        if any(domain in email_data.sender.lower() for domain in ['customer', 'service', 'support']):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _calculate_confidence_score(self, matches: List[CancellationMatch], email_data: EmailData) -> float:
        """Berechne Gesamt-Confidence Score"""
        if not matches:
            return 0.0
        
        # Gewichtete Summe der besten Matches
        top_matches = matches[:5]  # Top 5 Matches
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for i, match in enumerate(top_matches):
            weight = 1.0 / (i + 1)  # Abnehmende Gewichtung
            weighted_score += match.confidence * weight
            total_weight += weight
        
        base_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Bonus-Faktoren
        bonus = 0.0
        
        # Mehrere verschiedene Keywords
        unique_keywords = len(set(m.keyword for m in matches))
        if unique_keywords > 2:
            bonus += 0.1
        
        # Amazon-Bezug
        if self._check_amazon_relation(email_data):
            bonus += 0.15
        
        # Bestellnummern vorhanden
        if self._extract_order_numbers(f"{email_data.subject} {email_data.body}"):
            bonus += 0.1
        
        # Aktuelle E-Mail (letzten 7 Tage) - mit timezone-sicherer Berechnung
        try:
            current_time = self._normalize_datetime(datetime.now())
            email_time = self._normalize_datetime(email_data.raw_date)
            
            # Sichere Differenz-Berechnung
            time_diff = current_time - email_time
            if time_diff.days <= 7:
                bonus += 0.05
                
        except Exception as e:
            # Bei Fehlern einfach den Bonus überspringen
            self.logger.warning(f"Fehler bei Zeitberechnung: {e}")
        
        return min(1.0, base_score + bonus)
    
    def _determine_priority_level(self, matches: List[CancellationMatch], confidence: float) -> str:
        """Bestimme Prioritätslevel"""
        # Prüfe auf Prioritäts-Keywords
        priority_matches = [m for m in matches if m.category == 'priority']
        
        if priority_matches or confidence >= 0.8:
            return 'hoch'
        elif confidence >= 0.5:
            return 'mittel'
        else:
            return 'niedrig'
    
    def _check_amazon_relation(self, email_data: EmailData) -> bool:
        """Prüfe Amazon-Bezug"""
        full_text = f"{email_data.subject} {email_data.body} {email_data.sender}".lower()
        
        return any(pattern.search(full_text) for pattern in self.amazon_patterns)
    
    def _extract_order_numbers(self, text: str) -> List[str]:
        """Extrahiere Bestellnummern"""
        order_numbers = []
        
        for pattern in self.order_number_patterns:
            matches = pattern.findall(text)
            order_numbers.extend(matches)
        
        # Duplikate entfernen und validieren
        unique_orders = list(set(order_numbers))
        
        # Nur gültig aussehende Bestellnummern behalten
        validated_orders = [
            order for order in unique_orders 
            if len(order) >= 8 and any(c.isdigit() for c in order)
        ]
        
        return validated_orders
    
    def _update_statistics(self, stats: Dict, analysis: AnalysisResult):
        """Aktualisiere Statistiken"""
        if analysis.is_cancellation:
            stats['cancellation_count'] += 1
        
        if analysis.amazon_related:
            stats['amazon_related'] += 1
        
        if analysis.priority_level == 'hoch':
            stats['high_priority'] += 1
        
        # Keyword-Verteilung
        for match in analysis.matches:
            stats['keyword_distribution'][match.keyword] += 1
        
        # Absender-Verteilung
        sender_domain = analysis.email_data.sender.split('@')[-1] if '@' in analysis.email_data.sender else 'unknown'
        stats['sender_distribution'][sender_domain] += 1
        
        # Datums-Verteilung (nach Tag)
        date_key = analysis.email_data.raw_date.strftime('%Y-%m-%d')
        stats['date_distribution'][date_key] += 1
    
    def _format_cancellation_result(self, analysis: AnalysisResult) -> Dict[str, Any]:
        """Formatiere Stornierungsanfrage für Ausgabe"""
        keywords = ', '.join(set(m.keyword for m in analysis.matches[:5]))
        
        return {
            'Absender': analysis.email_data.sender,
            'Betreff': analysis.email_data.subject,
            'Datum': analysis.email_data.date,
            'Gefundene Schlüsselwörter': keywords,
            'Body Preview': analysis.email_data.body[:200] + "..." if len(analysis.email_data.body) > 200 else analysis.email_data.body,
            'Confidence Score': f"{analysis.confidence_score:.2f}",
            'Priorität': analysis.priority_level,
            'Amazon-Bezug': 'Ja' if analysis.amazon_related else 'Nein',
            'Bestellnummern': ', '.join(analysis.order_numbers) if analysis.order_numbers else 'Keine gefunden',
            'Match Count': len(analysis.matches)
        }
    
    def _format_email_summary(self, email_data: EmailData) -> Dict[str, Any]:
        """Formatiere E-Mail Summary"""
        return {
            'id': email_data.id,
            'subject': email_data.subject,
            'sender': email_data.sender,
            'date': email_data.date,
            'body_length': len(email_data.body)
        }
    
    def get_keyword_suggestions(self, text: str) -> List[str]:
        """Schlage verwandte Schlüsselwörter vor"""
        text_lower = text.lower()
        suggestions = []
        
        # Ähnliche Begriffe basierend auf vorhandenen Keywords
        similarity_map = {
            'stornierung': ['annullierung', 'rückgängig', 'abbrechen'],
            'rückgabe': ['zurücksenden', 'retoure', 'umtausch'],
            'cancel': ['void', 'terminate', 'abort'],
            'refund': ['reimbursement', 'payback', 'return payment']
        }
        
        for keyword, similar in similarity_map.items():
            if keyword in text_lower:
                suggestions.extend(similar)
        
        return list(set(suggestions))
    
    def analyze_trends(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """Analysiere Trends in den Stornierungsanfragen"""
        if not results:
            return {}
        
        # Zeitraum-Analyse mit timezone-sicherer Behandlung
        dates = []
        for r in results:
            if r.is_cancellation and r.email_data.raw_date:
                try:
                    date = self._normalize_datetime(r.email_data.raw_date)
                    dates.append(date)
                except Exception:
                    # Bei Fehlern Datum überspringen
                    continue
        
        if not dates:
            return {}
        
        # Trend-Berechnung
        try:
            date_counts = Counter(d.strftime('%Y-%m-%d') for d in dates)
            weekday_counts = Counter(d.strftime('%A') for d in dates)
            hour_counts = Counter(d.hour for d in dates)
            
            return {
                'daily_trend': dict(date_counts.most_common()),
                'weekday_pattern': dict(weekday_counts.most_common()),
                'hourly_pattern': dict(hour_counts.most_common()),
                'peak_day': weekday_counts.most_common(1)[0] if weekday_counts else None,
                'peak_hour': hour_counts.most_common(1)[0] if hour_counts else None
            }
        except Exception as e:
            self.logger.error(f"Fehler bei Trend-Analyse: {e}")
            return {}
