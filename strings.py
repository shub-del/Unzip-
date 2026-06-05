"""
╔══════════════════════════════════════════════════════════╗
║           UNZIP BOT — locales/strings.py                 ║
║  All user-facing strings, keyed by language code.        ║
╚══════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {

    # ─── ENGLISH ─────────────────────────────────────────────────────────────────
    "en": {
        # Greetings
        "start": (
            "╔══════════════════════════════╗\n"
            "║   🗜️  **UnZip Bot**           ║\n"
            "╚══════════════════════════════╝\n\n"
            "Hey **{name}**! 👋\n"
            "Send me any archive and I'll extract it instantly.\n\n"
            "📦 **Supported formats:**\n"
            "`ZIP · RAR · 7Z · TAR · GZ · BZ2 · XZ`\n\n"
            "💡 Use /help to see all commands."
        ),
        "help": (
            "📖 **Help & Commands**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**Extraction**\n"
            "• Send any archive → automatic extraction\n"
            "• Password protected? I'll ask you!\n\n"
            "**Commands**\n"
            "/start  — Welcome message\n"
            "/help   — This menu\n"
            "/status — Your current task status\n"
            "/cancel — Cancel active extraction\n"
            "/clean  — Delete your temp files\n"
            "/done   — Mark task as done\n"
            "/mode   — Toggle Document / Media upload\n"
            "/lang   — Change language\n"
            "/save   — Save a custom thumbnail\n"
            "/thget  — View your thumbnail\n"
            "/thdel  — Delete your thumbnail\n\n"
            "**Premium** 👑\n"
            "• Up to 4 GB file size\n"
            "• Priority queue\n"
            "• No ads\n\n"
            "📌 Multi-part archives are auto-detected!\n"
            "🔐 Encrypted archives supported.\n"
        ),
        "force_sub": (
            "⚠️ **Join Required**\n\n"
            "Please join our channel to use this bot:\n"
            "👉 {channel}\n\n"
            "After joining, press **✅ Joined** below."
        ),
        "banned": "🚫 You have been banned from using this bot.",
        "wait_queue": "⏳ You have {n} task(s) in queue. Please wait.",
        "queue_full": "🚦 Queue full ({max} tasks). Please wait or /cancel.",

        # File handling
        "unsupported": (
            "❌ **Unsupported format**\n\n"
            "Supported: `ZIP RAR 7Z TAR GZ BZ2 XZ`\n"
            "Send a valid archive file."
        ),
        "too_large": (
            "📏 **File too large!**\n\n"
            "Max size: **{max}**\n"
            "Your file: **{size}**\n\n"
            "👑 Upgrade to Premium for larger files."
        ),
        "downloading": "⬇️ Downloading **{name}** …\n\n{bar}  {percent}%\n{done} / {total}  •  {speed}/s  •  ETA {eta}",
        "extracting":  "🗜️ Extracting **{name}** …\n\n{bar}  {percent}%",
        "ask_password": "🔐 **Password Protected Archive**\n\nPlease send the password as a reply to this message.\n\n_Send /cancel to abort._",
        "wrong_password": "❌ Wrong password! Please try again or /cancel.",
        "corrupt": (
            "💥 **Corrupted Archive**\n\n"
            "The archive appears to be damaged.\n"
            "Error: `{error}`"
        ),
        "extract_done": "✅ **Extraction complete!**\n\n📂 {count} file(s) extracted  •  {size} total\n\n⬆️ Uploading now…",
        "uploading":    "⬆️ Uploading **{name}** …\n\n{bar}  {percent}%\n{done} / {total}  •  {speed}/s",
        "all_done": (
            "🎉 **All Done!**\n\n"
            "✅ {count} file(s) uploaded successfully.\n"
            "📦 Archive: `{archive}`\n"
            "💾 Total size: **{size}**\n"
            "⏱ Time taken: **{time}**\n\n"
            "Temp files auto-delete in {del_secs}s."
        ),
        "cancelled":  "🛑 Task cancelled.",
        "no_active":  "ℹ️ No active task.",
        "cleaned":    "🧹 Temp files cleaned.",
        "status_idle": "💤 No active extraction.",
        "status_active": (
            "📊 **Current Status**\n\n"
            "🗂 File: `{name}`\n"
            "📍 Stage: **{stage}**\n"
            "📈 Progress: **{percent}%**\n"
            "⏱ Elapsed: **{elapsed}**"
        ),

        # Mode & Settings
        "mode_set":  "⚙️ Upload mode set to **{mode}**.",
        "lang_set":  "🌐 Language set to **English**.",
        "thumb_saved": "🖼️ Custom thumbnail saved!",
        "thumb_none":  "❌ No thumbnail set.",
        "thumb_deleted": "🗑️ Thumbnail deleted.",

        # Errors
        "error_generic": "⚠️ Something went wrong:\n`{error}`",
        "not_archive":   "❌ Please send an archive file, not just text.",
    },

    # ─── HINDI ───────────────────────────────────────────────────────────────────
    "hi": {
        "start": (
            "╔══════════════════════════════╗\n"
            "║   🗜️  **अनज़िप बॉट**          ║\n"
            "╚══════════════════════════════╝\n\n"
            "नमस्ते **{name}**! 👋\n"
            "कोई भी आर्काइव भेजें और मैं उसे तुरंत निकालूँगा।\n\n"
            "📦 **समर्थित प्रारूप:**\n"
            "`ZIP · RAR · 7Z · TAR · GZ · BZ2 · XZ`\n\n"
            "💡 सभी कमांड देखने के लिए /help टाइप करें।"
        ),
        "help": (
            "📖 **सहायता और कमांड**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**एक्सट्रेक्शन**\n"
            "• कोई भी आर्काइव भेजें → स्वचालित एक्सट्रेक्शन\n"
            "• पासवर्ड संरक्षित? मैं पूछूँगा!\n\n"
            "सभी कमांड /start संदेश में देखें।"
        ),
        "banned": "🚫 आपको इस बॉट से प्रतिबंधित किया गया है।",
        "unsupported": "❌ **असमर्थित प्रारूप।** ZIP RAR 7Z TAR GZ BZ2 XZ भेजें।",
        "too_large": "📏 **फ़ाइल बहुत बड़ी है!** अधिकतम: {max} | आपकी: {size}",
        "downloading": "⬇️ **{name}** डाउनलोड हो रहा है…\n\n{bar}  {percent}%",
        "extracting":  "🗜️ **{name}** निकाला जा रहा है…\n\n{bar}  {percent}%",
        "ask_password": "🔐 यह आर्काइव पासवर्ड से सुरक्षित है। कृपया पासवर्ड भेजें।",
        "wrong_password": "❌ गलत पासवर्ड! दोबारा कोशिश करें या /cancel करें।",
        "corrupt":     "💥 **दूषित आर्काइव।** त्रुटि: `{error}`",
        "extract_done": "✅ एक्सट्रेक्शन पूर्ण! {count} फ़ाइलें | {size}",
        "uploading":   "⬆️ **{name}** अपलोड हो रहा है…\n{bar}  {percent}%",
        "all_done":    "🎉 **पूर्ण!** {count} फ़ाइलें अपलोड की गईं। आकार: {size}",
        "cancelled":   "🛑 कार्य रद्द किया गया।",
        "no_active":   "ℹ️ कोई सक्रिय कार्य नहीं।",
        "cleaned":     "🧹 अस्थायी फ़ाइलें हटाई गईं।",
        "mode_set":    "⚙️ अपलोड मोड **{mode}** पर सेट किया गया।",
        "lang_set":    "🌐 भाषा **हिन्दी** में सेट की गई।",
        "thumb_saved": "🖼️ कस्टम थंबनेल सहेजा गया!",
        "thumb_none":  "❌ कोई थंबनेल सेट नहीं है।",
        "thumb_deleted": "🗑️ थंबनेल हटाया गया।",
        "error_generic": "⚠️ कुछ गलत हुआ:\n`{error}`",
        "not_archive":  "❌ कृपया एक आर्काइव फ़ाइल भेजें।",
        "force_sub":   "⚠️ बॉट उपयोग करने के लिए हमारे चैनल से जुड़ें:\n👉 {channel}",
        "wait_queue":  "⏳ आपके {n} कार्य कतार में हैं। कृपया प्रतीक्षा करें।",
        "queue_full":  "🚦 कतार भरी है। /cancel करें या प्रतीक्षा करें।",
        "status_idle": "💤 कोई सक्रिय एक्सट्रेक्शन नहीं।",
        "status_active": "📊 **वर्तमान स्थिति**\n🗂 फ़ाइल: `{name}`\n📍 चरण: {stage}\n📈 प्रगति: {percent}%",
    },
}


def get_string(lang: str, key: str, **kwargs: object) -> str:
    """Return localised string for key, falling back to English."""
    template = STRINGS.get(lang, STRINGS["en"]).get(key) or STRINGS["en"].get(key, key)
    try:
        return template.format(**kwargs)
    except KeyError:
        return template
