from UI import start
from reminder import set_reminder
from threading import Thread

if __name__ == '__main__':
    Thread(target = start).start()
    Thread(target = set_reminder('hola', 10)).start()

    # hacer join?