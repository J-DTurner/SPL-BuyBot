from telegram import Update
from telegram.ext import CallbackContext

from dm_setup import wallet_address, handle_uuid_response
from setup_function import contract_address, image_url, chosen_emoji, start_setup
from bot_command import handle_new_token_address

STEP_CONTRACT, STEP_IMAGE_URL, STEP_EMOJI = range(3)

async def handle_user_response(update: Update, context: CallbackContext):
    if context.user_data.get('expecting_wallet_address'):
        await wallet_address(update, context)
        context.user_data.pop('expecting_wallet_address', None)
        return

    if context.user_data.get('awaiting_uuid'): 
        await handle_uuid_response(update, context)
        context.user_data.pop('awaiting_uuid', None)
        return
    
    if context.user_data.get('editing_token'):
        await handle_new_token_address(update, context)
        context.user_data.pop('editing_token', None)
        return
    
    setup_step = context.user_data.get('setup_step')

    if setup_step == STEP_CONTRACT:
        await contract_address(update, context)
    elif setup_step == STEP_IMAGE_URL:
        await image_url(update, context)
    elif setup_step == STEP_EMOJI:
        await chosen_emoji(update, context)
    else:
        await start_setup(update, context)