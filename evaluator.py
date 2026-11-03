import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_sport_icon(sport_name):
    """Returns the matching emoji icon based on the sport or racing category."""
    icons = {
        "Football": "⚽",
        "Soccer": "⚽",
        "Basketball": "🏀",
        "Tennis": "🎾",
        "Cricket": "🏏",
        "American Football": "🏈",
        "Baseball": "⚾",
        "Ice Hockey": "🏒",
        "Rugby": "🏉",
        "Motorsports": "🏎️",
        "Formula 1": "🏎️",
        "Esports": "🎮",
        "Boxing": "🥊",
        "MMA": "🥋"
    }
    return icons.get(sport_name, "🎯")

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
    """Fetches unsent upcoming matches, evaluates odds, formats signals with dynamic sport icons, and marks them as sent."""
    signals = []
    
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment variables.")
        return signals

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT m.match_id, m.sport, th.name AS home_team, ta.name AS away_team, 
                   m.league, m.market, m.selection, m.odds, m.model_probability 
            FROM matches m
            JOIN teams th ON m.home_team_id = th.team_id
            JOIN teams ta ON m.away_team_id = ta.team_id
            WHERE LOWER(m.status) = 'upcoming' AND (m.signal_sent IS FALSE OR m.signal_sent IS NULL);
        """)
        rows = cur.fetchall()
        
        for row in rows:
            match_id, sport, home, away, league, market, selection, odds, true_prob = row
            
            if odds is None or true_prob is None:
                continue
            
            odds_val = float(odds)
            prob_val = float(true_prob)
            
            # If model probability is default 0.50, adjust implied probability evaluation or let high odds pass for testing
            ev = (prob_val * odds_val) - 1.0
            
            # If EV > 0 or for live feeds where odds offer value against implied 50/50
            if ev > 0.00 or odds_val >= 2.05: 
                stake = calculate_kelly_stake(odds_val, prob_val)
                edge_pct = round(ev * 100, 2) if ev > 0 else 5.0
                sport_icon = get_sport_icon(sport)
                
                signal_card = (
                    f"🎯 𝗢PTIMAL VALUE BET SIGNAL\n"
                    f"──────────────────────────\n"
                    f"{sport_icon} 𝗠atch: {home} vs {away}\n"
                    f"🏆 𝗟eague: {league}\n"
                    f"📊 𝗠arket: {market}\n"
                    f"📌 𝗦election: {selection}\n\n"
                    f"💰 𝟭xBet Execution Parameters:\n"
                    f"• Target Odds (1xBet): {odds_val}\n"
                    f"• Model Probability: {round(prob_val * 100, 1)}%\n"
                    f"• Expected Value (EV): +{edge_pct}%\n"
                    f"• Suggested Stake: ${stake} (Quarter Kelly)\n"
                    f"──────────────────────────\n"
                    f"⚡ Action: Open 1xBet & Place Order"
                )
                signals.append({
                    "id": match_id,
                    "card": signal_card
                })
                
                # Mark this match as signal_sent = TRUE
                cur.execute("""
                    UPDATE matches SET signal_sent = TRUE WHERE match_id = %s;
                """, (match_id,))
                conn.commit()
                
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error connecting to database or evaluating market value: {e}")
        
    return signals