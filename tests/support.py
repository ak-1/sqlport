
from sqlport.lexer import SqlLexer
from sqlport.engine import parse
from io import StringIO

def onerror(obj, t):
    assert False

def tokens(text):
    lexer = SqlLexer()
    outfh = StringIO()
    for token in lexer.tokenize(text, onerror=None):
        outfh.write(token.value+'\n')
    return outfh.getvalue()

def port(text):
    return parse(text, onerror=onerror).render().strip()

def ifxproc(text):
    return """
    create procedure test()
    {}
    end procedure
    """.format(text)

def pgproc(text):
    return """
    CREATE OR REPLACE FUNCTION test() RETURNS VOID AS $$
    BEGIN
    {}
    END;
    $$ LANGUAGE plpgsql;
    """.format(text)
