from telegram.ext import CallbackContext
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import logging, re
from database import fetch_active_bots, fetch_current_token, update_token_address
from setup_function import start_setup
from token_function import get_token_symbol
from send_purchases import job_references

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def bot_command(update: Update, context: CallbackContext):
    global active_bots_mapping
    chat_type = update.effective_chat.type
    user_id = update.effective_chat.id

    if chat_type != "private":
        return

    active_bots = fetch_active_bots(user_id)
    if active_bots:
        bot_listing = "Select a bot to manage:\n"
        keyboard = []
        active_bots_mapping = {str(index): bot[2] for index, bot in enumerate(active_bots, start=1)}
        for index, bot in enumerate(active_bots, start=1):
            _, _, payment_uuid = bot
            bot_listing += f"{index}. {payment_uuid}\n"
            keyboard.append([InlineKeyboardButton(str(index), callback_data=f"bot_{index}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(bot_listing, reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            "You do not have any active bots.\n\nPlease purchase a bot to use this command.\n\nUse the \"/start\" command to get started!")

async def handle_bot_selection(update: Update, context: CallbackContext):
    global active_bots_mapping
    query = update.callback_query
    await query.answer()

    try:
        selected_number = query.data.replace('bot_', '')
        payment_uuid = active_bots_mapping.get(selected_number)

        if payment_uuid:
            context.user_data['payment_uuid'] = payment_uuid
            keyboard = [
                [InlineKeyboardButton("Setup", callback_data="setup")],
                [InlineKeyboardButton("Edit Token", callback_data="edit_token"),
                 InlineKeyboardButton("Edit Image", callback_data="edit_image")],
                [InlineKeyboardButton("Edit TG Group", callback_data="edit_group"),
                 InlineKeyboardButton("Edit Emoji", callback_data="edit_emoji")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"You chose the bot:\n{payment_uuid}.\n\nSelect an option to manage your bot:",
                reply_markup=reply_markup
            )
            logger.info("Bot management options sent for bot: %s", payment_uuid)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Invalid selection or bot not found."
            )
            logger.error("Invalid selection or bot not found.")

    except Exception as e:
        logger.exception("Error in handle_bot_selection: %s", str(e))
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="An error occurred while processing your request."
        )

async def handle_setup(update: Update, context: CallbackContext):
    logger.info("handle_setup called")
    query = update.callback_query
    await query.answer()

    message_text = query.message.text
    logger.info(f"Message Text: {message_text}")

    try:
        match = re.search(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', message_text)
        if match:
            payment_uuid = match.group(0)
            context.user_data['payment_uuid'] = payment_uuid
            context.user_data.pop('last_processed_text', None)
            await start_setup(query, context)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid UUID format.")
    except Exception as e:
        logger.error(f"Error in handle_setup: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="An error occurred while processing your request.")

async def handle_edit_token(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    payment_uuid = context.user_data.get('payment_uuid')
    if not payment_uuid:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Bot UUID not found.")
        return

    current_token_address, current_token_name = fetch_current_token(payment_uuid)
    context.user_data['current_token_name'] = current_token_name
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"Current Token:\n${current_token_name}\n{current_token_address}\n\nDo you want to change the token?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Yes, edit token", callback_data="edit_token_yes")],
            [InlineKeyboardButton("No", callback_data="edit_token_no")]
        ])
    )

async def handle_edit_token_yes(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please respond with the new token address"
    )
    context.user_data['editing_token'] = True

async def handle_edit_token_no(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="No changes made to the token address."
    )

async def handle_new_token_address(update: Update, context: CallbackContext):
    if context.user_data.get('editing_token'):
        new_token_address = update.message.text
        token_name = get_token_symbol(update.message.text)
        payment_uuid = context.user_data.get('payment_uuid')
        chat_id = update.effective_chat.id

        update_token_address(payment_uuid, new_token_address, token_name)
        await update.message.reply_text("Token address updated successfully.")

        if chat_id in job_references:
            job = job_references[chat_id]
            job.job.data['contract_address'] = new_token_address
            job.job.data['token_name'] = token_name

        context.user_data.pop('editing_token', None)

async def handle_edit_image(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Edit Image button pressed.")

async def handle_edit_group(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Edit TG Group button pressed.")

async def handle_edit_emoji(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Edit Emoji button pressed.")