import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta, date

JST = timezone(timedelta(hours=9))

def parse_ics_datetime(dt_str, tz_offset_hours=9):
    """
    ICSのDTSTART文字列 (例: '20260925T100000Z', '20260925T100000', '20260925') を
    JSTのdatetimeオブジェクトまたはdateオブジェクトに変換する。
    """
    dt_str = dt_str.strip()
    # タイムゾーンパラメータ等が付いている場合 (例: 'TZID=Asia/Tokyo:20260925T100000')
    if ':' in dt_str:
        dt_str = dt_str.split(':')[-1]
    
    # 終日予定: YYYYMMDD
    if len(dt_str) == 8 and dt_str.isdigit():
        return datetime.strptime(dt_str, "%Y%m%d").date(), True
    
    # 日時予定: YYYYMMDDTHHMMSS or YYYYMMDDTHHMMSSZ
    is_utc = dt_str.endswith('Z')
    clean_str = dt_str.rstrip('Z')
    try:
        dt = datetime.strptime(clean_str, "%Y%m%dT%H%M%S")
        if is_utc:
            dt = dt.replace(tzinfo=timezone.utc).astimezone(JST)
        else:
            # タイムゾーンなしは通常JSTとみなす
            dt = dt.replace(tzinfo=JST)
        return dt, False
    except ValueError:
        return None, False

def fetch_calendar_events(ics_url):
    """
    GoogleカレンダーのiCal非公開URLからイベントを取得し、
    今日・明日・この先1週間の予定に整理して返す。
    """
    if not ics_url or not ics_url.strip():
        return {"today": [], "tomorrow": [], "week": []}
    
    try:
        req = urllib.request.Request(ics_url, headers={'User-Agent': 'MorningSecretaryBot/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            ics_text = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Warning: Failed to fetch calendar: {e}")
        return {"today": [], "tomorrow": [], "week": []}
    
    # icalendar や dateutil があれば優先利用
    try:
        import icalendar
        from dateutil import rrule
        import dateutil.tz
        return parse_events_with_icalendar(ics_text)
    except ImportError:
        return parse_events_builtin(ics_text)

def parse_events_with_icalendar(ics_text):
    import icalendar
    
    now_jst = datetime.now(JST)
    today = now_jst.date()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)
    
    cal = icalendar.Calendar.from_ical(ics_text)
    
    raw_events = []
    
    for component in cal.walk():
        if component.name == "VEVENT":
            summary = str(component.get('summary', '予定'))
            dtstart = component.get('dtstart')
            if not dtstart:
                continue
            
            val = dtstart.dt
            is_all_day = not isinstance(val, datetime)
            
            # RRULE等の展開が必要な場合
            # シンプルな単発チェックと簡易RRULEチェック
            rrule_prop = component.get('rrule')
            if rrule_prop:
                # 簡易的な週間・デイリーの繰り返しチェック
                freq = rrule_prop.get('FREQ', [''])[0]
                # 今日の週のイベントとして該当日を計算
                # 複雑なルールに対応するため、日付ベースで走査
                for offset in range(8):
                    target_d = today + timedelta(days=offset)
                    # 曜日一致チェック
                    if freq == 'WEEKLY':
                        by_day = rrule_prop.get('BYDAY', [])
                        # BYDAYのパース (MO, TU, WE, TH, FR, SA, SU)
                        day_abbrs = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
                        target_abbr = day_abbrs[target_d.weekday()]
                        if target_abbr in by_day or (not by_day and val.weekday() == target_d.weekday()):
                            if isinstance(val, datetime):
                                target_dt = datetime.combine(target_d, val.time()).replace(tzinfo=JST)
                            else:
                                target_dt = target_d
                            raw_events.append((target_dt, is_all_day, summary))
                    elif freq == 'DAILY':
                        if isinstance(val, datetime):
                            target_dt = datetime.combine(target_d, val.time()).replace(tzinfo=JST)
                        else:
                            target_dt = target_d
                        raw_events.append((target_dt, is_all_day, summary))
            else:
                if isinstance(val, datetime):
                    if val.tzinfo is None:
                        val = val.replace(tzinfo=JST)
                    else:
                        val = val.astimezone(JST)
                raw_events.append((val, is_all_day, summary))
    
    return categorize_events(raw_events, today, tomorrow, week_end)

def parse_events_builtin(ics_text):
    now_jst = datetime.now(JST)
    today = now_jst.date()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)
    
    # 改行コード正規化と行結合の解除 (folded lines)
    unfolded = re.sub(r'\r\n[ \t]', '', ics_text)
    unfolded = re.sub(r'\n[ \t]', '', unfolded)
    
    events_raw = unfolded.split("BEGIN:VEVENT")
    parsed_events = []
    
    for ev in events_raw[1:]:
        summary_m = re.search(r'^SUMMARY:(.+)$', ev, re.MULTILINE)
        summary = summary_m.group(1).strip() if summary_m else "予定"
        
        dtstart_m = re.search(r'^DTSTART.*?:(.+)$', ev, re.MULTILINE)
        if not dtstart_m:
            continue
        
        dtstart_str = dtstart_m.group(1).strip()
        dt, is_all_day = parse_ics_datetime(dtstart_str)
        if not dt:
            continue
        
        # RRULEチェック
        rrule_m = re.search(r'^RRULE:(.+)$', ev, re.MULTILINE)
        if rrule_m:
            rule_str = rrule_m.group(1)
            # 簡易展開
            for offset in range(8):
                target_d = today + timedelta(days=offset)
                if "FREQ=WEEKLY" in rule_str:
                    target_weekday = target_d.weekday()
                    day_abbrs = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
                    abbr = day_abbrs[target_weekday]
                    byday_m = re.search(r'BYDAY=([A-Z,]+)', rule_str)
                    matched = False
                    if byday_m and abbr in byday_m.group(1).split(','):
                        matched = True
                    elif not byday_m and (dt.date() if isinstance(dt, datetime) else dt).weekday() == target_weekday:
                        matched = True
                    
                    if matched:
                        if isinstance(dt, datetime):
                            event_dt = datetime.combine(target_d, dt.time()).replace(tzinfo=JST)
                        else:
                            event_dt = target_d
                        parsed_events.append((event_dt, is_all_day, summary))
                elif "FREQ=DAILY" in rule_str:
                    if isinstance(dt, datetime):
                        event_dt = datetime.combine(target_d, dt.time()).replace(tzinfo=JST)
                    else:
                        event_dt = target_d
                    parsed_events.append((event_dt, is_all_day, summary))
        else:
            parsed_events.append((dt, is_all_day, summary))
    
    return categorize_events(parsed_events, today, tomorrow, week_end)

def categorize_events(events, today, tomorrow, week_end):
    today_list = []
    tomorrow_list = []
    week_list = []
    
    weekday_kanji = ["月", "火", "水", "木", "金", "土", "日"]
    
    # 重複除去とソート
    unique_events = set()
    cleaned = []
    for dt, is_all_day, summary in events:
        d_val = dt.date() if isinstance(dt, datetime) else dt
        key = (d_val, str(dt), summary)
        if key not in unique_events:
            unique_events.add(key)
            cleaned.append((dt, is_all_day, summary))
    
    # 日時順ソート
    def sort_key(item):
        dt, is_all_day, _ = item
        if isinstance(dt, datetime):
            return (dt.date(), 1, dt.time())
        return (dt, 0, datetime.min.time())
    
    cleaned.sort(key=sort_key)
    
    for dt, is_all_day, summary in cleaned:
        d_val = dt.date() if isinstance(dt, datetime) else dt
        
        if d_val == today:
            time_str = "終日" if is_all_day else dt.strftime("%H:%M")
            today_list.append(f"{time_str} {summary}")
        elif d_val == tomorrow:
            time_str = "終日" if is_all_day else dt.strftime("%H:%M")
            tomorrow_list.append(f"{time_str} {summary}")
        elif tomorrow < d_val <= week_end:
            w_kanji = weekday_kanji[d_val.weekday()]
            week_list.append(f"{d_val.month}/{d_val.day}（{w_kanji}） {summary}")
    
    event_counts = {}
    for dt, is_all_day, summary in cleaned:
        d_val = dt.date() if isinstance(dt, datetime) else dt
        event_counts[d_val] = event_counts.get(d_val, 0) + 1
    
    # 制限件数と「ほかN件」の処理
    def format_capped(items, limit):
        if len(items) <= limit:
            return items
        capped = items[:limit]
        extra = len(items) - limit
        capped.append(f"ほか{extra}件")
        return capped
    
    return {
        "today": format_capped(today_list, 5),
        "tomorrow": format_capped(tomorrow_list, 3),
        "week": format_capped(week_list, 5),
        "event_counts": event_counts
    }
