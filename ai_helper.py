"""
ai_helper.py - Optional Google AI Studio integration for narrative insights.
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any

try:
    import google.generativeai as genai
except Exception:  # library may not be installed in some environments
    genai = None


def generate_ai_insight(home_team: str, away_team: str, 
                         home_stats: Dict[str, Any], away_stats: Dict[str, Any],
                         match_pick: str, match_conf: float,
                         ou_text: Optional[str] = None, ou_conf: Optional[float] = None,
                         correct_score: Optional[str] = None) -> Optional[str]:
    """
    Produce a short Vietnamese narrative using Google AI Studio if GOOGLE_API_KEY is set.
    Returns a short markdown string or None.
    """
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return None
    if genai is None:
        return None

    try:
        genai.configure(api_key=api_key)
        # Try a small set of current model aliases in order
        candidates = [
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro-latest',
            'gemini-pro',
            'gemini-1.5-flash',
        ]
        model = None
        last_err = None
        for name in candidates:
            try:
                model = genai.GenerativeModel(name)
                # Quick dry-run token count method may not exist; rely on generate with short prompt
                break
            except Exception as e:
                last_err = e
                model = None
        # Dynamic discovery fallback if all candidates fail
        if model is None:
            try:
                models = list(genai.list_models())
                stable_models = []
                for m in models:
                    name = getattr(m, 'name', None)
                    if not name:
                        continue
                    # Skip experimental/preview models (low quota)
                    if any(x in name.lower() for x in ['exp', 'experimental', 'preview']):
                        continue
                    methods = getattr(m, 'supported_generation_methods', []) or []
                    if any(x.lower() in ("generatecontent", "generate_content") for x in methods):
                        stable_models.append(name)
                # Prefer flash models (faster, higher quota)
                for name in stable_models:
                    if 'flash' in name.lower():
                        model = genai.GenerativeModel(name)
                        break
                if model is None and stable_models:
                    model = genai.GenerativeModel(stable_models[0])
            except Exception:
                model = None
        if model is None:
            return None
        prompt = f"""
Bạn là chuyên gia phân tích bóng đá. Hãy viết đoạn tóm tắt ngắn gọn (3-5 câu, tiếng Việt, trung lập) cho trận {home_team} vs {away_team}.
Thông tin:
- {home_team}: ghi {home_stats.get('goals_scored_avg',0):.2f}/trận, thủng {home_stats.get('goals_conceded_avg',0):.2f}/trận, điểm 5 trận gần: {home_stats.get('points_last_5',0)}
- {away_team}: ghi {away_stats.get('goals_scored_avg',0):.2f}/trận, thủng {away_stats.get('goals_conceded_avg',0):.2f}/trận, điểm 5 trận gần: {away_stats.get('points_last_5',0)}
- Gợi ý kèo chấp: {match_pick} (độ tin cậy {match_conf*100:.1f}%)
- {('O/U: ' + ou_text + f' (độ tin cậy {ou_conf*100:.1f}%)') if ou_text else ''}
- Gợi ý tỉ số: {correct_score or 'N/A'}
Yêu cầu: Không hô hào cá cược. Chỉ nêu luận điểm chính (phong độ, ưu/nhược điểm, kịch bản bàn thắng), giữ giọng điệu trung lập.
"""
        res = model.generate_content(prompt, request_options={"timeout": 8})
        if not hasattr(res, 'text') or not res.text:
            return None
        text = res.text.strip()
        # Sanitize length
        if len(text) > 1000:
            text = text[:1000] + '...'
        return text
    except Exception as e:
        # Inline debug (optional minimal footprint)
        return None
