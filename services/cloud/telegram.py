import logging

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

import asyncio
import json
import os
import threading
import time
from difflib import get_close_matches

from telethon import TelegramClient, events, functions


class TelegramService:
    def __init__(self, msg_callback):

        with open(os.environ.get('TELEGRAM_CREDENTIALS'), 'r') as f:
            tg_credentials = json.load(f)

        self.msg_callback = msg_callback
        self._contacts = {}

        self.thread = threading.Thread(target=self._thread, args=(tg_credentials['api_id'], tg_credentials['api_hash']))
        self.thread.start()

    async def event_handler(self, event):
        u = await event.get_sender()
        self.msg_callback(u.first_name + ((' ' + u.last_name) if u.last_name else ''), event.raw_text)

    def _thread(self, api_id, api_hash):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = TelegramClient(os.environ.get('TELEGRAM_SESSION'), api_id, api_hash, loop=self.loop)

        with self.client:
            self.client.add_event_handler(self.event_handler, events.NewMessage(incoming=True, func=lambda e: e.is_private))
            self._contacts = {u.first_name.lower() + ((' ' + u.last_name.lower()) if u.last_name else ''): u.id for u in self.loop.run_until_complete(self.client(functions.contacts.GetContactsRequest(hash=0))).users}
            self.client.run_until_disconnected()
        self.loop.close()

    @property
    def contacts(self):
        return self._contacts
    
    def send_message(self, name, message):
        '''
        Send a message to a Telegram Entity.

        Warning: This method can only be called from a thread different than the one running the asyncio event loop
        '''
        contact_name = get_close_matches(word=name.lower(), possibilities=self._contacts.keys(), n=1)[0]
        print(contact_name)
        user_id = self._contacts[contact_name]

        return asyncio.run_coroutine_threadsafe(self.client.send_message(user_id, message), self.loop).result()

    def stop(self):
        '''
        Stop the service
        
        Warning: This method can only be called from a thread different than the one running the asyncio event loop
        '''
        disconnect_coro = self.client.disconnect()
        if disconnect_coro is not None:
            asyncio.run_coroutine_threadsafe(disconnect_coro, self.loop).result()
        self.thread.join()

if __name__ == '__main__':
    
        
    try:
        tg = TelegramService(msg_callback=lambda  u,x: print(f"[{u}] ", x))
        
        while True:
            msg = input()
            #print(tg.contacts)
            print('[Sent]', tg.send_message('Alberto Mentorcito', msg))
    except KeyboardInterrupt:
        print('[Ctrl+C] Exiting...')
        tg.stop()
