import psycopg2
from config import DATABASE_URL
from model import calculate_win_probability, find_value_bets

def evaluate_market_value():
    """
    Scans upcoming matches and current bookmaker odds in Neon,
    runs the Elo model, and returns a list of high-value betting edges.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Fetch upcoming matches along with bookmaker odds
        cur.execute("""
            SELECT m.match_id, h.name as home_team, a.name as away_team, 
                   h.elo_rating as home_elo, a.elo_rating as away_elo,
                   o.home_odds, o.draw_odds, o.away_odds, o.bookmaker
            FROM matches m
            JOIN teams h ON m.home_team_id = h.team_id
            JOIN teams a ON m.away_team_id = a.team_id
            LEFT JOIN odds o ON m.match_id = o.match_id
            WHERE m.status = 'UPCOMING';
        """)
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        alerts = []
        for row in rows:
            match_id, home_team, away_team, home_elo, away_elo, h_odds, d_odds, a_odds, bookie = row
            
            # Skip if odds haven't been logged for this match yet
            if not h_odds or not a_odds:
                continue
                
            # 1. Calculate model probabilities
            home_prob, away_prob = calculate_win_probability(home_elo, away_elo)
            
            # 2. Check for value against bookmaker odds (e.g., 1xBet)
            value_recs = find_value_bets(home_prob, away_prob, h_odds, a_odds, min_edge=0.02)
            
            if value_recs:
                alert_msg = f"🎯 **Value Play Found ({bookie})!**\n🏀 {home_team} vs {away_team}\n"
                for rec in value_recs:
                    alert_msg += f"• {rec}\n"
                alerts.append(alert_msg)
                
        return alerts

    except Exception as e:
        print(f"Error evaluating market value: {e}")
        return []

if __name__ == "__main__":
    results = evaluate_market_value()
    if results:
        for alert in results:
            print(alert)
    else:
        print("No value bets found with current database odds.")