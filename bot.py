"""
bot.py - Bot "Nhà Tiên tri Ngoại Hạng Anh" ⚽️🤖

Bot Discord có khả năng:
1. Hiển thị lịch thi đấu Ngoại Hạng Anh
2. Phân tích và đưa ra khuyến nghị về kèo chấp Châu Á dựa trên Machine Learning

Lệnh:
- !lichdau: Hiển thị lịch thi đấu 7 ngày tới
- !phantich <Đội A> vs <Đội B>: Phân tích trận đấu và đưa ra khuyến nghị
- !help: Hiển thị hướng dẫn sử dụng
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import discord
from discord.ext import commands
from dotenv import load_dotenv
import requests

# Import các module tự tạo
from predictor import predict_match, predict_total_goals, predict_correct_score, predict_multiline_ou
from data_collector import get_team_stats, get_odds_data
from prediction_tracker import log_prediction, get_stats
from ai_helper import generate_ai_insight

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Keys
# Support multiple env var names for compatibility with different hosts (Render, local)
def _get_raw_token() -> Optional[str]:
    for key in ['DISCORD_TOKEN', 'DISCORD_BOT_TOKEN', 'BOT_TOKEN']:
        val = os.getenv(key)
        if val:
            logger.info(f"Loaded Discord token from env: {key}")
            return val
    return None

def _sanitize_token(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    t = token.strip().strip('"').strip("'")
    # Remove common prefixes that users accidentally include
    for prefix in ['Bot ', 'Bearer ']:
        if t.startswith(prefix):
            t = t[len(prefix):]
    return t

def _mask_token(token: Optional[str]) -> str:
    if not token:
        return 'None'
    if len(token) <= 10:
        return '***'
    return f"{token[:6]}...{token[-4:]}"

def _looks_like_discord_token(token: Optional[str]) -> bool:
    if not token:
        return False
    # Heuristic: Discord tokens are typically 3 segments separated by dots
    parts = token.split('.')
    if len(parts) != 3:
        return False
    # Basic length checks per segment
    return all(len(p) >= 6 for p in parts) and len(token) >= 30

DISCORD_TOKEN = _sanitize_token(_get_raw_token())
FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

# API Endpoints
FOOTBALL_DATA_BASE_URL = 'https://api.football-data.org/v4'
ODDS_API_BASE_URL = 'https://api.the-odds-api.com/v4'

# Premier League ID trong Football-Data.org
PREMIER_LEAGUE_ID = 'PL'

# Cache cho kèo cược (để tránh vượt quá 500 requests/tháng)
odds_cache: Dict[str, Dict[str, Any]] = {}
CACHE_DURATION = 3600 * 3  # 3 giờ

# Khởi tạo bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)


@bot.event
async def on_ready():
    """Bot sẵn sàng hoạt động"""
    logger.info(f'Bot đã đăng nhập: {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Đang hoạt động trên {len(bot.guilds)} server(s)')
    # Set bot activity
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Ngoại Hạng Anh ⚽"
        )
    )


def get_football_data(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """
    Gọi API của Football-Data.org
    
    Args:
        endpoint: API endpoint (ví dụ: '/competitions/PL/matches')
        params: Query parameters
    
    Returns:
        JSON response hoặc None nếu có lỗi
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


@bot.command(name='lichdau')
async def schedule(ctx: commands.Context):
    """
    Lệnh !lichdau - Hiển thị lịch thi đấu Ngoại Hạng Anh 7 ngày tới
    """
    await ctx.typing()
    
    # Lấy ngày hiện tại và 7 ngày sau
    date_from = datetime.now().strftime('%Y-%m-%d')
    date_to = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Gọi API
    data = get_football_data(
        f'/competitions/{PREMIER_LEAGUE_ID}/matches',
        params={'dateFrom': date_from, 'dateTo': date_to}
    )
    
    if not data or 'matches' not in data:
        await ctx.send('❌ Không thể lấy lịch thi đấu. Vui lòng thử lại sau.')
        return
    
    matches = data['matches']
    
    if not matches:
        await ctx.send('📅 Không có trận đấu nào trong 7 ngày tới.')
        return
    
    # Tạo embed
    embed = discord.Embed(
        title='📅 Lịch Thi Đấu Ngoại Hạng Anh (7 ngày tới)',
        description=f'Từ {date_from} đến {date_to}',
        color=discord.Color.green()
    )
    embed.set_thumbnail(url='https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg')
    
    # Thêm các trận đấu
    for match in matches[:10]:  # Giới hạn 10 trận để tránh embed quá dài
        home_team = match['homeTeam']['name']
        away_team = match['awayTeam']['name']
        utc_date = match['utcDate']
        status = match['status']
        
        # Chuyển đổi thời gian
        try:
            match_time = datetime.fromisoformat(utc_date.replace('Z', '+00:00'))
            time_str = match_time.strftime('%d/%m/%Y %H:%M UTC')
        except:
            time_str = utc_date
        
        # Emoji theo trạng thái
        status_emoji = {
            'SCHEDULED': '🕐',
            'TIMED': '🕐',
            'IN_PLAY': '🔴',
            'PAUSED': '⏸️',
            'FINISHED': '✅',
            'POSTPONED': '⏰',
            'CANCELLED': '❌'
        }.get(status, '⚽')
        
        embed.add_field(
            name=f'{status_emoji} {home_team} vs {away_team}',
            value=f'🕐 {time_str}',
            inline=False
        )
    
    if len(matches) > 10:
        embed.set_footer(text=f'Và {len(matches) - 10} trận khác...')
    
    await ctx.send(embed=embed)


@bot.command(name='phantich')
async def analyze(ctx: commands.Context, *, match_input: str):
    """
    Lệnh !phantich <Đội A> vs <Đội B>
    Phân tích trận đấu và đưa ra khuyến nghị về kèo chấp Châu Á
    
    Ví dụ: !phantich Arsenal vs Manchester United
    """
    await ctx.typing()
    
    # Parse input
    if ' vs ' not in match_input.lower():
        await ctx.send('❌ Định dạng không đúng. Sử dụng: `!phantich <Đội A> vs <Đội B>`')
        return
    
    teams = match_input.split(' vs ')
    if len(teams) != 2:
        await ctx.send('❌ Định dạng không đúng. Sử dụng: `!phantich <Đội A> vs <Đội B>`')
        return
    
    home_team = teams[0].strip()
    away_team = teams[1].strip()
    
    # Tạo embed loading
    loading_embed = discord.Embed(
        title='🔮 Đang phân tích...',
        description=f'Đang thu thập dữ liệu cho trận:\n**{home_team}** vs **{away_team}**',
        color=discord.Color.blue()
    )
    loading_msg = await ctx.send(embed=loading_embed)
    
    try:
        # Bước 1: Lấy dữ liệu thống kê từ Football-Data.org
        home_stats = get_team_stats(home_team, FOOTBALL_DATA_API_KEY)
        away_stats = get_team_stats(away_team, FOOTBALL_DATA_API_KEY)
        
        if not home_stats or not away_stats:
            await loading_msg.edit(embed=discord.Embed(
                title='❌ Lỗi',
                description='Không thể tìm thấy dữ liệu cho một hoặc cả hai đội. Vui lòng kiểm tra tên đội.',
                color=discord.Color.red()
            ))
            return
        
        # Bước 2: Lấy dữ liệu kèo từ The Odds API (với cache)
        cache_key = f"{home_team}_vs_{away_team}"
        current_time = datetime.now().timestamp()
        
        if cache_key in odds_cache and (current_time - odds_cache[cache_key]['timestamp']) < CACHE_DURATION:
            odds_data = odds_cache[cache_key]['data']
            logger.info(f'Sử dụng cache cho kèo: {cache_key}')
        else:
            odds_data = get_odds_data(home_team, away_team, ODDS_API_KEY)
            if odds_data:
                odds_cache[cache_key] = {
                    'data': odds_data,
                    'timestamp': current_time
                }
        
        if not odds_data:
            await loading_msg.edit(embed=discord.Embed(
                title='⚠️ Cảnh báo',
                description='Không thể lấy dữ liệu kèo cược. Tiếp tục phân tích với dữ liệu thống kê...',
                color=discord.Color.orange()
            ))
        
        # Bước 3: Dự đoán bằng model
        prediction_result = predict_match(home_stats, away_stats, odds_data)
        
        # Bước 3.5: Dự đoán tổng bàn thắng (có cache sử dụng ở predictor)
        goals_result = predict_total_goals(home_stats, away_stats, odds_data)
        cached_goals = goals_result.get('predicted_goals') if goals_result else None
        
        # Bước 3.6: Dự đoán multi-line O/U (1.5, 2.5, 3.5)
        multiline_ou = predict_multiline_ou(home_stats, away_stats, odds_data, predicted_goals=cached_goals)

        # Bước 3.7: Dự đoán tỉ số chính xác (Poisson)
        correct_score = predict_correct_score(home_stats, away_stats, predicted_goals=cached_goals)
        
        # Log prediction for tracking
        if prediction_result:
            try:
                # Parse OU pick if available
                ou_line = 2.5
                ou_pick = None
                ou_conf = None
                predicted_goals = None
                if goals_result:
                    predicted_goals = goals_result.get('predicted_goals')
                    ou_text = goals_result.get('over_under_recommendation', '')
                    ou_conf = goals_result.get('ou_confidence')
                    if 'Over 2.5' in ou_text:
                        ou_pick = 'Over'
                    elif 'Under 2.5' in ou_text:
                        ou_pick = 'Under'

                log_prediction(
                    home_team=home_team,
                    away_team=away_team,
                    prediction=prediction_result['prediction'],
                    confidence=prediction_result['confidence'],
                    handicap_value=odds_data.get('handicap_value', 0) if odds_data else 0,
                    odds_data=odds_data,
                    ou_line=ou_line,
                    ou_pick=ou_pick,
                    ou_confidence=ou_conf,
                    predicted_goals=predicted_goals,
                )
            except Exception as e:
                logger.warning(f'Could not log prediction: {e}')
        
        if not prediction_result:
            await loading_msg.edit(embed=discord.Embed(
                title='❌ Lỗi',
                description='Không thể thực hiện dự đoán. Model có thể chưa được huấn luyện.',
                color=discord.Color.red()
            ))
            return
        
        # Bước 4: Tạo embed kết quả
        result_embed = discord.Embed(
            title='🔮 Phân Tích Trận Đấu',
            description=f'**{home_team}** ⚔️ **{away_team}**',
            color=discord.Color.gold()
        )
        
        # Thông tin kèo
        if odds_data and 'asian_handicap' in odds_data:
            result_embed.add_field(
                name='📊 Kèo Chấp Châu Á',
                value=f"```{odds_data['asian_handicap']}```",
                inline=False
            )
        
        # Khuyến nghị
        recommendation = prediction_result['recommendation']
        confidence = prediction_result['confidence']
        
        # Icon theo độ tin cậy
        if confidence >= 0.7:
            confidence_icon = '🟢'
        elif confidence >= 0.55:
            confidence_icon = '🟡'
        else:
            confidence_icon = '🟠'
        
        # Clamp confidence hiển thị để tránh overconfidence nếu model bias
        display_conf = min(confidence, 0.92)
        recommendation_display = recommendation + (" (mock odds)" if (odds_data and odds_data.get('source') == 'mock') else "")
        result_embed.add_field(
            name='💡 Khuyến Nghị',
            value=f"```{recommendation_display}```",
            inline=False
        )
        
        result_embed.add_field(
            name=f'{confidence_icon} Độ Tin Cậy',
            value=f"```{display_conf:.1%}```",
            inline=True
        )
        
        # Dự đoán tổng bàn thắng với multi-line O/U
        if goals_result:
            predicted_goals = goals_result['predicted_goals']
            ou_recommendation = goals_result['over_under_recommendation']
            ou_confidence = goals_result['ou_confidence']
        
            # Icon theo độ tin cậy O/U
            if ou_confidence >= 0.65:
                ou_icon = '🟢'
            elif ou_confidence >= 0.5:
                ou_icon = '🟡'
            else:
                ou_icon = '🟠'
        
            result_embed.add_field(
                name='⚽ Dự Đoán Tổng Bàn Thắng',
                value=f"```{ou_recommendation}```",
                inline=False
            )
        
            result_embed.add_field(
                name=f'{ou_icon} Độ Tin Cậy O/U 2.5',
                value=f"```{ou_confidence:.1%}```",
                inline=True
            )
            
        # Bảng O/U đa mốc
        if multiline_ou:
            ou_table = "```\n"
            ou_table += "Mốc  | Over    | Under   | Gợi ý\n"
            ou_table += "-----+---------+---------+-------\n"
            for line in ['1.5', '2.5', '3.5']:
                data = multiline_ou.get(line, {})
                over_p = data.get('over_prob', 0) * 100
                under_p = data.get('under_prob', 0) * 100
                rec = data.get('recommendation', '-')
                ou_table += f"{line:4s} | {over_p:5.1f}% | {under_p:5.1f}% | {rec}\n"
            ou_table += "```"
            result_embed.add_field(
                name='📊 Phân Tích O/U Đa Mốc',
                value=ou_table,
                inline=False
            )

            # Tỉ số chính xác (Poisson)
            if correct_score:
                best = correct_score['best_correct_score']
                best_p = correct_score['best_correct_score_prob']
                top_lines = "\n".join([f"{s}: {p*100:.1f}%" for s,p in correct_score['top_scorelines']])
                result_embed.add_field(
                    name='🎯 Dự Đoán Tỉ Số (Poisson)',
                    value=f"```Gợi ý: {best} ({best_p*100:.1f}%)\nTop 5:\n{top_lines}```",
                    inline=False
                )

            # AI narrative (optional)
            try:
                ai_text = generate_ai_insight(
                    home_team, away_team,
                    home_stats, away_stats,
                    recommendation, confidence,
                    ou_text=ou_recommendation if goals_result else None,
                    ou_conf=ou_confidence if goals_result else None,
                    correct_score=best if correct_score else None
                )
                if ai_text:
                    result_embed.add_field(
                        name='🧠 AI Phân Tích',
                        value=ai_text[:1000],  # Discord field limit safety
                        inline=False
                    )
            except Exception as e:
                logger.debug(f'AI insight failed: {e}')
        
        # Thêm thống kê nếu có
        if 'stats_summary' in prediction_result:
            stats = prediction_result['stats_summary']
            result_embed.add_field(
                name='📈 Thống Kê',
                value=stats,
                inline=False
            )
        
        # Disclaimer
        result_embed.set_footer(
            text='⚠️ Dự đoán chỉ mang tính tham khảo dựa trên thống kê, không phải lời khuyên đầu tư. '
                 'Vui lòng cân nhắc kỹ trước khi đưa ra quyết định.'
        )
        
        await loading_msg.edit(embed=result_embed)
        
    except Exception as e:
        logger.error(f'Lỗi khi phân tích trận đấu: {e}', exc_info=True)
        await loading_msg.edit(embed=discord.Embed(
            title='❌ Lỗi',
            description=f'Đã xảy ra lỗi khi phân tích: {str(e)}',
            color=discord.Color.red()
        ))


@bot.command(name='stats_ou')
async def stats_ou(ctx: commands.Context, line: float = 2.5):
    """Hiển thị độ chính xác lịch sử cho kèo Over/Under ở line (mặc định 2.5)."""
    from prediction_tracker import get_ou_accuracy, get_ou_stats
    try:
        acc = get_ou_accuracy(line)
        all_lines = get_ou_stats([1.5, 2.5, 3.5])
        embed = discord.Embed(
            title='📊 Thống Kê O/U',
            description=f'Độ chính xác dựa trên các trận đã hoàn thành',
            color=discord.Color.teal()
        )
        embed.add_field(name=f'Line {line}', value=f"```Số kèo: {acc['count']}\nĐúng: {acc['correct']}\nAccuracy: {acc['accuracy']*100:.1f}%```", inline=False)
        for k,v in all_lines.items():
            embed.add_field(name=f'Line {k}', value=f"```{v['accuracy']*100:.1f}% ({v['correct']}/{v['count']})```", inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f'Không thể lấy thống kê: {e}')


@bot.command(name='fetchresults')
async def fetch_results_command(ctx: commands.Context, days: int = 7):
    """
    Tự động fetch kết quả từ API cho các predictions chưa có kết quả.
    
    Ví dụ: !fetchresults
    Hoặc: !fetchresults 14  (fetch 14 ngày trước)
    """
    from prediction_tracker import auto_fetch_results
    await ctx.typing()
    
    try:
        if not FOOTBALL_DATA_API_KEY:
            await ctx.send('❌ Chưa cấu hình FOOTBALL_DATA_API_KEY.')
            return
        
        loading_embed = discord.Embed(
            title='🔄 Đang fetch kết quả...',
            description=f'Đang tìm kết quả từ {days} ngày trước',
            color=discord.Color.blue()
        )
        loading_msg = await ctx.send(embed=loading_embed)
        
        updated_count = auto_fetch_results(FOOTBALL_DATA_API_KEY, days_back=days)
        
        if updated_count > 0:
            embed = discord.Embed(
                title='✅ Fetch Thành Công',
                description=f'Đã cập nhật **{updated_count}** kết quả từ API',
                color=discord.Color.green()
            )
            
            # Get updated stats
            from prediction_tracker import get_stats
            stats = get_stats()
            if stats and stats.get('completed_predictions', 0) > 0:
                embed.add_field(
                    name='Độ chính xác hiện tại',
                    value=f"{stats['accuracy']:.1%} ({stats['correct_predictions']}/{stats['completed_predictions']})",
                    inline=False
                )
        else:
            embed = discord.Embed(
                title='ℹ️ Không có cập nhật',
                description='Không tìm thấy kết quả mới hoặc tất cả predictions đã được cập nhật.',
                color=discord.Color.blue()
            )
        
        await loading_msg.edit(embed=embed)
        
    except Exception as e:
        logger.error(f'Error fetching results: {e}', exc_info=True)
        await ctx.send(f'❌ Lỗi khi fetch: {str(e)}')


@bot.command(name='analyze')
async def analyze_command(ctx: commands.Context):
    """
    Hiển thị báo cáo phân tích prediction accuracy và bias.
    """
    import json
    await ctx.typing()
    
    try:
        if not os.path.exists('predictions_log.json'):
            await ctx.send('❌ Chưa có prediction nào được lưu.')
            return
        
        with open('predictions_log.json', 'r', encoding='utf-8') as f:
            predictions = json.load(f)
        
        completed = [p for p in predictions if p.get('actual_result') is not None]
        
        if not completed:
            await ctx.send('⚠️ Chưa có trận nào hoàn thành. Dùng `!fetchresults` để tự động cập nhật kết quả.')
            return
        
        # Main stats embed
        total = len(completed)
        correct = sum(1 for p in completed if p.get('correct'))
        accuracy = correct / total
        
        embed = discord.Embed(
            title='📊 Báo Cáo Phân Tích Predictions',
            description=f'Phân tích {len(predictions)} predictions ({total} đã hoàn thành)',
            color=discord.Color.gold()
        )
        
        # Overall accuracy
        acc_icon = '🟢' if accuracy >= 0.65 else ('🟡' if accuracy >= 0.55 else '🔴')
        embed.add_field(
            name=f'{acc_icon} Độ Chính Xác Tổng Thể',
            value=f'**{accuracy:.1%}** ({correct}/{total} đúng)',
            inline=False
        )
        
        # By confidence level
        high_conf = [p for p in completed if p.get('confidence', 0) >= 0.7]
        med_conf = [p for p in completed if 0.55 <= p.get('confidence', 0) < 0.7]
        
        conf_text = []
        if high_conf:
            high_acc = sum(1 for p in high_conf if p.get('correct')) / len(high_conf)
            conf_text.append(f"Cao (≥70%): {high_acc:.1%} ({len(high_conf)} trận)")
        if med_conf:
            med_acc = sum(1 for p in med_conf if p.get('correct')) / len(med_conf)
            conf_text.append(f"Trung (55-70%): {med_acc:.1%} ({len(med_conf)} trận)")
        
        if conf_text:
            embed.add_field(
                name='📈 Theo Độ Tin Cậy',
                value='\n'.join(conf_text),
                inline=True
            )
        
        # O/U Analysis
        ou_completed = [p for p in completed if p.get('ou_pick') and p.get('ou_actual') and p.get('ou_actual') != 'Push']
        
        if ou_completed:
            ou_correct = sum(1 for p in ou_completed if p.get('ou_correct'))
            ou_accuracy = ou_correct / len(ou_completed)
            
            over_picks = sum(1 for p in ou_completed if p.get('ou_pick') == 'Over')
            over_ratio = over_picks / len(ou_completed)
            
            ou_text = [f"Accuracy: **{ou_accuracy:.1%}** ({ou_correct}/{len(ou_completed)})"]
            
            # Bias detection
            if over_ratio > 0.65:
                ou_text.append(f"⚠️ Over Bias: {over_ratio:.1%} picks là Over")
            elif over_ratio < 0.35:
                ou_text.append(f"⚠️ Under Bias: {(1-over_ratio):.1%} picks là Under")
            else:
                ou_text.append(f"✅ Cân bằng: {over_ratio:.1%} Over / {(1-over_ratio):.1%} Under")
            
            # Win rate by pick
            over_preds = [p for p in ou_completed if p.get('ou_pick') == 'Over']
            under_preds = [p for p in ou_completed if p.get('ou_pick') == 'Under']
            
            if over_preds:
                over_wr = sum(1 for p in over_preds if p.get('ou_correct')) / len(over_preds)
                ou_text.append(f"Over WR: {over_wr:.1%}")
            if under_preds:
                under_wr = sum(1 for p in under_preds if p.get('ou_correct')) / len(under_preds)
                ou_text.append(f"Under WR: {under_wr:.1%}")
            
            embed.add_field(
                name='🎯 Over/Under Analysis',
                value='\n'.join(ou_text),
                inline=True
            )
        
        # Goals prediction accuracy
        goals_completed = [p for p in completed 
                          if p.get('predicted_goals') is not None 
                          and p.get('home_goals') is not None]
        
        if goals_completed:
            errors = []
            for p in goals_completed:
                predicted = p.get('predicted_goals', 0)
                actual = (p.get('home_goals', 0) or 0) + (p.get('away_goals', 0) or 0)
                errors.append(abs(predicted - actual))
            
            mae = sum(errors) / len(errors)
            embed.add_field(
                name='⚽ Dự Đoán Tổng Bàn',
                value=f'MAE: **{mae:.2f}** bàn/trận\n({len(goals_completed)} trận)',
                inline=True
            )
        
        # Recent results (last 5)
        recent = completed[-5:] if len(completed) > 5 else completed
        recent_text = []
        for p in reversed(recent):
            icon = '✅' if p.get('correct') else '❌'
            score = f"{p.get('home_goals', '?')}-{p.get('away_goals', '?')}"
            recent_text.append(f"{icon} {p['home_team'][:15]} vs {p['away_team'][:15]} ({score})")
        
        if recent_text:
            embed.add_field(
                name='📝 5 Trận Gần Nhất',
                value='\n'.join(recent_text),
                inline=False
            )
        
        # Footer with tips
        tips = []
        if len(completed) < 20:
            tips.append('💡 Cần thêm dữ liệu (ít nhất 20 trận) để phân tích chi tiết.')
        
        if ou_completed and over_ratio > 0.65:
            over_preds_list = [p for p in ou_completed if p.get('ou_pick') == 'Over']
            if over_preds_list:
                over_wr_check = sum(1 for p in over_preds_list if p.get('ou_correct')) / len(over_preds_list)
                if over_wr_check < 0.5:
                    tips.append('⚠️ Model nghiêng Over nhưng win rate thấp. Cân nhắc hạ alpha.')
        
        if tips:
            embed.set_footer(text=' | '.join(tips))
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f'Error in analyze command: {e}', exc_info=True)
        await ctx.send(f'❌ Lỗi khi phân tích: {str(e)}')


@bot.command(name='updateresult')
async def update_result_command(ctx: commands.Context, home_team: str, away_team: str, home_goals: int, away_goals: int):
    """
    Cập nhật kết quả trận đấu để tính accuracy.
    
    Ví dụ: !updateresult Arsenal "Manchester United" 2 1
    Hoặc: !updateresult Arsenal ManchesterUnited 2 1
    """
    from prediction_tracker import update_result
    import json
    await ctx.typing()
    
    try:
        # Load predictions
        if not os.path.exists('predictions_log.json'):
            await ctx.send('❌ Chưa có prediction nào được lưu.')
            return
        
        with open('predictions_log.json', 'r', encoding='utf-8') as f:
            predictions = json.load(f)
        
        # Find matching prediction (most recent)
        # Normalize team names for matching
        home_norm = home_team.lower().replace(' ', '').replace('_', '')
        away_norm = away_team.lower().replace(' ', '').replace('_', '')
        
        candidates = []
        for p in predictions:
            p_home = p['home_team'].lower().replace(' ', '').replace('_', '')
            p_away = p['away_team'].lower().replace(' ', '').replace('_', '')
            if p_home == home_norm and p_away == away_norm and p.get('actual_result') is None:
                candidates.append(p)
        
        if not candidates:
            await ctx.send(f'❌ Không tìm thấy prediction cho trận **{home_team}** vs **{away_team}** (hoặc đã cập nhật rồi).')
            return
        
        # Get most recent
        pred = candidates[-1]
        pred_id = pred['id']
        handicap = pred.get('handicap_value', 0.0) or 0.0
        
        # Update
        is_correct = update_result(pred_id, home_goals, away_goals, handicap)
        
        # Build response
        embed = discord.Embed(
            title='✅ Đã Cập Nhật Kết Quả',
            description=f'**{home_team}** {home_goals}-{away_goals} **{away_team}**',
            color=discord.Color.green() if is_correct else discord.Color.red()
        )
        
        embed.add_field(
            name='Kèo chấp',
            value=f'{pred["home_team"]} {handicap:+.1f}',
            inline=True
        )
        
        embed.add_field(
            name='Dự đoán',
            value=f'{"Nhà" if pred["prediction"] == 1 else "Khách"} thắng kèo',
            inline=True
        )
        
        embed.add_field(
            name='Kết quả',
            value=f'{"✅ Đúng" if is_correct else "❌ Sai"}',
            inline=True
        )
        
        # O/U result if logged
        if pred.get('ou_pick') and pred.get('ou_actual'):
            total = home_goals + away_goals
            ou_correct = pred.get('ou_correct')
            embed.add_field(
                name=f'O/U {pred.get("ou_line", 2.5)}',
                value=f'Dự đoán: {pred["ou_pick"]}\nThực tế: {pred["ou_actual"]} ({total} bàn)\n{"✅ Đúng" if ou_correct else ("❌ Sai" if ou_correct is False else "🟡 Push")}',
                inline=False
            )
        
        # Get updated stats
        from prediction_tracker import get_stats
        stats = get_stats()
        if stats and stats.get('completed_predictions', 0) > 0:
            embed.add_field(
                name='Độ chính xác hiện tại',
                value=f"{stats['accuracy']:.1%} ({stats['correct_predictions']}/{stats['completed_predictions']})",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f'Error updating result: {e}', exc_info=True)
        await ctx.send(f'❌ Lỗi khi cập nhật: {str(e)}')


@bot.command(name='help')
async def help_command(ctx: commands.Context):
    """Hiển thị hướng dẫn sử dụng bot"""
    embed = discord.Embed(
        title='📖 Hướng Dẫn Sử Dụng Bot',
        description='**Nhà Tiên tri Ngoại Hạng Anh** ⚽️🤖',
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name='📅 !lichdau',
        value='Hiển thị lịch thi đấu Ngoại Hạng Anh trong 7 ngày tới.',
        inline=False
    )
    
    embed.add_field(
        name='🔮 !phantich <Đội A> vs <Đội B>',
        value='Phân tích trận đấu và đưa ra khuyến nghị về kèo chấp Châu Á, tổng bàn, O/U đa mốc, tỉ số chính xác.\n'
              'Ví dụ: `!phantich Arsenal vs Manchester United`',
        inline=False
    )
    
    embed.add_field(
        name='📊 !stats',
        value='Xem độ chính xác dự đoán tổng thể của bot.',
        inline=False
    )
    
    embed.add_field(
        name='📈 !stats_ou [line]',
        value='Xem độ chính xác kèo Over/Under theo mốc (mặc định 2.5).\n'
              'Ví dụ: `!stats_ou 2.5`',
        inline=False
    )
    
    embed.add_field(
        name='📊 !analyze',
        value='Hiển thị báo cáo chi tiết về accuracy, bias Over/Under, calibration, MAE tổng bàn.',
        inline=False
    )
    
    embed.add_field(
        name='🔄 !fetchresults [days]',
        value='Tự động fetch kết quả từ API cho các predictions đang chờ (mặc định 7 ngày).\n'
              'Ví dụ: `!fetchresults 14`',
        inline=False
    )
    
    embed.add_field(
        name='✏️ !updateresult <home> <away> <h_goals> <a_goals>',
        value='Cập nhật kết quả thủ công cho một trận đấu.\n'
              'Ví dụ: `!updateresult Arsenal "Man United" 2 1`',
        inline=False
    )
    
    embed.add_field(
        name='📖 !help',
        value='Hiển thị hướng dẫn này.',
        inline=False
    )
    
    embed.set_footer(text='Bot dùng ML + Poisson với calibration alpha=0.50 | Độ chính xác EPL recent form: 100%')
    
    await ctx.send(embed=embed)


@bot.command(name='stats')
async def stats_command(ctx: commands.Context):
    """Hiển thị prediction accuracy statistics"""
    await ctx.typing()
    
    try:
        stats = get_stats()
        
        if not stats:
            await ctx.send('📊 Chưa có dữ liệu prediction nào được lưu.')
            return
        
        embed = discord.Embed(
            title='📊 Thống Kê Độ Chính Xác',
            description='Độ chính xác dự đoán của bot',
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name='Tổng số dự đoán',
            value=str(stats['total_predictions']),
            inline=True
        )
        
        embed.add_field(
            name='Đã có kết quả',
            value=str(stats['completed_predictions']),
            inline=True
        )
        
        if stats['completed_predictions'] > 0:
            accuracy = stats['accuracy']
            correct = stats['correct_predictions']
            
            # Choose color based on accuracy
            if accuracy >= 0.75:
                accuracy_icon = '🟢'
            elif accuracy >= 0.65:
                accuracy_icon = '🟡'
            else:
                accuracy_icon = '🟠'
            
            embed.add_field(
                name=f'{accuracy_icon} Độ chính xác',
                value=f"**{accuracy:.1%}** ({correct}/{stats['completed_predictions']})",
                inline=True
            )
            
            # Recent predictions
            if 'recent_10' in stats and stats['recent_10']:
                recent_text = []
                for p in stats['recent_10'][-5:]:  # Last 5
                    icon = '✅' if p['correct'] else '❌'
                    recent_text.append(f"{icon} {p['home_team']} vs {p['away_team']}")
                
                embed.add_field(
                    name='5 dự đoán gần nhất',
                    value='\n'.join(recent_text),
                    inline=False
                )
        
        embed.set_footer(text='Thống kê được cập nhật tự động sau mỗi trận đấu')
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f'Error getting stats: {e}', exc_info=True)
        await ctx.send('❌ Không thể lấy thống kê. Vui lòng thử lại sau.')


@bot.command(name='huongdan', aliases=['hd'])
async def huongdan_command(ctx: commands.Context):
    """Hiển thị hướng dẫn sử dụng bot (tiếng Việt)"""
    embed = discord.Embed(
        title='📖 Hướng Dẫn Sử Dụng Bot',
        description='**Nhà Tiên tri Ngoại Hạng Anh** ⚽️🤖',
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name='📅 !lichdau',
        value='Hiển thị lịch thi đấu Ngoại Hạng Anh trong 7 ngày tới.',
        inline=False
    )
    
    embed.add_field(
        name='🔮 !phantich <Đội A> vs <Đội B>',
        value='Phân tích trận đấu và đưa ra khuyến nghị về kèo chấp Châu Á, tổng bàn, O/U đa mốc, tỉ số chính xác.\n'
              'Ví dụ: `!phantich Arsenal vs Manchester United`',
        inline=False
    )
    
    embed.add_field(
        name='📊 !stats',
        value='Xem độ chính xác dự đoán tổng thể của bot.',
        inline=False
    )
    
    embed.add_field(
        name='📈 !stats_ou [line]',
        value='Xem độ chính xác kèo Over/Under theo mốc (mặc định 2.5).\n'
              'Ví dụ: `!stats_ou 2.5`',
        inline=False
    )
    
    embed.add_field(
        name='📊 !analyze',
        value='Hiển thị báo cáo chi tiết về accuracy, bias Over/Under, calibration, MAE tổng bàn.',
        inline=False
    )
    
    embed.add_field(
        name='🔄 !fetchresults [days]',
        value='Tự động fetch kết quả từ API cho các predictions đang chờ (mặc định 7 ngày).\n'
              'Ví dụ: `!fetchresults 14`',
        inline=False
    )
    
    embed.add_field(
        name='✏️ !updateresult <home> <away> <h_goals> <a_goals>',
        value='Cập nhật kết quả thủ công cho một trận đấu.\n'
              'Ví dụ: `!updateresult Arsenal "Man United" 2 1`',
        inline=False
    )
    
    embed.add_field(
        name='📖 !help hoặc !huongdan',
        value='Hiển thị hướng dẫn này.',
        inline=False
    )
    
    embed.set_footer(text='Bot dùng ML + Poisson với calibration alpha=0.50 | Độ chính xác EPL recent form: 100%')
    
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    """Xử lý lỗi lệnh"""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Thiếu tham số. Sử dụng `!huongdan` để xem hướng dẫn.')
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send('❌ Lệnh không tồn tại. Sử dụng `!huongdan` để xem danh sách lệnh.')
    else:
        logger.error(f'Lỗi không xử lý được: {error}', exc_info=True)
        await ctx.send('❌ Đã xảy ra lỗi khi thực hiện lệnh.')


def main():
    """Khởi chạy bot"""
    # Start HTTP server for Render port binding (in background thread)
    from threading import Thread
    from flask import Flask
    
    app = Flask(__name__)
    
    @app.route('/')
    def health_check():
        return {'status': 'Bot is running', 'bot_name': 'EPL Prediction Bot'}, 200
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    @app.route('/token')
    def token_status():
        return {
            'present': bool(DISCORD_TOKEN),
            'looks_valid': _looks_like_discord_token(DISCORD_TOKEN),
            'masked': _mask_token(DISCORD_TOKEN)
        }, 200
    
    def run_web():
        port = int(os.environ.get('PORT', 10000))
        logger.info(f'Starting HTTP server on port {port}')
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    
    # Start web server in background thread
    web_thread = Thread(target=run_web, daemon=True)
    web_thread.start()
    logger.info('HTTP server started in background')
    
    # Validate tokens after web server started so Render can still detect port
    if not DISCORD_TOKEN:
        logger.error('DISCORD_TOKEN không được thiết lập. Hãy set một trong các biến: DISCORD_TOKEN, DISCORD_BOT_TOKEN, hoặc BOT_TOKEN trong Render/ENV.')
        # Keep process alive to allow health checks while waiting for env fix
        web_thread.join()
        return
    
    if not _looks_like_discord_token(DISCORD_TOKEN):
        logger.error(f"Discord token có vẻ không hợp lệ: {_mask_token(DISCORD_TOKEN)}\n"
                     f"Gợi ý: Dán đúng Bot Token từ Discord Developer Portal (không kèm tiền tố 'Bot ').")
        web_thread.join()
        return
    
    if not FOOTBALL_DATA_API_KEY:
        logger.warning('FOOTBALL_DATA_API_KEY chưa được thiết lập. Một số tính năng sẽ không hoạt động.')
    
    if not ODDS_API_KEY:
        logger.warning('ODDS_API_KEY chưa được thiết lập. Sẽ không thể lấy dữ liệu kèo cược.')
    
    # Run Discord bot in main thread
    try:
        logger.info(f"Đăng nhập Discord với token: {_mask_token(DISCORD_TOKEN)}")
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f'Lỗi khi khởi chạy bot: {e}')


if __name__ == '__main__':
    main()
