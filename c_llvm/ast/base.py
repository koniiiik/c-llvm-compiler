from antlr3.tokens import CommonToken
from antlr3.tree import CommonTree, CommonTreeAdaptor


class AstNode(CommonTree):
    """
    Common base class for all our AST nodes describing all relevant tree
    traversal operations.
    """
    # Subclasses should override this for convenient access to child nodes
    # as attributes (like left or right). It should map attribute names to
    # indices in the child list.
    child_attributes = {}

    def __init__(self, payload):
        """
        We need to work around a bug in the antlr runtime where if you
        pass an imaginary token to a custom AST node type, it passes the
        integer type of the token instead of a token instance.
        """
        if isinstance(payload, (int, long)):
            payload = CommonToken(type=payload)
        super(AstNode, self).__init__(payload)

    def __getattr__(self, name):
        try:
            return self.getChild(self.child_attributes[name])
        except KeyError:
            return super(AstNode, self).__getattr__(name)

    def __setattr__(self, name, value):
        try:
            self.setChild(self.child_attributes[name], value)
        except KeyError:
            super(AstNode, self).__setattr__(name, value)

    def dupNode(self):
        return AstNode(self)


class AstTreeAdaptor(CommonTreeAdaptor):
    """
    Custom tree adaptor that creates instances of AstNode instead of
    CommonTree.
    """
    def createWithPayload(self, payload):
        return AstNode(payload)


class TranslationUnitNode(AstNode):
    def toString(self):
        return "translation unit\n"
