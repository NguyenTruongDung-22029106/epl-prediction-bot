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
from predictor import predict_match
from data_collector import get_team_stats, get_odds_data
from prediction_tracker import log_prediction, get_stats

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Keys
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
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
        
        # Log prediction for tracking
        if prediction_result and odds_data:
            try:
                log_prediction(
                    home_team=home_team,
                    away_team=away_team,
                    prediction=prediction_result['prediction'],
                    confidence=prediction_result['confidence'],
                    handicap_value=odds_data.get('handicap_value', 0),
                    odds_data=odds_data
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
        
        result_embed.add_field(
            name='💡 Khuyến Nghị',
            value=f"```{recommendation}```",
            inline=False
        )
        
        result_embed.add_field(
            name=f'{confidence_icon} Độ Tin Cậy',
            value=f"```{confidence:.1%}```",
            inline=True
        )
        
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
        value='Phân tích trận đấu và đưa ra khuyến nghị về kèo chấp Châu Á.\n'
              'Ví dụ: `!phantich Arsenal vs Manchester United`',
        inline=False
    )
    
    embed.add_field(
        name='📊 !stats',
        value='Xem độ chính xác dự đoán của bot (prediction accuracy).',
        inline=False
    )
    
    embed.add_field(
        name='📖 !help',
        value='Hiển thị hướng dẫn này.',
        inline=False
    )
    
    embed.set_footer(text='Bot được phát triển bằng Machine Learning dựa trên dữ liệu lịch sử.')
    
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


@bot.command(name='huongdan', aliases=['help', 'h'])
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
        value='Phân tích trận đấu và đưa ra khuyến nghị về kèo chấp Châu Á.\n'
              'Ví dụ: `!phantich Arsenal vs Manchester United`',
        inline=False
    )
    
    embed.add_field(
        name='� !stats',
        value='Xem thống kê độ chính xác của bot.',
        inline=False
    )
    
    embed.add_field(
        name='�📖 !huongdan (hoặc !help, !h)',
        value='Hiển thị hướng dẫn này.',
        inline=False
    )
    
    embed.set_footer(text='Bot được phát triển bằng Machine Learning dựa trên dữ liệu lịch sử.')
    
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
    if not DISCORD_TOKEN:
        logger.error('DISCORD_TOKEN chưa được thiết lập trong file .env')
        return
    
    if not FOOTBALL_DATA_API_KEY:
        logger.warning('FOOTBALL_DATA_API_KEY chưa được thiết lập. Một số tính năng sẽ không hoạt động.')
    
    if not ODDS_API_KEY:
        logger.warning('ODDS_API_KEY chưa được thiết lập. Sẽ không thể lấy dữ liệu kèo cược.')
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f'Lỗi khi khởi chạy bot: {e}')


if __name__ == '__main__':
    main()
