from c_llvm.ast.base import AstNode


class DeclarationNode(AstNode):
    def toString(self):
        return "declaration"
