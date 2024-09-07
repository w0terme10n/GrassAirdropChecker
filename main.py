from config import REQUESTS_AT_ONCE
from tqdm import tqdm
import aiohttp
import asyncio
import random


def split_list_by_length(lst: list, length: int):
    result = []
    arr = []
    for i in range(len(lst)):
        arr.append(lst[i])
        if len(arr) == length:
            result.append(arr)
            arr = []
    if len(arr) > 0:
        result.append(arr)
    return result


async def fetch_earnings(session: aiohttp.ClientSession, wallet: str, proxy: str) -> dict:
    url = f'https://api.getgrass.io/airdropAllocations?input=%7B%22walletAddress%22:%22{wallet}%22%7D'
    points = 0
    try:
        async with session.get(url, verify_ssl=False, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                if 'result' in data and 'data' in data['result']:
                    for epoch in data['result']['data']:
                        points += data['result']['data'][epoch]
                    points = round(points, 2)
    except Exception as e:
        print(f'error while request at wallet {wallet} with {proxy}\n{e}')
        points = 'undefined'
    return {'wallet': wallet, 'points': points}


async def process_requests(wallets: list[str], proxies: list[str]) -> list[dict]:
    splitted_wallets = split_list_by_length(wallets, REQUESTS_AT_ONCE)
    result = []
    for i in tqdm(range(len(splitted_wallets))):
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False, use_dns_cache=False)) as session:
                tasks = [fetch_earnings(session, wallet, random.choice(proxies)) for wallet in splitted_wallets[i]]
                result += await asyncio.gather(*tasks)
        except Exception as e:
            print(f'Error while {i+1} request\n{e}')
        await asyncio.sleep(0.2)
    return result


def main():
    with open('wallets.txt') as f:
        wallets = [i.strip() for i in f.readlines() if i.strip()]

    with open('proxies.txt') as f:
        proxies = [i.strip() for i in f.readlines() if i.strip()]
    
    result = asyncio.run(process_requests(wallets, proxies))
    total = 0
    with open('results.txt', 'w') as f:
        for row in result:
            if isinstance(row['points'], float) or isinstance(row['points'], int):
                total += row["points"]
            f.write(f'{row["wallet"]} - {row["points"]} tokens\n')
        f.write(f'total: {total} tokens\n')


if __name__ == '__main__':
    main()