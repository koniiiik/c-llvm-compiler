GRAMMAR := c_grammar
ANTLR ?= java -jar ../antlr-3.1.3.jar
ANTLRWORKS ?= java -jar ../antlrworks-1.2.3.jar

run: build
	python main.py test/first.c

build: c_llvm/parser/$(GRAMMAR)Parser.py

c_llvm/parser/$(GRAMMAR)Parser.py: grammar/$(GRAMMAR).g
	$(ANTLR) -fo c_llvm/parser $<

edit:
	$(ANTLRWORKS)

clean:
	rm -rf c_llvm/parser
