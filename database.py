import psycopg2
from config import DATABASE_URL

def get_db_connection():
    """Connects directly to your Neon PostgreSQL database."""
    return psycopg2.connect(DATABASE_URL)

def get_active_matches():
    """Fetches upcoming matches from the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.match_id, m.match_date, h.name as home_team, a.name as away_team 
        FROM matches m
        JOIN teams h ON m.home_team_id = h.team_id
        JOIN teams a ON m.away_team_id = a.team_id
        WHERE m.status = 'UPCOMING';
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_team_elo(team_name: str):
    """Fetches a team's current Elo rating."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT elo_rating FROM teams WHERE name = %s;", (team_name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else 1500.0