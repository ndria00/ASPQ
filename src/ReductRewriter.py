
import clingo
from .ConstraintProgramRewriter import ConstraintProgramRewriter
from .MyProgram import MyProgram
from clingo.ast import parse_string

class ReductRewriter(clingo.ast.Transformer):
    original_program : MyProgram
    constraint_program : MyProgram
    constraint_program_rewriter : ConstraintProgramRewriter 
    rewritten_program : list
    iteration : int
    suffix_p : str
    suffix_n : str
    fail_atom_name : str

    def __init__(self, original_program, constraint_program):
        self.original_program = original_program
        self.constraint_program = constraint_program
        self.rewritten_program = []
        self.constraint_program_rewriter = ConstraintProgramRewriter(self.original_program.head_predicates, self.constraint_program)
        self.iteration = 1
        self.suffix_p = f"_p_{self.iteration}"
        self.suffix_n = f"_n_{self.iteration}"
        self.fail_atom_name = f"fail_{self.iteration}"

    def rewrite(self):
        self.rewritten_program = []
        parse_string("\n".join(self.original_program.rules), lambda stm: (self(stm)))
        self.constraint_program_rewriter.rewrite(self.suffix_p, self.fail_atom_name)
        self.rewritten_program += self.constraint_program_rewriter.rewritten_program
        
        self.iteration += 1
        self.suffix_p = f"_p_{self.iteration}"
        self.suffix_n = f"_n_{self.iteration}"
        self.fail_atom_name = f"fail_{self.iteration}"

    def visit_Rule(self, node):
        rewritten_body = []
        new_head = None
        for elem in node.body:
            if elem.ast_type == clingo.ast.ASTType.Literal:
                if not elem.atom is None:
                    if elem.atom.ast_type == clingo.ast.ASTType.SymbolicAtom and elem.atom.symbol.name in self.original_program.head_predicates:
                        new_term = clingo.ast.Function(node.location, elem.atom.symbol.name + self.suffix_n,elem.atom.symbol.arguments, False)
                        new_atom = clingo.ast.SymbolicAtom(new_term)
                        new_literal = clingo.ast.Literal(node.location, elem.sign, new_atom)
                        rewritten_body.append(new_literal)
                        
                    else:
                        rewritten_body.append(elem)
                else:
                    raise Exception("body atom is None")    
            else:
                rewritten_body.append(elem)
        
        if node.head.atom.ast_type != clingo.ast.ASTType.BooleanConstant:
            try:
                new_term = clingo.ast.Function(node.location, node.head.atom.symbol.name + self.suffix_p, node.head.atom.symbol.arguments, False)
                new_head = clingo.ast.SymbolicAtom(new_term)
                #add fail :- a_p not a_n for every rule in P2
                f_1 = clingo.ast.Function(node.location, node.head.atom.symbol.name + self.suffix_p, node.head.atom.symbol.arguments, False)
                f_2 = clingo.ast.Function(node.location, node.head.atom.symbol.name + self.suffix_n, node.head.atom.symbol.arguments, False)
                l_1 = clingo.ast.Literal(node.location, False, f_1)
                l_2 = clingo.ast.Literal(node.location, True, f_2)
                fail_head = clingo.ast.Function(node.location,self.fail_atom_name, [], False)
                fail_body = [l_1, l_2]
                self.rewritten_program.append(str(clingo.ast.Rule(node.location, fail_head, fail_body)))
                nl_1 = clingo.ast.Literal(node.location, True, f_1)
                nl_2 = clingo.ast.Literal(node.location, False, f_2)
                fail_body = [nl_1, nl_2]
                self.rewritten_program.append(str(clingo.ast.Rule(node.location, fail_head, fail_body)))
            except:
                print("Usupported head")
                exit(1)
        else:
            new_term = clingo.ast.Function(node.location, self.fail_atom_name, [], False)
            new_head = clingo.ast.SymbolicAtom(new_term)
        
        self.rewritten_program.append(str(clingo.ast.Rule(node.location, new_head, rewritten_body)))
    

