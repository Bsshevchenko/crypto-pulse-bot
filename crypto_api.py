import aiohttp

async def get_all_coins_list():
    url = "https://api.coingecko.com/api/v3/coins/list"
    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        async with session.get(url) as response:
            coins = await response.json()
            return coins  # [{'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'}, ...]
