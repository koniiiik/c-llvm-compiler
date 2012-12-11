class Variable(object):
    """
    Represents a single variable. Keeps a reference to its type, name and
    the register through which it can be accessed.
    """
    def __init__(self, name, type, register, is_global):
        self.name = name
        self.type = type
        self.register = register
        self.is_global = is_global
