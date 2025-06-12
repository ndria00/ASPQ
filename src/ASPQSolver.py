import clingo
from .ReductRewriter import ReductRewriter
from .ProgramsHandler import ProgramsHandler
from clingo.ast import parse_string


class ASPQSolver:
    programs_handler : ProgramsHandler
    encoding : str
    instance : str
    ctl_relaxed_programs : clingo.Control
    ctl_counter_example : clingo.Control
    ctl_p1 : clingo.Control
    model_as_constraint: str
    assumptions : list
    atoms_defined_in_p1 = []
    atoms_defined_in_p2 = []
    forall_unsat : bool
    last_model_symbols : clingo.solving._SymbolSequence
    reduct_rewriter : ReductRewriter
    assumptions : list
    n_models : int
    models_found : int

    def __init__(self, encoding, instance, n_models) -> None:
        self.ctl_relaxed_programs = clingo.Control()
        self.ctl_counter_example = clingo.Control()
        self.ctl_p1 = clingo.Control()
        self.encoding = "\n".join(open(encoding).readlines())
        self.instance = "\n".join(open(instance).readlines())
        self.programs_handler = ProgramsHandler(self.encoding, self.instance)
        self.assumptions = []
        self.model_as_constraint = ""
        self.forall_unsat = False
        self.last_model_symbols = None
        self.assumptions = []
        self.atoms_defined_in_p1 = []
        self.atoms_defined_in_p2 = []
        self.n_models = n_models
        self.models_found = 0

    def ground(self):
        #ground relaxed programs
        for program in self.programs_handler.relaxed_programs:
            print("Adding program to relaxed programs ctl//\n", "\n".join(program.rules), "//")
            self.ctl_relaxed_programs.add("\n".join(program.rules))
        self.ctl_relaxed_programs.add(self.programs_handler.instance)

        #register an observer in such a way that the head of each ground rule is added to
        #the counterexample program as a choice 
        #self.ctl_relaxed_programs.ground([("instance", [])])
        #observer = GrounderObserver()
        #self.ctl_relaxed_programs.register_observer(observer)
        self.ctl_relaxed_programs.ground([("base", [])])

        #consider only predicates appearing in the head of program P1
        #for constructing assumption(fixing the model of P1) and adding the model as constraint
        choice ="{"
        disjoint = True
        for atom in self.ctl_relaxed_programs.symbolic_atoms:
            if atom.symbol.name in self.programs_handler.relaxed_programs[0].head_predicates:
                self.atoms_defined_in_p1.append(atom.symbol)
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
        
        self.ctl_counter_example.add(self.programs_handler.instance)
        #print(f"Added program instance to counterexample control: //{self.programs_handler.instance}//")
        self.ctl_counter_example.add("\n".join(self.programs_handler.original_programs[1].rules))
        #print(f"Added program forall to counterexample control: //", "\n".join(self.programs_handler.original_programs[1].rules), "//")
        self.ctl_counter_example.add("\n".join(self.programs_handler.flipped_constraint.rules))
        #print(f"Added program neg C to counterexample control: //", "\n".join(self.programs_handler.flipped_constraint.rules), "//")
        self.ctl_counter_example.ground([("base", [])])

        for atom in self.ctl_counter_example.symbolic_atoms:
            if atom.symbol.name in self.programs_handler.relaxed_programs[1].head_predicates:
                self.atoms_defined_in_p2.append(atom.symbol)

    def solve(self):
        result = self.ctl_relaxed_programs.solve(on_model=self.on_model)
        if not self.last_model_symbols is None:
            # no way to satisfy P1
            if any(symb.name =="unsat_p_1" for symb in self.last_model_symbols):
                print("ASPQ UNSAT")
                exit(20)
            # whatever M1 for P2 yields a program P2 | M1 which is unsat
            if any(symb.name =="unsat_p_2" for symb in self.last_model_symbols):
                self.models_found += 1
                print(f"Model {self.models_found}: {self.last_model_symbols}")
                if self.models_found == self.n_models:
                    print("ASPQ SAT")
                    exit(10)
                else:
                    self.add_model_as_constraint()
                    self.last_model_symbols = None
                    return
            # C can never be satisfied given M1 and M2
            if any(symb.name =="unsat_c" for symb in self.last_model_symbols):
                print("ASPQ UNSAT")
                exit(20)
        else:
            raise Exception("Relaxed program is unsatisfiable")
        print("CHAIN EXISTS")
        
        self.ctl_p1.add(self.programs_handler.instance)
        
        self.ctl_p1.add("\n".join(self.programs_handler.original_programs[0].rules))
        self.ctl_p1.ground()
        self.reduct_rewriter = ReductRewriter(self.programs_handler.original_programs[1], self.programs_handler.original_programs[2])
        
        while self.models_found != self.n_models:
            self.solve_once()
            result = self.ctl_p1.solve(on_model=self.on_model)
            if result.unsatisfiable:
                return

    def solve_once(self):
        # print("Model: ", self.last_model_symbols)
        # print("ADDED PROGRAM ", "\n".join(self.programs_handler.original_programs[0].rules), "TO CTL PROGRAM 1")
        
        while True:
            #add model M_1 of P_1 as assumption
            self.assumptions = []
            for symbol in self.atoms_defined_in_p1:
                if symbol in self.last_model_symbols and symbol.name in self.programs_handler.relaxed_programs[0].head_predicates:
                    self.assumptions.append((symbol, True))
                else:
                    self.assumptions.append((symbol, False))

            #print(f"ASSUMPTIONS: {self.assumptions}")
            #search for counterexample
            result = self.ctl_counter_example.solve(assumptions=self.assumptions, on_model=self.on_model)
            
            if result.unsatisfiable:
                print("ASPQ SAT ")
                self.models_found += 1
                print(f"Model {self.models_found}: {self.last_model_symbols}")
                if self.models_found == self.n_models:
                    exit(10)
                else:
                    self.add_model_as_constraint()
                    self.last_model_symbols = None
                    return
            else:
                print("Counterexample: ", self.last_model_symbols)

            counterexample_facts = ""
            for symbol in self.atoms_defined_in_p2:
                if symbol in self.last_model_symbols and symbol.name in self.programs_handler.relaxed_programs[1].head_predicates:
                    new_symbol = clingo.Function(symbol.name + self.reduct_rewriter.suffix_n, symbol.arguments, symbol.positive)
                    counterexample_facts = counterexample_facts + str(new_symbol) + "."
                    #self .assumptions.append((new_symbol, True))
                    #self.assumptions.append((symbol, True))
                # else:
                #     pass
                    #new_symbol = clingo.Function(symbol.name + self.reduct_rewriter.suffix_n, symbol.arguments, symbol.positive)
                    #self.assumptions.append((new_symbol, False))
                    #self.assumptions.append((symbol, False))
            
            self.reduct_rewriter.rewrite()
            print("Rewritten program: ", self.reduct_rewriter.rewritten_program)
            print("M2 facts: ", counterexample_facts)
            self.ctl_p1.add(f"iteration_{self.reduct_rewriter.iteration}", [], "\n".join(self.reduct_rewriter.rewritten_program) + counterexample_facts)

            self.ctl_p1.ground([(f"iteration_{self.reduct_rewriter.iteration}", [])])

            #find a new M_1 for which none of the already discovered counterexample is admitted
            self.last_model_symbols = None
            #print("Called solve")
            result = self.ctl_p1.solve(on_model=self.on_model)
            if result.unsatisfiable:
                print("ASPQ UNSAT")
                exit(20)
            # else:
            #     print("New M1 found: ", self.last_model_symbols)
    
    def on_model(self, model):
        self.last_model_symbols = model.symbols(shown=True)


    def add_model_as_constraint(self):
        constraint = ":-"
        for symbol in self.atoms_defined_in_p1:
            if symbol in self.last_model_symbols:
                constraint += f"{symbol},"

            else:
                constraint += f"not {symbol},"

        constraint = constraint[:-1]
        constraint += "."
        # print("ADDING CONSTRAINT: ", constraint)
        self.ctl_p1.add(f"constraint_{self.models_found}",[], constraint)
        self.ctl_p1.ground([(f"constraint_{self.models_found}", [])])
        