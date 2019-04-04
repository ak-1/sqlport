
from . support import onerror, tokens, port

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
    CREATE OR REPLACE FUNCTION test() RETURNS INT AS $$
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
    CREATE OR REPLACE FUNCTION test() RETURNS INT AS $$
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
# def test_on_exception_in():
# def test_with_resume():
# def test_if_list():
# def test_if_else():
# def test_document():
# def test_call_stmt():
# def test_args():
# def test_create_trigger():
# def test_create_view():
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
# def test_create_aggregate():
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
# def test_literal():
# def test_type_expr():
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
