import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from model import calculate_match_probabilities

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def ingest_sample_match():
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment variables.")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 1. Ensure teams exist and get their IDs
        teams = [
            ("Golden State Warriors", "Basketball", "USA", 1560.0),
            ("Phoenix Suns", "Basketball", "USA", 1540.0)
        ]
        
        team_ids = {}
        for name, sport, country, elo in teams:
            cur.execute("""
                INSERT INTO teams (name, sport, country, elo_rating) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating
                RETURNING team_id, name;
            """, (name, sport, country, elo))
            row = cur.fetchone()
            team_ids[row[1]] = row[0]

        # 2. Ensure matches table has required betting parameters
        cur.execute("""
            ALTER TABLE matches ADD COLUMN IF NOT EXISTS league VARCHAR(100);
            ALTER TABLE matches ADD COLUMN IF NOT EXISTS market VARCHAR(50);
            ALTER TABLE matches ADD COLUMN IF NOT EXISTS selection VARCHAR(100);
            ALTER TABLE matches ADD COLUMN IF NOT EXISTS odds NUMERIC(10,2);
            ALTER TABLE matches ADD COLUMN IF NOT EXISTS model_probability NUMERIC(5,4);
        """)

        home_id = team_ids["Golden State Warriors"]
        away_id = team_ids["Phoenix Suns"]
        
        # Calculate model probability using Poisson model
        probs = calculate_match_probabilities(1.65, 1.40)
        model_prob = probs["home_win"]
        
        # 3. Insert upcoming match
        cur.execute("""
            INSERT INTO matches (sport, match_date, home_team_id, away_team_id, league, market, selection, odds, model_probability, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'upcoming')
            RETURNING match_id;
        """, (
            'Basketball', datetime.now(), home_id, away_id, 
            'NBA', '1X2', 'Golden State Warriors Win', 2.15, model_prob
        ))
        
        match_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"Data ingestion completed successfully. Match ID: {match_id}")
        
    except Exception as e:
        print(f"Error during ingestion: {e}")

if __name__ == "__main__":
    ingest_sample_match()