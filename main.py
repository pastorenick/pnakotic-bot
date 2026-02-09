"""
PnakoticBot - Sorcery Card Telegram Bot
Entry point combining Flask web server + Telegram bot webhook
"""

import os
import asyncio
import logging
import threading
from concurrent.futures import Future
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

# Flask app
app = Flask(__name__)

# Global bot application and event loop
bot_application = None
_bot_initialized = False
_event_loop = None
_loop_thread = None


def start_background_loop(loop):
    """Run event loop in background thread"""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def run_coroutine_threadsafe(coro):
    """Run a coroutine in the background event loop"""
    global _event_loop
    if _event_loop is None:
        raise RuntimeError("Event loop not initialized")
    future = asyncio.run_coroutine_threadsafe(coro, _event_loop)
    return future.result(timeout=60)


async def init_bot_async():
    """Initialize bot application asynchronously"""
    global bot_application, _bot_initialized
    
    if _bot_initialized:
        return bot_application
    
    logger.info("Initializing PnakoticBot...")
    
    # Check required environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    # Setup bot
    bot_application = setup_bot()
    
    # Initialize the application (required before processing updates)
    await bot_application.initialize()
    
    # NOTE: Webhook is set manually via Telegram API due to DNS resolution issues
    # Don't set webhook here - it's managed externally
    
    _bot_initialized = True
    logger.info("PnakoticBot initialized successfully!")
    return bot_application


def init_bot():
    """Initialize bot and background event loop"""
    global _event_loop, _loop_thread
    
    if not _event_loop:
        # Create new event loop for background thread
        _event_loop = asyncio.new_event_loop()
        _loop_thread = threading.Thread(target=start_background_loop, args=(_event_loop,), daemon=True)
        _loop_thread.start()
        logger.info("Background event loop started")
    
    # Initialize bot in the background loop
    run_coroutine_threadsafe(init_bot_async())


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
        
        # Process update in background event loop
        run_coroutine_threadsafe(bot_application.process_update(update))
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
    if not _bot_initialized:
        init_bot()
    
    # Get port configuration
    port = int(os.getenv('PORT', 10000))
    
    logger.info(f"Starting Flask server on port {port}")
    logger.info("PnakoticBot is ready to receive messages!")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    main()
