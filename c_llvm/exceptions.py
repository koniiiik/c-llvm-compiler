class CompilationError(Exception):
    pass


class ScopePopException(CompilationError):
    """
    Raised in case it is impossible to pop() another scope.
    """
    pass
