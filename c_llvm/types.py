class VoidType(object):
    """
    Base class for all type definitions, at the same time acts as the void
    type.
    """
    llvm_type = 'i8'
    sizeof = 0
    name = 'void'
    # One of void, int, char, bool, pointer, function.
    internal_type = 'void'
    default_value = 0

    @property
    def is_integer(self):
        return self.internal_type in {'int', 'char', 'bool'}

    @property
    def is_pointer(self):
        return self.internal_type == 'pointer'

    @property
    def is_void(self):
        return self.internal_type == 'void'


class IntType(VoidType):
    llvm_type = 'i64'
    sizeof = 8
    name = 'int'
    internal_type = 'int'


class CharType(IntType):
    llvm_type = 'i8'
    sizeof = 1
    name = 'char'
    internal_type = 'char'


class TypeLibrary(object):
    """
    Library of known types. Prepopulated with builtin types, can create
    derived types (pointers, arrays) on demand.
    """
    def __init__(self):
        self.builtins = {
            'void': VoidType(),
            'int': IntType(),
            'char': CharType(),
        }

    def get_type(self, name):
        return self.builtins[name]
