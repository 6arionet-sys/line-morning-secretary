import os
import json
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

WEEKDAY_EN = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]

def get_icon_url(icon_name, repo_name=None):
    """
    GitHubリポジトリ上のアイコン画像URLを生成する。
    """
    if not repo_name:
        repo_name = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo_name:
        repo_name = "example/line-morning-secretary"
    
    # 拡張子補正
    if not icon_name.endswith(".png"):
        icon_name = f"{icon_name}.png"
    
    return f"https://raw.githubusercontent.com/{repo_name}/main/icons/{icon_name}"

def build_flex_message(weather_data, calendar_data, ai_summary, config, repo_name=None):
    """
    天気、カレンダー、AI要約、設定からLINE Flex Messageのペイロードを生成する。
    """
    now_jst = datetime.now(JST)
    month = now_jst.month
    day = now_jst.day
    w_idx = now_jst.weekday()
    w_en = WEEKDAY_EN[w_idx]
    w_ja = WEEKDAY_JA[w_idx]
    
    # 1. 今日のゴミの日判定
    weekly_schedule = config.get("weekly_schedule", {})
    today_trash = weekly_schedule.get(w_ja)
    
    # 2. ヘッダーのグラデーション判定
    main_type = weather_data.get("main_weather_type", "sunny")
    if main_type == "rainy":
        header_bg_start = "#4A90E2"
        header_bg_end = "#2F54EB"
        header_icon = "rainy"
    elif main_type == "cloudy":
        header_bg_start = "#8C9BAE"
        header_bg_end = "#5C6B7E"
        header_icon = "cloudy"
    elif main_type == "snowy":
        header_bg_start = "#70C1B3"
        header_bg_end = "#4B8B9B"
        header_icon = "snowy"
    else: # sunny
        header_bg_start = "#FF9A5A"
        header_bg_end = "#FF6F7D"
        header_icon = "sunny"
    
    # 3. altTextの生成
    trash_text = f"今日は{today_trash['label']}" if today_trash else "今日のゴミ出しなし"
    alt_text = f"{month}/{day}（{w_ja}）{weather_data.get('short_weather', '晴れ')} {weather_data.get('temp_max', '--')}℃ {trash_text}"
    
    # --- コンポーネント構築 ---
    
    # [A] ヘッダー
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
                                "backgroundColor": "#3A2A1E",
                                "cornerRadius": "8px",
                                "paddingStart": "8px",
                                "paddingEnd": "8px",
                                "paddingTop": "2px",
                                "paddingBottom": "2px",
                                "width": "100px",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": f"{month}.{day} {w_en}",
                                        "color": "#FFE9A8",
                                        "size": "xs",
                                        "weight": "bold",
                                        "align": "center"
                                    }
                                ]
                            },
                            {
                                "type": "text",
                                "text": "おはようございます",
                                "color": "#FFFFFF",
                                "size": "xl",
                                "weight": "bold",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": f"今日は{weather_data.get('raw_weather', '良い一日を！')}",
                                "color": "#FFFFFFE6",
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
                                "size": "60px",
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
    
    # [B] 天気パーティション
    # 傘の色
    umbrella_info = weather_data.get("umbrella", {})
    if umbrella_info.get("icon") == "umbrella":
        umb_bg = "#2E6FB5"
        umb_color = "#FFFFFF"
    elif umbrella_info.get("icon") == "umbrella_small":
        umb_bg = "#E8ECEF"
        umb_color = "#495057"
    else:
        umb_bg = "#FFF0E0"
        umb_color = "#D97706"
    
    # タイムラインバー（6-12, 12-18, 18-24）
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
    
    weather_partition = {
        "type": "box",
        "layout": "vertical",
        "backgroundColor": "#FFFFFF",
        "cornerRadius": "14px",
        "borderWidth": "2px",
        "borderColor": "#B85A0E",
        "paddingAll": "14px",
        "margin": "md",
        "contents": [
            # 見出し行
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "image",
                        "url": get_icon_url("sunny", repo_name),
                        "size": "20px",
                        "aspectRatio": "1:1",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": f"天気  {config.get('area_name', '東京')}",
                        "weight": "bold",
                        "size": "md",
                        "color": "#3A2A1E",
                        "margin": "sm"
                    }
                ],
                "alignItems": "center"
            },
            # 気温と傘
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "md",
                "alignItems": "center",
                "contents": [
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [
                            {"type": "text", "text": f"{weather_data.get('temp_max', '--')}℃", "size": "xxl", "weight": "bold", "color": "#E0561B", "flex": 0},
                            {"type": "text", "text": " / ", "size": "sm", "color": "#888888", "margin": "xs", "flex": 0},
                            {"type": "text", "text": f"{weather_data.get('temp_min', '--')}℃", "size": "lg", "weight": "bold", "color": "#2E6FB5", "margin": "xs", "flex": 0}
                        ],
                        "flex": 3
                    },
                    # 傘ピルラベル
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "backgroundColor": umb_bg,
                        "cornerRadius": "20px",
                        "paddingStart": "10px",
                        "paddingEnd": "10px",
                        "paddingTop": "4px",
                        "paddingBottom": "4px",
                        "contents": [
                            {
                                "type": "image",
                                "url": get_icon_url(umbrella_info.get("icon", "umbrella"), repo_name),
                                "size": "14px",
                                "aspectRatio": "1:1",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": umbrella_info.get("status", "傘はいらない"),
                                "size": "xs",
                                "weight": "bold",
                                "color": umb_color,
                                "margin": "xs"
                            }
                        ],
                        "alignItems": "center"
                    }
                ]
            },
            # 6時〜24時の横長バー
            {
                "type": "box",
                "layout": "vertical",
                "margin": "md",
                "contents": [
                    # バー本体
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "height": "8px",
                        "cornerRadius": "4px",
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
                                    {"type": "text", "text": "6-12時", "size": "xxs", "color": "#888888"},
                                    {"type": "text", "text": pops.get("6-12", "-"), "size": "xs", "weight": "bold", "color": "#2E6FB5" if "50" in pops.get("6-12", "") else "#555555"}
                                ],
                                "flex": 1
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "alignItems": "center",
                                "contents": [
                                    {"type": "text", "text": "12-18時", "size": "xxs", "color": "#888888"},
                                    {"type": "text", "text": pops.get("12-18", "-"), "size": "xs", "weight": "bold", "color": "#2E6FB5" if "50" in pops.get("12-18", "") else "#555555"}
                                ],
                                "flex": 1
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "alignItems": "center",
                                "contents": [
                                    {"type": "text", "text": "18-24時", "size": "xxs", "color": "#888888"},
                                    {"type": "text", "text": pops.get("18-24", "-"), "size": "xs", "weight": "bold", "color": "#2E6FB5" if "50" in pops.get("18-24", "") else "#555555"}
                                ],
                                "flex": 1
                            }
                        ]
                    }
                ]
            },
            # 洗濯情報
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "md",
                "backgroundColor": "#E6F6EE",
                "cornerRadius": "8px",
                "paddingAll": "6px",
                "alignItems": "center",
                "contents": [
                    {
                        "type": "image",
                        "url": get_icon_url(weather_data.get("laundry", {}).get("icon", "hanger"), repo_name),
                        "size": "16px",
                        "aspectRatio": "1:1",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": f"洗濯: {weather_data.get('laundry', {}).get('status', 'OK')}（{weather_data.get('laundry', {}).get('comment', '')}）",
                        "size": "xs",
                        "color": "#1E5E3E",
                        "weight": "bold",
                        "margin": "sm"
                    }
                ]
            },
            # 服装の一言
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "sm",
                "backgroundColor": "#F3ECFC",
                "cornerRadius": "8px",
                "paddingAll": "6px",
                "alignItems": "center",
                "contents": [
                    {
                        "type": "text",
                        "text": "👔",
                        "size": "sm",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": ai_summary.get("clothing_comment", "気温に合わせて調節しやすい服装を"),
                        "size": "xs",
                        "color": "#4B3A66",
                        "weight": "bold",
                        "margin": "sm",
                        "wrap": True
                    }
                ]
            }
        ]
    }
    body_contents.append(weather_partition)
    
    # [C] ゴミの日パーティション
    trash_bg_start = "#FFE3CF" if today_trash else "#F3F4F6"
    trash_bg_end = "#FFC9A8" if today_trash else "#E5E7EB"
    trash_border = "#8A2E0A" if today_trash else "#9CA3AF"
    trash_icon = today_trash.get("icon", "trash") if today_trash else "trash"
    trash_label = today_trash.get("label", "ゴミの日") if today_trash else "今日のゴミ出しはありません"
    
    trash_partition = {
        "type": "box",
        "layout": "vertical",
        "background": {
            "type": "linearGradient",
            "angle": "135deg",
            "startColor": trash_bg_start,
            "endColor": trash_bg_end
        },
        "cornerRadius": "14px",
        "borderWidth": "2px",
        "borderColor": trash_border,
        "paddingAll": "12px",
        "margin": "md",
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "alignItems": "center",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": "#FFFFFF",
                        "cornerRadius": "20px",
                        "width": "36px",
                        "height": "36px",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "contents": [
                            {
                                "type": "image",
                                "url": get_icon_url(trash_icon, repo_name),
                                "size": "20px",
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
                                "text": "ゴミの日" if today_trash else "ゴミ出し",
                                "size": "xxs",
                                "color": "#666666"
                            },
                            {
                                "type": "text",
                                "text": trash_label,
                                "weight": "bold",
                                "size": "md",
                                "color": "#3A2A1E"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    body_contents.append(trash_partition)
    
    # [D] 予定パーティション (Googleカレンダー)
    has_calendar = any(len(calendar_data.get(k, [])) > 0 for k in ["today", "tomorrow", "week"])
    
    if has_calendar:
        cal_sub_contents = [
            # 見出し
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "image",
                        "url": get_icon_url("calendar", repo_name),
                        "size": "20px",
                        "aspectRatio": "1:1",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": "予定",
                        "weight": "bold",
                        "size": "md",
                        "color": "#123F73",
                        "margin": "sm"
                    }
                ],
                "alignItems": "center"
            }
        ]
        
        # 今日の予定
        if calendar_data.get("today"):
            cal_sub_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": "今日",
                        "color": "#FFFFFF",
                        "size": "xxs",
                        "weight": "bold",
                        "flex": 0
                    }
                ],
                "backgroundColor": "#2F78C8",
                "cornerRadius": "4px",
                "paddingStart": "6px",
                "paddingEnd": "6px",
                "paddingTop": "2px",
                "paddingBottom": "2px",
                "width": "38px"
            })
            for ev in calendar_data["today"]:
                cal_sub_contents.append({
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "xs",
                    "contents": [
                        {"type": "text", "text": "•", "size": "xs", "color": "#2F78C8", "flex": 0},
                        {"type": "text", "text": ev, "size": "sm", "weight": "bold", "color": "#333333", "margin": "xs", "wrap": True}
                    ]
                })
        
        # 明日の予定
        if calendar_data.get("tomorrow"):
            cal_sub_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": "明日",
                        "color": "#123F73",
                        "size": "xxs",
                        "weight": "bold",
                        "flex": 0
                    }
                ],
                "backgroundColor": "#D6E4FF",
                "cornerRadius": "4px",
                "paddingStart": "6px",
                "paddingEnd": "6px",
                "paddingTop": "2px",
                "paddingBottom": "2px",
                "width": "38px"
            })
            for ev in calendar_data["tomorrow"]:
                cal_sub_contents.append({
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "xs",
                    "contents": [
                        {"type": "text", "text": "•", "size": "xs", "color": "#6FA9EA", "flex": 0},
                        {"type": "text", "text": ev, "size": "xs", "color": "#555555", "margin": "xs", "wrap": True}
                    ]
                })
        
        # 1週間の予定
        if calendar_data.get("week"):
            cal_sub_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": "今週",
                        "color": "#555555",
                        "size": "xxs",
                        "weight": "bold",
                        "flex": 0
                    }
                ],
                "backgroundColor": "#EEEEEE",
                "cornerRadius": "4px",
                "paddingStart": "6px",
                "paddingEnd": "6px",
                "paddingTop": "2px",
                "paddingBottom": "2px",
                "width": "38px"
            })
            for ev in calendar_data["week"]:
                cal_sub_contents.append({
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "xs",
                    "contents": [
                        {"type": "text", "text": "•", "size": "xs", "color": "#999999", "flex": 0},
                        {"type": "text", "text": ev, "size": "xxs", "color": "#777777", "margin": "xs", "wrap": True}
                    ]
                })
        
        calendar_partition = {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "cornerRadius": "14px",
            "borderWidth": "2px",
            "borderColor": "#123F73",
            "paddingAll": "14px",
            "margin": "md",
            "contents": cal_sub_contents
        }
        body_contents.append(calendar_partition)
    
    # [E] 釣りパーティション
    fishing_spots = weather_data.get("fishing_spots", [])
    if fishing_spots:
        fishing_sub_contents = [
            # 見出し
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "image",
                        "url": get_icon_url("fish_on", repo_name),
                        "size": "20px",
                        "aspectRatio": "1:1",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": "釣り予報",
                        "weight": "bold",
                        "size": "md",
                        "color": "#0C5A75",
                        "margin": "sm"
                    }
                ],
                "alignItems": "center"
            }
        ]
        
        # AIスコアの紐付け
        ai_hobbies = {h.get("name"): h for h in ai_summary.get("hobbies", [])}
        
        for spot in fishing_spots:
            spot_name = spot.get("name", "釣り場")
            spot_ai = ai_hobbies.get(spot_name, {})
            score = spot_ai.get("score", 3)
            ai_comment = spot_ai.get("comment", "気象状況を確認して安全に釣行してください")
            
            # スコアに応じた枠のグラデーション
            if score >= 3:
                spot_bg_start = "#EEFAFE"
                spot_bg_end = "#C8ECF8"
                spot_border = "#8FD3EA"
            else:
                spot_bg_start = "#FAFAFA"
                spot_bg_end = "#E6E6E6"
                spot_border = "#D2D2D2"
            
            # 魚アイコン（5段階）
            fish_icons = []
            for i in range(1, 6):
                icon_file = "fish_on" if i <= score else "fish_off"
                fish_icons.append({
                    "type": "image",
                    "url": get_icon_url(icon_file, repo_name),
                    "size": "14px",
                    "aspectRatio": "1:1"
                })
            
            # 波のラベル色
            is_high = spot.get("is_high_wave", False)
            wave_bg = "#C0392B" if is_high else "#E1F0FA"
            wave_text_color = "#FFFFFF" if is_high else "#0C5A75"
            
            fishing_sub_contents.append({
                "type": "box",
                "layout": "vertical",
                "background": {
                    "type": "linearGradient",
                    "angle": "135deg",
                    "startColor": spot_bg_start,
                    "endColor": spot_bg_end
                },
                "cornerRadius": "10px",
                "borderWidth": "1px",
                "borderColor": spot_border,
                "paddingAll": "10px",
                "margin": "md",
                "contents": [
                    # 釣り場名 ＆ スコア魚
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"📍 {spot_name}",
                                "weight": "bold",
                                "size": "sm",
                                "color": "#0C5A75",
                                "flex": 1
                            },
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
                        "contents": [
                            # 風
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "backgroundColor": "#E8ECEF",
                                "cornerRadius": "12px",
                                "paddingStart": "8px",
                                "paddingEnd": "8px",
                                "paddingTop": "2px",
                                "paddingBottom": "2px",
                                "contents": [
                                    {
                                        "type": "image",
                                        "url": get_icon_url(spot.get("wind_icon", "wind"), repo_name),
                                        "size": "12px",
                                        "aspectRatio": "1:1",
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": spot.get("wind_label", "-"),
                                        "size": "xxs",
                                        "color": "#495057",
                                        "margin": "xs"
                                    }
                                ],
                                "alignItems": "center"
                            },
                            # 波
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "margin": "xs",
                                "backgroundColor": wave_bg,
                                "cornerRadius": "12px",
                                "paddingStart": "8px",
                                "paddingEnd": "8px",
                                "paddingTop": "2px",
                                "paddingBottom": "2px",
                                "contents": [
                                    {
                                        "type": "image",
                                        "url": get_icon_url("wave", repo_name),
                                        "size": "12px",
                                        "aspectRatio": "1:1",
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": f"波 {spot.get('wave_label', '-')}",
                                        "size": "xxs",
                                        "weight": "bold" if is_high else "regular",
                                        "color": wave_text_color,
                                        "margin": "xs"
                                    }
                                ],
                                "alignItems": "center"
                            }
                        ]
                    },
                    # AI一言
                    {
                        "type": "text",
                        "text": f"💡 {ai_comment}",
                        "size": "xs",
                        "color": "#0C5A75",
                        "margin": "sm",
                        "wrap": True
                    }
                ]
            })
        
        fishing_partition = {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#FFFFFF",
            "cornerRadius": "14px",
            "borderWidth": "2px",
            "borderColor": "#0C5A75",
            "paddingAll": "14px",
            "margin": "md",
            "contents": fishing_sub_contents
        }
        body_contents.append(fishing_partition)
    
    # [F] フッター（出典・リンク）
    footer_component = {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "10px",
        "backgroundColor": "#FFF8EE",
        "contents": [
            {
                "type": "text",
                "text": "天気の出典：気象庁",
                "size": "xxs",
                "color": "#999999",
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
                "backgroundColor": "#FFF8EE"
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
