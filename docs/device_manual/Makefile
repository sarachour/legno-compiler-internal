

all: device_manual.pdf

device_manual.pdf: *.tex *.bib
	pdflatex device_manual
	bibtex device_manual
	pdflatex device_manual

clean:
	rm *.log
	rm *.pdf
	rm *.bbl
	rm *.blg
