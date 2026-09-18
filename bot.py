import logging
import json
import os
import random
import string
import requests
import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

# ============================================
# ⚙️ CONFIGURATION
# ============================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8823047979:AAGzzGGNYUaH5-o400m0Zx4ozvxjwgvIFxo")
PORT = int(os.environ.get("PORT", 8080))

# ============================================
# 🌐 PETIT SERVEUR WEB POUR RAILWAY
# ============================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 ProBot est en ligne !", 200

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# ============================================
# 📝 LOGGING
# ============================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# 💾 BASE DE DONNÉES
# ============================================
DATA_FILE = "users.json"

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"users": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# ============================================
# 🚀 COMMANDE /start
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_data()

    uid = str(user.id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": user.first_name,
            "start_date": str(datetime.now())
        }
        save_data(data)

    keyboard = [
        [InlineKeyboardButton("🛠️ Outils", callback_data="menu_tools"),
         InlineKeyboardButton("💰 Crypto", callback_data="menu_crypto")],
        [InlineKeyboardButton("🎮 Jeux", callback_data="menu_games"),
         InlineKeyboardButton("❓ Aide", callback_data="menu_help")]
    ]

    text = f"""
🤖 *Salut {user.first_name} !*

Je suis *ProBot*, ton assistant personnel.

📋 *Commandes :*
/start - Menu principal
/calc 2+2 - Calculatrice
/crypto - Prix crypto
/weather Paris - Météo
/quiz - Quiz
/rps - Pierre-Feuille-Ciseaux
/password - Mot de passe
/quote - Citation

Utilise les boutons 👇
    """

    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================
# 🧮 CALCULATRICE
# ============================================
async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🧮 Usage: /calc 2+2*3")
        return

    expr = " ".join(context.args)
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expr):
        await update.message.reply_text("❌ Caractères invalides!")
        return

    try:
        result = eval(expr)
        await update.message.reply_text(
            f"🧮 `{expr}` = *{result}*",
            parse_mode='Markdown'
        )
    except:
        await update.message.reply_text("❌ Expression invalide")

# ============================================
# 💰 PRIX CRYPTO
# ============================================
async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coins = context.args[0] if context.args else "bitcoin,ethereum,solana"

    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coins,
            "vs_currencies": "usd,eur",
            "include_24hr_change": "true"
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        msg = "💰 *PRIX CRYPTO*\n\n"
        for coin, vals in data.items():
            change = vals.get('usd_24h_change', 0)
            emoji = "📈" if change >= 0 else "📉"
            msg += f"*{coin.upper()}*\n"
            msg += f"💵 ${vals['usd']:,.2f}\n"
            msg += f"💶 €{vals['eur']:,.2f}\n"
            msg += f"{emoji} {change:+.2f}% (24h)\n\n"

        await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {e}")

# ============================================
# 🌤️ MÉTÉO
# ============================================
async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🌤️ Usage: /weather Paris")
        return

    city = " ".join(context.args)
    try:
        url = f"https://wttr.in/{city}?format=j1"
        r = requests.get(url, timeout=10)
        data = r.json()
        current = data['current_condition'][0]

        msg = f"""
🌤️ *Météo à {city}*

🌡️ {current['temp_C']}°C (ressenti {current['FeelsLikeC']}°C)
💧 Humidité: {current['humidity']}%
💨 Vent: {current['windspeedKmph']} km/h
☁️ {current['weatherDesc'][0]['value']}
        """
        await update.message.reply_text(msg, parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Ville non trouvée")

# ============================================
# 🎮 QUIZ
# ============================================
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = [
        {"q": "Capitale de l'Australie?", "opts": ["Sydney", "Canberra", "Melbourne"], "a": 1},
        {"q": "Planètes dans le système solaire?", "opts": ["7", "8", "9"], "a": 1},
        {"q": "Qui a peint la Joconde?", "opts": ["Michel-Ange", "De Vinci", "Raphael"], "a": 1},
        {"q": "Année premier pas sur la Lune?", "opts": ["1965", "1969", "1972"], "a": 1},
        {"q": "Plus grand océan?", "opts": ["Atlantique", "Pacifique", "Indien"], "a": 1},
        {"q": "Créateur de Python?", "opts": ["Guido van Rossum", "Linus Torvalds", "James Gosling"], "a": 0},
        {"q": "Combien d'os dans le corps?", "opts": ["186", "206", "226"], "a": 1},
    ]

    q = random.choice(questions)
    keyboard = [[InlineKeyboardButton(o, callback_data=f"quiz_{q['a']}_{i}")]
                for i, o in enumerate(q["opts"])]

    await update.message.reply_text(
        f"🧠 *QUIZ*\n\n{q['q']}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================
# 🎮 PIERRE-FEUILLE-CISEAUX
# ============================================
async def rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("🪨 Pierre", callback_data="rps_rock"),
        InlineKeyboardButton("📄 Feuille", callback_data="rps_paper"),
        InlineKeyboardButton("✂️ Ciseaux", callback_data="rps_scissors")
    ]]
    await update.message.reply_text(
        "🎮 *Pierre-Feuille-Ciseaux*\nChoisis!",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================
# 🔐 MOT DE PASSE
# ============================================
async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    length = int(context.args[0]) if context.args else 16
    length = min(max(length, 8), 64)
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    pwd = ''.join(random.choice(chars) for _ in range(length))
    await update.message.reply_text(
        f"🔐 *Mot de passe* ({length} car.):\n\n`{pwd}`",
        parse_mode='Markdown'
    )

# ============================================
# 💬 CITATION
# ============================================
async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quotes = [
        ("Le succès c'est d'aller d'échec en échec sans perdre l'enthousiasme.", "Churchill"),
        ("La seule façon de faire du bon travail est d'aimer ce que vous faites.", "Steve Jobs"),
        ("Talk is cheap. Show me the code.", "Linus Torvalds"),
        ("D'abord résolvez le problème, ensuite écrivez le code.", "John Johnson"),
        ("Le code est comme l'humour. Quand il faut l'expliquer, c'est mauvais.", "Paul Litwaker"),
    ]
    q, a = random.choice(quotes)
    await update.message.reply_text(
        f"💬 _\"{q}\"_\n\n— *{a}*",
        parse_mode='Markdown'
    )

# ============================================
# 🔘 GESTION DES BOUTONS
# ============================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_tools":
        await query.edit_message_text(
            "🛠️ *OUTILS*\n\n"
            "/calc - Calcul\n"
            "/password - Mot de passe\n"
            "/weather - Météo",
            parse_mode='Markdown'
        )
    elif data == "menu_crypto":
        await query.edit_message_text(
            "💰 *CRYPTO*\n\n"
            "/crypto - BTC, ETH, SOL\n"
            "/crypto doge - DOGE",
            parse_mode='Markdown'
        )
    elif data == "menu_games":
        kb = [[
            InlineKeyboardButton("🧠 Quiz", callback_data="play_quiz"),
            InlineKeyboardButton("🎮 RPS", callback_data="play_rps")
        ]]
        await query.edit_message_text(
            "🎮 *JEUX*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(kb)
        )
    elif data == "menu_help":
        await query.edit_message_text(
            "📖 *AIDE COMPLÈTE*\n\n"
            "/start - Menu\n"
            "/calc 2+2 - Calcul\n"
            "/crypto - Crypto\n"
            "/weather Paris - Météo\n"
            "/quiz - Quiz\n"
            "/rps - Pierre-Feuille-Ciseaux\n"
            "/password 16 - Mot de passe\n"
            "/quote - Citation",
            parse_mode='Markdown'
        )
    elif data == "play_quiz":
        await quiz(update, context)
    elif data == "play_rps":
        await rps(update, context)
    elif data.startswith("quiz_"):
        parts = data.split("_")
        correct = int(parts[1])
        chosen = int(parts[2])
        if correct == chosen:
            await query.edit_message_text("✅ Bravo! Bonne réponse! 🎉")
        else:
            await query.edit_message_text(f"❌ Raté! Bonne réponse: option {correct+1}")
    elif data.startswith("rps_"):
        choices = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        user_c = data.split("_")[1]
        bot_c = random.choice(["rock", "paper", "scissors"])
        wins = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

        if user_c == bot_c:
            result = "🤝 Égalité!"
        elif wins[user_c] == bot_c:
            result = "🎉 Tu gagnes!"
        else:
            result = "😢 Tu perds!"

        await query.edit_message_text(
            f"Toi: {choices[user_c]} vs Bot: {choices[bot_c]}\n\n{result}"
        )

# ============================================
# ❌ GESTION ERREURS
# ============================================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f'Error: {context.error}')

# ============================================
# 🏁 MAIN
# ============================================
def main():
    print("🤖 ProBot démarre...")

    # Lancer le serveur web dans un thread séparé
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"🌐 Serveur web démarré sur le port {PORT}")

    # Lancer le bot Telegram
    app_bot = Application.builder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("calc", calc))
    app_bot.add_handler(CommandHandler("crypto", crypto))
    app_bot.add_handler(CommandHandler("weather", weather))
    app_bot.add_handler(CommandHandler("quiz", quiz))
    app_bot.add_handler(CommandHandler("rps", rps))
    app_bot.add_handler(CommandHandler("password", password))
    app_bot.add_handler(CommandHandler("quote", quote))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_error_handler(error_handler)

    print("✅ ProBot est EN LIGNE!")
    print("📱 Ouvre Telegram et cherche ton bot!")
    app_bot.run_polling()

if __name__ == "__main__":
    main()