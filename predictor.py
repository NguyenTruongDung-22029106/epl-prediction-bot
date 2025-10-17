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
    Chuẩn bị features từ dữ liệu thống kê và kèo
    
    Features phải giống hệt với những gì được dùng khi training model
    
    Args:
        home_stats: Thống kê đội nhà
        away_stats: Thống kê đội khách
        odds_data: Dữ liệu kèo (optional)
    
    Returns:
        DataFrame chứa một dòng với tất cả features
    """
    features = {}
    
    # Feature từ đội nhà
    features['home_goals_scored_avg'] = home_stats.get('goals_scored_avg', 0)
    features['home_goals_conceded_avg'] = home_stats.get('goals_conceded_avg', 0)
    features['home_goals_avg'] = home_stats.get('home_goals_avg', 0)
    features['home_shots_per_game'] = home_stats.get('shots_per_game', 0)
    features['home_possession_avg'] = home_stats.get('possession_avg', 0)
    features['home_points_last_5'] = home_stats.get('points_last_5', 0)
    
    # Feature từ đội khách
    features['away_goals_scored_avg'] = away_stats.get('goals_scored_avg', 0)
    features['away_goals_conceded_avg'] = away_stats.get('goals_conceded_avg', 0)
    features['away_goals_avg'] = away_stats.get('away_goals_avg', 0)
    features['away_shots_per_game'] = away_stats.get('shots_per_game', 0)
    features['away_possession_avg'] = away_stats.get('possession_avg', 0)
    features['away_points_last_5'] = away_stats.get('points_last_5', 0)
    
    # Feature từ kèo (nếu có)
    if odds_data:
        features['handicap_value'] = odds_data.get('handicap_value', 0)
        features['home_odds'] = odds_data.get('home_odds', 2.0)
        features['away_odds'] = odds_data.get('away_odds', 2.0)
    else:
        features['handicap_value'] = 0
        features['home_odds'] = 2.0
        features['away_odds'] = 2.0
    
    # Tạo DataFrame
    df = pd.DataFrame([features])
    
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
