"""
SignalOS Enhanced Signal Parser
AI-powered signal parsing with multi-format support and edit tracking
"""
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SignalType(Enum):
    MARKET_ORDER = "MARKET_ORDER"
    PENDING_ORDER = "PENDING_ORDER"
    MODIFICATION = "MODIFICATION"
    CLOSURE = "CLOSURE"
    COMMAND = "COMMAND"

class ParseConfidence(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INVALID = "INVALID"

@dataclass
class ParsedSignal:
    signal_id: str
    original_text: str
    signal_type: SignalType
    confidence: ParseConfidence
    pair: Optional[str] = None
    action: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profits: List[float] = None
    lot_size: Optional[float] = None
    risk_percent: Optional[float] = None
    order_type: Optional[str] = None
    modification_type: Optional[str] = None
    provider_id: Optional[str] = None
    timestamp: datetime = None
    edit_sequence: int = 0
    original_message_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.take_profits is None:
            self.take_profits = []

class EnhancedSignalParser:
    """Advanced signal parser with AI-like pattern recognition"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.currency_pairs = self._initialize_currency_pairs()
        self.parse_history = {}
        self.provider_patterns = {}
        
    def parse_signal(self, text: str, provider_id: str = None, message_id: str = None) -> ParsedSignal:
        """Parse trading signal from text"""
        try:
            # Clean and normalize text
            cleaned_text = self._clean_text(text)
            
            # Generate signal ID
            signal_id = f"sig_{datetime.utcnow().timestamp()}_{hash(cleaned_text) % 10000}"
            
            # Detect signal type
            signal_type = self._detect_signal_type(cleaned_text)
            
            # Parse based on type
            if signal_type == SignalType.MARKET_ORDER or signal_type == SignalType.PENDING_ORDER:
                parsed = self._parse_trading_signal(cleaned_text, signal_id, signal_type)
            elif signal_type == SignalType.MODIFICATION:
                parsed = self._parse_modification_signal(cleaned_text, signal_id)
            elif signal_type == SignalType.CLOSURE:
                parsed = self._parse_closure_signal(cleaned_text, signal_id)
            elif signal_type == SignalType.COMMAND:
                parsed = self._parse_command_signal(cleaned_text, signal_id)
            else:
                parsed = ParsedSignal(
                    signal_id=signal_id,
                    original_text=text,
                    signal_type=SignalType.MARKET_ORDER,
                    confidence=ParseConfidence.INVALID
                )
            
            # Set metadata
            parsed.provider_id = provider_id
            parsed.original_message_id = message_id
            
            # Store in history for edit tracking
            if message_id:
                self._store_parse_history(message_id, parsed)
            
            # Learn provider patterns
            if provider_id and parsed.confidence != ParseConfidence.INVALID:
                self._learn_provider_patterns(provider_id, cleaned_text, parsed)
            
            logger.info(f"Parsed signal {signal_id}: {parsed.confidence.value} confidence")
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing signal: {e}")
            return ParsedSignal(
                signal_id=f"error_{datetime.utcnow().timestamp()}",
                original_text=text,
                signal_type=SignalType.MARKET_ORDER,
                confidence=ParseConfidence.INVALID
            )
    
    def parse_signal_edit(self, text: str, original_message_id: str, provider_id: str = None) -> ParsedSignal:
        """Parse edited/updated signal"""
        try:
            # Get original parse
            original_parse = self.parse_history.get(original_message_id)
            
            # Parse the edited text
            new_parse = self.parse_signal(text, provider_id, original_message_id)
            
            if original_parse:
                # Increment edit sequence
                new_parse.edit_sequence = original_parse.edit_sequence + 1
                new_parse.original_message_id = original_message_id
                
                # Detect what changed
                changes = self._detect_changes(original_parse, new_parse)
                new_parse.modification_type = json.dumps(changes)
                
                logger.info(f"Signal edit detected: {changes}")
            
            return new_parse
            
        except Exception as e:
            logger.error(f"Error parsing signal edit: {e}")
            return self.parse_signal(text, provider_id, original_message_id)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize signal text"""
        # Remove emojis and special characters
        text = re.sub(r'[^\w\s\.\,\:\;\-\+\%\/\(\)\[\]#]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Convert to uppercase for consistent processing
        text = text.upper().strip()
        
        return text
    
    def _detect_signal_type(self, text: str) -> SignalType:
        """Detect the type of signal"""
        # Command patterns
        command_patterns = [
            r'CLOSE\s+\d+%', r'CLOSE\s+ALL', r'CANCEL', r'DELETE',
            r'TP\s+TO', r'SL\s+TO', r'BREAK\s*EVEN', r'MODIFY'
        ]
        
        if any(re.search(pattern, text) for pattern in command_patterns):
            return SignalType.COMMAND
        
        # Modification patterns
        mod_patterns = [
            r'UPDATE', r'CHANGE', r'MOVE\s+SL', r'MOVE\s+TP',
            r'NEW\s+TP', r'NEW\s+SL'
        ]
        
        if any(re.search(pattern, text) for pattern in mod_patterns):
            return SignalType.MODIFICATION
        
        # Closure patterns
        close_patterns = [
            r'CLOSE', r'EXIT', r'PROFIT', r'LOSS'
        ]
        
        if any(re.search(pattern, text) for pattern in close_patterns):
            return SignalType.CLOSURE
        
        # Pending order patterns
        pending_patterns = [
            r'BUY\s+LIMIT', r'SELL\s+LIMIT', r'BUY\s+STOP', r'SELL\s+STOP',
            r'LIMIT', r'STOP', r'PENDING'
        ]
        
        if any(re.search(pattern, text) for pattern in pending_patterns):
            return SignalType.PENDING_ORDER
        
        return SignalType.MARKET_ORDER
    
    def _parse_trading_signal(self, text: str, signal_id: str, signal_type: SignalType) -> ParsedSignal:
        """Parse market or pending order signal"""
        parsed = ParsedSignal(
            signal_id=signal_id,
            original_text=text,
            signal_type=signal_type,
            confidence=ParseConfidence.MEDIUM
        )
        
        # Extract currency pair
        parsed.pair = self._extract_currency_pair(text)
        if not parsed.pair:
            parsed.confidence = ParseConfidence.LOW
        
        # Extract action (BUY/SELL)
        parsed.action = self._extract_action(text)
        if not parsed.action:
            parsed.confidence = ParseConfidence.LOW
        
        # Extract order type for pending orders
        if signal_type == SignalType.PENDING_ORDER:
            parsed.order_type = self._extract_order_type(text)
        
        # Extract prices
        prices = self._extract_prices(text)
        
        # Entry price
        parsed.entry_price = self._identify_entry_price(text, prices, parsed.action)
        
        # Stop Loss
        parsed.stop_loss = self._identify_stop_loss(text, prices)
        
        # Take Profits
        parsed.take_profits = self._identify_take_profits(text, prices)
        
        # Lot size and risk
        parsed.lot_size = self._extract_lot_size(text)
        parsed.risk_percent = self._extract_risk_percent(text)
        
        # Validate required fields
        required_fields = [parsed.pair, parsed.action, parsed.entry_price]
        if all(field is not None for field in required_fields):
            parsed.confidence = ParseConfidence.HIGH
        elif any(field is not None for field in required_fields):
            parsed.confidence = ParseConfidence.MEDIUM
        else:
            parsed.confidence = ParseConfidence.INVALID
        
        return parsed
    
    def _parse_modification_signal(self, text: str, signal_id: str) -> ParsedSignal:
        """Parse signal modification"""
        return ParsedSignal(
            signal_id=signal_id,
            original_text=text,
            signal_type=SignalType.MODIFICATION,
            confidence=ParseConfidence.MEDIUM,
            modification_type=self._extract_modification_type(text)
        )
    
    def _parse_closure_signal(self, text: str, signal_id: str) -> ParsedSignal:
        """Parse signal closure"""
        return ParsedSignal(
            signal_id=signal_id,
            original_text=text,
            signal_type=SignalType.CLOSURE,
            confidence=ParseConfidence.MEDIUM
        )
    
    def _parse_command_signal(self, text: str, signal_id: str) -> ParsedSignal:
        """Parse provider command"""
        return ParsedSignal(
            signal_id=signal_id,
            original_text=text,
            signal_type=SignalType.COMMAND,
            confidence=ParseConfidence.HIGH,
            modification_type=text.strip()
        )
    
    def _extract_currency_pair(self, text: str) -> Optional[str]:
        """Extract currency pair from text"""
        for pair in self.currency_pairs:
            if pair in text:
                return pair
        
        # Try pattern matching for common formats
        pair_patterns = [
            r'([A-Z]{3}[A-Z]{3})',
            r'([A-Z]{3}\/[A-Z]{3})',
            r'([A-Z]{3}\-[A-Z]{3})'
        ]
        
        for pattern in pair_patterns:
            match = re.search(pattern, text)
            if match:
                pair = match.group(1).replace('/', '').replace('-', '')
                if len(pair) == 6 and pair in self.currency_pairs:
                    return pair
        
        return None
    
    def _extract_action(self, text: str) -> Optional[str]:
        """Extract BUY/SELL action"""
        if re.search(r'\bBUY\b', text):
            return "BUY"
        elif re.search(r'\bSELL\b', text):
            return "SELL"
        return None
    
    def _extract_order_type(self, text: str) -> Optional[str]:
        """Extract order type for pending orders"""
        order_types = ["BUY_LIMIT", "SELL_LIMIT", "BUY_STOP", "SELL_STOP"]
        
        for order_type in order_types:
            if order_type.replace('_', ' ') in text:
                return order_type
        
        return None
    
    def _extract_prices(self, text: str) -> List[float]:
        """Extract all numeric prices from text"""
        # Pattern for price detection (handles various formats)
        price_patterns = [
            r'(\d+\.\d{2,5})',  # Standard price format
            r'(\d+\.\d{1,2})',  # Short price format
            r'(\d{3,6}\.?\d*)'  # JPY and other formats
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    price = float(match)
                    if 0.0001 < price < 1000000:  # Reasonable price range
                        prices.append(price)
                except ValueError:
                    continue
        
        return sorted(set(prices))  # Remove duplicates and sort
    
    def _identify_entry_price(self, text: str, prices: List[float], action: str) -> Optional[float]:
        """Identify entry price from extracted prices"""
        if not prices:
            return None
        
        # Look for explicit entry indicators
        entry_patterns = [
            r'ENTRY[:\s]*(\d+\.\d+)',
            r'ENTER[:\s]*(\d+\.\d+)',
            r'@[:\s]*(\d+\.\d+)',
            r'AT[:\s]*(\d+\.\d+)'
        ]
        
        for pattern in entry_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        # If no explicit entry, use first price or market price indicator
        if "MARKET" in text or "NOW" in text:
            return None  # Market execution
        
        return prices[0] if prices else None
    
    def _identify_stop_loss(self, text: str, prices: List[float]) -> Optional[float]:
        """Identify stop loss from extracted prices"""
        sl_patterns = [
            r'SL[:\s]*(\d+\.\d+)',
            r'STOP\s*LOSS[:\s]*(\d+\.\d+)',
            r'STOP[:\s]*(\d+\.\d+)'
        ]
        
        for pattern in sl_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _identify_take_profits(self, text: str, prices: List[float]) -> List[float]:
        """Identify take profit levels from extracted prices"""
        take_profits = []
        
        # Look for explicit TP indicators
        tp_patterns = [
            r'TP\s*1?[:\s]*(\d+\.\d+)',
            r'TP\s*2[:\s]*(\d+\.\d+)',
            r'TP\s*3[:\s]*(\d+\.\d+)',
            r'TP\s*4[:\s]*(\d+\.\d+)',
            r'TP\s*5[:\s]*(\d+\.\d+)',
            r'TAKE\s*PROFIT[:\s]*(\d+\.\d+)',
            r'TARGET[:\s]*(\d+\.\d+)'
        ]
        
        for pattern in tp_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    tp = float(match)
                    if tp not in take_profits:
                        take_profits.append(tp)
                except ValueError:
                    continue
        
        return sorted(take_profits)
    
    def _extract_lot_size(self, text: str) -> Optional[float]:
        """Extract lot size from text"""
        lot_patterns = [
            r'(\d+\.?\d*)\s*LOT',
            r'LOT[:\s]*(\d+\.?\d*)',
            r'SIZE[:\s]*(\d+\.?\d*)'
        ]
        
        for pattern in lot_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_risk_percent(self, text: str) -> Optional[float]:
        """Extract risk percentage from text"""
        risk_patterns = [
            r'RISK[:\s]*(\d+\.?\d*)%',
            r'(\d+\.?\d*)%\s*RISK'
        ]
        
        for pattern in risk_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_modification_type(self, text: str) -> str:
        """Extract type of modification"""
        if "TP" in text:
            return "MODIFY_TP"
        elif "SL" in text:
            return "MODIFY_SL"
        elif "ENTRY" in text:
            return "MODIFY_ENTRY"
        else:
            return "GENERAL_MODIFICATION"
    
    def _store_parse_history(self, message_id: str, parsed: ParsedSignal):
        """Store parse result for edit tracking"""
        self.parse_history[message_id] = parsed
    
    def _detect_changes(self, original: ParsedSignal, updated: ParsedSignal) -> Dict[str, Any]:
        """Detect changes between original and updated signals"""
        changes = {}
        
        fields_to_check = [
            'pair', 'action', 'entry_price', 'stop_loss', 'take_profits',
            'lot_size', 'risk_percent', 'order_type'
        ]
        
        for field in fields_to_check:
            original_value = getattr(original, field)
            updated_value = getattr(updated, field)
            
            if original_value != updated_value:
                changes[field] = {
                    'from': original_value,
                    'to': updated_value
                }
        
        return changes
    
    def _learn_provider_patterns(self, provider_id: str, text: str, parsed: ParsedSignal):
        """Learn and adapt to provider's signal patterns"""
        if provider_id not in self.provider_patterns:
            self.provider_patterns[provider_id] = {
                'successful_parses': 0,
                'common_formats': [],
                'confidence_scores': []
            }
        
        provider_data = self.provider_patterns[provider_id]
        
        if parsed.confidence in [ParseConfidence.HIGH, ParseConfidence.MEDIUM]:
            provider_data['successful_parses'] += 1
            provider_data['confidence_scores'].append(parsed.confidence.value)
            
            # Store text patterns for learning
            if len(provider_data['common_formats']) < 10:
                provider_data['common_formats'].append({
                    'text_length': len(text),
                    'has_pair': parsed.pair is not None,
                    'has_entry': parsed.entry_price is not None,
                    'has_sl': parsed.stop_loss is not None,
                    'tp_count': len(parsed.take_profits),
                    'sample_text': text[:50]  # First 50 chars for pattern recognition
                })
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Initialize parsing patterns"""
        return {
            'entry_patterns': [
                r'ENTRY[:\s]*(\d+\.\d+)',
                r'ENTER[:\s]*(\d+\.\d+)',
                r'@[:\s]*(\d+\.\d+)',
                r'AT[:\s]*(\d+\.\d+)'
            ],
            'sl_patterns': [
                r'SL[:\s]*(\d+\.\d+)',
                r'STOP\s*LOSS[:\s]*(\d+\.\d+)',
                r'STOP[:\s]*(\d+\.\d+)'
            ],
            'tp_patterns': [
                r'TP\s*(\d*)[:\s]*(\d+\.\d+)',
                r'TAKE\s*PROFIT[:\s]*(\d+\.\d+)',
                r'TARGET[:\s]*(\d+\.\d+)'
            ]
        }
    
    def _initialize_currency_pairs(self) -> List[str]:
        """Initialize supported currency pairs"""
        majors = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD'
        ]
        
        minors = [
            'EURJPY', 'EURGBP', 'EURCHF', 'EURAUD', 'EURCAD', 'EURNZD',
            'GBPJPY', 'GBPCHF', 'GBPAUD', 'GBPCAD', 'GBPNZD',
            'AUDJPY', 'AUDCHF', 'AUDCAD', 'AUDNZD',
            'CADJPY', 'CADCHF', 'NZDJPY', 'NZDCHF', 'NZDCAD',
            'CHFJPY'
        ]
        
        exotics = [
            'USDZAR', 'USDTRY', 'USDMXN', 'USDHKD', 'USDSGD',
            'EURPLN', 'EURTRY', 'EURZAR', 'GBPTRY', 'GBPZAR'
        ]
        
        return majors + minors + exotics
    
    def get_parse_statistics(self, provider_id: str = None) -> Dict[str, Any]:
        """Get parsing statistics"""
        if provider_id and provider_id in self.provider_patterns:
            return self.provider_patterns[provider_id]
        
        total_parses = len(self.parse_history)
        successful_parses = len([p for p in self.parse_history.values() 
                               if p.confidence != ParseConfidence.INVALID])
        
        return {
            'total_parses': total_parses,
            'successful_parses': successful_parses,
            'success_rate': (successful_parses / total_parses * 100) if total_parses > 0 else 0,
            'providers_learned': len(self.provider_patterns)
        }