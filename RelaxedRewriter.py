

import copy
import clingo
import clingo.ast


class RelaxedRewriter(clingo.ast.Transformer):
    unsat_pred_name : str
    program : list[str]
    weak_level : int
    head_predicates : set 

    def __init__(self):
        super().__init__()
        self.unsat_pred_name = "unsat"
        self.program = []
        self.weak_level = 2
        self.head_predicates = set()
    
    def visit_Literal(self, node):
        return node.update(**self.visit_children(node))

    def visit_Rule(self, node):
        head  = node.head
        clingo.ast.Literal
        if head.ast_type == clingo.ast.ASTType.Literal:
            try:
                self.extract_predicate_from_literal(head)         
            except :
                pass #head of constraints end up here
        elif clingo.ast.ASTType.Aggregate:
            self.extract_predicate_from_choice(head)

        unsat_atom = clingo.ast.SymbolicAtom(clingo.ast.Function(node.location, self.unsat_pred_name, [], False))

        node.body.insert(0, clingo.ast.Literal(location = node.location, sign=clingo.ast.Sign.Negation, atom=unsat_atom))
        self.program.append(str(clingo.ast.Rule(node.location, node.head, node.body)))
        return node.update(**self.visit_children(node))
    
    def visit_Program(self, node):
        choice = "{" + f"{self.unsat_pred_name}" + "}."
        weak = f":~{self.unsat_pred_name}. [1@{self.weak_level}]"
        self.program.append(weak)
        self.program.append(choice)
        return node.update(**self.visit_children(node))
    
    def extract_predicate_from_literal(self, node):
        #print(f"Added {node.atom.symbol.name} to head predicates")
        self.head_predicates.add(node.atom.symbol.name) 
       
    def extract_predicate_from_choice(self, node):
        for elem in node.elements:
            self.head_predicates.add(elem.literal.atom.symbol.name)
            #print(f"Added {elem.literal.atom.symbol.name} to head predicates")

    def reset(self):
        self.program = []
        self.head_predicates = set()


