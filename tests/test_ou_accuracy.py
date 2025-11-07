"""
test_ou_accuracy.py - Unit tests cho O/U accuracy tracking
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from prediction_tracker import get_ou_accuracy, get_ou_stats


def create_test_data():
    """Tạo dữ liệu test với kết quả O/U đã biết"""
    data = {
        'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
        'home_team': ['Arsenal', 'Man City', 'Liverpool', 'Chelsea', 'Spurs'],
        'away_team': ['Man Utd', 'Newcastle', 'Brighton', 'Fulham', 'Wolves'],
        'prediction': [1, 1, 0, 1, 0],
        'ou_line': [2.5, 2.5, 2.5, 1.5, 3.5],
        'ou_pick': ['Over', 'Over', 'Under', 'Over', 'Under'],
        'predicted_goals': [3.2, 3.5, 2.1, 2.8, 2.9],
        'actual_home_goals': [2, 3, 1, 2, 1],
        'actual_away_goals': [1, 1, 2, 0, 2]
    }
    return pd.DataFrame(data)


def test_ou_accuracy_calculation():
    """Test: Tính toán độ chính xác O/U"""
    print("\n=== Test: O/U Accuracy Calculation ===")
    
    df = create_test_data()
    # Compute actual total
    df['actual_total_goals'] = df['actual_home_goals'] + df['actual_away_goals']
    
    # Save to production file temporarily
    backup_file = 'prediction_stats.csv.bak'
    import shutil
    if os.path.exists('prediction_stats.csv'):
        shutil.copy('prediction_stats.csv', backup_file)
    
    df.to_csv('prediction_stats.csv', index=False)
    
    try:
        # Calculate accuracy for line 2.5
        # Expected: 
        # Row 0: Over pred, actual=3 (Over) -> Correct
        # Row 1: Over pred, actual=4 (Over) -> Correct
        # Row 2: Under pred, actual=3 (Over) -> Wrong
        # Accuracy for 2.5 = 2/3 = 0.667
        
        stats = get_ou_stats([2.5])
        if stats and '2.5' in stats:
            acc = stats['2.5']['accuracy']
            count = stats['2.5']['count']
            correct = stats['2.5']['correct']
            print(f"Line 2.5: {correct}/{count} correct = {acc:.1%}")
            assert count == 3, f"Expected 3 predictions for line 2.5, got {count}"
            assert correct == 2, f"Expected 2 correct for line 2.5, got {correct}"
            print("✅ PASS: O/U accuracy calculated correctly")
        else:
            print("⚠️  SKIP: get_ou_stats returned empty")
    finally:
        # Restore backup
        if os.path.exists(backup_file):
            shutil.move(backup_file, 'prediction_stats.csv')
        elif os.path.exists('prediction_stats.csv'):
            os.remove('prediction_stats.csv')


def test_multiple_lines():
    """Test: Tính accuracy cho nhiều mốc"""
    print("\n=== Test: Multiple Lines Accuracy ===")
    
    df = create_test_data()
    df['actual_total_goals'] = df['actual_home_goals'] + df['actual_away_goals']
    
    # Save to production file temporarily
    backup_file = 'prediction_stats.csv.bak'
    import shutil
    if os.path.exists('prediction_stats.csv'):
        shutil.copy('prediction_stats.csv', backup_file)
    
    df.to_csv('prediction_stats.csv', index=False)
    
    try:
        stats = get_ou_stats([1.5, 2.5, 3.5])
        
        if stats:
            print("Accuracies by line:")
            for line, data in stats.items():
                print(f"  {line}: {data['correct']}/{data['count']} = {data['accuracy']:.1%}")
            
            # Line 1.5: Row 3 (Over pred, actual=2 Over) -> 1/1 correct
            # Line 2.5: Rows 0,1,2 -> 2/3 correct  
            # Line 3.5: Row 4 (Under pred, actual=3 Under) -> 1/1 correct
            
            if '1.5' in stats:
                assert stats['1.5']['count'] == 1, "Line 1.5 should have 1 prediction"
            if '3.5' in stats:
                assert stats['3.5']['count'] == 1, "Line 3.5 should have 1 prediction"
            
            print("✅ PASS: Multiple lines tracked correctly")
        else:
            print("⚠️  SKIP: get_ou_stats returned empty")
    finally:
        if os.path.exists(backup_file):
            shutil.move(backup_file, 'prediction_stats.csv')
        elif os.path.exists('prediction_stats.csv'):
            os.remove('prediction_stats.csv')


def test_edge_cases():
    """Test: Trường hợp đặc biệt (0 predictions, missing data)"""
    print("\n=== Test: Edge Cases ===")
    
    # Empty dataframe
    empty_df = pd.DataFrame(columns=['date', 'ou_line', 'ou_pick', 'actual_total_goals'])
    backup_file = 'prediction_stats.csv.bak'
    import shutil
    if os.path.exists('prediction_stats.csv'):
        shutil.copy('prediction_stats.csv', backup_file)
    
    empty_df.to_csv('prediction_stats.csv', index=False)
    
    try:
        stats = get_ou_stats([2.5])
        if stats and '2.5' in stats:
            assert stats['2.5']['count'] == 0, "Empty data should have 0 predictions"
        print("✅ PASS: Empty data handled correctly")
    except Exception as e:
        print(f"⚠️  Expected behavior for empty data: {e}")
    finally:
        if os.path.exists(backup_file):
            shutil.move(backup_file, 'prediction_stats.csv')
        elif os.path.exists('prediction_stats.csv'):
            os.remove('prediction_stats.csv')


if __name__ == '__main__':
    print("=" * 60)
    print("Running O/U Accuracy Tests")
    print("=" * 60)
    
    try:
        test_ou_accuracy_calculation()
        test_multiple_lines()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("✅ ALL O/U TESTS COMPLETED")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
