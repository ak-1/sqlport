
from sly import Lexer

keywords = set("""
ADD ALL ALTER AND AS ASC BEGIN BETWEEN BOOLEAN BTREE BY BYTE
CALL CASE CHAR CHECK CONSTRAINT CONTINUE COUNT CREATE CROSS CURRENT
DATE DATETIME DAY DECIMAL DEFAULT DEFINE DELETE DESC DISTINCT DOCUMENT DROP
EACH ELIF ELSE END EXCEPTION EXECUTE EXISTS EXIT
FIRST FOR FOREACH FOREIGN FRACTION FROM FULL FUNCTION
GLOBAL GROUP HAVING HIGH HOUR
IF IMMEDIATE IN INDEX INNER INSERT INT INT8 INTEGER INTERVAL INTO IS
JOIN KEY LEFT LET LIKE LOW LVARCHAR
MATCHED MATCHES MEDIUM MERGE MINUTE MONTH MULTISET NEW NOT NULL
OF OLD ON OR ORDER OUTER PRIMARY PROCEDURE
RAISE REFERENCES REFERENCING RESUME RETURN RETURNING RETURNS REVOKE RIGHT ROW
SECOND SELECT SERIAL SET SMALLINT STATISTICS STEP SYNONYM SYSTEM
TABLE TEMP THEN TO TODAY TRAILING TRIGGER TRIM TRUNCATE
UNION UNIQUE UNIQUE UPDATE USING
VALUE VALUES VARCHAR VARIANT VIEW
WHEN WHERE WHILE WITH YEAR
LOCK MODE WAIT SHARE EXCLUSIVE UNLOCK UNITS
SEQUENCE INCREMENT MINVALUE MAXVALUE NOMINVALUE NOMAXVALUE NOCACHE CACHE NOORDER GRANT DBA AGGREGATE ITER COMBINE RESTART
START PUBLIC USAGE LANGUAGE NVL
""".split())

class SqlLexer(Lexer):
    literals = { ';', ',', '(', ')', '.', '=', '+', '-', '*', '/', '<', '>', '[', ']', ':', '@' }
    tokens = {
        CHAR, DECIMAL, DATE, INT, INT8, BYTE, BOOLEAN, SMALLINT, INTEGER, LVARCHAR, SERIAL, VARCHAR,
        YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, FRACTION, NVL,
        IF, LOCK, MODE, WAIT, SHARE, EXCLUSIVE, UNLOCK, UNITS,
        SEQUENCE, INCREMENT, MINVALUE, MAXVALUE, NOMINVALUE, NOMAXVALUE, NOCACHE, CACHE, NOORDER, GRANT, DBA, AGGREGATE, ITER, COMBINE,
        CONTINUE, RESTART, START, PUBLIC, USAGE, LANGUAGE,
        ELIF,
        FUNCTION,
        RETURN,
        RETURNS,
        TRIM,
        TRAILING,
        ASC,
        DESC,
        GLOBAL,
        RETURNING,
        SYSTEM,
        EXISTS,
        EXIT,
        DEFINE,
        DOCUMENT,
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
        DECIMAL,
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
    
    @_(r'{(.|\n)*?}')
    def ignore_multi_line_comment(self, t):
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

    DECIMAL = r'[0-9]+\.[0-9]*'
    CONCAT = r'\|\|'
    EQ = r'=='
    NE1 = r'!='
    NE2 = r'<>'
    GE = r'>='
    LE = r'<='
    CAST = r'::'
    UINT = r'[0-9]+'
    STRING = r"""("[^"]*")+|('[^']*')+"""

    def error(self, t):
        if len(t.value) > 10:
            t.value = t.value[:10] + '...'
        print("LexError: {}".format(t))
        #print("Illegal character '%s'" % t.value[0])
        self.index += 1
