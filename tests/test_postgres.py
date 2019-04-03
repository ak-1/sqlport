
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

def test_first():
    i = "select first 1 a from b"
    p = "SELECT a FROM b LIMIT 1;"
    assert port(i) == p

def test_keywords():
    i = "select all, end from default"
    p = "SELECT all_, end_ FROM default_;"
    assert port(i) == p

def test_outer():
    i = "select 1 from a, outer(b) where a.x = b.x"
    p = "SELECT 1 FROM a LEFT JOIN b ON a.x = b.x;"
    assert port(i) == p

def test_create_procedure():
    i = """
    create procedure test()
    end procedure
    """
    p = """
    CREATE OR REPLACE FUNCTION test() RETURNS VOID AS $$
    BEGIN
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)
    i = """
    create procedure test() returning int
    end procedure
    """
    p = """
    CREATE OR REPLACE FUNCTION test() RETURNS INT AS $$
    BEGIN
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)

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

def test_create_procedure_if():
    i = ifxproc("""
    if a = 1 then
      call a();
    elif a = 2 then
      call b();
    else
      call c();
    end if
    """)
    p = pgproc("""
    if a = 1 then
      select a();
    elsif a = 2 then
      select b();
    else
      select c();
    end if;
    """)
    assert tokens(port(i)) == tokens(p)

def test_create_procedure_while():
    i = ifxproc("""
    while 1=1
      call x();
    end while
    """)
    p = pgproc("""
    while 1=1 loop
      select x();
    end loop;
    """)
    assert tokens(port(i)) == tokens(p)

def test_create_procedure_select():
    i = """
    select first 1 a.c1, b.c2
    from a, b
    where a.c1 = b.c1
      and a.c3 = 2
    group by 1, 2
    having sum(a.c4) > 10
    order by 1, 2
    """
    p = """
    select a.c1, b.c2
    from a, b
    where a.c1 = b.c1
      and a.c3 = 2
    group by 1, 2
    having sum(a.c4) > 10
    order by 1, 2
    limit 1;
    """
    assert tokens(port(i)) == tokens(p)

def test_create_procedure_delete():
    i = """
    delete from a where 1=1;
    """
    assert tokens(port(i)) == tokens(i)

def test_create_procedure_insert_values():
    i = """
    insert into a values (1, 2);
    """
    assert tokens(port(i)) == tokens(i)
    i = """
    insert into a (c1, c2) values (1, 2);
    """
    assert tokens(port(i)) == tokens(i)

def test_create_procedure_insert_select():
    i = """
    insert into a select * from b;
    """
    assert tokens(port(i)) == tokens(i)
    i = """
    insert into a (c1, c2) select c1, c2 from b where 1=1;
    """
    assert tokens(port(i)) == tokens(i)

def test_create_procedure_update():
    i = """
    update a set x = 1;
    """
    assert tokens(port(i)) == tokens(i)
    i = """
    update a set x = 1, y = 2 where x > 1;
    """
    assert tokens(port(i)) == tokens(i)
    i = """
    update a set (x, y) = (y, x) where x != y;
    """
    assert tokens(port(i)) == tokens(i)

def test_create_procedure_update():
    i = """
    update a set x = 1;
    """
    assert tokens(port(i)) == tokens(i)
    i = """
    update a set x = 1, y = 2 where x > 1;
    """
    assert tokens(port(i)) == tokens(i)
    i = """
    update a set (x, y) = (y, x) where x != y;
    """
    assert tokens(port(i)) == tokens(i)
