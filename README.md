c-llvm-compiler
===============

This is a compiler from [C][] to the [LLVM assembly language][LLVM]. It is
written in Python and uses ANTLR3 as the parser generator.


[C]: http://www.open-std.org/jtc1/sc22/wg14/www/docs/n1256.pdf
     "The C language specification"
[LLVM]: http://llvm.org/docs/LangRef.html
        "LLVM Language Reference Manual"


Setting up the environment
--------------------------

To set up the environment correctly, we need [antlr 3.1.3][antlr], Python
2.7 and [virtualenv][]. Just follow these instructions:

 1. install the prerequisites, for example

        # aptitude install python2.7 python-virtualenv

 2. clone the repository

        $ git clone https://github.com/koniiiik/c-llvm-compiler.git

 3. create a virtualenv

        $ virtualenv --distribute --no-site-packages -p python2.7 env-c-llvm

    This creates a new directory, `env-c-llvm`, containing a Python
    virtualenv. This is useful to install Python packages into, isolated
    from the rest of your system.

 4. activate the virtualenv by sourcing the `activate` script in your
    shell

        $ . env-c-llvm/bin/activate

    You'll have to perform this step each time you want to work with the
    compiler. After this your shell prefix should start with
    `(env-c-llvm)`.

 5. add the cloned git repository to the env's Python path

        $ echo "$HOME/repos/git/c-llvm-compiler" > env-c-llvm/lib/python2.7/site-packages/c_llvm.pth

 6. install the ANTLR3 runtime in your env

        (env-c-llvm) ... $ pip install -r c-llvm-compiler/requirements.txt

 7. download the antlr JAR one level above the git repository

        $ wget -S http://www.antlr.org/download/antlr-3.1.3.jar

All done!

To regenerate the lexer and parser from the ANTLR grammar, use

    $ make

This rebuilds the lexer and parser from the grammar, stores the output in
`grammar/output` and then copies the result into the `c_llvm` package
where it can be picked up by the Python code.

Since newer versions of antlr don't support Python output properly, it is
necessary to use an older version of antlrworks as well (as it bundles its
own version of antlr). The correct version of antlrworks containing
antlr-3.1.3 has been found to be 1.2.3 which can be downloaded from
[here][antlrworks1] or [here][antlrworks2].


[antlr]: http://www.antlr.org/download/antlr-3.1.3.jar
[virtualenv]: http://www.virtualenv.org/en/latest/
[antlrworks1]: http://www.java2s.com/Code/Jar/a/Downloadantlrworks123jar.htm
[antlrworks2]: http://people.ksp.sk/~johnny64/antlrworks-1.2.3.jar


Differences from C99 and known issues
-------------------------------------

 *  incomplete types are not supported (arrays, function declarations)
 *  variable-length arrays are not supported
 *  function definitions and declarations with empty parentheses specify a
    function that takes no arguments, as opposed to incomplete types;
    declarations like `int a(void)` are not supported
 *  no `union` type support
 *  no compound literals
 *  no multi-character char literals
 *  no unicode/widechar character/string literals
 *  variables of type pointer to function have not been tested
 *  type composition is not supported obviously (since we don't support
    incomplete types anyway)
 *  LLVM 3.1 doesn't seem to support forward function declarations while
    2.9 does
 *  no initializer support
