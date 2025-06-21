"""
SignalOS News Filter
Economic calendar integration and news-based trading filters
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class NewsImpact(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@dataclass
class NewsEvent:
    event_id: str
    title: str
    currency: str
    impact: NewsImpact
    event_time: datetime
    actual: Optional[str] = None
    forecast: Optional[str] = None
    previous: Optional[str] = None
    
@dataclass
class NewsFilterSettings:
    enabled: bool = False
    block_before_minutes: int = 30
    block_after_minutes: int = 30
    minimum_impact: NewsImpact = NewsImpact.HIGH
    currencies_to_monitor: List[str] = None
    specific_events_to_monitor: List[str] = None
    
    def __post_init__(self):
        if self.currencies_to_monitor is None:
            self.currencies_to_monitor = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']
        if self.specific_events_to_monitor is None:
            self.specific_events_to_monitor = [
                'Non Farm Payrolls', 'Federal Funds Rate', 'CPI', 'GDP', 'PMI',
                'ECB Interest Rate Decision', 'BoE Interest Rate Decision'
            ]

@dataclass
class TimeWindowSettings:
    enabled: bool = False
    trading_sessions: List[Dict[str, Any]] = None
    excluded_days: List[str] = None  # ['Saturday', 'Sunday']
    timezone: str = "UTC"
    
    def __post_init__(self):
        if self.trading_sessions is None:
            self.trading_sessions = [
                {'name': 'London', 'start_hour': 8, 'end_hour': 17},
                {'name': 'New York', 'start_hour': 13, 'end_hour': 22}
            ]
        if self.excluded_days is None:
            self.excluded_days = ['Saturday', 'Sunday']

class NewsFilter:
    """Economic news and time window filtering system"""
    
    def __init__(self, settings: NewsFilterSettings = None, time_settings: TimeWindowSettings = None):
        self.settings = settings or NewsFilterSettings()
        self.time_settings = time_settings or TimeWindowSettings()
        self.news_events: List[NewsEvent] = []
        self.last_news_update = datetime.min
        self.news_cache_duration = timedelta(hours=6)
        
    async def should_block_signal(self, signal_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if signal should be blocked due to news or time filters"""
        try:
            # Check time windows first
            time_blocked, time_reason = self._check_time_windows()
            if time_blocked:
                return True, time_reason
            
            # Check news filter
            if self.settings.enabled:
                news_blocked, news_reason = await self._check_news_filter(signal_data)
                if news_blocked:
                    return True, news_reason
            
            return False, "Signal approved"
            
        except Exception as e:
            logger.error(f"Error in news filter check: {e}")
            return False, "Filter check failed, allowing signal"
    
    def _check_time_windows(self) -> Tuple[bool, str]:
        """Check if current time is within allowed trading windows"""
        if not self.time_settings.enabled:
            return False, ""
        
        now = datetime.utcnow()
        current_day = now.strftime('%A')
        current_hour = now.hour
        
        # Check excluded days
        if current_day in self.time_settings.excluded_days:
            return True, f"Trading blocked on {current_day}"
        
        # Check if we're in any allowed session
        in_session = False
        for session in self.time_settings.trading_sessions:
            start_hour = session['start_hour']
            end_hour = session['end_hour']
            
            if start_hour <= current_hour < end_hour:
                in_session = True
                break
        
        if not in_session:
            return True, f"Outside trading hours (current: {current_hour:02d}:00 UTC)"
        
        return False, ""
    
    async def _check_news_filter(self, signal_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if signal should be blocked due to news events"""
        try:
            # Update news events if cache is stale
            await self._update_news_events_if_needed()
            
            pair = signal_data.get('pair', '')
            if not pair or len(pair) < 6:
                return False, ""
            
            # Extract currencies from pair
            base_currency = pair[:3]
            quote_currency = pair[3:6]
            
            # Check for upcoming news events
            now = datetime.utcnow()
            block_until = now + timedelta(minutes=self.settings.block_after_minutes)
            block_from = now - timedelta(minutes=self.settings.block_before_minutes)
            
            for event in self.news_events:
                # Skip if event is not relevant to our currencies
                if event.currency not in [base_currency, quote_currency]:
                    continue
                
                # Skip if impact is below threshold
                if self._get_impact_level(event.impact) < self._get_impact_level(self.settings.minimum_impact):
                    continue
                
                # Check if event is in the blocking window
                if block_from <= event.event_time <= block_until:
                    time_to_event = (event.event_time - now).total_seconds() / 60
                    return True, f"News event '{event.title}' for {event.currency} in {abs(time_to_event):.0f} minutes"
            
            return False, ""
            
        except Exception as e:
            logger.error(f"Error checking news filter: {e}")
            return False, "News check failed, allowing signal"
    
    def _get_impact_level(self, impact: NewsImpact) -> int:
        """Get numeric impact level for comparison"""
        levels = {NewsImpact.LOW: 1, NewsImpact.MEDIUM: 2, NewsImpact.HIGH: 3}
        return levels.get(impact, 1)
    
    async def _update_news_events_if_needed(self):
        """Update news events from external source if cache is stale"""
        now = datetime.utcnow()
        
        if now - self.last_news_update > self.news_cache_duration:
            await self._fetch_news_events()
            self.last_news_update = now
    
    async def _fetch_news_events(self):
        """Fetch news events from economic calendar API"""
        try:
            # This would integrate with actual news API like ForexFactory, Investing.com, etc.
            # For now, we'll simulate some upcoming events
            
            now = datetime.utcnow()
            simulated_events = [
                NewsEvent(
                    event_id="nfp_2025_06_21",
                    title="Non Farm Payrolls",
                    currency="USD",
                    impact=NewsImpact.HIGH,
                    event_time=now + timedelta(hours=2),
                    forecast="200K",
                    previous="185K"
                ),
                NewsEvent(
                    event_id="cpi_2025_06_21",
                    title="Consumer Price Index",
                    currency="EUR",
                    impact=NewsImpact.HIGH,
                    event_time=now + timedelta(hours=4),
                    forecast="2.1%",
                    previous="2.0%"
                ),
                NewsEvent(
                    event_id="boe_rate_2025_06_21",
                    title="BoE Interest Rate Decision",
                    currency="GBP",
                    impact=NewsImpact.HIGH,
                    event_time=now + timedelta(hours=6),
                    forecast="5.25%",
                    previous="5.25%"
                )
            ]
            
            # Filter events to only include future events within next 24 hours
            future_events = [
                event for event in simulated_events
                if now <= event.event_time <= now + timedelta(hours=24)
            ]
            
            self.news_events = future_events
            logger.info(f"Updated news events: {len(future_events)} events loaded")
            
        except Exception as e:
            logger.error(f"Error fetching news events: {e}")
            # Keep existing events on error
    
    def get_upcoming_events(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """Get upcoming news events"""
        now = datetime.utcnow()
        end_time = now + timedelta(hours=hours_ahead)
        
        upcoming = [
            event for event in self.news_events
            if now <= event.event_time <= end_time
        ]
        
        # Sort by time
        upcoming.sort(key=lambda x: x.event_time)
        
        return [
            {
                "event_id": event.event_id,
                "title": event.title,
                "currency": event.currency,
                "impact": event.impact.value,
                "event_time": event.event_time.isoformat(),
                "time_until": str(event.event_time - now),
                "forecast": event.forecast,
                "previous": event.previous
            }
            for event in upcoming
        ]
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update news filter settings"""
        try:
            for key, value in new_settings.items():
                if hasattr(self.settings, key):
                    if key == 'minimum_impact':
                        value = NewsImpact(value)
                    setattr(self.settings, key, value)
                    logger.info(f"Updated news filter setting {key} = {value}")
                    
        except Exception as e:
            logger.error(f"Error updating news filter settings: {e}")
    
    def update_time_settings(self, new_settings: Dict[str, Any]):
        """Update time window settings"""
        try:
            for key, value in new_settings.items():
                if hasattr(self.time_settings, key):
                    setattr(self.time_settings, key, value)
                    logger.info(f"Updated time setting {key} = {value}")
                    
        except Exception as e:
            logger.error(f"Error updating time settings: {e}")
    
    def get_filter_status(self) -> Dict[str, Any]:
        """Get current filter status and statistics"""
        now = datetime.utcnow()
        
        # Count upcoming events by impact
        upcoming_events = self.get_upcoming_events(24)
        impact_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for event in upcoming_events:
            impact_counts[event['impact']] += 1
        
        # Check current time window status
        time_blocked, time_reason = self._check_time_windows()
        
        return {
            'news_filter_enabled': self.settings.enabled,
            'time_filter_enabled': self.time_settings.enabled,
            'current_time_blocked': time_blocked,
            'time_block_reason': time_reason,
            'upcoming_events_24h': len(upcoming_events),
            'high_impact_events': impact_counts['HIGH'],
            'medium_impact_events': impact_counts['MEDIUM'],
            'low_impact_events': impact_counts['LOW'],
            'last_news_update': self.last_news_update.isoformat(),
            'news_cache_valid': (datetime.utcnow() - self.last_news_update) < self.news_cache_duration,
            'monitored_currencies': self.settings.currencies_to_monitor,
            'blocking_window': f"{self.settings.block_before_minutes}min before / {self.settings.block_after_minutes}min after",
            'minimum_impact_level': self.settings.minimum_impact.value,
            'trading_sessions': self.time_settings.trading_sessions,
            'excluded_days': self.time_settings.excluded_days
        }
    
    async def force_news_update(self) -> Dict[str, Any]:
        """Force update of news events"""
        try:
            await self._fetch_news_events()
            self.last_news_update = datetime.utcnow()
            
            return {
                'status': 'success',
                'message': 'News events updated successfully',
                'events_count': len(self.news_events),
                'update_time': self.last_news_update.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error forcing news update: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def add_custom_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add custom news event"""
        try:
            event = NewsEvent(
                event_id=event_data['event_id'],
                title=event_data['title'],
                currency=event_data['currency'],
                impact=NewsImpact(event_data['impact']),
                event_time=datetime.fromisoformat(event_data['event_time']),
                forecast=event_data.get('forecast'),
                previous=event_data.get('previous')
            )
            
            self.news_events.append(event)
            
            return {
                'status': 'success',
                'message': 'Custom event added successfully',
                'event_id': event.event_id
            }
            
        except Exception as e:
            logger.error(f"Error adding custom event: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def remove_event(self, event_id: str) -> Dict[str, Any]:
        """Remove news event"""
        try:
            original_count = len(self.news_events)
            self.news_events = [e for e in self.news_events if e.event_id != event_id]
            
            removed_count = original_count - len(self.news_events)
            
            return {
                'status': 'success',
                'message': f'Removed {removed_count} event(s)',
                'events_remaining': len(self.news_events)
            }
            
        except Exception as e:
            logger.error(f"Error removing event: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }