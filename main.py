import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ==========================
# CONFIGURATION
# ==========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Add in Render environment
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME")  # Add in Render environment
ADMIN_IDS = [1044308364, 5895839913]  # Admin Telegram IDs

# ==========================
# LOGGING
# ==========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================
# DATABASE
# ==========================
DB_FILE = "ventbot.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute("""
CREATE TABLE IF NOT EXISTS vents (
    vent_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT,
    identity TEXT,
    allow_comments INTEGER,
    tags TEXT,
    approved INTEGER DEFAULT 0
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS comments (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vent_id INTEGER,
    user_id INTEGER,
    text TEXT,
    identity TEXT
)
""")
conn.commit()

# ==========================
# HELPERS
# ==========================
def vent_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Show my identity", callback_data="show_identity"),
             InlineKeyboardButton("Hide my identity", callback_data="hide_identity")],
            [InlineKeyboardButton("Cancel", callback_data="cancel_vent")]
        ]
    )

def comment_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Show my identity", callback_data="show_identity_comment"),
             InlineKeyboardButton("Hide my identity", callback_data="hide_identity_comment")],
            [InlineKeyboardButton("Finish", callback_data="finish_comment"),
             InlineKeyboardButton("Cancel", callback_data="cancel_comment")]
        ]
    )

# ==========================
# COMMAND HANDLERS
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Start Vent", callback_data="start_vent")],
            [InlineKeyboardButton("My Profile", callback_data="my_profile")],
            [InlineKeyboardButton("Feedback", callback_data="feedback")],
            [InlineKeyboardButton("Help", callback_data="help")],
            [InlineKeyboardButton("About Us", callback_data="about_us")]
        ]
    )
    await update.message.reply_text("Welcome to the Vent Bot! Choose an option:", reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Step-by-step guide:\n"
        "1. Click 'Start Vent' to send a vent.\n"
        "2. Choose whether to show your identity.\n"
        "3. Select if comments are allowed.\n"
        "4. Add tags and send your vent.\n"
        "5. Browse/add comments anonymously.\n"
        "Admin moderation handles approvals."
    )
    await update.message.reply_text(help_text)

# ==========================
# MESSAGE HANDLER
# ==========================
async def handle_vent_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    # Save vent as pending approval
    c.execute("INSERT INTO vents (user_id, text, identity, allow_comments, tags, approved) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, text, "hidden", 1, "", 0))
    conn.commit()
    await update.message.reply_text("Your vent has been sent for moderation 🔥")

# ==========================
# CALLBACK HANDLER
# ==========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "start_vent":
        await query.message.reply_text("Please send your vent text (text + emojis allowed):")
    elif data == "my_profile":
        # Count vents/comments
        c.execute("SELECT COUNT(*) FROM vents WHERE user_id=?", (user_id,))
        vents_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM comments WHERE user_id=?", (user_id,))
        comments_count = c.fetchone()[0]
        await query.message.reply_text(
            f"Your Profile:\nVents: {vents_count}\nComments: {comments_count}\nImpact Points: 0 🎖\nCommunity Acceptance: 0.0"
        )
    elif data == "feedback":
        await query.message.reply_text("Send your feedback now:")
    elif data == "help":
        await help_command(update, context)
    elif data == "about_us":
        about_text = "This bot allows users to vent safely and anonymously. Moderation ensures safety."
        await query.message.reply_text(about_text)
    elif data == "cancel_vent":
        await query.message.reply_text("Vent cancelled ✅")
    elif data == "cancel_comment":
        await query.message.reply_text("Comment cancelled ✅")
    elif data == "show_identity":
        await query.message.reply_text("You chose to show your identity for this vent.")
    elif data == "hide_identity":
        await query.message.reply_text("You chose to hide your identity for this vent.")
    elif data == "show_identity_comment":
        await query.message.reply_text("You chose to show your identity for this comment.")
    elif data == "hide_identity_comment":
        await query.message.reply_text("You chose to hide your identity for this comment.")
    elif data == "finish_comment":
        await query.message.reply_text("Comment added to vent ✅")
    else:
        await query.message.reply_text(f"Button clicked: {data}")

# ==========================
# MAIN APPLICATION
# ==========================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vent_message))

    # Callback query handler
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running…")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
