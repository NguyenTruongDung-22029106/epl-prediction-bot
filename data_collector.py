"""
data_collector.py - Thu thập dữ liệu từ API và xây dựng dataset

Module này chứa các hàm để:
1. Thu thập dữ liệu thống kê từ Football-Data.org
2. Thu thập dữ liệu kèo từ The Odds API
3. Xử lý và làm sạch dữ liệu
4. Feature engineering (tạo các đặc trưng từ dữ liệu thô)
5. Lưu dữ liệu vào CSV để huấn luyện model
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Keys
FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

# API Endpoints
FOOTBALL_DATA_BASE_URL = 'https://api.football-data.org/v4'
ODDS_API_BASE_URL = 'https://api.the-odds-api.com/v4'

PREMIER_LEAGUE_ID = 'PL'


def get_football_data(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """
    Gọi API của Football-Data.org
    """
    headers = {'X-Auth-Token': FOOTBALL_DATA_API_KEY}
    url = f"{FOOTBALL_DATA_BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi khi gọi Football-Data API: {e}")
        return None


def get_team_stats(team_name: str, api_key: str = None) -> Optional[Dict[str, Any]]:
    """
    Lấy thống kê chi tiết của một đội
    
    Args:
        team_name: Tên đội (ví dụ: "Arsenal", "Manchester United")
        api_key: Football-Data API key (optional, sẽ dùng từ env nếu không có)
    
    Returns:
        Dictionary chứa thống kê của đội hoặc None nếu có lỗi
    """
    # Đây là placeholder - trong thực tế sẽ gọi API và xử lý dữ liệu
    # Để đơn giản, trả về mock data để bot có thể chạy được
    
    logger.info(f'Đang lấy thống kê cho đội: {team_name}')
    
    # TODO: Implement API call để lấy dữ liệu thực
    # 1. Tìm team ID từ tên
    # 2. Lấy các trận đấu gần nhất
    # 3. Tính toán các thống kê: form, goals scored/conceded, etc.
    
    # Mock data tạm thời
    mock_stats = {
        'team_name': team_name,
        'recent_form': [1, 1, 0, 1, 0],  # W, W, D, W, D trong 5 trận gần nhất
        'goals_scored_avg': 1.8,
        'goals_conceded_avg': 1.2,
        'home_goals_avg': 2.1 if 'home' in team_name.lower() else 1.5,
        'away_goals_avg': 1.5 if 'away' in team_name.lower() else 1.1,
        'shots_per_game': 13.5,
        'shots_on_target_per_game': 5.2,
        'possession_avg': 54.3,
        'points_last_5': sum([1, 1, 0, 1, 0]) * 3 + [1, 1, 0, 1, 0].count(0),
    }
    
    return mock_stats


def get_odds_data(home_team: str, away_team: str, api_key: str = None) -> Optional[Dict[str, Any]]:
    """
    Lấy dữ liệu kèo cược từ The Odds API
    
    Args:
        home_team: Tên đội nhà
        away_team: Tên đội khách
        api_key: The Odds API key (optional)
    
    Returns:
        Dictionary chứa thông tin kèo hoặc None nếu có lỗi
    """
    logger.info(f'Đang lấy kèo cho trận: {home_team} vs {away_team}')
    
    # TODO: Implement API call để lấy kèo thực
    # Lưu ý: The Odds API chỉ có 500 requests/tháng miễn phí
    # Cần implement caching để tránh vượt quá giới hạn
    
    # Mock data tạm thời
    mock_odds = {
        'home_team': home_team,
        'away_team': away_team,
        'asian_handicap': f'{home_team} -0.5',  # Đội nhà chấp 0.5 bàn
        'handicap_value': -0.5,
        'home_odds': 1.95,
        'away_odds': 1.95,
        'timestamp': datetime.now().isoformat()
    }
    
    return mock_odds


def collect_historical_stats(seasons: List[str] = None) -> pd.DataFrame:
    """
    Thu thập dữ liệu thống kê lịch sử từ Football-Data.org
    
    Args:
        seasons: Danh sách các mùa giải (ví dụ: ['2021', '2022', '2023'])
    
    Returns:
        DataFrame chứa dữ liệu thống kê lịch sử
    """
    if seasons is None:
        # Mặc định lấy 3 mùa gần nhất
        current_year = datetime.now().year
        seasons = [str(year) for year in range(current_year - 3, current_year)]
    
    logger.info(f'Đang thu thập dữ liệu cho các mùa: {seasons}')
    
    all_matches = []
    
    for season in seasons:
        logger.info(f'Đang xử lý mùa giải {season}...')
        
        # Gọi API để lấy tất cả trận đấu của mùa
        # Endpoint: /competitions/PL/matches?season=2023
        # TODO: Implement actual API call
        
        # Mock data
        time.sleep(0.5)  # Tránh rate limit
        
    df = pd.DataFrame(all_matches)
    
    if df.empty:
        logger.warning('Không có dữ liệu nào được thu thập')
        return df
    
    # Lưu vào file CSV
    output_file = 'historical_stats.csv'
    df.to_csv(output_file, index=False)
    logger.info(f'Đã lưu {len(df)} trận đấu vào {output_file}')
    
    return df


def collect_historical_odds() -> pd.DataFrame:
    """
    Thu thập dữ liệu kèo lịch sử
    
    Vì The Odds API không cung cấp dữ liệu lịch sử miễn phí,
    chúng ta sẽ tải dữ liệu từ football-data.co.uk
    
    Returns:
        DataFrame chứa dữ liệu kèo lịch sử
    """
    logger.info('Đang thu thập dữ liệu kèo lịch sử từ football-data.co.uk...')
    
    # URLs cho các mùa giải gần đây
    # Ví dụ: https://www.football-data.co.uk/mmz4281/2324/E0.csv
    base_url = 'https://www.football-data.co.uk/mmz4281'
    seasons = ['2122', '2223', '2324']  # 2021-22, 2022-23, 2023-24
    
    all_data = []
    
    for season in seasons:
        url = f'{base_url}/{season}/E0.csv'  # E0 = Premier League
        logger.info(f'Đang tải: {url}')
        
        try:
            df = pd.read_csv(url)
            df['Season'] = season
            all_data.append(df)
            logger.info(f'Đã tải {len(df)} trận đấu từ mùa {season}')
            time.sleep(1)  # Lịch sự với server
        except Exception as e:
            logger.error(f'Lỗi khi tải dữ liệu mùa {season}: {e}')
    
    if not all_data:
        logger.warning('Không thể tải dữ liệu kèo lịch sử')
        return pd.DataFrame()
    
    # Gộp tất cả dữ liệu
    df_odds = pd.concat(all_data, ignore_index=True)
    
    # Lưu vào file
    output_file = 'historical_odds.csv'
    df_odds.to_csv(output_file, index=False)
    logger.info(f'Đã lưu {len(df_odds)} trận đấu vào {output_file}')
    
    return df_odds


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature Engineering - Tạo các đặc trưng từ dữ liệu thô
    
    Các feature quan trọng:
    - Phong độ gần đây (last 5 matches)
    - Sức mạnh tấn công/phòng ngự
    - Form sân nhà/sân khách
    - Head-to-head history
    - Vị trí trên bảng xếp hạng
    
    Args:
        df: DataFrame chứa dữ liệu thô
    
    Returns:
        DataFrame với các feature đã được tạo
    """
    logger.info('Đang thực hiện feature engineering...')
    
    # TODO: Implement các feature engineering strategies
    # 1. Calculate rolling averages (goals, shots, possession)
    # 2. Calculate form indicators (points in last N games)
    # 3. Home/Away performance metrics
    # 4. Head-to-head statistics
    # 5. League position and points
    
    # Placeholder - trong thực tế sẽ tính toán từ dữ liệu thực
    df['home_form_last5'] = 0  # Sẽ tính từ 5 trận gần nhất
    df['away_form_last5'] = 0
    df['home_goals_avg'] = 0
    df['away_goals_avg'] = 0
    df['home_goals_conceded_avg'] = 0
    df['away_goals_conceded_avg'] = 0
    df['h2h_home_wins'] = 0  # Head-to-head wins
    df['h2h_draws'] = 0
    df['h2h_away_wins'] = 0
    
    logger.info(f'Đã tạo {len(df.columns)} features')
    
    return df


def create_master_dataset() -> pd.DataFrame:
    """
    Tạo master dataset bằng cách gộp dữ liệu thống kê và kèo
    
    Returns:
        DataFrame chứa dataset hoàn chỉnh sẵn sàng cho training
    """
    logger.info('Đang tạo master dataset...')
    
    # Bước 1: Thu thập dữ liệu thống kê
    # df_stats = collect_historical_stats()
    
    # Bước 2: Thu thập dữ liệu kèo
    df_odds = collect_historical_odds()
    
    if df_odds.empty:
        logger.error('Không có dữ liệu kèo. Không thể tạo master dataset.')
        return pd.DataFrame()
    
    # Bước 3: Merge dữ liệu
    # TODO: Merge df_stats và df_odds dựa trên date, home_team, away_team
    
    # Bước 4: Feature engineering
    df_master = feature_engineering(df_odds)
    
    # Bước 5: Tạo target variable (kết quả kèo chấp)
    # Asian Handicap result: 1 = Home wins handicap, 0 = Away wins/draw
    if 'FTHG' in df_master.columns and 'FTAG' in df_master.columns:
        # FTHG = Full Time Home Goals, FTAG = Full Time Away Goals
        # Giả sử có cột handicap value
        # df_master['handicap_result'] = ...
        pass
    
    # Bước 6: Lưu master dataset
    output_file = 'master_dataset.csv'
    df_master.to_csv(output_file, index=False)
    logger.info(f'Đã lưu master dataset với {len(df_master)} trận đấu vào {output_file}')
    
    return df_master


def main():
    """
    Chạy toàn bộ quy trình thu thập dữ liệu
    """
    logger.info('=== BẮT ĐẦU THU THẬP DỮ LIỆU ===')
    
    if not FOOTBALL_DATA_API_KEY:
        logger.warning('FOOTBALL_DATA_API_KEY chưa được thiết lập')
    
    if not ODDS_API_KEY:
        logger.warning('ODDS_API_KEY chưa được thiết lập')
    
    # Tạo master dataset
    df = create_master_dataset()
    
    if not df.empty:
        logger.info(f'✅ Hoàn thành! Dataset có {len(df)} trận đấu và {len(df.columns)} features')
        logger.info(f'Các cột: {list(df.columns)}')
    else:
        logger.error('❌ Không thể tạo dataset')
    
    logger.info('=== KẾT THÚC THU THẬP DỮ LIỆU ===')


if __name__ == '__main__':
    main()
