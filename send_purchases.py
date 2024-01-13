import aiohttp, urllib.parse, logging
from telegram.ext import CallbackContext

from database import filter_new_transactions, store_transaction, fetch_image_url, fetch_chosen_emoji, fetch_existing_data
from price import get_asset

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

job_references = {}

def initialize_jobs_from_db(application):
    existing_data = fetch_existing_data()
    for chat_id, contract_address, token_name in existing_data:
        job_context = {'chat_id': chat_id, 'contract_address': contract_address, 'token_name': token_name}
        job = application.job_queue.run_repeating(fetch_and_send_transactions, interval=60, first=0, data=job_context)
        job_references[chat_id] = job  # Store the job reference

def initialize_job_for_chat(application, chat_id, contract_address, token_name):
    job_context = {'chat_id': chat_id, 'contract_address': contract_address, 'token_name': token_name}
    job = application.job_queue.run_repeating(fetch_and_send_transactions, interval=60, first=0, data=job_context)
    job_references[chat_id] = job  # Store the job reference

async def fetch_and_send_transactions(context: CallbackContext):
    job_context = context.job.data
    chat_id = job_context['chat_id']
    token_address = job_context['contract_address']
    logger.info("Token name in job context: %s", job_context['token_name'])
    chosen_ticker = job_context['token_name']
    image_url = fetch_image_url(chat_id)
    chosen_emoji = fetch_chosen_emoji(chat_id)

    if not chat_id or not token_address or not chosen_ticker or not image_url or not chosen_emoji:
        logger.info("Missing one or more required data points, skipping operation.")
        return

    price_per_token = get_asset(token_address)

    url = f'https://api.helius.xyz/v0/addresses/{token_address}/transactions?api-key=PUT YOUR API KEY HERE'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    swap_transactions = [t for t in data if t['type'] == 'SWAP']
                    transaction_hashes = [t['signature'] for t in swap_transactions]

                    new_transaction_hashes = filter_new_transactions(chat_id, transaction_hashes)

                    for transaction in swap_transactions:
                        transaction_hash = transaction['signature']

                        if transaction_hash in new_transaction_hashes:
                            description_parts = transaction['description'].split(' ')

                            swapped_index = description_parts.index('swapped')
                            for_index = description_parts.index('for')

                            if swapped_index != -1 and for_index != -1:
                                first_ticker = description_parts[swapped_index + 2]
                                second_amount_raw = description_parts[for_index + 1].replace(',', '')
                                second_ticker = description_parts[for_index + 2]

                                if first_ticker != chosen_ticker and second_ticker == chosen_ticker:
                                    try:
                                        second_amount_float = float(second_amount_raw)
                                        total_amount_in_dollars = second_amount_float * price_per_token

                                        num_circles = max(1, int(total_amount_in_dollars // 10))
                                        circles = chosen_emoji * num_circles

                                        second_amount_formatted = f"${total_amount_in_dollars:,.2f}"
                                    except Exception as e:
                                        logger.error(f"Error in calculating total amount in dollars: {e}")
                                        second_amount_formatted = f"{second_amount_raw} (error in conversion)"

                                    share_text = f"${chosen_ticker} is PUMPING!\n\nIYKYK\nhttps://birdeye.so/token/{transaction_hash}?chain=solana"
                                    encoded_text = urllib.parse.quote_plus(share_text)
                                    twitter_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
                                    
                                    message = (
                                        f"{circles}\n"
                                        f"{second_amount_formatted} of ${chosen_ticker} purchased.\n\n"
                                        f"📈: <a href='https://birdeye.so/token/{transaction_hash}?chain=solana'>Birdeye</a>\n"
                                        f"🖨: <a href='https://solscan.io/tx/{transaction_hash}'>Transaction</a>\n"
                                        f"🐦: <a href='{twitter_url}'>Share Tweet</a>"
                                    )

                                    if image_url:
                                        if image_url.lower().endswith('.gif'):
                                            await context.bot.send_animation(chat_id=chat_id, animation=image_url, caption=message, parse_mode='HTML')
                                        elif image_url.lower().endswith(('.jpg', '.jpeg', '.png')):
                                            await context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=message, parse_mode='HTML')
                                        else:
                                            logger.info("Image URL does not have a recognized extension, sending message without image.")
                                            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
                                    else:
                                        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

                                    store_transaction(chat_id, transaction_hash)

                else:
                    logger.error(f"fetch_and_send_transactions: Failed to fetch data. Status code: {response.status}")
    except Exception as e:
        logger.error(f"fetch_and_send_transactions: An error occurred: {e}")

    logger.info("fetch_and_send_transactions executed")
