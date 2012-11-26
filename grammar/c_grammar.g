grammar c_grammar;

options {
    language = Python;
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

declaration_specifiers
    :	type_specifier
    ;

type_specifier
    :	'int'
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
    :	identifier ':' statement
    |	'case' constant ':' statement
    |	'default' ':' statement
    ;

compound_statement
    :	'{' block_item* '}'
    ;

block_item
    :	declaration
    |	statement
    ;

expression_statement
    :	expression? ';'
    ;

selection_statement
    :	'if' '(' expression ')' statement ('else' statement)?
    |	'switch' '(' expression ')' statement
    ;

iteration_statement
    :	'while' '(' expression ')' statement
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

expression
    :	primary_expression
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

// Lexer

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
