from c_llvm.ast.base import AstNode


class CompoundStatementNode(AstNode):
    def toString(self):
        return ""

    def toStringTree(self):
        return "{\n%s\n}" % (
            super(CompoundStatementNode, self).toStringTree(),
        )
