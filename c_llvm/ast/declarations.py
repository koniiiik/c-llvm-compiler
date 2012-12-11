from c_llvm.ast.base import AstNode
from c_llvm.variables import Variable


class DeclarationNode(AstNode):
    child_attributes = {
        'var_type': 0,
        'name': 1,
    }

    def generate_code(self, state):
        # TODO: check redeclarations
        is_global = state.is_global()
        type = state.types.get_type(str(self.var_type))
        if is_global:
            register = '@%s' % (self.name,)
        else:
            register = state.get_var_register(self.name)
        var = Variable(type=type, name=str(self.name), register=register,
                       is_global=is_global)
        state.symbols[str(self.name)] = var
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
        if type.is_void:
            ret_statement = "ret void"
        else:
            ret_statement = self.ret_template % {
                'type': type.llvm_type,
                'register1': state.get_tmp_register(),
                'register2': state.get_tmp_register(),
            }
        return self.template % {
            'type': type.llvm_type,
            'name': str(self.name),
            'args': '', # TODO: use the actual args
            'contents': self.body.generate_code(state),
            'return': ret_statement,
        }

    def toString(self):
        return "function definition"

    def toStringTree(self):
        return "%s\n" % (super(FunctionDefinitionNode, self).toStringTree(),)
