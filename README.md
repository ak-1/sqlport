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

### Implemented transformations

#### Data types

| Informix  | Postgres            |
| --------- | ------------------- |
| `lvarchar` | `varchar` |
| `varchar(x,y)`   | `varchar(x)`      |
| `byte` | `bytea` |
| `interval (1) year to month` | `interval` |

#### Literals

| Informix  | Postgres            |
| --------- | ------------------- |
| `current` | `current_timestamp` |
| `today`   | `current_date`      |
| `"some text"` | `'some text'` |

#### Misc

| Informix  | Postgres            |
| --------- | ------------------- |
| `SELECT FIRST 1 ...` | `SELECT ... LIMIT 1` |
| `SELECT UNIQUE ...` | `SELECT DISTINCT ...` |
| `SELECT ... INTO TEMP x` | `CREATE TEMP TABLE x AS SELECT ...` |
| `SELECT x, y, z FROM TABLE(some_function(a, b)) AS t (x, y, z)` | SELECT x, y, z FROM some_function(a, b) AS t (x, y, z) |
| `nvl(x, y)` | `coalesce(x, y)` |
| `ALTER TABLE ADD CONSTRAINT PRIMARY KEY ...` | `ALTER TABLE ADD PRIMARY KEY ...` |
| `UPDATE STATISTICS [FOR table_name]` | `ANALYZE [table_name]` |

#### Procedures

| Informix | Postgres |
| -------- | -------- |
| `CREATE PROCEDURE` | `CREATE FUNCTION` |
| `RETURNING` | `RETURNS` |
| no return value | `RETURNS void` |
| `DEFINE x integer` | `x integer` in `DECLARE` block |
| `DEFINE x, y integer` | converted to individual declarations |
| `LET x = y` | `x := y` |
| `IF ... ELIF ... END IF` | `IF ... ELSIF ... END IF` |
| `WHILE x=y ... END WHILE` | `WHILE x=y LOOP ... END LOOP` |
| `EXIT WHILE`, `EXIT FOR`, ... | `EXIT` |
| `RAISE EXCEPTION -746, 0, "some text"` | `RAISE EXCEPTION "Error: %", 'some text'` |
| semicolon optional after `END IF`, `END FOR`, ...  | semicolon always required |
| `EXECUTE PROCEDURE name(x,y)`, `CALL name(x, y)` | `SELECT name(x, y)`, `PERFORM name(x, y)` |

#### MERGE

- Informix:
  ```
  MERGE INTO x USING y ON y.y1 = x.x1
  WHEN MATCHED THEN UPDATE SET x.x2 = y.y2
  WHEN NOT MATCHED THEN INSERT (x1, x2) VALUES (y1, y2)
  ```
- Postgres:
  ```
  INSERT INTO x (x1, x2)
  SELECT y1, y2 FROM y
  ON CONFLICT (x1) DO UPDATE SET x1 = y1, x2 = y2
  ```
- `MERGE` without WHEN NOT MATCHES THEN INSERT is translated into UPDATE FROM syntax.

#### Keywords as names

- Informix: `all`, `end`, `default`, ...
- Postgres: not allowed
- append underscore, e.g. `all_`, `end_`, `default_`, ...

#### Constraint names

- Postgres: contraint name must differ from table name
- Prefix constraint name, e.g. with `pk_`

### Limited transformations

#### SYSTEM

- Informix: `SYSTEM "sleep 10"`
- Postgres: `PERFORM system('sleep 10')`
- The `system` function has to be defined separately

#### ADD column BEFORE

- Informix: `ALTER TABLE x ADD a int BEFORE c`
- Postgres: `BEFORE` is not supported
- `BEFORE c` is dropped

#### FOREACH

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
- Using the record type directly could be cleaner.

#### OUTER(table)

- Informix: `SELECT ... FROM a, OUTER(b)`
- Postgres: not supported
- Supports limited translation to ANSI JOINs for simple cases.

#### Exception handlers and error codes

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
- Only a few error codes are mapped
- WITH RESUME is not supported
- ON EXCEPTION without error code is not supported

#### Unscaled decimal

- Informix: `decimal(20)`
- If you omit the scale in Informix it is not fixed.
- If you omit the scale in Postgres it defaults to zero.
- Currently these cases are translated to `DECIMAL(30,10)`.

#### MATCHES

- Informix: `MATCHES "*[a-z]?"`
- Postgres: `SIMILAR TO "%[a-z]_"`
- This is converted for literal string patterns, but not if the pattern is a variable.

#### Slice

- Informix: `text[2,4]`
- Postgres: `substring(text from 2 for 3)`
- This is automatically converted. However this does not work if the slice is on the left side of a `let` statement (variable assignment).

### Not Supported

| Informix | Postgres |
| -------- | -------- |
| `multiset(integer)` | |
| `SET LOCK MODE` | |
| `DEFINE GLOBAL` | |
| `database[@server]:name` | |
| `sys*` tables | |
| `LET x, y = y, x` | |
| `GRANT`, `REVOKE` | |
| multiple return values | use `record` type or `OUT` paramters |
| named return parameters | |

If something is not automatically translated a `NOT_SUPPORTED` message is included in the output.
