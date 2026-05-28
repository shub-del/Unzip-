# ⚡ Telegram Unzip Bot

Telegram par archive files (zip, rar, 7z, tar.gz) extract karne wala bot.

## ✅ Features
- 📦 ZIP, RAR, 7z, TAR.GZ, TAR.BZ2, TAR.XZ support
- 🔒 Password-protected archives
- 📤 Document ya Media mode upload
- 🧹 Auto cleanup
- ⚡ Fast extraction with progress updates

---

## 🚀 Render Par Deploy Kaise Karein

### Step 1 — Bot Token Banao
1. Telegram par [@BotFather](https://t.me/BotFather) ko open karo
2. `/newbot` command do
3. Naam aur username do
4. **BOT_TOKEN** copy karo

### Step 2 — Owner ID Lao
1. [@userinfobot](https://t.me/userinfobot) ko message karo
2. Aapka **User ID** (numbers) copy karo

### Step 3 — GitHub Par Upload Karo
1. [github.com](https://github.com) par ek naya repo banao
2. Saari files upload karo (bot.py, requirements.txt, render.yaml)

### Step 4 — Render Par Deploy Karo
1. [render.com](https://render.com) par sign up karo (free)
2. **New +** → **Web Service** click karo
3. Apna GitHub repo connect karo
4. Ye settings karo:
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** Free
5. **Environment Variables** mein add karo:
   - `BOT_TOKEN` = aapka bot token
   - `OWNER_ID`  = aapka Telegram ID
6. **Create Web Service** click karo ✅

---

## 💬 Bot Commands
| Command | Kaam |
|---------|------|
| /start  | Bot start karo |
| /help   | Help dekho |
| /status | Account status |
| /cancel | Process cancel karo |
| /clean  | Files delete karo |
| /done   | Session khatam karo |
| /mode   | Upload mode set karo |
| /lang   | Language set karo |

---

## 📁 Usage
1. Bot ko koi `.zip / .rar / .7z / .tar.gz` file bhejo
2. Bot automatically extract karega
3. Sare files wapas bhej dega
4. Password protected archive hai toh password maangega

---
Made with ❤️ Python + python-telegram-bot
