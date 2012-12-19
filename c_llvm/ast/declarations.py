from collections import Counter

from c_llvm.ast.base import AstNode
from c_llvm.types import PointerType
from c_llvm.variables import Variable


class DeclarationNode(AstNode):
    child_attributes = {
        'specifier': 0,
        'declarator': 1,
    }

    def generate_code(self, state):
        # TODO: check redeclarations
        is_global = state.is_global()
        state.declaration_stack.append(self.specifier.get_type(state))
        type = self.declarator.get_type(state)
        identifier = self.declarator.get_identifier()
        state.declaration_stack.pop()

        if is_global:
            register = '@%s' % (identifier,)
        else:
            register = state.get_var_register(identifier)
        var = Variable(type=type, name=identifier, register=register,
                       is_global=is_global)

        if type.is_function:
            if not is_global:
                self.log_error(state, "can't declare a non-global function")
            declaration = "declare %(ret_type)s %(register)s%(arg_types)s" % {
                'ret_type': type.return_type.llvm_type,
                'register': register,
                'arg_types': type.arg_types_str,
            }
        elif is_global:
            declaration = "%(register)s = global %(type)s %(value)s" % {
                'register': var.register,
                'type': var.type.llvm_type,
                'value': var.type.default_value,
            }
        else:
            declaration = "%(register)s = alloca %(type)s" % {
                'register': var.register,
                'type': var.type.llvm_type,
            }

        state.symbols[identifier] = var
        return declaration

    def toString(self):
        return "declaration"

    def toStringTree(self):
        return "%s\n" % (super(DeclarationNode, self).toStringTree(),)


class EmptyDeclarationNode(AstNode):
    """
    This simple node type handles the case of declarations without a
    declarator. This is used for example in struct declarations where the
    struct itself is defined but no variable of its type is declared.
    """
    child_attributes = {
        'specifier': 0,
    }

    def generate_code(self, state):
        self.specifier.get_type(state)
        return ""


class FunctionDefinitionNode(AstNode):
    child_attributes = {
        'specifier': 0,
        'declarator': 1,
        'body': 2,
    }
    template = """
define %(type)s @%(name)s(%(args)s)
{
%(init)s
%(contents)s
%(return)s
}
"""
    init_template = """
%(register)s = alloca %(type)s
store %(type)s %%%(name)s, %(type)s* %(register)s
"""

    def generate_code(self, state):
        specifier_type = self.specifier.get_type(state)
        state.declaration_stack.append(specifier_type)
        function_type = self.declarator.get_type(state)
        state.declaration_stack.pop()
        name = self.declarator.get_identifier()
        register = '@%s' % (name,)

        if not function_type.is_function:
            self.log_error(state, "invalid function definition -- "
                           "symbol of a non-function type declared")
            return ""

        if name in state.symbols:
            declared = state.symbols[name]
            if declared.type is not function_type:
                self.log_error(state, "%s already declared as %s" %
                               declared.type.name)
                return ""
            if declared.is_defined:
                self.log_error(state, "function already defined")
                return ""
            declared.is_defined = True
        else:
            state.symbols[name] = Variable(name, function_type, register,
                                           True, True)

        arguments = zip(self.declarator.get_argument_names(state),
                        function_type.arg_types)
        arg_init, arg_header = [], []
        pending_scope = {}
        for arg_name, arg_type in arguments:
            arg_header.append("%s %%%s" % (arg_type.llvm_type, arg_name))
            arg_register = state.get_var_register(arg_name)
            arg_init.append(self.init_template % {
                'type': arg_type.llvm_type,
                'register': arg_register,
                'name': arg_name,
            })
            pending_scope[arg_name] = Variable(arg_name, arg_type,
                                               arg_register, False)

        state.set_pending_scope(pending_scope)

        return_type = function_type.return_type
        state.return_type = return_type
        state.return_found = False
        # return something to keep LLVM happy
        if return_type.is_void:
            ret_statement = "ret void"
        else:
            ret_statement = "ret %s undef" % (
                    function_type.return_type.llvm_type,)
        result = self.template % {
            'type': function_type.return_type.llvm_type,
            'name': name,
            'args': ', '.join(arg_header),
            'init': '\n'.join(arg_init),
            'contents': self.body.generate_code(state),
            'return': ret_statement,
        }
        if not state.return_found and not state.return_type.is_void:
            self.log_warning(state, "missing return statement in "
                    "non void function %s" % self.declarator.get_identifier())
        state.return_type = None
        return result

    def toString(self):
        return "function definition"

    def toStringTree(self):
        return "%s\n" % (super(FunctionDefinitionNode, self).toStringTree(),)


class DeclaratorNode(AstNode):
    child_attributes = {
        'inner_declarator': 0,
    }

    def get_type(self, state):
        """
        Returns the Type instance of this declarator.
        """
        raise NotImplementedError

    def get_identifier(self):
        """
        Drills down through all levels of pointer and array specifiers to
        the identifier.
        """
        return self.inner_declarator.get_identifier()


class IdentifierDeclaratorNode(DeclaratorNode):
    child_attributes = {
        'identifier': 0,
    }

    def get_type(self, state):
        return state.declaration_stack[-1]

    def get_identifier(self):
        return str(self.identifier)


class PointerDeclaratorNode(DeclaratorNode):
    def get_type(self, state):
        child_type = self.inner_declarator.get_type(state)
        return state.types.get_pointer_type(child_type)


class FunctionDeclaratorNode(DeclaratorNode):
    child_attributes = {
        'inner_declarator': 0,
        'arg_list': 1,
    }

    def get_type(self, state):
        return_type = self.inner_declarator.get_type(state)
        if return_type.is_function:
            self.log_error(state, 'a function cannot return a function')
        if return_type.is_array:
            self.log_error(state, 'a function cannot return an array')
        arg_list = self.arg_list.children
        variable_arguments = len(arg_list) > 0 and str(arg_list[-1]) == '...'
        if variable_arguments:
            arg_list.pop()
        arg_types = [arg.get_type(state) for arg in arg_list]

        for i, type in enumerate(arg_types):
            if type.is_void:
                arg_list[i].log_error(state, "function arguments can't be void")
            elif type.is_function:
                arg_types[i] = state.get_pointer_type(type)

        return state.types.get_function_type(return_type, arg_types,
                                             variable_arguments)

    def get_argument_names(self, state):
        """
        This should only be called from function definitions as it will
        log errors only relevant for those.
        """
        names = [arg.get_identifier() for arg in self.arg_list.children]
        if any(name is None for name in names):
            self.log_error(state, "argument name not provided")
            return []
        counter = Counter(names)
        if counter and counter.most_common(1)[0][1] > 1:
            self.log_error(state, "duplicate argument name")
        return names


class ParameterListNode(AstNode):
    pass


class ParameterDeclarationNode(AstNode):
    child_attributes = {
        'type_specifier': 0,
        'declarator': 1,
    }

    def get_type(self, state):
        state.declaration_stack.append(self.type_specifier.get_type(state))
        type = self.declarator.get_type(state)
        state.declaration_stack.pop()
        return type

    def get_identifier(self):
        return self.declarator.get_identifier()


class ArrayDeclaratorNode(DeclaratorNode):
    child_attributes = {
        'inner_declarator': 0,
        'length': 1,
    }

    def get_type(self, state):
        if self.getChildCount() != 2:
            self.log_error(state, "incomplete array types are not "
                           "supported (you have to provide a length)")
            length = 0
        elif str(self.length) == '*':
            self.log_error(state, "variable-length arrays are not "
                           "supported")
            length = 0
        else:
            self.length.generate_code(state)
            length_result = state.pop_result()
            if (length_result is not None and length_result.is_constant
                    and length_result.type.is_integer):
                length = length_result.value
            else:
                self.log_error(state, "invalid array dimension (constant "
                               "integer expression required)")
                length = 0

        target_type = self.inner_declarator.get_type(state)

        if target_type.is_function:
            self.log_error(state, "can't declare an array of functions")

        return state.types.get_array_type(target_type, length)


class DeclarationSpecifierNode(AstNode):
    child_attributes = {
        'storage_class': 0,
        'type_specifier': 1,
    }

    def get_type(self, state):
        return self.type_specifier.get_type(state)

    def is_typedef(self):
        return str(self.storage_class) == "typedef"


class StorageClassNode(AstNode):
    child_attributes = {
        'storage_class': 0,
    }

    def toString(self):
        if self.getChildCount() < 1:
            return ""
        return str(self.storage_class)


class TypeSpecifierNode(AstNode):
    def get_type(self, state):
        specifiers = reversed(sorted(str(child) for child in self.children))
        type_name = " ".join(specifiers)
        try:
            return state.types.get_type(type_name)
        except KeyError:
            self.log_error(state, "invalid type: %s" % (type_name,))
            return state.types.get_type('void')


class StructIdentifierNode(AstNode):
    child_attributes = {
        'identifier': 0,
    }

    def get_identifier(self, state):
        if self.getChildCount() > 0:
            return str(self.identifier)
        return "anonymous.%d" % (state._get_next_number(),)


class StructDeclarationListNode(AstNode):
    def get_declarations(self, state):
        """
        Yields a (name, type) pair for each declaration in the child list.
        """
        seen_names = set()
        for child in self.children:
            name = child.get_identifier()
            if name in seen_names:
                self.log_error(state, "duplicate struct member name: %s" % (name,))
                continue
            else:
                seen_names.add(name)
            type = child.get_type(state)
            if not type.is_complete:
                self.log_error(state, "incomplete struct member type: %s" % (name,))
                continue
            yield (name, type)


class StructMemberDeclarationNode(AstNode):
    child_attributes = {
        'specifier': 0,
        'declarator': 1,
    }

    def get_identifier(self):
        return self.declarator.get_identifier()

    def get_type(self, state):
        specifier_type = self.specifier.get_type(state)
        state.declaration_stack.append(specifier_type)
        member_type = self.declarator.get_type(state)
        state.declaration_stack.pop()
        return member_type


class StructDefinitionNode(AstNode):
    child_attributes = {
        'identifier': 0,
        'definition': 1,
    }
    declaration_template = """
%(alias)s = type %(type)s
"""

    def get_type(self, state):
        name = self.identifier.get_identifier(state)
        struct_type = state.types.get_structure(name)
        if struct_type.is_complete:
            self.log_error(state, "redefinition of struct %s" % (name,))

        for member_name, member_type in self.definition.get_declarations(state):
            struct_type.add_member(member_name, member_type)

        struct_type.is_complete = True

        state.global_declarations.append(self.declaration_template % {
            'alias': struct_type.llvm_type,
            'type': struct_type.llvm_full_type,
        })

        return struct_type


class StructDeclarationNode(AstNode):
    child_attributes = {
        'identifier': 0,
    }

    def get_type(self, state):
        name = str(self.identifier)
        return state.types.get_structure(name)
