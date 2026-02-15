"""
Telegram bot command handlers
Supports both private chats and group chats with brief error messages in groups
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from bot.card_fetcher import search_card, get_card_image_url, load_cards
from bot.faq_scraper import get_card_faq, load_faqs
from bot.utils import is_rate_limited, format_card_message
from bot.replacement_finder import find_replacements, format_replacement_explanation
from bot.ebay_price_fetcher import (
    search_ebay_listings, 
    get_price_statistics, 
    format_price_message,
    search_ebay_sold_listings,
    format_sold_price_message
)
from bot.justtcg_price_fetcher import get_card_prices
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
        "`/replace <name>` - Find similar replacement cards\n"
        "`/price <name> [foil]` - Check active listings on eBay\n"
        "`/pricesold <name> [foil]` - Check historical sold prices\n"
        "`/help` - Show this help message\n\n"
        "📝 *Examples:*\n"
        "`/card Blink`\n"
        "`/replace Apprentice Wizard`\n"
        "`/price Blink`\n"
        "`/price Archmage foil`\n"
        "`/pricesold Blink`\n\n"
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
            # Multiple matches - show inline keyboard with options
            if is_group:
                # In groups, keep it brief with first few options
                matches = result[:5]
                msg = f"🔍 Found {len(result)} matches. Select one:"
            else:
                # In private chats, show up to 10 options
                matches = result[:10]
                msg = f"🔍 Found {len(result)} matches for '{card_name}'. Select one:"
            
            # Create inline keyboard with card name buttons
            keyboard = []
            for card in matches:
                # Use card name as callback data (encode to handle special chars)
                # Limit to 64 bytes for Telegram's callback_data limit
                callback_data = f"card:{card['name']}"
                if len(callback_data.encode('utf-8')) > 64:
                    # Truncate if too long (rare edge case)
                    callback_data = callback_data[:61] + "..."
                button = InlineKeyboardButton(card['name'], callback_data=callback_data)
                keyboard.append([button])  # One button per row
            
            # Add "Cancel" button at the end
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if is_group:
                await update.message.reply_text(
                    msg,
                    reply_markup=reply_markup,
                    reply_to_message_id=update.message.message_id
                )
            else:
                await update.message.reply_text(msg, reply_markup=reply_markup)
            return
        
        # Single card found - show card info
        await send_card_info(update, result, is_group)
    
    except Exception as e:
        logger.error(f"Error in card_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Something went wrong. Please try again later."
        )


async def replace_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /replace <card_name> command
    Suggests similar cards that can replace the given card
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
            msg = "❌ Please provide a card name.\nExample: `/replace Apprentice Wizard`"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    query = ' '.join(context.args)
    
    # Load cards
    cards = load_cards()
    if not cards:
        await update.message.reply_text("❌ Failed to load card database")
        return
    
    # Search for the card
    result = search_card(query, cards)
    
    if not result:
        if is_group:
            await update.message.reply_text("❌ Card not found")
        else:
            await update.message.reply_text(f"❌ No card found for '{query}'")
        return
    
    # Handle multiple matches
    if isinstance(result, list):
        if is_group:
            msg = f"❌ '{query}' matches multiple cards. Be more specific."
        else:
            card_names = [c['name'] for c in result[:5]]
            msg = f"❌ Multiple cards match '{query}':\n" + '\n'.join(f"• {n}" for n in card_names)
        
        await update.message.reply_text(msg)
        return
    
    # Single card found - find replacements
    card = result
    
    # Show "thinking" message
    thinking_msg = await update.message.reply_text(f"🔍 Finding replacements for *{card['name']}*...", parse_mode='Markdown')
    
    try:
        # Find replacement suggestions
        replacements = find_replacements(card['name'], cards, max_results=3, min_score=30.0)
        
        if not replacements:
            await thinking_msg.edit_text(
                f"❌ No suitable replacements found for *{card['name']}*.\n\n"
                f"Try cards with similar abilities or elements.",
                parse_mode='Markdown'
            )
            return
        
        # Format response
        response_lines = [f"🔄 *Replacements for {card['name']}:*\n"]
        
        for i, replacement in enumerate(replacements, 1):
            response_lines.append(f"{i}. {format_replacement_explanation(card, replacement)}")
            response_lines.append("")  # Blank line between cards
        
        response = '\n'.join(response_lines)
        
        # Send replacement suggestions
        await thinking_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error finding replacements: {e}", exc_info=True)
        await thinking_msg.edit_text("❌ Failed to find replacements. Try again later.")


async def send_card_info(update: Update, card: Dict, is_group: bool, query=None, context=None) -> None:
    """
    Send card information with image and FAQ
    
    Args:
        update: Telegram update
        card: Card data dictionary
        is_group: True if in group chat
        query: CallbackQuery if called from button click, None otherwise
        context: Bot context (needed when query is provided)
    """
    # Determine which message object to use
    msg_obj = query.message if query else update.message
    
    try:
        # Load FAQ data
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
                if is_group and not query:
                    # Direct command in group - reply to user's message
                    await msg_obj.reply_photo(
                        photo=image_url,
                        caption=message,
                        parse_mode='Markdown',
                        reply_to_message_id=update.message.message_id
                    )
                elif query:
                    # Callback query - send to chat (not as reply since selection message is deleted)
                    bot = context.bot if context else update.get_bot()
                    await bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=image_url,
                        caption=message,
                        parse_mode='Markdown'
                    )
                else:
                    # Private chat direct command
                    await msg_obj.reply_photo(
                        photo=image_url,
                        caption=message,
                        parse_mode='Markdown'
                    )
            else:
                # No image URL - send text only
                raise Exception("No image URL available")
        
        except Exception as e:
            # Image failed - send text-only response
            logger.warning(f"Image send failed for {card['name']}: {e}")
            
            if is_group and not query:
                # Direct command in group - reply to user's message
                await msg_obj.reply_text(
                    message,
                    parse_mode='Markdown',
                    reply_to_message_id=update.message.message_id,
                    disable_web_page_preview=True
                )
            elif query:
                # Callback query - send to chat (not as reply)
                bot = context.bot if context else update.get_bot()
                await bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            else:
                # Private chat direct command
                await msg_obj.reply_text(
                    message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
    except Exception as e:
        logger.error(f"Error sending card info: {e}", exc_info=True)
        await msg_obj.reply_text("❌ Failed to send card info. Try again later.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses"""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press
    
    # Parse callback data
    if query.data == "cancel":
        await query.edit_message_text("❌ Cancelled")
        return
    
    # Extract card slug from callback data
    if not query.data.startswith("card:"):
        await query.edit_message_text("❌ Invalid selection")
        return
    
    card_name = query.data.split(":", 1)[1]
    
    try:
        # Load cards and find the selected one
        cards = load_cards()
        card = next((c for c in cards if c['name'] == card_name), None)
        
        if not card:
            await query.edit_message_text("❌ Card not found")
            return
        
        # Delete the selection message
        await query.message.delete()
        
        # Check if this is a group
        is_group = update.effective_chat.type in ['group', 'supergroup']
        
        # Send the card info (pass context so it can use bot.send_message)
        await send_card_info(update, card, is_group, query, context)
        
    except Exception as e:
        logger.error(f"Error in button_callback: {e}", exc_info=True)
        # Try to edit message if it still exists, otherwise ignore
        try:
            await query.edit_message_text("❌ Something went wrong. Please try again.")
        except:
            pass


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /price <card_name> [foil] command
    Shows market prices from eBay and JustTCG (if available)
    Add 'foil' keyword to search for foil versions: /price Archmage foil
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
            msg = "❌ Please provide a card name.\nExample: `/price Blink` or `/price Archmage foil`"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    # Check if user wants foil prices
    args_list = list(context.args)
    foil_only = False
    
    # Check if 'foil' is in the arguments (case-insensitive)
    if args_list and args_list[-1].lower() == 'foil':
        foil_only = True
        args_list = args_list[:-1]  # Remove 'foil' from card name
    
    query = ' '.join(args_list)
    
    # Load cards to verify the card exists
    cards = load_cards()
    if not cards:
        await update.message.reply_text("❌ Failed to load card database")
        return
    
    # Search for the card to validate it exists
    result = search_card(query, cards)
    
    if not result:
        if is_group:
            await update.message.reply_text("❌ Card not found")
        else:
            await update.message.reply_text(f"❌ No card found for '{query}'")
        return
    
    # Handle multiple matches
    if isinstance(result, list):
        if is_group:
            msg = f"❌ '{query}' matches multiple cards. Be more specific."
        else:
            card_names = [c['name'] for c in result[:5]]
            msg = f"❌ Multiple cards match '{query}':\n" + '\n'.join(f"• {n}" for n in card_names)
        
        await update.message.reply_text(msg)
        return
    
    # Single card found
    card = result
    card_name = card['name']
    
    # Build search message
    foil_text = " (Foil)" if foil_only else " (Non-Foil)"
    
    # Show "searching" message
    thinking_msg = await update.message.reply_text(f"💰 Searching market prices for *{card_name}{foil_text}*...", parse_mode='Markdown')
    
    try:
        # Fetch prices from multiple sources
        response_parts = []
        has_any_data = False
        
        # 1. Try JustTCG first (usually more reliable for TCG prices)
        try:
            justtcg_message = get_card_prices(card_name)
            # get_card_prices returns formatted message ready for display
            # Only add if it contains actual price data (not just "not available" message)
            if justtcg_message and "not available yet" not in justtcg_message.lower():
                response_parts.append(justtcg_message)
                has_any_data = True
            elif justtcg_message:
                # Still include the "not available" message so users know why
                response_parts.append(justtcg_message)
        except Exception as e:
            logger.warning(f"JustTCG price fetch failed: {e}")
        
        # 2. Try eBay
        try:
            ebay_listings = search_ebay_listings(card_name, limit=10, foil_only=foil_only)
            if ebay_listings and len(ebay_listings) > 0:
                stats = get_price_statistics(ebay_listings)
                ebay_message = format_price_message(card_name, ebay_listings, stats, foil_only=foil_only)
                if "❌" not in ebay_message:  # Only add if successful
                    response_parts.append(ebay_message)
                    has_any_data = True
        except Exception as e:
            logger.warning(f"eBay price fetch failed: {e}")
        
        # Build final response
        if has_any_data:
            response = '\n\n---\n\n'.join(response_parts)
        else:
            # No data from any source
            response = (
                f"💰 *Market Prices for {card_name}*\n\n"
                "❌ No pricing data available from any source.\n\n"
                "*Possible reasons:*\n"
                "• API credentials not configured\n"
                "• Card not yet listed on marketplaces\n"
                "• Network connectivity issue\n\n"
                "💡 Try checking:\n"
                "• JustTCG.com directly\n"
                "• Sorcery Marketplace Discord"
            )
        
        await thinking_msg.edit_text(response, parse_mode='Markdown', disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Error fetching prices: {e}", exc_info=True)
        await thinking_msg.edit_text("❌ Failed to fetch market prices. Try again later.")


async def pricesold_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /pricesold <card_name> [foil] command
    Shows historical sold prices from eBay completed listings
    Add 'foil' keyword to search for foil versions: /pricesold Archmage foil
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
            msg = "❌ Please provide a card name.\nExample: `/pricesold Blink` or `/pricesold Archmage foil`"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    # Check if user wants foil prices
    args_list = list(context.args)
    foil_only = False
    
    # Check if 'foil' is in the arguments (case-insensitive)
    if args_list and args_list[-1].lower() == 'foil':
        foil_only = True
        args_list = args_list[:-1]  # Remove 'foil' from card name
    
    query = ' '.join(args_list)
    
    # Load cards to verify the card exists
    cards = load_cards()
    if not cards:
        await update.message.reply_text("❌ Failed to load card database")
        return
    
    # Search for the card to validate it exists
    result = search_card(query, cards)
    
    if not result:
        if is_group:
            await update.message.reply_text("❌ Card not found")
        else:
            await update.message.reply_text(f"❌ No card found for '{query}'")
        return
    
    # Handle multiple matches
    if isinstance(result, list):
        if is_group:
            msg = f"❌ '{query}' matches multiple cards. Be more specific."
        else:
            card_names = [c['name'] for c in result[:5]]
            msg = f"❌ Multiple cards match '{query}':\n" + '\n'.join(f"• {n}" for n in card_names)
        
        await update.message.reply_text(msg)
        return
    
    # Single card found
    card = result
    card_name = card['name']
    
    # Build search message
    foil_text = " (Foil)" if foil_only else " (Non-Foil)"
    
    # Show "searching" message
    thinking_msg = await update.message.reply_text(f"📊 Searching sold prices for *{card_name}{foil_text}*...", parse_mode='Markdown')
    
    try:
        # Fetch sold listings from eBay Finding API
        ebay_sold_listings = search_ebay_sold_listings(card_name, limit=20, foil_only=foil_only)
        
        if ebay_sold_listings and len(ebay_sold_listings) > 0:
            stats = get_price_statistics(ebay_sold_listings)
            response = format_sold_price_message(card_name, ebay_sold_listings, stats, foil_only=foil_only)
        else:
            # No sold listings found
            response = (
                f"📊 *Sold Prices for {card_name}{foil_text}*\n\n"
                "❌ No completed sales found on eBay.\n\n"
                "*Possible reasons:*\n"
                "• Card hasn't sold recently on eBay\n"
                "• API credentials not configured\n"
                "• Network connectivity issue\n\n"
                "💡 Try:\n"
                "• `/price` for current active listings\n"
                "• Check TCGPlayer or Sorcery Marketplace Discord"
            )
        
        await thinking_msg.edit_text(response, parse_mode='Markdown', disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Error fetching sold prices: {e}", exc_info=True)
        await thinking_msg.edit_text("❌ Failed to fetch sold prices. Try again later.")


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
    application.add_handler(CommandHandler('replace', replace_command))
    application.add_handler(CommandHandler('price', price_command))
    application.add_handler(CommandHandler('pricesold', pricesold_command))
    
    # Add callback query handler for inline keyboard buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("PnakoticBot handlers configured successfully")
    
    return application
