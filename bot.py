import os
import logging
import psycopg2
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv
from evaluator import evaluate_market_value

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and setup bottom reply keyboard."""
    keyboard = [
        [KeyboardButton("🎯 Check Value Bets"), KeyboardButton("⚙️ System Status")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🤖 **Sports Betting Analytics Bot**\n\nUse the permanent buttons below to interact:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Calculates and displays live syndicate portfolio performance."""
    if not DATABASE_URL:
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT COUNT(*), 
                   SUM(stake), 
                   SUM(profit_loss),
                   SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END)
            FROM matches 
            WHERE status = 'placed';
        """)
        total_bets, total_staked, total_pl, wins, losses = cur.fetchone()
        
        total_staked = float(total_staked or 0)
        total_pl = float(total_pl or 0)
        wins = int(wins or 0)
        losses = int(losses or 0)
        
        roi = (total_pl / total_staked * 100) if total_staked > 0 else 0.0
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0
        
        stats_card = (
            f"📈 **SYNDICATE PORTFOLIO PERFORMANCE**\n"
            f"──────────────────────────\n"
            f"🔢 Total Bets Placed: {total_bets or 0}\n"
            f"💰 Total Staked: ${total_staked:.2f}\n"
            f"🎯 Record (W-L): {wins}-{losses} ({win_rate:.1f}%)\n"
            f"💵 Net Profit/Loss: ${total_pl:+.2f}\n"
            f"📊 Return on Investment (ROI): {roi:+.2f}%\n"
            f"──────────────────────────"
        )
        
        cur.close()
        conn.close()
        await update.message.reply_text(stats_card, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        await update.message.reply_text("Error calculating portfolio statistics.")

async def background_value_scanner(context: ContextTypes.DEFAULT_TYPE):
    """Automatically scans database and pushes value bet signals to the chat channel."""
    if not CHAT_ID:
        return
        
    signals = evaluate_market_value()
    if signals:
        for sig in signals:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Log Bet", callback_data=f"log_{sig['id']}"),
                    InlineKeyboardButton("❌ Skip", callback_data=f"skip_{sig['id']}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=CHAT_ID, text=sig["card"], reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text clicks from the bottom reply keyboard and dispatch interactive cards."""
    text = update.message.text
    
    if text == "🎯 Check Value Bets":
        await update.message.reply_text("🔍 Scanning database and bookmaker odds...")
        signals = evaluate_market_value()
        
        if signals:
            for sig in signals:
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Log Bet", callback_data=f"log_{sig['id']}"),
                        InlineKeyboardButton("❌ Skip", callback_data=f"skip_{sig['id']}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(sig["card"], parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await update.message.reply_text("No value bets found with current database odds.")
            
    elif text == "⚙️ System Status":
        await update.message.reply_text("✅ **System Status:** Online & 24/7 background scanning active on Oracle Cloud.", parse_mode="Markdown")

async def button_response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button clicks to log bets into PostgreSQL."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, bet_id = data.split("_")
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    if action == "log":
        cur.execute("SELECT odds, model_probability FROM matches WHERE match_id = %s;", (bet_id,))
        row = cur.fetchone()
        if row:
            odds, prob = float(row[0]), float(row[1])
            b = odds - 1.0
            kelly = (b * prob - (1.0 - prob)) / b  # Changed 'p' to 'prob'
            stake = round(10000 * max(0, kelly) * 0.25, 2)
            
            cur.execute("""
                UPDATE matches 
                SET status = 'placed', stake = %s 
                WHERE match_id = %s;
            """, (stake, bet_id))
            conn.commit()
            
        await query.edit_message_text(text=query.message.text + "\n\n✅ **Status:** Logged to Active Portfolio.", parse_mode="Markdown")
    elif action == "skip":
        cur.execute("UPDATE matches SET status = 'skipped' WHERE match_id = %s;", (bet_id,))
        conn.commit()
        await query.edit_message_text(text=query.message.text + "\n\n❌ **Status:** Skipped.", parse_mode="Markdown")
        
    cur.close()
    conn.close()

def main():
    print("Bot is starting polling with automated background job queue...")
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_response_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Setup automated background job to check for value bets every 1800 seconds (30 minutes)
    job_queue = application.job_queue
    job_queue.run_repeating(background_value_scanner, interval=1800, first=10)

    application.run_polling()

if __name__ == "__main__":
    main()