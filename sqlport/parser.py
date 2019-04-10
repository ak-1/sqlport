
from termcolor import colored
from sys import stderr
from sly import Parser
from . lexer import SqlLexer, TooManyErrors
from . node import *
from . logger import Logger

def find_column(text, token):
    last_cr = text.rfind('\n', 0, token.index)
    if last_cr < 0:
        last_cr = 0
    column = (token.index - last_cr) + 1
    return column

class SqlParser(Parser):
    #debugfile = 'parser.out'

    log = Logger(stderr)
    
    tokens = SqlLexer.tokens

    precedence = (
#        ('left', ',', JOIN),
        ('left', OR),
        ('left', AND),
        ('nonassoc', IN, LIKE, MATCHES, BETWEEN),
        ('nonassoc', '<', '>', LE, GE, '=', EQ, NE1, NE2),
        ('nonassoc', NOT),
        ('nonassoc', ALL), # ANY SOME
        ('left', CONCAT),
        ('left', '+', '-'),
        ('left', '*', '/'),
        ('right', NAME, YEAR, MONTH), #function calls ?
        ('nonassoc', CAST),
        ('right', 'UMINUS'), # UPLUS
        # UNITS ?
        ('nonassoc', '.', '[', ']'),
        )

    @_('toplevel')
    def toplevel_list(self, p):
        return StatementList(p.toplevel)
    @_('toplevel ";" toplevel_list')
    def toplevel_list(self, p):
        return p.toplevel_list.push(p.toplevel)

    @_('statement')
    def toplevel(self, p):
        return p.statement
    @_('create_procedure')
    def toplevel(self, p):
        return p.create_procedure

    @_('create_table')
    def statement(self, p):
        return p.create_table
    @_('create_role')
    def statement(self, p):
        return p.create_role
    @_('create_view')
    def statement(self, p):
        return p.create_view
    @_('create_index')
    def statement(self, p):
        return p.create_index
    @_('create_synonym')
    def statement(self, p):
        return p.create_synonym
    @_('create_sequence')
    def statement(self, p):
        return p.create_sequence
    @_('alter_sequence')
    def statement(self, p):
        return p.alter_sequence
    @_('drop_stmt')
    def statement(self, p):
        return p.drop_stmt
    @_('lock_table')
    def statement(self, p):
        return p.lock_table
    @_('unlock_table')
    def statement(self, p):
        return p.unlock_table
    @_('grant_stmt')
    def statement(self, p):
        return p.grant_stmt
    @_('revoke_stmt')
    def statement(self, p):
        return p.revoke_stmt
    @_('create_aggregate')
    def statement(self, p):
        return p.create_aggregate
    @_('select')
    def statement(self, p):
        return p.select
    @_('delete_stmt')
    def statement(self, p):
        return p.delete_stmt
    @_('insert_stmt')
    def statement(self, p):
        return p.insert_stmt
    @_('update_stmt')
    def statement(self, p):
        return p.update_stmt
    @_('merge_stmt')
    def statement(self, p):
        return p.merge_stmt
    @_('truncate_stmt')
    def statement(self, p):
        return p.truncate_stmt
    @_('update_statistics_stmt')
    def statement(self, p):
        return p.update_statistics_stmt
    @_('alter_table_stmt')
    def statement(self, p):
        return p.alter_table_stmt
    @_('call_stmt')
    def statement(self, p):
        return p.call_stmt
    @_('create_trigger')
    def statement(self, p):
        return p.create_trigger
    @_('set_lock_mode')
    def statement(self, p):
        return p.set_lock_mode
    @_('BEGIN WORK', 'BEGIN TRANSACTION')
    def statement(self, p):
        return BeginTransaction()
    @_('COMMIT WORK', 'COMMIT TRANSACTION')
    def statement(self, p):
        return CommitTransaction()
    @_('SET CONSTRAINTS name constraint_mode')
    def statement(self, p):
        return SetConstraints(p.name, p.constraint_mode)
    @_('empty')
    def statement(self, p):
        return None

    @_('ENABLED', 'DISABLED')
    def constraint_mode(self, p):
        return p[0]
    @_('empty')
    def constraint_mode(self, p):
        return None
    
    @_("""
    CREATE procedure entity_name "(" parameter_list ")" returning with_variant opt_semicolon
    declare_list
    proc_list
    END procedure document
    """)
    def create_procedure(self, p):
        x = CreateProcedure(p.procedure0, p.entity_name, p.parameter_list, p.returning,
                            p.with_variant, p.declare_list, p.proc_list, p.document)
        x.index = p.index
        return x

    @_('FUNCTION', 'PROCEDURE')
    def procedure(self, p):
        return p[0]
    
    @_('";"', 'empty')
    def opt_semicolon(self, p):
        pass

    @_('WITH "(" VARIANT ")"')
    def with_variant(self, p):
        return True
    @_('WITH "(" NOT VARIANT ")"')
    def with_variant(self, p):
        return False
    @_('empty')
    def with_variant(self, p):
        pass

    @_('parameter "," parameter_list')
    def parameter_list(self, p):
        return p.parameter_list.push(p.parameter)
    @_('parameter')
    def parameter_list(self, p):
        return CommaList(p.parameter)
    @_('empty')
    def parameter_list(self, p):
        return CommaList()

    @_('name type_expr default')
    def parameter(self, p):
        return Parameter(p.name, p.type_expr, p.default)

    @_('RETURNING returning_list')
    def returning(self, p):
        return p.returning_list
    @_('RETURNS returning_list')
    def returning(self, p):
        return p.returning_list
    @_('empty')
    def returning(self, p):
        return None

    @_('return_type')
    def returning_list(self, p):
        return CommaList(p.return_type)
    @_('return_type "," returning_list')
    def returning_list(self, p):
        return p.returning_list.push(p.return_type)

    @_('type_expr')
    def return_type(self, p):
        return ReturnType(p.type_expr, None)
    @_('type_expr AS name')
    def return_type(self, p):
        return ReturnType(p.type_expr, p.name)

    @_('declare_step')
    def declare_list(self, p):
        return StatementList(p.declare_step)
    @_('declare_step declare_list')
    def declare_list(self, p):
        return p.declare_list.push(p.declare_step)
    @_('empty')
    def declare_list(self, p):
        return StatementList()

    @_('declare_stmt ";"')
    def declare_step(self, p):
        return p.declare_stmt

    @_('DEFINE name_list type_expr')
    def declare_stmt(self, p):
        return Define(p.name_list, p.type_expr)
    @_('DEFINE GLOBAL name type_expr DEFAULT expr')
    def declare_stmt(self, p):
        return DefineGlobal(p.name, p.type_expr, p.expr)

    @_('proc_step')
    def proc_list(self, p):
        return StatementList(p.proc_step)
    @_('proc_step proc_list')
    def proc_list(self, p):
        return p.proc_list.push(p.proc_step)
    @_('empty')
    def proc_list(self, p):
        return StatementList()

    @_('proc_stmt ";"')
    def proc_step(self, p):
        return p.proc_stmt
    @_('proc_expr')
    def proc_step(self, p):
        p.proc_expr.EXPR_STMT = True
        return p.proc_expr

    @_('LET let_list "=" expr_list')
    def proc_stmt(self, p):
        return Let(p.let_list, p.expr_list)
    @_('RAISE EXCEPTION integer "," integer "," expr')
    def proc_stmt(self, p):
        return Raise(p.integer0, p.integer1, p.expr)
    @_('RETURN expr_list WITH RESUME')
    def proc_stmt(self, p):
        return Return(p.expr_list, True)
    @_('RETURN expr_list')
    def proc_stmt(self, p):
        return Return(p.expr_list)
    @_('RETURN')
    def proc_stmt(self, p):
        return Return()
    @_('EXECUTE IMMEDIATE expr')
    def proc_stmt(self, p):
        return ExecuteImmediate(p.expr)
    @_('SYSTEM expr')
    def proc_stmt(self, p):
        return System(p.expr)
    @_('EXIT WHILE', 'EXIT FOR', 'EXIT FOREACH')
    def proc_stmt(self, p):
        return Exit(p[1])
    @_('CONTINUE WHILE', 'CONTINUE FOR', 'CONTINUE FOREACH')
    def proc_stmt(self, p):
        return Continue(p[1])
    @_('statement')
    def proc_stmt(self, p):
        return p.statement

    @_('IF if_list if_else END IF')
    def proc_expr(self, p):
        return If(p.if_list, p.if_else)
    @_('FOR name = expr TO expr STEP expr proc_list END FOR')
    def proc_expr(self, p):
        return For(p.name, p.expr0, p.expr1, p.expr2, p.proc_list)
    @_('FOR name = expr TO expr proc_list END FOR')
    def proc_expr(self, p):
        return For(p.name, p.expr0, p.expr1, None, p.proc_list)
    @_('FOREACH name FOR select proc_list END FOREACH')
    def proc_expr(self, p):
        return ForEach(p.name, p.select, p.proc_list)
    @_('FOREACH select proc_list END FOREACH')
    def proc_expr(self, p):
        return ForEach(None, p.select, p.proc_list)
    @_('WHILE expr proc_list END WHILE')
    def proc_expr(self, p):
        return While(p.expr, p.proc_list)
    @_('BEGIN declare_list proc_list END')
    def proc_expr(self, p):
        return BeginEnd(p.declare_list, p.proc_list)
    @_('ON EXCEPTION on_exception_in proc_list END EXCEPTION with_resume')
    def proc_expr(self, p):
        return OnException(p.on_exception_in, p.proc_list, p.with_resume)

    @_('let_expr')
    def let_list(self, p):
        return CommaList(p.let_expr)
    @_('let_expr "," let_list')
    def let_list(self, p):
        return p.let_list.push(p.let_expr)

    @_('name "[" UINT "," UINT "]"')
    def let_expr(self, p):
        return Slice(p.name, p.UINT0, p.UINT1)
    @_('name "[" UINT "]"')
    def let_expr(self, p):
        return Slice(p.name, p.UINT)
    @_('name')
    def let_expr(self, p):
        return p.name

    @_('IN "(" expr_list ")"')
    def on_exception_in(self, p):
        return p.expr_list
    @_('empty')
    def on_exception_in(self, p):
        pass
    
    @_('WITH RESUME')
    def with_resume(self, p):
        return True
    @_('empty')
    def with_resume(self, p):
        pass
    
    @_('expr THEN proc_list')
    def if_list(self, p):
        return NodeList(WhenThen(p.expr, p.proc_list))
    @_('if_list ELIF expr THEN proc_list')
    def if_list(self, p):
        p.if_list.append(WhenThen(p.expr, p.proc_list))
        return p.if_list

    @_('ELSE proc_list')
    def if_else(self, p):
        return p.proc_list
    @_('empty')
    def if_else(self, p):
        pass

    @_('DOCUMENT string_list')
    def document(self, p):
        return p.string_list
    @_('empty')
    def document(self, p):
        return None

    @_('STRING')
    def string_list(self, p):
        return NodeList(p.STRING)
    @_('string_list "," STRING')
    def string_list(self, p):
        return p.string_list.push(p.STRING)

    @_('execute_procedure entity_ref "(" args ")" call_returning')
    def call_stmt(self, p):
        return Call(p.entity_ref, p.args, True, returning=p.call_returning)

    @_('EXECUTE PROCEDURE', 'EXECUTE FUNCTION', 'CALL')
    def execute_procedure(self, p):
        pass

    @_('RETURNING name_list')
    def call_returning(self, p):
        return p.name_list
    @_('empty')
    def call_returning(self, p):
        return None

    @_('expr_list')
    def args(self, p):
        return p.expr_list
    @_('empty')
    def args(self, p):
        return CommaList()

    @_("""
    CREATE TRIGGER entity_name
    UPDATE OF VALUE ON entity_name
    REFERENCING OLD AS name NEW AS name
    FOR EACH ROW
    WHEN expr "(" statement ")"
    """)
    def create_trigger(self, p):
        return CreateTrigger(p.entity_name0, 'UPDATE OF VALUE', p.entity_name1, p.name0, p.name1, p.expr, p.statement)
    @_("""
    CREATE TRIGGER entity_name
    INSERT ON entity_name
    REFERENCING NEW AS name
    FOR EACH ROW
    WHEN expr "(" statement ")"
    """)
    def create_trigger(self, p):
        return CreateTrigger(p.entity_name0, 'INSERT', p.entity_name1, None, p.name, p.expr, p.statement)

    @_('CREATE ROLE STRING')
    def create_role(self, p):
        return CreateRole(p.STRING)

    @_('CREATE VIEW entity_name "(" name_list ")" AS select')
    def create_view(self, p):
        return View(p.entity_name, p.name_list, p.select)

    @_('SET LOCK MODE TO WAIT UINT')
    def set_lock_mode(self, p):
        return SetLockMode(p.UINT)
    @_('SET LOCK MODE TO NOT WAIT')
    def set_lock_mode(self, p):
        return SetLockMode(None)

    @_('ALTER TABLE entity_name ADD CONSTRAINT constraint',
       'ALTER TABLE entity_name ADD CONSTRAINT "(" constraint ")"')
    def alter_table_stmt(self, p):
        return AddConstraint(p.entity_name, p.constraint)
    @_('ALTER TABLE entity_name ADD create_table_column before_column')
    def alter_table_stmt(self, p):
        return AddColumn(p.entity_name, p.create_table_column)

    @_('BEFORE name', 'empty')
    def before_column(self, p):
        return None

    @_('MERGE INTO entity_ref_as USING entity_ref_as ON expr merge_case_list')
    def merge_stmt(self, p):
        return Merge(p.entity_ref_as0, p.entity_ref_as1, p.expr, p.merge_case_list)

    @_('merge_case')
    def merge_case_list(self, p):
        return NodeList(p.merge_case)
    @_('merge_case merge_case_list')
    def merge_case_list(self, p):
        return p.merge_case_list.push(p.merge_case)

    @_('WHEN MATCHED THEN UPDATE SET assignment_list')
    def merge_case(self, p):
        return NodeList('UPDATE_A', p.assignment_list)
    @_('WHEN MATCHED THEN UPDATE SET "(" column_list ")" "=" "(" expr_list ")"')
    def merge_case(self, p):
        return NodeList('UPDATE_B', p.column_list, p.expr_list)
    @_('WHEN NOT MATCHED THEN INSERT "(" column_list ")" VALUES "(" expr_list ")"')
    def merge_case(self, p):
        return NodeList('INSERT', p.column_list, p.expr_list)
    
    @_('UPDATE table_ref SET assignment_list where')
    def update_stmt(self, p):
        return UpdateA(p.table_ref, p.assignment_list, None, p.where)
    @_('UPDATE table_ref SET "(" name_list ")" "=" "(" expr_list ")" where')
    def update_stmt(self, p):
        return UpdateB(p.table_ref, p.name_list, p[8], None, p.where)

    @_('assignment')
    def assignment_list(self, p):
        return NodeList(p.assignment)
    @_('assignment "," assignment_list')
    def assignment_list(self, p):
        return p.assignment_list.push(p.assignment)

    @_('name_or_table_column "=" expr')
    def assignment(self, p):
        return NodeList(p.name_or_table_column, p.expr)

    @_('TRUNCATE entity_ref')
    def truncate_stmt(self, p):
        return Truncate(p.entity_ref)

    @_('UPDATE STATISTICS statistics_mode for_type_name opt_arg_type_list')
    def update_statistics_stmt(self, p):
        return UpdateStatistics(p.statistics_mode, p.for_type_name[0], p.for_type_name[1])
    
    @_('LOW', 'MEDIUM', 'HIGH', 'empty')
    def statistics_mode(self, p):
        return p[0]

    @_('FOR for_type opt_entity_ref')
    def for_type_name(self, p):
        return p.for_type, p.opt_entity_ref
    @_('empty')
    def for_type_name(self, p):
        return None, None

    @_('TABLE', 'PROCEDURE', 'FUNCTION')
    def for_type(self, p):
        return p[0]

    @_('entity_ref')
    def opt_entity_ref(self, p):
        return p[0]
    @_('empty')
    def opt_entity_ref(self, p):
        return None

    @_('GRANT permission grant_on TO grant_role grant_as')
    def grant_stmt(self, p):
        return Grant(p.permission, p.grant_on, p.grant_role, p.grant_as)

    @_('INSERT', 'UPDATE', 'DELETE', 'ALL', 'INDEX', 'CONNECT', 'ALTER',
       'DBA', 'SELECT', 'EXECUTE', 'USAGE', 'STRING', 'REFERENCES')
    def permission(self, p):
        return p[0]

    @_('PUBLIC', 'STRING')
    def grant_role(self, p):
        return p[0]
    
    @_('ON LANGUAGE name')
    def grant_on(self, p):
        return 'LANGUAGE ' + p.name.name;
    @_('ON grant_entity')
    def grant_on(self, p):
        return p.grant_entity
    @_('empty')
    def grant_on(self, p):
        return None

    @_('AS STRING')
    def grant_as(self, p):
        return p.STRING
    @_('empty')
    def grant_as(self, p):
        return None

    @_('REVOKE permission grant_on FROM grant_role grant_as')
    def revoke_stmt(self, p):
        return Revoke(p.permission, p.grant_on, p.grant_role, p.grant_as)

    @_('entity_name')
    def grant_entity(self, p):
        return p.entity_name
    @_('PROCEDURE entity_name "(" arg_type_list ")"',
       'FUNCTION entity_name "(" arg_type_list ")"')
    def grant_entity(self, p):
        return FunctionSignature(p[0], p.entity_name, p.arg_type_list)

    @_('return_type')
    def arg_type_list(self, p):
        return NodeList(p.return_type)
    @_('return_type "," arg_type_list')
    def arg_type_list(self, p):
        return p.arg_type_list.push(p.return_type)
    @_('empty')
    def arg_type_list(self, p):
        return NodeList()

    @_("""
    CREATE AGGREGATE entity_name
    WITH "(" aggregate_arg_list ")"
    """)
    def create_aggregate(self, p):
        return CreateAggregate(p.entity_name, p.aggregate_arg_list)

    @_('aggregate_arg')
    def aggregate_arg_list(self, p):
        return CommaList(p.aggregate_arg)
    @_('aggregate_arg_list "," aggregate_arg')
    def aggregate_arg_list(self, p):
        return p.aggregate_arg_list.append(p.aggregate_arg)

    @_('aggregate_argname "=" entity_name')
    def aggregate_arg(self, p):
        return p.aggregate_argname, p.entity_name

    @_('INIT', 'ITER', 'COMBINE', 'FINAL')
    def aggregate_argname(self, p):
        return p[0]

    @_('DROP kind if_exists entity_name opt_arg_type_list')
    def drop_stmt(self, p):
        return Drop(p[1], p.entity_name, p.if_exists, p.opt_arg_type_list)

    @_('"(" arg_type_list ")"')
    def opt_arg_type_list(self, p):
        return p.arg_type_list
    @_('empty')
    def opt_arg_type_list(self, p):
        return None
    
    @_('TABLE', 'VIEW', 'SYNONYM', 'INDEX', 'PROCEDURE', 'FUNCTION', 'CONSTRAINT', 'SEQUENCE', 'TRIGGER')
    def kind(self, p):
        return p[0]
    
    @_('LOCK TABLE entity_name IN EXCLUSIVE MODE', 'LOCK TABLE entity_name IN SHARE MODE')
    def lock_table(self, p):
        return LockTable(p.entity_name, p[4])

    @_('UNLOCK TABLE entity_name')
    def unlock_table(self, p):
        return UnlockTable(p.entity_name)
    
    @_('CREATE unique INDEX if_not_exists entity_name ON entity_name "(" name_list ")" using_btree')
    def create_index(self, p):
        return CreateIndex(p.entity_name0, p.entity_name1, p.name_list, p.unique, p.if_not_exists)

    @_('UNIQUE', 'empty')
    def unique(self, p):
        return p[0]

    @_('USING BTREE', 'empty')
    def using_btree(self, p):
        pass

    @_('CREATE SYNONYM entity_name FOR entity_ref')
    def create_synonym(self, p):
        return CreateSynonym(p.entity_name, p.entity_ref)

    @_('CREATE SEQUENCE entity_name increment start_with maxvalue minvalue seq_cache seq_order')
    def create_sequence(self, p):
        return CreateSequence(p.entity_name, p.increment, p.start_with, p.minvalue, p.maxvalue, p.seq_cache, p.seq_order)

    @_('ALTER SEQUENCE entity_name RESTART WITH UINT')
    def alter_sequence(self, p):
        return AlterSequence(p.entity_name, p.UINT)
    
    @_('INCREMENT BY UINT', 'INCREMENT UINT')
    def increment(self, p):
        return p.UINT
    @_('empty')
    def increment(self, p):
        return None
    
    @_('START WITH UINT')
    def start_with(self, p):
        return p.UINT
    @_('empty')
    def start_with(self, p):
        return None

    @_('MINVALUE UINT')
    def minvalue(self, p):
        return p.UINT
    @_('empty', 'NOMINVALUE')
    def minvalue(self, p):
        return None
    
    @_('MAXVALUE UINT')
    def maxvalue(self, p):
        return p.UINT
    @_('empty', 'NOMAXVALUE')
    def maxvalue(self, p):
        return None
    
    @_('CACHE UINT')
    def seq_cache(self, p):
        return 'CACHE ' + p.UINT
    @_('empty', 'NOCACHE')
    def seq_cache(self, p):
        return None
    
    @_('ORDER', 'NOORDER')
    def seq_order(self, p):
        return p[0]
    @_('empty')
    def seq_order(self, p):
        return None
    
    @_('primary_key_constraint',
       'foreign_key_constraint',
       'check_constraint',
       'unique_constraint')
    def constraint(self, p):
        return p[0]

    @_('FOREIGN KEY "(" name_list ")" REFERENCES entity_name constraint_entity_name')
    def foreign_key_constraint(self, p):
        return ForeignKeyConstraint(p.constraint_entity_name, p.name_list, p.entity_name)

    @_('PRIMARY KEY "(" name_list ")" constraint_entity_name')
    def primary_key_constraint(self, p):
        return PrimaryKeyConstraint(p.constraint_entity_name, p.name_list)

    @_('CHECK "(" expr ")" constraint_entity_name')
    def check_constraint(self, p):
        return CheckConstraint(p.constraint_entity_name, p.expr)

    @_('UNIQUE "(" name_list ")" constraint_entity_name')
    def unique_constraint(self, p):
        return UniqueConstraint(p.constraint_entity_name, p.name_list)

    @_('CONSTRAINT entity_name')
    def constraint_entity_name(self, p):
        return p.entity_name
    @_('empty')
    def constraint_entity_name(self, p):
        return None

    @_('name_or_table_column')
    def column_list(self, p):
        return CommaList(p.name_or_table_column)
    @_('name_or_table_column "," column_list')
    def column_list(self, p):
        return p.column_list.push(p.name_or_table_column)

    @_('name', 'table_column')
    def name_or_table_column(self, p):
        return p[0]

    @_('name')
    def name_list(self, p):
        return CommaList(p.name)
    @_('name "," name_list')
    def name_list(self, p):
        return p.name_list.push(p.name)

    @_('CREATE temp TABLE if_not_exists entity_name "(" create_table_item_list ")"')
    def create_table(self, p):
        return CreateTable(p.entity_name, p.create_table_item_list, p.temp, p.if_not_exists)

    @_('TEMP', 'empty')
    def temp(self, p):
        return p[0]

    @_('IF EXISTS', 'empty')
    def if_exists(self, p):
        return p[0]

    @_('IF NOT EXISTS', 'empty')
    def if_not_exists(self, p):
        return p[0]

    @_('create_table_item')
    def create_table_item_list(self, p):
        return CommaList(p.create_table_item)
    @_('create_table_item "," create_table_item_list')
    def create_table_item_list(self, p):
        return p.create_table_item_list.push(p.create_table_item)

    @_('create_table_column')
    def create_table_item(self, p):
        return p.create_table_column
    @_('check_constraint')
    def create_table_item(self, p):
        return p.check_constraint
    @_('primary_key_constraint')
    def create_table_item(self, p):
        return p.primary_key_constraint
    @_('unique_constraint')
    def create_table_item(self, p):
        return p.unique_constraint

    @_('name type_expr column_default_constraints in_dbspace disabled')
    def create_table_column(self, p):
        default, column_constraints = p.column_default_constraints
        not_null, primary_key = column_constraints
        return CreateTableColumn(p.name, p.type_expr, default, not_null, primary_key)

    @_('default column_constraints',
       'column_constraints default')
    def column_default_constraints(self, p):
        return p.default, p.column_constraints

    @_('not_null primary_key',
       'primary_key not_null')
    def column_constraints(self, p):
        return p.not_null, p.primary_key

    @_('DISABLED', 'empty')
    def disabled(self, p):
        return None

    @_('DEFAULT literal')
    def default(self, p):
        return p.literal
    @_('empty')
    def default(self, p):
        return None

    @_('NOT NULL')
    def not_null(self, p):
        return True
    @_('empty')
    def not_null(self, p):
        return False

    @_('PRIMARY KEY')
    def primary_key(self, p):
        return True
    @_('empty')
    def primary_key(self, p):
        return False

    @_('IN name')
    def in_dbspace(self, p):
        return None
    @_('empty')
    def in_dbspace(self, p):
        return None

    @_('SELECT skip first distinct select_column_list into_vars FROM from_expr where group_by having union_list order_by into')
    def select(self, p):
        return Select(p.skip, p.first, p.distinct, p.select_column_list, p.into_vars, p.from_expr, p.where, p.group_by, p.having, p.union_list, p.order_by, p.into)

    @_('union_select')
    def union_list(self, p):
        return NodeList(p.union_select)
    @_('union_list union_select')
    def union_list(self, p):
        return p.union_list.append(p.union_select)
    @_('empty')
    def union_list(self, p):
        return None

    @_('union simple_select')
    def union_select(self, p):
        return Union(p.union, p.simple_select)

    @_('SELECT skip first distinct select_column_list into_vars FROM from_expr where group_by having')
    def simple_select(self, p):
        return Select(p.skip, p.first, p.distinct, p.select_column_list, p.into_vars, p.from_expr, p.where, p.group_by, p.having)

    @_('UNION')
    def union(self, p):
        return 'UNION'
    @_('UNION ALL')
    def union(self, p):
        return 'UNION ALL'

    @_('INTO name_list')
    def into_vars(self, p):
        return p.name_list
    @_('empty')
    def into_vars(self, p):
        return None
    
    @_('INTO TEMP NAME')
    def into(self, p):
        return p.NAME
    @_('empty')
    def into(self, p):
        return None

    @_('"(" from_expr ")"')
    def from_expr(self, p):
        return Group(p.from_expr)
    @_('from_expr "," from_expr')
    def from_expr(self, p):
        return Cons(p.from_expr0, p.from_expr1)
    @_('from_expr join from_expr on_expr')
    def from_expr(self, p):
        return Join(p.join, p.from_expr0, p.from_expr1, p.on_expr)
    @_('OUTER "(" from_expr ")"')
    def from_expr(self, p):
        return Outer(p.from_expr)
    @_('table_expr')
    def from_expr(self, p):
        return p.table_expr
    @_('entity_ref_as')
    def from_expr(self, p):
        return p.entity_ref_as
    @_('sub_select as_name insert_stmt_name_list')
    def from_expr(self, p):
        return SubSelectAsSelectTable(p.sub_select, p.as_name, p.insert_stmt_name_list)

    @_('INNER JOIN',
       'LEFT outer JOIN',
       'RIGHT outer JOIN',
       'FULL outer JOIN',
       'CROSS JOIN')
    def join(self, p):
        return p[0]
    @_('JOIN')
    def join(self, p):
        return 'INNER'

    @_('OUTER', 'empty')
    def outer(self, p):
        pass

    @_('ON expr')
    def on_expr(self, p):
        return p.expr
    @_('empty')
    def on_expr(self, p):
        return None

    @_('entity_ref AS name', 'entity_ref name')
    def entity_ref_as(self, p):
        return As(p.entity_ref, p.name)
    @_('entity_ref')
    def entity_ref_as(self, p):
        return p.entity_ref

    @_('name "@" name ":" entity_name')
    def entity_ref(self, p):
        return EntityRef(p.entity_name, p.name0, p.name1)
    @_('name ":" entity_name')
    def entity_ref(self, p):
        return EntityRef(p.entity_name, p.name)
    @_('entity_name')
    def entity_ref(self, p):
        return EntityRef(p.entity_name)

    @_('STRING "." name')
    def entity_name(self, p):
        return OwnerDotName(p.STRING, p.name)
    @_('name')
    def entity_name(self, p):
        return p.name

    @_('AS name')
    def as_name(self, p):
        return p.name
    @_('name')
    def as_name(self, p):
        return p.name
    @_('empty')
    def as_name(self, p):
        return None
    
    @_('DELETE FROM table_ref where',
       'DELETE table_ref where')
    def delete_stmt(self, p):
        return Delete(p.table_ref, p.where)

    @_('INSERT INTO table_ref insert_stmt_name_list VALUES "(" expr_list ")"')
    def insert_stmt(self, p):
        return Insert(p.table_ref, p.insert_stmt_name_list, p.expr_list, None)
    @_('INSERT INTO table_ref insert_stmt_name_list select')
    def insert_stmt(self, p):
        return Insert(p.table_ref, p.insert_stmt_name_list, None, p.select)
    @_('INSERT INTO table_ref insert_stmt_name_list call_stmt')
    def insert_stmt(self, p):
        return Insert(p.table_ref, p.insert_stmt_name_list, None, p.call_stmt)

    @_('entity_ref_as')
    def table_ref(self, p):
        return p.entity_ref_as
    @_('table_expr')
    def table_ref(self, p):
        return p.table_expr
    
    @_('TABLE "(" FUNCTION expr ")" as_name insert_stmt_name_list',
       'TABLE "(" expr ")" as_name insert_stmt_name_list')
    def table_expr(self, p):
        return Table(p.expr, p.as_name, p.insert_stmt_name_list)

    @_('"(" name_list ")"')
    def insert_stmt_name_list(self, p):
        return p.name_list
    @_('empty')
    def insert_stmt_name_list(self, p):
        return None

    @_('SKIP UINT')
    def skip(self, p):
        return p.UINT
    @_('empty')
    def skip(self, p):
        return None

    @_('FIRST UINT')
    def first(self, p):
        return p.UINT
    @_('empty')
    def first(self, p):
        return None

    @_('UNIQUE')
    def distinct(self, p):
        return True
    @_('DISTINCT')
    def distinct(self, p):
        return True
    @_('empty')
    def distinct(self, p):
        return False

    @_('WHERE expr')
    def where(self, p):
        return p.expr
    @_('empty')
    def where(self, p):
        return None

    @_('GROUP BY expr_list')
    def group_by(self, p):
        return p.expr_list
    @_('empty')
    def group_by(self, p):
        return None

    @_('HAVING expr')
    def having(self, p):
        return p.expr
    @_('empty')
    def having(self, p):
        return None

    @_('ORDER BY order_list')
    def order_by(self, p):
        return p.order_list
    @_('empty')
    def order_by(self, p):
        return None

    @_('order_item')
    def order_list(self, p):
        return CommaList(p.order_item)
    @_('order_list "," order_item')
    def order_list(self, p):
        return p.order_list.append(p.order_item)
    
    @_('expr ASC', 'expr DESC')
    def order_item(self, p):
        return OrderByItem(p.expr, p[1])
    @_('expr')
    def order_item(self, p):
        return OrderByItem(p.expr, None)
    
    @_('select_column')
    def select_column_list(self, p):
        return CommaList(p.select_column)
    @_('select_column "," select_column_list')
    def select_column_list(self, p):
        return p.select_column_list.push(p.select_column)
    
    @_('expr AS name')
    def select_column(self, p):
        return SelectColumn(p.expr, p.name)
    @_('expr name')
    def select_column(self, p):
        return SelectColumn(p.expr, p.name)
    @_('expr')
    def select_column(self, p):
        return SelectColumn(p.expr)
        
    @_('expr')
    def expr_list(self, p):
        return CommaList(p.expr)
    @_('expr "," expr_list')
    def expr_list(self, p):
        return p.expr_list.push(p.expr)
    
    @_('NVL "(" args ")"')
    def expr(self, p):
        return Nvl(p.args)
    @_('entity_ref "(" args ")"')
    def expr(self, p):
        return Call(p.entity_ref, p.args)
    @_('expr BETWEEN and_expr')
    def expr(self, p):
        return Between(p.expr, p.and_expr.left, p.and_expr.right)
    @_('expr NOT BETWEEN and_expr')
    def expr(self, p):
        return NotBetween(p.expr, p.and_expr.left, p.and_expr.right)
    @_('and_expr')
    def expr(self, p):
        return p.and_expr
    @_('expr "<" expr', 'expr ">" expr',
       'expr LE expr', 'expr GE expr',
       'expr "=" expr', 'expr EQ expr',
       'expr OR expr',
       'expr LIKE expr',
       'expr NE1 expr', 'expr NE2 expr',
       'expr "+" expr', 'expr "-" expr',
       'expr "*" expr', 'expr "/" expr',
       'expr CONCAT expr')
    def expr(self, p):
        return Operator(p[1], p.expr0, p.expr1)
    @_('expr NOT LIKE expr')
    def expr(self, p):
        return Operator('NOT '+p[2], p.expr0, p.expr1)
    @_('expr MATCHES expr')
    def expr(self, p):
        return Matches(p.expr0, p.expr1, False)
    @_('expr NOT MATCHES expr')
    def expr(self, p):
        return Matches(p.expr0, p.expr1, True)
    @_('"-" expr %prec UMINUS')
    def expr(self, p):
        return Minus(p.expr)
    @_('NOT expr')
    def expr(self, p):
        return Not(p.expr)
    @_('expr "[" UINT "]"')
    def expr(self, p):
        return Slice(p.expr, p.UINT)
    @_('expr "[" UINT "," UINT "]"')
    def expr(self, p):
        return Slice(p.expr, p.UINT0, p.UINT1)
    @_('expr CAST type_expr')
    def expr(self, p):
        return Cast(p.expr, p.type_expr)
    @_('EXISTS "(" select ")"',
       'EXISTS "(" "(" select ")" ")"')
    def expr(self, p):
        return Exists(p.select)
    @_('expr IN "(" expr_list ")"',
       'expr IN "(" select ")"')
    def expr(self, p):
        return In(p.expr, p[3])
    @_('expr IN expr')
    def expr(self, p):
        return In(p.expr0, p.expr1)
    @_('expr NOT IN "(" expr_list ")"',
       'expr NOT IN "(" select ")"')
    def expr(self, p):
        return NotIn(p.expr, p[4])
    @_('expr NOT IN expr')
    def expr(self, p):
        return NotIn(p.expr0, p.expr1)
    @_('expr IS NULL')
    def expr(self, p):
        return IsNull(p.expr)
    @_('expr IS NOT NULL')
    def expr(self, p):
        return IsNotNull(p.expr)
    @_('TRIM "(" trim_from expr ")"')
    def expr(self, p):
        return Trim(p.trim_from[0], p.trim_from[1], p.expr)
    @_('SUBSTRING "(" expr FROM expr for_expr ")"')
    def expr(self, p):
        return Substring(p.expr0, p.expr1, p.for_expr)
    @_('COUNT "(" distinct expr ")"')
    def expr(self, p):
        return Count(p.distinct, p.expr)
    @_('MULTISET "(" select ")"')
    def expr(self, p):
        return MultiSetValue(p.select)
    @_('literal')
    def expr(self, p):
        return p.literal
    @_('table_column')
    def expr(self, p):
        return p.table_column
    @_('name')
    def expr(self, p):
        return p[0]
    @_('sub_select')
    def expr(self, p):
        return p.sub_select
    @_('"(" expr ")"')
    def expr(self, p):
        return Group(p.expr)
    @_('CASE case_expr END')
    def expr(self, p):
        return p.case_expr
    @_('CURRENT OF name')
    def expr(self, p):
        return CurrentOf(p.name)
    @_('LIST "{" args "}"')
    def expr(self, p):
        return ListExpr(p.args)

    @_('FOR expr')
    def for_expr(self, p):
        return p.expr
    @_('empty')
    def for_expr(self, p):
        return None

    @_('trim_type pad_char FROM')
    def trim_from(self, p):
        return p[0], p[1]
    @_('empty')
    def trim_from(self, p):
        return None, None

    @_('BOTH', 'LEADING', 'TRAILING')
    def trim_type(self, p):
        return p[0]

    @_('expr')
    def pad_char(self, p):
        return p[0]
    @_('empty')
    def pad_char(self, p):
        return None

    @_('expr AND expr')
    def and_expr(self, p):
        return Operator(p[1], p.expr0, p.expr1)
    
    @_('entity_ref "." name')
    def table_column(self, p):
        return TableColumn(p.entity_ref, p.name)

    @_('"(" select ")"')
    def sub_select(self, p):
        p.select.__class__ = SubSelect
        return p.select

    @_('case_when_list case_else')
    def case_expr(self, p):
        return Case(p.case_when_list, p.case_else)

    @_('case_when')
    def case_when_list(self, p):
        return NodeList(p.case_when)
    @_('case_when case_when_list')
    def case_when_list(self, p):
        return p.case_when_list.push(p.case_when)

    @_('WHEN expr THEN expr')
    def case_when(self, p):
        return WhenThen(p.expr0, p.expr1)

    @_('ELSE expr')
    def case_else(self, p):
        return p.expr
    @_('empty')
    def case_else(self, p):
        return None

    @_('NULL')
    def literal(self, p):
        return p.NULL
    @_('STRING')
    def literal(self, p):
        return String(p.STRING)
    @_('decimal')
    def literal(self, p):
        return p.decimal
    @_('integer')
    def literal(self, p):
        return p.integer
    @_('integer UNITS time_unit')
    def literal(self, p):
        return Units(p.integer, p.time_unit)
    @_('TODAY')
    def literal(self, p):
        return Today()
    @_('CURRENT')
    def literal(self, p):
        return Current()
    @_('CURRENT time_unit TO time_unit')
    def literal(self, p):
        return Current(p.time_unit0, p.time_unit1)
    @_('INTERVAL "(" interval_values ")" time_unit TO time_unit')
    def literal(self, p):
        return Interval(p.interval_values, p.time_unit0, p.time_unit1)

    @_('UINT ivsep UINT ivsep UINT ivsep UINT ivsep UINT')
    def interval_values(self, p):
        return ''.join((p.UINT0, p.ivsep0, p.UINT1, p.ivsep1, p.UINT2, p.ivsep2, p.UINT3, p.ivsep3, p.UINT4))
    @_('UINT ivsep UINT ivsep UINT ivsep UINT')
    def interval_values(self, p):
        return ''.join((p.UINT0, p.ivsep0, p.UINT1, p.ivsep1, p.UINT2, p.ivsep2, p.UINT3))
    @_('UINT ivsep UINT ivsep UINT')
    def interval_values(self, p):
        return ''.join((p.UINT0, p.ivsep0, p.UINT1, p.ivsep1, p.UINT2))
    @_('UINT ivsep UINT')
    def interval_values(self, p):
        return ''.join((p.UINT0, p.ivsep, p.UINT1))
    @_('UINT')
    def interval_values(self, p):
        return p.UINT

    @_('"-"', '":"', '"."')
    def ivsep(self, p):
        return p[0]
    @_('empty')
    def ivsep(self, p):
        return ' '

    @_('ROW "(" row_list ")"')
    def type_expr(self, p):
        return RowType(p.row_list)
    @_('MULTISET "(" simple_type_expr ")"')
    def type_expr(self, p):
        return MultiSetType(p.simple_type_expr)
    @_('MULTISET "(" simple_type_expr NOT NULL ")"')
    def type_expr(self, p):
        return MultiSetType(p.simple_type_expr, True)
    @_('SET "(" simple_type_expr ")"')
    def type_expr(self, p):
        return SetType(p.simple_type_expr)
    @_('SET "(" simple_type_expr NOT NULL ")"')
    def type_expr(self, p):
        return SetType(p.simple_type_expr, True)
    @_('LIST "(" simple_type_expr ")"')
    def type_expr(self, p):
        return ListType(p.simple_type_expr)
    @_('LIST "(" simple_type_expr NOT NULL ")"')
    def type_expr(self, p):
        return ListType(p.simple_type_expr, True)
    @_('simple_type_expr')
    def type_expr(self, p):
        return p.simple_type_expr


    @_('row_type')
    def row_list(self, p):
        return CommaList(p.row_type)
    @_('row_list "," row_type')
    def row_list(self, p):
        return p.row_list.append(p.row_type)

    @_('simple_type_expr')
    def row_type(self, p):
        return p.simple_type_expr
    @_('create_table_column')
    def row_type(self, p):
        return p.create_table_column

    @_('DATETIME time_unit TO time_unit', 'INTERVAL time_unit TO time_unit')
    def simple_type_expr(self, p):
        return DatetimeType(p[0], p.time_unit0, p.time_unit1)
    @_('owner datatype')
    def simple_type_expr(self, p):
        return Type(OwnerDotName(p.owner, p.datatype))
    @_('datatype')
    def simple_type_expr(self, p):
        return Type(p.datatype)
    @_('datatype "(" UINT ")"')
    def simple_type_expr(self, p):
        return Type(p.datatype, p.UINT)
    @_('datatype "(" UINT "," UINT ")"')
    def simple_type_expr(self, p):
        return Type(p.datatype, p.UINT0, p.UINT1)

    @_('CHAR', 'DECIMAL', 'DATE', 'INT', 'INT8', 'BYTE', 'BOOLEAN', 'BLOB',
       'SMALLINT', 'INTEGER', 'LVARCHAR', 'SERIAL', 'VARCHAR', 'TEXT',
       'INTERVAL', 'DATETIME')
    def datatype(self, p):
        return p[0]

    @_('STRING "."')
    def owner(self, p):
        return p.STRING

    @_('sign UINT')
    def integer(self, p):
        return p.sign + p.UINT

    @_('sign UINT "." UINT')
    def decimal(self, p):
        return p.sign + p.UINT0 + '.' + p.UINT1

    @_('"+"', '"-"')
    def sign(self, p):
        return p[0]
    @_('empty')
    def sign(self, p):
        return ''

    @_('time_unit_name')
    def time_unit(self, p):
        return TimeUnit(p.time_unit_name)
    @_('time_unit_name "(" UINT ")"')
    def time_unit(self, p):
        return TimeUnit(p.time_unit_name, p.UINT)
    
    @_('YEAR', 'MONTH', 'DAY', 'HOUR', 'MINUTE', 'SECOND', 'FRACTION')
    def time_unit_name(self, p):
        return p[0]

    @_('NAME', 'ALL', 'KEY', 'UPDATE', 'time_unit_name', 'MATCHED', 'END', 'DEFAULT',
       'LANGUAGE', 'ROLE', 'VARIANT', 'INCREMENT', 'CONSTRAINT', 'USAGE', 'FUNCTION', #'GROUP',
       'COUNT', 'ENABLED', 'FIRST', 'DOCUMENT', 'SYSTEM', 'INIT', 'ITER', 'COMBINE', 'FINAL',
       'VALUE', 'datatype', 'TRIM', 'BEGIN', 'GLOBAL', 'STEP', 'SHARE', '*', 'NEW', 'OLD')
    def name(self, p):
        return Name(p[0])

    @_('')
    def empty(self, p):
        pass

    def parse(self, tokens, onerror=None, maxerrors=1000000):
        self.maxerrors = maxerrors
        self.errcount = 0
        self.onerror = onerror
        return super().parse(tokens)

    def error(self, t):
        txt = self.input_text
        stderr.write("Syntax Error [state {}] {}\n".format(self.state, t))
        if t != None:
            line_start = txt.rfind('\n', 0, t.index) + 1
            line_end = txt.find('\n', t.index)
            stderr.write(colored(txt[line_start:t.index], 'yellow'))
            stderr.write(colored(txt[t.index:t.index+len(t.value)], 'red'))
            stderr.write(colored(txt[t.index+len(t.value):line_end]+'\n', 'yellow'))
        if self.onerror:
            self.onerror(self, t)
        self.errcount += 1
        if self.errcount >= self.maxerrors:
            raise TooManyErrors()
