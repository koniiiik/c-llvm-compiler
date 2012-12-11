from c_llvm.ast.base import AstNode


class ExpressionNode(AstNode):
    """
    Common superclass for all expression type AST nodes.
    """
    pass


class BinaryExpressionNode(ExpressionNode):
    child_attributes = {
        'left': 0,
        'right': 1,
    }


class UnaryExpressionNode(ExpressionNode):
    child_attributes = {
        'operand': 0,
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


class AdditionExpressionNode(BinaryExpressionNode):
    def generate_code(self, state):
        return ""


class SubtractionExpressionNode(BinaryExpressionNode):
    def generate_code(self, state):
        return ""


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


class BitwiseNegationExpressionNode(UnaryExpressionNode):
    def generate_code(self, state):
        operand_code = self.operand.generate_code(state)
        value = state.pop_result()
        if value is None:
            # There was a compilation error somewhere down the line.
            return ""

        if (not value.type.is_integer):
            self.log_error(state, "operand is not integer")
            return ""
        if value.is_constant:
            state.set_result(~value.value, value.type, True)
            return ""
        register = state.get_tmp_register()
        state.set_result(register, value.type, False)
        return "%s\n%s = xor %s %s, -1" % (operand_code, register,
                                           value.type.llvm_type,
                                           value.value)


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
        register = state.get_tmp_register()
        state.set_result(value=register, type=var.type, is_constant=False)
        return "%s = load %s* %s" % (register, var.type.llvm_type,
                                     var.register)


class IntegerConstantNode(ExpressionNode):
    child_attributes = {
        'value': 0,
    }

    def generate_code(self, state):
        # TODO: handle suffixes
        # TODO: hex and oct representations
        upper = str(self.value).upper()
        is_unsigned = 'U' in upper
        while not upper.isdigit():
            upper = upper[:-1]
        # Thanks to base=0 this parses hex and oct literals as well.
        value = int(upper, base=0)
        state.set_result(value=value,
                         type=state.types.get_type('int'),
                         is_constant=True)
        return ""
