# Changelog

Tất cả thay đổi quan trọng của Tara Bot được ghi lại ở đây.

---

## [v2.0.0] — 2026-05-14

### 🚀 Highlights
Upgrade toàn diện engine từ Gemini → Claude Sonnet 4.6, thêm prompt caching và adaptive thinking, fix nhiều bug quan trọng.

### ✨ Tính năng mới
- **Prompt caching** — `cache_control: ephemeral` trên system prompt, tiết kiệm ~90% token cost từ turn thứ 2 trở đi
- **Adaptive thinking** — Claude tự quyết dùng extended thinking khi câu hỏi phức tạp, không cần cấu hình thêm
- **`/uptime` command** — xem số session đang active
- **Daily monitor tách script** — `scripts/monitor.py` độc lập, dễ customize routes và format

### 🐛 Bug fixes
- **Bug nghiêm trọng**: `agents.py` lưu `reply_text` (string) vào history thay vì `response.content` (list of blocks) — gây lỗi API khi bật thinking ở turn tiếp theo
- `monitor.yml` bị lỗi YAML syntax do inline `python -c "..."` với dấu ngoặc kép
- `serpapi.py`: layovers là `list[dict]`, không phải `list[str]`
- `agents.py`: xử lý sai khi Claude trả về nhiều tool_use blocks cùng lúc (Anthropic 400)
- `TODAY` bị đặt trong system prompt → cache bị invalidate mỗi ngày, đã chuyển sang inject vào user message

### ♻️ Refactor
- `max_tokens` tăng từ 4000 → 16000 (cần thiết cho thinking blocks)
- Thêm `stream_chat()` async generator cho fake-streaming Telegram
- System prompt tách thành frozen string, không còn f-string

### 📝 Docs
- README đồng bộ với source thực tế (affiliate, SerpAPI quota, monitor schedule, env vars)

---

## [v1.0.0] — 2026-05-11

### 🚀 Initial release
- Telegram bot chạy 24/7 trên Fly.io (region Singapore)
- **Claude Sonnet 4.6** — NLU + tool-calling (migrate từ Gemini Flash)
- **SerpAPI** — Google Flights search + Google Shopping
- **Daily monitor** — GitHub Actions cron 9AM Vietnam, check 4 tuyến SGN↔HAN/DAD/PQC
- Session memory trong conversation
- `/reset` command xóa lịch sử chat
- Health check endpoint cho Fly.io
- `ALLOWED_USER_ID` để giới hạn truy cập

---

## Hướng dẫn cho người fork

Nếu bạn đang dùng v1.x, để upgrade lên v2.0:

1. Pull code mới: `git pull`
2. Không cần cài thêm dependency (đã có `anthropic>=0.50.0`)
3. Thêm secret `TELEGRAM_CHAT_ID` vào GitHub repo (cho daily monitor)
4. Redeploy: `fly deploy`

Xem chi tiết: [DEPLOY.md](./DEPLOY.md)
