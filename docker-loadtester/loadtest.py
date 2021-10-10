from datetime import datetime
import aiohttp
import asyncio

class LoadTester():

    CONTINUOUS_THREAD_REQUESTS = 1000
    PAUSING_THREAD_REQUESTS_BEFORE_PAUSE = 500
    PAUSING_THREAD_REQUESTS_AFTER_PAUSE = 1000
    PAUSE_TIME_SECONDS = 60

    def __init__(self, url, logger):
        self.url = url
        self.logger = logger

    def log(self, data):
        self.logger.log(data)

    async def send_request(self, session, url):
        async with session.get(url) as response:
            return response

    async def requestLoop(self, url, amount, thread_name):
        self.log(f'Sending requests in {thread_name}...')
        async with aiohttp.ClientSession() as session:
            for i in range(amount):
                try:
                    await self.send_request(session, url)
                except Exception as ex:
                    self.log(f'Exception: {ex}')
                if (i+1) % 100 == 0:
                    self.log(f"Request #{str(i + 1)} in {thread_name}")

    async def requestWithDelay(self, url, thread_name):
        await self.requestLoop(url, self.PAUSING_THREAD_REQUESTS_BEFORE_PAUSE, thread_name)
        self.log(f'Pausing {thread_name}')
        await asyncio.sleep(self.PAUSE_TIME_SECONDS)
        self.log(f'Resuming {thread_name}')
        await self.requestLoop(url, self.PAUSING_THREAD_REQUESTS_AFTER_PAUSE, thread_name)
        self.log(f'Finished {thread_name}')

    def benchmark(self):
        sequential = asyncio.ensure_future(self.requestLoop(self.url, self.CONTINUOUS_THREAD_REQUESTS, 'continuous thread'))
        withWait = asyncio.ensure_future(self.requestWithDelay(self.url, 'thread with pause'))
        asyncio.get_event_loop().run_until_complete(asyncio.gather(sequential, withWait))


class SimpleLogger():
    def __init__(self, file = None):
        if (file is not None):
            self.file = open(file, 'w+')
    
    def log(self, message):
        time = datetime.now().strftime("%H:%M:%S")
        contents = f'[{time}]: {message}'
        print(contents)
        if (self.file is not None):
            self.file.write(f'{contents}\n')


