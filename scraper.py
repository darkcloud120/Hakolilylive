import argparse
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CALENDAR_FILE = os.path.join(BASE_DIR, "all-events.ics")
EVENTS_FILE = os.path.join(BASE_DIR, "events.json")
MANUAL_EVENTS_FILE = os.path.join(BASE_DIR, "manual_events.json")
CALENDAR_NAME = "ハコリリ活動行事曆"
CALENDAR_DESCRIPTION = "Hakolilylive all-events calendar feed"

def scrape_article_image(article_url):
    """深度掃描內頁，尋找所有可能的圖片來源"""
    if requests is None or BeautifulSoup is None:
        print("缺少 requests 或 beautifulsoup4，略過圖片抓取")
        return None

    try:
        time.sleep(1.5) 
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        response = requests.get(article_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. 針對官網常見的 WordPress 區塊結構進行精確搜尋
        # 依序尋找：文章內的第一個圖片、文章特色圖、或是任何在內容區的圖
        img_target = soup.select_one(".post-content img") or \
                     soup.select_one(".entry-content img") or \
                     soup.select_one(".wp-block-image img") or \
                     soup.select_one("article img")
        
        if img_target:
            # 優先抓取可能存放真實網址的屬性 (處理懶加載)
            src = img_target.get("data-lazy-src") or \
                  img_target.get("data-src") or \
                  img_target.get("src")
            
            if src:
                # 排除小圖或裝飾圖
                if any(x in src.lower() for x in ["icon", "logo", "avatar", "sns", "facebook", "twitter"]):
                    return None
                
                # 轉換為絕對路徑
                full_url = src if src.startswith("http") else "https://hakoniwalily.jp" + src
                print(f"成功抓取圖片網址: {full_url}") # 讓 Actions 的 Log 看得到
                return full_url

    except Exception as e:
        print(f"抓取內頁失敗: {e}")
    return None

def scrape_hakoniwalily():
    if requests is None or BeautifulSoup is None:
        print("缺少 requests 或 beautifulsoup4，略過網站抓取")
        return []

    url = "https://hakoniwalily.jp/news/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 抓取列表中的所有文章
        articles = soup.select("article")
        new_events = []

        for article in articles:
            date_raw = article.select_one(".date")
            title_raw = article.select_one(".title")
            link_raw = article.select_one("a")

            if date_raw and title_raw:
                date_str = date_raw.get_text(strip=True).replace(".", "-")
                title_str = title_raw.get_text(strip=True)
                link_url = link_raw["href"] if link_raw else "https://hakoniwalily.jp/news/"

                # 初始化 image 欄位為 None
                image_url = None
                
                # 只在確實有連結且是新聞內頁時才去抓圖
                if link_url and "hakoniwalily.jp" in link_url and link_url != "https://hakoniwalily.jp/news/":
                    print(f"正在分析內頁圖片: {title_str}")
                    image_url = scrape_article_image(link_url)

                new_events.append({
                    "title": title_str,
                    "start": date_str,
                    "url": link_url,
                    "description": title_str,
                    "image": image_url
                })

        return new_events
    except Exception as e:
        print(f"列表抓取失敗: {e}")
        return []

def load_events(file_name):
    if not os.path.exists(file_name):
        return []

    try:
        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"讀取 {file_name} 失敗: {e}")
        return []

def build_birthday_events():
    current_year = date.today().year
    birthday_templates = [
        ("🐧 Hanon Birthday", "03-06", ["event-birthday", "event-hanon"], "Hanon 生日快樂！🐧"),
        ("🍀 Kotoha Birthday", "06-10", ["event-birthday", "event-kotoha"], "Kotoha 生日快樂！🍀")
    ]

    birthday_events = []
    for year in range(current_year, current_year + 3):
        for title, month_day, class_names, description in birthday_templates:
            birthday_events.append({
                "title": title,
                "start": f"{year}-{month_day}",
                "allDay": True,
                "classNames": class_names,
                "description": description
            })

    return birthday_events

def merge_calendar_events():
    merged = {}
    for event in load_events(EVENTS_FILE) + load_events(MANUAL_EVENTS_FILE) + build_birthday_events():
        key = f"{event.get('title', '')}_{event.get('start', '')}_{event.get('end', '')}"
        merged[key] = {**merged.get(key, {}), **event}

    return sorted(merged.values(), key=lambda x: (x.get("start", ""), x.get("title", "")))

def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def format_ical_date(date_obj):
    return date_obj.strftime("%Y%m%d")

def escape_ical_text(value):
    if value is None:
        return ""

    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace(";", r"\;")
        .replace(",", r"\,")
    )

def fold_ical_line(line, max_bytes=73):
    encoded = line.encode("utf-8")
    if len(encoded) <= max_bytes:
        return line

    chunks = []
    start = 0
    while start < len(line):
        current = []
        current_bytes = 0

        for char in line[start:]:
            char_bytes = len(char.encode("utf-8"))
            if current and current_bytes + char_bytes > max_bytes:
                break
            current.append(char)
            current_bytes += char_bytes

        chunk = "".join(current)
        chunks.append(chunk if not chunks else f" {chunk}")
        start += len(chunk)

    return "\r\n".join(chunks)

def build_event_uid(event):
    unique_bits = "|".join([
        event.get("title", ""),
        event.get("start", ""),
        event.get("end", ""),
        event.get("url", "")
    ])
    digest = sha256(unique_bits.encode("utf-8")).hexdigest()
    return f"{digest}@hakolilylive"

def build_ical_lines(events):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Hakolilylive//Calendar Feed//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_ical_text(CALENDAR_NAME)}",
        f"X-WR-CALDESC:{escape_ical_text(CALENDAR_DESCRIPTION)}"
    ]

    for event in events:
        if not event.get("title") or not event.get("start"):
            continue

        start_date = parse_date(event["start"])
        end_date = parse_date(event["end"]) if event.get("end") else start_date + timedelta(days=1)

        if end_date <= start_date:
            end_date = start_date + timedelta(days=1)

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{build_event_uid(event)}",
            f"DTSTAMP:{timestamp}",
            f"SUMMARY:{escape_ical_text(event.get('title'))}",
            f"DTSTART;VALUE=DATE:{format_ical_date(start_date)}",
            f"DTEND;VALUE=DATE:{format_ical_date(end_date)}",
        ])

        description = event.get("description") or event.get("title")
        if description:
            lines.append(f"DESCRIPTION:{escape_ical_text(description)}")

        if event.get("url"):
            lines.append(f"URL:{event['url'].replace(chr(10), '').replace(chr(13), '')}")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return [fold_ical_line(line) for line in lines]

def write_calendar_ics():
    events = merge_calendar_events()
    ics_body = "\r\n".join(build_ical_lines(events)) + "\r\n"

    with open(CALENDAR_FILE, "w", encoding="utf-8", newline="") as f:
        f.write(ics_body)

    print(f"ICS 行事曆已更新，共 {len(events)} 筆活動")

def parse_args():
    parser = argparse.ArgumentParser(description="Scrape Hakoniwa Lily events")
    parser.add_argument(
        "--generate-ics",
        action="store_true",
        help="Generate all-events.ics after updating JSON data"
    )
    return parser.parse_args()

def save_and_merge_events(new_events):
    file_name = EVENTS_FILE
    
    # 讀取現有資料
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
        except:
            existing_events = []
    else:
        existing_events = []

    # 建立現有資料的檢索字典
    # 用標題 + 日期 當 Key
    db = {f"{ev['title']}_{ev['start']}": ev for ev in existing_events}

    for ne in new_events:
        eid = f"{ne['title']}_{ne['start']}"
        if eid not in db:
            # 全新活動
            existing_events.append(ne)
            db[eid] = ne
        else:
            # 活動已存在，檢查是否需要補上圖片
            if not db[eid].get("image") and ne.get("image"):
                db[eid]["image"] = ne["image"]
                print(f"已為舊活動補上圖片: {ne['title']}")

    # 排序
    existing_events.sort(key=lambda x: x['start'], reverse=True)

    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(existing_events, f, ensure_ascii=False, indent=2)
    
    print(f"資料存檔完成，目前總數: {len(existing_events)}")

if __name__ == "__main__":
    args = parse_args()
    latest = scrape_hakoniwalily()
    if latest:
        save_and_merge_events(latest)
    else:
        print("沒有抓到新活動，沿用現有活動資料")

    if args.generate_ics:
        write_calendar_ics()
