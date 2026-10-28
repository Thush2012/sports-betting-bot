import os
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

def evaluate_market_value():
    """Fetches matches via JOINs from PostgreSQL, evaluates odds, and formats signals."""
    signals = []
    
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment variables.")
        return signals

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT m.match_id, th.name AS home_team, ta.name AS away_team, 
                   m.league, m.market, m.selection, m.odds, m.model_probability 
            FROM matches m
            JOIN teams th ON m.home_team_id = th.team_id
            JOIN teams ta ON m.away_team_id = ta.team_id
            WHERE LOWER(m.status) = 'upcoming';
        """)
        rows = cur.fetchall()
        
        for row in rows:
            match_id, home, away, league, market, selection, odds, true_prob = row
            
            # Skip rows where odds or true_probability are NULL/None to prevent crash
            if odds is None or true_prob is None:
                continue
            
            ev = (float(true_prob) * float(odds)) - 1.0
            
            if ev > 0.00:  # Threshold for testing signals
                stake = calculate_kelly_stake(float(odds), float(true_prob))
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
                    f"• Model Probability: {round(float(true_prob) * 100, 1)}%\n"
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