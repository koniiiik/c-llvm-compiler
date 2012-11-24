#!/usr/bin/env python
from __future__ import absolute_import
import antlr3
import sys
# Pop the first entry which is the path to the directory containing this
# script.
sys.path.pop(0)
from c_llvm.parser.c_grammarLexer import c_grammarLexer
from c_llvm.parser.c_grammarParser import c_grammarParser

# input = '...what you want to feed into the parser...'
# char_stream = antlr3.ANTLRStringStream(input)
# or to parse a file:
char_stream = antlr3.ANTLRFileStream(sys.argv[1])
# or to parse an opened file or any other file-like object:
# char_stream = antlr3.ANTLRInputStream(file)

lexer = c_grammarLexer(char_stream)
tokens = antlr3.CommonTokenStream(lexer)
parser = c_grammarParser(tokens)
parser.program()
