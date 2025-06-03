import sys
import clingo
from clingo.ast import parse_string
from ASPQSolver import ASPQSolver
from GrounderObserver import GrounderObserver
from ProgramsHandler import ProgramsHandler
from RelaxedRewriter import RelaxedRewriter
from SplitProgramRewriter import SplitProgramRewriter



def on_model(model):
    print(f"model found {model}")
    symbols = model.symbols(shown=True)

    if any(symb.name =="unsat_p_0" for symb in symbols):
        print("ASPQ UNSAT")
        exit(20)
    elif any(symb.name =="unsat_p_1" for symb in symbols):
        print("ASPQ SAT")
        exit(10)

    # for atom in symbols:
    #     print(f"Found atom {atom} {atom.name} in model")


def main():

    solver  = ASPQSolver("example.asp", "instance.asp") 
    
    
    # ctl = clingo.Control()
    # encoding_file = "example.asp" #sys.argv[1]
    # instance_file = "instance.asp" #sys.argv[2]

    # encoding = "\n".join(open(encoding_file).readlines())
    # instance = "\n".join(open(instance_file).readlines())

    # programs_handler = ProgramsHandler(encoding, instance)

    # # ctlG = clingo.Control()
    
    # # programs_handler.relaxed_programs[0].print_head_predicates()

    # # ctlG.add("\n".join(programs_handler.relaxed_programs[0].rules))
    # # print(f"Added {programs_handler.relaxed_programs[0].rules} to CONTROL {programs_handler.instance}")
    # # ctlG.add(programs_handler.instance)
    # # p1_grounder_observer = GrounderObserver()
    # # ctlG.register_observer(p1_grounder_observer)
    # # ctlG.ground([("base", [])])
    
    # for program in programs_handler.relaxed_programs:
    #     #print("Adding program to ctl -> ", "\n".join(program.rules))
    #     ctl.add("\n".join(program.rules))

    # grounder_observer = GrounderObserver()
    # ctl.register_observer(grounder_observer)


    # #print("Adding instance to ctl -> ", programs_handler.instance)
    # ctl.add(programs_handler.instance)
    # ctl.ground([("instance", [])])
    
    # ctl.ground([("base", [])])
    # atoms_defined_in_p1 = []
    # for atom in ctl.symbolic_atoms:
    #     if atom.symbol.name in programs_handler.relaxed_programs[0].head_predicates:
    #         atoms_defined_in_p1.append(atom.symbol)
    #         print(f"Symbolic atom used for assumptions {atom.symbol}")
    #     else:
    #         print(f"Not used for assumptions {atom.symbol}")

    # # print("Ground program")
    # # with ctl.backend() as backend:
    # #     for atom in ctl.symbolic_atoms:
    # #         print(atom.symbol)
    # assumptions = []
    
    # while True:
    #     result = ctl.solve(on_model=on_model)
    #     #Project result over M_1 and add assumptions

    #     #solve to find counterexample

    #     #if counterexample found, then add M1 as constraint, M2 as counterexample and go ahead

    #     #add M1 as constraint

    #     if result.satisfiable:
    #         print("CHAIN EXISTS")
    #     elif result.unsatisfiable:
    #         print("ASPQ UNSAT")
    #         exit(20)
    #     else:
    #         raise Exception("Unexpected exit code")



if __name__ == "__main__":
    main()