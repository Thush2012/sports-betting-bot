import os
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# Comprehensive list of sports and racing categories available on The Odds API
TARGET_SPORTS = [
    "basketball_nba",
    "basketball_euroleague",
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "tennis_atp_us_open",
    "tennis_wta_rome",
    "motorsports_formula_one",
    "esports_counter_strike"
]

def fetch_and_store_live_odds():
    if not ODDS_API_KEY or not DATABASE_URL:
        print("Missing API key or Database URL.")
        return

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    for sport_key in TARGET_SPORTS:
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"
        
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Skipping {sport_key}: API Error {response.status_code}")
            continue
            
        events = response.json()
        print(f"Fetched {len(events)} events for {sport_key}")

        for event in events:
            home_team = event['home_team']
            away_team = event['away_team']
            commence_time = datetime.fromisoformat(event['commence_time'].replace('Z', '+00:00'))
            league = event['sport_title']
            sport_category = event.get('sport_group', 'General')
            
            # Insert participants/teams or competitors into database
            for participant in [home_team, away_team]:
                cur.execute("""
                    INSERT INTO teams (name, sport, country, elo_rating) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING;
                """, (participant, sport_category, 'Global', 1500.0))
            
            cur.execute("SELECT team_id FROM teams WHERE name = %s;", (home_team,))
            home_row = cur.fetchone()
            if not home_row:
                continue
            home_id = home_row[0]
            
            cur.execute("SELECT team_id FROM teams WHERE name = %s;", (away_team,))
            away_row = cur.fetchone()
            if not away_row:
                continue
            away_id = away_row[0]
            
            for bookmaker in event.get('bookmakers', []):
                if bookmaker['key'] in ['pinnacle', '1xbet', 'betfair']:
                    markets = bookmaker.get('markets', [])
                    if not markets:
                        continue
                    market = markets[0]
                    market_key = market.get('key', 'h2h')
                    
                    for outcome in market['outcomes']:
                        selection = outcome['name']
                        price = outcome['price']
                        
                        cur.execute("""
                            INSERT INTO matches (sport, match_date, home_team_id, away_team_id, league, market, selection, odds, model_probability, status, signal_sent)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'upcoming', FALSE)
                            ON CONFLICT (home_team_id, away_team_id, market, selection) 
                            DO UPDATE SET odds = EXCLUDED.odds, match_date = EXCLUDED.match_date;
                        """, (sport_category, commence_time, home_id, away_id, league, market_key, selection, price, 0.55))
                        
    conn.commit()
    cur.close()
    conn.close()
    print("Multi-sport and racing live odds successfully synchronized from API.")

if __name__ == "__main__":
    fetch_and_store_live_odds()