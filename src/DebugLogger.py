
from .MyLogger import MyLogger


class DebugLogger(MyLogger):
    
    def print(self, str):
        print(str)