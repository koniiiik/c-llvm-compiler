from collections import deque, namedtuple

from c_llvm.exceptions import CompilationError
from c_llvm.types import TypeLibrary


class ScopedSymbolTable(object):
    """
    A dictionary-like class for a scoped symbol table.

    Shamelessly stolen from django.template.context.BaseContext which is
    used as a scoped context for template rendering and removed some
    unnecessary methods.
    """
    def __init__(self, dict_=None):
        self._reset_dicts(dict_)

    def _reset_dicts(self, value=None):
        if value is None:
            self.dicts = [{}]
        else:
            self.dicts = [value]

    def __repr__(self):
        return repr(self.dicts)

    def __iter__(self):
        for d in reversed(self.dicts):
            yield d

    def push(self, scope=None):
        if scope is None:
            scope = {}
        self.dicts.append(scope)
        return scope

    def pop(self):
        if len(self.dicts) == 1:
            raise ScopePopException
        return self.dicts.pop()

    def __setitem__(self, key, value):
        "Set a variable in the current scope"
        self.dicts[-1][key] = value

    def __getitem__(self, key):
        "Get a variable's value, starting at the current scope and going upward"
        for d in reversed(self.dicts):
            if key in d:
                return d[key]
        raise KeyError(key)

    def __delitem__(self, key):
        "Delete a variable from the current scope"
        del self.dicts[-1][key]

    def has_key(self, key):
        for d in self.dicts:
            if key in d:
                return True
        return False

    def __contains__(self, key):
        return self.has_key(key)

    def get(self, key, otherwise=None):
        for d in reversed(self.dicts):
            if key in d:
                return d[key]
        return otherwise

    def get_current_scope(self, name, otherwise=None):
        return self.dicts[-1].get(name, otherwise)


ResultType = namedtuple('ResultType', ['value', 'type', 'is_constant', 'pointer'])


class CompilerState(object):
    def __init__(self):
        self.symbols = ScopedSymbolTable()
        self.types = TypeLibrary()
        # declaration_scope is used in declarators where it contains
        # declaration specifiers.
        self.declaration_stack = deque()
        self.errors = []
        self.warnings = []
        self.next_free_id = 0
        self.last_result = None
        self.return_type = None
        self.break_labels = []
        self.continue_labels = []
        self.switches = []
        self.global_declarations = []
        self.pending_scope = {}

    def _get_next_number(self):
        result = self.next_free_id
        self.next_free_id += 1
        return result

    def get_tmp_register(self):
        return "%%tmp.%d" % (self._get_next_number(),)

    def get_var_register(self, name):
        return "%%var.%s.%d" % (name, self._get_next_number())

    def get_label(self):
        return "label%d" % (self._get_next_number(),)

    def set_pending_scope(self, scope):
        """
        Sets the initial state of the next scope that's going to be
        created. Used in function definitions.
        """
        self.pending_scope.update(scope)

    def enter_block(self):
        self.symbols.push(self.pending_scope)
        self.pending_scope = {}

    def leave_block(self):
        self.symbols.pop()
        self.pending_scope = {}

    def is_global(self):
        """
        Are we in the global scope or inside a function definition?
        """
        return len(self.symbols.dicts) == 1

    def push_result(self, value):
        self.last_result = value;

    def set_result(self, value, type, is_constant=False, pointer=None):
        self.last_result = ResultType(value, type, is_constant, pointer)

    def pop_result(self):
        result = self.last_result
        self.last_result = None
        return result

    def enter_switch(self, number):
        # number of the current switch, 'default' found, list of 'case' labels
        self.switches.append([number, False, []])

    def leave_switch(self):
        self.switches.pop()
