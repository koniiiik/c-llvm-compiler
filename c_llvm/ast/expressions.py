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
            code = left_result.type.cast_to_float(left_result, None, state, self)
            left_result = state.pop_result()
            return code, left_result, right_result
        return "", left_result, right_result

    @classmethod
    def common_type(self, left_type, right_type):
        if left_type.priority > right_type.priority:
            return left_type
        return right_type


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
        left_bool_cast = left_result.type.cast_to_bool(left_result, None,
                                                       state, self)
        left_bool_result = state.pop_result()

        right_code = self.right.generate_code(state)
        right_result = state.pop_result()
        right_bool_cast = right_result.type.cast_to_bool(right_result, None,
                                                         state, self)
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

            register = state.get_tmp_register()
            add = "%s = add %s %s, %s" % (
                register, left_result.type.llvm_type, left_result.value,
                right_result.value
            )
            state.set_result(register, left_result.type)
        else:
            instance.log_error(state, "incompatible types")
            raise CompilationError()
        return add

    def generate_code(self, state):
        left_code = self.left.generate_code(state)
        left_result = state.pop_result()
        right_code = self.right.generate_code(state)
        right_result = state.pop_result()
        if right_result is None or left_result is None:
            return ""

        if right_result.is_constant and left_result.is_constant:
            state.set_result(right_result.value + left_result.value,
                    self.common_type(left_result.type, right_result.type), True)
            return ""

        try:
            add = self.perform_operation(self, state, left_result,
                                         right_result)
        except CompilationError:
            return ""

        return self.template % {
            'left_code': left_code,
            'right_code': right_code,
            'add': add,
        }


class SubtractionExpressionNode(BinaryExpressionNode):
    template = """
%(left_code)s
%(right_code)s
%(subtract)s
"""

    @classmethod
    def perform_operation(cls, instance, state, left_result, right_result):
        if (left_result.type.is_pointer and
                right_result.type.is_integer):
            raise NotImplementedError
        elif (left_result.type.is_pointer and
                right_result.type.is_pointer):
            raise NotImplementedError
        elif (left_result.type.is_arithmetic and
                right_result.type.is_arithmetic):
            # TODO: casts
            # TODO: floats
            register = state.get_tmp_register()
            add = "%s = sub %s %s, %s" % (
                register, left_result.type.llvm_type, left_result.value,
                right_result.value
            )
            state.set_result(register, left_result.type)
        else:
            instance.log_error(state, "incompatible types")
            raise CompilationError()
        return add

    def generate_code(self, state):
        left_code = self.left.generate_code(state)
        left_result = state.pop_result()
        right_code = self.right.generate_code(state)
        right_result = state.pop_result()
        if right_result is None or left_result is None:
            return ""

        if right_result.is_constant and left_result.is_constant:
            state.set_result(left_result.value - right_result.value,
                    self.common_type(left_result.type, right_result.type), True)
            return ""

        try:
            subtract = self.perform_operation(self, state, left_result,
                                              right_result)
        except CompilationError:
            return ""

        return self.template % {
            'left_code': left_code,
            'right_code': right_code,
            'subtract': subtract,
        }


class MultiplicativeExpressionNode(BinaryExpressionNode):
    pass


class CastExpressionNode(ExpressionNode):
    def toString(self):
        return ""


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
        state.set_result(register, value.type)
        return "%s\n%s = xor %s %s, -1" % (operand_code, register,
                                           value.type.llvm_type,
                                           value.value)


class LogicalNegationExpressionNode(ExpressionNode):
    pass


class FunctionCallNode(ExpressionNode):
    child_attributes = {
        'function': 0,
        'arguments': 1,
    }
    template = """
%(arg_eval_codes)s
%(arg_cast_codes)s
%(register)s = call %(type)s* %(name)s(%(arg_values)s)
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

        register = state.get_tmp_register()

        return self.template % {
            'arg_eval_codes': '\n'.join(arg_code),
            'arg_cast_codes': '',
            'register': register,
            'type': function.type.llvm_type,
            'name': function.value,
            'arg_values': ', '.join(
                '%(type)s %(val)s' % {
                    'type': result.type.llvm_type,
                    'val': result.value,
                } for result in arg_results
            ),
        }


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
        # TODO: handle suffixes
        upper = str(self).upper()
        while upper[-1] in ('L', 'F'):
            upper = upper[:-1]
        state.set_result(value=float(upper),
                         type=state.types.get_type('float'),
                         is_constant=True)
        return ""


class CharConstantNode(ExpressionNode):
    pass


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
    child_attributes = {
        'value': 0,
    }
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
        '*=': None,
        '/=': None,
        '%=': None,
        '+=': AdditionExpressionNode.perform_operation,
        '-=': SubtractionExpressionNode.perform_operation,
        '<<=': None,
        '>>=': None,
        '&=': None,
        '^=': None,
        '|=': None,
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
            # TODO: remove this
            if func is None:
                raise NotImplementedError
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
            assignment = state.types.cast_value(rvalue_result, lvalue_result, state, self)
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
