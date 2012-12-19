class BaseType(object):
    """
    Base class for all type definitions.
    """
    llvm_type = None
    sizeof = None
    # One of void, int, bool, pointer, function.
    internal_type = None
    default_value = 'undef'
    priority = 0
    is_complete = True

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

    @property
    def is_array(self):
        return self.internal_type == 'array'

    @property
    def is_function(self):
        return self.internal_type == 'function'

    @property
    def is_struct(self):
        return self.internal_type == 'struct'

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
    priority = 2

    def __init__(self, sizeof, *args, **kwargs):
        self.sizeof = sizeof
        super(IntType, self).__init__(*args, **kwargs)

    @property
    def llvm_type(self):
        return 'i%d' % (self.sizeof * 8,)

    def cast_to_int(self, value, state):
        state.push_result(value)
        return ""

    def cast_to_float(self, value, state):
        target_type = state.types.get_type('float')
        template = "%(register)s = sitofp %(type)s %(value)s to %(target_type)s"
        register = state.get_tmp_register()
        state.set_result(register, target_type, False)
        return template % {
            'register': register,
            'type': self.llvm_type,
            'value': value.value,
            'target_type': target_type.llvm_type,
        }

    def cast_to_bool(self, value, state):
        template = "%(register)s = icmp ne %(type)s %(value)s, 0"
        register = state.get_tmp_register()
        state.set_result(register, state.types.get_type('_Bool'), False)
        return template % {
            'register': register,
            'type': self.llvm_type,
            'value': value.value,
        }


class FloatType(BaseType):
    sizeof = 8
    internal_type = 'float'
    llvm_type = 'double'
    default_value = 0.0
    priority = 4

    def cast_to_int(self, value, state):
        target_type = state.types.get_type('int')
        template = "%(register)s = fptosi %(type)s %(value)s to %(target_type)s"
        register = state.get_tmp_register()
        state.set_result(register, target_type, False)
        return template % {
            'register': register,
            'type': self.llvm_type,
            'value': value.value,
            'target_type': target_type.llvm_type,
        }

    def cast_to_float(self, value, state):
        state.push_result(value)
        return ""


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


class FunctionType(BaseType):
    internal_type = 'function'

    def __init__(self, name, return_type, arg_types, variable_args):
        self.name = name
        self.return_type = return_type
        self.arg_types = arg_types
        self.variable_args = variable_args

    @property
    def arg_types_str(self):
        types = [t.llvm_type for t in self.arg_types]
        if self.variable_args:
            types.append('...')
        return "(%s)" % (', '.join(types),)

    @property
    def llvm_type(self):
        return "%s %s" % (self.return_type.llvm_type, self.arg_types_str)


class ArrayType(BaseType):
    internal_type = 'array'

    def __init__(self, name, target_type, length):
        self.name = name
        self.target_type = target_type
        self.length = length

    @property
    def llvm_type(self):
        return "[%d x %s]" % (self.length, self.target_type.llvm_type)

    @property
    def sizeof(self):
        return self.length * self.target_type.sizeof


class StructType(BaseType):
    internal_type = 'struct'

    def __init__(self, name, struct_name):
        self.name = name
        self.struct_name = struct_name
        self.member_types = []
        self.name_indices = {}
        self.is_complete = False

    @property
    def llvm_type(self):
        return "%%struct.%s" % (self.struct_name,)

    @property
    def llvm_full_type(self):
        return "{ %s }" % (", ".join(t.llvm_type
                                     for t in self.member_types),)

    def add_member(self, name, type):
        self.name_indices[name] = len(self.member_types)
        self.member_types.append(type)

    def get_member(self, name):
        """
        Returns a pair (index, type) for the specified member.
        """
        index = self.name_indices[name]
        return (index, self.member_types[index])


class TypeLibrary(object):
    """
    Library of known types. Prepopulated with builtin types, can create
    derived types (pointers, arrays, structures) on demand.
    """
    def __init__(self):
        char_type = IntType(sizeof=1, name='char')
        builtins = {
            'void': VoidType(name='void'),
            'int': IntType(sizeof=8, name='int'),
            'char': char_type,
            'float': FloatType(name='float'),
            'double': FloatType(name='double'),
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

    def get_function_type(self, return_type, arg_types, variable_args):
        name = "%(return)s(%(args)s%(varargs)s)" % {
            'return': return_type.name,
            'args': ','.join(type.name for type in arg_types),
            'varargs': variable_args and ',...' or '',
        }
        try:
            return self._types[name]
        except KeyError:
            func_type = FunctionType(name, return_type, arg_types,
                                     variable_args)
            self._types[name] = func_type
            return func_type

    def get_array_type(self, target_type, length):
        name = "%s[%d]" % (target_type.name, length)
        try:
            return self._types[name]
        except KeyError:
            array_type = ArrayType(name, target_type, length)
            self._types[name] = array_type
            return array_type

    def get_structure(self, struct_name):
        name = "struct %s" % (struct_name,)
        try:
            return self._types[name]
        except KeyError:
            struct_type = StructType(name, struct_name)
            self._types[name] = struct_type
            return struct_type

    def cast_value(self, value, state, target_type):
        """
        Returns the code required to cast value to target_type and sets
        the state accordingly.
        """
        cast_method = getattr(value.type,
                              'cast_to_%s' % (target_type.internal_type,))
        return cast_method(value, state)
