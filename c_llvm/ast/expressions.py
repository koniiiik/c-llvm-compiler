from c_llvm.ast.base import AstNode


class ExpressionNode(AstNode):
    """
    Common superclass for all expression type AST nodes.
    """
    pass


class ExpressionListNode(ExpressionNode):
    pass


class AssignmentExpressionNode(ExpressionNode):
    def toString(self):
        return ""
