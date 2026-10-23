import psycopg2
from datetime import datetime
from config import DATABASE_URL
from model import calculate_win_probability

def ingest_sample_match():
    """
    Example ingestion script to add incoming fixtures, 
    update teams, and check values programmatically.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 1. Ensure teams exist and get their IDs & Elo ratings
        teams = [("Golden State Warriors", "Basketball", "USA", 1560.0), 
                 ("Phoenix Suns", "Basketball", "USA", 1540.0)]
        
        team_ids = {}
        for name, sport, country, elo in teams:
            cur.execute("""
                INSERT INTO teams (name, sport, country, elo_rating) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating
                RETURNING team_id, name, elo_rating;
            """, (name, sport, country, elo))
            row = cur.fetchone()
            team_ids[row[1]] = {"id": row[0], "elo": row[2]}

        # 2. Insert an upcoming match
        home_team = "Golden State Warriors"
        away_team = "Phoenix Suns"
        
        cur.execute("""
            INSERT INTO matches (sport, match_date, home_team_id, away_team_id, status)
            VALUES (%s, %s, %s, %s, 'UPCOMING')
            RETURNING match_id;
        """, ('Basketball', datetime.now(), team_ids[home_team]["id"], team_ids[away_team]["id"]))
        
        conn.commit()
        cur.close()
        conn.close()
        print("Data ingestion completed successfully.")
        
    except Exception as e:
        print(f"Error during ingestion: {e}")

if __name__ == "__main__":
    ingest_sample_match()