
from sys import stderr
from sly import Lexer

keywords = set("""
ADD ALL ALTER AND AS ASC BEGIN BETWEEN BOOLEAN BTREE BY BYTE
CALL CASE CHAR CHECK CONSTRAINT CONTINUE COUNT CREATE CROSS CURRENT
DATE DATETIME DAY DECIMAL DEFAULT DEFINE DELETE DESC DISTINCT DOCUMENT DROP
EACH ELIF ELSE END EXCEPTION EXECUTE EXISTS EXIT DISABLED
FIRST FOR FOREACH FOREIGN FRACTION FROM FULL FUNCTION BLOB
GLOBAL GROUP HAVING HIGH HOUR TEXT LIST SKIP CONSTRAINTS
IF IMMEDIATE IN INDEX INNER INSERT INT INT8 INTEGER INTERVAL INTO IS
JOIN KEY LEFT LET LIKE LOW LVARCHAR COMMIT TRANSACTION WORK
MATCHED MATCHES MEDIUM MERGE MINUTE MONTH MULTISET NEW NOT NULL
OF OLD ON OR ORDER OUTER PRIMARY PROCEDURE
RAISE REFERENCES REFERENCING RESUME RETURN RETURNING RETURNS REVOKE RIGHT ROW
SECOND SELECT SERIAL SET SMALLINT STATISTICS STEP SYNONYM SYSTEM
TABLE TEMP THEN TO TODAY LEADING TRAILING BOTH TRIGGER TRIM TRUNCATE
UNION UNIQUE UNIQUE UPDATE USING CONNECT FINAL INIT
VALUE VALUES VARCHAR VARIANT VIEW ROLE SUBSTRING
WHEN WHERE WHILE WITH YEAR BEFORE ENABLED
LOCK MODE WAIT SHARE EXCLUSIVE UNLOCK UNITS
SEQUENCE INCREMENT MINVALUE MAXVALUE NOMINVALUE NOMAXVALUE NOCACHE CACHE NOORDER GRANT DBA AGGREGATE ITER COMBINE RESTART
START PUBLIC USAGE LANGUAGE NVL
ELSIF LOOP LIMIT
""".split())

class TooManyErrors(Exception):
    pass

class SqlLexer(Lexer):
    literals = { ';', ',', '(', ')', '.', '=', '+', '-', '*', '/', '<', '>', '[', ']', ':', '@', '{', '}' }
    tokens = {
        CHAR, DECIMAL, DATE, INT, INT8, BYTE, BOOLEAN, SMALLINT, INTEGER, LVARCHAR, SERIAL, VARCHAR,
        YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, FRACTION, NVL,
        IF, LOCK, MODE, WAIT, SHARE, EXCLUSIVE, UNLOCK, UNITS,
        SEQUENCE, INCREMENT, MINVALUE, MAXVALUE, NOMINVALUE, NOMAXVALUE, NOCACHE, CACHE, NOORDER, GRANT, DBA, AGGREGATE, ITER, COMBINE,
        CONTINUE, RESTART, START, PUBLIC, USAGE, LANGUAGE,
        ELIF, BEFORE, CONSTRAINTS,
        FUNCTION, TEXT, BLOB,
        RETURN, DISABLED,
        RETURNS, SKIP, SUBSTRING,
        TRIM, LIST, ENABLED,
        TRAILING, LEADING, BOTH,
        ASC, COMMIT, TRANSACTION, WORK,
        DESC, FINAL, INIT,
        GLOBAL,
        RETURNING,
        SYSTEM,
        EXISTS,
        EXIT,
        DEFINE,
        DOCUMENT,
        CONNECT,
        ROLE,
        LET,
        ALTER,
        OF,
        WITH,
        VARIANT,
        VALUE,
        REFERENCING,
        OLD,
        NEW,
        EACH,
        ROW,
        CALL,
        EXECUTE,
        STEP,
        IMMEDIATE,
        TRIGGER,
        BETWEEN,
        RAISE,
        EXCEPTION,
        ADD,
        COUNT,
        WHILE,
        FOREIGN,
        REFERENCES,
        CASE,
        BEGIN,
        END,
        WHEN,
        THEN,
        ELSE,
        RESUME,
        STATISTICS,
        HIGH,
        MEDIUM,
        LOW,
        TRUNCATE,
        ALL,
        AND,
        OR,
        MATCHES,
        MATCHED,
        INNER,
        LIKE,
        AS,
        BTREE,
        CAST,
        IS,
        CROSS,
        CREATE,
        UNION,
        CONCAT,
        DATETIME,
        INTERVAL,
        SET,
        DEFAULT,
        DROP,
        FOR,
        FOREACH,
        FROM,
        INDEX,
        INTO,
        VALUES,
        UINT,
        NAME,
        NE1,
        NE2,
        GE,
        LE,
        NOT,
        EQ,
        NULL,
        ON,
        PROCEDURE,
        PG_HERE,
        REVOKE,
        SELECT,
        STRING,
        SYNONYM,
        TABLE,
        TEMP,
        TO,
        MULTISET,
        UNIQUE,
        USING,
        VIEW,
        PRIMARY,
        KEY,
        TODAY,
        CURRENT,
        CONSTRAINT,
        CHECK,
        FIRST,
        JOIN,
        RIGHT,
        INSERT,
        WHERE,
        ORDER,
        DELETE,
        OUTER,
        HAVING,
        LEFT,
        BY,
        FULL,
        UPDATE,
        MERGE,
        GROUP,
        UNIQUE,
        DISTINCT,
        IN,
    }
    
    @_(r'/\*(.|\n)+?\*/')
    def ignore_multi_line_comment_1(self, t):
        self.lineno += t.value.count('\n')
    @_(r'{(.|\n)+?}')
    def ignore_multi_line_comment_2(self, t):
        self.lineno += t.value.count('\n')
    ignore_line_comment = r'--.*(?=\n)'
    ignore = ' \t'
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)
    
    # Tokens
    #NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
    @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    def NAME(self, t):
        if t.value.upper() in keywords:
            t.value = t.type = t.value.upper()
        return t

    CONCAT = r'\|\|'
    EQ = r'=='
    NE1 = r'!='
    NE2 = r'<>'
    GE = r'>='
    LE = r'<='
    CAST = r'::'
    UINT = r'[0-9]+'
    STRING = r"""("[^"]*")+|('[^']*')+"""
    PG_HERE = r'\$\$'

    def tokenize(self, text, onerror=None, maxerrors=1000000):
        self.maxerrors = maxerrors
        self.errcount = 0
        self.onerror = onerror
        return super().tokenize(text)

    def error(self, t):
        if len(t.value) > 10:
            t.value = t.value[:10] + '...'
        stderr.write("LexError: {}\n".format(t))
        self.index += 1
        if self.onerror:
            self.onerror(self, t)
        self.errcount += 1
        if self.errcount >= self.maxerrors:
            raise TooManyErrors()
