"""
analyze_predictions.py - Phân tích chi tiết prediction accuracy và bias

Script này phân tích predictions_log.json để:
1. Tính accuracy tổng thể và theo confidence level
2. Phát hiện bias (Over/Under win rate)
3. Calibration analysis (confidence vs actual accuracy)
4. Performance theo thời gian
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt

PREDICTIONS_FILE = 'predictions_log.json'


def load_predictions():
    """Load predictions log."""
    if not os.path.exists(PREDICTIONS_FILE):
        print(f'❌ Không tìm thấy file: {PREDICTIONS_FILE}')
        return []
    
    with open(PREDICTIONS_FILE, 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    
    return predictions


def analyze_handicap_accuracy(predictions):
    """Phân tích accuracy cho kèo chấp."""
    completed = [p for p in predictions if p.get('actual_result') is not None]
    
    if not completed:
        print('⚠️ Chưa có trận nào hoàn thành.')
        return
    
    total = len(completed)
    correct = sum(1 for p in completed if p.get('correct'))
    accuracy = correct / total
    
    print('='*60)
    print('📊 PHÂN TÍCH KÈO CHẤP CHÂU Á')
    print('='*60)
    print(f'Tổng số dự đoán: {len(predictions)}')
    print(f'Đã hoàn thành: {total}')
    print(f'Dự đoán đúng: {correct}')
    print(f'Độ chính xác: {accuracy:.2%}')
    print()
    
    # Accuracy by confidence level
    conf_buckets = {
        'Cao (≥70%)': [p for p in completed if p.get('confidence', 0) >= 0.7],
        'Trung (55-70%)': [p for p in completed if 0.55 <= p.get('confidence', 0) < 0.7],
        'Thấp (<55%)': [p for p in completed if p.get('confidence', 0) < 0.55],
    }
    
    print('Theo độ tin cậy:')
    for label, preds in conf_buckets.items():
        if preds:
            correct_in_bucket = sum(1 for p in preds if p.get('correct'))
            acc_in_bucket = correct_in_bucket / len(preds)
            print(f'  {label}: {acc_in_bucket:.2%} ({correct_in_bucket}/{len(preds)})')
    print()
    
    # By home/away pick
    home_picks = [p for p in completed if p.get('prediction') == 1]
    away_picks = [p for p in completed if p.get('prediction') == 0]
    
    if home_picks:
        home_correct = sum(1 for p in home_picks if p.get('correct'))
        print(f'Chọn Nhà: {home_correct}/{len(home_picks)} đúng ({home_correct/len(home_picks):.2%})')
    if away_picks:
        away_correct = sum(1 for p in away_picks if p.get('correct'))
        print(f'Chọn Khách: {away_correct}/{len(away_picks)} đúng ({away_correct/len(away_picks):.2%})')
    print()


def analyze_ou_bias(predictions):
    """Phân tích bias Over/Under."""
    completed = [p for p in predictions 
                 if p.get('ou_pick') and p.get('ou_actual') and p.get('ou_actual') != 'Push']
    
    if not completed:
        print('⚠️ Chưa có dữ liệu O/U hoàn thành.')
        return
    
    print('='*60)
    print('🎯 PHÂN TÍCH OVER/UNDER BIAS')
    print('='*60)
    
    # Overall O/U accuracy
    total = len(completed)
    correct = sum(1 for p in completed if p.get('ou_correct'))
    accuracy = correct / total
    print(f'Tổng số dự đoán O/U: {total}')
    print(f'Độ chính xác: {accuracy:.2%} ({correct}/{total})')
    print()
    
    # Pick distribution
    over_picks = [p for p in completed if p.get('ou_pick') == 'Over']
    under_picks = [p for p in completed if p.get('ou_pick') == 'Under']
    
    print(f'Phân bổ pick:')
    print(f'  Over: {len(over_picks)} ({len(over_picks)/total:.1%})')
    print(f'  Under: {len(under_picks)} ({len(under_picks)/total:.1%})')
    print()
    
    # Win rate by pick
    if over_picks:
        over_correct = sum(1 for p in over_picks if p.get('ou_correct'))
        over_wr = over_correct / len(over_picks)
        print(f'Win rate khi pick Over: {over_wr:.2%} ({over_correct}/{len(over_picks)})')
    
    if under_picks:
        under_correct = sum(1 for p in under_picks if p.get('ou_correct'))
        under_wr = under_correct / len(under_picks)
        print(f'Win rate khi pick Under: {under_wr:.2%} ({under_correct}/{len(under_picks)})')
    print()
    
    # BIAS detection
    if over_picks and under_picks:
        over_bias = (len(over_picks) / total) - 0.5
        print(f'📈 Over Bias: {over_bias:+.1%} ({"Nghiêng Over" if over_bias > 0.1 else ("Nghiêng Under" if over_bias < -0.1 else "Cân bằng")})')
        
        # Performance vs market expectation
        # If we're picking Over too much, but win rate is low -> overconfident on Over
        if over_bias > 0.15 and over_wr < 0.5:
            print('⚠️ Cảnh báo: Model nghiêng Over quá mức nhưng win rate thấp!')
        elif over_bias < -0.15 and under_wr < 0.5:
            print('⚠️ Cảnh báo: Model nghiêng Under quá mức nhưng win rate thấp!')
    print()
    
    # By line
    lines = {}
    for p in completed:
        line = p.get('ou_line')
        if line:
            if line not in lines:
                lines[line] = []
            lines[line].append(p)
    
    if lines:
        print('Theo từng line:')
        for line in sorted(lines.keys()):
            preds = lines[line]
            correct_at_line = sum(1 for p in preds if p.get('ou_correct'))
            acc_at_line = correct_at_line / len(preds)
            over_at_line = sum(1 for p in preds if p.get('ou_pick') == 'Over')
            print(f'  Line {line}: {acc_at_line:.2%} ({correct_at_line}/{len(preds)}) | Over picks: {over_at_line}/{len(preds)}')
    print()


def analyze_calibration(predictions):
    """Phân tích calibration: confidence có khớp với accuracy thực tế không."""
    completed = [p for p in predictions if p.get('actual_result') is not None]
    
    if len(completed) < 10:
        print('⚠️ Cần ít nhất 10 trận để phân tích calibration.')
        return
    
    print('='*60)
    print('📐 PHÂN TÍCH CALIBRATION (Confidence vs Accuracy)')
    print('='*60)
    
    # Group by confidence bins
    bins = [
        (0.5, 0.6, '50-60%'),
        (0.6, 0.7, '60-70%'),
        (0.7, 0.8, '70-80%'),
        (0.8, 0.9, '80-90%'),
        (0.9, 1.0, '90-100%'),
    ]
    
    print('Confidence Range | Actual Accuracy | Count | Calibration Gap')
    print('-'*60)
    
    for min_conf, max_conf, label in bins:
        in_bin = [p for p in completed if min_conf <= p.get('confidence', 0) < max_conf]
        if in_bin:
            actual_acc = sum(1 for p in in_bin if p.get('correct')) / len(in_bin)
            expected_conf = sum(p.get('confidence', 0) for p in in_bin) / len(in_bin)
            gap = actual_acc - expected_conf
            
            gap_str = f'{gap:+.1%}'
            if abs(gap) > 0.15:
                gap_str += ' ⚠️ (Poorly calibrated)'
            elif abs(gap) < 0.05:
                gap_str += ' ✅ (Well calibrated)'
            
            print(f'{label:16s} | {actual_acc:15.1%} | {len(in_bin):5d} | {gap_str}')
    print()


def analyze_goals_prediction(predictions):
    """Phân tích độ chính xác dự đoán tổng bàn."""
    completed = [p for p in predictions 
                 if p.get('predicted_goals') is not None 
                 and p.get('home_goals') is not None 
                 and p.get('away_goals') is not None]
    
    if not completed:
        print('⚠️ Chưa có dữ liệu tổng bàn hoàn thành.')
        return
    
    print('='*60)
    print('⚽ PHÂN TÍCH DỰ ĐOÁN TỔNG BÀN THẮNG')
    print('='*60)
    
    errors = []
    for p in completed:
        predicted = p.get('predicted_goals', 0)
        actual = (p.get('home_goals', 0) or 0) + (p.get('away_goals', 0) or 0)
        error = abs(predicted - actual)
        errors.append(error)
    
    mae = sum(errors) / len(errors)
    print(f'Số trận: {len(completed)}')
    print(f'MAE (Mean Absolute Error): {mae:.2f} bàn')
    print(f'Dự đoán trung bình: {sum(p.get("predicted_goals", 0) for p in completed) / len(completed):.2f} bàn')
    print(f'Tổng bàn thực tế trung bình: {sum((p.get("home_goals", 0) or 0) + (p.get("away_goals", 0) or 0) for p in completed) / len(completed):.2f} bàn')
    
    # Bias
    over_predictions = sum(1 for p in completed 
                          if p.get('predicted_goals', 0) > ((p.get('home_goals', 0) or 0) + (p.get('away_goals', 0) or 0)))
    under_predictions = len(completed) - over_predictions
    print(f'\nDự đoán cao hơn thực tế: {over_predictions}/{len(completed)} ({over_predictions/len(completed):.1%})')
    print(f'Dự đoán thấp hơn thực tế: {under_predictions}/{len(completed)} ({under_predictions/len(completed):.1%})')
    print()


def print_recent_predictions(predictions, n=10):
    """In danh sách n predictions gần nhất."""
    recent = predictions[-n:] if len(predictions) > n else predictions
    
    print('='*60)
    print(f'📝 {min(n, len(recent))} DỰ ĐOÁN GẦN NHẤT')
    print('='*60)
    
    for p in reversed(recent):
        status = '⏳'
        if p.get('actual_result') is not None:
            status = '✅' if p.get('correct') else '❌'
        
        conf = p.get('confidence', 0)
        pick = 'Nhà' if p.get('prediction') == 1 else 'Khách'
        
        date_str = ''
        if p.get('timestamp'):
            try:
                dt = datetime.fromisoformat(p['timestamp'])
                date_str = dt.strftime('%d/%m %H:%M')
            except:
                pass
        
        print(f'{status} {date_str:12s} {p["home_team"]:20s} vs {p["away_team"]:20s}')
        print(f'   Pick: {pick:5s} | Conf: {conf:.1%}', end='')
        
        if p.get('home_goals') is not None:
            print(f' | Tỉ số: {p["home_goals"]}-{p["away_goals"]}', end='')
        
        if p.get('ou_pick'):
            ou_status = ''
            if p.get('ou_correct') is not None:
                ou_status = ' ✅' if p['ou_correct'] else (' ❌' if p['ou_correct'] is False else ' 🟡')
            print(f' | O/U: {p["ou_pick"]}{ou_status}', end='')
        
        print()
    print()


def main():
    """Chạy toàn bộ phân tích."""
    predictions = load_predictions()
    
    if not predictions:
        print('Không có dữ liệu để phân tích.')
        return
    
    print(f'\n📊 PHÂN TÍCH PREDICTION TRACKER')
    print(f'Thời gian: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Tổng số predictions: {len(predictions)}')
    print()
    
    # Run all analyses
    analyze_handicap_accuracy(predictions)
    analyze_ou_bias(predictions)
    analyze_calibration(predictions)
    analyze_goals_prediction(predictions)
    print_recent_predictions(predictions, n=15)
    
    # Summary recommendations
    completed = [p for p in predictions if p.get('actual_result') is not None]
    if len(completed) >= 20:
        print('='*60)
        print('💡 GỢI Ý CẢI THIỆN')
        print('='*60)
        
        # Check Over bias
        ou_completed = [p for p in completed if p.get('ou_pick') and p.get('ou_actual')]
        if ou_completed:
            over_picks = sum(1 for p in ou_completed if p.get('ou_pick') == 'Over')
            over_ratio = over_picks / len(ou_completed)
            
            if over_ratio > 0.65:
                print('• Model nghiêng Over quá mức (>65% picks là Over)')
                print('  → Gợi ý: Giảm alpha trong calibration hoặc tăng defensive dampening')
            elif over_ratio < 0.35:
                print('• Model nghiêng Under quá mức (<35% picks là Over)')
                print('  → Gợi ý: Tăng alpha hoặc kiểm tra scaler')
        
        # Check calibration
        high_conf = [p for p in completed if p.get('confidence', 0) >= 0.8]
        if len(high_conf) >= 5:
            high_conf_acc = sum(1 for p in high_conf if p.get('correct')) / len(high_conf)
            if high_conf_acc < 0.7:
                print('• Độ tin cậy cao (≥80%) nhưng accuracy thấp (<70%)')
                print('  → Gợi ý: Model overconfident, cần recalibrate hoặc thêm regularization')
        
        print()


if __name__ == '__main__':
    main()
