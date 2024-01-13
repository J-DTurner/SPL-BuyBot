import requests, datetime
from database import transaction_exists, update_payment_details

def parse_wallet(wallet_address, sender_wallet):
    #Put your Helius API key here
    api_key = ""
    url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/transactions?api-key={api_key}"

    response = requests.get(url)
    data = response.json()

    for transaction in data:
        if transaction['type'] == 'TRANSFER' and \
           transaction['feePayer'] == sender_wallet and \
           any(tt['tokenAmount'] >= 50 and tt['mint'] == 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' for tt in transaction['tokenTransfers']):
            signature = transaction['signature']
            if not transaction_exists(signature):
                current_time = datetime.datetime.utcnow()
                cancel_time = current_time + datetime.timedelta(days=30)
                update_payment_details(sender_wallet, signature, current_time, cancel_time)
                return True
    return False
