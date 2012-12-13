from c_llvm.ast.base import AstNode
from c_llvm.variables import Variable


class DeclarationNode(AstNode):
    child_attributes = {
        'var_type': 0,
        'declarator': 1,
    }

    def generate_code(self, state):
        # TODO: check redeclarations
        is_global = state.is_global()
        state.declaration_stack.append(str(self.var_type))
        type = self.declarator.get_type(state)
        identifier = self.declarator.get_identifier()
        state.declaration_stack.pop()
        if is_global:
            register = '@%s' % (identifier,)
        else:
            register = state.get_var_register(identifier)
        var = Variable(type=type, name=identifier, register=register,
                       is_global=is_global)
        state.symbols[identifier] = var
        if is_global:
            return "%(register)s = global %(type)s %(value)s" % {
                'register': var.register,
                'type': var.type.llvm_type,
                'value': var.type.default_value,
            }
        return "%(register)s = alloca %(type)s" % {
            'register': var.register,
            'type': var.type.llvm_type,
        }

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
        return state.types.get_type(self.get_type_key(state))

    def get_type_key(self, state):
        """
        Returns the key of this type used to access the actual Type
        instance in the type library. This method should ensure that the
        type gets registered in the library.
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

    def get_type_key(self, state):
        return state.declaration_stack[-1]

    def get_identifier(self):
        return str(self.identifier)


class PointerDeclaratorNode(DeclaratorNode):
    def get_type_key(self, state):
        child_key = self.inner_declarator.get_type_key(state)
        key = "%s*" % (child_key,)
        try:
            state.types.get_type(key)
        except KeyError:
            child_type = state.types.get_type(child_key)
            state.types.set_type(key, PointerType(child_type))
        return key
