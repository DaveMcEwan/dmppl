
MAIN := treebalance

PERCENT := %

default: build

plots:
	./treebalance.py -p --wmax 300

tables:
	./treebalance.py -t -o results.txt --wmax 300

dump:
	./treebalance.py -d -o results.yml --wmax 300

rebuild:
	pdflatex -interaction=batchmode $(MAIN)

build:
	pdflatex $(MAIN)
	-bibtex -terse $(MAIN)
	pdflatex -interaction=batchmode $(MAIN)
	pdflatex -interaction=batchmode $(MAIN)

full: clean
	pdflatex $(MAIN)
	bibtex -terse $(MAIN)
	pdflatex -interaction=batchmode $(MAIN)
	pdflatex -interaction=batchmode $(MAIN)

open: build
	xdg-open $(MAIN).pdf

.PHONY: clean
clean:
	-kill $(PERCENT)1 $(PERCENT)2 $(PERCENT)3
	rm -f *.aux
	rm -f *.bbl
	rm -f *.blg
	rm -f *.lof
	rm -f *.log
	rm -f *.lot
	rm -f *.out
	rm -f *.toc
	rm -f *.pyc
	rm -f *.pyo
	rm -f $(MAIN).pdf

