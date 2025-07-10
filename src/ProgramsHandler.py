
import clingo
from clingo.ast import parse_string
from .FlipConstraintRewriter import FlipConstraintRewriter
from .MyProgram import MyProgram, ProgramQuantifier
from .RelaxedRewriter import RelaxedRewriter
from .SplitProgramRewriter import SplitProgramRewriter


class ProgramsHandler:
    
    encoding : str
    original_programs :dict
    relaxed_programs : dict
    
    relaxed_rewriter : RelaxedRewriter
    split_rewriter : SplitProgramRewriter

    flipped_constraint : MyProgram

    
    def split_programs(self):
        self.split_rewriter = SplitProgramRewriter()
        parse_string(self.encoding, lambda stm: (self.split_rewriter(stm)))
        self.split_rewriter.check_aspq_type()
        for i in range(1,len(self.split_rewriter.programs)+1):
            prg = self.split_rewriter.programs[i-1]
            self.original_programs[prg.program_type] = prg

    def relax_programs(self):
        lvl = len(self.split_rewriter.programs)
        for i in range(1,len(self.split_rewriter.programs)+1):
            prg = self.split_rewriter.programs[i-1]
            self.original_programs[prg.program_type] = prg
            self.relaxed_rewriter = RelaxedRewriter(lvl, f"unsat_{prg.name}")
            parse_string("\n".join(prg.rules), lambda stm : (self.relaxed_rewriter(stm)))

            # print(f"Adding program to ctl: {self.relaxed_rewriter.program}")
            # self.ctl.add(prg.name, [], "\n".join(self.relaxed_rewriter.program))
            self.relaxed_programs[prg.program_type] = MyProgram(program_name=prg.name, program_type=prg.program_type, head_predicates=self.relaxed_rewriter.head_predicates, rules=self.relaxed_rewriter.program)
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
        if ProgramQuantifier.CONSTRAINTS in self.original_programs:
            program = self.original_programs[ProgramQuantifier.CONSTRAINTS] 
            flipConstraintRewriter = FlipConstraintRewriter("unsat_c")

            parse_string("\n".join(program.rules), lambda stm: (flipConstraintRewriter(stm)))
            self.flipped_constraint = MyProgram(rules=flipConstraintRewriter.program, program_type=ProgramQuantifier.CONSTRAINTS, program_name=program.name, head_predicates=flipConstraintRewriter.head_predicates)
            #print("Original constraint program: ", constraint_program)
            #print("Flipped constraint program: ", self.flipped_constraint)
            # print("Flipped program ", self.flipped_constraint, "Head predicates: ", self.flipped_constraint.head_predicates)
     
    def p1(self):
        return self.original_programs[ProgramQuantifier.EXISTS] if self.split_rewriter.exists_forall() or self.split_rewriter.exists() else self.original_programs[ProgramQuantifier.FORALL]
    
    def p2(self):
        program = None
        if self.split_rewriter.exists_forall():
            program = self.original_programs[ProgramQuantifier.FORALL]
        elif self.split_rewriter.forall_exists():
            program = self.original_programs[ProgramQuantifier.EXISTS]
        return program
    
    def c(self):
        return self.original_programs[ProgramQuantifier.CONSTRAINTS]

    def neg_c(self):
        return self.flipped_constraint

    def __init__(self, encoding):
        self.encoding = encoding
        self.original_programs = {}
        self.relaxed_programs = {}
        self.flipped_constraint = None
        self.split_programs()
        #self.relax_programs()
        self.flip_constraint()