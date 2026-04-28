import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('OWNER_ID', 0))

# Get group links from environment variables
GROUP_LINKS = []
for i in range(1, 8):
    link = os.environ.get(f'GROUP_{i}')
    if link:
        GROUP_LINKS.append(link)

# Group display names
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

def load_users():
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
    users = load_users()
    
    if user_id not in users:
        users[user_id] = {'joined': []}
        save_users(users)
    
    keyboard = []
    for i in range(len(GROUP_LINKS)):
        if i in users[user_id]['joined']:
            keyboard.append([InlineKeyboardButton(f"✅ {GROUP_NAMES[i]}", callback_data=f"already_{i}")])
        else:
            keyboard.append([InlineKeyboardButton(f"🔗 {GROUP_NAMES[i]}", callback_data=f"join_{i}")])
    
    if len(users[user_id]['joined']) >= len(GROUP_LINKS):
        keyboard.append([InlineKeyboardButton("✅ CLAIM", callback_data="claim")])
    
    await update.message.reply_text(
        f"👤 *Hey There {update.effective_user.first_name}! Welcome To Bot!*\n\n"
        f"⚠️ *Must Join Total {len(GROUP_LINKS)} Channel To Use Our Bot*\n"
        f"📧 *After Joining Click Claim*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    users = load_users()
    
    print(f"DEBUG: Callback received: {data} from user {user_id}")  # Check Replit logs
    
    if data.startswith("join_"):
        idx = int(data.split("_")[1])
        group_name = GROUP_NAMES[idx]
        group_link = GROUP_LINKS[idx]
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔗 JOIN NOW", url=group_link),
            InlineKeyboardButton("✅ I HAVE JOINED", callback_data=f"joined_{idx}")
        ]])
        
        await query.edit_message_text(
            f"📢 *Join This Channel*\n\n"
            f"Channel: *{group_name}*\n\n"
            f"After joining, click the button below:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif data.startswith("joined_"):
        idx = int(data.split("_")[1])
        
        if idx not in users[user_id]['joined']:
            users[user_id]['joined'].append(idx)
            save_users(users)
        
        # Rebuild main menu
        keyboard = []
        for i in range(len(GROUP_LINKS)):
            if i in users[user_id]['joined']:
                keyboard.append([InlineKeyboardButton(f"✅ {GROUP_NAMES[i]}", callback_data=f"already_{i}")])
            else:
                keyboard.append([InlineKeyboardButton(f"🔗 {GROUP_NAMES[i]}", callback_data=f"join_{i}")])
        
        if len(users[user_id]['joined']) >= len(GROUP_LINKS):
            keyboard.append([InlineKeyboardButton("✅ CLAIM", callback_data="claim")])
        
        await query.edit_message_text(
            f"👤 *Hey There {query.from_user.first_name}! Welcome To Bot!*\n\n"
            f"⚠️ *Must Join Total {len(GROUP_LINKS)} Channel To Use Our Bot*\n"
            f"📧 *After Joining Click Claim*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif data == "claim":
        if len(users[user_id]['joined']) >= len(GROUP_LINKS):
            await query.edit_message_text(
                f"✅ *CLAIM SUCCESSFUL!*\n\n"
                f"Thank you for joining all {len(GROUP_LINKS)} channels!\n\n"
                f"💰 Your reward will be processed soon.\n\n"
                f"Keep visiting for more rewards!",
                parse_mode="Markdown"
            )
            await context.bot.send_message(
                OWNER_ID,
                f"💰 *New Claim!*\n\n"
                f"User: {query.from_user.first_name}\n"
                f"ID: `{user_id}`\n"
                f"Username: @{query.from_user.username or 'N/A'}",
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ Join all groups first!", show_alert=True)
    
    elif data.startswith("already_"):
        await query.answer("✅ You already joined this group!", show_alert=True)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Unauthorized!")
        return
    
    users = load_users()
    total = len(users)
    verified = sum(1 for u in users.values() if len(u['joined']) >= len(GROUP_LINKS))
    
    await update.message.reply_text(
        f"📊 *Bot Statistics*\n\n"
        f"👥 Total Users: {total}\n"
        f"✅ Verified Users: {verified}\n"
        f"📢 Groups: {len(GROUP_LINKS)}",
        parse_mode="Markdown"
    )

def main():
    if not TOKEN:
        print("❌ ERROR: BOT_TOKEN not set in Secrets!")
        return
    
    print(f"✅ Bot starting...")
    print(f"📢 Loaded {len(GROUP_LINKS)} groups")
    print(f"👑 Owner ID: {OWNER_ID}")
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("🚀 Bot is running! Press Ctrl+C to stop")
    app.run_polling()

if __name__ == "__main__":
    main()