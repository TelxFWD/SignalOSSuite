# SignalOS Installation and Setup Guide

## Prerequisites
- Windows 10/11 (64-bit)
- MetaTrader 5 installed
- Python 3.11+ (for development)
- Minimum 4GB RAM, 2GB free disk space

## Quick Start Setup

### 1. Telegram Configuration
1. Obtain API credentials from https://my.telegram.org
2. Enter API ID and API Hash in settings
3. Add target channel usernames/IDs
4. Test connection and authorization

### 2. MetaTrader 5 Integration
1. Install SignalOS EA (automatic detection)
2. Configure terminal path if not auto-detected
3. Set up login credentials
4. Test file communication

### 3. Signal Parser Setup
1. Choose confidence threshold (0.8 recommended)
2. Enable OCR for image signals (optional)
3. Configure buffer pips for SL adjustment
4. Test with sample signals

### 4. Execution Settings
1. Set maximum risk percentage per trade
2. Configure stealth mode options
3. Set delay between executions
4. Enable/disable automatic trading

## Troubleshooting

### Common Issues
- **Telegram connection fails**: Check API credentials and network
- **MT5 not detected**: Verify installation path and permissions
- **Signals not parsing**: Lower confidence threshold or check format
- **EA not responding**: Check file permissions and heartbeat

### Log Files
- Main log: ~/.signalos/logs/signalos_YYYYMMDD.log
- Signal log: ~/.signalos/logs/signals.log
- Trade log: ~/.signalos/logs/trades.log
- Error log: ~/.signalos/logs/errors_YYYYMMDD.log

### Support
- Documentation: https://docs.signalos.io
- Community: https://community.signalos.io
- Support: support@signalos.io