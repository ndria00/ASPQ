

import copy
import clingo
from clingo.ast import parse_string
from .MyProgram import MyProgram


class ConstraintProgramRewriter(clingo.ast.Transformer):
    constraints_program : MyProgram
    rewritten_program : list
    rewrite_predicates : set
    iteration : int
    suffix_p : str
    fail_atom_name : str
    
    def __init__(self, p2_predicates, constraints_program):
        self.rewrite_predicates = constraints_program.head_predicates | p2_predicates
        # print("REWRITE PREDICATES FOR C ", self.rewrite_predicates)
        self.constraints_program = constraints_program
        self.iteration = 1
        self.rewritten_program = []

    def rewrite(self, suffix_p, fail_atom_name):
        self.suffix_p = suffix_p
        self.fail_atom_name = fail_atom_name
        self.rewritten_program = []
        parse_string("\n".join(self.constraints_program.rules), lambda stm: (self(stm)))

    def visit_Rule(self, node):
        rewritten_body = []
        if node.head.atom.ast_type == clingo.ast.ASTType.BooleanConstant:
            new_head = node.head
        else:
            if node.head.ast_type == clingo.ast.ASTType.Literal:
                new_term = clingo.ast.Function(node.location, node.head.atom.symbol.name + self.suffix_p, node.head.atom.symbol.arguments, False)
                new_head = clingo.ast.SymbolicAtom(new_term)
            else:
                raise Exception("Not supported head")

        for elem in node.body:
            if elem.ast_type == clingo.ast.ASTType.Literal:
                if not elem.atom is None:
                    #lit is defined in P2
                    if elem.atom.ast_type == clingo.ast.ASTType.SymbolicAtom and elem.atom.symbol.name in self.rewrite_predicates:
                        new_term = clingo.ast.Function(node.location, elem.atom.symbol.name + self.suffix_p,elem.atom.symbol.arguments, False)
                        new_atom = clingo.ast.SymbolicAtom(new_term)
                        new_literal = clingo.ast.Literal(node.location, elem.sign, new_atom)
                        rewritten_body.append(new_literal)
                    else:
                        rewritten_body.append(elem)
                else:
                    raise Exception("body atom is None")    
            else:
                rewritten_body.append(elem)
        fail_func = clingo.ast.Function(node.location, self.fail_atom_name, [], False)
        fail_lit = clingo.ast.Literal(node.location, clingo.ast.Sign.Negation, clingo.ast.SymbolicAtom(fail_func))
        rewritten_body.append(fail_lit)

        self.rewritten_program.append(str(clingo.ast.Rule(node.location, new_head, rewritten_body)))


