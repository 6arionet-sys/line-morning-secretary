import os
import json
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

WEEKDAY_EN = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
WEEKDAY_SUNDAY_FIRST_JA = ["日", "月", "火", "水", "木", "金", "土"]

def get_icon_url(icon_name, repo_name=None):
    if not repo_name:
        repo_name = os.environ.get("GITHUB_REPOSITORY", "").strip() or "6arionet-sys/line-morning-secretary"
    if not icon_name.endswith(".png"):
        icon_name = f"{icon_name}.png"
    return f"https://raw.githubusercontent.com/{repo_name}/main/icons/v2/{icon_name}"

def card_box(contents, border="#B85A0E", bg="#FFFFFF", bg_gradient=None, shadow="#3A2A1E", pad="12px", margin="lg"):
    inner_box = {
        "type": "box",
        "layout": "vertical",
        "cornerRadius": "14px",
        "borderWidth": "1.5px",
        "borderColor": border,
        "paddingAll": pad,
        "contents": contents
    }
    if bg_gradient:
        inner_box["background"] = bg_gradient
    else:
        inner_box["backgroundColor"] = bg
        
    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": shadow,
        "cornerRadius": "16px",
        "paddingBottom": "3.5px",
        "paddingEnd": "2.5px",
        "margin": margin,
        "contents": [inner_box]
    }

def build_flex_message(weather_data, calendar_data, ai_summary, config, repo_name=None):
    now = datetime.now(JST)
    month, day = now.month, now.day
    w_idx = now.weekday()
    w_en = WEEKDAY_EN[w_idx]
    w_ja = ["月", "火", "水", "木", "金", "土", "日"][w_idx]
    
    weekly_schedule = config.get("weekly_schedule", {})
    today_trash = weekly_schedule.get(w_ja)
    max_pop = weather_data.get("max_pop", 0)
    
    # 傘・洗濯・服装（3D立体ピル用）
    if max_pop >= 50:
        umb_t, umb_bg, umb_c, umb_icon = f"傘が必要　夜は雨 {max_pop}%", "#EBF5FF", "#1E40AF", "pill_umbrella"
    elif max_pop >= 30:
        umb_t, umb_bg, umb_c, umb_icon = f"折りたたみ傘　降水確率 {max_pop}%", "#F1F5F9", "#334155", "pill_umbrella_small"
    else:
        umb_t, umb_bg, umb_c, umb_icon = f"傘はいらない　降水確率 {max_pop}%", "#FFFBEB", "#B45309", "pill_umbrella_off"
    
    laundry_st = weather_data.get("laundry", {}).get("status", "一日中OK")
    if "一日中" in laundry_st:
        lnd_t, lnd_bg, lnd_c, lnd_icon = "洗濯 一日中OK　気持ちよく乾く", "#ECFDF5", "#065F46", "pill_laundry"
    elif "6〜18" in laundry_st or "OK" in laundry_st:
        lnd_t, lnd_bg, lnd_c, lnd_icon = "洗濯 6〜18時OK　夕方には取り込む", "#ECFDF5", "#065F46", "pill_laundry"
    else:
        lnd_t, lnd_bg, lnd_c, lnd_icon = "洗濯 部屋干し推奨　雨や高湿度に注意", "#F8FAFC", "#475569", "pill_home"
    
    clothing_text = (ai_summary.get("clothing_comment", "") or "").strip() or "日中は快適。朝晩は薄手の上着を"
    
    trash_str = today_trash['label'] if today_trash else "ゴミ出しなし"
    alt_text = f"【朝の秘書】{month}/{day}({w_ja}) {config.get('area_name', '横浜')} {weather_data.get('temp_max', '--')}℃ / {trash_str}"
    
    # --- [1] ヘッダー ---
    days_since_sunday = (w_idx + 1) % 7
    sunday = now.date() - timedelta(days=days_since_sunday)
    event_counts = calendar_data.get("event_counts", {})
    
    week_cells = []
    for i in range(7):
        curr_d = sunday + timedelta(days=i)
        is_today = (curr_d == now.date())
        ev_cnt = event_counts.get(curr_d, 0)
        
        bg = "#FFFFFF" if is_today else "#FFFFFF33"
        c = "#E03131" if is_today else "#FFFFFF"
        
        cell_contents = [
            {"type": "text", "text": WEEKDAY_SUNDAY_FIRST_JA[i], "size": "xxs", "weight": "bold", "color": c, "align": "center"},
            {"type": "text", "text": str(curr_d.day), "size": "xs", "weight": "bold", "color": c, "align": "center", "margin": "xs"}
        ]
        if ev_cnt > 0:
            dots_str = "●●" if ev_cnt >= 2 else "●"
            cell_contents.append({"type": "text", "text": dots_str, "size": "xxs", "color": c, "align": "center"})
        else:
            # プレースホルダーで高さを揃える
            cell_contents.append({"type": "box", "layout": "vertical", "height": "14px", "contents": []})
        
        cell_dict = {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": bg,
            "cornerRadius": "6px",
            "paddingTop": "4px",
            "paddingBottom": "4px",
            "alignItems": "center",
            "flex": 1,
            "contents": cell_contents
        }
        if is_today:
            cell_dict["borderWidth"] = "2px"
            cell_dict["borderColor"] = "#E03131"
        
        week_cells.append(cell_dict)
    
    header = {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "16px",
        "background": {
            "type": "linearGradient",
            "angle": "135deg",
            "startColor": "#FF9A5A",
            "endColor": "#C67FD8"
        },
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "contents": [
                    {"type": "text", "text": f"{month}.{day} {w_en}", "size": "sm", "weight": "bold", "color": "#FFFFFF"},
                    {"type": "image", "url": get_icon_url("sun_white", repo_name), "size": "26px", "align": "end"}
                ]
            },
            {"type": "text", "text": "おはようございます", "size": "xl", "weight": "bold", "color": "#FFFFFF", "margin": "xs"},
            {"type": "box", "layout": "horizontal", "spacing": "xs", "margin": "md", "contents": week_cells}
        ]
    }
    
    body_contents = []
    
    # --- [2] 天気カード ---
    pops = weather_data.get("pops", {})
    weather_periods = weather_data.get("weather_by_period", {})
    rain_notice = (weather_data.get("rain_notice", "") or "").strip()
    if not rain_notice:
        rain_notice = "夜から雨が降りそう" if max_pop >= 40 else "傘なしでお出かけOK"
    short_w = (weather_data.get("short_weather", "") or "").strip() or "晴れ"
    
    # 天気グラデーション判定
    # 晴れのち曇り -> 左オレンジフェードで→右灰色
    if ("晴" in short_w) and ("くもり" in short_w or "曇" in short_w):
        wbox_start, wbox_end, wbox_border = "#FFF3E0", "#E9ECEF", "#CED4DA"
        second_w_icon = "cloudy"
    elif ("晴" in short_w) and ("雨" in short_w or max_pop >= 40):
        wbox_start, wbox_end, wbox_border = "#FFF3E0", "#D9EEFC", "#BCE0F8"
        second_w_icon = "rainy"
    elif ("くもり" in short_w or "曇" in short_w) and ("晴" in short_w):
        wbox_start, wbox_end, wbox_border = "#E9ECEF", "#FFF3E0", "#FFD8A8"
        second_w_icon = "sunny"
    elif "雨" in short_w or max_pop >= 40:
        wbox_start, wbox_end, wbox_border = "#EBF5FF", "#D9EEFC", "#BCE0F8"
        second_w_icon = "rainy"
    elif "くもり" in short_w or "曇" in short_w:
        wbox_start, wbox_end, wbox_border = "#FFFFFF", "#E9ECEF", "#CED4DA"
        second_w_icon = "cloudy"
    else:
        wbox_start, wbox_end, wbox_border = "#FFFFFF", "#FFE8D6", "#FFD8A8"
        second_w_icon = "sunny"
    
    weather_contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "alignItems": "center",
            "contents": [
                {"type": "image", "url": get_icon_url("badge_weather", repo_name), "size": "26px", "flex": 0},
                {"type": "text", "text": " 天気", "weight": "bold", "size": "md", "color": "#8A4B1A", "margin": "xs", "flex": 0},
                {"type": "text", "text": config.get("area_name", "横浜") or "横浜", "size": "xs", "color": "#888888", "align": "end", "flex": 1}
            ]
        },

        # 天気メイン枠
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "background": {"type": "linearGradient", "angle": "90deg", "startColor": wbox_start, "endColor": wbox_end},
            "cornerRadius": "12px",
            "borderWidth": "1px",
            "borderColor": wbox_border,
            "paddingAll": "10px",
            "alignItems": "center",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "alignItems": "center",
                    "flex": 0,
                    "contents": [
                        {"type": "image", "url": get_icon_url("sunny" if "晴" in short_w else "cloudy", repo_name), "size": "32px", "flex": 0},
                        {"type": "image", "url": get_icon_url("arrow_right", repo_name), "size": "12px", "margin": "xs", "flex": 0},
                        {"type": "image", "url": get_icon_url(second_w_icon, repo_name), "size": "32px", "margin": "xs", "flex": 0}
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 1,
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "今日の天気", "size": "xxs", "color": "#6E8B9E"},
                        {"type": "text", "text": short_w, "size": "md", "weight": "bold", "color": "#2A6496"},
                        {"type": "text", "text": rain_notice, "size": "xxs", "color": "#5A788E"}
                    ]
                }
            ]
        },
        # 気温
        {
            "type": "box",
            "layout": "baseline",
            "margin": "sm",
            "contents": [
                {"type": "text", "text": "最高", "size": "xs", "color": "#888888"},
                {"type": "text", "text": f" {weather_data.get('temp_max', '--')}°", "size": "xl", "weight": "bold", "color": "#E0561B"},
                {"type": "text", "text": "   最低", "size": "xs", "color": "#888888", "margin": "md"},
                {"type": "text", "text": f" {weather_data.get('temp_min', '--')}°", "size": "md", "weight": "bold", "color": "#2E6FB5"}
            ]
        },
        # タイムライン
        {
            "type": "box",
            "layout": "vertical",
            "margin": "sm",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "image", "url": get_icon_url(weather_periods.get("6-12", "sunny"), repo_name), "size": "18px", "align": "center"},
                        {"type": "image", "url": get_icon_url(weather_periods.get("12-18", "cloudy"), repo_name), "size": "18px", "align": "center"},
                        {"type": "image", "url": get_icon_url(weather_periods.get("18-24", "rainy"), repo_name), "size": "18px", "align": "center"}
                    ]
                },
                {
                    "type": "image",
                    "url": get_icon_url("timeline_bar_3d", repo_name),
                    "size": "full",
                    "aspectRatio": "24:1",
                    "aspectMode": "cover",
                    "margin": "xs"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "xs",
                    "contents": [
                        {"type": "text", "text": "6時", "size": "xxs", "color": "#9E9E9E", "flex": 1},
                        {"type": "text", "text": "12時", "size": "xxs", "color": "#9E9E9E", "align": "center", "flex": 1},
                        {"type": "text", "text": "18時", "size": "xxs", "color": "#9E9E9E", "align": "center", "flex": 1},
                        {"type": "text", "text": "24時", "size": "xxs", "color": "#9E9E9E", "align": "end", "flex": 1}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": pops.get("6-12", "-"), "size": "xs", "weight": "bold", "color": "#333333", "align": "center", "flex": 1},
                        {"type": "text", "text": pops.get("12-18", "-"), "size": "xs", "weight": "bold", "color": "#333333", "align": "center", "flex": 1},
                        {"type": "text", "text": pops.get("18-24", "-"), "size": "xs", "weight": "bold", "color": "#2E6FB5" if "50" in pops.get("18-24", "") else "#333333", "align": "center", "flex": 1}
                    ]
                }
            ]
        },
        # 3ピル (傘・洗濯・服) - 立体ボタンアイコン（左寄せ）
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "backgroundColor": umb_bg,
            "cornerRadius": "18px",
            "paddingAll": "6px",
            "alignItems": "center",
            "contents": [
                {"type": "image", "url": get_icon_url(umb_icon, repo_name), "size": "24px", "flex": 0},
                {"type": "text", "text": umb_t, "size": "xs", "weight": "bold", "color": umb_c, "margin": "sm", "flex": 1}
            ]
        },
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "xs",
            "backgroundColor": lnd_bg,
            "cornerRadius": "18px",
            "paddingAll": "6px",
            "alignItems": "center",
            "contents": [
                {"type": "image", "url": get_icon_url(lnd_icon, repo_name), "size": "24px", "flex": 0},
                {"type": "text", "text": lnd_t, "size": "xs", "weight": "bold", "color": lnd_c, "margin": "sm", "flex": 1}
            ]
        },
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "xs",
            "backgroundColor": "#F5EEFA",
            "cornerRadius": "18px",
            "paddingAll": "6px",
            "alignItems": "center",
            "contents": [
                {"type": "image", "url": get_icon_url("pill_clothing", repo_name), "size": "24px", "flex": 0},
                {"type": "text", "text": clothing_text, "size": "xs", "weight": "bold", "color": "#5B21B6", "margin": "sm", "wrap": True, "flex": 1}
            ]
        },
        # 気象庁ボタン
        {
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "backgroundColor": "#8A2E0A",
            "cornerRadius": "16px",
            "paddingBottom": "2px",
            "action": {"type": "uri", "label": "気象庁", "uri": f"https://www.jma.go.jp/bosai/forecast/#area_type=offices&area_code={config.get('area_code', '140000')}"},
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "background": {"type": "linearGradient", "angle": "180deg", "startColor": "#FFA94D", "endColor": "#E8590C"},
                    "cornerRadius": "14px",
                    "paddingTop": "7px",
                    "paddingBottom": "7px",
                    "justifyContent": "center",
                    "contents": [{"type": "text", "text": "☁ 気象庁で詳しく見る 〉", "size": "xs", "weight": "bold", "color": "#FFFFFF", "align": "center"}]
                }
            ]
        }
    ]
    body_contents.append(card_box(weather_contents, border="#E58C3A", shadow="#5C3A21"))
    
    # --- [3] ゴミカード ---
    trash_cells = []
    for i in range(7):
        curr_d = sunday + timedelta(days=i)
        w_k = WEEKDAY_SUNDAY_FIRST_JA[i]
        is_today = (curr_d == now.date())
        t_info = weekly_schedule.get(w_k)
        
        if is_today:
            bg = "#FF922B"
            bc = "#D9480F"
            bw = "1.5px"
            tc = "#FFFFFF"
            lbl = "今日"
            icon_name = "flame_white" if (t_info and t_info.get("icon") == "flame") else (t_info.get("icon", "flame") if t_info else "flame_white")
        else:
            bg = "#FFFFFF"
            bc = "#FFD8A8"
            bw = "1px"
            tc = "#8A4B1A"
            lbl = (t_info["short"] if t_info else "ー")
            icon_name = t_info.get("icon", "flame") if t_info else None
        
        cell_inner = [
            {"type": "text", "text": w_k, "size": "xxs", "weight": "bold", "color": tc, "align": "center"}
        ]
        if icon_name:
            cell_inner.append({"type": "image", "url": get_icon_url(icon_name, repo_name), "size": "16px", "align": "center", "margin": "xs"})
        else:
            cell_inner.append({"type": "text", "text": "ー", "size": "xs", "color": "#DDAA88", "align": "center", "margin": "xs"})
        cell_inner.append({"type": "text", "text": lbl, "size": "xxs", "weight": "bold" if is_today else "regular", "color": tc, "align": "center", "margin": "xs"})
        
        trash_cells.append({
            "type": "box",
            "layout": "vertical",
            "backgroundColor": bg,
            "cornerRadius": "8px",
            "borderWidth": bw,
            "borderColor": bc,
            "paddingTop": "4px",
            "paddingBottom": "4px",
            "alignItems": "center",
            "flex": 1,
            "contents": cell_inner
        })
    
    trash_contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "alignItems": "center",
            "contents": [
                {"type": "image", "url": get_icon_url("badge_trash", repo_name), "size": "26px", "flex": 0},
                {"type": "text", "text": " ゴミ", "weight": "bold", "size": "md", "color": "#5C2607", "margin": "xs", "flex": 0}
            ]
        },
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "md",
            "alignItems": "center",
            "contents": [
                {"type": "image", "url": get_icon_url("trash_sphere", repo_name), "size": "44px", "flex": 0},
                {"type": "text", "text": today_trash.get("label", "ゴミ出しなし") if today_trash else "本日のゴミ出しはありません", "weight": "bold", "size": "lg", "color": "#4E2A14", "margin": "md", "flex": 1, "wrap": True}
            ]
        },
        {"type": "box", "layout": "horizontal", "spacing": "xs", "margin": "md", "contents": trash_cells}
    ]
    trash_gradient = {"type": "linearGradient", "angle": "180deg", "startColor": "#FFF5ED", "endColor": "#FFE7D6"}
    body_contents.append(card_box(trash_contents, border="#D96520", bg_gradient=trash_gradient, shadow="#5C3A21"))
    
    # --- [4] 予定カード ---
    cal_today = calendar_data.get("today", [])
    cal_tomorrow = calendar_data.get("tomorrow", [])
    cal_week = calendar_data.get("week", [])
    
    cal_contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "alignItems": "center",
            "contents": [
                {"type": "image", "url": get_icon_url("badge_calendar", repo_name), "size": "26px", "flex": 0},
                {"type": "text", "text": " 予定", "weight": "bold", "size": "md", "color": "#1A4B7D", "margin": "xs", "flex": 0}
            ]
        },
        {
            "type": "box",
            "layout": "baseline",
            "margin": "sm",
            "contents": [{"type": "text", "text": "今日", "color": "#FFFFFF", "size": "xs", "weight": "bold", "align": "center"}],
            "backgroundColor": "#3B82F6",
            "cornerRadius": "10px",
            "paddingStart": "8px", "paddingEnd": "8px", "paddingTop": "2px", "paddingBottom": "2px",
            "width": "46px"
        }
    ]
    
    if cal_today:
        for ev in cal_today:
            ev = (ev or "").strip()
            if not ev:
                continue
            if ev.startswith("ほか"):
                cal_contents.append({
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "xs",
                    "contents": [
                        {"type": "text", "text": ev, "size": "xs", "color": "#888888", "margin": "md"}
                    ]
                })
                continue
            parts = ev.split(" ", 1)
            if len(parts) > 1:
                t_str = parts[0].strip() or "終日"
                title_str = parts[1].strip() or "予定あり"
            else:
                t_str = "終日"
                title_str = ev
            cal_contents.append({
                "type": "box",
                "layout": "horizontal",
                "margin": "sm",
                "alignItems": "center",
                "contents": [
                    {"type": "image", "url": get_icon_url("dot_blue", repo_name), "size": "10px", "flex": 0},
                    {"type": "text", "text": t_str, "size": "sm", "weight": "bold", "color": "#2B6CB0", "flex": 0, "margin": "sm"},
                    {"type": "text", "text": title_str, "size": "sm", "weight": "bold", "color": "#1A1A1A", "flex": 1, "margin": "md", "wrap": True}
                ]
            })
    else:
        cal_contents.append({"type": "text", "text": "今日の予定はありません", "size": "xs", "color": "#888888", "margin": "xs"})
    
    if cal_tomorrow:
        cal_contents.append({
            "type": "box",
            "layout": "baseline",
            "margin": "md",
            "contents": [{"type": "text", "text": "明日", "color": "#1E40AF", "size": "xxs", "weight": "bold", "align": "center"}],
            "backgroundColor": "#DBEAFE",
            "cornerRadius": "8px",
            "paddingStart": "6px", "paddingEnd": "6px", "paddingTop": "2px", "paddingBottom": "2px",
            "width": "38px"
        })
        for ev in cal_tomorrow:
            ev = (ev or "").strip()
            if not ev:
                continue
            if ev.startswith("ほか"):
                cal_contents.append({
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "xs",
                    "contents": [
                        {"type": "text", "text": ev, "size": "xs", "color": "#888888", "margin": "md"}
                    ]
                })
                continue
            parts = ev.split(" ", 1)
            if len(parts) > 1:
                t_str = parts[0].strip() or "終日"
                title_str = parts[1].strip() or "予定あり"
            else:
                t_str = "終日"
                title_str = ev
            cal_contents.append({
                "type": "box",
                "layout": "horizontal",
                "margin": "xs",
                "alignItems": "center",
                "contents": [
                    {"type": "image", "url": get_icon_url("dot_light_blue", repo_name), "size": "8px", "flex": 0},
                    {"type": "text", "text": t_str, "size": "xs", "color": "#556B82", "flex": 0, "margin": "sm"},
                    {"type": "text", "text": title_str, "size": "xs", "color": "#2B3B4C", "flex": 1, "margin": "md", "wrap": True}
                ]
            })
    
    if cal_week:
        cal_contents.append({
            "type": "box",
            "layout": "baseline",
            "margin": "md",
            "contents": [{"type": "text", "text": "この先1週間", "color": "#4B5563", "size": "xxs", "weight": "bold", "align": "center"}],
            "backgroundColor": "#E5E7EB",
            "cornerRadius": "8px",
            "paddingStart": "6px", "paddingEnd": "6px", "paddingTop": "2px", "paddingBottom": "2px",
            "width": "68px"
        })
        for ev in cal_week:
            ev = (ev or "").strip()
            if not ev:
                continue
            cal_contents.append({
                "type": "box",
                "layout": "horizontal",
                "margin": "xs",
                "alignItems": "center",
                "contents": [
                    {"type": "image", "url": get_icon_url("dot_grey", repo_name), "size": "6px", "flex": 0},
                    {"type": "text", "text": ev, "size": "xxs", "color": "#4B5563", "flex": 1, "margin": "sm", "wrap": True}
                ]
            })
    
    # カレンダーボタン
    cal_contents.append({
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "backgroundColor": "#1E40AF",
        "cornerRadius": "16px",
        "paddingBottom": "2px",
        "action": {"type": "uri", "label": "カレンダー", "uri": "https://calendar.google.com/calendar/"},
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "background": {"type": "linearGradient", "angle": "180deg", "startColor": "#60A5FA", "endColor": "#2563EB"},
                "cornerRadius": "14px",
                "paddingTop": "7px",
                "paddingBottom": "7px",
                "justifyContent": "center",
                "contents": [{"type": "text", "text": "📅 カレンダーを開く 〉", "size": "xs", "weight": "bold", "color": "#FFFFFF", "align": "center"}]
            }
        ]
    })
    cal_gradient = {"type": "linearGradient", "angle": "180deg", "startColor": "#F3F8FE", "endColor": "#E4EFFD"}
    body_contents.append(card_box(cal_contents, border="#4A90E2", bg_gradient=cal_gradient, shadow="#1B3B60"))
    
    # --- [5] 釣りカード（城ヶ島のみ） ---
    fishing_spots = weather_data.get("fishing_spots", [])
    if fishing_spots:
        fish_contents = [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "contents": [
                    {"type": "image", "url": get_icon_url("badge_fishing", repo_name), "size": "26px", "flex": 0},
                    {"type": "text", "text": " 釣り", "weight": "bold", "size": "md", "color": "#0C5A75", "margin": "xs", "flex": 0}
                ]
            }
        ]
        
        ai_hobbies = {h.get("name"): h for h in ai_summary.get("hobbies", [])}
        for spot in fishing_spots:
            s_name = (spot.get("name") or "城ヶ島").strip() or "城ヶ島"
            # 木更津は除外（城ヶ島のみ表示）
            if "木更津" in s_name:
                continue
            sc = ai_hobbies.get(s_name, {}).get("score", 4)
            cm = (ai_hobbies.get(s_name, {}).get("comment") or "").strip() or "朝は穏やか。昼から風が強まるので早めに"
            
            f_icons = []
            for j in range(1, 6):
                f_icons.append({"type": "image", "url": get_icon_url("fish_on" if j <= sc else "fish_off", repo_name), "size": "16px"})
            
            is_high = spot.get("is_high_wave", False)
            w_bg = "#FEE2E2" if is_high else "#E0F2FE"
            w_c = "#DC2626" if is_high else "#0369A1"
            
            w_lbl = (spot.get('wind_label') or "-").strip() or "-"
            wv_lbl = (spot.get('wave_label') or "-").strip() or "-"
            
            fish_contents.append({
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#FFFFFF",
                "cornerRadius": "10px",
                "borderWidth": "1px",
                "borderColor": "#BCE3EC",
                "paddingAll": "10px",
                "margin": "sm",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "alignItems": "center",
                        "contents": [
                            {"type": "text", "text": s_name, "weight": "bold", "size": "sm", "color": "#1A1A1A", "flex": 1},
                            {"type": "box", "layout": "horizontal", "contents": f_icons, "alignItems": "center", "spacing": "xs", "flex": 0}
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "margin": "xs",
                        "spacing": "xs",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "backgroundColor": "#FFFFFF",
                                "cornerRadius": "10px",
                                "borderWidth": "1px",
                                "borderColor": "#CED4DA",
                                "paddingStart": "6px", "paddingEnd": "6px", "paddingTop": "2px", "paddingBottom": "2px",
                                "alignItems": "center",
                                "flex": 0,
                                "contents": [
                                    {"type": "image", "url": get_icon_url(spot.get("wind_icon", "wind"), repo_name), "size": "12px", "flex": 0},
                                    {"type": "text", "text": f" {w_lbl}", "size": "xxs", "color": "#495057", "margin": "xs", "flex": 0}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "backgroundColor": w_bg,
                                "cornerRadius": "10px",
                                "paddingStart": "6px", "paddingEnd": "6px", "paddingTop": "2px", "paddingBottom": "2px",
                                "alignItems": "center",
                                "flex": 0,
                                "contents": [
                                    {"type": "image", "url": get_icon_url("wave", repo_name), "size": "12px", "flex": 0},
                                    {"type": "text", "text": f" {wv_lbl}", "size": "xxs", "weight": "bold" if is_high else "regular", "color": w_c, "margin": "xs", "flex": 0}
                                ]
                            }
                        ]
                    },
                    {"type": "text", "text": cm, "size": "xxs", "color": "#334155", "margin": "xs", "wrap": True}
                ]
            })
        
        fish_gradient = {"type": "linearGradient", "angle": "180deg", "startColor": "#F0FBFC", "endColor": "#D8F3F7"}
        body_contents.append(card_box(fish_contents, border="#2BB0C7", bg_gradient=fish_gradient, shadow="#0E4A59"))
    
    # 出典表記
    body_contents.append({
        "type": "text",
        "text": "天気の出典: 気象庁",
        "size": "xxs",
        "color": "#A0AEC0",
        "align": "end",
        "margin": "md"
    })
    
    bubble = {
        "type": "bubble",
        "size": "giga",
        "styles": {"body": {"backgroundColor": "#FFF8EE"}},
        "header": header,
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "14px",
            "backgroundColor": "#FFF8EE",
            "contents": body_contents
        }
    }
    
    return {
        "type": "flex",
        "altText": alt_text,
        "contents": bubble
    }
