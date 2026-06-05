# 🗜️ UnZip Bot — Complete Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Get API Credentials](#get-api-credentials)
3. [Configure the Bot](#configure-the-bot)
4. [MongoDB Setup](#mongodb-setup)
5. [Deploy on VPS](#deploy-on-vps)
6. [Deploy with Docker](#deploy-with-docker)
7. [Deploy on Railway](#deploy-on-railway)
8. [Deploy on Heroku](#deploy-on-heroku)
9. [Bot Commands Reference](#bot-commands-reference)
10. [Admin Commands](#admin-commands)
11. [Premium System](#premium-system)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Tool         | Version | Notes                          |
|--------------|---------|--------------------------------|
| Python       | 3.11+   | Required                       |
| MongoDB      | 6.0+    | Local or Atlas (free tier OK)  |
| unrar / p7zip| latest  | System packages for extraction |

---

## Get API Credentials

### 1. Bot Token
1. Open Telegram and message **[@BotFather](https://t.me/BotFather)**
2. Send `/newbot` and follow the prompts
3. Copy the token: `123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2. Telegram API Credentials
1. Visit **[my.telegram.org](https://my.telegram.org)**
2. Log in with your phone number
3. Go to **API development tools**
4. Create a new application
5. Copy `App api_id` and `App api_hash`

### 3. Your User ID
Message **[@userinfobot](https://t.me/userinfobot)** — it replies with your numeric ID.

---

## Configure the Bot

```bash
# Clone / copy the project
cd unzip_bot

# Copy example config
cp .env.example .env

# Edit with your values
nano .env
```

### Minimum required `.env`:
```env
BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
OWNER_ID=123456789
MONGO_URI=mongodb://localhost:27017
```

### Optional settings:
| Variable              | Default        | Description                            |
|-----------------------|----------------|----------------------------------------|
| `FORCE_SUB_CHANNEL`   | —              | Channel username e.g. `@mychannel`     |
| `FORCE_SUB_ID`        | —              | Channel numeric ID e.g. `-1001234567` |
| `LOG_CHANNEL`         | —              | Log channel numeric ID                 |
| `MAX_FILE_SIZE`       | 2147483648     | 2 GB in bytes                          |
| `PREMIUM_MAX_SIZE`    | 4294967296     | 4 GB in bytes                          |
| `AUTO_DELETE_SECS`    | 60             | Seconds before temp file cleanup       |
| `DEFAULT_LANG`        | en             | `en` or `hi`                           |

---

## MongoDB Setup

### Option A: MongoDB Atlas (Recommended — Free)
1. Sign up at **[cloud.mongodb.com](https://cloud.mongodb.com)**
2. Create a free **M0** cluster
3. Create a database user (Settings → Database Access)
4. Whitelist `0.0.0.0/0` in Network Access
5. Get the connection string:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   ```
6. Set `MONGO_URI` in your `.env`

### Option B: Local MongoDB
```bash
# Ubuntu/Debian
sudo apt-get install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
# Use: MONGO_URI=mongodb://localhost:27017
```

### Indexes created automatically on first run:
```
users.user_id    (unique)
queue.user_id
queue.created_at
```

---

## Deploy on VPS

### 1. Install system dependencies

```bash
# Ubuntu 22.04 / Debian 12
sudo apt-get update
sudo apt-get install -y \
    python3.11 python3.11-venv python3-pip \
    unrar p7zip-full tar gzip bzip2 xz-utils \
    git
```

### 2. Clone and install

```bash
git clone https://github.com/yourname/unzip-bot.git
cd unzip-bot

python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
nano .env   # Fill in your values
```

### 4. Run (foreground test)

```bash
python main.py
```

### 5. Run as systemd service (production)

```bash
sudo nano /etc/systemd/system/unzip-bot.service
```

Paste:
```ini
[Unit]
Description=Telegram UnZip Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/unzip-bot
ExecStart=/home/ubuntu/unzip-bot/venv/bin/python main.py
Restart=always
RestartSec=5
EnvironmentFile=/home/ubuntu/unzip-bot/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable unzip-bot
sudo systemctl start unzip-bot
sudo systemctl status unzip-bot

# View logs
journalctl -u unzip-bot -f
```

---

## Deploy with Docker

### Quick start (with bundled MongoDB)

```bash
cp .env.example .env
# Edit .env — set MONGO_URI=mongodb://botuser:botpassword@mongodb:27017/unzip_bot

docker-compose up -d
docker-compose logs -f bot
```

### Without MongoDB (external Atlas URI)

```bash
# Edit .env with your Atlas URI, then:
docker build -t unzip-bot .
docker run -d \
  --name unzip-bot \
  --env-file .env \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/extracted:/app/extracted \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  unzip-bot
```

---

## Deploy on Railway

1. Push your code to **GitHub**
2. Go to **[railway.app](https://railway.app)** → New Project → Deploy from GitHub
3. Select your repository
4. Add **environment variables** in Railway's Variables panel (copy from `.env`)
5. Add a **MongoDB** plugin: `+ New` → `Database` → `MongoDB`
6. Railway auto-sets `MONGO_URL` — rename it to `MONGO_URI` in your Variables
7. Click **Deploy** — Railway detects `railway.toml` and uses the Dockerfile

```
Build time: ~3 minutes
Free tier: 500 hours/month (enough for one always-on bot)
```

---

## Deploy on Heroku

### Prerequisites
```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
```

### Deploy

```bash
heroku create your-unzip-bot
heroku addons:create mongolab:sandbox   # Free MongoDB

# Set all env vars
heroku config:set BOT_TOKEN="your_token"
heroku config:set API_ID="your_api_id"
heroku config:set API_HASH="your_api_hash"
heroku config:set OWNER_ID="your_user_id"
# MONGO_URI is set automatically by mongolab addon as MONGODB_URI
heroku config:set MONGO_URI=$(heroku config:get MONGODB_URI)

git push heroku main

# Scale worker dyno (NOT web!)
heroku ps:scale worker=1
heroku logs --tail
```

> ⚠️ **Heroku note**: The free tier (Eco dynos) sleeps after 30 minutes of inactivity. Use at least a **Basic** dyno ($7/mo) for a bot.

---

## Bot Commands Reference

| Command   | Description                                    |
|-----------|------------------------------------------------|
| `/start`  | Welcome message with inline menu               |
| `/help`   | Full help text with all features               |
| `/status` | Show your current extraction status            |
| `/cancel` | Cancel the active extraction task              |
| `/clean`  | Delete all your temporary files                |
| `/done`   | Alias for cancel + clean                       |
| `/mode`   | Toggle Document / Media upload mode            |
| `/lang`   | Change language (English / हिन्दी)              |
| `/save`   | Reply to a photo to save it as thumbnail       |
| `/thget`  | View your saved thumbnail                      |
| `/thdel`  | Delete your saved thumbnail                    |

### How to extract an archive:
1. Send any supported archive file to the bot
2. If password-protected, the bot asks you to reply with the password
3. Watch the live progress bar during download and extraction
4. Files are automatically uploaded back to you

### Multi-part archives:
- **RAR**: Send only `part1.rar` — the bot auto-finds the rest (must all be in the same upload batch or send sequentially)
- **ZIP**: Send `archive.zip.001` as the first part

---

## Admin Commands

These commands only work for users listed in `OWNER_ID` or `ADMIN_IDS`.

| Command                  | Description                    |
|--------------------------|--------------------------------|
| `/ban <user_id>`         | Ban a user                     |
| `/unban <user_id>`       | Unban a user                   |
| `/addpremium <user_id>`  | Grant premium status           |
| `/delpremium <user_id>`  | Revoke premium status          |
| `/stats`                 | Global bot statistics          |
| `/broadcast`             | Reply to a message to send it to all users |

---

## Premium System

### What Premium unlocks:
- 📏 **4 GB** max file size (vs 2 GB free)
- ⚡ Priority queue (skips ahead of free users)
- ♾️ No queue limits

### Grant premium via command:
```
/addpremium 123456789
```

### Grant via code (e.g. payment webhook):
```python
from database import set_premium
await set_premium(user_id=123456789, value=True)
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'rarfile'`
```bash
pip install rarfile
# Also ensure unrar is installed:
sudo apt-get install unrar   # or unrar-free
```

### `Cannot extract .rar — unrar not found`
```bash
# Ubuntu
sudo apt-get install unrar
# macOS
brew install rar
```

### `MongoDB connection refused`
- Check your `MONGO_URI` in `.env`
- If using Atlas, verify your IP is whitelisted
- If local: `sudo systemctl start mongod`

### Bot doesn't respond
1. Check `logs/bot.log` for errors
2. Ensure `BOT_TOKEN` is correct
3. Run `python main.py` in foreground to see stdout

### `FloodWait` errors
- Normal for very active bots — Pyrogram handles these automatically
- Increase `PROGRESS_UPDATE_SECS` to reduce Telegram API calls

### Large files fail to download
- Pyrogram streams files — ensure sufficient disk space
- Check `MAX_FILE_SIZE` setting
- Telegram limits bots to ~2 GB without special access

---

## Project Structure

```
unzip_bot/
├── main.py                 # Entry point
├── config.py               # All configuration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── Procfile                # Heroku
├── railway.toml            # Railway
├── app.json                # Heroku manifest
├── .env.example
├── .gitignore
│
├── database/
│   ├── __init__.py
│   └── mongo.py            # All MongoDB operations
│
├── handlers/
│   ├── __init__.py
│   ├── state.py            # Per-user task state
│   ├── commands.py         # Slash command handlers
│   ├── archive.py          # Archive file handler pipeline
│   └── callbacks.py        # Inline button callbacks
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py          # Progress bars, formatters, KB builders
│   └── extractor.py        # Archive extraction engine
│
├── locales/
│   └── strings.py          # i18n strings (EN + HI)
│
├── downloads/              # Temp: downloaded archives (auto-cleaned)
├── extracted/              # Temp: extracted files (auto-cleaned)
├── thumbnails/             # Custom thumbnails
└── logs/                   # Rotating log files
```
