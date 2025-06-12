import copy
from enum import Enum

class ProgramType(str, Enum):
    EXISTS = "exists"
    FORALL = "forall"
    CONSTRAINTS = "constraint"

class MyProgram:
    rules : list[str]
    program_type : ProgramType
    name : str
    head_predicates : set

    def __init__(self, rules, program_type, program_name, head_predicates) -> None:
        self.rules = copy.copy(rules)
        self.program_type = program_type
        self.name = program_name
        self.head_predicates = copy.copy(head_predicates)
    
    def print_head_predicates(self):
        for predicate in self.head_predicates : 
            print(f"Head predicate {predicate}, ")

    def __str__(self):
        return "\n".join(self.rules)