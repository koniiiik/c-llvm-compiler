from c_llvm.exceptions import CompilationError


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

    def push(self):
        d = {}
        self.dicts.append(d)
        return d

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


class CompilerState(object):
    def __init__(self):
        self.symbols = ScopedSymbolTable()
        self.errors = []
        self.next_free_id = 0

    def _get_next_number(self):
        result = self.next_free_id
        self.next_free_id += 1
        return result

    def get_tmp_register(self):
        return "%%tmp.%d" % (self._get_next_number(),)

    def get_var_register(self, name):
        return "%%var.%s.%d" % (self._get_next_number(),)

    def get_label(self):
        return "label%d" % (self._get_next_number(),)
