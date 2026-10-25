import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from model import calculate_match_probabilities

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def strip_vig_and_compare(sharp_home_odds, sharp_away_odds, soft_target_odds):
    """Removes bookmaker juice from sharp baseline odds to find true probability, 
       then compares against target soft book odds."""
    if sharp_home_odds <= 1.0 or sharp_away_odds <= 1.0 or soft_target_odds <= 1.0:
        return 0.0, 0.0
        
    implied_home = 1.0 / sharp_home_odds
    implied_away = 1.0 / sharp_away_odds
    
    total_overround = implied_home + implied_away
    true_home_prob = implied_home / total_overround
    
    ev = (true_home_prob * soft_target_odds) - 1.0
    return round(true_home_prob, 4), round(ev * 100, 2)

def ingest_sample_match():
    """
    Ingests sample fixtures with sharp vs retail odds comparison,
    calculates model probabilities using the Poisson model, 
    and saves them to PostgreSQL in the format required by evaluator.py.
    """
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment variables.")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Example incoming fixture data
        match_data = {
            "home_team": "Golden State Warriors",
            "away_team": "Phoenix Suns",
            "league": "NBA",
            "market": "1X2",
            "selection": "Golden State Warriors Win",
            "soft_odds": 2.15,
            "sharp_home_odds": 2.02,
            "sharp_away_odds": 1.85,
            "home_lambda": 1.65, 
            "away_lambda": 1.40
        }
        
        # Calculate model probability using the Poisson model from model.py
        probs = calculate_match_probabilities(match_data["home_lambda"], match_data["away_lambda"])
        model_prob = probs["home_win"]
        
        # Insert fixture matching the active database schema
        cur.execute("""
            INSERT INTO matches (home_team, away_team, league, market, selection, odds, model_probability, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'upcoming')
            RETURNING id;
        """, (
            match_data["home_team"],
            match_data["away_team"],
            match_data["league"],
            match_data["market"],
            match_data["selection"],
            match_data["soft_odds"],
            model_prob
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