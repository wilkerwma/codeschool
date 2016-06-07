HTML = main.html
MINIFIED = $(HTML:.html=.min.html)
VULCANIZED = $(HTML:.html=.vulcanized.html)

all: $(MINIFIED)

#%.min.html: %.vulcanized.html 
#	html-minifier $< --collapse-inline-tag-whitespace --collapse-whitespace --conservative-collapse --html-5 --remove-tag-whitespace --minify-js --minify-css > $@
    
%.min.html: %.vulcanized.html 
	html-minifier $< --minify-js --minify-css > $@

main.vulcanized.html: main.html
	vulcanize -o $@ $< --inline-scripts --inline-css --exclude "../bower_components/ace-builds/src-min/ace.js"
    
%.vulcanized.html: %.html
	vulcanize -o $@ $< --inline-scripts --inline-css

clean:
	rm $(MINIFIED) $(VULCANIZED) -f

