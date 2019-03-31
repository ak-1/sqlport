## sqlport - Aspires to port Informix SQL to PostgreSQL

```
$ echo 'select first 1 hello from world' | sqlport
SELECT hello FROM world LIMIT 1;
```

```
$ sqlport -h
usage: sqlport [-h] [--outfile OUTFILE | --outdir OUTDIR | --replace]
               [--file-list [FILE]] [--quiet] [--verbose] [--debug]
               [--parse-tree] [--lex] [--informix]
               [INFILE [INFILE ...]]

Ports SQL code to another dialect.

positional arguments:
  INFILE

optional arguments:
  -h, --help            show this help message and exit
  --outfile OUTFILE, -o OUTFILE
			output file path pattern with place holders: "#" =
			input file path; "%" = input file path with last file
			extension removed; "%%" = input file path with last
			two file extensions removed; ...
  --outdir OUTDIR, -d OUTDIR
                        output base directory
  --replace, -r         replace input file
  --file-list [FILE], -f [FILE]
			read file list from file or stdin
  --quiet, -q           do not output anything
  --verbose, -v         verbose output
  --debug, -D           debugging output
  --parse-tree, -T      show parse tree
  --lex, -L             show lexer output
  --informix, -i        generate informix SQL
```
