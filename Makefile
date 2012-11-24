GRAMMAR := c_grammar

run: build
	python main.py test/first.c

build: output/$(GRAMMAR)Parser.py

output/$(GRAMMAR)Parser.py: grammar/$(GRAMMAR).g
	java -jar ../antlr-3.4-complete.jar -fo output $<

edit:
	java -jar ../antlrworks-1.4.3.jar

clean:
	rm -rf output/
