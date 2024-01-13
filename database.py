import mysql.connector, time, logging
from mysql.connector import Error
from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

#Put your SQL database info here
def execute_db_query(query, params=None, is_fetch=False):
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host="",
            port=,
            user="",
            password="",
            database="",
            charset=''
        )
        cursor = connection.cursor()
        cursor.execute(query, params)

        if is_fetch:
            return cursor.fetchall()
        else:
            connection.commit()

    except Error as e:
        print(f"Error: {e}")
        time.sleep(5)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def store_data(user_id, chat_id, contract_address, token_name, image_url, chosen_emoji):
    query = """
    INSERT INTO telegram_bot_data (user_id, chat_id, contract_address, token_name, image_url, chosen_emoji) 
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    execute_db_query(query, (user_id, chat_id, contract_address, token_name, image_url, chosen_emoji))

def fetch_existing_data():
    query = "SELECT chat_id, contract_address, token_name FROM telegram_bot_data"
    return execute_db_query(query, is_fetch=True)

def filter_new_transactions(chat_id, transaction_hashes):
    format_strings = ','.join(['%s'] * len(transaction_hashes))
    query = f"SELECT transaction_hash FROM processed_transactions WHERE chat_id = %s AND transaction_hash IN ({format_strings})"
    params = [chat_id, *transaction_hashes]
    result = execute_db_query(query, params, is_fetch=True)
    existing_hashes = {row[0] for row in result}
    new_hashes = set(transaction_hashes) - existing_hashes
    return list(new_hashes)

def store_transaction(chat_id, transaction_hash):
    insert_query = "INSERT INTO processed_transactions (chat_id, transaction_hash) VALUES (%s, %s)"
    execute_db_query(insert_query, (chat_id, transaction_hash))

    delete_query = """
    DELETE FROM processed_transactions
    WHERE chat_id = %s AND transaction_hash NOT IN (
        SELECT transaction_hash
        FROM (
            SELECT transaction_hash
            FROM processed_transactions
            WHERE chat_id = %s
            ORDER BY transaction_hash DESC
            LIMIT 100
        ) AS subquery
    )
    """
    execute_db_query(delete_query, (chat_id, chat_id))

def fetch_image_url(chat_id):
    query = "SELECT image_url FROM telegram_bot_data WHERE chat_id = %s"
    result = execute_db_query(query, (chat_id,), is_fetch=True)
    if result:
        return result[0][0]
    return None

def fetch_chosen_emoji(chat_id):
    query = "SELECT chosen_emoji FROM telegram_bot_data WHERE chat_id = %s"
    result = execute_db_query(query, (chat_id,), is_fetch=True)
    if result:
        return result[0][0]
    return '🟢'

def store_user_wallet(user_id, wallet_address):
    default_contract_address = ""
    default_token_name = ""
    default_image_url = ""
    default_chosen_emoji = ""
    chat_id = "1"

    query = """
    INSERT INTO telegram_bot_data 
    (chat_id, user_id, wallet_address, contract_address, token_name, image_url, chosen_emoji) 
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (chat_id, user_id, wallet_address, default_contract_address, default_token_name, default_image_url, default_chosen_emoji)
    execute_db_query(query, params)

def fetch_user_wallet(user_id):
    query = "SELECT wallet_address FROM telegram_bot_data WHERE user_id = %s"
    result = execute_db_query(query, (user_id,), is_fetch=True)
    if result:
        return result[0][0]
    else:
        return None
    
def transaction_exists(signature):
    query = "SELECT COUNT(1) FROM telegram_bot_data WHERE payment_transaction = %s"
    result = execute_db_query(query, (signature,), is_fetch=True)
    return result[0][0] > 0

def update_payment_details(user_wallet, signature, payment_date, cancel_date):
    query = """
    UPDATE telegram_bot_data 
    SET payment_transaction = %s, payment_date = %s, cancel_date = %s
    WHERE wallet_address = %s
    """
    execute_db_query(query, (signature, payment_date, cancel_date, user_wallet))

def fetch_active_bots(user_id):
    try:
        current_time = datetime.utcnow()
        query = """
        SELECT contract_address, token_name, payment_uuid 
        FROM telegram_bot_data 
        WHERE user_id = %s AND cancel_date > %s
        """
        params = (user_id, current_time)
        result = execute_db_query(query, params, is_fetch=True)
        return result if result else []
    except Exception as e:
        logger.error(f"Error in fetch_active_bots: {e}")
        return []

def store_payment_uuid(user_id, payment_uuid):
    query = """
    UPDATE telegram_bot_data 
    SET payment_uuid = %s
    WHERE user_id = %s
    """
    execute_db_query(query, (payment_uuid, user_id))

def transaction_exists(payment_uuid):
    query = "SELECT COUNT(1) FROM telegram_bot_data WHERE payment_uuid = %s"
    result = execute_db_query(query, (payment_uuid,), is_fetch=True)
    return result[0][0] > 0

def update_chat_id_for_uuid(chat_id, payment_uuid):
    query = """
    UPDATE telegram_bot_data 
    SET chat_id = %s
    WHERE payment_uuid = %s
    """
    execute_db_query(query, (chat_id, payment_uuid))

def update_setup_data(payment_uuid, chat_id, contract_address, token_name, image_url, chosen_emoji):
    logger.info("update_setup_data called")
    query = """
    UPDATE telegram_bot_data 
    SET chat_id = %s, contract_address = %s, token_name = %s, image_url = %s, chosen_emoji = %s
    WHERE payment_uuid = %s
    """
    params = (chat_id, contract_address, token_name, image_url, chosen_emoji, payment_uuid)
    print("update_setup_data Query data:", params)
    try:
        execute_db_query(query, params)
    except Error as e:
        logger.error(f"Error in update_setup_data: {e}")
        raise

def fetch_current_token(payment_uuid):
    query = "SELECT contract_address, token_name FROM telegram_bot_data WHERE payment_uuid = %s"
    result = execute_db_query(query, (payment_uuid,), is_fetch=True)
    if result:
        return result[0][0], result[0][1]
    else:
        return None, None

def update_token_address(payment_uuid, new_token_address, token_name):
    query = "UPDATE telegram_bot_data SET contract_address = %s, token_name = %s WHERE payment_uuid = %s"
    execute_db_query(query, (new_token_address, token_name, payment_uuid))