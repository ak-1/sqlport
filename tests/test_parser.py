
from . support import onerror, tokens, port, pgproc, ifxproc

def test_toplevel_list():
    i = """
    select a from b;
    select a from b;    
    """
    assert tokens(port(i)) == tokens(i)
    
def test_toplevel():
    i = """
    select a from b;
    """
    assert tokens(port(i)) == tokens(i)
    
def test_statement():
    i = """
    """
    assert tokens(port(i)) == tokens(i)
    
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
    create function test() returning int
    end function
    """
    p = """
    CREATE OR REPLACE FUNCTION test() RETURNS INT AS $$
    BEGIN
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)
    
# def test_procedure():
# def test_opt_semicolon():

def test_with_variant():
    i = """
    create function test() returning int with ( variant )
    end function
    """
    p = """
    CREATE OR REPLACE FUNCTION test() RETURNS INT VOLATILE AS $$
    BEGIN
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)
    i = """
    create function test() returning int with ( not variant )
    end function
    """
    p = """
    CREATE OR REPLACE FUNCTION test() RETURNS INT IMMUTABLE AS $$
    BEGIN
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)

def test_parameter_list():
    i = """
    create procedure test(a int)
    end procedure
    """
    p = """
    CREATE OR REPLACE FUNCTION test(a int) RETURNS VOID AS $$
    BEGIN
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)
    i = """
    create procedure test(a int, b int)
    end procedure
    """
    p = """
    CREATE OR REPLACE FUNCTION test(a int, b int) RETURNS VOID AS $$
    BEGIN
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)

def test_parameter():
    i = """
    create procedure test(a varchar(100,50) default "foo", b int default 0)
    end procedure
    """
    p = """
    CREATE OR REPLACE FUNCTION test(a varchar(100) default 'foo', b int default 0) RETURNS VOID AS $$
    BEGIN
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)

def test_returning():
    i1 = """
    create function test() returning int
    end function
    """
    i2 = """
    create function test() returns int
    end function
    """
    p = """
    CREATE OR REPLACE FUNCTION test() RETURNS INT AS $$
    BEGIN
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i1)) == tokens(p)
    assert tokens(port(i2)) == tokens(p)

# def test_returning_list():
# def test_return_type():

def test_declare_list():
    i = """
    create procedure test()
    define a int;
    define b int;
    define c, d int;
    end procedure
    """
    p = """
    CREATE OR REPLACE FUNCTION test() RETURNS VOID AS $$
    DECLARE
    a int;
    b int;
    c int;
    d int;
    BEGIN
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)

# def test_declare_step():
# def test_declare_stmt():
# def test_proc_list():
# def test_proc_step():

def test_proc_stmt_let():
    i = """
    create procedure test()
    define a int;
    define b int;
    let a = a + b;
    let a, b = b, a;
    end procedure
    """
    p = """
    CREATE OR REPLACE FUNCTION test() RETURNS VOID AS $$
    DECLARE
    a int;
    b int;
    BEGIN
    a := a + b;
    a, b := b, a;
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)

def test_proc_stmt_raise():
    i = """
    create procedure test()
    raise exception -746, 0, "message";
    end procedure
    """
    p = """
    CREATE OR REPLACE FUNCTION test() RETURNS VOID AS $$
    BEGIN
    raise exception 'Error: %', 'message';
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)

def test_proc_stmt_return():
    i = """
    create procedure test() returns int
    return 1;
    end procedure
    """
    p = """
    CREATE OR REPLACE FUNCTION test() RETURNS INT AS $$
    BEGIN
    return 1;
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)

# def test_proc_expr():
# def test_let_list():

# def test_let_expr():
def test_on_exception_in():
    i = ifxproc("""
    ON EXCEPTION IN (-206, -218)
    let x = 0;
    END EXCEPTION
    let x = 1;
    """)
    p = pgproc("""
    x := 1;
    EXCEPTION
    WHEN undefined_table OR NOT_SUPPORTED: -218 THEN
    x := 0;
    """)
    assert tokens(port(i)) == tokens(p)
    i = ifxproc("""
    ON EXCEPTION IN (-206)
    END EXCEPTION WITH RESUME
    let x = 1;
    """)
    p = pgproc("""
    x := 1;
    EXCEPTION
    WHEN undefined_table THEN
    NOT_SUPPORTED: WITH RESUME
    """)
    assert tokens(port(i)) == tokens(p)

# def test_with_resume():
# def test_if_list():
# def test_if_else():
def test_if():
    i = ifxproc("""
    if a=1 then
    call x();
    elif a=2 then
    call y();
    else
    call z();
    end if
    """)
    p = pgproc("""
    if a=1 then
    select x();
    elsif a=2 then
    select y();
    else
    select z();
    end if;
    """)
    assert tokens(port(i)) == tokens(p)

# def test_document():
# def test_call_stmt():
def test_call_stmt():
    i = """
    call x();
    execute procedure y(1);
    execute procedure z(1,2);
    """
    p = """
    select x();
    select y(1);
    select z(1,2);
    """
    assert tokens(port(i)) == tokens(p)

# def test_args():
# def test_create_trigger():
# def test_create_view():
def test_create_view():
    i = """
    create view x (a, b) as
    select c, d from y
    """
    p = """
    CREATE OR REPLACE VIEW x (a, b) as
    select c, d from y;
    """
    assert tokens(port(i)) == tokens(p)

# def test_set_lock_mode():
# def test_alter_table_stmt():
# def test_merge_stmt():
# def test_merge_case_list():
# def test_merge_case():
# def test_update_stmt():
# def test_assignment_list():
# def test_assignment():
# def test_truncate_stmt():
# def test_update_statistics_stmt():
# def test_statistics_mode():
# def test_for_table():
# def test_grant_stmt():
# def test_permission():
# def test_grant_role():
# def test_grant_on():
# def test_grant_as():
# def test_revoke_stmt():
# def test_grant_entity():
# def test_arg_type_list():

def test_create_aggregate():
    i = """
    create aggregate test with (
    INIT = init,
    ITER = iter,
    COMBINE = combine,
    FINAL = final
    )
    """
    p = """
    create aggregate test (NOT_SUPPORTED: arg_data_type) (
    initial_condition = NOT_SUPPORTED: init,
    sfunc = iter,
    ffunc = final
    );
    """
    assert tokens(port(i)) == tokens(p)

# def test_drop_stmt():
# def test_kind():
# def test_lock_table():
# def test_unlock_table():
# def test_create_index():
# def test_unique():
# def test_using_btree():
# def test_create_synonym():
# def test_create_sequence():
# def test_alter_sequence():
# def test_increment():
# def test_start_with():
# def test_minvalue():
# def test_maxvalue():
# def test_seq_cache():
# def test_seq_order():
# def test_constraint():
# def test_foreign_key_constraint():
# def test_primary_key_constraint():
# def test_check_constraint():
# def test_unique_constraint():
# def test_constraint_entity_name():
# def test_column_list():
# def test_name_or_table_column():
# def test_name_list():
# def test_create_table():
# def test_temp():
# def test_if_exists():
# def test_if_not_exists():
# def test_create_table_item_list():
# def test_create_table_item():
# def test_create_table_column():
# def test_default():
# def test_not_null():
# def test_primary_key():
# def test_select():
# def test_union_list():
# def test_union_select():
# def test_simple_select():
# def test_union():
# def test_into_vars():
# def test_into():
# def test_from_expr():
# def test_join():
# def test_on_expr():
# def test_entity_ref_as():
# def test_entity_ref():
# def test_entity_name():
# def test_as_name():
# def test_delete_stmt():
# def test_insert_stmt():
# def test_insert_stmt_name_list():
# def test_first():
# def test_distinct():
# def test_where():
# def test_group_by():
# def test_having():
# def test_order_by():
# def test_order_list():
# def test_order_item():
# def test_select_column_list():
# def test_select_column():
# def test_expr_list():
# def test_expr():
# def test_and_expr():
# def test_table_column():
# def test_sub_select():
# def test_case_expr():
# def test_case_when_list():
# def test_case_when():
# def test_case_else():
def test_case():
    i = """
    select case when a=1 then 1 when a=2 then 2 else 3 end from x;
    """
    p = """
    select case when a=1 then 1 when a=2 then 2 else 3 end from x;
    """
    assert tokens(port(i)) == tokens(p)

# def test_literal():
def test_literal():
    i = """
    select 1, -1, 1.12, -1.12, "ab""cd", 'ab''cd',
    today, current
    from x
    """
    p = """
    select 1, -1, 1.12, -1.12, 'ab"cd', 'ab''cd',
    current_date, current_timestamp
    from x;
    """
    assert tokens(port(i)) == tokens(p)

def test_literal_interval():
    i = """
    select
    interval (1) year to year,
    interval (2) month to month,
    interval (1-2) year to month,
    interval (1 02:03:04.5) day to fraction,
    interval (1 02:03:04) day to second,
    interval (1 02:03) day to minute,
    interval (1 02) day to hour,
    interval (1) day to day,
    interval (02:03:04.5) hour to fraction,
    interval (02:03:04) hour to second,
    interval (02:03) hour to minute,
    interval (02) hour to hour,
    interval (03:04.5) minute to fraction,
    interval (03:04) minute to second,
    interval (03) minute to minute,
    interval (04.5) second to fraction,
    interval (04) second to second,
    interval (5) fraction to fraction
    from x
    """
    p = """
    select
    interval '1 year',
    interval '2 months',
    interval '1 year 2 months',
    interval '1 day 2 hours 3 minutes 4 seconds NOT_SUPPORTED: 5 fractions',
    interval '1 day 2 hours 3 minutes 4 seconds',
    interval '1 day 2 hours 3 minutes',
    interval '1 day 2 hours',
    interval '1 day',
    interval '2 hours 3 minutes 4 seconds NOT_SUPPORTED: 5 fractions',
    interval '2 hours 3 minutes 4 seconds',
    interval '2 hours 3 minutes',
    interval '2 hours',
    interval '3 minutes 4 seconds NOT_SUPPORTED: 5 fractions',
    interval '3 minutes 4 seconds',
    interval '3 minutes',
    interval '4 seconds NOT_SUPPORTED: 5 fractions',
    interval '4 seconds',
    interval 'NOT_SUPPORTED: 5 fractions'
    from x;
    """
    assert tokens(port(i)) == tokens(p)

# def test_type_expr():
def test_type_expr():
    i = """
    create procedure test()
    define r row(int, decimal(20,10));
    create table x (
    c2 set(int not null),
    c4 set(int),
    c5 list(int),
    c6 datetime year to second default current year to second,
    c7 interval hour to minute,
    c8 int,
    c9 integer default 1 not null,
    c10 decimal(20),
    c11 decimal(20,10),
    c12 char(1),
    c13 varchar(100,100) not null,
    c14 varchar(100) default "",
    c15 text,
    c16 byte,
    c17 blob in adbs,
    c18 boolean,
    c19 date,
    c20 date default today,
    c21 int8,
    c22 smallint,
    c23 lvarchar(2048)
    );
    end procedure
    """
    p = """
    CREATE OR REPLACE FUNCTION test() RETURNS VOID AS $$
    DECLARE
    r row(int, decimal(20,10));
    BEGIN
    create table x (
    c2 set(int not null),
    c4 set(int),
    c5 list(int),
    c6 timestamp default current_timestamp,
    c7 interval,
    c8 int,
    c9 integer default 1 not null,
    c10 decimal(30,10),
    c11 decimal(20,10),
    c12 char(1),
    c13 varchar(100) not null,
    c14 varchar(100) default '',
    c15 text,
    c16 bytea,
    c17 blob,
    c18 boolean,
    c19 date,
    c20 date default current_date,
    c21 int8,
    c22 smallint,
    c23 varchar(2048)
    );
    END;
    $$ LANGUAGE plpgsql;
    """
    assert tokens(port(i)) == tokens(p)

# def test_simple_type_expr():
# def test_datatype():
# def test_owner():
# def test_integer():
# def test_time_unit():
# def test_time_unit_name():
# def test_name():
# def test_empty():
# def test_parse():
# def test_error():
