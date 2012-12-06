from antlr3.tree import CommonTree, CommonTreeAdaptor


class AstNode(CommonTree):
    """
    Common base class for all our AST nodes describing all relevant tree
    traversal operations.
    """
    def dupNode(self):
        return AstNode(self)


class AstTreeAdaptor(CommonTreeAdaptor):
    """
    Custom tree adaptor that creates instances of AstNode instead of
    CommonTree.
    """
    def createWithPayload(self, payload):
        return AstNode(payload)
