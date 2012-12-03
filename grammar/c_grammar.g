grammar c_grammar;

options {
    language = Python;
}

@init {
    self.it_number = 0
}

translation_unit
    :	external_declaration+
    ;

external_declaration
    :	function_definition {print('found function declaration');}
    |	declaration {print('found declaration');}
    ;

function_definition
    :	declaration_specifiers identifier '(' parameter_list (',' '...')? ')' compound_statement
    ;

parameter_list
    :	parameter_declaration (',' parameter_declaration)*
    |
    ;

parameter_declaration
    :	declaration_specifiers declarator
    ;

declaration
    :	declaration_specifiers init_declarator (',' init_declarator)* ';'
    ;

init_declarator
    :	identifier
    |	identifier '=' primary_expression
    ;

declarator
    :	identifier
    |	'(' declarator ')'
    ;

declaration_specifiers // TODO
    :	type_specifier
    ;

type_specifier // TODO
    :	'int'
    ;

type_name // TODO
    :	type_specifier
    ;

// Statements

statement returns [code]
    :	labeled_statement {code=""}
    |	compound_statement {code=""}
    |	expression_statement {code=""}
    |	selection_statement {code=""}
    |	iteration_statement {code=$iteration_statement.code}
    |	jump_statement {code=""}
    ;

labeled_statement
    :	identifier ':' statement
    |	'case' constant ':' statement
    |	'default' ':' statement
    ;

compound_statement
    :	'{' block_item* '}'
    ;

block_item
    :	declaration
    |	statement {print $statement.code;}
    ;

expression_statement
    :	expression? ';'
    ;

selection_statement
    :	('if' '(' expression ')' statement 'else') => 'if' '(' expression ')' statement 'else' statement
    |	('if') => 'if' '(' expression ')' statement
    |	'switch' '(' expression ')' statement
    ;

iteration_statement returns [code]
@init {
    self.it_number+=1
}
    :	'while' {code="while"+str(self.it_number)+".cond:\n"} '(' expression ')' {code+=$expression.code+"  \%cmp = icmp ne i32 \%e, 0\n  br i1 \%cmp, label \%while"+str(self.it_number)+".body, label \%while"+str(self.it_number)+".end\nwhile"+str(self.it_number)+".body:\n"} statement {code+=$statement.code+"while"+str(self.it_number)+".end:\n"}
    |	'do' statement 'while' '(' expression ')' ';'
    |	'for' '(' expression? ';' expression? ';' expression? ')' statement
    |	'for' '(' declaration expression? ';' expression? ')' statement
    ;

// 'goto' is not supported
jump_statement
    :	'goto' identifier ';'
    |	'continue' ';'
    |	'break' ';'
    |	'return' expression? ';'
    ;

// Expressions

expression returns [code]
    :	{code="  compute expression and put result into \%e\n"} assignment_expression (',' assignment_expression)*
    ;

assignment_expression
    :	(unary_expression assignment_operator) => unary_expression assignment_operator assignment_expression
    |	conditional_expression
    ;

conditional_expression
    :	logical_or_expression ('?' expression ':' conditional_expression)?
    ;

logical_or_expression
    :	logical_and_expression ('||' logical_and_expression)*
    ;

logical_and_expression
    :	inclusive_or_expression ('&&' inclusive_or_expression)*
    ;

inclusive_or_expression
    :	exclusive_or_expression ('|' exclusive_or_expression)*
    ;

exclusive_or_expression
    :	and_expression ('^' and_expression)*
    ;

and_expression
    :	equality_expression ('&' equality_expression)*
    ;

equality_expression
    :	relational_expression (equality_operator relational_expression)*
    ;

relational_expression
    :	shift_expression (relational_operator shift_expression)*
    ;

shift_expression
    :	additive_expression (shift_operator additive_expression)*
    ;

additive_expression
    :	multiplicative_expression (additive_operator multiplicative_expression)*
    ;

multiplicative_expression
    :	cast_expression (multiplicative_operator cast_expression)*
    ;

cast_expression
    :	('(' type_name ')')* unary_expression
    ;

unary_expression
    :	postfix_expression
    |	unary_operator cast_expression
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
        )
    // Are we sure we want to support the following?
    //|	'(' type_name ')' '{' initializer_list '}'
    ;

primary_expression
    :	identifier
    |	constant
    |	string_literal
    |	'(' expression ')'
    ;

// Parser -> Lexer mapping

identifier
    :	ID
    ;

constant
    :	INTEGER
    |	CHAR
    ;

string_literal
    :	STRING
    ;

assignment_operator
    :	ASSIGNMENT_OPERATOR
    ;

equality_operator
    :	EQUALITY_OPERATOR
    ;

relational_operator
    :	RELATIONAL_OPERATOR
    ;

shift_operator
    :	SHIFT_OPERATOR
    ;

additive_operator
    :	ADDITIVE_OPERATOR
    ;

multiplicative_operator
    :	MULTIPLICATIVE_OPERATOR
    ;

unary_operator
    :	UNARY_OPERATOR
    ;

// Lexer

ID  :	('a'..'z'|'A'..'Z'|'_') ('a'..'z'|'A'..'Z'|'0'..'9'|'_')*
    ;

ASSIGNMENT_OPERATOR
    :	('*'|'/'|'%'|'+'|'-'|'<<'|'>>'|'&'|'^'|'|')? '='
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

ADDITIVE_OPERATOR
    :	'+'|'-'
    ;

MULTIPLICATIVE_OPERATOR
    :	'*'|'/'|'%'
    ;

UNARY_OPERATOR
    :	'+'|'-'|'&'|'*'|'~'|'!'
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
    :	'1'..'9' ('0'..'9')*
    ;

CHAR:	'\'' ( ESC_SEQ | ~('\''|'\\') ) '\''
    ;

fragment
HEX_DIGIT :	('0'..'9'|'a'..'f'|'A'..'F') ;

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
