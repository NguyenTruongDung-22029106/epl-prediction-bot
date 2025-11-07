"""
refit_models.py - Refit các models hiện có với DataFrame để preserve feature names
Điều này giúp loại bỏ cảnh báo sklearn về feature names mismatch.
"""

import pickle
import logging
import pandas as pd
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def refit_with_feature_names():
    """
    Load models đã lưu, refit với DataFrame thay vì numpy array để giữ feature names.
    """
    # 1. Load dataset
    try:
        df = pd.read_csv('master_dataset.csv')
        logger.info(f'Loaded dataset: {len(df)} rows')
    except Exception as e:
        logger.error(f'Cannot load dataset: {e}')
        return
    
    # 2. Prepare data (same logic as model_trainer.py)
    exclude_columns = [
        'handicap_result', 'Date', 'HomeTeam', 'AwayTeam',
        'FTHG', 'FTAG', 'FTR', 'Season'
    ]
    
    if 'handicap_result' not in df.columns:
        if 'FTHG' in df.columns and 'FTAG' in df.columns:
            df['handicap_result'] = (df['FTHG'] > df['FTAG']).astype(int)
        else:
            logger.error('Cannot create target variable')
            return
    
    feature_columns = [col for col in df.columns if col not in exclude_columns]
    numeric_columns = df[feature_columns].select_dtypes(include=['number']).columns.tolist()
    
    X = df[numeric_columns].copy().fillna(0)
    y = df['handicap_result'].copy()
    
    # 3. Load existing models
    try:
        with open('epl_prediction_model.pkl', 'rb') as f:
            match_model = pickle.load(f)
        logger.info('Loaded match prediction model')
    except Exception as e:
        logger.error(f'Cannot load match model: {e}')
        return
    
    try:
        with open('match_features.pkl', 'rb') as f:
            match_features = pickle.load(f)
        logger.info(f'Loaded match features: {len(match_features)} columns')
    except Exception:
        match_features = X.columns.tolist()
    
    # Align X to match saved features
    for col in match_features:
        if col not in X.columns:
            X[col] = 0.0
    X = X[match_features]
    
    # 4. Scale with DataFrame (preserve feature names)
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(
        scaler.fit_transform(X),
        columns=X.columns,
        index=X.index
    )
    
    # 5. Refit match model
    logger.info('Refitting match prediction model with feature names...')
    match_model.fit(X_scaled, y)
    
    # Save refitted model
    with open('epl_prediction_model.pkl', 'wb') as f:
        pickle.dump(match_model, f)
    with open('scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    logger.info('✅ Saved refitted match model and scaler')
    
    # 6. Refit goals model if exists
    try:
        with open('epl_goals_model.pkl', 'rb') as f:
            goals_model = pickle.load(f)
        with open('goals_features.pkl', 'rb') as f:
            goals_features = pickle.load(f)
        logger.info(f'Loaded goals model with {len(goals_features)} features')
        
        # Prepare goals target
        if 'FTHG' in df.columns and 'FTAG' in df.columns:
            y_goals = (df['FTHG'] + df['FTAG']).copy()
            
            # Align features
            X_goals = X.copy()
            for col in goals_features:
                if col not in X_goals.columns:
                    X_goals[col] = 0.0
            X_goals = X_goals[goals_features]
            
            # Scale
            goals_scaler = StandardScaler()
            X_goals_scaled = pd.DataFrame(
                goals_scaler.fit_transform(X_goals),
                columns=X_goals.columns,
                index=X_goals.index
            )
            
            # Refit
            logger.info('Refitting goals model with feature names...')
            goals_model.fit(X_goals_scaled, y_goals)
            
            # Save
            with open('epl_goals_model.pkl', 'wb') as f:
                pickle.dump(goals_model, f)
            with open('goals_scaler.pkl', 'wb') as f:
                pickle.dump(goals_scaler, f)
            logger.info('✅ Saved refitted goals model and scaler')
        else:
            logger.warning('Cannot refit goals model: missing FTHG/FTAG')
    except Exception as e:
        logger.warning(f'Goals model refit skipped: {e}')
    
    logger.info('🎉 Refit complete! Models now have feature names and warnings should be gone.')

if __name__ == '__main__':
    refit_with_feature_names()
