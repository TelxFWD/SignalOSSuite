"""
Utility functions and helpers
"""

import re
import json
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import time
import functools

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename

def format_currency_pair(pair: str) -> str:
    """Format currency pair to standard format"""
    if not pair:
        return ""
    
    # Remove separators and convert to uppercase
    clean_pair = re.sub(r'[\/\-\s]', '', pair.upper())
    
    # Validate length
    if len(clean_pair) != 6:
        return pair  # Return original if invalid
    
    return clean_pair

def calculate_pip_value(pair: str, lot_size: float = 1.0) -> float:
    """Calculate pip value for a currency pair"""
    # Simplified pip value calculation
    # In a real implementation, this would consider account currency and current rates
    
    if pair.endswith('JPY'):
        # JPY pairs have different pip calculation
        return lot_size * 1000  # Simplified
    else:
        return lot_size * 10  # Simplified

def price_to_pips(price1: float, price2: float, pair: str) -> float:
    """Calculate pip difference between two prices"""
    price_diff = abs(price1 - price2)
    
    if pair.endswith('JPY'):
        # JPY pairs: 1 pip = 0.01
        return price_diff * 100
    else:
        # Most pairs: 1 pip = 0.0001
        return price_diff * 10000

def pips_to_price(pips: float, pair: str) -> float:
    """Convert pips to price difference"""
    if pair.endswith('JPY'):
        return pips / 100
    else:
        return pips / 10000

def format_price(price: float, pair: str) -> str:
    """Format price according to currency pair precision"""
    if pair.endswith('JPY'):
        return f"{price:.3f}"
    else:
        return f"{price:.5f}"

def validate_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Check if it's a reasonable length
    return 10 <= len(digits) <= 15

def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """Hash a string using specified algorithm"""
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()

def generate_unique_id() -> str:
    """Generate a unique identifier"""
    timestamp = int(time.time() * 1000)
    return f"{timestamp}"

def safe_json_load(file_path: Union[str, Path], default: Any = None) -> Any:
    """Safely load JSON file with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def safe_json_save(data: Any, file_path: Union[str, Path]) -> bool:
    """Safely save data as JSON"""
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on failure"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    continue
            
            raise last_exception
        return wrapper
    return decorator

def format_timestamp(dt: datetime, format_type: str = 'default') -> str:
    """Format timestamp according to specified type"""
    formats = {
        'default': '%Y-%m-%d %H:%M:%S',
        'iso': '%Y-%m-%dT%H:%M:%S',
        'filename': '%Y%m%d_%H%M%S',
        'display': '%d/%m/%Y %H:%M',
        'time_only': '%H:%M:%S',
        'date_only': '%Y-%m-%d'
    }
    
    format_str = formats.get(format_type, formats['default'])
    return dt.strftime(format_str)

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp string to datetime object"""
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%d/%m/%Y %H:%M',
        '%Y%m%d_%H%M%S'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    return None

def clean_text_for_parsing(text: str) -> str:
    """Clean text for signal parsing"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common noise characters
    text = re.sub(r'[📈📉🚀💰🔥⚡️✨🎯]', '', text)
    
    # Normalize currency pair separators
    text = re.sub(r'([A-Z]{3})[\/\-\s]([A-Z]{3})', r'\1\2', text)
    
    return text

def extract_numbers(text: str) -> List[float]:
    """Extract all numbers from text"""
    pattern = r'\d+\.?\d*'
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        try:
            numbers.append(float(match))
        except ValueError:
            continue
    
    return numbers

def is_valid_price(price: float, pair: str) -> bool:
    """Validate if price is reasonable for currency pair"""
    if price <= 0:
        return False
    
    # Basic sanity checks for major pairs
    price_ranges = {
        'EURUSD': (0.8, 1.5),
        'GBPUSD': (1.0, 2.0),
        'USDJPY': (80, 160),
        'USDCHF': (0.7, 1.2),
        'AUDUSD': (0.5, 1.2),
        'USDCAD': (1.0, 1.6),
        'NZDUSD': (0.4, 1.0)
    }
    
    if pair in price_ranges:
        min_price, max_price = price_ranges[pair]
        return min_price <= price <= max_price
    
    # For other pairs, just check if it's positive and reasonable
    return 0.001 <= price <= 10000

def calculate_lot_size_for_risk(
    balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss: float,
    pair: str
) -> float:
    """Calculate appropriate lot size based on risk parameters"""
    if not all([balance, risk_percent, entry_price, stop_loss]) or balance <= 0:
        return 0.01  # Minimum lot size
    
    # Calculate risk amount
    risk_amount = balance * (risk_percent / 100)
    
    # Calculate pip distance
    pip_distance = price_to_pips(entry_price, stop_loss, pair)
    
    if pip_distance <= 0:
        return 0.01
    
    # Calculate pip value per lot
    pip_value_per_lot = calculate_pip_value(pair, 1.0)
    
    # Calculate lot size
    lot_size = risk_amount / (pip_distance * pip_value_per_lot)
    
    # Round to reasonable precision and apply limits
    lot_size = round(lot_size, 2)
    return max(0.01, min(10.0, lot_size))  # Limit between 0.01 and 10 lots

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get file size in megabytes"""
    try:
        size_bytes = Path(file_path).stat().st_size
        return size_bytes / (1024 * 1024)
    except:
        return 0.0

def create_backup_filename(original_name: str, timestamp: datetime = None) -> str:
    """Create backup filename with timestamp"""
    if timestamp is None:
        timestamp = datetime.now()
    
    path = Path(original_name)
    timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
    
    return f"{path.stem}_backup_{timestamp_str}{path.suffix}"

def is_market_open(pair: str = 'EURUSD') -> bool:
    """Check if market is open (simplified check)"""
    # This is a very simplified check
    # In a real implementation, you'd consider market hours for different sessions
    now = datetime.now()
    
    # Check if it's weekend
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Very basic check - assume market is open on weekdays
    return True

def normalize_action(action: str) -> Optional[str]:
    """Normalize trading action to standard format"""
    if not action:
        return None
    
    action = action.upper().strip()
    
    buy_terms = ['BUY', 'LONG', 'CALL', 'B']
    sell_terms = ['SELL', 'SHORT', 'PUT', 'S']
    
    if action in buy_terms:
        return 'BUY'
    elif action in sell_terms:
        return 'SELL'
    
    return None

class TimeoutError(Exception):
    """Custom timeout exception"""
    pass

def timeout(seconds: float):
    """Decorator to add timeout to function execution"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            # Set up the timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Clean up
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        return wrapper
    return decorator

def memory_usage_mb() -> float:
    """Get current memory usage in MB"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except:
        return 0.0

def disk_usage_gb(path: Union[str, Path]) -> Dict[str, float]:
    """Get disk usage information in GB"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        return {
            'total': total / (1024**3),
            'used': used / (1024**3),
            'free': free / (1024**3),
            'percent_used': (used / total) * 100
        }
    except:
        return {'total': 0, 'used': 0, 'free': 0, 'percent_used': 0}
