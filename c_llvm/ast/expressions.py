from c_llvm.ast.base import AstNode


class ExpressionNode(AstNode):
    """
    Common superclass for all expression type AST nodes.
    """
    def allocate_result_register(self, state):
        register = state.get_tmp_register()
        state.last_expression_register = register
        return register

    def get_type(self, state):
        raise NotImplementedError


class BinaryExpressionNode(ExpressionNode):
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


class VariableExpressionNode(ExpressionNode):
    child_attributes = {
        'name': 0,
    }

    def generate_code(self, state):
        try:
            var = state.symbols[str(self.name)]
        except KeyError:
            self.log_error(state, "unknown variable: %s" % (str(self.name),))
            return ""
        register = self.allocate_result_register(state)
        return "%s = load %s* %s" % (register, var.type.llvm_type,
                                     var.register)


class IntegerConstantNode(ExpressionNode):
    child_attributes = {
        'value': 0,
    }

    def get_type(self, state):
        # TODO: decide based on suffixes
        return state.types.get_type('int')

    def generate_code(self, state):
        # TODO: handle suffixes
        # TODO: hex and oct representations
        register = self.allocate_result_register(state)
        return "%s = add %s 0, %s" % (register,
                                      self.get_type(state).llvm_type,
                                      str(self.value))
