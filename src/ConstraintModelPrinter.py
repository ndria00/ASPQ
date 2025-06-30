
from .ModelPrinter import ModelPrinter


class ConstraintModelPrinter(ModelPrinter):
    
    def __init__(self):
        pass
    
    def print_model(self, model, p1_symbols):
        print("Model:{", end="")

        for symbol in p1_symbols:
            if symbol in model:
                print(":- not ", symbol, ". ",end="")
            else:
                print(":- ", symbol, ". ",end="")
        print("}")