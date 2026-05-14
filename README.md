# TARA BOT 🤖✈️🛒

[![Version](https://img.shields.io/badge/version-v2.0.0-brightgreen?style=flat-square)](https://github.com/thaolst/tara-bot/releases)
[![GitHub stars](https://img.shields.io/github/stars/thaolst/tara-bot?style=flat-square&color=yellow)](https://github.com/thaolst/tara-bot/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/thaolst/tara-bot?style=flat-square&color=blue)](https://github.com/thaolst/tara-bot/network/members)

**AI agent cá nhân trên Telegram — săn vé máy bay, so sánh giá, cào deal.**

[![Deploy on Fly.io](https://img.shields.io/badge/deploy-fly.io-6a0dad?style=flat-square)](https://fly.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-4ade80?style=flat-square)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-60a5fa?style=flat-square)](https://python.org)

> Build bởi **Lê Song Tiên Thảo** · [GitHub](https://github.com/thaolst) · [LinkedIn](https://www.linkedin.com/in/thaolst/) · [Facebook](https://www.facebook.com/LeSongTienThao)

---

## ✨ Tính năng

| Tính năng | Mô tả | Trạng thái |
|---|---|---|
| 💬 **Chat tự nhiên** | Hỏi "tìm vé SG Đà Nẵng cuối tuần" — Claude hiểu, SerpAPI search | ✅ |
| ✈️ **Tra cứu chuyến bay** | Giá, hãng, giờ bay real-time từ Google Flights + link Google Flights | ✅ |
| 🛒 **So sánh giá đồ** | Search sản phẩm, so sánh giá, rating, link mua | ✅ |
| 🔔 **Daily monitor** | 9AM mỗi sáng check giá 4 tuyến quen (SGN↔HAN, SGN↔DAD, SGN↔PQC), gửi Telegram alert | ✅ |
| 🧠 **Context-aware** | Claude nhớ lịch sử chat trong session | ✅ |
| ⚡ **Prompt caching** | Cache system prompt → tiết kiệm ~90% token cost từ turn 2 | ✅ |
| 🧩 **Adaptive thinking** | Claude tự quyết dùng extended thinking khi câu hỏi phức tạp | ✅ |
| 🔗 **Affiliate link** | Link Google Flights tự động trong mỗi kết quả tìm vé | ✅ |
| 🆕 **Shopee cào giá** | *(coming soon)* | 🔜 |
| 🔔 **Auto-deal alert** | Notify khi deal tốt xuất hiện | 🔜 |
| 👥 **Multi-user** | Hỗ trợ nhiều user | 🔜 |

---

## 🎬 Demo

```
👤: tìm vé SG ra Hà Nội thứ 7 tuần này
🤖: ✈️ Sài Gòn → Hà Nội
    📅 2026-05-16 → 2026-05-21 (3 chuyến)

    🏆 1,450,000đ 06:00→08:05 (2h5)
       `Vietjet Air VJ123` · *Thẳng*

    🥈 2,100,000đ 08:30→10:30 (2h0)
       `Vietnam Airlines VN123` · *Thẳng*

    [🔍 Xem thêm trên Google Flights](https://...)
```

---

## 🧱 Tech stack

```
┌──────────┐     ┌─────────────────────┐     ┌──────────────┐
│ Telegram │ ←→ │  Claude Sonnet 4.6  │ ←→ │   SerpAPI    │
│   Bot    │     │  Tool-use loop      │     │  (Flights +  │
│          │     │  Prompt caching     │     │   Shopping)  │
│          │     │  Adaptive thinking  │     └──────────────┘
└──────────┘     └─────────────────────┘
                          ↕
                  ┌──────────────┐
                  │ GitHub       │
                  │ Actions      │
                  │ (9AM daily)  │
                  └──────────────┘
```

- **Telegram Bot** — python-telegram-bot v20+
- **Claude Sonnet 4.6** — NLU + multi-turn tool-calling + prompt caching + adaptive thinking
- **SerpAPI** — Google Flights + Google Shopping (250 free/tháng)
- **Fly.io** — host 24/7 (free tier, region: Singapore)
- **GitHub Actions** — daily cron 9AM Vietnam time

---

## 🚀 Deploy 5 phút

1. **Fork repo** → `git clone https://github.com/thaolst/tara-bot`
2. **Get API keys**:
   - [@BotFather](https://t.me/botfather) → tạo bot → copy token
   - [SerpAPI](https://serpapi.com) → sign up → copy key (250 free/tháng)
   - [Anthropic API](https://console.anthropic.com/settings/keys) → copy key
   - Telegram: lấy `TELEGRAM_CHAT_ID` của bạn qua [@userinfobot](https://t.me/userinfobot)
3. **Deploy lên Fly.io**:

```bash
fly launch --from Dockerfile
fly secrets set \
  TELEGRAM_TOKEN=xxx \
  ANTHROPIC_API_KEY=xxx \
  SERPAPI_KEY=xxx \
  ALLOWED_USER_ID=xxx \
  TELEGRAM_CHAT_ID=xxx
fly deploy
```

4. **Bật daily monitor**:
   - GitHub repo → Settings → Secrets → thêm `SERPAPI_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`
   - Actions tab → **Flight Monitor** → enable workflow

*Chi tiết: [DEPLOY.md](./DEPLOY.md)*

---

## ⚙️ Cấu hình

| Env var | Bắt buộc | Mô tả |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key |
| `TELEGRAM_TOKEN` | ✅ | Telegram Bot token từ @BotFather |
| `ALLOWED_USER_ID` | ✅ | Telegram user ID — bot chỉ phục vụ ID này |
| `SERPAPI_KEY` | ✅ | SerpAPI key cho Flights + Shopping |
| `TELEGRAM_CHAT_ID` | ✅ | Chat ID nhận daily monitor alert |
| `AFFILIATE_TEMPLATE` | ❌ | Template URL affiliate (chưa implement) |

---

## 📁 Cấu trúc

```
src/
├── bot.py              # Telegram bot — polling, session management, /reset, /uptime
├── agents.py           # Claude agent — tool-use loop, prompt caching, adaptive thinking
├── config.py           # Env config loader
└── tools/
    └── serpapi.py      # Flight search + Shopping search (SerpAPI)
.github/workflows/
└── monitor.yml         # Daily 9AM: check giá 4 tuyến SGN↔HAN/DAD/PQC → Telegram alert
```

---

## 🗺️ Roadmap

- [x] Flight search (SerpAPI + Google Flights link)
- [x] Shopping price compare (SerpAPI)
- [x] Daily price monitor 9AM (GitHub Actions)
- [x] 24/7 Telegram bot (Fly.io, region Singapore)
- [x] Prompt caching (tiết kiệm token cost)
- [x] Adaptive thinking (extended thinking tự động)
- [x] /reset và /uptime commands
- [ ] Shopee price scraper
- [ ] Affiliate link injection đầy đủ
- [ ] Auto-deal alert (notify khi deal tốt)
- [ ] Multi-user support

---

## 📝 License

MIT — free to use, fork, modify.

---

*Tara Bot — AI agent cá nhân, build public để chia sẻ, không phải product thương mại.*
