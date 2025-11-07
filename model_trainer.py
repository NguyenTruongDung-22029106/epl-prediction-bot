"""
model_trainer.py - Huấn luyện Machine Learning Model

Module này chứa toàn bộ logic để:
1. Load và chuẩn bị dữ liệu từ master_dataset.csv
2. Phân chia dữ liệu thành training và testing sets
3. Huấn luyện model với nhiều thuật toán khác nhau
4. Đánh giá performance
5. Lưu model tốt nhất
"""

import os
import logging
from typing import Tuple, Dict, Any
import pickle

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, mean_squared_error, mean_absolute_error, r2_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File paths
DATASET_PATH = 'master_dataset.csv'
MODEL_PATH = 'epl_prediction_model.pkl'
SCALER_PATH = 'scaler.pkl'
GOALS_MODEL_PATH = 'epl_goals_model.pkl'
GOALS_SCALER_PATH = 'goals_scaler.pkl'


def load_dataset() -> pd.DataFrame:
    """
    Load master dataset từ CSV
    
    Returns:
        DataFrame chứa dữ liệu
    """
    if not os.path.exists(DATASET_PATH):
        logger.error(f'Dataset không tồn tại: {DATASET_PATH}')
        logger.info('Vui lòng chạy data_collector.py trước để tạo dataset.')
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(DATASET_PATH)
        logger.info(f'Đã load dataset: {len(df)} trận đấu, {len(df.columns)} cột')
        return df
    except Exception as e:
        logger.error(f'Lỗi khi load dataset: {e}')
        return pd.DataFrame()


def prepare_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Chuẩn bị dữ liệu cho training
    
    Args:
        df: DataFrame chứa toàn bộ dữ liệu
    
    Returns:
        Tuple (X, y) - Features và target variable
    """
    logger.info('Đang chuẩn bị dữ liệu...')
    
    # Xác định target variable
    # Target: Kết quả kèo chấp Châu Á
    # 1 = Đội nhà thắng kèo, 0 = Đội khách thắng kèo hoặc hòa
    
    if 'handicap_result' not in df.columns:
        logger.warning('Cột handicap_result không tồn tại. Tạo target variable từ dữ liệu có sẵn.')
        
        # Giả sử có cột FTHG (Full Time Home Goals) và FTAG (Full Time Away Goals)
        if 'FTHG' in df.columns and 'FTAG' in df.columns:
            # Tính kết quả với handicap (giả sử handicap = 0 để đơn giản)
            # Trong thực tế, cần tính với handicap thực tế
            df['handicap_result'] = (df['FTHG'] > df['FTAG']).astype(int)
        else:
            logger.error('Không thể tạo target variable. Cần cột FTHG và FTAG.')
            return pd.DataFrame(), pd.Series()
    
    # Xác định features
    # Loại bỏ các cột không cần thiết
    exclude_columns = [
        'handicap_result',  # Target
        'Date', 'HomeTeam', 'AwayTeam',  # Metadata
        'FTHG', 'FTAG', 'FTR',  # Kết quả (không dùng làm feature)
        'Season'  # Metadata
    ]
    
    feature_columns = [col for col in df.columns if col not in exclude_columns]
    
    # Chỉ giữ các cột số
    numeric_columns = df[feature_columns].select_dtypes(include=[np.number]).columns.tolist()
    
    X = df[numeric_columns].copy()
    y = df['handicap_result'].copy()
    
    # Xử lý missing values
    X = X.fillna(X.mean())
    
    logger.info(f'Features: {len(X.columns)} cột')
    logger.info(f'Số lượng samples: {len(X)}')
    logger.info(f'Target distribution: {y.value_counts().to_dict()}')
    
    return X, y


def train_models(X_train, X_test, y_train, y_test) -> Dict[str, Any]:
    """
    Huấn luyện nhiều models và so sánh performance
    
    Args:
        X_train, X_test: Training và testing features
        y_train, y_test: Training và testing targets
    
    Returns:
        Dictionary chứa thông tin về models và kết quả
    """
    logger.info('Đang huấn luyện models...')
    
    # Chuẩn hóa dữ liệu
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Lưu scaler
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    logger.info(f'Đã lưu scaler vào {SCALER_PATH}')
    
    # Định nghĩa các models
    models = {
        'Random Forest': RandomForestClassifier(
                n_estimators=50,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        ),
        'Gradient Boosting': GradientBoostingClassifier(
                n_estimators=50,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        ),
        'Logistic Regression': LogisticRegression(
            max_iter=1000,
            random_state=42
        )
    }
    
    results = {}
    
    for name, model in models.items():
        logger.info(f'\n{"="*50}')
        logger.info(f'Đang huấn luyện: {name}')
        logger.info(f'{"="*50}')
        
        # Training
        model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred = model.predict(X_test_scaled)
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
        
        results[name] = {
            'model': model,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        # Log results
        logger.info(f'Accuracy: {accuracy:.4f}')
        logger.info(f'Precision: {precision:.4f}')
        logger.info(f'Recall: {recall:.4f}')
        logger.info(f'F1 Score: {f1:.4f}')
        logger.info(f'CV Score: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})')
        
        # Classification report
        logger.info('\nClassification Report:')
        logger.info(f'\n{classification_report(y_test, y_pred)}')
    
    return results


def save_best_model(results: Dict[str, Any]) -> None:
    """
    Lưu model tốt nhất dựa trên F1 score
    
    Args:
        results: Dictionary chứa kết quả của tất cả models
    """
    # Tìm model tốt nhất
    best_model_name = max(results, key=lambda x: results[x]['f1'])
    best_model = results[best_model_name]['model']
    best_f1 = results[best_model_name]['f1']
    
    logger.info(f'\n{"="*50}')
    logger.info(f'Model tốt nhất: {best_model_name}')
    logger.info(f'F1 Score: {best_f1:.4f}')
    logger.info(f'{"="*50}')
    
    # Lưu model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(best_model, f)
    
    logger.info(f'✅ Đã lưu model vào {MODEL_PATH}')
    # Lưu danh sách features dùng cho model chính
    try:
        with open('match_features.pkl', 'wb') as f:
            # best model was trained on X_train_scaled -> original columns preserved earlier in prepare_data
            # We can reload dataset and re-run prepare_data quickly to capture columns
            df = load_dataset()
            if not df.empty:
                X_tmp, _y_tmp = prepare_data(df)
                pickle.dump(X_tmp.columns.tolist(), f)
                logger.info(f'Đã lưu danh sách features (match) vào match_features.pkl')
    except Exception as e:
        logger.warning(f'Không thể lưu danh sách features match: {e}')


def prepare_goals_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Chuẩn bị dữ liệu để dự đoán tổng số bàn thắng
    
    Args:
        df: DataFrame chứa toàn bộ dữ liệu
    
    Returns:
        Tuple (X, y) - Features và total goals
    """
    logger.info('Đang chuẩn bị dữ liệu cho dự đoán tổng bàn thắng...')
    
    # Target: Tổng số bàn thắng
    if 'FTHG' not in df.columns or 'FTAG' not in df.columns:
        logger.error('Không tìm thấy cột FTHG hoặc FTAG')
        return pd.DataFrame(), pd.Series()
    
    df['TotalGoals'] = df['FTHG'] + df['FTAG']
    
    # Xác định features
    exclude_columns = [
        'TotalGoals', 'FTHG', 'FTAG', 'FTR', 'HTHG', 'HTAG', 'HTR',
        'Date', 'HomeTeam', 'AwayTeam', 'Season', 'handicap_result'
    ]
    
    feature_columns = [col for col in df.columns if col not in exclude_columns]
    numeric_columns = df[feature_columns].select_dtypes(include=[np.number]).columns.tolist()
    
    X = df[numeric_columns].copy()
    y = df['TotalGoals'].copy()
    
    # Xử lý missing values
    X = X.fillna(X.mean())
    
    logger.info(f'Features: {len(X.columns)} cột')
    logger.info(f'Số lượng samples: {len(X)}')
    logger.info(f'Tổng bàn - Mean: {y.mean():.2f}, Median: {y.median():.2f}, Std: {y.std():.2f}')
    
    return X, y


def train_goals_models(X_train, X_test, y_train, y_test) -> Dict[str, Any]:
    """
    Huấn luyện models để dự đoán tổng số bàn thắng
    
    Args:
        X_train, X_test: Training và testing features
        y_train, y_test: Training và testing total goals
    
    Returns:
        Dictionary chứa thông tin về models và kết quả
    """
    logger.info('Đang huấn luyện models dự đoán tổng bàn thắng...')
    
    # Chuẩn hóa dữ liệu
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Lưu scaler
    with open(GOALS_SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    logger.info(f'Đã lưu goals scaler vào {GOALS_SCALER_PATH}')
    
    # Định nghĩa các models (regression)
    models = {
        'Random Forest': RandomForestRegressor(
                n_estimators=50,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        ),
        'Gradient Boosting': GradientBoostingRegressor(
                n_estimators=50,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        ),
        'Linear Regression': LinearRegression()
    }
    
    results = {}
    
    for name, model in models.items():
        logger.info(f'\n{"="*50}')
        logger.info(f'Đang huấn luyện: {name}')
        logger.info(f'{"="*50}')
        
        # Training
        model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred = model.predict(X_test_scaled)
        
        # Metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        results[name] = {
            'model': model,
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2': r2
        }
        
        # Log results
        logger.info(f'MSE: {mse:.4f}')
        logger.info(f'RMSE: {rmse:.4f}')
        logger.info(f'MAE: {mae:.4f}')
        logger.info(f'R² Score: {r2:.4f}')
        
        # Sample predictions
        logger.info('\nMẫu dự đoán (5 trận đầu):')
        for i in range(min(5, len(y_test))):
            logger.info(f'Thực tế: {y_test.iloc[i]:.1f}, Dự đoán: {y_pred[i]:.1f}')
    
    return results


def save_best_goals_model(results: Dict[str, Any]) -> None:
    """
    Lưu model tốt nhất dự đoán tổng bàn (dựa trên MAE thấp nhất)
    
    Args:
        results: Dictionary chứa kết quả của tất cả models
    """
    # Tìm model tốt nhất (MAE thấp nhất)
    best_model_name = min(results, key=lambda x: results[x]['mae'])
    best_model = results[best_model_name]['model']
    best_mae = results[best_model_name]['mae']
    best_r2 = results[best_model_name]['r2']
    
    logger.info(f'\n{"="*50}')
    logger.info(f'Model dự đoán tổng bàn tốt nhất: {best_model_name}')
    logger.info(f'MAE: {best_mae:.4f}')
    logger.info(f'R² Score: {best_r2:.4f}')
    logger.info(f'{"="*50}')
    
    # Lưu model
    with open(GOALS_MODEL_PATH, 'wb') as f:
        pickle.dump(best_model, f)
    
    logger.info(f'✅ Đã lưu goals model vào {GOALS_MODEL_PATH}')
    # Lưu danh sách features dùng cho goals model
    try:
        df = load_dataset()
        if not df.empty:
            Xg_tmp, yg_tmp = prepare_goals_data(df)
            with open('goals_features.pkl', 'wb') as f:
                pickle.dump(Xg_tmp.columns.tolist(), f)
            logger.info('Đã lưu danh sách features (goals) vào goals_features.pkl')
    except Exception as e:
        logger.warning(f'Không thể lưu danh sách features goals: {e}')


def create_mock_dataset() -> pd.DataFrame:
    """
    Tạo mock dataset để test khi chưa có dữ liệu thực
    
    Returns:
        DataFrame chứa mock data
    """
    logger.info('Tạo mock dataset để test...')
    
    np.random.seed(42)
    n_samples = 500
    
    data = {
        # Features đội nhà
        'home_goals_scored_avg': np.random.uniform(1.0, 2.5, n_samples),
        'home_goals_conceded_avg': np.random.uniform(0.8, 2.0, n_samples),
        'home_goals_avg': np.random.uniform(1.2, 2.8, n_samples),
        'home_shots_per_game': np.random.uniform(10, 18, n_samples),
        'home_possession_avg': np.random.uniform(45, 65, n_samples),
        'home_points_last_5': np.random.randint(3, 16, n_samples),
        
        # Features đội khách
        'away_goals_scored_avg': np.random.uniform(1.0, 2.5, n_samples),
        'away_goals_conceded_avg': np.random.uniform(0.8, 2.0, n_samples),
        'away_goals_avg': np.random.uniform(0.8, 2.2, n_samples),
        'away_shots_per_game': np.random.uniform(9, 16, n_samples),
        'away_possession_avg': np.random.uniform(40, 60, n_samples),
        'away_points_last_5': np.random.randint(3, 16, n_samples),
        
        # Features kèo
        'handicap_value': np.random.choice([-1.0, -0.5, 0, 0.5, 1.0], n_samples),
        'home_odds': np.random.uniform(1.7, 2.2, n_samples),
        'away_odds': np.random.uniform(1.7, 2.2, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Tạo target variable dựa trên logic đơn giản
    # Đội nhà thắng kèo nếu: goals_scored_avg cao hơn và form tốt hơn
    df['handicap_result'] = (
        (df['home_goals_scored_avg'] > df['away_goals_scored_avg']) & 
        (df['home_points_last_5'] > df['away_points_last_5'])
    ).astype(int)
    
    # Thêm một chút noise
    noise_mask = np.random.random(n_samples) < 0.2  # 20% noise
    df.loc[noise_mask, 'handicap_result'] = 1 - df.loc[noise_mask, 'handicap_result']
    
    return df


def main():
    """
    Chạy toàn bộ quy trình training
    """
    logger.info('=== BẮT ĐẦU TRAINING MODEL ===\n')
    
    # Load dataset
    df = load_dataset()
    
    # Nếu không có dataset thực, dùng mock data
    if df.empty:
        logger.warning('Không tìm thấy dataset thực. Sử dụng mock data để demo.')
        df = create_mock_dataset()
        logger.info(f'Đã tạo mock dataset với {len(df)} samples')
    
    if df.empty:
        logger.error('Không có dữ liệu để training.')
        return
    
    # Prepare data
    X, y = prepare_data(df)
    
    if X.empty or y.empty:
        logger.error('Không thể chuẩn bị dữ liệu.')
        return
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f'\nPhân chia dữ liệu:')
    logger.info(f'Training set: {len(X_train)} samples')
    logger.info(f'Testing set: {len(X_test)} samples\n')
    
    # Train models
    results = train_models(X_train, X_test, y_train, y_test)
    
    # Save best model
    save_best_model(results)
    
    # === TRAIN MODEL DỰ ĐOÁN TỔNG BÀN THẮNG ===
    logger.info('\n\n=== BẮT ĐẦU TRAINING MODEL DỰ ĐOÁN TỔNG BÀN THẮNG ===\n')
    
    # Prepare goals data
    X_goals, y_goals = prepare_goals_data(df)
    
    if X_goals.empty or y_goals.empty:
        logger.error('Không thể chuẩn bị dữ liệu cho tổng bàn thắng.')
    else:
        # Split data
        X_train_g, X_test_g, y_train_g, y_test_g = train_test_split(
            X_goals, y_goals, test_size=0.2, random_state=42
        )
        
        logger.info(f'Phân chia dữ liệu tổng bàn:')
        logger.info(f'Training set: {len(X_train_g)} samples')
        logger.info(f'Testing set: {len(X_test_g)} samples\n')
        
        # Train goals models
        goals_results = train_goals_models(X_train_g, X_test_g, y_train_g, y_test_g)
        
        # Save best goals model
        save_best_goals_model(goals_results)
    
    logger.info('\n=== KẾT THÚC TRAINING ===')
    logger.info('Cả 2 models đã sẵn sàng:')
    logger.info(f'  ✅ Model dự đoán kết quả: {MODEL_PATH}')
    logger.info(f'  ✅ Model dự đoán tổng bàn: {GOALS_MODEL_PATH}')


if __name__ == '__main__':
    main()
