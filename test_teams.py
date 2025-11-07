from data_collector import get_team_stats
from predictor import predict_match, predict_total_goals, predict_correct_score

print("=== Testing Real API Data ===\n")

# Test Arsenal
print("🔴 ARSENAL:")
arsenal = get_team_stats('Arsenal')
print(f"  Goals/game: {arsenal['goals_scored_avg']:.2f}")
print(f"  Conceded/game: {arsenal['goals_conceded_avg']:.2f}")
print(f"  Form (last 5): {arsenal['recent_form']}")
print(f"  Points (last 5): {arsenal['points_last_5']}")

print()

# Test Liverpool
print("🔴 LIVERPOOL:")
liverpool = get_team_stats('Liverpool')
print(f"  Goals/game: {liverpool['goals_scored_avg']:.2f}")
print(f"  Conceded/game: {liverpool['goals_conceded_avg']:.2f}")
print(f"  Form (last 5): {liverpool['recent_form']}")
print(f"  Points (last 5): {liverpool['points_last_5']}")

print("\n" + "="*60)
print("=== PREDICTION: Arsenal vs Liverpool ===")
print("="*60 + "\n")

# Predict match result
print("📊 DỰ ĐOÁN KẾT QUẢ:")
match_result = predict_match(arsenal, liverpool)
if match_result:
	print(f"  {match_result['recommendation']}")
	print(f"  Độ tin cậy: {match_result['confidence']:.1%}")

print()

# Predict total goals
print("⚽ DỰ ĐOÁN TỔNG BÀN THẮNG:")
goals_result = predict_total_goals(arsenal, liverpool)
if goals_result:
	print(f"  {goals_result['over_under_recommendation']}")
	print(f"  Độ tin cậy: {goals_result['ou_confidence']:.1%}")

# Correct score via Poisson
print("\n🎯 DỰ ĐOÁN TỈ SỐ (POISSON):")
cs = predict_correct_score(arsenal, liverpool)
print(f"  Gợi ý: {cs['best_correct_score']} ({cs['best_correct_score_prob']*100:.1f}%)")
print("  Top 5:")
for s, p in cs['top_scorelines']:
	print(f"   - {s}: {p*100:.1f}%")
