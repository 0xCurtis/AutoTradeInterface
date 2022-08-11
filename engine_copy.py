import os
from time import sleep
from module import Bybot_copy

if __name__ == '__main__':
    if not os.path.exists("logs"):
        os.makedirs("logs")
    bot = Bybot_copy.ByBot()
    sleep(1)
    exit(0)