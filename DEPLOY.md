# DEPLOY.md — Hướng dẫn setup tara-bot

## 1. Tạo API keys

### 1.1 Telegram Bot Token
- Mở Telegram, tìm `@BotFather`
- Send `/newbot` → đặt tên → nhận token
- Lưu token dạng: `123456:ABC-DEF1234`

### 1.2 Lấy Telegram User ID của bạn
- Mở Telegram, tìm `@userinfobot`
- Send `/start` → copy số ID (VD: `123456789`)

### 1.3 SerpAPI Key
- Vào https://serpapi.com
- Sign up → Dashboard copy key
- Free: 500 searches/tháng — đủ cho 1 bot + daily check

### 1.4 Anthropic API Key
- Vào https://console.anthropic.com/settings/keys
- Create key (free $3 credit)
- Dùng model `claude-sonnet-4-6`

---

## 2. Deploy lên Fly.io

### 2.1 Cài Fly CLI
```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh
```

### 2.2 Login & launch
```bash
cd tara-bot
fly auth login
fly launch --from Dockerfile --name tara-bot-yourname
```

### 2.3 Set secrets
```bash
fly secrets set \
  TELEGRAM_TOKEN=your_bot_token \
  ANTHROPIC_API_KEY=your_anthropic_key \
  SERPAPI_KEY=your_serpapi_key \
  ALLOWED_USER_ID=your_telegram_id
```

### 2.4 Deploy
```bash
fly deploy
```

### 2.5 Check logs
```bash
fly logs
```

Sau deploy, bot sẽ chạy 24/7. Mở Telegram → tìm tên bot → `/start`.

---

## 3. Setup Daily Monitor (GitHub Actions)

Bot chat chạy trên Fly.io. Monitor chạy trên GitHub Actions (free).

### 3.1 Thêm secrets vào GitHub repo
- Settings → Secrets and variables → Actions
- Add:
  - `SERPAPI_KEY`
  - `TELEGRAM_TOKEN`
  - `TELEGRAM_CHAT_ID` (user ID của bạn)
  - `ANTHROPIC_API_KEY`

### 3.2 Enable workflow
- Actions tab → "Flight Monitor" → Enable
- Workflow chạy mỗi ngày 9:00 AM Vietnam time

---

## 4. Test

```bash
# Gửi tin nhắn đến bot:
/start

# Thử:
tìm vé SG Hà Nội thứ 7
iPhone 16 giá bao nhiêu
so sánh giá máy lọc nước
```

## 5. Update

```bash
git pull
fly deploy
```

---

## Budget

| Service | Cost | Ghi chú |
|---------|------|---------|
| Fly.io | $0 | Free tier: 3 VMs 256MB |
| SerpAPI | $0 | Free: 500 req/tháng |
| Claude (Anthropic) | $0 | Free $3 credit, ~$0.50/tháng |
| GitHub Actions | $0 | Public repo free |
| **Total** | **$0/tháng** | |
