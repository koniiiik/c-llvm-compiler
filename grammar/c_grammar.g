grammar c_grammar;

options {
    language = Python;
    output = AST;
}

tokens {
    // A dummy token type for all AST node types where we don't have a
    // token to put as the root of a subtree.
    DUMMY;
}

@header {
from c_llvm.ast.base import EmptyNode, OptionalNode, TranslationUnitNode
from c_llvm.ast.expressions import *
from c_llvm.ast.declarations import *
from c_llvm.ast.statements import *
}

translation_unit
    :	external_declaration+
        -> ^(DUMMY<TranslationUnitNode> external_declaration+)
    ;

external_declaration
    :	function_definition
    |	declaration
    ;

function_definition // TODO
    :	declaration_specifiers identifier '(' parameter_list (',' '...')? ')' compound_statement
        -> ^(DUMMY<FunctionDefinitionNode> declaration_specifiers
             identifier parameter_list? compound_statement)
    ;

parameter_list // TODO
    :	parameter_declaration (',' parameter_declaration)*
    |
    ;

parameter_declaration // TODO
    :	declaration_specifiers declarator
    ;

declaration
    :	declaration_specifiers init_declarator (',' init_declarator)* ';'
        -> ^(DUMMY<DeclarationNode> declaration_specifiers init_declarator)+
    ;

init_declarator // TODO
    :	declarator
    ;

declarator
    :	pointer declarator -> ^(DUMMY<PointerDeclaratorNode> declarator)
    |	direct_declarator
    ;

direct_declarator
    :	identifier -> ^(DUMMY<IdentifierDeclaratorNode> identifier)
    |	'('! declarator ')'!
    // TODO: arrays
    // TODO: functions
    ;

pointer
    :	'*' TYPE_QUALIFIER*
    ;

declaration_specifiers // TODO
    :	type_specifier
    ;

type_specifier // TODO
    :	'int'
    |	'void'
    ;

type_name // TODO
    :	type_specifier
    ;

// Statements

statement
    :	labeled_statement
    |	compound_statement
    |	expression_statement
    |	selection_statement
    |	iteration_statement
    |	jump_statement
    ;

labeled_statement
    :	identifier ':' statement ///< not supported
    |	'case' e=constant_expression ':' s=statement
        -> ^('case'<CaseStatementNode> $e $s)
    |	'default' ':' s=statement
        -> ^('default'<DefaultStatementNode> $s)
    ;

compound_statement
    :	'{' block_item* '}'
        -> ^(DUMMY<CompoundStatementNode> block_item*)
    ;

block_item
    :	declaration
    |	statement
    ;

expression_statement
    :	e+=expression? ';' -> {$e is None or not $e}? DUMMY<EmptyNode>
                          -> $e
    ;

selection_statement
    :	('if' '(' expression ')' statement 'else') => 'if' '(' e=expression ')' s1=statement 'else' s2=statement ->
            ^(DUMMY<IfElseNode> $e $s1 $s2)
    |	('if') => 'if' '(' e=expression ')' s=statement ->
            ^(DUMMY<IfNode> $e $s)
    |	'switch' '(' e=expression ')' s=statement
        -> ^('switch'<SwitchStatementNode> $e $s)
    ;

iteration_statement
    :	'while' '(' e=expression ')' s=statement -> ^(DUMMY<WhileNode> $e $s)
    |	'do' s=statement 'while' '(' e=expression ')' ';' -> ^(DUMMY<DoWhileNode> $e $s)
    |	'for' '(' e1=optional_expression ';' e2=optional_expression ';' e3=optional_expression ')' s=statement ->
            ^(DUMMY<ForNode> $e1 $e2 $e3 $s)
    |	'for' '(' d=declaration e2=expression? ';' e3=expression? ')' s=statement ->
            ^(DUMMY<ForNode> $d $e2 $e3 $s)
    ;

optional_expression
    :	expression? -> ^(DUMMY<OptionalNode> expression?)
    ;

jump_statement
    :	'goto' identifier ';' ///< 'goto' is not supported
    |	'break' ';' -> ^('break'<BreakStatementNode>)
    |	'continue' ';' -> ^('continue'<ContinueStatementNode>)
    |	'return' expression? ';' -> ^('return'<ReturnStatementNode> expression?)
    ;

// Expressions

constant_expression
    :	conditional_expression
    ;

expression
    :	(e=assignment_expression -> assignment_expression)
        ((',' assignment_expression)+ -> ^(',' $e assignment_expression+))?
    ;

assignment_expression
    options {
        backtrack = true;
    }
    :	 lvalue=unary_expression op=assignment_operator rvalue=assignment_expression
        -> ^(DUMMY<AssignmentExpressionNode> $op $lvalue $rvalue)
    |	conditional_expression
    ;

conditional_expression
    :	(condition=logical_or_expression -> logical_or_expression)
        (('?' if_true=expression ':' if_false=conditional_expression)
            -> ^('?'<ConditionalExpressionNode> $condition $if_true $if_false))?
    ;

logical_or_expression
    :	logical_and_expression ('||'<LogicalExpressionNode>^ logical_and_expression)*
    ;

logical_and_expression
    :	inclusive_or_expression ('&&'<LogicalExpressionNode>^ inclusive_or_expression)*
    ;

inclusive_or_expression
    :	exclusive_or_expression ('|'<BitwiseExpressionNode>^ exclusive_or_expression)*
    ;

exclusive_or_expression
    :	and_expression ('^'<BitwiseExpressionNode>^ and_expression)*
    ;

and_expression
    :	equality_expression ('&'<BitwiseExpressionNode>^ equality_expression)*
    ;

equality_expression
    :	relational_expression (EQUALITY_OPERATOR<EqualityExpressionNode>^ relational_expression)*
    ;

relational_expression
    :	shift_expression (RELATIONAL_OPERATOR<RelationalExpressionNode>^ shift_expression)*
    ;

shift_expression
    :	additive_expression (SHIFT_OPERATOR<ShiftExpressionNode>^ additive_expression)*
    ;

additive_expression
    // This construct is so clumsy because of a bug in antlr which doesn't
    // allow us to create custom AST nodes out of parser nonterminals
    // while it is perfectly possible to create default nodes. Also, we
    // can't use a lexer nonterminal here for the same reasons as
    // described in assignment_operator.
    :	multiplicative_expression (('-'<SubtractionExpressionNode>^ multiplicative_expression)
                                  |('+'<AdditionExpressionNode>^ multiplicative_expression))*
    ;

multiplicative_expression
    // Ugly in the same way as additive_expression, for the same reasons
    // (token '*').
    :	cast_expression (('*'<MultiplicativeExpressionNode>^ cast_expression)
                        |('/'<MultiplicativeExpressionNode>^ cast_expression)
                        |('%'<MultiplicativeExpressionNode>^ cast_expression))*
    ;

cast_expression
    :	unary_expression
    |	'(' type_name ')' cast_expression
        -> ^(DUMMY<CastExpressionNode> type_name cast_expression)
    ;

unary_expression
    :	postfix_expression
    |	'*'<DereferenceExpressionNode>^ cast_expression
    |	'&'<AddressExpressionNode>^ cast_expression
    |	'+'<UnaryArithmeticExpressionNode>^ cast_expression
    |	'-'<UnaryArithmeticExpressionNode>^ cast_expression
    |	'~'<BitwiseNegationExpressionNode>^ cast_expression
    |	'!'<LogicalNegationExpressionNode>^ cast_expression
    |	sizeof_expression
    |	('++'|'--') unary_expression
    ;

sizeof_expression
    :	'sizeof' (unary_expression | '(' type_name ')')
    ;

postfix_expression
    :	primary_expression
        (   '[' expression ']'
        |   '(' (assignment_expression (',' assignment_expression)*)? ')'
        |   '.' identifier
        |   '->' identifier
        |   '++'
        |   '--'
        )*
    ;

primary_expression
    :	identifier -> ^(DUMMY<VariableExpressionNode> identifier)
    |	constant
    |	string_literal
    |	'('! expression ')'!
    ;

// Parser -> Lexer mapping

identifier
    :	ID
    ;

constant
    :	INTEGER -> ^(DUMMY<IntegerConstantNode> INTEGER)
    |	FLOAT
    |	CHAR
    ;

string_literal
    :	STRING
    ;

assignment_operator
    // This has to be a parser rule, not a lexer rule, because otherwise
    // the parser won't be able to pick up the '=' token used elsewhere.
    :	'='
    |	'*='
    |	'/='
    |	'%='
    |	'+='
    |	'-='
    |	'<<='
    |	'>>='
    |	'&='
    |	'^='
    |	'|='
    ;

EQUALITY_OPERATOR
    :	'=='|'!='
    ;

RELATIONAL_OPERATOR
    :	'>'|'<'|'>='|'<='
    ;

SHIFT_OPERATOR
    :	'<<'|'>>'
    ;

// Lexer

TYPE_QUALIFIER
    :	'const'|'volatile'|'restrict'
    ;

ID  :	('a'..'z'|'A'..'Z'|'_') ('a'..'z'|'A'..'Z'|'0'..'9'|'_')*
    ;

COMMENT
    :	'//' ~('\n'|'\r')* '\r'? '\n' {$channel=HIDDEN;}
    |	'/*' ( options {greedy=false;} :	. )* '*/' {$channel=HIDDEN;}
    ;

WS  :	( ' '
    |	'\t'
    |	'\r'
    |	'\n'
        ) {$channel=HIDDEN;}
    ;

STRING
    :	'"' ( ESC_SEQ | ~('\\'|'"') )* '"'
    ;

INTEGER
    :	DECIMAL INT_SUF?
    |	OCTAL INT_SUF?
    |	HEXADECIMAL INT_SUF?
    ;

fragment
DECIMAL
    :	('1'..'9') ('0'..'9')*
    ;

fragment
OCTAL
    :	'0' ('0'..'7')*
    ;

fragment
HEXADECIMAL
    :	'0' ('x'|'X') HEX_DIGIT+
    ;

fragment
HEX_DIGIT
    :	('0'..'9'|'a'..'f'|'A'..'F')
    ;

fragment
INT_SUF
    :	('u'|'U') ('l'|'L')?
    |	('u'|'U') ('ll'|'LL')
    |	('l'|'L') ('u'|'U')?
    |	('ll'|'LL') ('u'|'U')?
    ;

FLOAT
    :	DEC_FLOAT
//  |	HEX_FLOAT Do we really need this ?
    ;

fragment
DEC_FLOAT
    :	FRAC EXP? ('f'|'l'|'F'|'L')?
    |	('0'..'9')+ EXP ('f'|'l'|'F'|'L')?
    ;

fragment
FRAC
    :	('0'..'9')* '.' ('0'..'9')+
    |	('0'..'9')+ '.'
    ;

fragment
EXP
    :	('e'|'E') ('+'|'-')? ('0'..'9')+
    ;

CHAR
    :	'\'' ( ESC_SEQ | ~('\''|'\\') ) '\''
    ;

fragment
ESC_SEQ
    :	'\\' ('b'|'t'|'n'|'f'|'r'|'\"'|'\''|'\\')
    |	UNICODE_ESC
    |	OCTAL_ESC
    ;

fragment
OCTAL_ESC
    :	'\\' ('0'..'3') ('0'..'7') ('0'..'7')
    |	'\\' ('0'..'7') ('0'..'7')
    |	'\\' ('0'..'7')
    ;

fragment
UNICODE_ESC
    :	'\\' 'u' HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT
    ;
