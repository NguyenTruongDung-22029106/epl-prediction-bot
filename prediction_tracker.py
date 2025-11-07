"""
prediction_tracker.py - Track and monitor prediction accuracy

Module này lưu lại tất cả predictions và so sánh với kết quả thực tế
để đánh giá độ chính xác của model theo thời gian.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PREDICTIONS_FILE = 'predictions_log.json'
STATS_FILE = 'prediction_stats.csv'


def log_prediction(
    home_team: str,
    away_team: str,
    prediction: int,
    confidence: float,
    handicap_value: float = None,
    odds_data: Dict[str, Any] = None,
    # Over/Under logging
    ou_line: float | None = None,
    ou_pick: str | None = None,  # 'Over' or 'Under'
    ou_confidence: float | None = None,
    predicted_goals: float | None = None,
) -> str:
    """
    Lưu lại một prediction
    
    Returns:
        prediction_id: ID để track prediction này
    """
    prediction_id = f"{home_team}_{away_team}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    prediction_record = {
        'id': prediction_id,
        'timestamp': datetime.now().isoformat(),
        'home_team': home_team,
        'away_team': away_team,
        'prediction': prediction,  # 1 = home wins handicap, 0 = away wins
        'confidence': confidence,
        'handicap_value': handicap_value,
        'odds_data': odds_data,
        'actual_result': None,  # Sẽ update sau khi trận đấu kết thúc
        'correct': None,
        # Over/Under fields
        'ou_line': ou_line,
        'ou_pick': ou_pick,
        'ou_confidence': ou_confidence,
        'predicted_goals': predicted_goals,
        'ou_actual': None,
        'ou_correct': None
    }
    
    # Load existing predictions
    if os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, 'r', encoding='utf-8') as f:
            predictions = json.load(f)
    else:
        predictions = []
    
    # Add new prediction
    predictions.append(prediction_record)
    
    # Save
    with open(PREDICTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(predictions, f, indent=2, ensure_ascii=False)
    
    logger.info(f'Logged prediction: {prediction_id}')
    return prediction_id


def update_result(
    prediction_id: str,
    home_goals: int,
    away_goals: int,
    handicap_value: float,
) -> bool:
    """
    Cập nhật kết quả thực tế sau khi trận đấu kết thúc
    
    Returns:
        True nếu prediction đúng, False nếu sai
    """
    if not os.path.exists(PREDICTIONS_FILE):
        logger.error('Predictions file not found')
        return False
    
    with open(PREDICTIONS_FILE, 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    
    # Find prediction
    for pred in predictions:
        if pred['id'] == prediction_id:
            # Calculate actual result with handicap
            home_adjusted = home_goals + handicap_value
            actual_result = 1 if home_adjusted > away_goals else 0
            
            pred['actual_result'] = actual_result
            pred['home_goals'] = home_goals
            pred['away_goals'] = away_goals
            pred['correct'] = (pred['prediction'] == actual_result)

            # Over/Under outcome if logged
            if pred.get('ou_line') is not None and pred.get('ou_pick'):
                total_goals = (home_goals or 0) + (away_goals or 0)
                line = float(pred['ou_line'])
                # Standard Asian O/U grading (push if exactly equals line when using whole/half)
                if total_goals > line:
                    ou_actual = 'Over'
                elif total_goals < line:
                    ou_actual = 'Under'
                else:
                    ou_actual = 'Push'
                pred['ou_actual'] = ou_actual
                pred['ou_correct'] = (ou_actual == pred['ou_pick']) if ou_actual != 'Push' else None
            
            # Save
            with open(PREDICTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(predictions, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated result for {prediction_id}: {'Correct' if pred['correct'] else 'Wrong'}")
            
            # Update stats
            update_stats()
            
            return pred['correct']
    
    logger.error(f'Prediction {prediction_id} not found')
    return False


def update_stats():
    """
    Tính toán và lưu statistics từ tất cả predictions
    """
    if not os.path.exists(PREDICTIONS_FILE):
        return
    
    with open(PREDICTIONS_FILE, 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    
    # Filter predictions có kết quả
    completed = [p for p in predictions if p['actual_result'] is not None]
    
    if not completed:
        logger.warning('No completed predictions to analyze')
        return
    
    # Calculate statistics
    total = len(completed)
    correct = sum(1 for p in completed if p['correct'])
    accuracy = correct / total if total > 0 else 0
    
    # Accuracy by confidence level
    high_conf = [p for p in completed if p['confidence'] >= 0.7]
    med_conf = [p for p in completed if 0.55 <= p['confidence'] < 0.7]
    low_conf = [p for p in completed if p['confidence'] < 0.55]
    
    stats = {
        'last_updated': datetime.now().isoformat(),
        'total_predictions': len(predictions),
        'completed_predictions': total,
        'correct_predictions': correct,
        'overall_accuracy': accuracy,
        'high_confidence_accuracy': sum(1 for p in high_conf if p['correct']) / len(high_conf) if high_conf else 0,
        'medium_confidence_accuracy': sum(1 for p in med_conf if p['correct']) / len(med_conf) if med_conf else 0,
        'low_confidence_accuracy': sum(1 for p in low_conf if p['correct']) / len(low_conf) if low_conf else 0,
    }
    
    # Save to CSV for easy analysis
    df = pd.DataFrame([stats])
    df.to_csv(STATS_FILE, index=False)
    
    logger.info(f"Stats updated: {correct}/{total} correct ({accuracy:.2%})")
    
    return stats


def get_ou_accuracy(line: float) -> Dict[str, Any]:
    """Compute accuracy for Over/Under predictions at a given line (e.g., 2.5)."""
    if not os.path.exists(PREDICTIONS_FILE):
        return {'count': 0, 'correct': 0, 'accuracy': 0.0}

    with open(PREDICTIONS_FILE, 'r', encoding='utf-8') as f:
        predictions = json.load(f)

    filtered = [p for p in predictions if p.get('ou_line') == float(line) and p.get('ou_correct') is not None]
    count = len(filtered)
    correct = sum(1 for p in filtered if p['ou_correct'])
    acc = correct / count if count else 0.0
    return {'line': line, 'count': count, 'correct': correct, 'accuracy': acc}


def get_ou_stats(lines: list[float] = [1.5, 2.5, 3.5]) -> Dict[str, Any]:
    """Aggregate OU accuracy across common lines."""
    out = {str(l): get_ou_accuracy(l) for l in lines}
    return out


def get_stats() -> Optional[Dict[str, Any]]:
    """
    Lấy statistics hiện tại
    """
    if not os.path.exists(PREDICTIONS_FILE):
        return None
    
    with open(PREDICTIONS_FILE, 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    
    completed = [p for p in predictions if p['actual_result'] is not None]
    
    if not completed:
        return {
            'total_predictions': len(predictions),
            'completed_predictions': 0,
            'accuracy': 0,
            'message': 'No completed predictions yet'
        }
    
    total = len(completed)
    correct = sum(1 for p in completed if p['correct'])
    
    return {
        'total_predictions': len(predictions),
        'completed_predictions': total,
        'correct_predictions': correct,
        'accuracy': correct / total,
        'recent_10': completed[-10:] if len(completed) >= 10 else completed
    }


def print_report():
    """
    In báo cáo chi tiết về prediction accuracy
    """
    stats = get_stats()
    
    if not stats:
        print('No predictions logged yet.')
        return
    
    print('='*50)
    print('PREDICTION ACCURACY REPORT')
    print('='*50)
    print(f"Total predictions: {stats['total_predictions']}")
    print(f"Completed: {stats['completed_predictions']}")
    
    if stats['completed_predictions'] > 0:
        print(f"Correct: {stats['correct_predictions']}")
        print(f"Accuracy: {stats['accuracy']:.2%}")
        
        print('\nRecent predictions:')
        for p in stats.get('recent_10', []):
            result = '✓' if p['correct'] else '✗'
            print(f"  {result} {p['home_team']} vs {p['away_team']} - Confidence: {p['confidence']:.1%}")
    
    print('='*50)


if __name__ == '__main__':
    # Test
    print('Testing prediction tracker...\n')
    
    # Log a test prediction
    pred_id = log_prediction(
        'Arsenal',
        'Manchester United',
        prediction=1,
        confidence=0.82,
        handicap_value=-0.5
    )
    
    print(f'Logged prediction: {pred_id}')
    
    # Simulate updating result (Arsenal 2-1 Man Utd)
    # With handicap -0.5: Arsenal gets 2-0.5 = 1.5 vs Man Utd 1
    # Result: Arsenal wins handicap (1.5 > 1)
    is_correct = update_result(pred_id, home_goals=2, away_goals=1, handicap_value=-0.5)
    print(f'Prediction was: {"Correct!" if is_correct else "Wrong!"}')
    
    print('\nCurrent stats:')
    print_report()
