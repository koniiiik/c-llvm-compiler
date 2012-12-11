from c_llvm.ast.base import AstNode


class DeclarationNode(AstNode):
    def generate_code(self, state):
        return ""

    def toString(self):
        return "declaration"

    def toStringTree(self):
        return "%s\n" % (super(DeclarationNode, self).toStringTree(),)


class FunctionDefinitionNode(AstNode):
    template = """
define %(type)s @%(name)s(%(args)s)
{
%(contents)s
}
"""

    def generate_code(self, state):
        # TODO: Add the function to the symbol table.
        # TODO: Verify that the function isn't already defined.
        children = self.process_children(state)
        return self.template % {
            'type': state.types.get_type(str(self.getChild(0))).llvm_type,
            'name': str(self.getChild(1)),
            'args': '',
            'contents': '\n'.join(children),
        }

    def toString(self):
        return "function definition"

    def toStringTree(self):
        return "%s\n" % (super(FunctionDefinitionNode, self).toStringTree(),)
