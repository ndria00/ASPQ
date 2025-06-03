
import clingo
from clingo.ast import parse_string
from MyProgram import MyProgram
from RelaxedRewriter import RelaxedRewriter
from SplitProgramRewriter import SplitProgramRewriter


class ProgramsHandler:
    
    encoding : str
    instance : str
    original_programs : list[MyProgram]
    relaxed_programs : list[MyProgram]
    
    relaxed_rewriter : RelaxedRewriter
    split_rewriter : SplitProgramRewriter


    
    def split_programs(self):
        self.split_rewriter = SplitProgramRewriter()
        parse_string(self.encoding, lambda stm: (self.split_rewriter(stm)))
        self.split_rewriter.closed_program()

    def relax_programs(self):
        self.relaxed_rewriter = RelaxedRewriter()
        
        lvl = len(self.split_rewriter.programs)
        for prg in self.split_rewriter.programs:
            self.relaxed_rewriter.unsat_pred_name = f"unsat_{prg.name}"
            self.relaxed_rewriter.weak_level = lvl
            parse_string("\n".join(prg.rules), lambda stm : (self.relaxed_rewriter(stm)))

            # print(f"Adding program to ctl: {self.relaxed_rewriter.program}")
            # self.ctl.add(prg.name, [], "\n".join(self.relaxed_rewriter.program))
            self.relaxed_programs.append(MyProgram(program_name=prg.name, program_type=prg.program_type, head_predicates=self.relaxed_rewriter.head_predicates, rules=self.relaxed_rewriter.program))
            
            # print(f"Added program with name {prg.name} -> {relaxed_rewriter.program} and type {prg.program_type}")
            self.relaxed_rewriter.reset()
            lvl -= 1

    def __init__(self, encoding, instance):
        self.encoding = encoding
        self.instance = instance
        self.original_programs = []
        self.relaxed_programs = []
        self.split_programs()
        self.relax_programs()