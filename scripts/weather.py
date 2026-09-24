import json
import urllib.request
import re
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

def parse_direction(wind_text):
    """
    気象庁の風の文章（例: '北東の風 後 南東の風 やや強く'）から
    8方位（北、北東、東、南東、南、南西、西、北西）を抽出し、
    風が吹いていく向きの矢印アイコンコードと文字列表現を返す。
    北の風（北から吹く） -> 南を指す矢印 (dir_n)
    """
    if not wind_text:
        return None, ""
    
    dir_map = {
        "北東": ("dir_ne", "北東"),
        "北西": ("dir_nw", "北西"),
        "南東": ("dir_se", "南東"),
        "南西": ("dir_sw", "南西"),
        "北":   ("dir_n",  "北"),
        "東":   ("dir_e",  "東"),
        "南":   ("dir_s",  "南"),
        "西":   ("dir_w",  "西"),
    }
    
    # 順番にマッチ
    # 複合方位（北東など）を先にマッチさせるためキー順に注意
    found = []
    # 単語の出現順を調べる
    pattern = r'(北東|北西|南東|南西|北|東|南|西)の風'
    matches = list(re.finditer(pattern, wind_text))
    
    if not matches:
        return None, wind_text
    
    for m in matches:
        d = m.group(1)
        found.append(dir_map[d])
    
    if len(found) == 1:
        icon, name = found[0]
        # 「やや強く」などの強さ表現を抽出
        strength = ""
        if "やや強く" in wind_text:
            strength = " やや強く"
        elif "強く" in wind_text:
            strength = " 強く"
        return icon, f"{name}の風{strength}"
    else:
        first_icon, first_name = found[0]
        last_icon, last_name = found[-1]
        strength = ""
        if "やや強く" in wind_text:
            strength = " やや強く"
        elif "強く" in wind_text:
            strength = " 強く"
        return first_icon, f"{first_name} → {last_name}{strength}"

def parse_wave(wave_text):
    """
    全角数字や文字列表現（例: '１メートル後１．５メートル'）から波の高さを抽出する。
    """
    if not wave_text:
        return "", 0.0
    
    # 全角を半角に変換
    norm = wave_text.translate(str.maketrans('０１２３４５６７８９．', '0123456789.'))
    nums = [float(n) for n in re.findall(r'\d+(?:\.\d+)?', norm)]
    if not nums:
        return wave_text, 0.0
    
    max_wave = max(nums)
    if len(nums) > 1 and nums[0] != nums[-1]:
        label = f"{nums[0]}m → {nums[-1]}m"
    else:
        label = f"{nums[0]}m"
    return label, max_wave

def get_weather_type(weather_text, max_pop=0):
    """
    天気文章と降水確率から、基本天気タイプ ('sunny', 'cloudy', 'rainy', 'snowy') を返す。
    """
    if not weather_text:
        return 'sunny'
    if '雪' in weather_text:
        return 'snowy'
    if '雨' in weather_text or max_pop >= 50:
        return 'rainy'
    if 'くもり' in weather_text or '曇' in weather_text or max_pop >= 30:
        return 'cloudy'
    return 'sunny'

def simplify_weather(weather_text):
    """
    長い気象庁の天気をカード用に8文字程度に短縮する。
    例: '晴れ　夜遅く　くもり' -> '晴れ のち 曇り'
    """
    if not weather_text:
        return "晴れ"
    t = weather_text.replace('\u3000', ' ').strip()
    t = re.sub(r'所により|一時|遅く|朝晩|夕方', '', t).strip()
    t = re.sub(r'\s+', ' ', t)
    if len(t) > 10:
        t = t[:10]
    return t

def fetch_weather_data(area_code, sub_area="東部", temp_area="横浜", fishing_spots=None):
    """
    気象庁のJSONから天気、気温、降水確率、風、波などの情報を取得・整理して返す。
    """
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    
    now_jst = datetime.now(JST)
    today_str = now_jst.strftime('%Y-%m-%d')
    
    # 1. 今日の天気、風、波
    ts0 = data[0]['timeSeries'][0]
    area_ts0 = None
    for a in ts0['areas']:
        if sub_area in a['area']['name']:
            area_ts0 = a
            break
    if not area_ts0 and ts0['areas']:
        area_ts0 = ts0['areas'][0]
    
    raw_weather = area_ts0['weathers'][0] if area_ts0 and area_ts0.get('weathers') else "晴れ"
    raw_wind = area_ts0['winds'][0] if area_ts0 and area_ts0.get('winds') else ""
    raw_waves = area_ts0['waves'][0] if area_ts0 and area_ts0.get('waves') else ""
    
    # 2. 降水確率 (6-12, 12-18, 18-24)
    ts1 = data[0]['timeSeries'][1]
    time_defines1 = ts1['timeDefines']
    area_ts1 = None
    for a in ts1['areas']:
        if sub_area in a['area']['name']:
            area_ts1 = a
            break
    if not area_ts1 and ts1['areas']:
        area_ts1 = ts1['areas'][0]
    
    pops_by_period = {"6-12": "-", "12-18": "-", "18-24": "-"}
    weather_by_period = {"6-12": "sunny", "12-18": "sunny", "18-24": "cloudy"}
    
    if area_ts1 and area_ts1.get('pops'):
        for t_str, pop in zip(time_defines1, area_ts1['pops']):
            # t_str example: '2026-09-25T06:00:00+09:00'
            t_hour = int(t_str[11:13])
            t_date = t_str[:10]
            # 当日または翌日未明
            if t_date == today_str or (t_hour == 0 and len(pops_by_period["18-24"]) == 1):
                if t_hour == 6:
                    pops_by_period["6-12"] = f"{pop}%"
                elif t_hour == 12:
                    pops_by_period["12-18"] = f"{pop}%"
                elif t_hour == 18:
                    pops_by_period["18-24"] = f"{pop}%"
    
    # 3. 気温 (最高・最低)
    ts2 = data[0]['timeSeries'][2]
    area_ts2 = None
    for a in ts2['areas']:
        if temp_area in a['area']['name']:
            area_ts2 = a
            break
    if not area_ts2 and ts2['areas']:
        area_ts2 = ts2['areas'][0]
    
    temp_min = "--"
    temp_max = "--"
    if area_ts2 and area_ts2.get('temps'):
        temps = [t for t in area_ts2['temps'] if t]
        if len(temps) >= 2:
            temp_min = temps[0]
            temp_max = temps[1]
        elif len(temps) == 1:
            temp_max = temps[0]
    
    # 週間予報から補完
    if (temp_min == "--" or temp_max == "--") and len(data) > 1:
        ts_week = data[1]['timeSeries'][1]
        for a in ts_week['areas']:
            if temp_area in a['area']['name']:
                mins = [m for m in a.get('tempsMin', []) if m]
                maxs = [m for m in a.get('tempsMax', []) if m]
                if temp_min == "--" and mins:
                    temp_min = mins[0]
                if temp_max == "--" and maxs:
                    temp_max = maxs[0]
                break
    
    # 降水確率数値
    pop_nums = []
    for p in pops_by_period.values():
        digits = re.findall(r'\d+', p)
        if digits:
            pop_nums.append(int(digits[0]))
    max_pop = max(pop_nums) if pop_nums else 0
    
    # 傘判定
    if max_pop >= 50:
        umbrella_status = "傘が必要"
        umbrella_icon = "umbrella"
        umbrella_desc = "しっかり降る時間がありそう"
    elif max_pop >= 30:
        umbrella_status = "折りたたみ傘"
        umbrella_icon = "umbrella_small"
        umbrella_desc = "念のため持っておくと安心"
    else:
        umbrella_status = "傘はいらない"
        umbrella_icon = "umbrella_off"
        umbrella_desc = "傘なしでお出かけOK"
    
    # 各時間帯の天気タイプ
    for period in ["6-12", "12-18", "18-24"]:
        p_val = int(re.findall(r'\d+', pops_by_period[period])[0]) if re.findall(r'\d+', pops_by_period[period]) else 0
        weather_by_period[period] = get_weather_type(raw_weather, p_val)
    
    main_weather_type = get_weather_type(raw_weather, max_pop)
    
    # 洗濯判定
    if max_pop <= 20 and main_weather_type in ['sunny', 'cloudy']:
        laundry_status = "一日中OK"
        laundry_icon = "hanger"
        laundry_comment = "気持ちよく乾きそう"
    elif max_pop <= 40:
        laundry_status = "6〜18時OK"
        laundry_icon = "hanger"
        laundry_comment = "夕方には取り込むのがおすすめ"
    else:
        laundry_status = "部屋干し"
        laundry_icon = "home"
        laundry_comment = "雨や高湿度に注意"
    
    # 雨の降り始め情報
    rain_notice = ""
    if max_pop >= 40:
        if pops_by_period["6-12"] != "-" and int(re.findall(r'\d+', pops_by_period["6-12"])[0]) >= 40:
            rain_notice = "朝から雨が降りやすい"
        elif pops_by_period["12-18"] != "-" and int(re.findall(r'\d+', pops_by_period["12-18"])[0]) >= 40:
            rain_notice = "昼過ぎから雨の予報"
        elif pops_by_period["18-24"] != "-" and int(re.findall(r'\d+', pops_by_period["18-24"])[0]) >= 40:
            rain_notice = "夜から雨が降りそう"
    
    # 風と波の解析
    wind_icon, wind_label = parse_direction(raw_wind)
    wave_label, max_wave_val = parse_wave(raw_waves)
    is_high_wave = max_wave_val >= 1.5
    
    # 釣り場ごとのデータ取得
    spots_data = []
    if fishing_spots:
        for spot in fishing_spots:
            spot_name = spot.get("name", "釣り場")
            s_code = spot.get("area_code", area_code)
            s_sub = spot.get("sub_area", sub_area)
            
            # 同じ地域コードなら現在のデータから検索、異なるなら別途取得
            if s_code == area_code:
                s_data = data
            else:
                try:
                    s_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{s_code}.json"
                    s_req = urllib.request.Request(s_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(s_req, timeout=5) as s_resp:
                        s_data = json.loads(s_resp.read().decode('utf-8'))
                except Exception:
                    s_data = data
            
            s_ts0 = s_data[0]['timeSeries'][0]
            s_area_ts0 = None
            for a in s_ts0['areas']:
                if s_sub in a['area']['name']:
                    s_area_ts0 = a
                    break
            if not s_area_ts0 and s_ts0['areas']:
                s_area_ts0 = s_ts0['areas'][0]
            
            s_wind = s_area_ts0['winds'][0] if s_area_ts0 and s_area_ts0.get('winds') else ""
            s_wave = s_area_ts0['waves'][0] if s_area_ts0 and s_area_ts0.get('waves') else ""
            
            s_w_icon, s_w_label = parse_direction(s_wind)
            s_wv_label, s_max_wv = parse_wave(s_wave)
            
            spots_data.append({
                "name": spot_name,
                "sub_area": s_sub,
                "wind_icon": s_w_icon or "wind",
                "wind_label": s_w_label or s_wind,
                "wave_label": s_wv_label,
                "is_high_wave": s_max_wv >= 1.5,
                "raw_wind": s_wind,
                "raw_wave": s_wave
            })
    
    return {
        "raw_weather": raw_weather,
        "short_weather": simplify_weather(raw_weather),
        "main_weather_type": main_weather_type,
        "temp_min": temp_min,
        "temp_max": temp_max,
        "pops": pops_by_period,
        "weather_by_period": weather_by_period,
        "max_pop": max_pop,
        "umbrella": {
            "status": umbrella_status,
            "icon": umbrella_icon,
            "desc": umbrella_desc
        },
        "laundry": {
            "status": laundry_status,
            "icon": laundry_icon,
            "comment": laundry_comment
        },
        "rain_notice": rain_notice,
        "wind": {
            "icon": wind_icon or "wind",
            "label": wind_label or raw_wind
        },
        "wave": {
            "label": wave_label,
            "is_high_wave": is_high_wave
        },
        "fishing_spots": spots_data
    }
