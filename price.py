import requests, json

def get_asset(token_address):
    url = "https://mainnet.helius-rpc.com/?api-key=PUT YOUR API KEY HERE"
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "jsonrpc": "2.0",
        "id": "my-id",
        "method": "getAsset",
        "params": {
            "id": token_address,
            "displayOptions": {
                "showFungible": True
            }
        },
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    result = response.json()['result']
    price_per_token = result['token_info']['price_info']['price_per_token']
    
    return float(price_per_token)