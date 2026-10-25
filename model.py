import math
import numpy as np

def poisson_probability(lmbda, k):
    """Calculates Poisson probability for k goals given expected lambda."""
    return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

def calculate_match_probabilities(home_lambda, away_lambda, max_goals=6):
    """Calculates exact scoreline matrix and converts to 1X2 and Over/Under probabilities."""
    home_win = 0.0
    draw = 0.0
    away_win = 0.0
    over_2_5 = 0.0
    
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_probability(home_lambda, h) * poisson_probability(away_lambda, a)
            
            if h > a:
                home_win += p
            elif h == a:
                draw += p
            else:
                away_win += p
                
            if (h + a) > 2.5:
                over_2_5 += p
                
    return {
        "home_win": round(home_win, 4),
        "draw": round(draw, 4),
        "away_win": round(away_win, 4),
        "over_2_5": round(over_2_5, 4)
    }