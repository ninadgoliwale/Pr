import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 0))

# Get 6 groups from environment variables
GROUPS = []
for i in range(1, 7):
    group_data = os.getenv(f'GROUP_{i}', '')
    if group_data:
        name, link = group_data.split(',', 1)
        GROUPS.append({'name': name, 'link': link})

USER_DATA_FILE = 'user_data.json'

def load_users():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()
    
    if user_id not in users:
        users[user_id] = {'joined': []}
        save_users(users)
    
    joined_count = len(users[user_id]['joined'])
    
    # Create join buttons
    keyboard = []
    for i, group in enumerate(GROUPS):
        if i in users[user_id]['joined']:
            keyboard.append([InlineKeyboardButton(f"✅ {group['name']} (Joined)", callback_data=f"dummy")])
        else:
            keyboard.append([InlineKeyboardButton(f"🔗 {group['name']}", callback_data=f"join_{i}")])
    
    # Claim button - shows only if all groups joined
    if joined_count >= len(GROUPS):
        keyboard.append([InlineKeyboardButton("✅ CLAIM", callback_data="claim")])
    
    await update.message.reply_text(
        f"👤 *Hey There {update.effective_user.first_name}! Welcome To Bot!*\n\n"
        f"⚠️ *Must Join Total {len(GROUPS)} Channel To Use Our Bot*\n"
        f"📧 *After Joining Click Claim*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = query.data
    
    users = load_users()
    
    if data.startswith("join_"):
        group_index = int(data.split("_")[1])
        group = GROUPS[group_index]
        
        # Send join link button
        join_keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔗 JOIN NOW", url=group['link']),
            InlineKeyboardButton("✅ I HAVE JOINED", callback_data=f"joined_{group_index}")
        ]])
        
        await query.edit_message_text(
            f"📢 *Join This Channel*\n\n"
            f"Channel: *{group['name']}*\n\n"
            f"After joining, click the 'I HAVE JOINED' button.",
            reply_markup=join_keyboard,
            parse_mode="Markdown"
        )
    
    elif data.startswith("joined_"):
        group_index = int(data.split("_")[1])
        
        if group_index not in users[user_id]['joined']:
            users[user_id]['joined'].append(group_index)
            save_users(users)
        
        # Show updated main menu
        joined_count = len(users[user_id]['joined'])
        
        keyboard = []
        for i, group in enumerate(GROUPS):
            if i in users[user_id]['joined']:
                keyboard.append([InlineKeyboardButton(f"✅ {group['name']} (Joined)", callback_data=f"dummy")])
            else:
                keyboard.append([InlineKeyboardButton(f"🔗 {group['name']}", callback_data=f"join_{i}")])
        
        if joined_count >= len(GROUPS):
            keyboard.append([InlineKeyboardButton("✅ CLAIM", callback_data="claim")])
        
        await query.edit_message_text(
            f"👤 *Hey There {query.from_user.first_name}! Welcome To Bot!*\n\n"
            f"⚠️ *Must Join Total {len(GROUPS)} Channel To Use Our Bot*\n"
            f"📧 *After Joining Click Claim*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif data == "claim":
        joined_count = len(users[user_id]['joined'])
        
        if joined_count >= len(GROUPS):
            await query.edit_message_text(
                f"✅ *CLAIM SUCCESSFUL!*\n\n"
                f"Thank you for joining all {len(GROUPS)} channels!\n\n"
                f"💰 Your reward will be processed soon.\n\n"
                f"Keep visiting for more rewards!",
                parse_mode="Markdown"
            )
            # Notify owner
            await context.bot.send_message(
                OWNER_ID,
                f"💰 *New Claim!*\n\n"
                f"User: {query.from_user.first_name}\n"
                f"ID: `{user_id}`\n"
                f"Username: @{query.from_user.username or 'N/A'}",
                parse_mode="Markdown"
            )
        else:
            await query.answer("Join all groups first!", show_alert=True)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Unauthorized!")
        return
    
    users = load_users()
    total_users = len(users)
    total_verified = sum(1 for u in users.values() if len(u['joined']) >= len(GROUPS))
    
    await update.message.reply_text(
        f"📊 *Bot Stats*\n\n"
        f"👥 Total Users: {total_users}\n"
        f"✅ Verified Users: {total_verified}\n"
        f"📢 Groups: {len(GROUPS)}",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print(f"✅ Bot started! Owner: {OWNER_ID}")
    print(f"📢 {len(GROUPS)} groups configured")
    
    app.run_polling()

if __name__ == "__main__":
    main()