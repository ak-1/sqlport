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

### support

#### keywords as names

- Informix: `all`, `end`, `default`, ...
- Postgres: not allowed
- Status: done; add underscore at the end, e.g. `all_`, `end_`, `default_`, ...

#### constraint names

- Postgres: contraint name must differ from table name
- Status: fixme

#### variable declarations

- Informix: DEFINE x integer
- Postgres: x integer
- status: done

- Informix: DEFINE x, y integer
- Postgres: Multi-variable declarions are not supported.
- status: done; convert to individual declarations

#### data types

- Informix: lvarchar
- Postgres: varchar
- status: done

#### foreach

- Informix:
  ```
  FOREACH SELECT a, b INTO x, y FROM ...
  ...
  END FOREACH
  ```
- Postgres:
  ```
  FOR record IN SELECT a AS x, b AS y
  FROM ... LOOP
  ...
  X := record x;
  y := record y;
  ...
  END LOOP;
  ```
- Status: done

Just using the record type would be preferable. 

#### outer

- Informix: FROM a, outer(b)
- Postgres: not supported
- status: limited convertion to ANSI JOINs

#### string literals

- Informix: "alright"
- Postgres: only allows single quoted strings
- Status: done; double quoted strings are converted to single quoted

#### exception handlers

- Informix:
  ```
  ON EXCEPTION IN (-206, -958)
  ...
  END EXCEPTION
  ```
- Postgres:
  ```
  BEGIN
  ...
  EXCEPTION
  WHEN undefined_table OR duplicate_table THEN
  ...
  END
  ```
- Status: limited support; Only a few error codes are mapped; WITH RESUME is not supported
