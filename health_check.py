import os
import json
import traceback

# Load environment variables
def load_env_best_effort():
    """Try python-dotenv first; if unavailable, parse .env manually."""
    loaded = False
    try:
        from dotenv import load_dotenv, dotenv_values  # type: ignore
        load_dotenv()
        # Forcefully apply parsed values in case system env is not picked up
        env_path = os.path.join(os.getcwd(), ".env")
        parsed = dotenv_values(env_path) or {}
        for k, v in parsed.items():
            if v is not None:
                os.environ[str(k)] = str(v)
        loaded = True
    except Exception:
        loaded = False

    # Manual parser (always run to ensure local .env is applied)
    env_path = os.path.join(os.getcwd(), ".env")
    parsed_count = 0
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and v:
                        os.environ[k] = v
                        parsed_count += 1
        loaded = True
    except Exception:
        pass
    # Drop a debug flag
    os.environ["CHECK_ENV_LOADED"] = "1" if loaded else "0"
    os.environ["CHECK_ENV_PARSED_COUNT"] = str(parsed_count)
    return loaded

load_env_best_effort()

RESULTS = {}

def mark(name, ok, detail=None):
    RESULTS[name] = {
        "status": "PASS" if ok else "FAIL",
        "detail": detail or ""
    }

# 1) Env presence
keys = [
    "DISCORD_TOKEN",
    "FOOTBALL_DATA_API_KEY",
    "ODDS_API_KEY",
    "GOOGLE_API_KEY",
    "RAPIDAPI_KEY",
    "API_FOOTBALL_HOST",
]
for k in keys:
    mark(f"ENV::{k}", bool(os.getenv(k)), None)

# Debug markers
mark("ENV::CHECK_ENV_LOADED", os.getenv("CHECK_ENV_LOADED") == "1", os.getenv("CHECK_ENV_PARSED_COUNT"))

# 2) API-Football probe via data_collector.get_team_stats
try:
    import data_collector as dc
    stats = dc.get_team_stats("Arsenal")
    ok = isinstance(stats, dict) and all(k in stats for k in [
        "goals_for_avg", "goals_against_avg", "form", "points_last_5"
    ])
    # Heuristic: consider it PASS if values are numeric and form is non-empty
    ok = ok and isinstance(stats.get("goals_for_avg"), (int, float)) and isinstance(stats.get("goals_against_avg"), (int, float)) and isinstance(stats.get("form"), str) and len(stats.get("form", "")) > 0
    mark("API_FOOTBALL::get_team_stats(Arsenal)", ok, detail=("ok" if ok else "unexpected response"))
except Exception as e:
    mark("API_FOOTBALL::get_team_stats(Arsenal)", False, detail=str(e))

# 3) Football-Data.org simple probe
try:
    import data_collector as dc  # already imported, but safe
    fd = dc.get_football_data("/competitions/PL/matches", params={"season": 2024})
    ok = isinstance(fd, dict) or isinstance(fd, list)
    mark("FOOTBALL_DATA::competitions/PL/matches", ok, detail=("received data" if ok else "no data"))
except Exception as e:
    mark("FOOTBALL_DATA::competitions/PL/matches", False, detail=str(e))

# 4) Google AI Studio probe (optional)
try:
    if os.getenv("GOOGLE_API_KEY"):
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            # Prefer stable models over experimental ones
            chosen = None
            try:
                models = list(genai.list_models())
                stable_models = []
                for m in models:
                    name = getattr(m, "name", "")
                    # Skip experimental/preview models (low quota)
                    if any(x in name.lower() for x in ['exp', 'experimental', 'preview']):
                        continue
                    methods = getattr(m, "supported_generation_methods", []) or []
                    if any(x.lower() in ("generatecontent", "generate_content") for x in methods):
                        stable_models.append(name)
                # Prefer flash models (faster, higher quota)
                for m in stable_models:
                    if 'flash' in m.lower():
                        chosen = m
                        break
                if not chosen and stable_models:
                    chosen = stable_models[0]
            except Exception:
                chosen = None
            # Fallback hardcoded list if discovery fails
            fallback = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-1.5-pro-latest", "gemini-pro"]
            model_name = chosen or next((n for n in fallback), None)
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content("ping")
            ok = hasattr(resp, "text") and isinstance(resp.text, str)
            mark("GOOGLE_AI::gemini_ping", ok, detail=(f"model={model_name}" if ok else "empty"))
        except Exception as ge:
            mark("GOOGLE_AI::gemini_ping", False, detail=str(ge))
    else:
        mark("GOOGLE_AI::gemini_ping", False, detail="GOOGLE_API_KEY missing")
except Exception as e:
    mark("GOOGLE_AI::gemini_ping", False, detail=str(e))

# 5) The Odds API: env only (integration mocked in code)
mark("ODDS_API::env_only", bool(os.getenv("ODDS_API_KEY")), None)

print(json.dumps(RESULTS, indent=2, ensure_ascii=False))
