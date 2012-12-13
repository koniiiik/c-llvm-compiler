class BaseType(object):
    """
    Base class for all type definitions.
    """
    llvm_type = None
    sizeof = None
    # One of void, int, bool, pointer, function.
    internal_type = None
    default_value = 'undef'

    def __init__(self, name):
        self.name = name

    @property
    def is_integer(self):
        return self.internal_type in {'int', 'bool'}

    @property
    def is_float(self):
        return self.internal_type in {'float', 'double', 'extended'}

    @property
    def is_arithmetic(self):
        return self.is_integer or self.is_float

    @property
    def is_pointer(self):
        return self.internal_type == 'pointer'

    @property
    def is_void(self):
        return self.internal_type == 'void'

    @property
    def is_scalar(self):
        return self.is_arithmetic or self.is_pointer

    def cast_to_void(self, *args, **kwargs):
        raise NotImplementedError

    def cast_to_int(self, *args, **kwargs):
        raise NotImplementedError

    def cast_to_bool(self, *args, **kwargs):
        raise NotImplementedError

    def cast_to_pointer(self, *args, **kwargs):
        raise NotImplementedError

    def cast_to_function(self, *args, **kwargs):
        raise NotImplementedError


class VoidType(BaseType):
    llvm_type = 'void'
    sizeof = 0
    internal_type = 'void'


class IntType(BaseType):
    sizeof = 8
    internal_type = 'int'
    default_value = 0

    def __init__(self, sizeof, *args, **kwargs):
        self.sizeof = sizeof
        super(IntType, self).__init__(*args, **kwargs)

    @property
    def llvm_type(self):
        return 'i%d' % (self.sizeof * 8,)

    def cast_to_bool(self, value, target_type, state, ast_node):
        template = "%(register)s = icmp ne %(type)s %(value)s, 0"
        register = state.get_tmp_register()
        state.set_result(register, state.types.get_type('_Bool'), False)
        return template % {
            'register': register,
            'type': self.llvm_type,
            'value': value.value,
        }


class BoolType(BaseType):
    sizeof = 1
    internal_type = 'bool'
    llvm_type = 'i1'
    default_value = 0


class PointerType(BaseType):
    sizeof = 8 # TODO: this is not portable
    internal_type = 'pointer'

    def __init__(self, target_type):
        self.target_type = target_type

    @property
    def llvm_type(self):
        return "%s *" % (self.target_type.llvm_type,)

    @property
    def name(self):
        return "%s*" % (self.target_type.name,)


class TypeLibrary(object):
    """
    Library of known types. Prepopulated with builtin types, can create
    derived types (pointers, arrays) on demand.
    """
    def __init__(self):
        char_type = IntType(sizeof=1, name='char')
        builtins = {
            'void': VoidType(name='void'),
            'int': IntType(sizeof=8, name='int'),
            'char': char_type,
            '_Bool': BoolType(name='_Bool'),
            # We create the following pointer type explicitly because LLVM
            # doesn't allow void* and suggests using i8* instead.
            'void*': PointerType(char_type),
        }
        self._types = builtins

    def get_type(self, name):
        return self._types[name]

    def set_type(self, name, type):
        self._types[name] = type

    def get_pointer_type(self, type):
        name = "%s*" % (type.name,)
        try:
            return self._types[name]
        except KeyError:
            ptr_type = PointerType(type)
            self._types[name] = ptr_type
            return ptr_type

    def cast_value(self, value, target_type, state, ast_node):
        """
        Returns the code required to cast value to target_type and sets
        the state accordingly.
        """
        cast_method = getattr(value.type,
                              'cast_to_%s' % (target_type.internal_name,))
        return cast_method(value, target_type, state, ast_node)
