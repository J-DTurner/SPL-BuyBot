from telegram import Update, ForceReply
from telegram.ext import CallbackContext
import logging

from database import update_setup_data
from token_function import get_token_symbol

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

STEP_CONTRACT, STEP_IMAGE_URL, STEP_EMOJI = range(3)

async def store_partial_data_and_proceed(update, context, next_step_func):
    logger.info("store_partial_data_and_proceed called")
    chat_id = 1
    payment_uuid = context.user_data.get('payment_uuid')
    logger.info(f"UUID in store_partial_data_and_proceed: {payment_uuid}")
    contract_address = context.user_data.get('contract', '')
    token_name = context.user_data.get('token_name', '')
    image_url = context.user_data.get('image_url', '')
    chosen_emoji = context.user_data.get('chosen_emoji', '')

    try:
        update_setup_data(payment_uuid, chat_id, contract_address, token_name, image_url, chosen_emoji)
        await next_step_func(update, context)
    except Exception as e:
        logger.error(f"Error in store_partial_data_and_proceed: {e}")

async def start_setup(query: Update, context: CallbackContext):
    context.user_data['setup_step'] = STEP_CONTRACT
    logger.info("start_setup called")
    await query.message.reply_text(
        "Please send me the contract address you want the Solana BuyBot to track.",
        reply_markup=ForceReply(selective=True),
    )

async def contract_address(update: Update, context: CallbackContext):
    logger.info("contract_address called")
    if 'last_processed_text' not in context.user_data or update.message.text != context.user_data['last_processed_text']:
        logger.info("contract_address found context data")
        context.user_data['last_processed_text'] = update.message.text
        context.user_data['contract'] = update.message.text
        context.user_data['token_name'] = get_token_symbol(update.message.text)
        context.user_data['setup_step'] = STEP_IMAGE_URL
        await store_partial_data_and_proceed(update, context, image_url)
    else:
        await update.message.reply_text("Please send the contract address.")

async def image_url(update: Update, context: CallbackContext):
    logger.info("image_url called")
    if update.message.text != context.user_data.get('last_processed_text'):
        logger.info("image_url found context data")
        context.user_data['last_processed_text'] = update.message.text
        context.user_data['setup_step'] = STEP_EMOJI
        context.user_data['image_url'] = update.message.text
        await store_partial_data_and_proceed(update, context, chosen_emoji)
    else:
        await update.message.reply_text("Now please respond with a URL to a JPG, PNG, or GIF.\n\nThis needs to be a DIRECT link to the image, or it will not work.")

async def chosen_emoji(update: Update, context: CallbackContext):
    logger.info("chosen_emoji called")
    if update.message.text != context.user_data.get('last_processed_text'):
        logger.info("chosen_emoji found context data")
        context.user_data['last_processed_text'] = update.message.text
        context.user_data['chosen_emoji'] = update.message.text
        await store_partial_data_and_proceed(update, context, finalize_setup)
    else:
        await update.message.reply_text("Please send the emoji you want to use for indicating purchase amounts.")

async def finalize_setup(update: Update, context: CallbackContext):
    logger.info("finalize_setup called")
    payment_uuid = context.user_data.get('payment_uuid', '')
    instruction_message = (
        f"Setup complete! Your UUID is: {payment_uuid}\n\n"
        "Please add the bot to your group or channel.\n"
        "Then, use the '/setup_buybot' command in the group or channel.\n"
        "When prompted, reply with this UUID.\n"
    )
    await update.message.reply_text(instruction_message)
