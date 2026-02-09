"""
PnakoticBot - Sorcery Card Telegram Bot
Entry point combining Flask web server + Telegram bot webhook
"""

import os
import asyncio
import logging
from flask import Flask, request, Response
from telegram import Update
from bot.telegram_bot import setup_bot
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=os.getenv('LOG_LEVEL', 'INFO')
)
logger = logging.getLogger(__name__)

# Flask app for Render health checks
app = Flask(__name__)

# Global bot application
bot_application = None


@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return {'status': 'ok', 'bot': 'PnakoticBot', 'version': '1.0.0'}, 200


@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook receiver"""
    try:
        update = Update.de_json(request.get_json(force=True), bot_application.bot)
        # Process update asynchronously in a new event loop
        asyncio.run(bot_application.process_update(update))
        return Response(status=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return Response(status=500)


@app.route('/')
def index():
    """Root endpoint"""
    return {
        'bot': 'PnakoticBot',
        'version': '1.0.0',
        'status': 'running',
        'description': 'Sorcery: Contested Realm card bot for Telegram',
        'source': 'https://curiosa.io'
    }, 200


def main():
    """Main entry point"""
    global bot_application
    
    try:
        # Setup Telegram bot
        logger.info("Setting up PnakoticBot...")
        bot_application = setup_bot()
        
        # Get configuration
        webhook_url = os.getenv('WEBHOOK_URL')
        port = int(os.getenv('PORT', 10000))
        
        if not webhook_url:
            raise ValueError("WEBHOOK_URL environment variable not set")
        
        # Set webhook
        logger.info(f"Setting webhook to {webhook_url}")
        asyncio.get_event_loop().run_until_complete(
            bot_application.bot.set_webhook(url=webhook_url)
        )
        
        logger.info(f"Starting Flask server on port {port}")
        logger.info("PnakoticBot is ready to receive messages!")
        
        # Run Flask app
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
