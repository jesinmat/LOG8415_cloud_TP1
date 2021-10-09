from datetime import datetime
import aiohttp
import asyncio

CONTINUOUS_THREAD_REQUESTS = 1000
PAUSING_THREAD_REQUESTS_BEFORE_PAUSE = 500
PAUSING_THREAD_REQUESTS_AFTER_PAUSE = 1000
PAUSE_TIME_SECONDS = 60

def log(message):
    time = datetime.now().strftime("%H:%M:%S")
    print(f'[{time}]: {message}')

async def send_request(session, url):
    async with session.get(url) as response:
        return response

async def requestLoop(url, amount, thread_name):
    log(f'Sending requests in {thread_name}...')
    async with aiohttp.ClientSession() as session:
        for i in range(amount):
            try:
                await send_request(session, url)
            except Exception as ex:
                log(f'Exception: {ex}')
            if (i+1) % 100 == 0:
                log(f"Request #{str(i + 1)} in {thread_name}")

async def requestLoopAsync(url, amount, thread_name):
    log(f'Sending requests in {thread_name}...')
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(amount):
            task = asyncio.ensure_future(send_request(session, url))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

async def requestWithDelay(url, thread_name):
    await requestLoopAsync(url, PAUSING_THREAD_REQUESTS_BEFORE_PAUSE, thread_name)
    log(f'Pausing {thread_name}')
    await asyncio.sleep(PAUSE_TIME_SECONDS)
    log(f'Resuming {thread_name}')
    await requestLoopAsync(url, PAUSING_THREAD_REQUESTS_AFTER_PAUSE, thread_name)
    log(f'Finished {thread_name}')

async def benchmark(url):
    sequential = asyncio.ensure_future(requestLoop(url, CONTINUOUS_THREAD_REQUESTS, 'continuous thread'))
    withWait = asyncio.ensure_future(requestWithDelay(url, 'thread with pause'))
    await asyncio.gather(sequential, withWait)

def main():
    import os
    url = os.getenv("AWS_URL")
    if url is not None:
        log("Starting benchmark for {}".format(url))
        asyncio.get_event_loop().run_until_complete(benchmark(url))
        log('Done')
    else:
        log("No AWS_URL env variable specified.")
    

main()
