"""
lol_bot.py

Hướng dẫn ngắn:
- Tạo file `.env` trong cùng thư mục với nội dung:
  DISCORD_TOKEN=your_discord_bot_token
  RIOT_API_KEY=your_riot_api_key
- Cài dependencies: python -m pip install -r requirements.txt
- Chạy: python lol_bot.py

Lưu ý bảo mật: Không commit file `.env` vào Git. Token và API key phải được lưu trong biến môi trường.

Mô tả: Bot hỗ trợ 3 lệnh prefix:
- !profile <summonerName> <region>
- !livegame <summonerName> <region>
- !matchhistory <summonerName> <region>

Region: dùng mã nền tảng Riot (ví dụ: NA1, EUW1, EUN1, KR, VN2, BR1, OC1, TR1, RU)
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional

import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Load .env if present
load_dotenv()

logging.basicConfig(level=logging.INFO)

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
RIOT_API_KEY = os.environ.get("RIOT_API_KEY")

if not DISCORD_TOKEN:
    logging.error("DISCORD_TOKEN is not set. Exiting.")
    # Do not exit here to allow import inside editors; runtime will fail if not set.

# Basic mappings for Riot hosts and routing values (used for match-v5)
PLATFORM_HOST = {
    'NA1': 'na1', 'BR1': 'br1', 'LA1': 'la1', 'LA2': 'la2', 'OC1': 'oc1',
    'KR': 'kr', 'JP1': 'jp1', 'EUN1': 'eun1', 'EUW1': 'euw1', 'TR1': 'tr1', 'RU': 'ru', 'VN2': 'vn2'
}

# Routing values for the Match-V5 (aggregate) endpoints
ROUTING = {
    'NA1': 'americas', 'BR1': 'americas', 'LA1': 'americas', 'LA2': 'americas', 'OC1': 'americas',
    'KR': 'asia', 'JP1': 'asia',
    'EUN1': 'europe', 'EUW1': 'europe', 'TR1': 'europe', 'RU': 'europe', 'VN2': 'asia'
}

# Cache for static data (ddragon)
DD_VERSION: Optional[str] = None
CHAMPION_KEY_TO_NAME: Dict[str, str] = {}


def dd_version() -> str:
    global DD_VERSION
    if DD_VERSION:
        return DD_VERSION
    try:
        r = requests.get('https://ddragon.leagueoflegends.com/api/versions.json', timeout=5)
        r.raise_for_status()
        versions = r.json()
        DD_VERSION = versions[0]
        return DD_VERSION
    except Exception:
        return '13.1.1'  # fallback


def load_champion_mapping() -> None:
    global CHAMPION_KEY_TO_NAME
    if CHAMPION_KEY_TO_NAME:
        return
    ver = dd_version()
    try:
        url = f'https://ddragon.leagueoflegends.com/cdn/{ver}/data/en_US/champion.json'
        r = requests.get(url, timeout=6)
        r.raise_for_status()
        data = r.json().get('data', {})
        # mapping from key (numeric string) to champion name
        for champ_name, info in data.items():
            key = info.get('key')
            if key:
                CHAMPION_KEY_TO_NAME[str(key)] = champ_name
    except Exception:
        logging.exception('Failed to load champion mapping')


def champion_name_from_key(key: Any) -> str:
    if key is None:
        return 'Unknown'
    load_champion_mapping()
    return CHAMPION_KEY_TO_NAME.get(str(key), str(key))


def platform_host(region: str) -> Optional[str]:
    return PLATFORM_HOST.get(region.upper())


def routing_for(region: str) -> Optional[str]:
    return ROUTING.get(region.upper())


def riot_get(url: str, params: Dict[str, Any] = None) -> Optional[requests.Response]:
    headers = {'X-Riot-Token': os.environ.get('RIOT_API_KEY', '')}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=8)
        # basic rate-limit handling
        if r.status_code == 429:
            retry = r.headers.get('Retry-After') or r.headers.get('retry-after')
            logging.warning(f'Riot rate limited. Retry-After: {retry}')
        return r
    except requests.RequestException:
        return None


bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())


@bot.event
async def on_ready():
    logging.info(f'Bot logged in as {bot.user} (ID {bot.user.id})')


def format_rank(entries: List[Dict[str, Any]]) -> str:
    if not entries:
        return 'Unranked'
    solo = next((e for e in entries if e.get('queueType') == 'RANKED_SOLO_5x5'), entries[0])
    tier = solo.get('tier', 'UNR')
    rank = solo.get('rank', '')
    lp = solo.get('leaguePoints', 0)
    wins = solo.get('wins', 0)
    losses = solo.get('losses', 0)
    winrate = f"{round(wins / max(1, wins + losses) * 100, 1)}%"
    return f"{tier.title()} {rank} — {lp} LP — {wins}W/{losses}L ({winrate})"


@bot.command(name='profile')
async def profile(ctx: commands.Context, summoner_name: str, region: str):
    """!profile <summonerName> <region>"""
    await ctx.trigger_typing()
    host = platform_host(region)
    if not host:
        await ctx.send(f'Region `{region}` không hợp lệ. Ví dụ hợp lệ: NA1, EUW1, EUN1, KR, VN2')
        return
    # Summoner-v4
    url = f'https://{host}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}'
    r = riot_get(url)
    if r is None:
        await ctx.send('Không thể liên hệ Riot API. Vui lòng thử lại sau.')
        return
    if r.status_code == 404:
        await ctx.send(f'Không tìm thấy người chơi `{summoner_name}` trên region {region}.')
        return
    if r.status_code == 401:
        await ctx.send('RIOT_API_KEY không hợp lệ hoặc chưa được cung cấp.')
        return
    if not r.ok:
        await ctx.send(f'Riot API trả về trạng thái lỗi: {r.status_code}')
        return
    summoner = r.json()
    # Get ranked info
    enc_id = summoner.get('id')
    puuid = summoner.get('puuid')
    profile_icon_id = summoner.get('profileIconId')
    lvl = summoner.get('summonerLevel')

    rank = 'Unranked'
    rank_detail = None
    if enc_id:
        url2 = f'https://{host}.api.riotgames.com/lol/league/v4/entries/by-summoner/{enc_id}'
        r2 = riot_get(url2)
        if r2 and r2.ok:
            entries = r2.json()
            rank = format_rank(entries)
            rank_detail = entries

    ver = dd_version()
    icon_url = f'https://ddragon.leagueoflegends.com/cdn/{ver}/img/profileicon/{profile_icon_id}.png' if profile_icon_id else None

    embed = discord.Embed(title=f"Profile: {summoner.get('name')}", color=discord.Color.blue())
    if icon_url:
        embed.set_thumbnail(url=icon_url)
    embed.add_field(name='Level', value=str(lvl or 'N/A'), inline=True)
    embed.add_field(name='Region', value=region.upper(), inline=True)
    embed.add_field(name='Rank', value=rank, inline=False)
    # if detailed entries available, show wins/losses separately
    if rank_detail:
        solo = next((e for e in rank_detail if e.get('queueType') == 'RANKED_SOLO_5x5'), rank_detail[0])
        embed.add_field(name='Wins', value=str(solo.get('wins', 0)), inline=True)
        embed.add_field(name='Losses', value=str(solo.get('losses', 0)), inline=True)
    embed.set_footer(text=f'Region: {region.upper()}')
    await ctx.send(embed=embed)


@bot.command(name='livegame')
async def livegame(ctx: commands.Context, summoner_name: str, region: str):
    """!livegame <summonerName> <region>"""
    await ctx.trigger_typing()
    host = platform_host(region)
    if not host:
        await ctx.send(f'Region `{region}` không hợp lệ.')
        return
    url = f'https://{host}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}'
    r = riot_get(url)
    if not r:
        await ctx.send('Không thể liên hệ Riot API.')
        return
    if r.status_code == 404:
        await ctx.send(f'Không tìm thấy người chơi `{summoner_name}`.')
        return
    summ = r.json()
    enc_id = summ.get('id')
    if not enc_id:
        await ctx.send('Không tìm được summoner id.')
        return
    url2 = f'https://{host}.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{enc_id}'
    r2 = riot_get(url2)
    if r2 is None:
        await ctx.send('Không thể liên hệ Riot API (spectator).')
        return
    if r2.status_code == 404:
        await ctx.send(f'Người chơi {summoner_name} hiện không ở trong trận.')
        return
    if not r2.ok:
        await ctx.send(f'Riot API (spectator) trả về lỗi: {r2.status_code}')
        return
    data = r2.json()
    participants = data.get('participants', [])
    if not participants:
        await ctx.send('Không có thông tin người chơi trong trận.')
        return
    blue = participants[:5]
    red = participants[5:]
    load_champion_mapping()

    def format_part(p):
        name = p.get('summonerName')
        champ_key = p.get('championId')
        champ = champion_name_from_key(champ_key)
        # champion icon (ddragon)
        ver = dd_version()
        champ_img = f'https://ddragon.leagueoflegends.com/cdn/{ver}/img/champion/{champ}.png'
        return f"{name} — {champ}", champ_img

    # Build embed. We'll include names and champion names; too many images in one embed are not allowed per field, so keep simple.
    embed = discord.Embed(title=f'Live Game: {summoner_name}', color=discord.Color.green())
    embed.add_field(name='🟦 Đội Xanh', value='\n'.join(f"{p.get('summonerName')} — {champion_name_from_key(p.get('championId'))}" for p in blue), inline=True)
    embed.add_field(name='🟥 Đội Đỏ', value='\n'.join(f"{p.get('summonerName')} — {champion_name_from_key(p.get('championId'))}" for p in red), inline=True)
    await ctx.send(embed=embed)


@bot.command(name='matchhistory')
async def matchhistory(ctx: commands.Context, summoner_name: str, region: str):
    """!matchhistory <summonerName> <region>"""
    await ctx.trigger_typing()
    host = platform_host(region)
    routing = routing_for(region)
    if not host or not routing:
        await ctx.send('Region không hợp lệ.')
        return
    url = f'https://{host}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}'
    r = riot_get(url)
    if not r or not r.ok:
        await ctx.send('Không thể tìm summoner hoặc Riot API lỗi.')
        return
    summ = r.json()
    puuid = summ.get('puuid')
    if not puuid:
        await ctx.send('Không tìm thấy puuid của người chơi.')
        return
    url_ids = f'https://{routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids'
    r_ids = riot_get(url_ids, params={'start': 0, 'count': 5})
    if not r_ids or not r_ids.ok:
        await ctx.send('Không thể lấy lịch sử trận (match-v5).')
        return
    match_ids = r_ids.json()
    if not match_ids:
        await ctx.send('Không có trận nào trong lịch sử.')
        return
    load_champion_mapping()
    lines = []
    for mid in match_ids:
        r_match = riot_get(f'https://{routing}.api.riotgames.com/lol/match/v5/matches/{mid}')
        if not r_match or not r_match.ok:
            lines.append(f'{mid}: Không thể lấy chi tiết')
            continue
        m = r_match.json()
        info = m.get('info', {})
        participants = info.get('participants', [])
        part = next((p for p in participants if p.get('puuid') == puuid), None)
        if not part:
            lines.append(f'{mid}: Người chơi không có trong match data')
            continue
        champ = champion_name_from_key(part.get('championId'))
        win = part.get('win')
        k = part.get('kills', 0)
        d = part.get('deaths', 0)
        a = part.get('assists', 0)
        mode = info.get('gameMode') or info.get('queueId')
        result = '✅ Win' if win else '❌ Loss'
        lines.append(f'{result} — {champ} — KDA: {k}/{d}/{a} — Mode: {mode}')
    desc = '\n'.join(lines)
    if len(desc) > 1900:
        desc = desc[:1900] + '\n...'
    embed = discord.Embed(title=f'{summoner_name} — 5 trận gần nhất', description=desc, color=discord.Color.blurple())
    await ctx.send(embed=embed)


@bot.command(name='helpme')
async def helpme(ctx: commands.Context):
    txt = (
        "Lệnh có sẵn:\n"
        "!profile <summonerName> <region> — Hiển thị profile và rank.\n"
        "!livegame <summonerName> <region> — Kiểm tra trận đấu hiện tại.\n"
        "!matchhistory <summonerName> <region> — 5 trận gần nhất.\n"
        "Region ví dụ: NA1, EUW1, EUN1, KR, VN2"
    )
    await ctx.send(f'```{txt}```')


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Thiếu tham số. Kiểm tra lại lệnh và các tham số.')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('Bạn không có quyền thực hiện lệnh này.')
    else:
        logging.exception('Uncaught command error')
        await ctx.send('Đã xảy ra lỗi khi thực hiện lệnh.')


def main():
    if not DISCORD_TOKEN:
        logging.error('DISCORD_TOKEN missing. Set it in environment or .env file.')
        return
    if not RIOT_API_KEY:
        logging.warning('RIOT_API_KEY not set. Some commands will not work without it.')
    bot.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
