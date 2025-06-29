from abc import abstractmethod


class ModelPrinter:
    
    @abstractmethod
    def print_model(self, model, p1_symbols):
        pass