from sys import stderr

from antlr3.tokens import CommonToken
from antlr3.tree import CommonTree, CommonTreeAdaptor

from c_llvm.exceptions import CompilationError
from c_llvm.traversal_state import CompilerState


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
            raise AttributeError("%s has no attribute %s"
                                 % (self.__class__.__name__, name))

    def __setattr__(self, name, value):
        try:
            self.setChild(self.child_attributes[name], value)
        except KeyError:
            super(AstNode, self).__setattr__(name, value)

    def dupNode(self):
        return AstNode(self)

    def log_error(self, state, message):
        state.errors.append("%d:%d: %s" % (
            self.getLine(),
            self.getCharPositionInLine(),
            message,
        ))

    def process_children(self, state):
        """
        Process the child nodes and return a list of pieces of output
        code for each child.
        """
        output = []
        for child in self.children:
            output.append(child.generate_code(state))
        return output

    def generate_code(self, state):
        """
        The main walker method. Each node should implement this. The state
        argument is an instance of CompilerState, a class that holds all
        kinds of information like all symbol tables, next free register,
        list of compilation errors etc.

        Should return a string, which is the output LLVM code for this AST
        node. If an error is encountered, it should be logged using
        log_error but a string should be returned anyway.
        """
        raise NotImplementedError


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

    def generate_code(self):
        state = CompilerState()

        children = self.process_children(state)

        if state.errors:
            raise CompilationError("\n".join(state.errors))

        return "\n".join(children)


class EmptyNode(AstNode):
    def generate_code(self, state):
        return ""


class OptionalNode(AstNode):
    """
    This special AST node class is useful for situations where a
    nonterminal is optional but we need an AST node anyway.
    """
    def generate_code(self, state):
        return "\n".join(self.process_children(state))
