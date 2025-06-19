"""
AI-powered signal parser for extracting trading information from text and images
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

try:
    import spacy
    from spacy.lang.en import English
except ImportError:
    spacy = None
    English = None

try:
    import easyocr
except ImportError:
    easyocr = None

from config.settings import settings
from models.signal_model import RawSignal, ParsedSignal
from core.logger import get_logger

logger = get_logger(__name__)

class SignalParser:
    """AI-powered signal parser for Forex signals"""
    
    def __init__(self):
        self.nlp = None
        self.ocr_reader = None
        self.currency_pairs = self._load_currency_pairs()
        self.action_keywords = self._load_action_keywords()
        self.fallback_patterns = self._load_fallback_patterns()
        
        # Initialize NLP model
        self.initialize_nlp()
        
        # Initialize OCR if enabled
        if settings.parser.ocr_enabled:
            self.initialize_ocr()
    
    def initialize_nlp(self) -> bool:
        """Initialize spaCy NLP model"""
        try:
            if not spacy:
                logger.error("spaCy library not available")
                return False
            
            # Try to load the specified model
            try:
                self.nlp = spacy.load(settings.parser.model_name)
                logger.info(f"Loaded spaCy model: {settings.parser.model_name}")
                return True
            except OSError:
                # Fallback to basic English model
                try:
                    self.nlp = English()
                    logger.warning(f"Model {settings.parser.model_name} not found, using basic English")
                    return True
                except Exception as e:
                    logger.error(f"Failed to load any spaCy model: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error initializing NLP: {e}")
            return False
    
    def initialize_ocr(self) -> bool:
        """Initialize OCR reader"""
        try:
            if not easyocr:
                logger.error("EasyOCR library not available")
                return False
            
            # Initialize EasyOCR with English language
            self.ocr_reader = easyocr.Reader(['en'])
            logger.info("OCR reader initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing OCR: {e}")
            return False
    
    def parse_signal(self, raw_signal: RawSignal) -> Optional[ParsedSignal]:
        """Parse a raw signal into structured data"""
        try:
            # Start with text parsing
            parsed_data = self.parse_text(raw_signal.text)
            
            # If OCR is enabled and media is available, try OCR parsing
            if (settings.parser.ocr_enabled and raw_signal.media_path and 
                raw_signal.has_media and self.ocr_reader):
                ocr_data = self.parse_image(raw_signal.media_path)
                if ocr_data:
                    # Merge OCR data with text data
                    parsed_data = self.merge_parsed_data(parsed_data, ocr_data)
            
            # Apply fallback rules if enabled and confidence is low
            if (settings.parser.fallback_rules and 
                parsed_data.get('confidence', 0) < settings.parser.confidence_threshold):
                fallback_data = self.apply_fallback_rules(raw_signal.text)
                if fallback_data:
                    parsed_data = self.merge_parsed_data(parsed_data, fallback_data)
            
            # Validate and create ParsedSignal
            if self.validate_parsed_data(parsed_data):
                return ParsedSignal(
                    raw_signal_id=raw_signal.message_id,
                    pair=parsed_data.get('pair'),
                    action=parsed_data.get('action'),
                    entry_price=parsed_data.get('entry_price'),
                    stop_loss=parsed_data.get('stop_loss'),
                    take_profit=parsed_data.get('take_profit'),
                    lot_size=parsed_data.get('lot_size'),
                    confidence=parsed_data.get('confidence', 0),
                    parsed_at=datetime.now(),
                    metadata=parsed_data.get('metadata', {})
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing signal: {e}")
            return None
    
    def parse_text(self, text: str) -> Dict[str, Any]:
        """Parse text using NLP and regex patterns"""
        try:
            if not text or not text.strip():
                return {}
            
            # Clean and normalize text
            cleaned_text = self.clean_text(text)
            
            # Initialize result
            result = {
                'confidence': 0.0,
                'metadata': {
                    'original_text': text,
                    'cleaned_text': cleaned_text
                }
            }
            
            # Extract currency pair
            pair = self.extract_currency_pair(cleaned_text)
            if pair:
                result['pair'] = pair
                result['confidence'] += 0.3
            
            # Extract action (BUY/SELL)
            action = self.extract_action(cleaned_text)
            if action:
                result['action'] = action
                result['confidence'] += 0.2
            
            # Extract prices
            prices = self.extract_prices(cleaned_text)
            if prices:
                result.update(prices)
                result['confidence'] += 0.3
            
            # Extract lot size
            lot_size = self.extract_lot_size(cleaned_text)
            if lot_size:
                result['lot_size'] = lot_size
                result['confidence'] += 0.1
            
            # NLP-based extraction if spaCy is available
            if self.nlp:
                nlp_data = self.extract_with_nlp(cleaned_text)
                if nlp_data:
                    result = self.merge_parsed_data(result, nlp_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing text: {e}")
            return {}
    
    def parse_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Parse signal from image using OCR"""
        try:
            if not self.ocr_reader or not Path(image_path).exists():
                return None
            
            # Read text from image
            results = self.ocr_reader.readtext(image_path)
            
            # Combine all detected text
            extracted_text = " ".join([result[1] for result in results if result[2] > 0.5])
            
            if extracted_text:
                logger.info(f"OCR extracted text: {extracted_text}")
                # Parse the extracted text
                return self.parse_text(extracted_text)
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing image: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove emoji and special characters
        cleaned = re.sub(r'[^\w\s\.\@\#\$\%\-\+\(\)\/]', ' ', cleaned)
        
        # Convert to uppercase for consistency
        cleaned = cleaned.upper()
        
        return cleaned
    
    def extract_currency_pair(self, text: str) -> Optional[str]:
        """Extract currency pair from text"""
        # Look for standard currency pair patterns
        patterns = [
            r'\b([A-Z]{3}[\/\-\s]?[A-Z]{3})\b',  # EURUSD, EUR/USD, EUR-USD
            r'\b([A-Z]{6})\b'  # EURUSD
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean the match
                pair = re.sub(r'[\/\-\s]', '', match)
                if len(pair) == 6 and pair in self.currency_pairs:
                    return pair
        
        return None
    
    def extract_action(self, text: str) -> Optional[str]:
        """Extract trading action (BUY/SELL) from text"""
        buy_keywords = ['BUY', 'LONG', 'CALL', 'BULLISH', 'UP']
        sell_keywords = ['SELL', 'SHORT', 'PUT', 'BEARISH', 'DOWN']
        
        text_upper = text.upper()
        
        # Check for action keywords
        for keyword in buy_keywords:
            if keyword in text_upper:
                return 'BUY'
        
        for keyword in sell_keywords:
            if keyword in text_upper:
                return 'SELL'
        
        return None
    
    def extract_prices(self, text: str) -> Dict[str, float]:
        """Extract entry, stop loss, and take profit prices"""
        prices = {}
        
        # Price patterns
        price_pattern = r'(\d+\.?\d*)'
        
        # Entry price patterns - enhanced for Gold/XAU formats
        entry_patterns = [
            r'(?:ENTRY|ENTER|PRICE|@)\s*:?\s*' + price_pattern,
            r'(?:BUY|SELL)\s+(?:AT|@)\s*' + price_pattern,
            r'(?:LONG|SHORT)\s+(?:ENTRY|POSITION)\s*:?\s*' + price_pattern,
            r'(?:GOLD|XAU)\s+(?:LONG|SHORT)\s+(?:ENTRY|POSITION)\s*:?\s*' + price_pattern,
            r'(?:GOLD|XAU|XAUUSD)\s+(?:BUY|SELL)\s+(?:AT|@)?\s*' + price_pattern,
            r'(?:GOLD|XAU)\s+(?:LONG|SHORT)?\s*(?:ENTRY)?\s*:?\s*' + price_pattern,
            r'(?:LONG|SHORT)\s+(?:ENTRY)\s*:?\s*' + price_pattern,
            r'(?:ENTRY)\s*:?\s*' + price_pattern
        ]
        
        for pattern in entry_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    prices['entry_price'] = float(matches[0])
                    break
                except ValueError:
                    continue
        
        # Stop Loss patterns
        sl_patterns = [
            r'(?:SL|STOP\s*LOSS|STOPLOSS)\s*:?\s*' + price_pattern,
            r'(?:STOP|SL)\s+(?:AT|@)\s*' + price_pattern
        ]
        
        for pattern in sl_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    prices['stop_loss'] = float(matches[0])
                    break
                except ValueError:
                    continue
        
        # Take Profit patterns
        tp_patterns = [
            r'(?:TP|TAKE\s*PROFIT|TAKEPROFIT|TARGET)\s*:?\s*' + price_pattern,
            r'(?:TP|TARGET)\s+(?:AT|@)\s*' + price_pattern
        ]
        
        for pattern in tp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    prices['take_profit'] = float(matches[0])
                    break
                except ValueError:
                    continue
        
        return prices
    
    def extract_lot_size(self, text: str) -> Optional[float]:
        """Extract lot size from text"""
        patterns = [
            r'(?:LOT|SIZE|VOLUME)\s*:?\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*(?:LOT|LOTS)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return float(matches[0])
                except ValueError:
                    continue
        
        return None
    
    def extract_with_nlp(self, text: str) -> Dict[str, Any]:
        """Extract information using NLP"""
        try:
            if not self.nlp:
                return {}
            
            doc = self.nlp(text)
            result = {}
            
            # Extract entities
            entities = {}
            for ent in doc.ents:
                entities[ent.label_] = ent.text
            
            if entities:
                result['entities'] = entities
            
            # Extract numbers and their context
            numbers = []
            for token in doc:
                if token.like_num:
                    numbers.append({
                        'value': token.text,
                        'context': ' '.join([t.text for t in token.sent])
                    })
            
            if numbers:
                result['numbers'] = numbers
            
            return result
            
        except Exception as e:
            logger.error(f"Error in NLP extraction: {e}")
            return {}
    
    def apply_fallback_rules(self, text: str) -> Dict[str, Any]:
        """Apply fallback regex patterns"""
        result = {}
        
        for rule in self.fallback_patterns:
            pattern = rule['pattern']
            field = rule['field']
            
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    if field in ['entry_price', 'stop_loss', 'take_profit', 'lot_size']:
                        result[field] = float(matches[0])
                    else:
                        result[field] = matches[0].upper()
                except (ValueError, IndexError):
                    continue
        
        if result:
            result['confidence'] = 0.4  # Lower confidence for fallback
        
        return result
    
    def merge_parsed_data(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two parsed data dictionaries"""
        result = data1.copy()
        
        for key, value in data2.items():
            if key not in result or not result[key]:
                result[key] = value
            elif key == 'confidence':
                # Average the confidence scores
                result[key] = (result[key] + value) / 2
            elif key == 'metadata':
                # Merge metadata
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata'].update(value)
        
        return result
    
    def validate_parsed_data(self, data: Dict[str, Any]) -> bool:
        """Validate parsed signal data"""
        # Check minimum requirements
        required_fields = ['pair', 'action']
        
        for field in required_fields:
            if not data.get(field):
                return False
        
        # Check confidence threshold
        confidence = data.get('confidence', 0)
        if confidence < settings.parser.confidence_threshold:
            return False
        
        # Validate currency pair
        pair = data.get('pair')
        if pair and pair not in self.currency_pairs:
            return False
        
        # Validate action
        action = data.get('action')
        if action and action not in ['BUY', 'SELL']:
            return False
        
        return True
    
    def _load_currency_pairs(self) -> List[str]:
        """Load supported currency pairs"""
        return [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
            'EURJPY', 'GBPJPY', 'EURGBP', 'AUDJPY', 'EURAUD', 'EURCHF', 'AUDNZD',
            'NZDJPY', 'GBPAUD', 'GBPCAD', 'EURNZD', 'AUDCAD', 'GBPCHF', 'AUDCHF',
            'EURCAD', 'CADJPY', 'GBPNZD', 'CADCHF', 'CHFJPY', 'NZDCAD', 'NZDCHF',
            'XAUUSD', 'XAGUSD', 'GOLD', 'SILVER', 'USOIL', 'BRENT'
        ]
    
    def _load_action_keywords(self) -> Dict[str, List[str]]:
        """Load action keywords"""
        return {
            'buy': ['BUY', 'LONG', 'CALL', 'BULLISH', 'UP', 'ASCENDING', 'ENTRY'],
            'sell': ['SELL', 'SHORT', 'PUT', 'BEARISH', 'DOWN', 'DESCENDING', 'POSITION']
        }
    
    def _load_fallback_patterns(self) -> List[Dict[str, str]]:
        """Load fallback regex patterns"""
        return [
            {'pattern': r'([A-Z]{6})', 'field': 'pair'},
            {'pattern': r'(BUY|SELL)', 'field': 'action'},
            {'pattern': r'(\d+\.\d+)', 'field': 'entry_price'},
            {'pattern': r'SL\s*(\d+\.\d+)', 'field': 'stop_loss'},
            {'pattern': r'TP\s*(\d+\.\d+)', 'field': 'take_profit'}
        ]
