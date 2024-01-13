from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          CallbackQueryHandler, filters, CommandHandler)

import logging

from utility_functions import handle_user_response
from dm_setup import (start_command, handle_enter_new_wallet, handle_payment_sent, handle_use_existing_wallet, handle_yes_response, setup_buybot_command)

from bot_command import (bot_command, handle_bot_selection, handle_setup, handle_edit_token, 
                         handle_edit_image, handle_edit_group, handle_edit_emoji, handle_edit_token_no, handle_edit_token_yes)

from send_purchases import initialize_jobs_from_db

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Put your Telegram Bot Token here
TOKEN = ''
CONTRACT, IMAGE_URL, EMOJI, WALLET_ADDRESS = range(4)

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('bot', bot_command))
    application.add_handler(CommandHandler('setup_buybot', setup_buybot_command))

    application.add_handler(CallbackQueryHandler(handle_yes_response, pattern='^yes$'))
    application.add_handler(CallbackQueryHandler(handle_use_existing_wallet, pattern='^use_existing$'))
    application.add_handler(CallbackQueryHandler(handle_enter_new_wallet, pattern='^enter_new$'))
    application.add_handler(CallbackQueryHandler(handle_payment_sent, pattern='^payment_sent$'))
    application.add_handler(CallbackQueryHandler(handle_bot_selection, pattern='^bot_\\d+$'))

    application.add_handler(CallbackQueryHandler(handle_setup, pattern='^setup$'))
    application.add_handler(CallbackQueryHandler(handle_edit_token, pattern='^edit_token$'))
    application.add_handler(CallbackQueryHandler(handle_edit_image, pattern='^edit_image$'))
    application.add_handler(CallbackQueryHandler(handle_edit_group, pattern='^edit_group$'))
    application.add_handler(CallbackQueryHandler(handle_edit_emoji, pattern='^edit_emoji$'))

    application.add_handler(CallbackQueryHandler(handle_edit_token_no, pattern='^edit_token_no$'))
    application.add_handler(CallbackQueryHandler(handle_edit_token_yes, pattern='^edit_token_yes$'))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_response))

    initialize_jobs_from_db(application)

    application.run_polling()

if __name__ == '__main__':
    main()
