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
    child_attributes = {
        'op': 0,
        'lvalue': 1,
        'rvalue': 2,
    }
    template = """
%(lvalue_code)s
%(rvalue_code)s
%(assignment)s
"""

    def generate_code(self, state):
        lvalue_code = self.lvalue.generate_code(state)
        lvalue_result = state.pop_result()
        rvalue_code = self.rvalue.generate_code(state)
        rvalue_result = state.pop_result()
        if not lvalue_result.pointer:
            self.log_error(state, "not an lvalue")
            return ""
        # TODO: check types and cast
        # TODO: compound assignments
        assignment = "store %s %s, %s* %s" % (
            rvalue_result.type.llvm_type, rvalue_result.value,
            lvalue_result.type.llvm_type, lvalue_result.pointer,
        )
        state.set_result(rvalue_result.value, rvalue_result.type,
                         rvalue_result.is_constant)
        return self.template % {
            'lvalue_code': lvalue_code,
            'rvalue_code': rvalue_code,
            'assignment': assignment,
        }

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
    template = """
%(left_code)s
%(right_code)s
%(add)s
"""

    def generate_code(self, state):
        left_code = self.left.generate_code(state)
        left_result = state.pop_result()
        right_code = self.right.generate_code(state)
        right_result = state.pop_result()
        if right_result is None or left_result is None:
            return ""
        if right_result.type.is_pointer:
            left_result, right_result = right_result, left_result
            left_code, right_code = right_code, left_code

        if (left_result.type.is_pointer and
                right_result.type.is_integer):
            raise NotImplementedError
        elif (left_result.type.is_arithmetic and
                right_result.type.is_arithmetic):
            # TODO: casts
            # TODO: floats
            register = state.get_tmp_register()
            add = "%s = add %s %s, %s" % (
                register, left_result.type.llvm_type, left_result.value,
                right_result.value
            )
            state.set_result(register, left_result.type, False)
        else:
            self.log_error(state, "incompatible types")
            return ""

        return self.template % {
            'left_code': left_code,
            'right_code': right_code,
            'add': add,
        }


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
        state.set_result(value=register, type=var.type, is_constant=False,
                         pointer=var.register)
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
