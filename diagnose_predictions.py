import os
from data_collector import get_team_stats, get_odds_data
from predictor import predict_match, predict_total_goals, predict_multiline_ou, predict_correct_score

FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

SAMPLE_MATCHES = [
    ("Arsenal", "Manchester United"),
    ("Manchester City", "Chelsea"),
    ("Liverpool", "Tottenham"),
    ("Newcastle", "Brighton"),
    ("Aston Villa", "Everton"),
]

def run_one(home, away):
    home_stats = get_team_stats(home, FOOTBALL_DATA_API_KEY)
    away_stats = get_team_stats(away, FOOTBALL_DATA_API_KEY)
    odds_data = get_odds_data(home, away, ODDS_API_KEY)

    pred = predict_match(home_stats, away_stats, odds_data)
    goals = predict_total_goals(home_stats, away_stats, odds_data)
    cached_goals = goals.get('predicted_goals') if goals else None
    ou_multi = predict_multiline_ou(home_stats, away_stats, odds_data, predicted_goals=cached_goals)
    cs = predict_correct_score(home_stats, away_stats, predicted_goals=cached_goals)

    return {
        'match': f"{home} vs {away}",
        'prediction': pred,
        'goals': goals,
        'ou_multi': ou_multi,
        'correct_score': cs,
    }


def main():
    print("== Diagnostic Prediction Run ==")
    results = []
    for home, away in SAMPLE_MATCHES:
        try:
            res = run_one(home, away)
            results.append(res)
        except Exception as e:
            print(f"Error on {home} vs {away}: {e}")

    # Print succinct summary
    for r in results:
        pred = r['prediction'] or {}
        goals = r['goals'] or {}
        ou = r['ou_multi'] or {}
        cs = r['correct_score'] or {}
        print("\n---", r['match'], "---")
        print("recommendation:", pred.get('recommendation'))
        print("confidence:", pred.get('confidence'))
        print("predicted_goals:", goals.get('predicted_goals'))
        if 'over_under_recommendation' in goals:
            print("ou_2.5:", goals.get('over_under_recommendation'), goals.get('ou_confidence'))
        # show OU multi quick snapshot
        for line in ['1.5','2.5','3.5']:
            d = ou.get(line) or {}
            if d:
                print(f"line {line}: over={d.get('over_prob'):.3f} under={d.get('under_prob'):.3f} rec={d.get('recommendation')}")
        # top scoreline
        if 'best_correct_score' in cs:
            print("best_correct_score:", cs['best_correct_score'], cs['best_correct_score_prob'])

if __name__ == '__main__':
    main()
