import os
import math
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def calculate_kelly_stake(decimal_odds, true_probability, bankroll=10000, fraction=0.25):
    """Calculates fractional Kelly criterion stake size."""
    b = decimal_odds - 1.0
    p = true_probability
    q = 1.0 - p
    
    kelly_fraction = (b * p - q) / b
    if kelly_fraction <= 0:
        return 0.0
        
    recommended_stake = bankroll * kelly_fraction * fraction
    return round(recommended_stake, 2)

def scan_arbitrage_opportunities(odds_list):
    """Scans multi-bookmaker odds for guaranteed arbitrage margins."""
    if not odds_list:
        return {"is_arbitrage": False}
        
    best_selection = max(odds_list, key=lambda x: x["odds"])
    implied_sum = sum(1.0 / item["odds"] for item in odds_list)
    
    if implied_sum < 1.0:
        profit_margin = (1.0 - implied_sum) * 100
        return {
            "is_arbitrage": True,
            "margin": round(profit_margin, 2),
            "best_book": best_selection["bookmaker"],
            "best_odds": best_selection["odds"]
        }
        
    return {"is_arbitrage": False}

def evaluate_market_value():
    """Fetches matches from PostgreSQL, evaluates odds, and formats 1xBet signals."""
    signals = []
    
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment variables.")
        return signals

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, home_team, away_team, league, market, selection, odds, model_probability 
            FROM matches 
            WHERE status = 'upcoming';
        """)
        rows = cur.fetchall()
        
        for row in rows:
            match_id, home, away, league, market, selection, odds, true_prob = row
            
            ev = (true_prob * odds) - 1.0
            
            if ev > 0.03:  # 3% Edge Threshold
                stake = calculate_kelly_stake(odds, true_prob)
                edge_pct = round(ev * 100, 2)
                
                signal_card = (
                    f"🎯 𝗢PTIMAL VALUE BET SIGNAL\n"
                    f"──────────────────────────\n"
                    f"⚽ 𝗠atch: {home} vs {away}\n"
                    f"🏆 𝗟eague: {league}\n"
                    f"📊 𝗠arket: {market}\n"
                    f"📌 𝗦election: {selection}\n\n"
                    f"💰 𝟭xBet Execution Parameters:\n"
                    f"• Target Odds (1xBet): {odds}\n"
                    f"• Model Probability: {round(true_prob * 100, 1)}%\n"
                    f"• Expected Value (EV): +{edge_pct}%\n"
                    f"• Suggested Stake: ${stake} (Quarter Kelly)\n"
                    f"──────────────────────────\n"
                    f"⚡ Action: Open 1xBet & Place Order"
                )
                signals.append({
                    "id": match_id,
                    "card": signal_card
                })
                
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error connecting to database or evaluating market value: {e}")
        
    return signals