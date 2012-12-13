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

    template = """
%(exp_code)s
%(exp_cast_code)s
br i1 %(exp_cast_value)s, label %%If%(num)d.True, label %%If%(num)d.False
If%(num)d.True:
%(statement1_code)s
br label %%If%(num)d.End
If%(num)d.False:
%(statement2_code)s
br label %%If%(num)d.End
If%(num)d.End:
"""

    def generate_code(self, state):
        exp_code = self.exp.generate_code(state)
        exp_result = state.pop_result()
        exp_cast_code = exp_result.type.cast_to_bool(exp_result, None,
                                                     state, self)
        exp_cast_result = state.pop_result()

        return self.template % {
            'exp_code': exp_code,
            'exp_cast_code': exp_cast_code,
            'exp_cast_value': exp_cast_result.value,
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
        num = state._get_next_number()
        state.enter_cycle("While%d.End" % (num), "While%d.Body" % (num))
        exp_code = self.exp.generate_code(state)
        exp_result = state.pop_result()
        exp_cast_code = exp_result.type.cast_to_bool(exp_result, None,
                                                     state, self)
        exp_cast_value = state.pop_result().value
        statement_code = self.statement.generate_code(state)
        state.leave_cycle()
        return self.template % {
            'exp_code': exp_code,
            'exp_cast_code': exp_cast_code,
            'exp_cast_value': exp_cast_value,
            'num': num,
            'statement_code': statement_code,
        }


class WhileNode(WhileStatement):
    # end previous basic block with br
    template = """
br label %%While%(num)d.Test
While%(num)d.Test:
%(exp_code)s
%(exp_cast_code)s
br i1 %(exp_cast_value)s, label %%While%(num)d.Body, label %%While%(num)d.End
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
%(exp_cast_code)s
br i1 %(exp_cast_value)s, label %%While%(num)d.Body, label %%While%(num)d.End
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
%(e2_cast_code)s
br i1 %(e2_cast_value)s, label %%For%(num)d.Body, label %%For%(num)d.End
For%(num)d.Body:
%(statement_code)s
br label %%For%(num)d.Inc
For%(num)d.Inc:
%(e3_code)s
br label %%For%(num)d.Test
For%(num)d.End:
"""

    def generate_code(self, state):
        num = state._get_next_number()
        state.enter_cycle("For%d.End" % (num), "For%d.Inc" % (num))
        e1_code = self.exp1.generate_code(state)

        e2_code = self.exp2.generate_code(state)
        e2_result = state.pop_result()
        e2_cast_code = e2_result.type.cast_to_bool(e2_result, None,
                                                     state, self)
        e2_cast_value = state.pop_result().value

        e3_code = self.exp3.generate_code(state)
        statement_code = self.statement.generate_code(state)
        state.leave_cycle()
        return self.template % {
            'e1_code': e1_code,
            'e2_code': e2_code,
            'e3_code': e3_code,
            'e2_cast_code': e2_cast_code,
            'e2_cast_value': e2_cast_value,
            'num': num,
            'statement_code': statement_code,
        }


class BreakStatementNode(AstNode):
    def generate_code(self, state):
        if not state.cycles:
            self.log_error(state, "'break' used outside of cycle")
        return "br label %%%s" % (state.cycles[-1][0])


class ContinueStatementNode(AstNode):
    def generate_code(self, state):
        if not state.cycles:
            self.log_error(state, "'break' used outside of cycle")
        return "br label %%%s" % (state.cycles[-1][1])


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
