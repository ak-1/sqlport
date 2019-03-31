## sqlport - aspires to port Informix SQL to PostgreSQL

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

### Supported transformations

#### keywords as names

- Informix: `all`, `end`, `default`, ...
- Postgres: not allowed; add underscore at the end, e.g. `all_`, `end_`, `default_`, ...

#### variable declarations

- Informix: DEFINE x integer
- Postgres: x integer

#### multi-variable declarations

- Informix: DEFINE x, y integer
- Postgres: No multi-variable declarions; convert to individual declarations

#### data types

| Informix  | Postgres            |
| --------- | ------------------- |
| `lvarchar` | `varchar` |
| `varchar(x,y)`   | `varchar(x)`      |
| `byte` | `bytea` |

#### select into temp

- Informix: `SELECT ... INTO TEMP x`
- Postgres: `CREATE TEMP TABLE x AS SELECT ...`

#### select unique

- Postgres: `SELECT UNIQUE ...`
- Informix: `SELECT DISTINCT ...`

#### string literals

- Informix: `"alright"`
- Postgres: only allows single quoted strings; double quoted strings are converted to single quoted

#### date/time literals

| Informix  | Postgres            |
| --------- | ------------------- |
| `current` | `current_timestamp` |
| `today`   | `current_date`      |

#### nvl

- Informix: `nvl(x, y)`
- Postgres: `coalesce(x, y)`

#### constraints

- Informix: `ALTER TABLE ADD CONSTRAINT PRIMARY KEY ...`
- Postgres: `ALTER TABLE ADD PRIMARY KEY ...`

#### create procedure

| Informix | Postgres |
| -------- | -------- |
| `CREATE PROCEDURE` | `CREATE FUNCTION` |
| `RETURNING` | `RETURNS` |


### Partial support

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
- Status: limited convertion to ANSI JOINs

#### exception handlers and error codes

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
- Status: Only a few error codes are mapped; WITH RESUME is not supported

#### decimal

- Informix: `decimal(20)`
- Postgres: If you omit the scale in Postgres it default to zero.

#### matches

- Informix: `matches "*[a-z]?"`
- Postgres: `similar to "%[a-z]_"`
- Status: This is converted for literal string patterns, but not if the pattern is a variable.

#### slice

- Informix: `text[2,4]`
- Postgres: `substring(text from 2 for 3)`
- Status: This is automatically converted. However this does not work if the slice is on the left side of a `let` statement (variable assignment).

### Unsupported

#### constraint names

- Postgres: contraint name must differ from table name
- Status: fixme

