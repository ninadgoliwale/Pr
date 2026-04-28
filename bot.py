import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
OWNER = int(os.getenv('OWNER_ID', 0))

# YOUR 7 GROUPS FROM IMAGE (change names and links as needed)
GROUPS = [
    {"name": "Free Earning Loots 🎁🎁", "link": os.getenv('GROUP_1')},
    {"name": "Dhani Extra Loot", "link": os.getenv('GROUP_2')},
    {"name": "Earn Loot Tips 🏆🏆", "link": os.getenv('GROUP_3')},
    {"name": "Super Loots", "link": os.getenv('GROUP_4')},
    {"name": "Mani looters (official)", "link": os.getenv('GROUP_5')},
    {"name": "Diwa 777 Game Codes !!", "link": os.getenv('GROUP_6')},
    {"name": "Tricks By Manas [Official]", "link": os.getenv('GROUP_7')},
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
    for i, group in enumerate(GROUPS):
        if i in users[user_id]['joined']:
            keyboard.append([InlineKeyboardButton(f"✅ {group['name']}", callback_data="no")])
        else:
            keyboard.append([InlineKeyboardButton(f"🔗 {group['name']}", callback_data=f"join_{i}")])
    
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
        group = GROUPS[idx]
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔗 JOIN NOW", url=group['link']),
            InlineKeyboardButton("✅ I HAVE JOINED", callback_data=f"done_{idx}")
        ]])
        await query.edit_message_text(
            f"📢 *Join This Channel*\n\nChannel: *{group['name']}*\n\nAfter joining, click 'I HAVE JOINED'.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    
    elif data.startswith("done_"):
        idx = int(data.split("_")[1])
        if idx not in users[user_id]['joined']:
            users[user_id]['joined'].append(idx)
            save_users(users)
        
        keyboard = []
        for i, g in enumerate(GROUPS):
            if i in users[user_id]['joined']:
                keyboard.append([InlineKeyboardButton(f"✅ {g['name']}", callback_data="no")])
            else:
                keyboard.append([InlineKeyboardButton(f"🔗 {g['name']}", callback_data=f"join_{i}")])
        
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
            await context.bot.send_message(OWNER, f"💰 New Claim!\nUser: {query.from_user.first_name}\nID: {user_id}")
        else:
            await query.answer("Join all groups first!", show_alert=True)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER:
        return
    users = get_users()
    await update.message.reply_text(f"📊 Total Users: {len(users)}\n✅ Verified: {sum(1 for u in users.values() if len(u['joined']) >= len(GROUPS))}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()