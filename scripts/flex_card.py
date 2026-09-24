import os
import json
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

WEEKDAY_EN = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]
WEEKDAY_SUNDAY_FIRST_JA = ["日", "月", "火", "水", "木", "金", "土"]

def get_icon_url(icon_name, repo_name=None):
    """
    GitHubリポジトリ上のアイコン画像URLを生成する。
    """
    if not repo_name:
        repo_name = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo_name:
        repo_name = "6arionet-sys/line-morning-secretary"
    
    if not icon_name.endswith(".png"):
        icon_name = f"{icon_name}.png"
    
    return f"https://raw.githubusercontent.com/{repo_name}/main/icons/{icon_name}"

def create_3d_box(inner_contents, border_color="#B85A0E", bg_color="#FFFFFF", shadow_color=None, padding="14px", margin="md"):
    """
    立体感（3Dポップスタイル）のあるカードコンポーネントを作成する。
    外枠とシャドウカラーで浮き出たようなポップな立体感を再現。
    """
    if not shadow_color:
        shadow_color = border_color
    
    return {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": shadow_color,
        "cornerRadius": "16px",
        "paddingBottom": "4px",
        "paddingEnd": "4px",
        "margin": margin,
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": bg_color,
                "cornerRadius": "14px",
                "borderWidth": "2px",
                "borderColor": border_color,
                "paddingAll": padding,
                "contents": inner_contents
            }
        ]
    }

def build_flex_message(weather_data, calendar_data, ai_summary, config, repo_name=None):
    """
    視認性とデザイン性を極限まで高めたLINE Flex Messageを生成する。
    """
    now_jst = datetime.now(JST)
    month = now_jst.month
    day = now_jst.day
    w_idx = now_jst.weekday()
    w_en = WEEKDAY_EN[w_idx]
    w_ja = WEEKDAY_JA[w_idx]
    
    weekly_schedule = config.get("weekly_schedule", {})
    today_trash = weekly_schedule.get(w_ja)
    
    # 1. ヘッダー配色（天気に合わせて変化）
    main_type = weather_data.get("main_weather_type", "sunny")
    if main_type == "rainy":
        header_bg_start = "#1E3C72"
        header_bg_end = "#2A5298"
        header_icon = "rainy"
    elif main_type == "cloudy":
        header_bg_start = "#4B6CB7"
        header_bg_end = "#182848"
        header_icon = "cloudy"
    elif main_type == "snowy":
        header_bg_start = "#3A6073"
        header_bg_end = "#3A7BD5"
        header_icon = "snowy"
    else:  # sunny
        header_bg_start = "#FF512F"
        header_bg_end = "#DD2476"
        header_icon = "sunny"
    
    # 傘と洗濯の判定
    max_pop = weather_data.get("max_pop", 0)
    
    # 傘
    if max_pop >= 50:
        umb_title = "傘が必要！"
        umb_sub = f"降水確率 {max_pop}%・雨具を"
        umb_bg = "#228BE6"
        umb_color = "#FFFFFF"
        umb_icon = "umbrella"
        umb_short = "傘必要"
    elif max_pop >= 30:
        umb_title = "折りたたみ傘"
        umb_sub = f"降水確率 {max_pop}%・念のため"
        umb_bg = "#E7F5FF"
        umb_color = "#1971C2"
        umb_icon = "umbrella_small"
        umb_short = "折りたたみ傘"
    else:
        umb_title = "傘はいらない"
        umb_sub = f"降水確率 {max_pop}%・安心です"
        umb_bg = "#FFF3BF"
        umb_color = "#D97706"
        umb_icon = "umbrella_off"
        umb_short = "傘不要"
    
    # 洗濯
    laundry_info = weather_data.get("laundry", {})
    laundry_st = laundry_info.get("status", "一日中OK")
    if "一日中" in laundry_st:
        lnd_title = "外干し日和！"
        lnd_sub = "一日中よく乾きます"
        lnd_bg = "#D3F9D8"
        lnd_color = "#2B8A3E"
        lnd_icon = "hanger"
        lnd_short = "外干しOK"
    elif "6〜18" in laundry_st or "OK" in laundry_st:
        lnd_title = "夕方までOK"
        lnd_sub = "夕方には取り込みを"
        lnd_bg = "#FFF9DB"
        lnd_color = "#E67700"
        lnd_icon = "hanger"
        lnd_short = "夕方まで干せる"
    else:
        lnd_title = "部屋干し推奨"
        lnd_sub = "湿気や雨にご注意を"
        lnd_bg = "#F1F3F5"
        lnd_color = "#495057"
        lnd_icon = "home"
        lnd_short = "部屋干し"
    
    # altTextの生成（通知画面で劇的な変化がわかるようにする！）
    trash_str = f"【{today_trash['label']}】" if today_trash else "【ゴミ出しなし】"
    alt_text = f"【朝の秘書】{month}/{day}({w_ja}) {config.get('area_name', '横浜')} {weather_data.get('temp_max', '--')}℃ / {umb_short} / {lnd_short} / {trash_str}"
    
    # --- [A] ヘッダー ---
    header_component = {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "20px",
        "background": {
            "type": "linearGradient",
            "angle": "135deg",
            "startColor": header_bg_start,
            "endColor": header_bg_end
        },
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            # 日付ラベル
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "backgroundColor": "#1A1A1A",
                                "cornerRadius": "8px",
                                "paddingStart": "10px",
                                "paddingEnd": "10px",
                                "paddingTop": "4px",
                                "paddingBottom": "4px",
                                "width": "115px",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": f"{month}.{day} {w_en}",
                                        "color": "#FFE066",
                                        "size": "sm",
                                        "weight": "bold",
                                        "align": "center"
                                    }
                                ]
                            },
                            {
                                "type": "text",
                                "text": "おはようございます！",
                                "color": "#FFFFFF",
                                "size": "xxl",
                                "weight": "bold",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": f"今日の{config.get('area_name', '横浜')}は {weather_data.get('raw_weather', '良い一日を！')}",
                                "color": "#FFFFFFAA",
                                "size": "xs",
                                "wrap": True,
                                "margin": "sm"
                            }
                        ],
                        "flex": 4
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "image",
                                "url": get_icon_url(header_icon, repo_name),
                                "size": "68px",
                                "aspectRatio": "1:1",
                                "align": "center"
                            }
                        ],
                        "flex": 2,
                        "justifyContent": "center",
                        "alignItems": "center"
                    }
                ]
            }
        ]
    }
    
    body_contents = []
    
    # --- [B] 今日のゴミ出し（最上部でドカンと超特大アピール！） ---
    if today_trash:
        trash_box = {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#C92A2A",
            "cornerRadius": "16px",
            "paddingBottom": "4px",
            "paddingEnd": "4px",
            "margin": "md",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "background": {
                        "type": "linearGradient",
                        "angle": "135deg",
                        "startColor": "#FF6B6B",
                        "endColor": "#FA5252"
                    },
                    "cornerRadius": "14px",
                    "borderWidth": "2px",
                    "borderColor": "#C92A2A",
                    "paddingAll": "14px",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "alignItems": "center",
                            "contents": [
                                # 丸アイコン
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": "#FFFFFF",
                                    "cornerRadius": "25px",
                                    "width": "50px",
                                    "height": "50px",
                                    "justifyContent": "center",
                                    "alignItems": "center",
                                    "contents": [
                                        {
                                            "type": "image",
                                            "url": get_icon_url(today_trash.get("icon", "flame"), repo_name),
                                            "size": "30px",
                                            "aspectRatio": "1:1"
                                        }
                                    ]
                                },
                                # 特大文字
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "margin": "lg",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "📢 本日のゴミ収集",
                                            "size": "xs",
                                            "weight": "bold",
                                            "color": "#FFE3E3"
                                        },
                                        {
                                            "type": "text",
                                            "text": today_trash.get("label", "ゴミの日"),
                                            "weight": "bold",
                                            "size": "xxl",
                                            "color": "#FFFFFF",
                                            "wrap": True
                                        },
                                        {
                                            "type": "text",
                                            "text": "※朝8時までに集積所へ出しましょう",
                                            "size": "xxs",
                                            "color": "#FFF5F5",
                                            "margin": "xs"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    else:
        trash_box = create_3d_box(
            inner_contents=[
                {
                    "type": "box",
                    "layout": "horizontal",
                    "alignItems": "center",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#F1F3F5",
                            "cornerRadius": "20px",
                            "width": "40px",
                            "height": "40px",
                            "justifyContent": "center",
                            "alignItems": "center",
                            "contents": [
                                {
                                    "type": "image",
                                    "url": get_icon_url("trash", repo_name),
                                    "size": "22px",
                                    "aspectRatio": "1:1"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "md",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "ゴミ出し情報",
                                    "size": "xxs",
                                    "color": "#868E96"
                                },
                                {
                                    "type": "text",
                                    "text": "本日のゴミ出しはありません",
                                    "weight": "bold",
                                    "size": "md",
                                    "color": "#495057"
                                }
                            ]
                        }
                    ]
                }
            ],
            border_color="#CED4DA",
            bg_color="#F8F9FA",
            shadow_color="#ADB5BD",
            padding="10px",
            margin="md"
        )
    body_contents.append(trash_box)
    
    # --- [C] 今週の7日間スケジュール（ウィークリービュー） ---
    days_since_sunday = (w_idx + 1) % 7
    sunday_date = now_jst.date() - timedelta(days=days_since_sunday)
    event_counts = calendar_data.get("event_counts", {})
    
    week_boxes = []
    for i in range(7):
        curr_d = sunday_date + timedelta(days=i)
        w_kanji = WEEKDAY_SUNDAY_FIRST_JA[i]
        is_today = (curr_d == now_jst.date())
        t_info = weekly_schedule.get(w_kanji)
        ev_count = event_counts.get(curr_d, 0)
        
        # 曜日色
        if i == 0:
            day_color = "#E03131"  # 日曜：赤
        elif i == 6:
            day_color = "#1971C2"  # 土曜：青
        else:
            day_color = "#343A40"  # 平日：黒
        
        # 今日のマスは特大ハイライト
        if is_today:
            cell_bg = "#FFE066"
            cell_border = "#F59F00"
            cell_border_w = "2px"
            today_badge_text = "今日"
            today_badge_color = "#D9480F"
        else:
            cell_bg = "#FFFFFF"
            cell_border = "#E9ECEF"
            cell_border_w = "1px"
            today_badge_text = ""
            today_badge_color = "#00000000"
        
        t_short = t_info["short"] if t_info else "ー"
        t_color = "#C92A2A" if t_info else "#ADB5BD"
        
        cell_contents = [
            {"type": "text", "text": w_kanji, "size": "xs", "weight": "bold", "color": day_color, "align": "center"},
            {"type": "text", "text": str(curr_d.day), "size": "md", "weight": "bold" if is_today else "regular", "color": "#1A1A1A", "align": "center", "margin": "xs"},
            {"type": "text", "text": t_short, "size": "xxs", "weight": "bold" if t_info else "regular", "color": t_color, "align": "center", "margin": "xs"}
        ]
        
        if is_today:
            cell_contents.append({
                "type": "text",
                "text": "★今日",
                "size": "xxs",
                "weight": "bold",
                "color": "#D9480F",
                "align": "center",
                "margin": "xs"
            })
        elif ev_count > 0:
            cell_contents.append({
                "type": "text",
                "text": f"●予定{ev_count}",
                "size": "xxs",
                "color": "#1971C2",
                "align": "center",
                "margin": "xs"
            })
        else:
            cell_contents.append({
                "type": "text",
                "text": " ",
                "size": "xxs",
                "align": "center",
                "margin": "xs"
            })
        
        week_boxes.append({
            "type": "box",
            "layout": "vertical",
            "backgroundColor": cell_bg,
            "cornerRadius": "8px",
            "borderWidth": cell_border_w,
            "borderColor": cell_border,
            "paddingTop": "6px",
            "paddingBottom": "6px",
            "paddingStart": "2px",
            "paddingEnd": "2px",
            "alignItems": "center",
            "flex": 1,
            "contents": cell_contents
        })
    
    weekly_card = create_3d_box(
        inner_contents=[
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "image", "url": get_icon_url("calendar", repo_name), "size": "18px", "aspectRatio": "1:1", "flex": 0},
                    {"type": "text", "text": "今週のスケジュール（日〜土）", "size": "sm", "weight": "bold", "color": "#343A40", "margin": "sm"}
                ],
                "alignItems": "center"
            },
            {
                "type": "box",
                "layout": "horizontal",
                "spacing": "xs",
                "margin": "md",
                "contents": week_boxes
            }
        ],
        border_color="#495057",
        shadow_color="#212529",
        padding="12px",
        margin="md"
    )
    body_contents.append(weekly_card)
    
    # --- [D] 今日の天気＆お出かけ情報（傘・洗濯を特大強化！） ---
    def get_period_color(p_type):
        if p_type == "rainy":
            return "#4A90E2"
        elif p_type == "cloudy":
            return "#A6AEBC"
        elif p_type == "snowy":
            return "#5BA4CF"
        return "#FFB566"
    
    weather_periods = weather_data.get("weather_by_period", {})
    pops = weather_data.get("pops", {})
    
    weather_card = create_3d_box(
        inner_contents=[
            # 見出し＆気温
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "image", "url": get_icon_url("sunny", repo_name), "size": "22px", "aspectRatio": "1:1", "flex": 0},
                            {"type": "text", "text": f"天気  {config.get('area_name', '横浜')}", "weight": "bold", "size": "lg", "color": "#1A1A1A", "margin": "xs"}
                        ],
                        "alignItems": "center",
                        "flex": 1
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": f"{weather_data.get('temp_max', '--')}℃", "size": "xxl", "weight": "bold", "color": "#E03131", "flex": 0},
                            {"type": "text", "text": " / ", "size": "md", "color": "#888888", "margin": "xs", "flex": 0},
                            {"type": "text", "text": f"{weather_data.get('temp_min', '--')}℃", "size": "xl", "weight": "bold", "color": "#1971C2", "margin": "xs", "flex": 0}
                        ]
                    }
                ],
                "alignItems": "center"
            },
            # 【特大強化】傘 ＆ 洗濯の2大お出かけカード
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "lg",
                "spacing": "md",
                "contents": [
                    # 傘カード
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": umb_bg,
                        "cornerRadius": "12px",
                        "paddingAll": "12px",
                        "flex": 1,
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {"type": "image", "url": get_icon_url(umb_icon, repo_name), "size": "22px", "aspectRatio": "1:1", "flex": 0},
                                    {"type": "text", "text": "傘の必要性", "size": "xxs", "weight": "bold", "color": umb_color, "margin": "xs"}
                                ],
                                "alignItems": "center"
                            },
                            {
                                "type": "text",
                                "text": umb_title,
                                "size": "md",
                                "weight": "bold",
                                "color": umb_color,
                                "margin": "sm"
                            },
                            {
                                "type": "text",
                                "text": umb_sub,
                                "size": "xxs",
                                "color": umb_color,
                                "margin": "xs"
                            }
                        ]
                    },
                    # 洗濯カード
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": lnd_bg,
                        "cornerRadius": "12px",
                        "paddingAll": "12px",
                        "flex": 1,
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {"type": "image", "url": get_icon_url(lnd_icon, repo_name), "size": "22px", "aspectRatio": "1:1", "flex": 0},
                                    {"type": "text", "text": "お洗濯指数", "size": "xxs", "weight": "bold", "color": lnd_color, "margin": "xs"}
                                ],
                                "alignItems": "center"
                            },
                            {
                                "type": "text",
                                "text": lnd_title,
                                "size": "md",
                                "weight": "bold",
                                "color": lnd_color,
                                "margin": "sm"
                            },
                            {
                                "type": "text",
                                "text": lnd_sub,
                                "size": "xxs",
                                "color": lnd_color,
                                "margin": "xs"
                            }
                        ]
                    }
                ]
            },
            # 6時〜24時タイムラインバー
            {
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "contents": [
                    # バー上の天気アイコン
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "image", "url": get_icon_url(weather_periods.get("6-12", "sunny"), repo_name), "size": "18px", "aspectRatio": "1:1", "align": "center"},
                            {"type": "image", "url": get_icon_url(weather_periods.get("12-18", "sunny"), repo_name), "size": "18px", "aspectRatio": "1:1", "align": "center"},
                            {"type": "image", "url": get_icon_url(weather_periods.get("18-24", "cloudy"), repo_name), "size": "18px", "aspectRatio": "1:1", "align": "center"}
                        ]
                    },
                    # バー本体
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "height": "12px",
                        "cornerRadius": "6px",
                        "margin": "xs",
                        "contents": [
                            {"type": "box", "layout": "vertical", "backgroundColor": get_period_color(weather_periods.get("6-12")), "flex": 1},
                            {"type": "box", "layout": "vertical", "backgroundColor": "#FFFFFF", "width": "2px"},
                            {"type": "box", "layout": "vertical", "backgroundColor": get_period_color(weather_periods.get("12-18")), "flex": 1},
                            {"type": "box", "layout": "vertical", "backgroundColor": "#FFFFFF", "width": "2px"},
                            {"type": "box", "layout": "vertical", "backgroundColor": get_period_color(weather_periods.get("18-24")), "flex": 1}
                        ]
                    },
                    # 目盛りと降水確率
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "margin": "xs",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "alignItems": "center",
                                "contents": [
                                    {"type": "text", "text": "6-12時", "size": "xxs", "color": "#868E96"},
                                    {"type": "text", "text": pops.get("6-12", "-"), "size": "sm", "weight": "bold", "color": "#1971C2" if "50" in pops.get("6-12", "") else "#343A40"}
                                ],
                                "flex": 1
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "alignItems": "center",
                                "contents": [
                                    {"type": "text", "text": "12-18時", "size": "xxs", "color": "#868E96"},
                                    {"type": "text", "text": pops.get("12-18", "-"), "size": "sm", "weight": "bold", "color": "#1971C2" if "50" in pops.get("12-18", "") else "#343A40"}
                                ],
                                "flex": 1
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "alignItems": "center",
                                "contents": [
                                    {"type": "text", "text": "18-24時", "size": "xxs", "color": "#868E96"},
                                    {"type": "text", "text": pops.get("18-24", "-"), "size": "sm", "weight": "bold", "color": "#1971C2" if "50" in pops.get("18-24", "") else "#343A40"}
                                ],
                                "flex": 1
                            }
                        ]
                    }
                ]
            },
            # 服装アドバイス
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "md",
                "backgroundColor": "#F3ECFC",
                "cornerRadius": "8px",
                "paddingAll": "10px",
                "alignItems": "center",
                "contents": [
                    {"type": "text", "text": "👔", "size": "md", "flex": 0},
                    {
                        "type": "text",
                        "text": f"服装目安: {ai_summary.get('clothing_comment', '気温に合わせた服装でお出かけください')}",
                        "size": "xs",
                        "color": "#4B3A66",
                        "weight": "bold",
                        "margin": "sm",
                        "wrap": True
                    }
                ]
            }
        ],
        border_color="#F08A24",
        shadow_color="#B85A0E",
        padding="14px",
        margin="md"
    )
    body_contents.append(weather_card)
    
    # --- [E] 今日の予定（Googleカレンダー） ---
    cal_today = calendar_data.get("today", [])
    cal_tomorrow = calendar_data.get("tomorrow", [])
    cal_week = calendar_data.get("week", [])
    has_calendar = any(len(evs) > 0 for evs in [cal_today, cal_tomorrow, cal_week])
    
    cal_sub_contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "image", "url": get_icon_url("calendar", repo_name), "size": "22px", "aspectRatio": "1:1", "flex": 0},
                {"type": "text", "text": "今日の予定（カレンダー）", "weight": "bold", "size": "lg", "color": "#1864AB", "margin": "xs"}
            ],
            "alignItems": "center"
        }
    ]
    
    if has_calendar:
        # 今日の予定
        if cal_today:
            cal_sub_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "md",
                "contents": [
                    {"type": "text", "text": "今日", "color": "#FFFFFF", "size": "xs", "weight": "bold", "flex": 0}
                ],
                "backgroundColor": "#1971C2",
                "cornerRadius": "4px",
                "paddingStart": "8px",
                "paddingEnd": "8px",
                "paddingTop": "2px",
                "paddingBottom": "2px",
                "width": "46px"
            })
            for ev in cal_today:
                cal_sub_contents.append({
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "sm",
                    "contents": [
                        {"type": "text", "text": "▶", "size": "sm", "color": "#1971C2", "flex": 0},
                        {"type": "text", "text": ev, "size": "md", "weight": "bold", "color": "#1A1A1A", "margin": "sm", "wrap": True}
                    ]
                })
        else:
            cal_sub_contents.append({
                "type": "box",
                "layout": "horizontal",
                "margin": "md",
                "contents": [
                    {"type": "text", "text": "今日の予定はありません（良い一日を！）", "size": "sm", "color": "#868E96"}
                ]
            })
        
        # 明日の予定
        if cal_tomorrow:
            cal_sub_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "lg",
                "contents": [
                    {"type": "text", "text": "明日", "color": "#1864AB", "size": "xxs", "weight": "bold", "flex": 0}
                ],
                "backgroundColor": "#D0EBFF",
                "cornerRadius": "4px",
                "paddingStart": "6px",
                "paddingEnd": "6px",
                "paddingTop": "2px",
                "paddingBottom": "2px",
                "width": "38px"
            })
            for ev in cal_tomorrow:
                cal_sub_contents.append({
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "xs",
                    "contents": [
                        {"type": "text", "text": "•", "size": "xs", "color": "#74C0FC", "flex": 0},
                        {"type": "text", "text": ev, "size": "sm", "color": "#495057", "margin": "xs", "wrap": True}
                    ]
                })
        
        # 1週間の予定
        if cal_week:
            cal_sub_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "md",
                "contents": [
                    {"type": "text", "text": "今週", "color": "#495057", "size": "xxs", "weight": "bold", "flex": 0}
                ],
                "backgroundColor": "#F1F3F5",
                "cornerRadius": "4px",
                "paddingStart": "6px",
                "paddingEnd": "6px",
                "paddingTop": "2px",
                "paddingBottom": "2px",
                "width": "38px"
            })
            for ev in cal_week:
                cal_sub_contents.append({
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "xs",
                    "contents": [
                        {"type": "text", "text": "•", "size": "xs", "color": "#ADB5BD", "flex": 0},
                        {"type": "text", "text": ev, "size": "xs", "color": "#495057", "margin": "xs", "wrap": True}
                    ]
                })
    else:
        cal_sub_contents.append({
            "type": "box",
            "layout": "horizontal",
            "margin": "md",
            "contents": [
                {"type": "text", "text": "予定はありません。今日も充実した一日を！", "size": "sm", "color": "#868E96"}
            ]
        })
    
    calendar_card = create_3d_box(
        inner_contents=cal_sub_contents,
        border_color="#1864AB",
        shadow_color="#0C3E6D",
        padding="14px",
        margin="md"
    )
    body_contents.append(calendar_card)
    
    # --- [F] 釣り予報（城ヶ島） ---
    fishing_spots = weather_data.get("fishing_spots", [])
    if fishing_spots:
        fishing_sub_contents = [
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "image", "url": get_icon_url("fish_on", repo_name), "size": "24px", "aspectRatio": "1:1", "flex": 0},
                    {"type": "text", "text": "釣り予報", "weight": "bold", "size": "lg", "color": "#0C5A75", "margin": "xs"}
                ],
                "alignItems": "center"
            }
        ]
        
        ai_hobbies = {h.get("name"): h for h in ai_summary.get("hobbies", [])}
        
        for spot in fishing_spots:
            spot_name = spot.get("name", "釣り場")
            spot_ai = ai_hobbies.get(spot_name, {})
            score = spot_ai.get("score", 4)
            ai_comment = spot_ai.get("comment", "波風穏やかで釣りやすいコンディション")
            
            # スコア別背景色
            if score >= 3:
                spot_bg = "#E6FCF5"
                spot_border = "#63E6BE"
            else:
                spot_bg = "#F8F9FA"
                spot_border = "#CED4DA"
            
            # 魚アイコン（5段階）
            fish_icons = []
            for i in range(1, 6):
                icon_file = "fish_on" if i <= score else "fish_off"
                fish_icons.append({
                    "type": "image",
                    "url": get_icon_url(icon_file, repo_name),
                    "size": "18px",
                    "aspectRatio": "1:1"
                })
            
            is_high = spot.get("is_high_wave", False)
            wave_bg = "#E03131" if is_high else "#D0EBFF"
            wave_color = "#FFFFFF" if is_high else "#1864AB"
            
            fishing_sub_contents.append({
                "type": "box",
                "layout": "vertical",
                "backgroundColor": spot_bg,
                "cornerRadius": "12px",
                "borderWidth": "1px",
                "borderColor": spot_border,
                "paddingAll": "12px",
                "margin": "md",
                "contents": [
                    # 名前 ＆ 魚アイコン
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": f"📍 {spot_name}", "weight": "bold", "size": "md", "color": "#0C5A75", "flex": 1},
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": fish_icons,
                                "alignItems": "center"
                            }
                        ],
                        "alignItems": "center"
                    },
                    # 風と波のバッジ
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "margin": "sm",
                        "spacing": "sm",
                        "contents": [
                            # 風
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "backgroundColor": "#FFFFFF",
                                "cornerRadius": "12px",
                                "borderWidth": "1px",
                                "borderColor": "#CED4DA",
                                "paddingStart": "8px",
                                "paddingEnd": "8px",
                                "paddingTop": "4px",
                                "paddingBottom": "4px",
                                "contents": [
                                    {"type": "image", "url": get_icon_url(spot.get("wind_icon", "wind"), repo_name), "size": "14px", "aspectRatio": "1:1", "flex": 0},
                                    {"type": "text", "text": spot.get("wind_label", "-"), "size": "xs", "color": "#495057", "margin": "xs"}
                                ],
                                "alignItems": "center"
                            },
                            # 波
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "backgroundColor": wave_bg,
                                "cornerRadius": "12px",
                                "paddingStart": "8px",
                                "paddingEnd": "8px",
                                "paddingTop": "4px",
                                "paddingBottom": "4px",
                                "contents": [
                                    {"type": "image", "url": get_icon_url("wave", repo_name), "size": "14px", "aspectRatio": "1:1", "flex": 0},
                                    {"type": "text", "text": f"波 {spot.get('wave_label', '-')}", "size": "xs", "weight": "bold", "color": wave_color, "margin": "xs"}
                                ],
                                "alignItems": "center"
                            }
                        ]
                    },
                    # AIワンポイント
                    {
                        "type": "text",
                        "text": f"💡 {ai_comment}",
                        "size": "xs",
                        "color": "#0C5A75",
                        "weight": "bold",
                        "margin": "sm",
                        "wrap": True
                    }
                ]
            })
        
        fishing_card = create_3d_box(
            inner_contents=fishing_sub_contents,
            border_color="#0C5A75",
            shadow_color="#063242",
            padding="14px",
            margin="md"
        )
        body_contents.append(fishing_card)
    
    # --- [G] フッター ---
    footer_component = {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "10px",
        "backgroundColor": "#FFFDF9",
        "contents": [
            {
                "type": "text",
                "text": "天気の出典：気象庁",
                "size": "xxs",
                "color": "#ADB5BD",
                "align": "center",
                "action": {
                    "type": "uri",
                    "label": "気象庁予報",
                    "uri": f"https://www.jma.go.jp/bosai/forecast/#area_type=offices&area_code={config.get('area_code', '140000')}"
                }
            }
        ]
    }
    
    # バブルメッセージの結合
    bubble = {
        "type": "bubble",
        "size": "giga",
        "styles": {
            "body": {
                "backgroundColor": "#FFFDF9"
            }
        },
        "header": header_component,
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "14px",
            "contents": body_contents
        },
        "footer": footer_component
    }
    
    return {
        "type": "flex",
        "altText": alt_text,
        "contents": bubble
    }
