import re
from clingo.ast import Transformer
from MyProgram import MyProgram, ProgramType


class SplitProgramRewriter(Transformer):
    programs: list[MyProgram]
    rules : list[str]
    program_type : ProgramType
    program_name : str

    def __init__(self) -> None:
        super().__init__()
        self.programs = []
        self.rules = []
        self.program_type = ProgramType.CONSTRAINTS
        self.program_name = "c"

    def visit_Comment(self, value):
        self.closed_program()
        value_str = str(value)
        if not re.match("%@exists", value_str) is None:
            self.program_type = ProgramType.EXISTS
            self.program_name = f"p_{len(self.programs)}"
            # print("Existential subprogram start")
        elif not re.match("%@forall", value_str) is None:
            self.program_type = ProgramType.FORALL
            self.program_name = f"p_{len(self.programs)}"
            # print("Universal subprogram start")
        elif not re.match("%@constraint", value_str) is None:
            self.program_type = ProgramType.CONSTRAINTS
            self.program_name = "c"
            # print("Constraints subprogram start")
        # else:
            #print("Spurious comment subprogram start")
        
        

    def visit_Rule(self, value):
        self.rules.append(str(value))
        # print(f"Found rule {value}\n")
    
    def closed_program(self):
        if len(self.rules) != 0:
            self.programs.append(MyProgram(self.rules, self.program_type, self.program_name,{}))
            self.rules = []

    def print_programs(self):
        for prg in self.programs:
            if prg.program_type == ProgramType.EXISTS:
                print("EXISTS PROGRAM")
            elif prg.program_type == ProgramType.FORALL:
                print("FORALL PROGRAM")
            else:
                print("CONSTRAINTS PROGRAM")
            print(f"{prg.rules}")