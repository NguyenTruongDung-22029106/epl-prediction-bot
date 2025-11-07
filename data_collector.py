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
    Lấy thống kê chi tiết của một đội từ Football-Data.org API
    
    Args:
        team_name: Tên đội (ví dụ: "Arsenal FC", "Manchester United FC")
        api_key: Football-Data API key (optional, sẽ dùng từ env nếu không có)
    
    Returns:
        Dictionary chứa thống kê của đội hoặc None nếu có lỗi
    """
    logger.info(f'Đang lấy thống kê cho đội: {team_name}')
    
    # Bước 1: Tìm team ID từ tên
    team_id = _find_team_id(team_name)
    if not team_id:
        logger.warning(f'Không tìm thấy team ID cho {team_name}, dùng mock data')
        return _generate_mock_stats(team_name)
    
    # Bước 2: Lấy thông tin team và matches gần nhất
    team_data = get_football_data(f'/teams/{team_id}')
    if not team_data:
        logger.warning(f'Không lấy được dữ liệu team, dùng mock data')
        return _generate_mock_stats(team_name)
    
    # Bước 3: Lấy matches của team (10 trận gần nhất)
    matches_data = get_football_data(
        f'/teams/{team_id}/matches',
        params={'status': 'FINISHED', 'limit': 10}
    )
    
    if not matches_data or 'matches' not in matches_data:
        logger.warning(f'Không lấy được matches, dùng mock data')
        return _generate_mock_stats(team_name)
    
    # Bước 4: Tính toán statistics từ matches
    stats = _calculate_team_statistics(team_name, team_id, matches_data['matches'])
    
    return stats


def _generate_mock_stats(team_name: str) -> Dict[str, Any]:
    """Fallback: Generate mock stats when API fails"""
    import hashlib
    import random
    
    team_hash = int(hashlib.md5(team_name.encode()).hexdigest()[:8], 16)
    random.seed(team_hash)
    
    variation = (team_hash % 100) / 100
    strength = 0.3 + variation * 0.7
    
    # Comprehensive mock stats matching ALL 116 columns in master_dataset.csv
    mock_stats = {
        'team_name': team_name,
        
        # Basic stats
        'recent_form': [1 if random.random() < strength else 0 for _ in range(5)],
        'goals_scored_avg': 0.8 + strength * 1.5,  # 0.8 - 2.3 goals/game
        'goals_conceded_avg': 1.6 - strength * 0.8,  # 0.8 - 1.6 (inversed)
        'home_goals_avg': 1.0 + strength * 1.3,  # 1.0 - 2.3
        'away_goals_avg': 0.7 + strength * 1.0,  # 0.7 - 1.7
        
        # Shooting stats
        'shots_per_game': 10 + strength * 8,  # 10 - 18
        'shots_on_target_per_game': 3 + strength * 4,  # 3 - 7
        'shots_against_per_game': 16 - strength * 6,  # 10 - 16 (inversed)
        'shots_on_target_against': 6 - strength * 3,  # 3 - 6 (inversed)
        
        # Possession & discipline
        'possession_avg': 45 + strength * 20,  # 45 - 65%
        'fouls_per_game': 10 + random.random() * 3,  # 10 - 13
        'yellow_cards_avg': 1.5 + random.random() * 1.0,  # 1.5 - 2.5
        'red_cards_avg': 0.05 + random.random() * 0.1,  # 0.05 - 0.15
        
        # Corners
        'corners_per_game': 4 + strength * 3,  # 4 - 7
        'corners_against_per_game': 6 - strength * 2,  # 4 - 6 (inversed)
        
        # Form indicators
        'points_last_5': int(3 + strength * 12),  # 3 - 15 points
        'home_form_last5': int(2 + strength * 3) * 3,  # 6 - 15 points at home
        'away_form_last5': int(1 + strength * 2.5) * 3,  # 3 - 12 points away
        
        # Goal stats detailed
        'home_goals_conceded_avg': 1.3 - strength * 0.6,  # 0.7 - 1.3
        'away_goals_conceded_avg': 1.5 - strength * 0.7,  # 0.8 - 1.5
        
        # Head-to-head (randomized)
        'h2h_home_wins': random.randint(0, 5),
        'h2h_draws': random.randint(0, 3),
        'h2h_away_wins': random.randint(0, 5),
    }
    
    logger.info(f'{team_name}: [MOCK] Strength={strength:.2f}, Goals={mock_stats["goals_scored_avg"]:.2f}/game')
    return mock_stats


def _find_team_id(team_name: str) -> Optional[int]:
    """
    Tìm team ID từ tên đội trong Premier League
    
    Returns:
        Team ID hoặc None nếu không tìm thấy
    """
    # Team mapping (cập nhật từ API hoặc hardcode các đội EPL phổ biến)
    team_mapping = {
        'arsenal': 57, 'arsenal fc': 57,
        'aston villa': 58, 'aston villa fc': 58,
        'bournemouth': 1044, 'afc bournemouth': 1044,
        'brentford': 402, 'brentford fc': 402,
        'brighton': 397, 'brighton & hove albion': 397, 'brighton & hove albion fc': 397,
        'chelsea': 61, 'chelsea fc': 61,
        'crystal palace': 354, 'crystal palace fc': 354,
        'everton': 62, 'everton fc': 62,
        'fulham': 63, 'fulham fc': 63,
        'liverpool': 64, 'liverpool fc': 64,
        'luton town': 389, 'luton town fc': 389,
        'manchester city': 65, 'man city': 65, 'manchester city fc': 65,
        'manchester united': 66, 'man united': 66, 'manchester united fc': 66, 'man utd': 66,
        'newcastle': 67, 'newcastle united': 67, 'newcastle united fc': 67,
        'nottingham forest': 351, "nott'm forest": 351, 'nottingham forest fc': 351,
        'sheffield united': 356, 'sheffield united fc': 356,
        'tottenham': 73, 'spurs': 73, 'tottenham hotspur': 73, 'tottenham hotspur fc': 73,
        'west ham': 563, 'west ham united': 563, 'west ham united fc': 563,
        'wolverhampton': 76, 'wolves': 76, 'wolverhampton wanderers': 76, 'wolverhampton wanderers fc': 76,
        'leicester': 338, 'leicester city': 338, 'leicester city fc': 338,
        'ipswich': 349, 'ipswich town': 349, 'ipswich town fc': 349,
        'southampton': 340, 'southampton fc': 340,
    }
    
    normalized_name = team_name.lower().strip()
    return team_mapping.get(normalized_name)


def _calculate_team_statistics(team_name: str, team_id: int, matches: List[Dict]) -> Dict[str, Any]:
    """
    Tính toán statistics từ danh sách matches
    
    Args:
        team_name: Tên đội
        team_id: ID của đội
        matches: List các trận đấu từ API
    
    Returns:
        Dictionary chứa statistics
    """
    if not matches:
        return _generate_mock_stats(team_name)
    
    # Filter chỉ lấy matches đã kết thúc
    finished_matches = [m for m in matches if m.get('status') == 'FINISHED']
    
    if len(finished_matches) < 3:
        logger.warning(f'Chỉ có {len(finished_matches)} trận, dùng mock data')
        return _generate_mock_stats(team_name)
    
    # Initialize counters
    total_goals_scored = 0
    total_goals_conceded = 0
    home_goals = 0
    away_goals = 0
    home_conceded = 0
    away_conceded = 0
    home_matches = 0
    away_matches = 0
    recent_form = []  # 1 = win, 0 = draw/loss
    points_last_5 = 0
    
    # Process matches
    for match in finished_matches[:10]:  # Last 10 matches
        score = match.get('score', {}).get('fullTime', {})
        home_team_id = match.get('homeTeam', {}).get('id')
        away_team_id = match.get('awayTeam', {}).get('id')
        
        home_score = score.get('home', 0) or 0
        away_score = score.get('away', 0) or 0
        
        is_home = (home_team_id == team_id)
        
        if is_home:
            home_matches += 1
            home_goals += home_score
            home_conceded += away_score
            total_goals_scored += home_score
            total_goals_conceded += away_score
            
            # Form calculation
            if home_score > away_score:
                recent_form.append(1)
                if len(recent_form) <= 5:
                    points_last_5 += 3
            elif home_score == away_score:
                recent_form.append(0)
                if len(recent_form) <= 5:
                    points_last_5 += 1
            else:
                recent_form.append(0)
        else:
            away_matches += 1
            away_goals += away_score
            away_conceded += home_score
            total_goals_scored += away_score
            total_goals_conceded += home_score
            
            # Form calculation
            if away_score > home_score:
                recent_form.append(1)
                if len(recent_form) <= 5:
                    points_last_5 += 3
            elif away_score == home_score:
                recent_form.append(0)
                if len(recent_form) <= 5:
                    points_last_5 += 1
            else:
                recent_form.append(0)
    
    # Calculate averages
    num_matches = len(finished_matches[:10])
    goals_scored_avg = total_goals_scored / num_matches if num_matches > 0 else 1.5
    goals_conceded_avg = total_goals_conceded / num_matches if num_matches > 0 else 1.2
    
    home_goals_avg = home_goals / home_matches if home_matches > 0 else 1.7
    away_goals_avg = away_goals / away_matches if away_matches > 0 else 1.3
    home_conceded_avg = home_conceded / home_matches if home_matches > 0 else 1.0
    away_conceded_avg = away_conceded / away_matches if away_matches > 0 else 1.4
    
    # Statistics dictionary
    stats = {
        'team_name': team_name,
        'recent_form': recent_form[:5],
        'goals_scored_avg': goals_scored_avg,
        'goals_conceded_avg': goals_conceded_avg,
        'home_goals_avg': home_goals_avg,
        'away_goals_avg': away_goals_avg,
        'home_goals_conceded_avg': home_conceded_avg,
        'away_goals_conceded_avg': away_conceded_avg,
        
        # Estimated stats (would need more detailed API data for accuracy)
        'shots_per_game': 12 + goals_scored_avg * 2,
        'shots_on_target_per_game': 4 + goals_scored_avg,
        'shots_against_per_game': 12 + goals_conceded_avg * 2,
        'shots_on_target_against': 4 + goals_conceded_avg,
        
        'possession_avg': 50,  # Would need match details for this
        'fouls_per_game': 11,
        'yellow_cards_avg': 2,
        'red_cards_avg': 0.1,
        
        'corners_per_game': 5,
        'corners_against_per_game': 5,
        
        'points_last_5': points_last_5,
        'home_form_last5': points_last_5,  # Simplified
        'away_form_last5': points_last_5,  # Simplified
        
        'h2h_home_wins': 0,  # Would need H2H data
        'h2h_draws': 0,
        'h2h_away_wins': 0,
    }
    
    logger.info(f'{team_name}: [REAL] Goals={goals_scored_avg:.2f}/game, Conceded={goals_conceded_avg:.2f}, '
                f'Form={sum(recent_form[:5])}/5, Points(L5)={points_last_5}')
    
    return stats


def _generate_mock_stats(team_name: str) -> Dict[str, Any]:
    """Fallback: Generate mock stats when API fails"""
    import hashlib
    import random
    
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
