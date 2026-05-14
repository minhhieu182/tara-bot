"""Daily flight price monitor — chạy bởi GitHub Actions lúc 9AM Vietnam."""

import httpx
import os
from datetime import date, timedelta

chat_id = os.environ["TELEGRAM_CHAT_ID"]
token   = os.environ["TELEGRAM_TOKEN"]
serpapi = os.environ["SERPAPI_KEY"]

today      = date.today()
days_ahead = (4 - today.weekday()) % 7
if days_ahead == 0:
    days_ahead = 7
friday = today + timedelta(days=days_ahead)
sunday = friday + timedelta(days=2)

ROUTES = [
    ("SGN", "HAN", "Sài Gòn → Hà Nội"),
    ("SGN", "DAD", "Sài Gòn → Đà Nẵng"),
    ("SGN", "PQC", "Sài Gòn → Phú Quốc"),
    ("HAN", "SGN", "Hà Nội → Sài Gòn"),
]

messages = [f"☀️ Báo giá vé cuối tuần {friday} → {sunday}\n"]

for dep, arr, label in ROUTES:
    params = {
        "engine":        "google_flights",
        "departure_id":  dep,
        "arrival_id":    arr,
        "outbound_date": friday.isoformat(),
        "return_date":   sunday.isoformat(),
        "adults":        1,
        "currency":      "VND",
        "api_key":       serpapi,
    }
    try:
        r      = httpx.get("https://serpapi.com/search.json", params=params, timeout=15)
        data   = r.json()
        best   = data.get("best_flights", [])
        prices = [f.get("price", 0) for f in best if f.get("price")]
        if prices:
            messages.append(f"✈️ {label}: từ {min(prices):,} VND")
        else:
            messages.append(f"✈️ {label}: không tìm thấy")
    except Exception as e:
        messages.append(f"⚠️ {label}: lỗi — {e}")

text = "\n".join(messages)
httpx.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
    timeout=10,
)
print(text)
