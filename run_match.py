import os
import logging
from data_collector import get_team_stats, get_odds_data
from predictor import predict_match, predict_total_goals, predict_multiline_ou, predict_correct_score

logging.basicConfig(level=logging.DEBUG)

FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

def run(home, away):
    print(f"\n=== {home} vs {away} ===")
    hs = get_team_stats(home, FOOTBALL_DATA_API_KEY)
    as_ = get_team_stats(away, FOOTBALL_DATA_API_KEY)
    odds = get_odds_data(home, away, ODDS_API_KEY)

    pm = predict_match(hs, as_, odds)
    pg = predict_total_goals(hs, as_, odds)
    pred_goals = pg.get('predicted_goals') if pg else None
    ml = predict_multiline_ou(hs, as_, odds, predicted_goals=pred_goals)
    cs = predict_correct_score(hs, as_, predicted_goals=pred_goals)

    print("\n-- Handicap prediction --")
    print(pm)
    print("\n-- Goals (with calibration & clamp) --")
    print(pg)
    if ml:
        print("\n-- OU Multi (1.5/2.5/3.5) --")
        for line in ['1.5','2.5','3.5']:
            d = ml.get(line)
            if d:
                print(f"{line}: over={d['over_prob']:.3f} under={d['under_prob']:.3f} rec={d['recommendation']} conf={d['confidence']:.3f}")
    if cs:
        print("\n-- Best correct score --")
        print(cs['best_correct_score'], cs['best_correct_score_prob'])

if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 3:
        home = sys.argv[1]
        away = sys.argv[2]
    else:
        home = 'Aston Villa FC'
        away = 'AFC Bournemouth'
    run(home, away)
