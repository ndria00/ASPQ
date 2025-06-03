import clingo
from ProgramsHandler import ProgramsHandler


class ASPQSolver:
    programs_handler : ProgramsHandler
    encoding : str
    instance : str
    ctl : clingo.Control
    model : clingo.Model
    model_as_constraint: str
    assumptions : list
    atoms_defined_in_p1 = []

    def __init__(self, encoding, instance) -> None:
        self.ctl = clingo.Control()
        self.encoding = "\n".join(open(encoding).readlines())
        self.instance = "\n".join(open(instance).readlines())
        self.programs_handler = ProgramsHandler(self.encoding, self.instance)
        self.assumptions = []       
        self.ground()
        self.solve()

    
    def ground(self):
        for program in self.programs_handler.relaxed_programs:
            #print("Adding program to ctl -> ", "\n".join(program.rules))
            self.ctl.add("\n".join(program.rules))

        self.ctl.add(self.programs_handler.instance)
        self.ctl.ground([("instance", [])])
    
        self.ctl.ground([("base", [])])

    def solve(self):
        for atom in self.ctl.symbolic_atoms:
            if atom.symbol.name in self.programs_handler.relaxed_programs[0].head_predicates:
                self.atoms_defined_in_p1.append(atom.symbol)
                print(f"Symbolic atom used for assumptions {type(atom.symbol)}")
            else:
                print(f"Not used for assumptions {atom.symbol}")
        while True:
            result = self.ctl.solve(assumptions = [], on_model=self.on_model)
            #Project result over M_1 and add assumptions

            #solve to find counterexample

            #if counterexample found, then add M1 as constraint, M2 as counterexample and go ahead

            #add M1 as constraint
            self.ctl.add("constraints", [], self.model_as_constraint)
            self.ctl.ground([("constraints", [])])
            if result.satisfiable:
                print("CHAIN EXISTS")
                    
            elif result.unsatisfiable:
                print("ASPQ UNSAT")
                exit(20)
            else:
                raise Exception("Unexpected exit code")
            

    def on_model(self, model):
        self.model = model
        print(f"model found {model}")
        symbols = model.symbols(shown=True)

        if any(symb.name =="unsat_p_0" for symb in symbols):
            print("ASPQ UNSAT")
            exit(20)
        elif any(symb.name =="unsat_p_1" for symb in symbols):
            print("ASPQ SAT")
            exit(10)

        self.model_as_constraint = ":-"
        first = True
        for sym in self.atoms_defined_in_p1:
            if sym in symbols:
                self.assumptions.append((str(sym), True))
                conj = f"{str(sym)}" if first else f", {str(sym)}" 
                self.model_as_constraint += conj
            else:
                self.assumptions.append((str(sym), False))
                conj = f"not {str(sym)}" if first else f", not {str(sym)}" 
                self.model_as_constraint += conj            
            first = False
        self.model_as_constraint += "."
        print(f"ASSUMPTIONS: {self.assumptions}")
        print(f"CONSTRAINT: {self.model_as_constraint}")
