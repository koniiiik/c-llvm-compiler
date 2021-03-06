GRAMMAR := c_grammar
ANTLR ?= java -jar ../antlr-3.1.3.jar
ANTLRWORKS ?= java -jar ../antlrworks-1.2.3.jar
LLI ?= lli

SAMPLES = trivial pointers statements functions arrays struct typedef simple fibonacci 99

run: $(addprefix test/,$(addsuffix .ll,$(SAMPLES)))

$(foreach sample,$(SAMPLES),$(eval \
$(sample): test/$(sample).ll))

test/%.ll: test/%.c build
	@echo
	@echo ===============================================
	@echo
	bin/c_llvm.py $<
	# to see the code use: cat $@
	$(LLI) $@

build: c_llvm/parser/$(GRAMMAR)Parser.py c_llvm/parser/__init__.py

c_llvm/parser/$(GRAMMAR)Parser.py: grammar/$(GRAMMAR).g
	$(ANTLR) -fo c_llvm/parser $<

c_llvm/parser/__init__.py:
	touch c_llvm/parser/__init__.py

edit:
	$(ANTLRWORKS)

clean:
	rm -rf c_llvm/parser
	rm -rf test/*.ll
