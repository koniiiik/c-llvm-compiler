from c_llvm.ast.base import AstNode


class CompoundStatementNode(AstNode):
    def generate_code(self, state):
        state.enter_block()
        children = self.process_children(state)
        state.leave_block()
        return "\n".join(children)

    def toString(self):
        return ""

    def toStringTree(self):
        return "{\n%s\n}" % (
            super(CompoundStatementNode, self).toStringTree(),
        )


class IfNode(AstNode):
    child_attributes = {
        'exp': 0,
        'statement': 1
    }

    #TODO type?
    #FIXME where is the result of expression ?
    template = """
%(exp_code)s
%(exp_cast_code)s
br i1 %(exp_cast_value)s, label %%If%(num)d.True, label %%If%(num)d.False
If%(num)d.True:
%(statement_code)s
br label %%If%(num)d.False
If%(num)d.False:
"""

    def generate_code(self, state):
        exp_code = self.exp.generate_code(state)
        exp_result = state.pop_result()
        exp_cast_code = exp_result.type.cast_to_bool(exp_result, None,
                                                     state, self)
        exp_cast_result = state.pop_result()

        return self.template % {
            'cmp': state.get_tmp_register(),
            'exp_code': exp_code,
            'exp_cast_code': exp_cast_code,
            'exp_cast_value': exp_cast_result.value,
            'num': state._get_next_number(),
            'statement_code': self.statement.generate_code(state),
        }


class IfElseNode(AstNode):
    child_attributes = {
        'exp': 0,
        'statement1': 1,
        'statement2': 2,
    }

    #TODO type?
    #FIXME where is the result of expression ?
    template = """
%(exp_code)s
%(exp_res)s = add i64 1, 1
%(cmp)s = icmp ne i64 %(exp_res)s, 0
br i1 %(cmp)s, label %%If%(num)d.True, label %%If%(num)d.False
If%(num)d.True:
%(statement1_code)s
br label %%If%(num)d.End
If%(num)d.False:
%(statement2_code)s
br label %%If%(num)d.End
If%(num)d.End:
"""

    def generate_code(self, state):
        return self.template % {
            'cmp': state.get_tmp_register(),
            'exp_code': self.exp.generate_code(state),
            'exp_res': state.get_tmp_register(),
            'num': state._get_next_number(),
            'statement1_code': self.statement1.generate_code(state),
            'statement2_code': self.statement2.generate_code(state),
        }


class WhileStatement(AstNode):
    child_attributes = {
        'exp': 0,
        'statement': 1
    }

    def generate_code(self, state):
        return self.template % {
            'cmp': state.get_tmp_register(),
            'exp_code': self.exp.generate_code(state),
            'exp_res': state.get_tmp_register(),
            'num': state._get_next_number(),
            'statement_code': self.statement.generate_code(state),
        }


class WhileNode(WhileStatement):
    # end previous basic block with br
    template = """
br label %%While%(num)d.Test
While%(num)d.Test:
%(exp_code)s
%(exp_res)s = add i64 1, 1
%(cmp)s = icmp ne i64 %(exp_res)s, 0
br i1 %(cmp)s, label %%While%(num)d.Body, label %%While%(num)d.End
While%(num)d.Body:
%(statement_code)s
br label %%While%(num)d.Test
While%(num)d.End:
"""


class DoWhileNode(WhileStatement):
    # end previous basic block with br
    template = """
br label %%While%(num)d.Body
While%(num)d.Body:
%(statement_code)s
br label %%While%(num)d.Test
While%(num)d.Test:
%(exp_code)s
%(exp_res)s = add i64 1, 1
%(cmp)s = icmp ne i64 %(exp_res)s, 0
br i1 %(cmp)s, label %%While%(num)d.Body, label %%While%(num)d.End
While%(num)d.End:
"""


class ForNode(AstNode):
    child_attributes = {
        'exp1': 0,
        'exp2': 1,
        'exp3': 2,
        'statement': 3
    }

    template = """
%(e1_code)s
br label %%For%(num)d.Test
For%(num)d.Test:
%(e2_code)s
%(e2_res)s = add i64 1, 1
%(cmp)s = icmp ne i64 %(e2_res)s, 0
br i1 %(cmp)s, label %%For%(num)d.Body, label %%For%(num)d.End
For%(num)d.Body:
%(statement_code)s
%(e3_code)s
br label %%For%(num)d.Test
For%(num)d.End:
"""

    def generate_code(self, state):
        return self.template % {
            'cmp': state.get_tmp_register(),
            'e1_code': self.exp1.generate_code(state),
            'e2_code': self.exp2.generate_code(state),
            'e3_code': self.exp3.generate_code(state),
            'e2_res': state.get_tmp_register(),
            'num': state._get_next_number(),
            'statement_code': self.statement.generate_code(state),
        }


class ReturnStatementNode(AstNode):
    child_attributes = {
        'expression': 0,
    }

    def generate_code(self, state):
        return_type = state.return_type
        if return_type.is_void:
            if self.getChildCount():
                self.log_error(state, "a void function can't return a "
                               "value")
            return "ret void"
        expression_code = self.expression.generate_code(state)
        expression_result = state.pop_result()
        # TODO: cast
        return "ret %s %s" % (expression_result.type.llvm_type,
                              expression_result.value)
