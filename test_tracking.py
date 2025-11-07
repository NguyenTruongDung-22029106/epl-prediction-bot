"""
test_tracking.py - Test auto-log và analysis với mock data
"""
from prediction_tracker import log_prediction, update_result
import random
from datetime import datetime, timedelta

# Mock teams
teams = [
    ('Arsenal', 'Manchester United'),
    ('Liverpool', 'Chelsea'),
    ('Manchester City', 'Tottenham'),
    ('Newcastle', 'Brighton'),
    ('Aston Villa', 'Everton'),
    ('West Ham', 'Crystal Palace'),
    ('Fulham', 'Brentford'),
    ('Wolves', 'Nottingham Forest'),
]

print('🧪 Testing prediction tracking với mock data...\n')

# Create mock predictions and results
for i, (home, away) in enumerate(teams):
    # Generate mock prediction
    confidence = random.uniform(0.55, 0.95)
    prediction = random.choice([0, 1])
    handicap = random.choice([-1.0, -0.5, -0.25, 0, 0.25, 0.5, 1.0])
    
    # O/U
    ou_line = 2.5
    ou_pick = random.choice(['Over', 'Under'])
    ou_conf = random.uniform(0.5, 0.75)
    predicted_goals = random.uniform(2.0, 3.5)
    
    # Log prediction
    pred_id = log_prediction(
        home, away,
        prediction=prediction,
        confidence=confidence,
        handicap_value=handicap,
        odds_data={'handicap_value': handicap, 'source': 'mock'},
        ou_line=ou_line,
        ou_pick=ou_pick,
        ou_confidence=ou_conf,
        predicted_goals=predicted_goals
    )
    print(f'✓ Logged: {home} vs {away}')
    
    # Simulate result for most matches
    if i < len(teams) - 2:  # Leave 2 pending
        home_goals = random.randint(0, 4)
        away_goals = random.randint(0, 3)
        
        is_correct = update_result(pred_id, home_goals, away_goals, handicap)
        print(f'  → Result: {home_goals}-{away_goals} | {"✅ Correct" if is_correct else "❌ Wrong"}')
    else:
        print(f'  → ⏳ Pending...')

print('\n✅ Mock data created!')
print('\nChạy analyze_predictions.py để xem phân tích...')
