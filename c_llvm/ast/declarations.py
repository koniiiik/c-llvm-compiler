from c_llvm.ast.base import AstNode
from c_llvm.types import PointerType
from c_llvm.variables import Variable


class DeclarationNode(AstNode):
    child_attributes = {
        'var_type': 0,
        'declarator': 1,
    }

    def generate_code(self, state):
        # TODO: check redeclarations
        is_global = state.is_global()
        state.declaration_stack.append(state.types.get_type(str(self.var_type)))
        type = self.declarator.get_type(state)
        identifier = self.declarator.get_identifier()
        state.declaration_stack.pop()

        if is_global:
            register = '@%s' % (identifier,)
        else:
            register = state.get_var_register(identifier)
        var = Variable(type=type, name=identifier, register=register,
                       is_global=is_global)

        if type.is_function:
            if not is_global:
                self.log_error(state, "can't declare a non-global function")
            declaration = "declare %(ret_type)s %(register)s%(arg_types)s" % {
                'ret_type': type.return_type.llvm_type,
                'register': register,
                'arg_types': type.arg_types_str,
            }
        elif is_global:
            declaration = "%(register)s = global %(type)s %(value)s" % {
                'register': var.register,
                'type': var.type.llvm_type,
                'value': var.type.default_value,
            }
        else:
            declaration = "%(register)s = alloca %(type)s" % {
                'register': var.register,
                'type': var.type.llvm_type,
            }

        state.symbols[identifier] = var
        return declaration

    def toString(self):
        return "declaration"

    def toStringTree(self):
        return "%s\n" % (super(DeclarationNode, self).toStringTree(),)


class FunctionDefinitionNode(AstNode):
    child_attributes = {
        'return_type': 0,
        'name': 1,
        'body': -1,
    }
    template = """
define %(type)s @%(name)s(%(args)s)
{
%(contents)s
%(return)s
}
"""
    ret_template = """
%(register1)s = alloca %(type)s
%(register2)s = load %(type)s* %(register1)s
ret %(type)s %(register2)s
"""

    def generate_code(self, state):
        # TODO: Add the function to the symbol table.
        # TODO: Verify that the function isn't already defined.
        type = state.types.get_type(str(self.return_type))
        state.return_type = type
        if type.is_void:
            ret_statement = "ret void"
        else:
            ret_statement = self.ret_template % {
                'type': type.llvm_type,
                'register1': state.get_tmp_register(),
                'register2': state.get_tmp_register(),
            }
        result = self.template % {
            'type': type.llvm_type,
            'name': str(self.name),
            'args': '', # TODO: use the actual args
            'contents': self.body.generate_code(state),
            'return': ret_statement,
        }
        state.return_type = None
        return result

    def toString(self):
        return "function definition"

    def toStringTree(self):
        return "%s\n" % (super(FunctionDefinitionNode, self).toStringTree(),)


class DeclaratorNode(AstNode):
    child_attributes = {
        'inner_declarator': 0,
    }

    def get_type(self, state):
        """
        Returns the Type instance of this declarator.
        """
        raise NotImplementedError

    def get_identifier(self):
        """
        Drills down through all levels of pointer and array specifiers to
        the identifier.
        """
        return self.inner_declarator.get_identifier()


class IdentifierDeclaratorNode(DeclaratorNode):
    child_attributes = {
        'identifier': 0,
    }

    def get_type(self, state):
        return state.declaration_stack[-1]

    def get_identifier(self):
        return str(self.identifier)


class PointerDeclaratorNode(DeclaratorNode):
    def get_type(self, state):
        child_type = self.inner_declarator.get_type(state)
        return state.types.get_pointer_type(child_type)


class FunctionDeclaratorNode(DeclaratorNode):
    child_attributes = {
        'inner_declarator': 0,
        'arg_list': 1,
    }

    def get_type(self, state):
        return_type = self.inner_declarator.get_type(state)
        if return_type.is_function:
            self.log_error(state, 'a function cannot return a function')
        if return_type.is_array:
            self.log_error(state, 'a function cannot return an array')
        arg_list = self.arg_list.children
        variable_arguments = len(arg_list) > 0 and str(arg_list[-1]) == '...'
        if variable_arguments:
            arg_list.pop()
        arg_types = [arg.get_type(state) for arg in arg_list]
        if len(arg_types) == 0:
            self.log_error(state, "incomplete function types not supported")
        elif (not variable_arguments and len(arg_types) == 1 and
                arg_types[0].is_void):
            arg_types = []

        for i, type in enumerate(arg_types):
            if type.is_void:
                arg_list[i].log_error(state, "function arguments can't be void")
            elif type.is_function:
                arg_types[i] = state.get_pointer_type(type)

        return state.types.get_function_type(return_type, arg_types,
                                             variable_arguments)


class ParameterListNode(AstNode):
    pass


class ParameterDeclarationNode(AstNode):
    child_attributes = {
        'type_specifier': 0,
        'declarator': 1,
    }

    def get_type(self, state):
        state.declaration_stack.append(state.types.get_type(str(self.type_specifier)))
        type = self.declarator.get_type(state)
        state.declaration_stack.pop()
        return type

    def get_identifier(self):
        return self.declarator.get_identifier()
