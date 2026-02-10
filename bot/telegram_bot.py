"""
Telegram bot command handlers
Supports both private chats and group chats with brief error messages in groups
"""

from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes,
    MessageHandler,
    filters
)
from bot.card_fetcher import search_card, get_card_image_url, load_cards
from bot.faq_scraper import get_card_faq, load_faqs
from bot.utils import is_rate_limited, format_card_message
import os
import logging
from typing import Dict, List


# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    welcome_message = (
        "👋 *Welcome to PnakoticBot!*\n\n"
        "I can fetch Sorcery: Contested Realm card information from curiosa.io.\n\n"
        "📋 *Commands:*\n"
        "`/card <name>` - Get card image and FAQ\n"
        "`/help` - Show this help message\n\n"
        "📝 *Examples:*\n"
        "`/card Blink`\n"
        "`/card Apprentice Wizard`\n\n"
        "💡 *Tip:* I can handle typos and partial names!\n\n"
        "🔗 Data from [curiosa.io](https://curiosa.io)"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown', disable_web_page_preview=True)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    # Same as /start
    await start_command(update, context)


async def card_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /card <name> command
    Supports both private chats and group chats
    Brief error messages in groups as per user preference
    """
    
    # Check rate limiting
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    is_group = update.effective_chat.type in ['group', 'supergroup']
    
    if is_rate_limited(user_id if not is_group else chat_id, is_group):
        error_msg = "⏳ Rate limit exceeded. Please wait a moment."
        await update.message.reply_text(error_msg)
        return
    
    # Parse card name from command
    if not context.args:
        if is_group:
            msg = "❌ Provide card name"
        else:
            msg = "❌ Please provide a card name.\nExample: `/card Blink`"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    card_name = ' '.join(context.args)
    
    # Send typing indicator to show bot is working
    await update.effective_chat.send_action('typing')
    
    try:
        # Load card data (lazy load from cache)
        logger.info(f"Loading cards for query: {card_name}")
        cards = load_cards()
        if not cards:
            await update.message.reply_text("❌ Failed to load card database. Try again later.")
            return
        
        # Search for card
        result = search_card(card_name, cards)
        
        # Handle search results
        if result is None:
            # Not found - brief message in groups
            if is_group:
                msg = "❌ Not found"
            else:
                msg = f"❌ Card '{card_name}' not found. Check spelling?"
            
            await update.message.reply_text(msg)
            return
        
        elif isinstance(result, list):
            # Multiple matches - brief in groups
            if is_group:
                msg = f"🔍 {len(result)} matches. Be more specific."
            else:
                names = [c['name'] for c in result[:5]]
                msg = (
                    f"🔍 Found {len(result)} matches for '{card_name}':\n\n" +
                    '\n'.join(f"• {name}" for name in names)
                )
                if len(result) > 5:
                    msg += f"\n\n...and {len(result) - 5} more."
                msg += "\n\nPlease be more specific."
            
            await update.message.reply_text(msg)
            return
        
        # Single card found
        card = result
        
        # Load FAQ data (lazy load from cache)
        faqs = load_faqs()
        card_faqs = get_card_faq(card['name'], faqs)
        
        # Format message
        message = format_card_message(card, card_faqs)
        
        # Get image URL
        image_url = get_card_image_url(card)
        
        # Send response
        try:
            if image_url:
                # Try to send with image
                if is_group:
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=message,
                        parse_mode='Markdown',
                        reply_to_message_id=update.message.message_id
                    )
                else:
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=message,
                        parse_mode='Markdown'
                    )
            else:
                # No image URL - send text only
                raise Exception("No image URL available")
        
        except Exception as e:
            # Image failed - send text-only response (as per user preference)
            logger.warning(f"Image send failed for {card['name']}: {e}")
            
            if is_group:
                await update.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    reply_to_message_id=update.message.message_id,
                    disable_web_page_preview=True
                )
            else:
                await update.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
    
    except Exception as e:
        logger.error(f"Error in card_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Something went wrong. Please try again later."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors gracefully"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    # Notify user if possible
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred. Please try again later."
        )


def setup_bot() -> Application:
    """
    Setup and configure the bot
    
    Returns:
        Configured Application instance
    """
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('card', card_command))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("PnakoticBot handlers configured successfully")
    
    return application
