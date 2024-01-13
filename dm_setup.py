from telegram.ext import CallbackContext
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import logging, uuid

from send_purchases import initialize_job_for_chat

from database import store_user_wallet, fetch_user_wallet, store_payment_uuid, execute_db_query
from parse_wallet import parse_wallet

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: CallbackContext):
    chat_type = update.effective_chat.type
    #Put your bot image here!
    image_url = ""

    if chat_type == "private":
        caption = (
            "Welcome to the premiere Solana BuyBot for Telegram groups!\n\n"
            "Features:\n"
            "- Select an SPL token to track.\n"
            "- Customize emojis for buybot messages.\n"
            "- Customize the image in messages.\n"
            "- Customize the text your users will tweet when they click the 'share tweet' button.\n"
            "- Manage multiple buy bots with memberships.\n\n"
            "Membership: $50 for 30 days (one token, one group).\n\n"
            "Only the purchaser can manage the buybot.\n\n"
            "Would you like to sign up to use the buybot?"
        )

        keyboard = [
            [InlineKeyboardButton("Yes", callback_data='yes'), 
             InlineKeyboardButton("No", callback_data='no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_photo(photo=image_url, caption=caption, reply_markup=reply_markup)
    else:
        await update.message.reply_text("Please use the /start command in a DM.")

async def wallet_address(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    wallet = update.message.text

    store_user_wallet(user_id, wallet)

    await update.message.reply_text(
        f"Please send $50 USDC to the following address:\n"
        "UifrcG2hjT2p4F2e96dLUrxdmKP8VedwfVb1zNpUnuo\n"
        "Click the button once you've sent the payment.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Sent the Payment", callback_data='payment_sent')]
        ])
    )

async def handle_use_existing_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_wallet = fetch_user_wallet(user_id)

    await query.message.reply_text(
        f"You are using your existing wallet: {user_wallet}\n"
        "Please send $50 USDC to the following address:\n"
        "UifrcG2hjT2p4F2e96dLUrxdmKP8VedwfVb1zNpUnuo",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Sent the Payment", callback_data='payment_sent')]
        ])
    )

async def handle_enter_new_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("Please provide the new wallet address you will be sending the $50 USDC payment from.")
    context.user_data['telegram_id'] = query.from_user.id

async def handle_yes_response(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    existing_wallet = fetch_user_wallet(user_id)
    if existing_wallet:
        message = (
            f"You have previously used the wallet address: {existing_wallet}\n"
            "Would you like to use this wallet again?"
        )
        keyboard = [
            [InlineKeyboardButton("Use Existing Wallet", callback_data='use_existing')],
            [InlineKeyboardButton("Enter New Wallet", callback_data='enter_new')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await query.message.reply_text("Please provide the wallet address you will be sending the $50 USDC payment from.")
        context.user_data['telegram_id'] = user_id
        context.user_data['expecting_wallet_address'] = True 

async def handle_wallet_address(update: Update, context: CallbackContext):
    wallet_address = update.message.text
    user_id = context.user_data['telegram_id']

    store_user_wallet(user_id, wallet_address)

    await update.message.reply_text(
        f"Please send $50 USDC to the following address:\n"
        "UifrcG2hjT2p4F2e96dLUrxdmKP8VedwfVb1zNpUnuo\n"
        "Click the button once you've sent the payment.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Sent the Payment", callback_data='payment_sent')]
        ])
    )

async def handle_payment_sent(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_wallet = fetch_user_wallet(user_id)

    payment_received = parse_wallet("UifrcG2hjT2p4F2e96dLUrxdmKP8VedwfVb1zNpUnuo", user_wallet)
    if payment_received:
        payment_uuid = str(uuid.uuid4())
        store_payment_uuid(user_id, payment_uuid)

        await query.message.reply_text(f"Payment received. Thank you!\n\nYour Payment UUID is: {payment_uuid}\n\nPlease use \"/bot\" command to start setting up your BuyBot!")
    else:
        await query.message.reply_text("Payment not received yet. Please check again later.")

async def setup_buybot_command(update: Update, context: CallbackContext):
    chat_type = update.effective_chat.type
    if chat_type in ["group", "supergroup", "channel"]:
        context.user_data['awaiting_uuid'] = True
        await update.message.reply_text("Please reply with the UUID for the bot you want to set up.\n\nThat means, please click\"reply\" on the top right of this message, and then paste your UUID into the response.")
    else:
        await update.message.reply_text("This command can only be used in groups or channels.")

async def handle_uuid_response(update: Update, context: CallbackContext):
    if context.user_data.get('awaiting_uuid'):
        uuid = update.message.text
        chat_id = update.effective_chat.id

        query = "SELECT chat_id, contract_address, token_name FROM telegram_bot_data WHERE payment_uuid = %s"
        result = execute_db_query(query, (uuid,), is_fetch=True)

        if result:
            retrieved_chat_id, contract_address, token_name = result[0]
            logger.info(f"Retrieved data from database: chat_id={retrieved_chat_id}, contract_address={contract_address}, token_name={token_name}")
        else:
            logger.info("No result found for the given UUID.")

        if not result:
            await update.message.reply_text("There's no UUID that matches that.")
        elif result and str(retrieved_chat_id) == str(1):
            update_query = "UPDATE telegram_bot_data SET chat_id = %s WHERE payment_uuid = %s"
            execute_db_query(update_query, (chat_id, uuid))
            await update.message.reply_text("Setup has been completed.\n\nThe Solana BuyBot should start momentarily.\n\nImportant note:\nAt the beginning of the process, the bot will be cataloging past purchases - so there will be many purchases coming through that might not be current. After that process it will keep all purchases up-to-date within 1-2 minutes of purchase.")
            
            initialize_job_for_chat(context.application, chat_id, contract_address, token_name)

        else:
            await update.message.reply_text("There's already an assigned chat for the bot, please go reset the chat using the /bot command in a DM to access bot management.")
        
        context.user_data.pop('awaiting_uuid', None)