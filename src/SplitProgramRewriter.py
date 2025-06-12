import re
import clingo
from clingo.ast import Transformer
from .MyProgram import MyProgram, ProgramType
from .Rewriter import Rewriter


class SplitProgramRewriter(Rewriter):
    programs: list[MyProgram]
    rules : list[str]
    program_type : ProgramType
    program_name : str
    open_program : bool
    def __init__(self) -> None:
        super().__init__()
        self.programs = []
        self.rules = []
        self.program_type = ProgramType.CONSTRAINTS
        self.program_name = "c"
        self.open_program = False

    def visit_Comment(self, value):
        self.closed_program()
        value_str = str(value)
        if not re.match("%@exists", value_str) is None:
            self.open_program = True
            self.program_type = ProgramType.EXISTS
            self.program_name = f"p_{len(self.programs)+1}"
            # print("Existential subprogram start")
        elif not re.match("%@forall", value_str) is None:
            self.open_program = True
            self.program_type = ProgramType.FORALL
            self.program_name = f"p_{len(self.programs)+1}"
            # print("Universal subprogram start")
        elif not re.match("%@constraint", value_str) is None:
            self.open_program = True
            self.program_type = ProgramType.CONSTRAINTS
            self.program_name = "c"
            # print("Constraints subprogram start")
        # else:
            #print("Spurious comment subprogram start")
        
        

    def visit_Rule(self, node):
        self.rules.append(str(node))
        head  = node.head
        if head.ast_type == clingo.ast.ASTType.Literal:
            if not head.atom.ast_type == clingo.ast.ASTType.BooleanConstant:
                self.extract_predicate_from_literal(head)         
        elif clingo.ast.ASTType.Aggregate:
            self.extract_predicate_from_choice(head)
        return node.update(**self.visit_children(node))
        # print(f"Found rule {value}\n")
    
    def closed_program(self):
        if self.open_program:
            self.programs.append(MyProgram(self.rules, self.program_type, self.program_name,self.head_predicates))
        self.rules = []
        self.head_predicates = set()

    def print_programs(self):
        for prg in self.programs:
            if prg.program_type == ProgramType.EXISTS:
                print("EXISTS PROGRAM")
            elif prg.program_type == ProgramType.FORALL:
                print("FORALL PROGRAM")
            else:
                print("CONSTRAINTS PROGRAM")
            print(f"{prg.rules}")