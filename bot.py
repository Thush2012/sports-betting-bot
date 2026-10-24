import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
from evaluator import evaluate_market_value

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message with interactive control buttons."""
    keyboard = [
        [InlineKeyboardButton("🎯 Check Value Bets", callback_data="check_value")],
        [InlineKeyboardButton("⚙️ System Status", callback_data="status")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 **Sports Betting Analytics Bot**\n\nChoose an action below:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check system operational status."""
    msg = "✅ **System Status:** Online & 24/7 background scanning active on Oracle Cloud."
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown")

async def value_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Evaluate market odds and return value bets."""
    msg = "🔍 Scanning database and bookmaker odds..."
    if update.message:
        await update.message.reply_text(msg)
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg)
        
    results = evaluate_market_value()
    if results:
        for alert in results:
            if update.message:
                await update.message.reply_text(alert, parse_mode="Markdown")
            elif update.callback_query:
                await update.callback_query.message.reply_text(alert, parse_mode="Markdown")
    else:
        no_res = "No value bets found with current database odds."
        if update.message:
            await update.message.reply_text(no_res)
        elif update.callback_query:
            await update.callback_query.message.reply_text(no_res)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button click events."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_value":
        await value_command(update, context)
    elif query.data == "status":
        await status_command(update, context)

def main():
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("value", value_command))
    
    # Callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is polling...")
    application.run_polling()

if __name__ == "__main__":
    main()