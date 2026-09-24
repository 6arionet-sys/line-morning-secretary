import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

from weather import fetch_weather_data
from calendar_sync import fetch_calendar_events
from gemini_summary import get_ai_summary
from flex_card import build_flex_message

JST = timezone(timedelta(hours=9))

def build_fallback_text(weather_data, calendar_data, ai_summary, config):
    """
    Flex Message送信失敗時用のテキストメッセージを作成する。
    """
    now_jst = datetime.now(JST)
    month = now_jst.month
    day = now_jst.day
    w_ja = ["月", "火", "水", "木", "金", "土", "日"][now_jst.weekday()]
    
    weekly_schedule = config.get("weekly_schedule", {})
    today_trash = weekly_schedule.get(w_ja)
    trash_str = today_trash.get("label", "なし") if today_trash else "なし"
    
    lines = [
        f"☀️【{month}/{day}（{w_ja}）朝のまとめ】",
        "",
        f"📍 天気（{config.get('area_name', '東京')}）",
        f"・天気: {weather_data.get('raw_weather', '情報なし')}",
        f"・気温: {weather_data.get('temp_max', '--')}℃ / {weather_data.get('temp_min', '--')}℃",
        f"・傘: {weather_data.get('umbrella', {}).get('status', '不要')}",
        f"・服装: {ai_summary.get('clothing_comment', '調整しやすい服装を')}",
        "",
        f"🗑️ 今日のゴミ: {trash_str}"
    ]
    
    # 予定
    today_evs = calendar_data.get("today", [])
    if today_evs:
        lines.append("")
        lines.append("📅 今日の予定:")
        for ev in today_evs:
            lines.append(f"・{ev}")
    
    # 釣り
    spots = weather_data.get("fishing_spots", [])
    if spots:
        lines.append("")
        lines.append("🎣 釣り予報:")
        ai_hobbies = {h.get("name"): h for h in ai_summary.get("hobbies", [])}
        for s in spots:
            name = s.get("name", "")
            sc = ai_hobbies.get(name, {}).get("score", 3)
            stars = "★" * sc + "☆" * (5 - sc)
            lines.append(f"・{name}: {stars} (風: {s.get('wind_label', '-')}, 波: {s.get('wave_label', '-')})")
    
    return "\n".join(lines)

def send_line_message(token, user_id, message_payload):
    """
    LINE Messaging APIのPush Messageエンドポイントへ送信する。
    """
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    body = {
        "to": user_id,
        "messages": [message_payload]
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode('utf-8'),
        headers=headers,
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.getcode(), resp.read().decode('utf-8')

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config.json")
    
    if not os.path.exists(config_path):
        print(f"Error: config.json not found at {config_path}")
        sys.exit(1)
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    line_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    line_user_ids_str = os.environ.get("LINE_USER_ID", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    calendar_url = os.environ.get("GOOGLE_CALENDAR_ICS_URL", "").strip()
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
    repo_name = os.environ.get("GITHUB_REPOSITORY", "").strip() or config.get("github_repo", "")
    
    if not line_token:
        print("Error: LINE_CHANNEL_ACCESS_TOKEN is not set.")
        sys.exit(1)
    
    if not line_user_ids_str:
        print("Error: LINE_USER_ID is not set.")
        sys.exit(1)
    
    user_ids = [uid.strip() for uid in line_user_ids_str.split(",") if uid.strip()]
    if not user_ids:
        print("Error: No valid LINE_USER_ID found.")
        sys.exit(1)
    
    print(f"[{datetime.now(JST).isoformat()}] Starting morning secretary bot...")
    print(f"Area: {config.get('area_name', '東京')} ({config.get('area_code', '130000')})")
    
    # 1. 天気の取得
    try:
        weather_data = fetch_weather_data(
            area_code=config.get("area_code", "140000"),
            sub_area=config.get("sub_area", "東部"),
            temp_area=config.get("temp_area", "横浜"),
            fishing_spots=config.get("fishing_spots", [])
        )
        print("Weather data successfully fetched.")
    except Exception as e:
        print(f"Warning: Failed to fetch weather data: {e}")
        weather_data = {
            "raw_weather": "天気を取得できませんでした",
            "short_weather": "不明",
            "main_weather_type": "sunny",
            "temp_min": "--",
            "temp_max": "--",
            "pops": {"6-12": "-", "12-18": "-", "18-24": "-"},
            "weather_by_period": {"6-12": "sunny", "12-18": "sunny", "18-24": "sunny"},
            "max_pop": 0,
            "umbrella": {"status": "傘はいらない", "icon": "umbrella_off", "desc": ""},
            "laundry": {"status": "情報なし", "icon": "hanger", "comment": ""},
            "rain_notice": "",
            "wind": {"icon": "wind", "label": "-"},
            "wave": {"label": "-", "is_high_wave": False},
            "fishing_spots": []
        }
    
    # 2. カレンダーの予定取得
    try:
        calendar_data = fetch_calendar_events(calendar_url)
        print(f"Calendar events fetched: Today={len(calendar_data.get('today', []))}, Tomorrow={len(calendar_data.get('tomorrow', []))}, Week={len(calendar_data.get('week', []))}")
    except Exception as e:
        print(f"Warning: Calendar fetch error: {e}")
        calendar_data = {"today": [], "tomorrow": [], "week": []}
    
    # 3. GeminiによるAI要約
    ai_summary = get_ai_summary(
        weather_data=weather_data,
        hobbies=config.get("hobbies", []),
        fishing_spots=config.get("fishing_spots", []),
        api_key=gemini_key,
        model=gemini_model
    )
    print(f"AI Summary clothing: {ai_summary.get('clothing_comment')}")
    
    # 4. Flex Messageの構築
    flex_msg = build_flex_message(
        weather_data=weather_data,
        calendar_data=calendar_data,
        ai_summary=ai_summary,
        config=config,
        repo_name=repo_name
    )
    
    # デバッグ用に書き出し
    debug_path = os.path.join(base_dir, "last_flex.json")
    try:
        with open(debug_path, "w", encoding="utf-8") as f:
            json.dump(flex_msg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    
    # 5. LINE送信
    all_success = True
    send_results = []
    for uid in user_ids:
        try:
            print(f"Sending Flex Message to {uid[:6]}...{uid[-4:] if len(uid) > 10 else ''}")
            code, resp_text = send_line_message(line_token, uid, flex_msg)
            print(f"Success! Status: {code}")
            send_results.append(f"Flex message sent to {uid[:6]}: Status {code}")
        except urllib.error.HTTPError as http_err:
            error_resp = http_err.read().decode('utf-8', errors='ignore')
            print(f"Error sending Flex Message ({http_err.code}): {error_resp}")
            send_results.append(f"Flex FAILED ({http_err.code}): {error_resp}")
            print("Attempting fallback to plain text message...")
            
            try:
                fallback_txt = build_fallback_text(weather_data, calendar_data, ai_summary, config)
                txt_msg = {"type": "text", "text": fallback_txt}
                code, resp_text = send_line_message(line_token, uid, txt_msg)
                print(f"Fallback text message sent successfully! Status: {code}")
                send_results.append(f"Fallback text sent to {uid[:6]}: Status {code}")
            except Exception as fb_err:
                print(f"Fatal: Fallback text message also failed: {fb_err}")
                send_results.append(f"Fallback text FAILED: {fb_err}")
                all_success = False
        except Exception as err:
            print(f"Unexpected error sending to {uid}: {err}")
            send_results.append(f"Unexpected error: {err}")
            all_success = False
    
    # 6. last_run.txt の記録
    last_run_path = os.path.join(base_dir, "last_run.txt")
    log_info = {
        "timestamp": datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST"),
        "all_success": all_success,
        "results": send_results if 'send_results' in locals() else []
    }
    try:
        with open(last_run_path, "w", encoding="utf-8") as f:
            f.write(f"Timestamp: {log_info['timestamp']}\n")
            f.write(f"Success: {log_info['all_success']}\n")
            for res in log_info['results']:
                f.write(f"Result: {res}\n")
    except Exception as e:
        print(f"Warning: Could not write last_run.txt: {e}")
    
    if not all_success:
        print("One or more messages failed to send.")
        sys.exit(1)
    
    print("All tasks completed successfully!")

if __name__ == "__main__":
    main()
