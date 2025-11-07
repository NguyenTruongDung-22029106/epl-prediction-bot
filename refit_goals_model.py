"""refit_goals_model.py - Refit chuyên biệt cho model tổng bàn thắng với calibration metadata.

Steps:
1. Load master_dataset.csv
2. Build goals feature matrix (exclude leakage targets)
3. Train regression models; choose best by MAE
4. Save best model, scaler, feature list, and calibration file (goals_calibration.pkl)
"""
import os
import pickle
import logging
from typing import Dict, Any

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATASET_PATH = 'master_dataset.csv'
GOALS_MODEL_PATH = 'epl_goals_model.pkl'
GOALS_SCALER_PATH = 'goals_scaler.pkl'
GOALS_FEATURES_PATH = 'goals_features.pkl'
GOALS_CALIBRATION_PATH = 'goals_calibration.pkl'

EXCLUDE_COLS = {
    'FTHG', 'FTAG', 'FTR', 'HTHG', 'HTAG', 'HTR', 'Date', 'HomeTeam', 'AwayTeam', 'Season', 'handicap_result'
}

def load_dataset() -> pd.DataFrame:
    if not os.path.exists(DATASET_PATH):
        logger.error(f'Dataset not found: {DATASET_PATH}')
        return pd.DataFrame()
    df = pd.read_csv(DATASET_PATH)
    logger.info(f'Loaded dataset: {len(df)} rows, {len(df.columns)} columns')
    return df


def build_goals_data(df: pd.DataFrame):
    if 'FTHG' not in df.columns or 'FTAG' not in df.columns:
        logger.error('Missing FTHG/FTAG columns for total goals target.')
        return pd.DataFrame(), pd.Series()
    df = df.copy()
    df['TotalGoals'] = df['FTHG'] + df['FTAG']
    feature_cols = [c for c in df.columns if c not in EXCLUDE_COLS and c != 'TotalGoals']
    num_cols = df[feature_cols].select_dtypes(include=['number']).columns.tolist()
    X = df[num_cols].fillna(df[num_cols].mean())
    y = df['TotalGoals'].astype(float)
    logger.info(f'Goals features: {len(X.columns)} numeric columns')
    logger.info(f'Target stats -> mean: {y.mean():.2f}, std: {y.std():.2f}, min: {y.min():.1f}, max: {y.max():.1f}')
    return X, y


def train_models(X_train, X_val, y_train, y_val) -> Dict[str, Dict[str, Any]]:
    scaler = StandardScaler()
    # Fit scaler and wrap scaled arrays back into DataFrame to preserve feature names
    X_train_s_arr = scaler.fit_transform(X_train)
    X_val_s_arr = scaler.transform(X_val)
    X_train_s = pd.DataFrame(X_train_s_arr, columns=X_train.columns, index=X_train.index)
    X_val_s = pd.DataFrame(X_val_s_arr, columns=X_val.columns, index=X_val.index)

    models = {
        'RandomForest': RandomForestRegressor(n_estimators=200, max_depth=12, min_samples_split=4, random_state=42),
        'GradientBoosting': GradientBoostingRegressor(n_estimators=150, learning_rate=0.07, max_depth=4, random_state=42),
        'LinearRegression': LinearRegression(),
    }
    results = {}
    for name, model in models.items():
        logger.info(f'Training {name} ...')
        model.fit(X_train_s, y_train)
        preds = model.predict(X_val_s)
        mae = mean_absolute_error(y_val, preds)
        rmse = mean_squared_error(y_val, preds) ** 0.5
        r2 = r2_score(y_val, preds)
        results[name] = {
            'model': model,
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'preds': preds,
            'scaler': scaler
        }
        logger.info(f'{name}: MAE={mae:.3f} RMSE={rmse:.3f} R2={r2:.3f}')
    return results


def choose_and_save(results: Dict[str, Dict[str, Any]], X: pd.DataFrame, y_val: pd.Series):
    best_name = min(results.keys(), key=lambda k: results[k]['mae'])
    best = results[best_name]
    model = best['model']
    scaler = best['scaler']
    preds = best['preds']
    # Derive shrink factor for calibration
    pred_mean = float(np.mean(preds))
    true_mean = float(y_val.mean())
    pred_std = float(np.std(preds))
    true_std = float(y_val.std())
    if pred_std > 0:
        shrink_factor = min(0.85, max(0.35, true_std / pred_std))
    else:
        shrink_factor = 0.6
    league_mean = true_mean
    calibration = {
        'league_mean': league_mean,
        'shrink_factor': shrink_factor,
        'pred_mean': pred_mean,
        'true_mean': true_mean,
        'pred_std': pred_std,
        'true_std': true_std,
        'model': best_name
    }

    # Save artifacts
    with open(GOALS_MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(GOALS_SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    with open(GOALS_FEATURES_PATH, 'wb') as f:
        pickle.dump(list(X.columns), f)
    with open(GOALS_CALIBRATION_PATH, 'wb') as f:
        pickle.dump(calibration, f)
    logger.info(f'Saved best goals model: {best_name} (MAE={best["mae"]:.3f})')
    logger.info(f'Calibration -> league_mean={league_mean:.2f} shrink_factor={shrink_factor:.2f}')


def main():
    df = load_dataset()
    if df.empty:
        logger.error('Dataset empty; aborting refit.')
        return
    X, y = build_goals_data(df)
    if X.empty:
        logger.error('No features built; aborting.')
        return
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    results = train_models(X_train, X_val, y_train, y_val)
    choose_and_save(results, X, y_val)
    logger.info('Goals model refit complete.')

if __name__ == '__main__':
    main()
