EPYDOC=epydoc
DSTDOC=docstrings

doc: clean
	$(EPYDOC) --html --graph=all -v -o $(DSTDOC) pyinotify.py

clean:
	rm -rf $(DSTDOC)
