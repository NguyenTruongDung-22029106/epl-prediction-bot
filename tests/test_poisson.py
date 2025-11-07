"""
test_poisson.py - Unit tests cho Poisson model
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from poisson_model import score_matrix, top_scorelines, ou_probabilities, expected_goals


def test_probability_sums_to_one():
    """Test: Tổng xác suất tất cả scorelines phải gần 1.0"""
    print("\n=== Test: Probability Matrix Sum ===")
    lam_h, lam_a = 1.5, 1.2
    prob = score_matrix(lam_h, lam_a, max_goals=8)
    total = float(np.sum(prob))
    print(f"Lambda Home: {lam_h}, Lambda Away: {lam_a}")
    print(f"Total probability: {total:.6f}")
    assert 0.98 <= total <= 1.02, f"Total probability should be ~1.0, got {total}"
    print("✅ PASS: Total probability is ~1.0")


def test_ou_probabilities_sum():
    """Test: over + under + push phải = 1.0 (hoặc gần 1.0)"""
    print("\n=== Test: O/U Probabilities Sum ===")
    lam_h, lam_a = 1.8, 1.3
    prob = score_matrix(lam_h, lam_a, max_goals=8)
    
    for line in [1.5, 2.5, 3.5]:
        over, under, push = ou_probabilities(prob, line)
        total = over + under + push
        print(f"Line {line}: Over={over:.3f}, Under={under:.3f}, Push={push:.3f}, Sum={total:.3f}")
        assert 0.98 <= total <= 1.02, f"O/U probabilities should sum to ~1.0 for line {line}, got {total}"
    print("✅ PASS: All O/U sums are ~1.0")


def test_top_scorelines_order():
    """Test: Top scorelines phải được sắp xếp theo xác suất giảm dần"""
    print("\n=== Test: Top Scorelines Order ===")
    lam_h, lam_a = 2.0, 1.5
    prob = score_matrix(lam_h, lam_a, max_goals=6)
    top5 = top_scorelines(prob, n=5)
    
    print(f"Top 5 scorelines:")
    for i, (score, p) in enumerate(top5):
        print(f"  {i+1}. {score}: {p*100:.2f}%")
    
    # Kiểm tra xác suất giảm dần
    for i in range(len(top5) - 1):
        assert top5[i][1] >= top5[i+1][1], f"Scorelines not in descending order at position {i}"
    
    print("✅ PASS: Scorelines are ordered by probability")


def test_expected_goals_positive():
    """Test: Expected goals phải > 0"""
    print("\n=== Test: Expected Goals Positive ===")
    
    # Mock strengths with correct keys (home_attack, home_defense, away_attack, away_defense)
    strengths = {
        'Arsenal': {'home_attack': 1.2, 'home_defense': 0.8, 'away_attack': 1.1, 'away_defense': 0.85},
        'Liverpool': {'home_attack': 1.15, 'home_defense': 0.9, 'away_attack': 1.05, 'away_defense': 0.9}
    }
    mu_home, mu_away = 1.5, 1.3
    
    lam_h, lam_a = expected_goals('Arsenal', 'Liverpool', strengths, mu_home, mu_away)
    print(f"Arsenal vs Liverpool: λ_home={lam_h:.3f}, λ_away={lam_a:.3f}")
    
    assert lam_h > 0, f"Home expected goals should be > 0, got {lam_h}"
    assert lam_a > 0, f"Away expected goals should be > 0, got {lam_a}"
    print("✅ PASS: Expected goals are positive")


def test_zero_line_ou():
    """Test: Line 0.5 phải có under rất thấp"""
    print("\n=== Test: Zero Line O/U ===")
    lam_h, lam_a = 1.5, 1.2
    prob = score_matrix(lam_h, lam_a, max_goals=8)
    over, under, push = ou_probabilities(prob, 0.5)
    
    print(f"Line 0.5: Over={over:.3f}, Under={under:.3f}")
    assert over > 0.8, f"Over 0.5 should be very high, got {over}"
    assert under < 0.2, f"Under 0.5 should be very low, got {under}"
    print("✅ PASS: Line 0.5 behaves correctly")


if __name__ == '__main__':
    print("=" * 60)
    print("Running Poisson Model Tests")
    print("=" * 60)
    
    try:
        test_probability_sums_to_one()
        test_ou_probabilities_sum()
        test_top_scorelines_order()
        test_expected_goals_positive()
        test_zero_line_ou()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
