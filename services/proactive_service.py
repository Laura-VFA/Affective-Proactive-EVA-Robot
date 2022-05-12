import json
import random
from datetime import datetime, timedelta


class ProactivePhrases:
    phrases_file = None
    phrases = None

    @staticmethod
    def load(encodings_file='files/proactive_phrases.json'):
        ProactivePhrases.encodings_file = encodings_file

        with open(encodings_file) as json_file:
            ProactivePhrases.phrases = json.load(json_file)
    
    @staticmethod
    def get(phrase_key):
        return random.choice(ProactivePhrases.phrases[phrase_key])


class ProactiveService:
    def __init__(self, callback) -> None:
        self.question = None
        self.callback = callback

        # Put an alarm every day at 8 am to ask for user mood
        self.next_question_time = (datetime.now() + timedelta(days=1)).replace(hour=8,minute=0)
        # print('TIMER SETT') TODO logging
        # [TEST] self.next_question_time = datetime.now() + timedelta(minutes=1)

        self.tg_messages = {} # Telegram pending incoming messages

    
    def update(self, type, subtype, args={}):
        if type == 'sensor':
            if subtype == 'presence':
                # Timeout, ask 'How are you?'
                if (self.next_question_time - datetime.now()).total_seconds() <= 0: 
                    self.callback('ask_how_are_you')
                
                if self.tg_messages: # Read telegram messages
                    self.callback('read_pending_messages', self.tg_messages)

            elif subtype == 'unknown_face': # Ask new user's name
                self.callback('ask_who_are_you')
            
            elif subtype == 'received_tg_message': # Save telegram messages for later
                prev_messages = self.tg_messages.get(args['name'], [])
                prev_messages.append(args['message'])
                self.tg_messages[args['name']] = prev_messages
            
        elif type == 'abort':
            if subtype == 'how_are_you':
                # Postpone the timer 2 hours
                self.next_question_time = datetime.now() + timedelta(hours=2)
                print('TIMER POSTPONED') # TODO logging
                # [TEST] self.next_question_time = datetime.now() + timedelta(seconds=30)
            
            elif subtype == 'who_are_you':
                pass
            
            elif subtype == 'read_pending_messages':
                pass

        elif type == 'confirm': # Questions asked
            if subtype == 'how_are_you': # Put again a timer tomorrow at 8 am
                self.next_question_time = (datetime.now() + timedelta(days=1)).replace(hour=8,minute=0)
                print('TIMER SETT') # TODO logging
                # [TEST] self.next_question_time = datetime.now() + timedelta(minutes=1)

            elif subtype == 'who_are_you':
                pass
            
            elif subtype == 'read_pending_messages':
                self.tg_messages.clear() # Clear messages
