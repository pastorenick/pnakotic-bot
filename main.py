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
_bot_initialized = False


async def init_bot_async():
    """Initialize bot application asynchronously"""
    global bot_application, _bot_initialized
    
    if _bot_initialized:
        return bot_application
    
    logger.info("Initializing PnakoticBot...")
    
    # Check required environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    if not webhook_url:
        raise ValueError("WEBHOOK_URL environment variable not set")
    
    # Setup bot
    bot_application = setup_bot()
    
    # Initialize the application (required before processing updates)
    await bot_application.initialize()
    
    # Set webhook
    logger.info(f"Setting webhook to {webhook_url}")
    await bot_application.bot.set_webhook(url=webhook_url)
    
    _bot_initialized = True
    logger.info("PnakoticBot initialized successfully!")
    return bot_application


def init_bot():
    """Synchronous wrapper for bot initialization"""
    return asyncio.run(init_bot_async())


@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return {'status': 'ok', 'bot': 'PnakoticBot', 'version': '1.0.0'}, 200


@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook receiver"""
    global bot_application
    
    try:
        # Lazy initialization on first webhook
        if not _bot_initialized:
            init_bot()
        
        # Parse update
        update = Update.de_json(request.get_json(force=True), bot_application.bot)
        
        # Process update asynchronously
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
    """Main entry point for local development"""
    global bot_application
    
    # Initialize bot if not already done
    if bot_application is None:
        init_bot()
    
    # Get port configuration
    port = int(os.getenv('PORT', 10000))
    
    logger.info(f"Starting Flask server on port {port}")
    logger.info("PnakoticBot is ready to receive messages!")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    main()
