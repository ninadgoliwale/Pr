import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Get from Secrets (Environment Variables)
TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('OWNER_ID', 0))

# Get 7 groups from Secrets
GROUPS = []
for i in range(1, 8):
    link = os.environ.get(f'GROUP_{i}')
    if link:
        GROUPS.append(link)

# Group names (can't put emojis in Secrets, so names here)
GROUP_NAMES = [
    "Free Earning Loots 🎁🎁",
    "Dhani Extra Loot",
    "Earn Loot Tips 🏆🏆",
    "Super Loots",
    "Mani looters (official)",
    "Diwa 777 Game Codes !!",
    "Tricks By Manas [Official]"
]

DATA_FILE = 'users.json'

def get_users():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = get_users()
    
    if user_id not in users:
        users[user_id] = {'joined': []}
        save_users(users)
    
    keyboard = []
    for i in range(len(GROUPS)):
        if i in users[user_id]['joined']:
            keyboard.append([InlineKeyboardButton(f"✅ {GROUP_NAMES[i]}", callback_data="no")])
        else:
            keyboard.append([InlineKeyboardButton(f"🔗 {GROUP_NAMES[i]}", callback_data=f"join_{i}")])
    
    if len(users[user_id]['joined']) >= len(GROUPS):
        keyboard.append([InlineKeyboardButton("✅ CLAIM", callback_data="claim")])
    
    await update.message.reply_text(
        f"👤 *Hey There {update.effective_user.first_name}! Welcome To Bot!*\n\n"
        f"⚠️ *Must Join Total {len(GROUPS)} Channel To Use Our Bot*\n"
        f"📧 *After Joining Click Claim*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = query.data
    users = get_users()
    
    if data.startswith("join_"):
        idx = int(data.split("_")[1])
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔗 JOIN NOW", url=GROUPS[idx]),
            InlineKeyboardButton("✅ I HAVE JOINED", callback_data=f"done_{idx}")
        ]])
        await query.edit_message_text(
            f"📢 *Join This Channel*\n\nChannel: *{GROUP_NAMES[idx]}*\n\nAfter joining, click 'I HAVE JOINED'.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    
    elif data.startswith("done_"):
        idx = int(data.split("_")[1])
        if idx not in users[user_id]['joined']:
            users[user_id]['joined'].append(idx)
            save_users(users)
        
        keyboard = []
        for i in range(len(GROUPS)):
            if i in users[user_id]['joined']:
                keyboard.append([InlineKeyboardButton(f"✅ {GROUP_NAMES[i]}", callback_data="no")])
            else:
                keyboard.append([InlineKeyboardButton(f"🔗 {GROUP_NAMES[i]}", callback_data=f"join_{i}")])
        
        if len(users[user_id]['joined']) >= len(GROUPS):
            keyboard.append([InlineKeyboardButton("✅ CLAIM", callback_data="claim")])
        
        await query.edit_message_text(
            f"👤 *Hey There {query.from_user.first_name}! Welcome To Bot!*\n\n"
            f"⚠️ *Must Join Total {len(GROUPS)} Channel To Use Our Bot*\n"
            f"📧 *After Joining Click Claim*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif data == "claim":
        if len(users[user_id]['joined']) >= len(GROUPS):
            await query.edit_message_text(
                f"✅ *CLAIM SUCCESSFUL!*\n\nThank you for joining all {len(GROUPS)} channels!\n\n💰 Your reward will be processed soon.",
                parse_mode="Markdown"
            )
            await context.bot.send_message(OWNER_ID, f"💰 New Claim!\nUser: {query.from_user.first_name}\nID: {user_id}")
        else:
            await query.answer("Join all groups first!", show_alert=True)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    users = get_users()
    verified = sum(1 for u in users.values() if len(u['joined']) >= len(GROUPS))
    await update.message.reply_text(f"📊 Users: {len(users)}\n✅ Verified: {verified}")

def main():
    if not TOKEN:
        print("ERROR: BOT_TOKEN not set in Secrets!")
        return
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button))
    
    print(f"✅ Bot started! {len(GROUPS)} groups loaded")
    app.run_polling()

if __name__ == "__main__":
    main()