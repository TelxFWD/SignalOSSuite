"""
WSGI entry point for SignalOS with proper eventlet initialization
Fixes WebSocket timeout issues for production deployment
"""

import eventlet
eventlet.monkey_patch()

from main import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)