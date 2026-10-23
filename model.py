import math

def calculate_win_probability(home_elo, away_elo, home_advantage=50):
    """
    Calculates expected win probabilities for Home and Away teams using Elo.
    Home advantage is typically added to the home team's rating (e.g., +50 points).
    """
    adjusted_home_elo = home_elo + home_advantage
    diff = adjusted_home_elo - away_elo
    
    # Standard Elo probability formula
    home_prob = 1 / (1 + math.pow(10, -diff / 400))
    away_prob = 1 - home_prob
    
    return home_prob, away_prob

def find_value_bets(home_prob, away_prob, home_odds, away_odds, min_edge=0.03):
    """
    Compares model probability against bookmaker implied probability.
    Edge = Model Probability - Implied Probability.
    """
    implied_home_prob = 1 / home_odds
    implied_away_prob = 1 / away_odds
    
    home_edge = home_prob - implied_home_prob
    away_edge = away_prob - implied_away_prob
    
    recommendations = []
    if home_edge > min_edge:
        recommendations.append(f"🔥 VALUE BET ON HOME TEAM! Edge: {home_edge * 100:.2f}% (Odds: {home_odds})")
    if away_edge > min_edge:
        recommendations.append(f"🔥 VALUE BET ON AWAY TEAM! Edge: {away_edge * 100:.2f}% (Odds: {away_odds})")
        
    return recommendations