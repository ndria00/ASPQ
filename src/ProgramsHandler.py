
import clingo
from clingo.ast import parse_string
from .FlipConstraintRewriter import FlipConstraintRewriter
from .MyProgram import MyProgram, ProgramType
from .RelaxedRewriter import RelaxedRewriter
from .SplitProgramRewriter import SplitProgramRewriter


class ProgramsHandler:
    
    encoding : str
    instance : str
    original_programs : list[MyProgram]
    relaxed_programs : list[MyProgram]
    
    relaxed_rewriter : RelaxedRewriter
    split_rewriter : SplitProgramRewriter

    flipped_constraint : MyProgram

    
    def split_programs(self):
        self.split_rewriter = SplitProgramRewriter()
        parse_string(self.encoding, lambda stm: (self.split_rewriter(stm)))
        self.split_rewriter.closed_program()

    def relax_programs(self):
        lvl = len(self.split_rewriter.programs)
        for i in range(1,len(self.split_rewriter.programs)+1):
            prg = self.split_rewriter.programs[i-1]
            self.original_programs.append(prg)
            self.relaxed_rewriter = RelaxedRewriter(lvl, f"unsat_{prg.name}")
            parse_string("\n".join(prg.rules), lambda stm : (self.relaxed_rewriter(stm)))

            # print(f"Adding program to ctl: {self.relaxed_rewriter.program}")
            # self.ctl.add(prg.name, [], "\n".join(self.relaxed_rewriter.program))
            self.relaxed_programs.append(MyProgram(program_name=prg.name, program_type=prg.program_type, head_predicates=self.relaxed_rewriter.head_predicates, rules=self.relaxed_rewriter.program))
            #print("Original program was ", prg.rules)
            #print("Relaxed program is ", self.relaxed_programs[len(self.relaxed_programs)-1])
            # print(f"Added program with name {prg.name} -> {relaxed_rewriter.program} and type {prg.program_type}")
            self.relaxed_rewriter.reset()
            lvl -= 1
        
        # prg = self.split_rewriter.programs[len(self.split_rewriter.programs) -1]
        # constraint_rewriter = ConstraintRewriter(lvl, "unsat_c")
        # parse_string("\n".join(prg.rules), lambda stm : (constraint_rewriter(stm)))
        # self.relaxed_programs.append(MyProgram(program_name=prg.name, program_type=prg.program_type, head_predicates=constraint_rewriter.head_predicates, rules=constraint_rewriter.program))

    def flip_constraint(self):
        for program in self.original_programs:
            if program.program_type == ProgramType.CONSTRAINTS:
                flipConstraintRewriter = FlipConstraintRewriter("unsat_c")
                parse_string("\n".join(program.rules), lambda stm: (flipConstraintRewriter(stm)))
                self.flipped_constraint = MyProgram(rules=flipConstraintRewriter.program, program_type=ProgramType.CONSTRAINTS, program_name=program.name, head_predicates=flipConstraintRewriter.head_predicates)
                #print("Original constraint program: ", constraint_program)
                #print("Flipped constraint program: ", self.flipped_constraint)
                print("Flipped program ", self.flipped_constraint)
                break

    def __init__(self, encoding, instance):
        self.encoding = encoding
        self.instance = instance
        self.original_programs = []
        self.relaxed_programs = []
        self.split_programs()
        self.relax_programs()
        self.flip_constraint()