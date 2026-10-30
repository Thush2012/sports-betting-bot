import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def settle_pending_bets():
    """Automatically settles completed matches, updates P/L, and tracks Closing Line Value (CLV)."""
    if not DATABASE_URL:
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Select active placed bets where match is completed
        cur.execute("""
            SELECT match_id, stake, odds, closing_odds, result 
            FROM matches 
            WHERE status = 'placed' AND result != 'pending';
        """)
        bets = cur.fetchall()
        
        for match_id, stake, odds, closing_odds, result in bets:
            stake = float(stake or 0)
            odds = float(odds or 0)
            
            # Calculate Profit / Loss
            if result == 'won':
                pl = stake * (odds - 1.0)
            elif result == 'lost':
                pl = -stake
            else:
                pl = 0.0
                
            # Calculate CLV Edge if closing odds are available
            clv_edge = None
            if closing_odds:
                clv_edge = round((odds / float(closing_odds)) - 1.0, 4)

            # Update database record
            cur.execute("""
                UPDATE matches 
                SET profit_loss = %s, clv_edge = %s, status = 'settled' 
                WHERE match_id = %s;
            """, (pl, clv_edge, match_id))
            conn.commit()
            
        cur.close()
        conn.close()
        print("Portfolio bets successfully settled and CLV calculated.")
        
    except Exception as e:
        print(f"Error settling matches: {e}")

if __name__ == "__main__":
    settle_pending_bets()