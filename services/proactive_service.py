from datetime import datetime, timedelta

class ProactiveService():
    phrases = {
        'how_are_you' : [
            '¿Cómo estás?',
            '¿Qué tal?',
            '¿Qué tal estás?',
            '¿Cómo te encuentras?',
        ],
        'who_are_you': [
            'Creo que no nos conocemos. ¿Cómo te llamas?'
        ]
    }


    def __init__(self, callback) -> None:
        self.question = None
        self.callback = callback

        # Put an alarm every day at 8 am 
        #self.next_question_time = (datetime.now() + timedelta(days=1)).replace(hour=8,minute=0)
        print('TIMER SETT')
        self.next_question_time = datetime.now() + timedelta(minutes=1)

    
    def update(self, type, subtype):
        if type == 'sensor':
            if subtype == 'presence':
                # Ask the user 'How are you?'
                if (self.next_question_time - datetime.now()).total_seconds() <= 0: 
                    self.callback('ask_how_are_you')

            elif subtype == 'unknown_face':
                return
                self.callback('who_are_you')
            
        elif type == 'abort':
            if subtype == 'how_are_you':
                # postpone the timer 2 hours
                #self.next_question_time = datetime.now() + timedelta(hours=2)
                print('TIMER POSTPONED')
                self.next_question_time = datetime.now() + timedelta(seconds=30)
        
        elif type == 'confirm':
            if subtype == 'how_are_you':
                #self.next_question_time = (datetime.now() + timedelta(days=1)).replace(hour=8,minute=0)
                print('TIMER SETT')
                self.next_question_time = datetime.now() + timedelta(minutes=1)
