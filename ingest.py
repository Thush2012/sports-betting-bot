import os
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def ingest_comprehensive_data():
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment variables.")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 1. Ensure required tables and columns exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                team_id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                sport VARCHAR(50),
                country VARCHAR(50),
                elo_rating NUMERIC(10,2)
            );
            
            CREATE TABLE IF NOT EXISTS matches (
                match_id SERIAL PRIMARY KEY,
                sport VARCHAR(50),
                match_date TIMESTAMP,
                home_team_id INT REFERENCES teams(team_id),
                away_team_id INT REFERENCES teams(team_id),
                league VARCHAR(100),
                market VARCHAR(50),
                selection VARCHAR(100),
                odds NUMERIC(10,2),
                model_probability NUMERIC(5,4),
                status VARCHAR(20) DEFAULT 'upcoming'
            );
        """)
        
        # 2. Insert Teams (Player/Club details)
        teams_data = [
            ("Real Madrid", "Football", "Spain", 1850.0),
            ("Barcelona", "Football", "Spain", 1830.0),
            ("Golden State Warriors", "Basketball", "USA", 1560.0),
            ("Phoenix Suns", "Basketball", "USA", 1540.0),
            ("Manchester City", "Football", "England", 1870.0),
            ("Arsenal", "Football", "England", 1810.0)
        ]
        
        team_ids = {}
        for name, sport, country, elo in teams_data:
            cur.execute("""
                INSERT INTO teams (name, sport, country, elo_rating) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET elo_rating = EXCLUDED.elo_rating
                RETURNING team_id, name;
            """, (name, sport, country, elo))
            row = cur.fetchone()
            team_ids[row[1]] = row[0]

        # 3. Insert Historical / Previous Matches
        past_matches = [
            ("Football", datetime.now() - timedelta(days=3), team_ids["Real Madrid"], team_ids["Barcelona"], "La Liga", "1X2", "Real Madrid Win", 2.10, 0.52, 'completed'),
            ("Football", datetime.now() - timedelta(days=5), team_ids["Manchester City"], team_ids["Arsenal"], "Premier League", "1X2", "Draw", 3.40, 0.31, 'completed')
        ]
        
        for sport, m_date, home_id, away_id, league, market, selection, odds, prob, status in past_matches:
            cur.execute("""
                INSERT INTO matches (sport, match_date, home_team_id, away_team_id, league, market, selection, odds, model_probability, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (sport, m_date, home_id, away_id, league, market, selection, odds, prob, status))

        # 4. Insert Upcoming Value Matches
        upcoming_matches = [
            ("Basketball", datetime.now() + timedelta(hours=4), team_ids["Golden State Warriors"], team_ids["Phoenix Suns"], "NBA", "1X2", "Golden State Warriors Win", 2.15, 0.55, 'upcoming'),
            ("Football", datetime.now() + timedelta(hours=8), team_ids["Real Madrid"], team_ids["Manchester City"], "UEFA Champions League", "1X2", "Real Madrid Win", 2.50, 0.45, 'upcoming')
        ]
        
        for sport, m_date, home_id, away_id, league, market, selection, odds, prob, status in upcoming_matches:
            cur.execute("""
                INSERT INTO matches (sport, match_date, home_team_id, away_team_id, league, market, selection, odds, model_probability, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (sport, m_date, home_id, away_id, league, market, selection, odds, prob, status))

        conn.commit()
        cur.close()
        conn.close()
        
        print("Comprehensive database ingestion completed successfully!")
        
    except Exception as e:
        print(f"Error during data ingestion: {e}")

if __name__ == "__main__":
    ingest_comprehensive_data()