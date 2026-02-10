"""
PnakoticBot - Simplified version for debugging
"""

import os
import logging
from flask import Flask

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=os.getenv('LOG_LEVEL', 'INFO')
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'bot': 'PnakoticBot', 'version': '1.0.0-simple'}, 200

@app.route('/')
def index():
    """Root endpoint"""
    return {
        'bot': 'PnakoticBot',
        'version': '1.0.0-simple',
        'status': 'running',
        'description': 'Simplified version - checking if Flask works'
    }, 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook receiver - placeholder"""
    logger.info("Webhook received")
    return {'status': 'received'}, 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
