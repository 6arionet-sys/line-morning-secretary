import os
import json
import urllib.request
import urllib.error

def get_ai_summary(weather_data, hobbies, fishing_spots, api_key=None, model=None):
    """
    Gemini APIに天気の数値と趣味情報を送り、服装のアドバイスと趣味日和スコアを取得する。
    カレンダーの予定等の個人情報は一切送信しない。
    APIキーがない場合や通信エラー時は、安全にデフォルト値を返す。
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    if not api_key:
        print("Note: GEMINI_API_KEY not set. Using rule-based fallback for clothing and hobbies.")
        return fallback_summary(weather_data, hobbies, fishing_spots)
    
    if not model:
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
    
    # プロンプト用の天気の数値情報
    weather_summary = {
        "天気": weather_data.get("raw_weather", ""),
        "最高気温": f"{weather_data.get('temp_max', '--')}℃",
        "最低気温": f"{weather_data.get('temp_min', '--')}℃",
        "降水確率": weather_data.get("pops", {}),
        "最大降水確率": f"{weather_data.get('max_pop', 0)}%",
        "風": weather_data.get("wind", {}).get("label", ""),
        "波": weather_data.get("wave", {}).get("label", ""),
        "釣り場情報": [
            {
                "名前": spot.get("name"),
                "風": spot.get("wind_label"),
                "波": spot.get("wave_label")
            }
            for spot in weather_data.get("fishing_spots", [])
        ]
    }
    
    system_instruction = (
        "あなたは親切で的確な朝の秘書AIです。"
        "提供された天気の数値・データのみを根拠にして、服装のアドバイスと趣味（特に釣り）の日和を判定してください。\n"
        "【ルール】\n"
        "1. 提供された数値にない推測情報を勝手に足さないこと。\n"
        "2. やさしい言葉（専門用語を避ける）で簡潔に書くこと。\n"
        "3. 服装の一言 (clothing_comment) は30文字以内で、気温や天気に合った服のアドバイスをすること。\n"
        "4. 趣味の日和 (hobbies)：\n"
        "   - 釣りは風と波の数値で判定すること（波1.5m以上や強風ならスコア1〜2の危険/注意、波穏やか・微風ならスコア4〜5）。潮汐は使わない。\n"
        "   - スコア (score) は 1〜5 の整数。\n"
        "   - コメント (comment) は30文字以内で風や波の様子に触れること。\n"
        "必ず指定されたJSONフォーマットのみを出力してください。"
    )
    
    prompt = (
        f"以下の今日の気象データをもとに、JSONを作成してください。\n\n"
        f"気象データ:\n{json.dumps(weather_summary, ensure_ascii=False, indent=2)}\n\n"
        f"対象の趣味: {json.dumps([h.get('name') for h in hobbies], ensure_ascii=False)}\n"
        f"釣り場一覧: {json.dumps([s.get('name') for s in fishing_spots], ensure_ascii=False)}\n\n"
        "返却フォーマット:\n"
        "{\n"
        '  "clothing_comment": "（30文字以内の服装アドバイス）",\n'
        '  "hobbies": [\n'
        '    {"name": "城ヶ島", "hobby": "釣り", "score": 4, "comment": "波風穏やかで絶好の釣り日和"}\n'
        '  ]\n'
        "}"
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_instruction}\n\n{prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            text = res_data['candidates'][0]['content']['parts'][0]['text']
            parsed = json.loads(text)
            return {
                "clothing_comment": parsed.get("clothing_comment", "気候に合わせた服装でお出かけください"),
                "hobbies": parsed.get("hobbies", [])
            }
    except Exception as e:
        print(f"Warning: Gemini API call failed: {e}. Using fallback.")
        return fallback_summary(weather_data, hobbies, fishing_spots)

def fallback_summary(weather_data, hobbies, fishing_spots):
    """
    APIキー未設定やエラー時にルールベースで生成するフォールバック
    """
    temp_max_str = weather_data.get("temp_max", "20")
    try:
        temp_max = int(temp_max_str)
    except ValueError:
        temp_max = 20
    
    max_pop = weather_data.get("max_pop", 0)
    
    # 服装判定
    if temp_max >= 28:
        clothing = "日中は暑くなるので半袖で涼しく"
    elif temp_max >= 22:
        clothing = "過ごしやすい陽気。羽織るものがあると便利"
    elif temp_max >= 15:
        clothing = "朝晩は涼しいのでジャケットや上着を"
    else:
        clothing = "冷え込むのでしっかり防寒してお出かけを"
    
    # 釣り場ごとのスコア判定
    hobby_results = []
    for spot in weather_data.get("fishing_spots", []):
        name = spot.get("name", "釣り場")
        is_high = spot.get("is_high_wave", False)
        wind = spot.get("raw_wind", "")
        
        if is_high or "やや強く" in wind or "強く" in wind:
            score = 2
            comment = "波風がやや強め。足元に注意してください"
        else:
            score = 4
            comment = "波風が穏やかで釣りやすいコンディション"
        
        hobby_results.append({
            "name": name,
            "hobby": "釣り",
            "score": score,
            "comment": comment
        })
    
    return {
        "clothing_comment": clothing,
        "hobbies": hobby_results
    }
