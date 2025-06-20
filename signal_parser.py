"""
SignalOS Signal Parser
Advanced signal parsing with Gold/XAU support and normalization
"""
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from models import Signal, db
from app import app

class SignalParser:
    """Advanced signal parser with comprehensive forex pair detection"""
    
    def __init__(self):
        # Forex pair synonyms and variations
        self.pair_synonyms = {
            'GOLD': ['GOLD', 'XAU', 'XAUUSD', 'GOLD/USD', 'XAU/USD', 'GOLDSPOT'],
            'EURUSD': ['EURUSD', 'EUR/USD', 'EU', 'EURO'],
            'GBPUSD': ['GBPUSD', 'GBP/USD', 'GU', 'CABLE', 'POUND'],
            'USDJPY': ['USDJPY', 'USD/JPY', 'UJ', 'YEN'],
            'USDCHF': ['USDCHF', 'USD/CHF', 'UC', 'SWISSY'],
            'USDCAD': ['USDCAD', 'USD/CAD', 'LOONIE'],
            'AUDUSD': ['AUDUSD', 'AUD/USD', 'AU', 'AUSSIE'],
            'NZDUSD': ['NZDUSD', 'NZD/USD', 'NU', 'KIWI'],
            'EURGBP': ['EURGBP', 'EUR/GBP', 'EG'],
            'EURJPY': ['EURJPY', 'EUR/JPY', 'EJ'],
            'GBPJPY': ['GBPJPY', 'GBP/JPY', 'GJ'],
            'SILVER': ['SILVER', 'XAG', 'XAGUSD', 'SILVER/USD'],
            'OIL': ['OIL', 'CRUDE', 'WTI', 'BRENT', 'USOIL'],
            'BITCOIN': ['BITCOIN', 'BTC', 'BTCUSD', 'BTC/USD'],
            'ETHEREUM': ['ETHEREUM', 'ETH', 'ETHUSD', 'ETH/USD']
        }
        
        # Action keywords
        self.action_keywords = {
            'BUY': ['BUY', 'LONG', 'BULL', 'PURCHASE', 'ENTRY LONG', 'GO LONG'],
            'SELL': ['SELL', 'SHORT', 'BEAR', 'ENTRY SHORT', 'GO SHORT']
        }
        
        # Price level keywords
        self.price_keywords = {
            'ENTRY': ['ENTRY', 'ENTER', 'PRICE', 'AT', '@'],
            'STOP_LOSS': ['SL', 'STOP LOSS', 'STOPLOSS', 'STOP', 'LOSS'],
            'TAKE_PROFIT': ['TP', 'TAKE PROFIT', 'TAKEPROFIT', 'TARGET', 'PROFIT']
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize input text for better parsing"""
        if not text:
            return ""
        
        # Convert to uppercase
        text = text.upper()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Normalize common separators
        text = re.sub(r'[:\-=→]', ' ', text)
        
        # Remove special characters but keep numbers and basic punctuation
        text = re.sub(r'[^\w\s\.\,\/]', ' ', text)
        
        return text
    
    def detect_forex_pair(self, text: str) -> Optional[str]:
        """Detect forex pair from text using synonyms"""
        normalized_text = self.normalize_text(text)
        
        for standard_pair, synonyms in self.pair_synonyms.items():
            for synonym in synonyms:
                # Check for exact word match or as part of compound words
                if re.search(r'\b' + re.escape(synonym) + r'\b', normalized_text):
                    return standard_pair
        
        return None
    
    def detect_action(self, text: str) -> Optional[str]:
        """Detect trading action (BUY/SELL)"""
        normalized_text = self.normalize_text(text)
        
        for action, keywords in self.action_keywords.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', normalized_text):
                    return action
        
        return None
    
    def extract_price_levels(self, text: str) -> Dict[str, Optional[float]]:
        """Extract entry, stop loss, and take profit levels"""
        normalized_text = self.normalize_text(text)
        price_levels = {'entry': None, 'stop_loss': None, 'take_profit': None}
        
        # Find all numbers that could be prices
        price_pattern = r'\b\d+\.?\d*\b'
        numbers = re.findall(price_pattern, normalized_text)
        
        # Try to match prices to keywords
        for level_type, keywords in self.price_keywords.items():
            for keyword in keywords:
                # Look for keyword followed by a price
                pattern = r'\b' + re.escape(keyword) + r'\s*:?\s*(\d+\.?\d*)'
                match = re.search(pattern, normalized_text)
                if match:
                    price = float(match.group(1))
                    if level_type == 'ENTRY':
                        price_levels['entry'] = price
                    elif level_type == 'STOP_LOSS':
                        price_levels['stop_loss'] = price
                    elif level_type == 'TAKE_PROFIT':
                        price_levels['take_profit'] = price
        
        # If no explicit keywords found, try positional parsing
        if not any(price_levels.values()) and len(numbers) >= 2:
            try:
                # Common format: "GOLD Long Entry: 1980 SL: 1975 TP: 1990"
                if len(numbers) >= 3:
                    price_levels['entry'] = float(numbers[0])
                    price_levels['stop_loss'] = float(numbers[1])
                    price_levels['take_profit'] = float(numbers[2])
                elif len(numbers) == 2:
                    price_levels['entry'] = float(numbers[0])
                    price_levels['stop_loss'] = float(numbers[1])
            except (ValueError, IndexError):
                pass
        
        return price_levels
    
    def calculate_confidence(self, parsed_data: Dict) -> float:
        """Calculate confidence score for parsed signal"""
        confidence = 0.0
        
        # Base confidence for having required fields
        if parsed_data.get('pair'):
            confidence += 0.3
        if parsed_data.get('action'):
            confidence += 0.3
        if parsed_data.get('entry_price'):
            confidence += 0.2
        
        # Additional confidence for optional fields
        if parsed_data.get('stop_loss'):
            confidence += 0.1
        if parsed_data.get('take_profit'):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def parse_signal(self, signal_text: str) -> Dict:
        """Main parsing function"""
        if not signal_text:
            return {'error': 'Empty signal text'}
        
        try:
            # Normalize text
            normalized_text = self.normalize_text(signal_text)
            
            # Extract components
            pair = self.detect_forex_pair(normalized_text)
            action = self.detect_action(normalized_text)
            price_levels = self.extract_price_levels(normalized_text)
            
            # Build result
            parsed_data = {
                'pair': pair,
                'action': action,
                'entry_price': price_levels.get('entry'),
                'stop_loss': price_levels.get('stop_loss'),
                'take_profit': price_levels.get('take_profit'),
                'raw_text': signal_text,
                'normalized_text': normalized_text,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Calculate confidence
            parsed_data['confidence'] = self.calculate_confidence(parsed_data)
            
            # Validate minimum requirements
            if not pair or not action:
                parsed_data['status'] = 'INVALID'
                parsed_data['error'] = f"Missing required fields - Pair: {pair}, Action: {action}"
            else:
                parsed_data['status'] = 'VALID'
            
            return parsed_data
            
        except Exception as e:
            return {
                'error': f'Parsing error: {str(e)}',
                'status': 'ERROR',
                'raw_text': signal_text
            }
    
    def save_signal(self, parsed_data: Dict) -> Optional[int]:
        """Save parsed signal to database"""
        try:
            with app.app_context():
                signal = Signal(
                    raw_text=parsed_data.get('raw_text', ''),
                    parsed_pair=parsed_data.get('pair'),
                    parsed_action=parsed_data.get('action'),
                    entry_price=parsed_data.get('entry_price'),
                    stop_loss=parsed_data.get('stop_loss'),
                    take_profit=parsed_data.get('take_profit'),
                    confidence_score=parsed_data.get('confidence', 0.0),
                    status=parsed_data.get('status', 'PENDING'),
                    received_at=datetime.utcnow()
                )
                
                db.session.add(signal)
                db.session.commit()
                return signal.id
                
        except Exception as e:
            print(f"Error saving signal: {e}")
            return None


# Test function for Gold/XAU parsing
def test_gold_parsing():
    """Test Gold/XAU signal parsing"""
    parser = SignalParser()
    
    test_signals = [
        "Gold Long Entry: 1980 SL: 1975 TP: 1990",
        "XAUUSD BUY @ 1985.50 Stop: 1980 Target: 1995",
        "GOLD SHORT at 2000, SL 2005, TP 1990",
        "XAU/USD SELL Entry 1975 Stop Loss 1980 Take Profit 1960"
    ]
    
    print("\n=== Gold/XAU Parsing Test ===")
    for i, signal in enumerate(test_signals, 1):
        result = parser.parse_signal(signal)
        print(f"\nTest {i}: {signal}")
        print(f"Result: {json.dumps(result, indent=2)}")
    
    return True


if __name__ == "__main__":
    test_gold_parsing()