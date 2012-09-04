all: test

test: test.o
	gcc -o $@ $^

clean:
	rm -f *.o
	rm -f test
