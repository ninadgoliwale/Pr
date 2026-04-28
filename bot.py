import os
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from Environment Variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 0))
MIN_WITHDRAWAL = int(os.getenv('MIN_WITHDRAWAL', 100))
DAILY_BONUS = int(os.getenv('DAILY_BONUS', 5))
REFERRAL_BONUS = int(os.getenv('REFERRAL_BONUS', 3))

# Get group/channel links from environment variables
GROUP_LINKS = []
for i in range(1, 7):
    group_data = os.getenv(f'GROUP_{i}', '')
    if group_data:
        parts = group_data.split(',', 1)
        if len(parts) == 2:
            GROUP_LINKS.append({'name': parts[0], 'link': parts[1], 'joined': False})

# User data storage
user_data = {}
DATA_FILE = 'user_data.json'

def load_user_data():
    global user_data
    try:
        with open(DATA_FILE, 'r') as f:
            user_data = json.load(f)
    except FileNotFoundError:
        user_data = {}

def save_user_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(user_data, f, indent=2)

def get_user(user_id):
    user_id = str(user_id)
    if user_id not in user_data:
        user_data[user_id] = {
            'verified': False,
            'verified_groups': [],
            'balance': 0,
            'last_daily': None,
            'referrals': 0,
            'referred_by': None
        }
        save_user_data()
    return user_data[user_id]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    # Check for referral
    if context.args and not user.get('referred_by'):
        referrer_id = context.args[0]
        if str(referrer_id) != str(user_id):
            referrer = get_user(referrer_id)
            referrer['balance'] += REFERRAL_BONUS
            referrer['referrals'] += 1
            user['referred_by'] = str(referrer_id)
            save_user_data()
            await context.bot.send_message(
                int(referrer_id),
                f"🎉 New referral! +{REFERRAL_BONUS}₹ added to your balance!"
            )
    
    welcome_text = (
        f"🌟 *Welcome to RDX Verification System* 🌟\n\n"
        f"Please join our channels/groups to verify your account.\n\n"
        f"💰 *Rewards:*\n"
        f"• Daily Bonus: {DAILY_BONUS}₹\n"
        f"• Per Referral: {REFERRAL_BONUS}₹\n"
        f"• Minimum Withdrawal: {MIN_WITHDRAWAL}₹\n\n"
        f"👇 *Click the buttons below to join:*"
    )
    
    keyboard = []
    for i, group in enumerate(GROUP_LINKS):
        status = "✅" if i in user['verified_groups'] else "❌"
        keyboard.append([InlineKeyboardButton(
            f"{status} Join {group['name']}", 
            callback_data=f"join_{i}"
        )])
    
    keyboard.append([InlineKeyboardButton("✅ Verify Completion", callback_data="verify")])
    keyboard.append([InlineKeyboardButton("💰 Daily Bonus", callback_data="daily")])
    keyboard.append([InlineKeyboardButton("👥 Referral System", callback_data="referral")])
    keyboard.append([InlineKeyboardButton("💳 Withdraw", callback_data="withdraw")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    data = query.data
    
    if data.startswith("join_"):
        group_index = int(data.split("_")[1])
        if group_index < len(GROUP_LINKS):
            group = GROUP_LINKS[group_index]
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔗 Join Now", url=group['link']),
                InlineKeyboardButton("✅ I've Joined", callback_data=f"joined_{group_index}")
            ]])
            await query.edit_message_text(
                f"Please join: *{group['name']}*\n\nAfter joining, click 'I've Joined' button.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    
    elif data.startswith("joined_"):
        group_index = int(data.split("_")[1])
        if group_index not in user['verified_groups']:
            user['verified_groups'].append(group_index)
            save_user_data()
            
            all_joined = len(user['verified_groups']) == len(GROUP_LINKS)
            
            if all_joined and not user['verified']:
                user['verified'] = True
                save_user_data()
                await query.edit_message_text(
                    f"✅ *Verification Complete!*\n\n"
                    f"You have joined all required groups!\n\n"
                    f"💰 You can now claim daily bonus using /start menu.",
                    parse_mode="Markdown"
                )
            else:
                await start_command(update, context)
    
    elif data == "verify":
        all_joined = len(user['verified_groups']) == len(GROUP_LINKS)
        if all_joined:
            user['verified'] = True
            save_user_data()
            await query.edit_message_text(
                f"✅ *Verification Successful!*\n\n"
                f"You can now claim daily bonus and refer friends.",
                parse_mode="Markdown"
            )
        else:
            remaining = len(GROUP_LINKS) - len(user['verified_groups'])
            await query.edit_message_text(
                f"❌ *Verification Failed*\n\n"
                f"You need to join {remaining} more group(s).\n"
                f"Please join each group and click 'I've Joined'.",
                parse_mode="Markdown"
            )
    
    elif data == "daily":
        last_claim = user.get('last_daily')
        if last_claim:
            last_date = datetime.fromisoformat(last_claim)
            if datetime.now() - last_date < timedelta(days=1):
                hours_left = 24 - (datetime.now() - last_date).seconds // 3600
                await query.edit_message_text(
                    f"⏳ *Daily Bonus Already Claimed*\n\n"
                    f"Come back in {hours_left} hours!\n"
                    f"Your current balance: {user['balance']}₹",
                    parse_mode="Markdown"
                )
                return
        
        user['balance'] += DAILY_BONUS
        user['last_daily'] = datetime.now().isoformat()
        save_user_data()
        await query.edit_message_text(
            f"💰 *Daily Bonus Claimed!*\n\n"
            f"+{DAILY_BONUS}₹ added to your balance!\n"
            f"Current balance: {user['balance']}₹",
            parse_mode="Markdown"
        )
    
    elif data == "referral":
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        
        referral_keyboard = []
        for group in GROUP_LINKS:
            referral_keyboard.append([InlineKeyboardButton(
                f"📢 {group['name']}", 
                url=group['link']
            )])
        
        referral_keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
        
        await query.edit_message_text(
            f"👥 *Referral System*\n\n"
            f"Share these groups with friends:\n\n"
            f"🔗 Your Referral Link:\n`{referral_link}`\n\n"
            f"📊 *Stats:*\n"
            f"• Referrals: {user['referrals']}\n"
            f"• Earned from referrals: {user['referrals'] * REFERRAL_BONUS}₹\n\n"
            f"Share the groups below to get more referrals!",
            reply_markup=InlineKeyboardMarkup(referral_keyboard),
            parse_mode="Markdown"
        )
    
    elif data == "withdraw":
        if user['balance'] < MIN_WITHDRAWAL:
            await query.edit_message_text(
                f"❌ *Withdrawal Failed*\n\n"
                f"Minimum withdrawal amount: {MIN_WITHDRAWAL}₹\n"
                f"Your current balance: {user['balance']}₹\n\n"
                f"Earn more by:\n"
                f"• Daily bonus: {DAILY_BONUS}₹/day\n"
                f"• Referrals: {REFERRAL_BONUS}₹/referral",
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                OWNER_ID,
                f"💰 *Withdrawal Request*\n\n"
                f"User: @{query.from_user.username or query.from_user.first_name}\n"
                f"ID: `{user_id}`\n"
                f"Amount: {user['balance']}₹\n\n"
                f"Use /approve_{user_id} to approve",
                parse_mode="Markdown"
            )
            await query.edit_message_text(
                f"✅ *Withdrawal Request Sent!*\n\n"
                f"Amount: {user['balance']}₹\n"
                f"Admin will process your request soon.",
                parse_mode="Markdown"
            )
            user['balance_pending'] = user['balance']
            user['balance'] = 0
            save_user_data()
    
    elif data == "back_main":
        await start_command(update, context)

async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /approve <user_id>")
        return
    
    user_id = context.args[0]
    user = get_user(user_id)
    
    if user.get('balance_pending'):
        amount = user['balance_pending']
        await update.message.reply_text(
            f"✅ Approved withdrawal of {amount}₹ for user {user_id}\n\n"
            f"Send payment to user manually."
        )
        user['balance_pending'] = 0
        del user['balance_pending']
        save_user_data()
        
        try:
            await context.bot.send_message(
                int(user_id),
                f"✅ *Withdrawal Approved!*\n\n"
                f"Amount: {amount}₹\n"
                f"Admin will process your payment soon.",
                parse_mode="Markdown"
            )
        except:
            pass
    else:
        await update.message.reply_text("No pending withdrawal for this user.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return
    
    total_users = len(user_data)
    total_verified = sum(1 for u in user_data.values() if u.get('verified', False))
    total_balance = sum(u.get('balance', 0) for u in user_data.values())
    total_referrals = sum(u.get('referrals', 0) for u in user_data.values())
    
    await update.message.reply_text(
        f"📊 *Bot Statistics*\n\n"
        f"👥 Total Users: {total_users}\n"
        f"✅ Verified Users: {total_verified}\n"
        f"💰 Total Balance: {total_balance}₹\n"
        f"👤 Total Referrals: {total_referrals}\n\n"
        f"📢 Groups Configured: {len(GROUP_LINKS)}",
        parse_mode="Markdown"
    )

def main():
    load_user_data()
    
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print(f"✅ Bot started! Owner ID: {OWNER_ID}")
    print(f"📊 Groups configured: {len(GROUP_LINKS)}")
    
    app.run_polling()

if __name__ == "__main__":
    main()