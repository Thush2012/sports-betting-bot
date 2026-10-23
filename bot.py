import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from database import get_active_matches, get_team_elo
from model import calculate_win_probability

# Enable logging to track errors in your terminal
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if TELEGRAM_CHAT_ID and str(user_id) != str(TELEGRAM_CHAT_ID):
        logger.warning(f"Unauthorized access attempt from user ID: {user_id}")
        return
    await update.message.reply_text("🤖 Sports Analytics & Betting Pipeline Active. Use /status to check upcoming matches.")

# Command: /status (Fetches real upcoming matches from Neon)
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if TELEGRAM_CHAT_ID and str(user_id) != str(TELEGRAM_CHAT_ID):
        logger.warning(f"Unauthorized status request from user ID: {user_id}")
        return
    
    matches = get_active_matches()
    
    if not matches:
        await update.message.reply_text("📊 **Current System Status:**\n• Database: Connected (Neon)\n• Active Matches: None found.")
        return
    
    response_text = "📊 **Upcoming Matches & Analysis:**\n\n"
    for match in matches:
        match_id, match_date, home_team, away_team = match
        home_elo = get_team_elo(home_team)
        away_elo = get_team_elo(away_team)
        
        home_prob, away_prob = calculate_win_probability(home_elo, away_elo)
        
        response_text += (
            f"🏀 **{home_team} vs {away_team}**\n"
            f"• Date: {match_date}\n"
            f"• Elo -> {home_team}: {home_elo} | {away_team}: {away_elo}\n"
            f"• Win Prob -> {home_team}: {home_prob*100:.1f}% | {away_team}: {away_prob*100:.1f}%\n\n"
        )
        
    await update.message.reply_text(response_text, parse_mode="Markdown")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_command))

    logger.info("Bot is starting polling...")
    app.run_polling()

if __name__ == "__main__":
    main()