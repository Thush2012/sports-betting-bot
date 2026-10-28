import os
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

def fetch_and_store_live_odds(sport_key="basketball_nba"):
    if not ODDS_API_KEY or not DATABASE_URL:
        print("Missing API key or Database URL.")
        return

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching odds: {response.status_code}")
        return
        
    events = response.json()
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    for event in events:
        home_team = event['home_team']
        away_team = event['away_team']
        commence_time = datetime.fromisoformat(event['commence_time'].replace('Z', '+00:00'))
        league = event['sport_title']
        
        for team_name in [home_team, away_team]:
            cur.execute("""
                INSERT INTO teams (name, sport, country, elo_rating) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING;
            """, (team_name, 'Basketball', 'Global', 1500.0))
        
        cur.execute("SELECT team_id FROM teams WHERE name = %s;", (home_team,))
        home_id = cur.fetchone()[0]
        
        cur.execute("SELECT team_id FROM teams WHERE name = %s;", (away_team,))
        away_id = cur.fetchone()[0]
        
        for bookmaker in event.get('bookmakers', []):
            if bookmaker['key'] in ['pinnacle', '1xbet', 'betfair']:
                market = bookmaker['markets'][0]
                for outcome in market['outcomes']:
                    selection = outcome['name']
                    price = outcome['price']
                    
                    cur.execute("""
                        INSERT INTO matches (sport, match_date, home_team_id, away_team_id, league, market, selection, odds, model_probability, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'upcoming')
                        ON CONFLICT DO NOTHING;
                    """, ('Basketball', commence_time, home_id, away_id, league, '1X2', selection, price, 0.50))
                    
    conn.commit()
    cur.close()
    conn.close()
    print("Live odds successfully synchronized from API.")

if __name__ == "__main__":
    fetch_and_store_live_odds()