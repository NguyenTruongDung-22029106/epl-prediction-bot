"""
predictor.py - Module dự đoán sử dụng Machine Learning model

Module này chứa logic để:
1. Load model đã được huấn luyện
2. Chuẩn bị features từ dữ liệu trận đấu mới
3. Đưa ra dự đoán và khuyến nghị
"""

import os
import logging
from typing import Dict, Any, Optional
import pickle

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Đường dẫn đến model file
MODEL_PATH = 'epl_prediction_model.pkl'


def load_model():
    """
    Load model Machine Learning đã được huấn luyện
    
    Returns:
        Model object hoặc None nếu không tìm thấy
    """
    if not os.path.exists(MODEL_PATH):
        logger.warning(f'Model file không tồn tại: {MODEL_PATH}')
        return None
    
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        logger.info(f'Đã load model từ {MODEL_PATH}')
        return model
    except Exception as e:
        logger.error(f'Lỗi khi load model: {e}')
        return None


def prepare_features(home_stats: Dict[str, Any], away_stats: Dict[str, Any], 
                     odds_data: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Chuẩn bị features từ dữ liệu thống kê và kèo - PHẢI KHỚP VỚI 105 FEATURES TRONG TRAINING DATA
    
    Features phải giống hệt với những gì được dùng khi training model
    
    NOTE: Không bao gồm FTHG, FTAG, FTR vì đây là target/result columns được loại bỏ trong training
    
    Args:
        home_stats: Thống kê đội nhà
        away_stats: Thống kê đội khách
        odds_data: Dữ liệu kèo (optional)
    
    Returns:
        DataFrame chứa một dòng với đúng 105 features
    """
    import random
    
    features = {}
    
    # === MATCH BASIC INFO (simulated) ===
    # NOTE: KHÔNG BAO GỒM FTHG, FTAG vì model training loại bỏ chúng
    # features['FTHG'] = home_stats.get('goals_scored_avg', 1.5)  # REMOVED - not in training features
    # features['FTAG'] = away_stats.get('goals_scored_avg', 1.2)  # REMOVED - not in training features
    features['HTHG'] = home_stats.get('goals_scored_avg', 1.5) * 0.45  # Half-time estimate
    features['HTAG'] = away_stats.get('goals_scored_avg', 1.2) * 0.45
    
    # === SHOTS STATISTICS ===
    features['HS'] = home_stats.get('shots_per_game', 13)  # Home shots
    features['AS'] = away_stats.get('shots_against_per_game', 11)  # Away shots
    features['HST'] = home_stats.get('shots_on_target_per_game', 5)  # Home shots on target
    features['AST'] = away_stats.get('shots_on_target_against', 4)  # Away shots on target
    
    # === FOULS & CARDS ===
    features['HF'] = home_stats.get('fouls_per_game', 11)  # Home fouls
    features['AF'] = away_stats.get('fouls_per_game', 11)  # Away fouls
    features['HY'] = home_stats.get('yellow_cards_avg', 2)  # Home yellow cards
    features['AY'] = away_stats.get('yellow_cards_avg', 2)  # Away yellow cards
    features['HR'] = home_stats.get('red_cards_avg', 0.08)  # Home red cards
    features['AR'] = away_stats.get('red_cards_avg', 0.08)  # Away red cards
    
    # === CORNERS ===
    features['HC'] = home_stats.get('corners_per_game', 5)  # Home corners
    features['AC'] = away_stats.get('corners_against_per_game', 5)  # Away corners
    
    # === BETTING ODDS - 1X2 (Multiple bookmakers) ===
    # Default odds based on team strength
    home_strength = home_stats.get('goals_scored_avg', 1.5) / (home_stats.get('goals_conceded_avg', 1.0) + 0.5)
    away_strength = away_stats.get('goals_scored_avg', 1.2) / (away_stats.get('goals_conceded_avg', 1.2) + 0.5)
    
    total_strength = home_strength + away_strength
    implied_home_win = home_strength / total_strength * 0.55 + 0.25  # Home advantage
    implied_away_win = away_strength / total_strength * 0.45 + 0.15
    implied_draw = 1 - implied_home_win - implied_away_win
    
    # Convert to odds (with margin)
    margin = 1.05
    home_odd = (1 / implied_home_win) * margin if implied_home_win > 0 else 3.0
    draw_odd = (1 / implied_draw) * margin if implied_draw > 0 else 3.3
    away_odd = (1 / implied_away_win) * margin if implied_away_win > 0 else 3.5
    
    # Bet365 odds
    features['B365H'] = home_odd
    features['B365D'] = draw_odd
    features['B365A'] = away_odd
    
    # Other bookmakers (slight variations)
    for prefix in ['BW', 'IW', 'PS', 'WH', 'VC']:
        features[f'{prefix}H'] = home_odd * (0.95 + random.random() * 0.1)
        features[f'{prefix}D'] = draw_odd * (0.95 + random.random() * 0.1)
        features[f'{prefix}A'] = away_odd * (0.95 + random.random() * 0.1)
    
    # Max/Avg odds
    features['MaxH'] = home_odd * 1.05
    features['MaxD'] = draw_odd * 1.05
    features['MaxA'] = away_odd * 1.05
    features['AvgH'] = home_odd
    features['AvgD'] = draw_odd
    features['AvgA'] = away_odd
    
    # === OVER/UNDER 2.5 GOALS ===
    total_goals_avg = home_stats.get('goals_scored_avg', 1.5) + away_stats.get('goals_scored_avg', 1.2)
    over_prob = min(0.8, max(0.2, (total_goals_avg - 1.5) / 2.0))
    under_prob = 1 - over_prob
    
    over_odd = (1 / over_prob) * 1.05 if over_prob > 0 else 2.0
    under_odd = (1 / under_prob) * 1.05 if under_prob > 0 else 2.0
    
    features['B365>2.5'] = over_odd
    features['B365<2.5'] = under_odd
    features['P>2.5'] = over_odd * 0.98
    features['P<2.5'] = under_odd * 0.98
    features['Max>2.5'] = over_odd * 1.03
    features['Max<2.5'] = under_odd * 1.03
    features['Avg>2.5'] = over_odd
    features['Avg<2.5'] = under_odd
    
    # === ASIAN HANDICAP ===
    goal_diff = home_stats.get('goals_scored_avg', 1.5) - away_stats.get('goals_scored_avg', 1.2)
    handicap = round(goal_diff * 2) / 2  # Round to nearest 0.5
    
    features['AHh'] = handicap if odds_data is None else odds_data.get('handicap_value', handicap)
    features['B365AHH'] = 1.95  # Home team with handicap
    features['B365AHA'] = 1.95  # Away team with handicap
    features['PAHH'] = 1.93
    features['PAHA'] = 1.97
    features['MaxAHH'] = 2.00
    features['MaxAHA'] = 2.00
    features['AvgAHH'] = 1.95
    features['AvgAHA'] = 1.95
    
    # === CLOSING ODDS (similar to opening) ===
    for prefix in ['B365C', 'BWC', 'IWC', 'PSC', 'WHC', 'VCC']:
        features[f'{prefix}H'] = home_odd * (0.97 + random.random() * 0.06)
        features[f'{prefix}D'] = draw_odd * (0.97 + random.random() * 0.06)
        features[f'{prefix}A'] = away_odd * (0.97 + random.random() * 0.06)
    
    features['MaxCH'] = home_odd * 1.04
    features['MaxCD'] = draw_odd * 1.04
    features['MaxCA'] = away_odd * 1.04
    features['AvgCH'] = home_odd * 0.99
    features['AvgCD'] = draw_odd * 0.99
    features['AvgCA'] = away_odd * 0.99
    
    # === CLOSING OVER/UNDER ===
    features['B365C>2.5'] = over_odd * 0.99
    features['B365C<2.5'] = under_odd * 0.99
    features['PC>2.5'] = over_odd * 0.98
    features['PC<2.5'] = under_odd * 0.98
    features['MaxC>2.5'] = over_odd * 1.02
    features['MaxC<2.5'] = under_odd * 1.02
    features['AvgC>2.5'] = over_odd * 0.99
    features['AvgC<2.5'] = under_odd * 0.99
    
    # === CLOSING ASIAN HANDICAP ===
    features['AHCh'] = features['AHh']
    features['B365CAHH'] = 1.96
    features['B365CAHA'] = 1.94
    features['PCAHH'] = 1.94
    features['PCAHA'] = 1.96
    features['MaxCAHH'] = 2.01
    features['MaxCAHA'] = 1.99
    features['AvgCAHH'] = 1.96
    features['AvgCAHA'] = 1.94
    
    # === FORM & HISTORICAL ===
    features['home_form_last5'] = home_stats.get('home_form_last5', 9)
    features['away_form_last5'] = away_stats.get('away_form_last5', 6)
    features['home_goals_avg'] = home_stats.get('home_goals_avg', 1.8)
    features['away_goals_avg'] = away_stats.get('away_goals_avg', 1.2)
    features['home_goals_conceded_avg'] = home_stats.get('home_goals_conceded_avg', 1.0)
    features['away_goals_conceded_avg'] = away_stats.get('away_goals_conceded_avg', 1.3)
    features['h2h_home_wins'] = home_stats.get('h2h_home_wins', 2)
    features['h2h_draws'] = home_stats.get('h2h_draws', 1)
    features['h2h_away_wins'] = away_stats.get('h2h_away_wins', 2)
    
    # Tạo DataFrame
    df = pd.DataFrame([features])
    
    logger.info(f'Prepared {len(df.columns)} features for prediction')
    
    return df


def predict_match(home_stats: Dict[str, Any], away_stats: Dict[str, Any], 
                  odds_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Dự đoán kết quả kèo chấp cho trận đấu
    
    Args:
        home_stats: Thống kê đội nhà
        away_stats: Thống kê đội khách
        odds_data: Dữ liệu kèo (optional)
    
    Returns:
        Dictionary chứa dự đoán và các thông tin liên quan
    """
    # Load model
    model = load_model()
    
    if model is None:
        logger.warning('Model chưa được huấn luyện. Sử dụng dự đoán dựa trên thống kê cơ bản.')
        # Fallback: Dự đoán đơn giản dựa trên form
        return predict_without_model(home_stats, away_stats, odds_data)
    
    # Chuẩn bị features
    features_df = prepare_features(home_stats, away_stats, odds_data)
    
    logger.info(f'DEBUG: Features prepared - shape: {features_df.shape}, columns: {len(features_df.columns)}')
    logger.info(f'DEBUG: First 10 columns: {list(features_df.columns[:10])}')
    
    try:
        # Dự đoán
        # prediction = 1 nghĩa là đội nhà thắng kèo, 0 nghĩa là đội khách thắng kèo
        prediction = model.predict(features_df)[0]
        
        # Lấy xác suất (confidence)
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(features_df)[0]
            confidence = probabilities[int(prediction)]
        else:
            confidence = 0.6  # Default confidence nếu model không hỗ trợ predict_proba
        
        # Tạo khuyến nghị
        if prediction == 1:
            recommendation = f"Chọn {home_stats['team_name']} thắng kèo"
        else:
            recommendation = f"Chọn {away_stats['team_name']} thắng kèo"
        
        # Tạo tóm tắt thống kê
        stats_summary = generate_stats_summary(home_stats, away_stats)
        
        result = {
            'prediction': int(prediction),
            'confidence': float(confidence),
            'recommendation': recommendation,
            'stats_summary': stats_summary,
            'model_used': True
        }
        
        logger.info(f'Dự đoán: {recommendation} (Confidence: {confidence:.2%})')
        
        return result
        
    except Exception as e:
        logger.error(f'Lỗi khi dự đoán: {e}', exc_info=True)
        return predict_without_model(home_stats, away_stats, odds_data)


def predict_without_model(home_stats: Dict[str, Any], away_stats: Dict[str, Any],
                          odds_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Dự đoán đơn giản dựa trên thống kê khi không có model
    
    Dùng heuristic: So sánh form, goals scored/conceded
    """
    logger.info('Sử dụng phương pháp dự đoán đơn giản (không dùng ML model)')
    
    # Tính điểm cho mỗi đội
    home_score = 0
    away_score = 0
    
    # So sánh form
    home_points = home_stats.get('points_last_5', 0)
    away_points = away_stats.get('points_last_5', 0)
    if home_points > away_points:
        home_score += 2
    elif away_points > home_points:
        away_score += 2
    
    # So sánh goals scored
    home_goals = home_stats.get('goals_scored_avg', 0)
    away_goals = away_stats.get('goals_scored_avg', 0)
    if home_goals > away_goals:
        home_score += 1
    elif away_goals > home_goals:
        away_score += 1
    
    # So sánh goals conceded (càng ít càng tốt)
    home_conceded = home_stats.get('goals_conceded_avg', 999)
    away_conceded = away_stats.get('goals_conceded_avg', 999)
    if home_conceded < away_conceded:
        home_score += 1
    elif away_conceded < home_conceded:
        away_score += 1
    
    # Lợi thế sân nhà
    home_score += 1
    
    # Quyết định
    if home_score > away_score:
        prediction = 1
        recommendation = f"Chọn {home_stats['team_name']} thắng kèo"
        confidence = 0.55 + (home_score - away_score) * 0.05
    else:
        prediction = 0
        recommendation = f"Chọn {away_stats['team_name']} thắng kèo"
        confidence = 0.55 + (away_score - home_score) * 0.05
    
    confidence = min(confidence, 0.75)  # Cap ở 75%
    
    stats_summary = generate_stats_summary(home_stats, away_stats)
    
    return {
        'prediction': prediction,
        'confidence': confidence,
        'recommendation': recommendation,
        'stats_summary': stats_summary,
        'model_used': False
    }


def generate_stats_summary(home_stats: Dict[str, Any], away_stats: Dict[str, Any]) -> str:
    """
    Tạo chuỗi tóm tắt thống kê để hiển thị
    """
    home_name = home_stats['team_name']
    away_name = away_stats['team_name']
    
    summary = f"""
🏠 **{home_name}**
   • Goals/trận: {home_stats.get('goals_scored_avg', 0):.1f}
   • Thủng lưới/trận: {home_stats.get('goals_conceded_avg', 0):.1f}
   • Điểm 5 trận gần nhất: {home_stats.get('points_last_5', 0)}

✈️ **{away_name}**
   • Goals/trận: {away_stats.get('goals_scored_avg', 0):.1f}
   • Thủng lưới/trận: {away_stats.get('goals_conceded_avg', 0):.1f}
   • Điểm 5 trận gần nhất: {away_stats.get('points_last_5', 0)}
"""
    
    return summary.strip()


def main():
    """
    Test predictor với mock data
    """
    logger.info('=== TEST PREDICTOR ===')
    
    # Mock data
    home_stats = {
        'team_name': 'Arsenal',
        'goals_scored_avg': 2.1,
        'goals_conceded_avg': 0.9,
        'home_goals_avg': 2.5,
        'shots_per_game': 15.2,
        'possession_avg': 58.3,
        'points_last_5': 13
    }
    
    away_stats = {
        'team_name': 'Manchester United',
        'goals_scored_avg': 1.8,
        'goals_conceded_avg': 1.2,
        'away_goals_avg': 1.4,
        'shots_per_game': 12.8,
        'possession_avg': 52.1,
        'points_last_5': 10
    }
    
    odds_data = {
        'asian_handicap': 'Arsenal -0.5',
        'handicap_value': -0.5,
        'home_odds': 1.95,
        'away_odds': 1.95
    }
    
    # Dự đoán
    result = predict_match(home_stats, away_stats, odds_data)
    
    if result:
        print(f"\n{'='*50}")
        print(f"Khuyến nghị: {result['recommendation']}")
        print(f"Độ tin cậy: {result['confidence']:.1%}")
        print(f"Dùng ML Model: {'Có' if result['model_used'] else 'Không'}")
        print(f"{'='*50}")
        print(f"\nThống kê:\n{result['stats_summary']}")
    
    logger.info('=== KẾT THÚC TEST ===')


if __name__ == '__main__':
    main()
