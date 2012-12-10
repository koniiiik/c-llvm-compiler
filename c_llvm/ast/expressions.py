from c_llvm.ast.base import AstNode


class ExpressionNode(AstNode):
    """
    Common superclass for all expression type AST nodes.
    """
    pass


def BinaryExpressionNode(ExpressionNode):
    child_attributes = {
        'left': 0,
        'right': 1,
    }


class ExpressionListNode(ExpressionNode):
    pass


class AssignmentExpressionNode(ExpressionNode):
    def toString(self):
        return ""


class ConditionalExpressionNode(ExpressionNode):
    pass


class LogicalExpressionNode(BinaryExpressionNode):
    pass


class BitwiseExpressionNode(BinaryExpressionNode):
    pass


class EqualityExpressionNode(BinaryExpressionNode):
    pass


class RelationalExpressionNode(BinaryExpressionNode):
    pass


class ShiftExpressionNode(BinaryExpressionNode):
    pass


class AdditiveExpressionNode(BinaryExpressionNode):
    pass


class MultiplicativeExpressionNode(BinaryExpressionNode):
    pass


class CastExpressionNode(ExpressionNode):
    def toString(self):
        return ""


class DereferenceExpressionNode(ExpressionNode):
    pass


class AddressExpressionNode(ExpressionNode):
    pass


class UnaryArithmeticExpressionNode(ExpressionNode):
    pass


class BitwiseNegationExpressionNode(ExpressionNode):
    pass


class LogicalNegationExpressionNode(ExpressionNode):
    pass
