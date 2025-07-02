from pathlib import Path
import clingo
from src import MyProgram
from src.ConstraintModelPrinter import ConstraintModelPrinter
from src.DebugLogger import DebugLogger
from src.ExecutionLogger import ExecutionLogger
from src.ModelPrinter import ModelPrinter
from src.MyLogger import MyLogger
from src.PositiveModelPrinter import PositiveModelPrinter
from src.SplitProgramRewriter import ProgramType
from .ReductRewriter import ReductRewriter
from .ProgramsHandler import ProgramsHandler
from clingo.ast import parse_string

class ASPQSolver:
    programs_handler : ProgramsHandler
    encoding : str
    ctl_relaxed_programs : clingo.Control
    ctl_counter_example : clingo.Control
    ctl_p1 : clingo.Control
    assumptions : list
    p1 : MyProgram
    p2 : MyProgram
    symbols_defined_in_p1 : set
    symbols_defined_in_p2 : set
    last_model_symbols : clingo.solving._SymbolSequence
    last_model_symbols_set : set
    reduct_rewriter : ReductRewriter
    n_models : int
    models_found : int
    exists_forall: bool
    counterexample_found : int
    model_printer : ModelPrinter
    logger : MyLogger

    def __init__(self, encoding_path, n_models, debug, constraint_print) -> None:
        self.ctl_relaxed_programs = clingo.Control()
        self.ctl_counter_example = clingo.Control()
        self.ctl_p1 = clingo.Control()
        self.encoding = "\n".join(open(encoding_path).readlines())
        self.programs_handler = ProgramsHandler(self.encoding)
        self.assumptions = []
        self.last_model_symbols = None
        self.last_model_symbols_set = set()
        self.symbols_defined_in_p1 = set()
        self.symbols_defined_in_p2 = set()
        self.p1 = self.programs_handler.p1()
        self.p2 = self.programs_handler.p2()
        self.n_models = n_models
        self.models_found = 0
        self.counterexample_found = 0
        self.model_printer = PositiveModelPrinter() if not constraint_print else ConstraintModelPrinter()
        self.logger = DebugLogger() if debug else ExecutionLogger()
        self.exists_forall = self.programs_handler.split_rewriter.exists_forall()

    def ground(self):
        #solve directly
        #program is of the form \exists P_1 or \exists P_1 : C
        if self.programs_handler.split_rewriter.program_type == ProgramType.EXISTS:
            ctl_exists = clingo.Control([f"-n {self.n_models}"])
            ctl_exists.add("\n".join(self.p1.rules))
            ctl_exists.ground([("base", [])])
            with ctl_exists.solve(yield_=True) as handle:
                for m in handle:
                    self.models_found += 1
                    print(m)
                    if self.models_found == self.n_models:
                        self.exit_sat()
                    handle.get()
            if self.models_found == 0:
                self.exit_unsat()
            else: # models are less than the desired number
                self.exit_sat()
        if self.programs_handler.split_rewriter.program_type == ProgramType.FORALL:
            ctl_forall = clingo.Control([])
            ctl_forall.add("\n".join(self.p1.rules))
            ctl_forall.add("\n".join(self.programs_handler.neg_c().rules))
            ctl_forall.ground([("base", [])])
            result =  ctl_forall.solve()
            if result.unsatisfiable:
                self.exit_sat()
            else:
                self.exit_unsat()


        #ground relaxed programs
        for program in self.programs_handler.relaxed_programs.values():
            program_rules = "\n".join(program.rules)
            self.logger.print(f"Adding program to relaxed programs ctl//\n {program_rules}//")
            self.ctl_relaxed_programs.add(program_rules)
 
        self.ctl_relaxed_programs.ground([("base", [])])

        #consider only predicates appearing in the head of program P1
        #for constructing assumption(fixing the model of P1) and adding the model as constraint
        choice ="{"
        disjoint = True
        for atom in self.ctl_relaxed_programs.symbolic_atoms:
            if atom.symbol.name in self.p1.head_predicates:
                self.symbols_defined_in_p1.add(atom.symbol)
                choice = choice + str(atom.symbol) + ";"
                disjoint = False

            #     print(f"Symbolic atom used for assumptions {atom.symbol}")
            # else:
            #     print(f"Not used for assumptions {atom.symbol}")
        if not disjoint:
            choice = choice[:-1]
            choice += "}.\n"
            self.ctl_counter_example.add(choice)
            #print(f"Added program choice to counterexample control: //{choice}//")
        
        
        self.ctl_counter_example.add("\n".join(self.p2.rules))
        #print(f"Added program forall to counterexample control: //", "\n".join(self.programs_handler.original_programs[1].rules), "//")
        
        
        if self.exists_forall:
            self.ctl_counter_example.add("\n".join(self.programs_handler.neg_c().rules))
        else:
            self.ctl_counter_example.add("\n".join(self.programs_handler.c().rules))
        #print(f"Added program neg C to counterexample control: //", "\n".join(self.programs_handler.flipped_constraint.rules), "//")
        self.ctl_counter_example.ground([("base", [])])

        for atom in self.ctl_counter_example.symbolic_atoms:
            if atom.symbol.name in self.programs_handler.relaxed_programs[self.p2.program_type].head_predicates:
                self.symbols_defined_in_p2.add(atom.symbol)

    def solve(self):
        result = self.ctl_relaxed_programs.solve(on_model=self.on_model, on_finish=self.finished_solve)
        if not self.last_model_symbols is None:
            # no way to satisfy P1
            if any(symb.name =="unsat_p_1" for symb in self.last_model_symbols):
                if self.exists_forall:
                    self.exit_unsat()
                else:
                    self.exit_sat()
            # whatever M1 for P2 yields a program P2 | M1 which is unsat
            if any(symb.name =="unsat_p_2" for symb in self.last_model_symbols):
                if not self.exists_forall:
                    self.exit_unsat()
                self.models_found += 1
                # print(f"Model {self.models_found}:")
                self.print_projected_model()
                if self.models_found == self.n_models:
                    self.exit_sat()
                else:
                    self.add_model_as_constraint()
                    self.last_model_symbols = None
                    return
            # C can never be satisfied given M1 and M2
            if any(symb.name =="unsat_c" for symb in self.last_model_symbols):
                self.exit_unsat()
        else:
            raise Exception("Relaxed program is unsatisfiable")
        # print("CHAIN EXISTS")
        
        
        self.ctl_p1.add("\n".join(self.programs_handler.original_programs[self.p1.program_type].rules))
        self.ctl_p1.ground()
        if self.exists_forall:
            self.reduct_rewriter = ReductRewriter(self.programs_handler.original_programs[self.p2.program_type], self.programs_handler.c())
        else:
            self.reduct_rewriter = ReductRewriter(self.programs_handler.original_programs[self.p2.program_type], self.programs_handler.neg_c())
        while self.models_found != self.n_models:
            self.solve_once()
            result = self.ctl_p1.solve(on_model=self.on_model, on_finish=self.finished_solve)
            if result.unsatisfiable:
                if self.n_models != 0:
                    self.exit_sat()
                else:
                    self.exit_unsat()

    def solve_once(self): 
        while True:
            #add model M_1 of P_1 as assumption
            self.assumptions = []
            for symbol in self.symbols_defined_in_p1:
                if symbol in self.last_model_symbols_set and symbol.name in self.p1.head_predicates:
                    self.assumptions.append((symbol, True))
                else:
                    self.assumptions.append((symbol, False))

            #print(f"ASSUMPTIONS: {self.assumptions}")
            #search for counterexample
            result = self.ctl_counter_example.solve(assumptions=self.assumptions, on_model=self.on_model, on_finish=self.finished_solve)
            
            if result.unsatisfiable:
                #print("No counterexample found")
                if not self.exists_forall:
                    self.exit_unsat()
                self.print_projected_model()
                
                self.models_found += 1
                #print(f"Model {self.models_found}:")
                if self.models_found == self.n_models:
                    self.exit_sat()
                else:
                    #print("adding model as constraint after SAT")
                    self.add_model_as_constraint()
                    self.last_model_symbols = None
                    return
            else:
                self.counterexample_found += 1
                # print("Counterexample: ", self.last_model_symbols)
            counterexample_facts = ""
            for symbol in self.symbols_defined_in_p2:
                if symbol in self.last_model_symbols_set and symbol.name in self.programs_handler.relaxed_programs[self.p2.program_type].head_predicates:
                    new_symbol = clingo.Function(symbol.name + self.reduct_rewriter.suffix_n, symbol.arguments, symbol.positive)
                    counterexample_facts = counterexample_facts + str(new_symbol) + "."
            
            self.reduct_rewriter.rewrite()
            # print("Rewritten program: ", self.reduct_rewriter.rewritten_program)
            # print("M2 facts: ", counterexample_facts)
            self.ctl_p1.add(f"iteration_{self.reduct_rewriter.iteration}", [], self.reduct_rewriter.rewritten_program + counterexample_facts)

            self.ctl_p1.ground([(f"iteration_{self.reduct_rewriter.iteration}", [])])

            #find a new M_1 for which none of the already discovered counterexample is admitted
            self.last_model_symbols = None
            #print("Called solve")
            result = self.ctl_p1.solve(on_model=self.on_model, on_finish=self.finished_solve)
            if result.unsatisfiable:
                if self.exists_forall:
                    self.exit_unsat()
                else:
                    self.exit_sat()
            # else:
            #     print("New M1 found: ", self.last_model_symbols)
    
    def on_model(self, model):
        self.last_model_symbols = model.symbols(shown=True)

    def finished_solve(self, result):
        if not result.unsatisfiable:
            self.last_model_symbols_set.clear()
            for symbol in self.last_model_symbols:
                self.last_model_symbols_set.add(symbol)
            
    def add_model_as_constraint(self):
        constraint = ":-"
        for symbol in self.symbols_defined_in_p1:
            if symbol in self.last_model_symbols_set:
                constraint += f"{symbol},"

            else:
                constraint += f"not {symbol},"

        constraint = constraint[:-1]
        constraint += "."
        #print("Adding constraint: ", constraint)
        self.ctl_p1.add(f"constraint_{self.models_found}",[], constraint)
        self.ctl_p1.ground([(f"constraint_{self.models_found}", [])])
        

    def print_projected_model(self):
        self.model_printer.print_model(self.last_model_symbols_set, self.symbols_defined_in_p1)
        

    def exit_sat(self):
        self.print_debug_info()
        print("ASPQ SAT")
        exit(10)
    
    def exit_unsat(self):
        self.print_debug_info()
        print("ASPQ UNSAT")
        exit(20)

    def print_debug_info(self):
        if self.exists_forall:
            self.logger.print(f"Models found: {self.models_found}")
        self.logger.print(f"Counterexample found in the search: {self.counterexample_found}")
