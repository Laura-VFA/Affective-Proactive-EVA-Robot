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


class ProactiveService():
    def __init__(self, callback) -> None:
        self.question = None
        self.callback = callback

        # Put an alarm every day at 8 am 
        self.next_question_time = (datetime.now() + timedelta(days=1)).replace(hour=8,minute=0)
        print('TIMER SETT')
        # TEST self.next_question_time = datetime.now() + timedelta(minutes=1)

    
    def update(self, type, subtype):
        if type == 'sensor':
            if subtype == 'presence':
                # Ask the user 'How are you?'
                if (self.next_question_time - datetime.now()).total_seconds() <= 0: 
                    self.callback('ask_how_are_you')

            elif subtype == 'unknown_face':
                self.callback('ask_who_are_you')
            
        elif type == 'abort':
            if subtype == 'how_are_you':
                # postpone the timer 2 hours
                self.next_question_time = datetime.now() + timedelta(hours=2)
                print('TIMER POSTPONED')
                # TEST self.next_question_time = datetime.now() + timedelta(seconds=30)
            
            elif subtype == 'who_are_you':
                pass
        
        elif type == 'confirm':
            if subtype == 'how_are_you':
                self.next_question_time = (datetime.now() + timedelta(days=1)).replace(hour=8,minute=0)
                print('TIMER SETT')
                #TEST self.next_question_time = datetime.now() + timedelta(minutes=1)

            elif subtype == 'who_are_you':
                pass
