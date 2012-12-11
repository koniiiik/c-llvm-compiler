from c_llvm.ast.base import AstNode


class CompoundStatementNode(AstNode):
    def generate_code(self, state):
        state.enter_block()
        children = self.process_children(state)
        state.leave_block()
        return "\n".join(children)

    def toString(self):
        return ""

    def toStringTree(self):
        return "{\n%s\n}" % (
            super(CompoundStatementNode, self).toStringTree(),
        )
