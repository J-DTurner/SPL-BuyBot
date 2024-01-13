import requests, json

def get_token_symbol(token_address):
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
    result = response.json().get('result', {})
    token_symbol = result.get('token_info', {}).get('symbol', '')

    return token_symbol
