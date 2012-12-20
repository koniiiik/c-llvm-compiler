from c_llvm.ast.base import AstNode
from c_llvm.exceptions import CompilationError


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

    @classmethod
    def cast_if_necessary(self, left_result, right_result, state):
        # assuming for both type.is_arithmetic is true (int or float)
        if right_result.type.is_integer:
            left_result, right_result = right_result, left_result

        if (left_result.type.is_integer and
                right_result.type.is_float):
            code = left_result.type.cast_to_float(left_result, state)
            left_result = state.pop_result()
            return code, left_result, right_result
        return "", left_result, right_result

    @classmethod
    def common_type(self, left_type, right_type):
        if left_type.priority > right_type.priority:
            return left_type
        return right_type


class BinaryArithmeticExpressionNode(BinaryExpressionNode):
    template = """
%(left_code)s
%(right_code)s
%(operation_code)s
"""

    def generate_code(self, state):
        left_code = self.left.generate_code(state)
        left_result = state.pop_result()
        right_code = self.right.generate_code(state)
        right_result = state.pop_result()
        if right_result is None or left_result is None:
            return "Surely this does not happen :-)"

        if right_result.is_constant and left_result.is_constant:
            state.set_result(
                    self.operation(left_result.value, right_result.value),
                    self.common_type(left_result.type, right_result.type),
                    True)
            return ""

        try:
            operation_code = self.perform_operation(
                    self, state, left_result, right_result)
        except CompilationError:
            # fake the result, otherwise AssignmentExpressionNode
            # can't handle the situation
            state.push_result(left_result)
            return ""

        return self.template % {
            'left_code': left_code,
            'right_code': right_code,
            'operation_code': operation_code,
        }


class UnaryExpressionNode(ExpressionNode):
    child_attributes = {
        'operand': 0,
    }


class CommaOperatorNode(BinaryExpressionNode):
    template = """
%(left_code)s
%(right_code)s
"""

    def generate_code(self, state):
        left_code = self.left.generate_code(state)
        right_code = self.right.generate_code(state)
        # right's result expression should stay in the state I hope
        return self.template % {
                'left_code': left_code,
                'right_code': right_code,
            }


class ConditionalExpressionNode(ExpressionNode):
    pass


class LogicalExpressionNode(BinaryExpressionNode):
    template = """
%(left_code)s
%(left_bool_cast)s
br i1 %(left_bool_value)s, label %%%(left_true_target)s, label %%%(left_false_target)s
%(right_label)s:
%(right_code)s
%(right_bool_cast)s
br i1 %(right_bool_value)s, label %%%(right_true_target)s, label %%%(right_false_target)s
%(is_true_label)s:
br label %%%(end_label)s
%(is_false_label)s:
br label %%%(end_label)s
%(end_label)s:
%(result_register)s = phi %(result_type)s [0, %%%(is_false_label)s], [1, %%%(is_true_label)s]
"""

    def generate_code(self, state):
        left_code = self.left.generate_code(state)
        left_result = state.pop_result()
        left_bool_cast = left_result.type.cast_to_bool(left_result, state)
        left_bool_result = state.pop_result()

        right_code = self.right.generate_code(state)
        right_result = state.pop_result()
        right_bool_cast = right_result.type.cast_to_bool(right_result, state)
        right_bool_result = state.pop_result()

        result_register = state.get_tmp_register()
        state.set_result(result_register, state.types.get_type('int'))

        right_label = state.get_label()
        is_true_label = state.get_label()
        is_false_label = state.get_label()
        end_label = state.get_label()
        context = {
            'left_code': left_code,
            'left_bool_cast': left_bool_cast,
            'left_bool_value': left_bool_result.value,
            'right_label': right_label,
            'right_code': right_code,
            'right_bool_cast': right_bool_cast,
            'right_bool_value': right_bool_result.value,
            'is_true_label': is_true_label,
            'is_false_label': is_false_label,
            'end_label': end_label,
            'result_register': result_register,
            'result_type': state.types.get_type('int').llvm_type,
        }

        if str(self.getToken()) == '||':
            context.update(left_true_target=is_true_label,
                           left_false_target=right_label,
                           right_true_target=is_true_label,
                           right_false_target=is_false_label)
        else:
            context.update(left_true_target=right_label,
                           left_false_target=is_false_label,
                           right_true_target=is_true_label,
                           right_false_target=is_false_label)

        return self.template % context


class BitwiseOrExpressionNode(BinaryArithmeticExpressionNode):
    def operation(self, left, right):
        return left | right

    @classmethod
    def perform_operation(cls, instance, state, left_result, right_result):
        if ((not left_result.type.is_integer) or
                (not right_result.type.is_integer)):
            instance.log_error(state, "|'s operands need to be integer type")
            raise CompilationError()
        register = state.get_tmp_register()
        operation_code = "%s = or %s %s, %s" % (
            register, left_result.type.llvm_type,
            left_result.value, right_result.value
        )
        state.set_result(register, left_result.type)
        return operation_code


class BitwiseXorExpressionNode(BinaryArithmeticExpressionNode):
    def operation(self, left, right):
        return left ^ right

    @classmethod
    def perform_operation(cls, instance, state, left_result, right_result):
        if ((not left_result.type.is_integer) or
                (not right_result.type.is_integer)):
            instance.log_error(state, "^'s operands need to be integer type")
            raise CompilationError()
        register = state.get_tmp_register()
        operation_code = "%s = xor %s %s, %s" % (
            register, left_result.type.llvm_type,
            left_result.value, right_result.value
        )
        state.set_result(register, left_result.type)
        return operation_code


class BitwiseAndExpressionNode(BinaryArithmeticExpressionNode):
    def operation(self, left, right):
        return left & right

    @classmethod
    def perform_operation(cls, instance, state, left_result, right_result):
        if ((not left_result.type.is_integer) or
                (not right_result.type.is_integer)):
            instance.log_error(state, "&'s operands need to be integer type")
            raise CompilationError()
        register = state.get_tmp_register()
        operation_code = "%s = and %s %s, %s" % (
            register, left_result.type.llvm_type,
            left_result.value, right_result.value
        )
        state.set_result(register, left_result.type)
        return operation_code


class CompareExpressionNode(BinaryExpressionNode):
    template = """
%(left_code)s
%(right_code)s
%(operation_code)s
"""
    operands = {
        '<': ('slt', 'olt'),
        '>': ('sgt', 'ogt'),
        '<=': ('sle', 'ole'),
        '>=': ('sge', 'oge'),
        '==': ('eq', 'oeq'),
        '!=': ('ne', 'one'),
    }

    def operation(self, left, right):
        operations = {
            '<': int(left < right),
            '>': int(left > right),
            '<=': int(left <= right),
            '>=': int(left >= right),
            '==': int(left == right),
            '!=': int(left != right),
        }
        return operations[str(self)]

    def generate_code(self, state):
        left_code = self.left.generate_code(state)
        left_result = state.pop_result()
        right_code = self.right.generate_code(state)
        right_result = state.pop_result()
        if right_result is None or left_result is None:
            return "Surely this does not happen :-)"

        if right_result.is_constant and left_result.is_constant:
            state.set_result(
                    self.operation(left_result.value, right_result.value),
                    state.types.get_type('int'),
                    True)
            return ""

        if ((not left_result.type.is_scalar) or
                (not right_result.type.is_scalar)):
            instance.log_error(state, "operands need to be scalar type")
            return ""
        operation_code, left_result, right_result = self.cast_if_necessary(
                left_result, right_result, state)
        if operation_code != "":
            operation_code += "\n"

        if left_result.type.is_float:
            op = "fcmp" + " " + self.operands[str(self)][1]
        else:
            op = "icmp" + " " + self.operands[str(self)][0]
        tmp_register = state.get_tmp_register()
        operation_code += "%s = %s %s %s, %s\n" % (
            tmp_register, op, left_result.type.llvm_type,
            left_result.value, right_result.value
        )
        result_register = state.get_tmp_register()
        operation_code += "%s = zext i1 %s to i64" % (
            result_register, tmp_register
        )
        state.set_result(result_register, state.types.get_type('int'))
        return self.template % {
            'left_code': left_code,
            'right_code': right_code,
            'operation_code': operation_code,
        }


class ShiftLeftExpressionNode(BinaryArithmeticExpressionNode):
    def operation(self, left, right):
        return left << right

    @classmethod
    def perform_operation(cls, instance, state, left_result, right_result):
        if ((not left_result.type.is_integer) or
                (not right_result.type.is_integer)):
            instance.log_error(state, "<<'s operands need to be integer type")
            raise CompilationError()
        register = state.get_tmp_register()
        operation_code = "%s = shl %s %s, %s" % (
            register, left_result.type.llvm_type,
            left_result.value, right_result.value
        )
        state.set_result(register, left_result.type)
        return operation_code


class ShiftRightExpressionNode(BinaryArithmeticExpressionNode):
    def operation(self, left, right):
        return left >> right

    @classmethod
    def perform_operation(cls, instance, state, left_result, right_result):
        if ((not left_result.type.is_integer) or
                (not right_result.type.is_integer)):
            instance.log_error(state, ">>'s operands need to be integer type")
            raise CompilationError()
        register = state.get_tmp_register()
        operation_code = "%s = lshr %s %s, %s" % (
            register, left_result.type.llvm_type,
            left_result.value, right_result.value
        )
        state.set_result(register, left_result.type)
        return operation_code


class AdditionExpressionNode(BinaryArithmeticExpressionNode):
    def operation(self, left, right):
        return left + right

    @classmethod
    def perform_operation(cls, instance, state, left_result, right_result):
        if right_result.type.is_pointer:
            left_result, right_result = right_result, left_result

        if (left_result.type.is_pointer and
                right_result.type.is_integer):
            register = state.get_tmp_register()
            add = "%s = getelementptr %s %s, %s %s" % (
                register, left_result.type.llvm_type, left_result.value,
                right_result.type.llvm_type, right_result.value
            )
            state.set_result(register, left_result.type)
        elif (left_result.type.is_arithmetic and
                right_result.type.is_arithmetic):
            add, left_result, right_result = cls.cast_if_necessary(
                    left_result, right_result, state)
            if add != "":
                add += "\n"
            op = "add"
            if left_result.type.is_float:
                op = "fadd"
            register = state.get_tmp_register()
            add += "%s = %s %s %s, %s" % (
                register, op, left_result.type.llvm_type,
                left_result.value, right_result.value
            )
            state.set_result(register, left_result.type)
        else:
            instance.log_error(state, "incompatible types")
            raise CompilationError()
        return add


class SubtractionExpressionNode(BinaryArithmeticExpressionNode):
    def operation(self, left, right):
        return left - right

    @classmethod
    def perform_operation(cls, instance, state, left_result, right_result):
        if right_result.type.is_pointer:
            left_result, right_result = right_result, left_result

        if (left_result.type.is_pointer and
                right_result.type.is_integer):
            raise NotImplementedError
        elif (left_result.type.is_pointer and
                right_result.type.is_pointer):
            raise NotImplementedError
        elif (left_result.type.is_arithmetic and
                right_result.type.is_arithmetic):
            subtract, left_result, right_result = cls.cast_if_necessary(
                    left_result, right_result, state)
            if subtract != "":
                subtract += "\n"
            op = "sub"
            if left_result.type.is_float:
                op = "fsub"
            register = state.get_tmp_register()
            subtract += "%s = %s %s %s, %s" % (
                register, op, left_result.type.llvm_type,
                left_result.value, right_result.value
            )
            state.set_result(register, left_result.type)
        else:
            instance.log_error(state, "incompatible types")
            raise CompilationError()
        return subtract


class MultiplicationExpressionNode(BinaryArithmeticExpressionNode):
    def operation(self, left, right):
        return left * right

    @classmethod
    def perform_operation(cls, instance, state, left_result, right_result):
        if ((not left_result.type.is_arithmetic) or
                (not right_result.type.is_arithmetic)):
            instance.log_error(state, "operands need to be arithmetic type")
            raise CompilationError()
        operation_code, left_result, right_result = cls.cast_if_necessary(
                left_result, right_result, state)
        if operation_code != "":
            operation_code += "\n"
        op = "mul"
        if left_result.type.is_float:
            op = "fmul"
        register = state.get_tmp_register()
        operation_code += "%s = %s %s %s, %s" % (
            register, op, left_result.type.llvm_type,
            left_result.value, right_result.value
        )
        state.set_result(register, left_result.type)
        return operation_code


class DivisionExpressionNode(BinaryArithmeticExpressionNode):
    def operation(self, left, right):
        return left / right

    @classmethod
    def perform_operation(cls, instance, state, left_result, right_result):
        if ((not left_result.type.is_arithmetic) or
                (not right_result.type.is_arithmetic)):
            instance.log_error(state, "operands need to be arithmetic type")
            raise CompilationError()
        operation_code, left_result, right_result = cls.cast_if_necessary(
                left_result, right_result, state)
        if operation_code != "":
            operation_code += "\n"
        op = "sdiv"
        if left_result.type.is_float:
            op = "fdiv"
        register = state.get_tmp_register()
        operation_code += "%s = %s %s %s, %s" % (
            register, op, left_result.type.llvm_type,
            left_result.value, right_result.value
        )
        state.set_result(register, left_result.type)
        return operation_code


class RemainderExpressionNode(BinaryArithmeticExpressionNode):
    def operation(self, left, right):
        return left % right

    @classmethod
    def perform_operation(cls, instance, state, left_result, right_result):
        if ((not left_result.type.is_integer) or
                (not right_result.type.is_integer)):
            instance.log_error(state, "%'s operands need to be integer type")
            raise CompilationError()
        register = state.get_tmp_register()
        operation_code = "%s = srem %s %s, %s" % (
            register, left_result.type.llvm_type,
            left_result.value, right_result.value
        )
        state.set_result(register, left_result.type)
        return operation_code


class CastExpressionNode(BinaryExpressionNode):
    template = """
%(operand_code)s
%(cast_code)s
"""

    def generate_code(self, state):
        new_type = state.types.get_type(str(self.left))
        operand_code = self.right.generate_code(state)
        value = state.pop_result()
        if value.is_constant:
            # let's hope we know only two types of constants
            if new_type.internal_type == 'int':
                new_value = int(value.value)
            else:
                new_value = float(value.value)
            state.set_result(new_value, new_type, True)
            return ""

        cast_code = state.types.cast_value(value, state, new_type)
        return self.template % {
                'operand_code': operand_code,
                'cast_code': cast_code,
            }


class DereferenceExpressionNode(ExpressionNode):
    child_attributes = {
        'expression': 0,
    }
    template = """
%(expr_code)s
%(register)s = load %(type)s %(pointer)s
"""
    template_array = """
%(expr_code)s
%(register)s = getelementptr %(type)s %(pointer)s, i64 0, i64 0
"""

    def generate_code(self, state):
        expr_code = self.expression.generate_code(state)
        expr_result = state.pop_result()
        expr_type = expr_result.type
        if not expr_type.is_pointer:
            self.log_error(state, "dereferencing a non-pointer value")
            return ""
        register = state.get_tmp_register()

        if expr_type.target_type.is_array:
            template = self.template_array
            result_type = state.types.get_pointer_type(expr_type.target_type.target_type)
            state.set_result(register, result_type)
        else:
            template = self.template
            state.set_result(register, expr_result.type.target_type,
                             pointer=expr_result.value)

        return template % {
            'expr_code': expr_code,
            'register': register,
            'type': expr_result.type.llvm_type,
            'pointer': expr_result.value,
        }


class AddressExpressionNode(ExpressionNode):
    child_attributes = {
        'expression': 0,
    }

    def generate_code(self, state):
        expr_code = self.expression.generate_code(state)
        expr_result = state.pop_result()
        if not expr_result.pointer:
            self.log_error(state, "address of a non-lvalue requested")
            return ""
        state.set_result(expr_result.pointer,
                         state.types.get_pointer_type(expr_result.type))
        return expr_code


class UnaryArithmeticExpressionNode(UnaryExpressionNode):
    template = """
%(operand_code)s
%(result_register)s = %(cmp_instruction)s %(type)s %(value)s, %(cmp_value)s
"""

    def generate_code(self, state):
        operand_code = self.operand.generate_code(state)
        value = state.pop_result()
        if (not value.type.is_arithmetic):
            self.log_error(state, "operand is not arithmetic")
            return ""
        if value.is_constant:
            state.set_result(int(str(self) + "1") * value.value,
                    value.type, True)
            return ""
        if str(self) == '+':
            state.push_result(value)
            return "%s" % operand_code
        if value.type.is_float:
            cmp_instruction = "fmul"
            cmp_value = "-1.0"
        else:
            cmp_instruction = "mul"
            cmp_value = "-1"
        result_register = state.get_tmp_register()
        state.set_result(result_register, value.type)
        return self.template % {
                'operand_code': operand_code,
                'cmp_instruction': cmp_instruction,
                'cmp_value': cmp_value,
                'type': value.type.llvm_type,
                'value': value.value,
                'result_register': result_register,
            }


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
        state.set_result(register, value.type)
        return "%s\n%s = xor %s %s, -1" % (operand_code, register,
                                           value.type.llvm_type,
                                           value.value)


class LogicalNegationExpressionNode(UnaryExpressionNode):
    template = """
%(operand_code)s
%(tmp_register)s = %(cmp_instruction)s %(type)s %(value)s, %(cmp_value)s
%(result_register)s = zext i1 %(tmp_register)s to i64
"""

    def generate_code(self, state):
        operand_code = self.operand.generate_code(state)
        value = state.pop_result()
        if (not value.type.is_scalar):
            self.log_error(state, "operand is not scalar")
            return ""
        if value.is_constant:
            state.set_result(int(not value.value),
                    state.types.get_type('int'), True)
            return ""
        if value.type.is_float:
            cmp_instruction = "fcmp one"
            cmp_value = "0.0"
        else:
            cmp_instruction = "icmp ne"
            cmp_value = "0"
        tmp_register = state.get_tmp_register()
        result_register = state.get_tmp_register()
        state.set_result(result_register, state.types.get_type('int'))
        return self.template % {
                'operand_code': operand_code,
                'tmp_register': tmp_register,
                'cmp_instruction': cmp_instruction,
                'cmp_value': cmp_value,
                'type': value.type.llvm_type,
                'value': value.value,
                'result_register': result_register,
            }


class FunctionCallNode(ExpressionNode):
    child_attributes = {
        'function': 0,
        'arguments': 1,
    }
    template_nonvoid = """
%(arg_eval_codes)s
%(arg_cast_codes)s
%(register)s = call %(type)s* %(name)s(%(arg_values)s)
"""
    template_void = """
%(arg_eval_codes)s
%(arg_cast_codes)s
call %(type)s* %(name)s(%(arg_values)s)
"""

    def generate_code(self, state):
        function_code = self.function.generate_code(state)
        function = state.pop_result()

        if not function.type.is_function:
            self.log_error(state, "attempting to call a non-function")
            return ""

        arg_code, arg_results = [], []
        for argument in self.arguments.children:
            arg_code.append(argument.generate_code(state))
            arg_results.append(state.pop_result())

        if len(function.type.arg_types) > len(arg_results):
            self.log_error(state, "not enough arguments given")
            return ""
        elif (len(function.type.arg_types) < len(arg_results) and
                not function.type.variable_args):
            self.log_error(state, "too many arguments given")
            return ""

        for expected_type, result in zip(function.type.arg_types,
                                         arg_results):
            # TODO: perform casts
            if result.type is not expected_type:
                raise NotImplementedError

        if function.type.return_type.is_void:
            template = self.template_void
        else:
            template = self.template_nonvoid

        register = state.get_tmp_register()
        state.set_result(register, function.type.return_type)

        return template % {
            'arg_eval_codes': '\n'.join(arg_code),
            'arg_cast_codes': '',
            'register': register,
            'type': function.type.llvm_type,
            'name': function.pointer,
            'arg_values': ', '.join(
                '%(type)s %(val)s' % {
                    'type': result.type.llvm_type,
                    'val': result.value,
                } for result in arg_results
            ),
        }


class StructMemberExpressionNode(ExpressionNode):
    child_attributes = {
        'struct': 0,
        'member': 1,
    }
    template_lvalue = """
%(struct_code)s
%(result_ptr)s = getelementptr %(struct_type)s* %(struct_ptr)s, i32 0, i32 %(index)d
%(result_reg)s = load %(result_type)s* %(result_ptr)s
"""
    template_non_lvalue = """
%(struct_code)s
%(result_reg)s = extractvalue %(struct_type)s %(struct_val)s, %(index)d
"""

    def generate_code(self, state):
        struct_code = self.struct.generate_code(state)
        struct_result = state.pop_result()
        if not struct_result.type.is_struct:
            self.log_error(state, "accessing a member on a non-struct expression")
            return ""

        member_name = str(self.member)
        member_index, member_type = struct_result.type.get_member(member_name)

        if struct_result.pointer:
            pointer_reg = state.get_tmp_register()
            result_reg = state.get_tmp_register()
            state.set_result(result_reg, member_type, pointer=pointer_reg)
            template = self.template_lvalue
        else:
            result_reg = state.get_tmp_register()
            pointer_reg = ""
            state.set_result(result_reg, member_type)
            template = self.template_non_lvalue

        return template % {
            'struct_code': struct_code,
            'result_ptr': pointer_reg,
            'struct_type': struct_result.type.llvm_type,
            'struct_ptr': struct_result.pointer,
            'index': member_index,
            'result_reg': result_reg,
            'result_type': member_type.llvm_type,
            'struct_val': struct_result.value,
        }


class VariableExpressionNode(ExpressionNode):
    def generate_code(self, state):
        try:
            var = state.symbols[str(self)]
        except KeyError:
            self.log_error(state, "unknown variable: %s" % (str(self),))
            print(state.symbols.dicts)
            return ""

        if var.type.is_function:
            state.set_result(value=None, type=var.type,
                             pointer=var.register)
            return ""

        register = state.get_tmp_register()

        if var.type.is_array:
            # We want to return a pointer to the first element. This is
            # not an lvalue, however, the target is (unless it is an array
            # as well).
            ptr_type = state.types.get_pointer_type(var.type.target_type)
            state.set_result(value=register, type=ptr_type)
            return "%s = getelementptr %s* %s, i64 0, i64 0" % (
                register, var.type.llvm_type, var.register
            )

        state.set_result(value=register, type=var.type,
                         pointer=var.register)
        return "%s = load %s* %s" % (register, var.type.llvm_type,
                                     var.register)


class IntegerConstantNode(ExpressionNode):
    def generate_code(self, state):
        # TODO: handle suffixes
        # TODO: hex and oct representations
        upper = str(self).upper()
        is_unsigned = 'U' in upper
        while not upper.isdigit():
            upper = upper[:-1]
        # Thanks to base=0 this parses hex and oct literals as well.
        value = int(upper, base=0)
        state.set_result(value=value,
                         type=state.types.get_type('int'),
                         is_constant=True)
        return ""


class FloatConstantNode(ExpressionNode):
    def generate_code(self, state):
        upper = str(self).upper()
        while upper[-1] in ('L', 'F'):
            upper = upper[:-1]
        state.set_result(value=float(upper),
                         type=state.types.get_type('float'),
                         is_constant=True)
        return ""


class CharConstantNode(ExpressionNode):
    def generate_code(self, state):
        char = str(self)
        char = char[:-1]
        if char[1] == '\\':
            if char[2] == 'x':
                value = int(char[3:],base=16)
            elif char[2:].isdigit():
                value = int(char[2:],base=8)
            else:
                value = char_escape_seqs[char[2]]
        else:
            value = ord(char[1])
        state.set_result(value,
                         type=state.types.get_type('char'),
                         is_constant=True)
        return ""


char_escape_seqs = {
    "'": ord("'"),
    '"': ord('"'),
    '\\': ord('\\'),
    '?': ord('?'),
    'a': ord('\a'),
    'b': ord('\b'),
    'f': ord('\f'),
    'n': ord('\n'),
    'r': ord('\r'),
    't': ord('\t'),
    'v': ord('\v'),
}


def unescape_octal_char_constant(char):
    return int(char, base=8) % 256


def unescape_hex_char_constant(char):
    return int(char, base=16) % 256


class StringLiteralNode(ExpressionNode):
    template = """
%(local_register)s = getelementptr %(array_type)s* %(global_register)s, i64 0, i64 0
"""
    declaration_template = """
%(register)s = global %(type)s c"%(content)s"
"""

    def get_length_content(self, state):
        res = []
        it = iter(str(self)[1:]) # We keep the ending quote mark as sentinel.
        buf = next(it)
        try:
            while True:
                if buf == '\\':
                    buf = next(it)
                    if buf == 'x':
                        hex_num = []
                        buf = next(it)
                        while ('0' <= buf <= '9'
                                or 'a' <= buf <= 'f'
                                or 'A' <= buf <= 'F'):
                            hex_num.append(buf)
                            buf = next(it)
                        res.append(unescape_hex_char_constant(''.join(hex_num)))
                    elif '0' <= buf <= '7':
                        oct_num = []
                        while '0' <= buf <= '7':
                            oct_num.append(buf)
                            buf = next(it)
                        res.append(unescape_octal_char_constant(''.join(oct_num)))
                    else:
                        res.append(char_escape_seqs[buf])
                        buf = next(it)
                else:
                    res.append(ord(buf))
                    buf = next(it)
        except StopIteration as e:
            pass
        # Replace the ending sentinel with the zero terminator.
        res[-1] = 0
        length = len(res)
        res = ''.join('\\%02X' % (byte,) for byte in res)
        return length, res

    def generate_code(self, state):
        register = "@string.%d" % (state._get_next_number(),)
        length, content = self.get_length_content(state)
        char_type = state.types.get_type('char')
        array_type = state.types.get_array_type(char_type, length)
        ptr_type = state.types.get_pointer_type(char_type)
        result_register = state.get_tmp_register()
        state.set_result(result_register, ptr_type)
        declaration = self.declaration_template % {
            'register': register,
            'type': array_type.llvm_type,
            'content': content,
        }
        state.global_declarations.append(declaration)
        return self.template % {
            'local_register': result_register,
            'array_type': array_type.llvm_type,
            'global_register': register,
        }


class AssignmentExpressionNode(ExpressionNode):
    child_attributes = {
        'op': 0,
        'lvalue': 1,
        'rvalue': 2,
    }
    template = """
%(lvalue_code)s
%(rvalue_code)s
%(operation)s
%(assignment)s
"""
    compound_operations = {
        '*=': MultiplicationExpressionNode.perform_operation,
        '/=': DivisionExpressionNode.perform_operation,
        '%=': RemainderExpressionNode.perform_operation,
        '+=': AdditionExpressionNode.perform_operation,
        '-=': SubtractionExpressionNode.perform_operation,
        '<<=': ShiftLeftExpressionNode.perform_operation,
        '>>=': ShiftRightExpressionNode.perform_operation,
        '&=': BitwiseAndExpressionNode.perform_operation,
        '^=': BitwiseXorExpressionNode.perform_operation,
        '|=': BitwiseOrExpressionNode.perform_operation,
    }

    def generate_code(self, state):
        lvalue_code = self.lvalue.generate_code(state)
        lvalue_result = state.pop_result()
        rvalue_code = self.rvalue.generate_code(state)
        rvalue_result = state.pop_result()
        if not lvalue_result.pointer:
            self.log_error(state, "not an lvalue")
            return ""
        if str(self.op) in self.compound_operations:
            func = self.compound_operations[str(self.op)]
            try:
                operation_code = func(self, state, lvalue_result,
                                      rvalue_result)
            except CompilationError:
                return ""
            rvalue_result = state.pop_result()
        else:
            operation_code = ""

        # TODO: check types and cast for pointers
        assignment = ""
        if not lvalue_result.type.is_pointer:
            assignment = state.types.cast_value(rvalue_result, state, lvalue_result.type)
            rvalue_result = state.pop_result()

        if assignment != "":
            assignment += "\n"

        assignment += "store %s %s, %s* %s" % (
            rvalue_result.type.llvm_type, rvalue_result.value,
            lvalue_result.type.llvm_type, lvalue_result.pointer,
        )
        state.set_result(rvalue_result.value, rvalue_result.type,
                         rvalue_result.is_constant)
        return self.template % {
            'lvalue_code': lvalue_code,
            'rvalue_code': rvalue_code,
            'operation': operation_code,
            'assignment': assignment,
        }

    def toString(self):
        return ""
