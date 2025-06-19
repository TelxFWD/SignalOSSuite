"""
Data models for signal processing
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class SignalStatus(Enum):
    """Signal execution status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class SignalAction(Enum):
    """Trading action enumeration"""
    BUY = "BUY"
    SELL = "SELL"

class SignalSource(Enum):
    """Signal source enumeration"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    MANUAL = "manual"
    API = "api"

@dataclass
class RawSignal:
    """Raw signal data from external sources"""
    text: str
    source_id: str
    source_name: str
    message_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    has_media: bool = False
    media_type: Optional[str] = None
    media_path: Optional[str] = None
    source_type: SignalSource = SignalSource.TELEGRAM
    raw_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.timestamp is None:
            self.timestamp = self.created_at
        
        # Ensure text is not None
        if self.text is None:
            self.text = ""

@dataclass
class ParsedSignal:
    """Parsed and structured signal data"""
    raw_signal_id: Optional[str]
    pair: Optional[str]
    action: Optional[str]
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    take_profit_levels: List[float] = field(default_factory=list)
    lot_size: Optional[float] = None
    confidence: float = 0.0
    parsed_at: datetime = field(default_factory=datetime.now)
    parser_version: str = "1.0"
    extraction_method: str = "nlp"  # nlp, ocr, regex, manual
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation"""
        # Normalize action
        if self.action:
            self.action = self.action.upper()
            if self.action not in ['BUY', 'SELL']:
                self.action = None
        
        # Validate confidence range
        self.confidence = max(0.0, min(1.0, self.confidence))
        
        # Ensure lot size is positive
        if self.lot_size is not None and self.lot_size <= 0:
            self.lot_size = None
    
    def is_valid(self) -> bool:
        """Check if parsed signal has minimum required data"""
        return (
            self.pair is not None and
            self.action is not None and
            self.action in ['BUY', 'SELL'] and
            len(self.pair) == 6 and
            self.confidence > 0
        )
    
    def has_entry_price(self) -> bool:
        """Check if signal has entry price"""
        return self.entry_price is not None and self.entry_price > 0
    
    def has_stop_loss(self) -> bool:
        """Check if signal has stop loss"""
        return self.stop_loss is not None and self.stop_loss > 0
    
    def has_take_profit(self) -> bool:
        """Check if signal has take profit"""
        return self.take_profit is not None and self.take_profit > 0
    
    def get_risk_reward_ratio(self) -> Optional[float]:
        """Calculate risk-reward ratio"""
        if not all([self.entry_price, self.stop_loss, self.take_profit]):
            return None
        
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.take_profit - self.entry_price)
        
        if risk == 0:
            return None
        
        return reward / risk

@dataclass
class ExecutionSignal:
    """Signal prepared for execution in MT5"""
    signal_id: str
    pair: str
    action: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    take_profit_levels: List[float] = field(default_factory=list)
    lot_size: float = 0.01
    magic_number: int = 123456
    comment: str = ""
    slippage: int = 3
    expiration: Optional[datetime] = None
    status: SignalStatus = SignalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    execution_time: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Execution results
    actual_entry_price: Optional[float] = None
    actual_lot_size: Optional[float] = None
    order_id: Optional[str] = None
    ticket_number: Optional[int] = None
    execution_error: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Normalize action
        if self.action:
            self.action = self.action.upper()
        
        # Set execution time if not provided
        if self.execution_time is None:
            self.execution_time = self.created_at
        
        # Validate lot size
        if self.lot_size <= 0:
            self.lot_size = 0.01
        
        # Limit comment length
        if len(self.comment) > 30:
            self.comment = self.comment[:30]
    
    def update_status(self, new_status: SignalStatus, error_message: str = None):
        """Update signal status"""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if error_message:
            self.execution_error = error_message
        
        if new_status == SignalStatus.EXECUTED:
            self.executed_at = datetime.now()
    
    def is_expired(self) -> bool:
        """Check if signal has expired"""
        if self.expiration is None:
            return False
        return datetime.now() > self.expiration
    
    def can_execute(self) -> bool:
        """Check if signal can be executed"""
        return (
            self.status == SignalStatus.PENDING and
            not self.is_expired() and
            self.pair and
            self.action in ['BUY', 'SELL'] and
            self.lot_size > 0
        )
    
    def to_mt5_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MT5 EA communication"""
        return {
            'signal_id': self.signal_id,
            'pair': self.pair,
            'action': self.action,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'lot_size': self.lot_size,
            'magic_number': self.magic_number,
            'comment': self.comment,
            'slippage': self.slippage,
            'timestamp': self.created_at.isoformat(),
            'execution_time': self.execution_time.isoformat() if self.execution_time else None,
            'expiration': self.expiration.isoformat() if self.expiration else None
        }

@dataclass
class SignalPerformance:
    """Signal performance tracking"""
    signal_id: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    profit_loss_pips: Optional[float] = None
    profit_loss_amount: Optional[float] = None
    max_favorable_excursion: Optional[float] = None
    max_adverse_excursion: Optional[float] = None
    duration_minutes: Optional[int] = None
    win: Optional[bool] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_performance(self, action: str, pair: str):
        """Calculate performance metrics"""
        if not all([self.entry_price, self.exit_price]):
            return
        
        # Calculate pip difference
        price_diff = self.exit_price - self.entry_price
        
        # Adjust for action type
        if action == 'SELL':
            price_diff = -price_diff
        
        # Calculate pips (simplified)
        if pair.endswith('JPY'):
            self.profit_loss_pips = price_diff * 100
        else:
            self.profit_loss_pips = price_diff * 10000
        
        # Determine win/loss
        self.win = self.profit_loss_pips > 0
        
        # Calculate duration
        if self.exit_time:
            duration = self.exit_time - self.entry_time
            self.duration_minutes = int(duration.total_seconds() / 60)

@dataclass
class SignalStatistics:
    """Signal processing and execution statistics"""
    total_signals_received: int = 0
    total_signals_parsed: int = 0
    total_signals_executed: int = 0
    parsing_success_rate: float = 0.0
    execution_success_rate: float = 0.0
    average_confidence: float = 0.0
    average_execution_time_ms: float = 0.0
    
    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pips: float = 0.0
    total_profit_loss: float = 0.0
    
    # Source breakdown
    signals_by_source: Dict[str, int] = field(default_factory=dict)
    signals_by_pair: Dict[str, int] = field(default_factory=dict)
    
    # Time tracking
    last_updated: datetime = field(default_factory=datetime.now)
    period_start: datetime = field(default_factory=datetime.now)
    
    def update_parsing_stats(self, received: int, parsed: int, avg_confidence: float):
        """Update parsing statistics"""
        self.total_signals_received += received
        self.total_signals_parsed += parsed
        
        if self.total_signals_received > 0:
            self.parsing_success_rate = (self.total_signals_parsed / self.total_signals_received) * 100
        
        self.average_confidence = avg_confidence
        self.last_updated = datetime.now()
    
    def update_execution_stats(self, attempted: int, executed: int, avg_time_ms: float):
        """Update execution statistics"""
        self.total_signals_executed += executed
        
        if attempted > 0:
            self.execution_success_rate = (executed / attempted) * 100
        
        self.average_execution_time_ms = avg_time_ms
        self.last_updated = datetime.now()
    
    def update_performance_stats(self, performance_data: List[SignalPerformance]):
        """Update performance statistics"""
        if not performance_data:
            return
        
        self.total_trades = len(performance_data)
        self.winning_trades = sum(1 for p in performance_data if p.win)
        self.losing_trades = self.total_trades - self.winning_trades
        
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        # Calculate total pips and P/L
        self.total_pips = sum(p.profit_loss_pips or 0 for p in performance_data)
        self.total_profit_loss = sum(p.profit_loss_amount or 0 for p in performance_data)
        
        self.last_updated = datetime.now()
    
    def reset_period(self):
        """Reset statistics for new period"""
        self.total_signals_received = 0
        self.total_signals_parsed = 0
        self.total_signals_executed = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pips = 0.0
        self.total_profit_loss = 0.0
        self.signals_by_source.clear()
        self.signals_by_pair.clear()
        self.period_start = datetime.now()
        self.last_updated = datetime.now()

@dataclass
class SignalAlert:
    """Signal alert/notification data"""
    signal_id: str
    alert_type: str  # success, warning, error
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def acknowledge(self):
        """Mark alert as acknowledged"""
        self.acknowledged = True

# Utility functions for signal models

def create_raw_signal_from_telegram(message_data: Dict[str, Any]) -> RawSignal:
    """Create RawSignal from Telegram message data"""
    return RawSignal(
        text=message_data.get('text', ''),
        source_id=str(message_data.get('chat_id', '')),
        source_name=message_data.get('chat_title', 'Unknown'),
        message_id=str(message_data.get('message_id', '')),
        sender_id=str(message_data.get('sender_id', '')),
        sender_name=message_data.get('sender_name', ''),
        has_media=message_data.get('has_media', False),
        media_type=message_data.get('media_type'),
        timestamp=message_data.get('timestamp'),
        source_type=SignalSource.TELEGRAM,
        raw_data=message_data
    )

def create_execution_signal_from_parsed(parsed_signal: ParsedSignal, signal_id: str) -> ExecutionSignal:
    """Create ExecutionSignal from ParsedSignal"""
    return ExecutionSignal(
        signal_id=signal_id,
        pair=parsed_signal.pair,
        action=parsed_signal.action,
        entry_price=parsed_signal.entry_price,
        stop_loss=parsed_signal.stop_loss,
        take_profit=parsed_signal.take_profit,
        lot_size=parsed_signal.lot_size or 0.01,
        metadata={
            'original_confidence': parsed_signal.confidence,
            'parser_version': parsed_signal.parser_version,
            'extraction_method': parsed_signal.extraction_method,
            'parsed_at': parsed_signal.parsed_at.isoformat()
        }
    )

def validate_currency_pair(pair: str) -> bool:
    """Validate currency pair format"""
    if not pair or len(pair) != 6:
        return False
    
    # Check if all characters are letters
    if not pair.isalpha():
        return False
    
    # Check if it follows XXX/YYY pattern
    base_currency = pair[:3].upper()
    quote_currency = pair[3:].upper()
    
    # List of valid currency codes (simplified)
    valid_currencies = {
        'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD',
        'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'TRY', 'ZAR',
        'SGD', 'HKD', 'MXN', 'INR', 'CNY', 'KRW', 'THB', 'MYR'
    }
    
    return base_currency in valid_currencies and quote_currency in valid_currencies

