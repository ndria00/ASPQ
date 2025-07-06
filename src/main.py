from .ASPQSolver import ASPQSolver
import argparse

def main():

    parser = argparse.ArgumentParser(prog = "ASPQ-native", description = "Native solver for 2-level ASPQ\n")

    parser.add_argument('--encoding', help="path to encoding file\n", required=True)
    parser.add_argument('--instance', help="path to encoding file\n", required=False, default="")
    parser.add_argument('--debug', help="enable debug\n", required=False, action="store_true")
    parser.add_argument('--constraint', help="enable constraint print of models\n", required=False, action="store_true")
    parser.add_argument('-n', help="number of q-answer sets to find\n", default=1)
    args = parser.parse_args()
    solver  = ASPQSolver(args.encoding, args.instance, int(args.n), bool(args.debug), bool(args.constraint)) 
    solver.ground()
    solver.solve()



if __name__ == "__main__":
    main()