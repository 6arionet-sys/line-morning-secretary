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
    return f"https://raw.githubusercontent.com/{repo_name}/main/icons/{icon_name}"

def card_box(contents, border="#B85A0E", bg="#FFF", shadow="#3A2A1E", pad="12px", margin="lg"):
    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": shadow,
        "cornerRadius": "14px",
        "paddingBottom": "4px",
        "paddingEnd": "4px",
        "margin": margin,
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": bg,
                "cornerRadius": "12px",
                "borderWidth": "2px",
                "borderColor": border,
                "paddingAll": pad,
                "contents": contents
            }
        ]
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
    
    # 傘・洗濯・服装
    if max_pop >= 50:
        umb_t, umb_bg, umb_c, umb_icon = f"傘が必要　夜は雨 {max_pop}%", "#E8F1FC", "#2E6FB5", "umbrella"
    elif max_pop >= 30:
        umb_t, umb_bg, umb_c, umb_icon = f"折りたたみ傘　降水確率 {max_pop}%", "#F1F3F5", "#495057", "umbrella_small"
    else:
        umb_t, umb_bg, umb_c, umb_icon = f"傘はいらない　降水確率 {max_pop}%", "#FFF9DB", "#D97706", "umbrella_off"
    
    laundry_st = weather_data.get("laundry", {}).get("status", "一日中OK")
    if "一日中" in laundry_st:
        lnd_t, lnd_bg, lnd_c, lnd_icon = "洗濯 一日中OK　気持ちよく乾く", "#E6F6EE", "#2E9E66", "hanger"
    elif "6〜18" in laundry_st or "OK" in laundry_st:
        lnd_t, lnd_bg, lnd_c, lnd_icon = "洗濯 6〜18時OK　夕方には取り込む", "#E6F6EE", "#2E9E66", "hanger"
    else:
        lnd_t, lnd_bg, lnd_c, lnd_icon = "洗濯 部屋干し推奨　雨や高湿度に注意", "#F8F9FA", "#868E96", "home"
    
    clothing_text = ai_summary.get("clothing_comment", "日中は快適。朝晩は薄手の上着を")
    
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
        dots = "●●" if ev_cnt >= 2 else ("●" if ev_cnt == 1 else " ")
        
        bg = "#FFF" if is_today else "#FFFFFF33"
        c = "#E03131" if is_today else "#FFF"
        bw = "2px" if is_today else "0px"
        bc = "#E03131" if is_today else "#0000"
        
        week_cells.append({
            "type": "box",
            "layout": "vertical",
            "backgroundColor": bg,
            "cornerRadius": "6px",
            "borderWidth": bw,
            "borderColor": bc,
            "paddingTop": "4px",
            "paddingBottom": "4px",
            "alignItems": "center",
            "flex": 1,
            "contents": [
                {"type": "text", "text": WEEKDAY_SUNDAY_FIRST_JA[i], "size": "xxs", "weight": "bold", "color": c, "align": "center"},
                {"type": "text", "text": str(curr_d.day), "size": "xs", "weight": "bold", "color": c, "align": "center", "margin": "xs"},
                {"type": "text", "text": dots, "size": "xxs", "color": c, "align": "center"}
            ]
        })
    
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
                    {"type": "text", "text": f"{month}.{day} {w_en}", "size": "sm", "weight": "bold", "color": "#FFFA"},
                    {"type": "image", "url": get_icon_url("sunny", repo_name), "size": "24px", "align": "end"}
                ]
            },
            {"type": "text", "text": "おはようございます", "size": "xl", "weight": "bold", "color": "#FFF", "margin": "xs"},
            {"type": "box", "layout": "horizontal", "spacing": "xs", "margin": "md", "contents": week_cells}
        ]
    }
    
    body_contents = []
    
    # --- [2] 天気カード ---
    pops = weather_data.get("pops", {})
    weather_periods = weather_data.get("weather_by_period", {})
    rain_notice = weather_data.get("rain_notice", "夜から雨が降りそう" if max_pop >= 40 else "傘なしでお出かけOK")
    short_w = weather_data.get("short_weather", "晴れ")
    
    weather_contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "alignItems": "center",
            "contents": [
                {"type": "image", "url": get_icon_url("sunny", repo_name), "size": "20px"},
                {"type": "text", "text": " 天気", "weight": "bold", "size": "md", "color": "#8A4B1A"},
                {"type": "text", "text": config.get("area_name", "横浜"), "size": "xs", "color": "#888", "align": "end"}
            ]
        },
        # 天気メイン枠
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "background": {"type": "linearGradient", "angle": "180deg", "startColor": "#FFF", "endColor": "#D9EEFC"},
            "cornerRadius": "10px",
            "borderWidth": "1px",
            "borderColor": "#BCE0F8",
            "paddingAll": "10px",
            "alignItems": "center",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "alignItems": "center",
                    "flex": 4,
                    "contents": [
                        {"type": "image", "url": get_icon_url("sunny", repo_name), "size": "28px"},
                        {"type": "text", "text": "→", "size": "sm", "color": "#7590A6", "margin": "xs"},
                        {"type": "image", "url": get_icon_url("rainy" if max_pop >= 40 else "cloudy", repo_name), "size": "28px", "margin": "xs"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "flex": 5,
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
                {"type": "text", "text": "最高", "size": "xs", "color": "#888"},
                {"type": "text", "text": f" {weather_data.get('temp_max', '--')}°", "size": "xl", "weight": "bold", "color": "#E0561B"},
                {"type": "text", "text": "   最低", "size": "xs", "color": "#888", "margin": "md"},
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
                        {"type": "image", "url": get_icon_url(weather_periods.get("6-12", "sunny"), repo_name), "size": "14px", "align": "center"},
                        {"type": "image", "url": get_icon_url(weather_periods.get("12-18", "cloudy"), repo_name), "size": "14px", "align": "center"},
                        {"type": "image", "url": get_icon_url(weather_periods.get("18-24", "rainy"), repo_name), "size": "14px", "align": "center"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "height": "6px",
                    "cornerRadius": "3px",
                    "margin": "xs",
                    "contents": [
                        {"type": "box", "layout": "vertical", "backgroundColor": "#FFB566", "flex": 1},
                        {"type": "box", "layout": "vertical", "backgroundColor": "#DDE1E8", "flex": 1},
                        {"type": "box", "layout": "vertical", "backgroundColor": "#6AA6EC", "flex": 1}
                    ]
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
                        {"type": "text", "text": pops.get("6-12", "-"), "size": "xs", "weight": "bold", "color": "#333", "align": "center", "flex": 1},
                        {"type": "text", "text": pops.get("12-18", "-"), "size": "xs", "weight": "bold", "color": "#333", "align": "center", "flex": 1},
                        {"type": "text", "text": pops.get("18-24", "-"), "size": "xs", "weight": "bold", "color": "#2E6FB5" if "50" in pops.get("18-24", "") else "#333", "align": "center", "flex": 1}
                    ]
                }
            ]
        },
        # 3ピル (傘・洗濯・服)
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "backgroundColor": umb_bg,
            "cornerRadius": "16px",
            "paddingAll": "6px",
            "alignItems": "center",
            "contents": [
                {
                    "type": "box", "layout": "vertical", "backgroundColor": "#3F84D6", "cornerRadius": "10px", "width": "20px", "height": "20px", "justifyContent": "center", "alignItems": "center",
                    "contents": [{"type": "image", "url": get_icon_url(umb_icon, repo_name), "size": "12px"}]
                },
                {"type": "text", "text": umb_t, "size": "xs", "weight": "bold", "color": "#1A4B75", "margin": "sm"}
            ]
        },
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "xs",
            "backgroundColor": lnd_bg,
            "cornerRadius": "16px",
            "paddingAll": "6px",
            "alignItems": "center",
            "contents": [
                {
                    "type": "box", "layout": "vertical", "backgroundColor": "#2E9E66", "cornerRadius": "10px", "width": "20px", "height": "20px", "justifyContent": "center", "alignItems": "center",
                    "contents": [{"type": "image", "url": get_icon_url(lnd_icon, repo_name), "size": "12px"}]
                },
                {"type": "text", "text": lnd_t, "size": "xs", "weight": "bold", "color": "#1E5E3E", "margin": "sm"}
            ]
        },
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "xs",
            "backgroundColor": "#F3ECFC",
            "cornerRadius": "16px",
            "paddingAll": "6px",
            "alignItems": "center",
            "contents": [
                {
                    "type": "box", "layout": "vertical", "backgroundColor": "#8E6BCB", "cornerRadius": "10px", "width": "20px", "height": "20px", "justifyContent": "center", "alignItems": "center",
                    "contents": [{"type": "text", "text": "👔", "size": "xxs"}]
                },
                {"type": "text", "text": clothing_text, "size": "xs", "weight": "bold", "color": "#4B3A66", "margin": "sm", "wrap": True}
            ]
        },
        # 気象庁ボタン
        {
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "backgroundColor": "#3A2A1E",
            "cornerRadius": "16px",
            "paddingBottom": "2px",
            "action": {"type": "uri", "label": "気象庁", "uri": f"https://www.jma.go.jp/bosai/forecast/#area_type=offices&area_code={config.get('area_code', '140000')}"},
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "background": {"type": "linearGradient", "angle": "180deg", "startColor": "#FFA34D", "endColor": "#F76B1C"},
                    "cornerRadius": "14px",
                    "paddingTop": "6px",
                    "paddingBottom": "6px",
                    "justifyContent": "center",
                    "contents": [{"type": "text", "text": "☁ 気象庁で詳しく見る 〉", "size": "xs", "weight": "bold", "color": "#FFF", "align": "center"}]
                }
            ]
        }
    ]
    body_contents.append(card_box(weather_contents, border="#B85A0E", shadow="#3A2A1E"))
    
    # --- [3] ゴミカード ---
    trash_cells = []
    for i in range(7):
        curr_d = sunday + timedelta(days=i)
        w_k = WEEKDAY_SUNDAY_FIRST_JA[i]
        is_today = (curr_d == now.date())
        t_info = weekly_schedule.get(w_k)
        
        bg = "#FFA94D" if is_today else "#FFF"
        bc = "#E8590C" if is_today else "#FFD8A8"
        bw = "2px" if is_today else "1px"
        c = "#FFF" if is_today else "#8A4B1A"
        lbl = "今日" if is_today else (t_info["short"] if t_info else "ー")
        
        cell_inner = [
            {"type": "text", "text": w_k, "size": "xxs", "weight": "bold", "color": c, "align": "center"}
        ]
        if t_info:
            cell_inner.append({"type": "image", "url": get_icon_url(t_info.get("icon", "flame"), repo_name), "size": "16px", "align": "center", "margin": "xs"})
        else:
            cell_inner.append({"type": "text", "text": "ー", "size": "xs", "color": "#DDAA88", "align": "center", "margin": "xs"})
        cell_inner.append({"type": "text", "text": lbl, "size": "xxs", "weight": "bold" if is_today else "regular", "color": c, "align": "center", "margin": "xs"})
        
        trash_cells.append({
            "type": "box",
            "layout": "vertical",
            "backgroundColor": bg,
            "cornerRadius": "6px",
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
                {"type": "image", "url": get_icon_url("trash", repo_name), "size": "18px"},
                {"type": "text", "text": " ゴミ", "weight": "bold", "size": "md", "color": "#8A4B1A"}
            ]
        },
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "sm",
            "alignItems": "center",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#D9480F",
                    "cornerRadius": "20px",
                    "paddingBottom": "2px",
                    "width": "40px",
                    "height": "40px",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "background": {"type": "linearGradient", "angle": "180deg", "startColor": "#FF922B", "endColor": "#E8590C"},
                            "cornerRadius": "18px",
                            "width": "40px",
                            "height": "38px",
                            "justifyContent": "center",
                            "alignItems": "center",
                            "contents": [{"type": "image", "url": get_icon_url(today_trash.get("icon", "flame") if today_trash else "trash", repo_name), "size": "22px"}]
                        }
                    ]
                },
                {"type": "text", "text": today_trash.get("label", "ゴミ出しなし") if today_trash else "本日のゴミ出しはありません", "weight": "bold", "size": "lg", "color": "#3A2A1E", "margin": "md"}
            ]
        },
        {"type": "box", "layout": "horizontal", "spacing": "xs", "margin": "md", "contents": trash_cells}
    ]
    body_contents.append(card_box(trash_contents, border="#8A2E0A", shadow="#3A2A1E", bg="#FFF5EC"))
    
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
                {
                    "type": "box", "layout": "vertical", "backgroundColor": "#1864AB", "cornerRadius": "6px", "width": "20px", "height": "20px", "justifyContent": "center", "alignItems": "center",
                    "contents": [{"type": "image", "url": get_icon_url("calendar", repo_name), "size": "14px"}]
                },
                {"type": "text", "text": " 予定", "weight": "bold", "size": "md", "color": "#123F73"}
            ]
        },
        {
            "type": "box",
            "layout": "baseline",
            "margin": "sm",
            "contents": [{"type": "text", "text": "今日", "color": "#FFF", "size": "xs", "weight": "bold", "align": "center"}],
            "backgroundColor": "#2F78C8",
            "cornerRadius": "10px",
            "paddingStart": "8px", "paddingEnd": "8px", "paddingTop": "2px", "paddingBottom": "2px",
            "width": "46px"
        }
    ]
    
    if cal_today:
        for ev in cal_today:
            parts = ev.split(" ", 1)
            t_str, title_str = (parts[0], parts[1]) if len(parts) > 1 else ("", ev)
            cal_contents.append({
                "type": "box",
                "layout": "horizontal",
                "margin": "xs",
                "alignItems": "center",
                "contents": [
                    {"type": "text", "text": "●", "size": "xs", "color": "#2F78C8"},
                    {"type": "text", "text": t_str, "size": "sm", "weight": "bold", "color": "#2F78C8", "margin": "xs"},
                    {"type": "text", "text": title_str, "size": "sm", "weight": "bold", "color": "#1A1A1A", "margin": "sm", "wrap": True}
                ]
            })
    else:
        cal_contents.append({"type": "text", "text": "今日の予定はありません", "size": "xs", "color": "#888", "margin": "xs"})
    
    if cal_tomorrow:
        cal_contents.append({
            "type": "box",
            "layout": "baseline",
            "margin": "md",
            "contents": [{"type": "text", "text": "明日", "color": "#123F73", "size": "xxs", "weight": "bold", "align": "center"}],
            "backgroundColor": "#D6E4FF",
            "cornerRadius": "8px",
            "paddingStart": "6px", "paddingEnd": "6px", "paddingTop": "2px", "paddingBottom": "2px",
            "width": "38px"
        })
        for ev in cal_tomorrow:
            parts = ev.split(" ", 1)
            t_str, title_str = (parts[0], parts[1]) if len(parts) > 1 else ("", ev)
            cal_contents.append({
                "type": "box",
                "layout": "horizontal",
                "margin": "xs",
                "alignItems": "center",
                "contents": [
                    {"type": "text", "text": "●", "size": "xs", "color": "#6FA9EA"},
                    {"type": "text", "text": t_str, "size": "xs", "color": "#555", "margin": "xs"},
                    {"type": "text", "text": title_str, "size": "xs", "color": "#333", "margin": "sm", "wrap": True}
                ]
            })
    
    if cal_week:
        cal_contents.append({
            "type": "box",
            "layout": "baseline",
            "margin": "md",
            "contents": [{"type": "text", "text": "この先1週間", "color": "#666", "size": "xxs", "weight": "bold", "align": "center"}],
            "backgroundColor": "#EEE",
            "cornerRadius": "8px",
            "paddingStart": "6px", "paddingEnd": "6px", "paddingTop": "2px", "paddingBottom": "2px",
            "width": "68px"
        })
        for ev in cal_week:
            cal_contents.append({
                "type": "box",
                "layout": "horizontal",
                "margin": "xs",
                "contents": [
                    {"type": "text", "text": "•", "size": "xs", "color": "#999"},
                    {"type": "text", "text": ev, "size": "xxs", "color": "#666", "margin": "xs", "wrap": True}
                ]
            })
    
    # カレンダーボタン
    cal_contents.append({
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "backgroundColor": "#123F73",
        "cornerRadius": "16px",
        "paddingBottom": "2px",
        "action": {"type": "uri", "label": "カレンダー", "uri": "https://calendar.google.com/calendar/"},
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "background": {"type": "linearGradient", "angle": "180deg", "startColor": "#4DABF7", "endColor": "#1971C2"},
                "cornerRadius": "14px",
                "paddingTop": "6px",
                "paddingBottom": "6px",
                "justifyContent": "center",
                "contents": [{"type": "text", "text": "📅 カレンダーを開く 〉", "size": "xs", "weight": "bold", "color": "#FFF", "align": "center"}]
            }
        ]
    })
    body_contents.append(card_box(cal_contents, border="#123F73", shadow="#3A2A1E"))
    
    # --- [5] 釣りカード ---
    fishing_spots = weather_data.get("fishing_spots", [])
    if fishing_spots:
        fish_contents = [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "contents": [
                    {
                        "type": "box", "layout": "vertical", "backgroundColor": "#1E9BC4", "cornerRadius": "6px", "width": "20px", "height": "20px", "justifyContent": "center", "alignItems": "center",
                        "contents": [{"type": "image", "url": get_icon_url("fish_on", repo_name), "size": "14px"}]
                    },
                    {"type": "text", "text": " 釣り", "weight": "bold", "size": "md", "color": "#0C5A75"}
                ]
            }
        ]
        
        ai_hobbies = {h.get("name"): h for h in ai_summary.get("hobbies", [])}
        for spot in fishing_spots:
            s_name = spot.get("name", "釣り場")
            sc = ai_hobbies.get(s_name, {}).get("score", 4)
            cm = ai_hobbies.get(s_name, {}).get("comment", "朝は穏やか。昼から風が強まるので早めに")
            
            spot_bg = "#EEFAFE" if sc >= 3 else "#FAFAFA"
            spot_border = "#8FD3EA" if sc >= 3 else "#D2D2D2"
            
            f_icons = []
            for j in range(1, 6):
                f_icons.append({"type": "image", "url": get_icon_url("fish_on" if j <= sc else "fish_off", repo_name), "size": "14px"})
            
            is_high = spot.get("is_high_wave", False)
            w_bg = "#E03131" if is_high else "#E1F0FA"
            w_c = "#FFF" if is_high else "#0C5A75"
            
            fish_contents.append({
                "type": "box",
                "layout": "vertical",
                "backgroundColor": spot_bg,
                "cornerRadius": "8px",
                "borderWidth": "1px",
                "borderColor": spot_border,
                "paddingAll": "10px",
                "margin": "sm",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "alignItems": "center",
                        "contents": [
                            {"type": "text", "text": s_name, "weight": "bold", "size": "sm", "color": "#1A1A1A", "flex": 1},
                            {"type": "box", "layout": "horizontal", "contents": f_icons, "alignItems": "center"}
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
                                "backgroundColor": "#FFF",
                                "cornerRadius": "10px",
                                "borderWidth": "1px",
                                "borderColor": "#CED4DA",
                                "paddingStart": "6px", "paddingEnd": "6px", "paddingTop": "2px", "paddingBottom": "2px",
                                "alignItems": "center",
                                "contents": [
                                    {"type": "image", "url": get_icon_url(spot.get("wind_icon", "wind"), repo_name), "size": "10px"},
                                    {"type": "text", "text": f" {spot.get('wind_label', '-')}", "size": "xxs", "color": "#495057"}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "backgroundColor": w_bg,
                                "cornerRadius": "10px",
                                "paddingStart": "6px", "paddingEnd": "6px", "paddingTop": "2px", "paddingBottom": "2px",
                                "alignItems": "center",
                                "contents": [
                                    {"type": "image", "url": get_icon_url("wave", repo_name), "size": "10px"},
                                    {"type": "text", "text": f" {spot.get('wave_label', '-')}", "size": "xxs", "weight": "bold" if is_high else "regular", "color": w_c}
                                ]
                            }
                        ]
                    },
                    {"type": "text", "text": cm, "size": "xxs", "color": "#333", "margin": "xs", "wrap": True}
                ]
            })
        
        body_contents.append(card_box(fish_contents, border="#0C5A75", shadow="#3A2A1E"))
    
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
