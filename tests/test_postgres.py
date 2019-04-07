
from . support import onerror, tokens, port, pgproc, ifxproc

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

def test_drop():
    i = """
    drop procedure x;
    """
    p = """
    drop function x;
    """
    assert tokens(port(i)) == tokens(p)

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

def test_create_table():
    i = """
    create table t (
    c1 int,
    c2 lvarchar(1024),
    c3 varchar(200,100),
    c4 byte,
    c5 interval year to month,
    c6 datetime year to second,
    primary key (c1) constraint t
    );
    """
    p = """
    create table t (
    c1 int,
    c2 varchar(1024),
    c3 varchar(200),
    c4 bytea,
    c5 interval,
    c6 timestamp,
    constraint pk_t primary key (c1)
    );
    """
    assert tokens(port(i)) == tokens(p)

def test_literals():
    i = """
    select today, current, "Foo ""Baz"" 'Bingo' Bar" from a;
    """
    p = """
    select current_date, current_timestamp, 'Foo "Baz" ''Bingo'' Bar' from a;
    """
    assert tokens(port(i)) == tokens(p)

def test_unqiue():
    i = """
    select unique a from b;
    """
    p = """
    select distinct a from b;
    """
    assert tokens(port(i)) == tokens(p)

def test_nvl():
    i = """
    select nvl(a, 1) from b;
    """
    p = """
    select coalesce(a, 1) from b;
    """
    assert tokens(port(i)) == tokens(p)

def test_select_into_temp():
    i = """
    select a from b into temp c;
    """
    p = """
    create temp table c as select a from b;
    """
    assert tokens(port(i)) == tokens(p)

def test_select_from_function():
    i = """
    select x, y from table(foo(a, b)) as t (x, y);
    """
    p = """
    select x, y from foo(a, b) as t (x, y);
    """
    assert tokens(port(i)) == tokens(p)
