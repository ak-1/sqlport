
import sys
import re
from .. node import *
from .. util import join_list, pretty_print
from . informix import InformixWriter
from functools import reduce

invalid_names = set("""
ALL END DEFAULT
""".split())

def map_matches(txt):
    r = ""
    quote = False
    charset = False
    for c in txt:
        if quote:
            quote = False
        elif c == "]":
            charset = False
        elif charset:
            pass
        elif c == "[":
            charset = True
        elif c == "\\":
            quote = True
        elif c == "?":
            c = "_"
        elif c == "*":
            c = "%"
        r += c
    return r

#class NotSupported(Exception): pass

exprStatements = (OnException, SetLockMode)

def ensure_name_prefix(prefix, obj):
    if isinstance(obj.name, OwnerDotName):
        obj = obj.name
    if isinstance(obj.name, Name):
        obj = obj.name
    if not obj.name.startswith(prefix):
        obj.name = "pk_" + obj.name

def fix_declarations(proc):
    fixed = StatementList()
    for dec in proc.declarations:
        if not isinstance(dec, DefineGlobal) and len(dec.names) > 1:
            for name in dec.names:
                fixed.append(Define((name,), dec.type))
        else:
            fixed.append(dec)
    proc.declarations = fixed

def fix_foreach(proc):
    """
    - find foreach loops
    - self.record = "__rec__", "__rec2__", ...
    - self.variables = ["x", "y"]
    - "SELECT a, b INTO x, y" -> "SELECT a as x, b as y"
    """
    loops = find_nodes(proc, lambda obj: isinstance(obj, ForEach), True)
    for i, loop in enumerate(loops):
        loop.record = "__rec{}__".format(i+1)
        proc.declarations.append(Define((loop.record,), "RECORD"))
        if loop.select.into_vars:
            loop.variables = [ x.writeout() for x in loop.select.into_vars ]
            loop.select.into_vars = None
            for i, column in enumerate(list(loop.select.columns)):
                column.name = loop.variables[i]
        else:
            loop.variables = []
    
def fix_outer(select):
    if not len(list(find_nodes(select.table,
                               lambda obj: isinstance(obj, Outer),
                               lambda obj, key, value: not isinstance(obj, Outer) and key != "on"))):
        return
    tables_done = set()
    while True:
        select.set_parents()
        tables = list(find_nodes(select.table,
                                 lambda obj: isinstance(obj, (As, EntityRef, Outer)),
                                 lambda obj, key, value: not isinstance(obj, (As, Outer)) and key != "on"))
        for table in tables[1:]:
            if table.id in tables_done:
                continue
            tables_done.add(table.id)
            if isinstance(table, Outer):
                outer = table
                cur_table = outer.expr
            else:
                outer = None
                cur_table = table
            break
        else:
            return
        table_ids = [ x.id for x in tables ]
        cur_index = table_ids.index(cur_table.id)
        expressions = []
        for expr in find_nodes(select.where, lambda x: isinstance(x, Operator), True):
            if expr.op in ('=','<','<>','>','<=','>=','!='):
                cur_table_found = False
                for table in find_nodes(expr, lambda x: isinstance(x, EntityRef), True):
                    if isinstance(table.parent, Call) and table.parent_key == "name":
                        continue
                    if table.id == cur_table.id:
                        cur_table_found = True
                    try:
                        if table_ids.index(table.id) > cur_index:
                            break
                    except ValueError:
                        # FIXME:
                        # we found a table that is not in the from clause
                        # so probably a table from a subselect
                        # should we break here?
                        # break means "do not move this expr into the join clause"
                        pass
                else:
                    if cur_table_found:
                        expressions.append(expr)
            elif expr.op != "AND":
                yield BlockComment(NotSupported("In fix_outer: Operation ", expr.op))
                return

        for expr in expressions:
            expr.detach(True)
        if len(expressions):
            join_expr = reduce(lambda left, right: Operator("AND", left, right), expressions)
        else:
            join_expr = None
        if not len(expressions):
            join_type = "CROSS"
        elif outer:
            join_type = "LEFT"
        else:
            join_type = "INNER"
        if outer:
            outer.detach(True)            
        cur_table.detach(True)
        left_table = tables[cur_index-1]
        while isinstance(left_table.parent, Join):
            left_table = left_table.parent
        join = Join(join_type, left_table, cur_table, join_expr)
        left_table.replace(join)
    
def handle_none_values(op, a, b):
    if a is None:
        if b is None:
            return None
        else:
            return b
    elif b is None:
        return a
    else:   
        return a, op, b

def convert_string(text):
    if text[0] == '"':
        return "'" + (text[1:-1].replace('""','"').replace("'","''")) + "'"
    return text

def move_exception_handlers(procedure):
    procedure.set_parents()
    move_list = []
    for obj, parents, path in list(nodewalk(procedure)):
        if isinstance(obj, OnException):
            move_list.append(obj)
    for obj in move_list:
        parent = obj.parent
        obj.detach()
        parent.append(obj)

errorMap = {
    "-206": "undefined_table",
    "-958": "duplicate_table",
    "-239": "unique_violation",
}

class PostgresWriter(InformixWriter):
    def Select(self):
        yield from fix_outer(self)
        br = Br(self)
        if self.into:
            yield 'CREATE TEMP TABLE ', self.into, ' AS', br
        yield "SELECT"
        if self.distinct:
            yield " DISTINCT "
        yield br, Indented(self.columns)
        if self.into_vars:
            yield br, 'INTO ', self.into_vars
            #yield NotSupported("INTO vars")
        yield br, "FROM ", self.table
        if self.where:
            yield br, 'WHERE ', self.where
        if self.group_by:
            yield br, 'GROUP BY ', self.group_by
        if self.having:
            yield br, 'HAVING ', self.having
        if self.order_by:
            yield br, 'ORDER BY ', self.order_by
        if self.first:
            yield br, 'LIMIT ', self.first
        if self.skip:
            yield br, 'OFFSET ', self.skip
        if self.unions:
            for union in self.unions:
                yield br, union

    def AddConstraint(self):
        yield 'ALTER TABLE ', self.table
        yield ' ADD ', self.constraint

    def CheckConstraint(self):
        if self.name:
            yield 'CONSTRAINT ', self.name, ' '
        yield 'CHECK (', self.expr, ')'

    def PrimaryKeyConstraint(self):
        if self.name:
            ensure_name_prefix("pk_", self)
            yield 'CONSTRAINT ', self.name, ' '
        yield 'PRIMARY KEY (', Indented(self.columns), ')'

    def ForeignKeyConstraint(self):
        if self.name:
            yield 'CONSTRAINT ', self.name, ' '
        yield 'FOREIGN KEY (', Indented(self.columns), ')',
        yield ' REFERENCES ', self.references

    def UniqueConstraint(self):
        if self.name:
            yield 'CONSTRAINT ', self.name, ' '
        yield 'UNIQUE (', self.columns, ')'

    def OwnerDotName(self):
        #yield self.owner, '.', self.name
        yield self.name

    def Grant(self):
        yield 'GRANT ', self.permission
        if self.on:
            yield ' ON ', self.on
        yield ' TO ', self.to
        if self._as:
            yield BlockComment(NotSupported(' AS ', self._as))

    def Revoke(self):
        yield 'REVOKE ', self.permission
        if self.on:
            yield ' ON ', self.on
        yield ' FROM ', self._from
        if self._as:
            yield BlockComment(NotSupported(' AS ', self._as))

    def Current(self):
        yield 'current_timestamp'

    def Today(self):
        yield 'current_date'

    def CreateTableColumn(self):
        yield self.name, ' ', self.ctype
        if self.default:
            yield " DEFAULT ", self.default
        if self.not_null:
            yield " NOT NULL"
        if self.primary_key:
            yield " PRIMARY KEY"

    def TableColumn(self):
        return self.table, '.', self.column

    def Name(self):
        if self.name in invalid_names:
            return self.name.lower() + '_'
        else:
            return self.name.lower()

    def DatetimeType(self):
        if self.type == "DATETIME":
            yield 'timestamp'
        elif self.type == "INTERVAL":
            yield 'interval'
        else:
            yield self.type

    def Nvl(self):
        yield 'coalesce(', self.args, ')'

    def Type(self):
        if self.name == "BYTE":
            yield "bytea"
        elif self.name == "LVARCHAR":
            yield "VARCHAR"
        else:
            yield self.name
        if self.name in ("CHAR", "VARCHAR"):
            self.size2 = None
        if self.name == "DECIMAL" and self.size2 is None:
            #self.size2 = str(min(int(int(self.size) / 3), 10))
            self.size = "30"
            self.size2 = "10"
        if self.size:
            yield '(', self.size
            if self.size2:
                yield ',', self.size2
            yield ')'

    def Matches(self):
        yield self.text
        if self.neg:
            yield ' NOT'
        if isinstance(self.pattern, (str, String)):
            yield ' SIMILAR TO ', map_matches(self.pattern.writeout())
        else:
            yield ' SIMILAR TO map_matches(', self.pattern, ')'

    def Slice(self):
        if hasattr(self, "parent") and isinstance(self.parent, CommaList) and isinstance(self.parent.parent, Let) and self.parent.parent_key == "names": 
            yield self.value, '[', self.left
            if self.right:
                yield ',', self.right
            yield ']'
            yield ' ', BlockComment(NotSupported("Slice assignment"))
        else:
            try:
                left = int(self.left)
                if self.right is None:
                    right = left
                else:
                    right = int(self.right)
            except TypeError:
                yield NotSupported("Cannot calulate Slice", self.left, self.right)
            else:
                yield 'substring(', self.value, ' from ', str(left), ' for ', str(right - left + 1), ')'

    def Outer(self):
        #yield 'OUTER(', self.expr, ')'
        yield NotSupported("OUTER")

    def Cons(self):
        yield handle_none_values(', ', self.a, self.b)

    def Operator(self):
        yield handle_none_values((' ', self.op, ' '), self.left, self.right)

    def View(self):
        return 'CREATE OR REPLACE VIEW ', self.name, ' (\n', Indented(self.columns), '\n) AS\n', self.select

    def Drop(self):
        yield 'DROP '
        if self.kind == 'PROCEDURE':
            yield 'FUNCTION'
        else:
            yield self.kind
        if self.if_exists:
            yield ' IF EXISTS'
        yield ' ', self.name
        if self.arg_types:
            yield "(", self.arg_types, ")"

    def CreateProcedure(self):
        fix_declarations(self)
        fix_foreach(self)
        move_exception_handlers(self)
        self.set_parents()
        # if self.returning:
        #     proc_type = 'FUNCTION'
        # else:
        #     proc_type = 'PROCEDURE'
        proc_type = 'FUNCTION'
        #yield 'DROP ', proc_type, ' IF EXISTS ', self.name, ';\n'
        yield 'CREATE OR REPLACE ', proc_type, ' ', self.name,
        yield '(', join_list(', ', self.parameters), ')'
        if self.returning:
            yield ' RETURNS ', join_list(', ', self.returning)
            if len(self.returning) > 1:
                yield NotSupported("RETURNS with multiple values")
        else:
            yield ' RETURNS VOID'
        if self.variant == True:
            yield ' VOLATILE'
        if self.variant == False:
            yield ' IMMUTABLE'
        yield " AS $$\n"
        if self.declarations:
            yield "DECLARE\n", Indented(self.declarations)
        yield "BEGIN\n", Indented(self.statements), 'END;\n'
        yield "$$ LANGUAGE plpgsql"
        # if self.doc:
        #     yield ' DOCUMENT ', self.doc
                   
    def Define(self):
        yield self.names[0], ' ', self.type

    def If(self):
        yield 'IF ', self.cases[0].when, ' THEN\n', Indented(self.cases[0].then)
        for case in self.cases[1:]:
            yield 'ELSIF ', case.when, ' THEN\n', Indented(case.then)
        if self.default != None:
            yield 'ELSE\n', Indented(self.default)
        yield 'END IF'

    def StatementList(self):
        for s in self:
            if s is None:
                continue
            #            s = s.write()
            #            if s != None:
            yield s
            #if not hasattr(s, "EXPR_STMT"):
            if not isinstance(s, exprStatements):
                yield ';'
            yield '\n\n'

    def While(self):
        yield 'WHILE ', self.expr, ' LOOP\n', Indented(self.statements), 'END LOOP\n'

    def Exit(self):
        #yield "EXIT ", self.loop
        yield "EXIT"

    def For(self):
        yield 'FOR ', self.var, ' IN ', self.a, '..', self.b
        if self.step:
            yield ' BY ', self.step
        yield ' LOOP\n', Indented(self.statements), 'END LOOP'

    def Let(self):
        if len(self.names) > 1:
            yield Comment(NotSupported('LET with multiple values:'))
            yield self.names, ' := ', self.values
        else:
            yield self.names[0], ' := ', self.values[0]

    def Call(self):
        br = Br(self)
        if self.statement:
            yield 'SELECT '
        yield self.name, '(', br, self.args, br, ')'
        if self.returning:
            yield ' ', NotSupported('RETURNING ', self.returning)

    def OnException(self):
        yield "EXCEPTION\n", Indent
        if self.codes:
            codes = [ errorMap.get(code, NotSupported(code)) for code in self.codes ]
        else:
            yield NotSupported("EXCEPTION WITHOUT ANY ERROR CODES")
            codes = []
        yield "WHEN ", join_list(" OR ", codes), " THEN\n"
        yield self.statements
        if self.resume:
            yield NotSupported("WITH RESUME")
        yield Dedent

    def Noop(self):
        yield 'NULL'

    def UpdateStatistics(self):
        if self.type == 'TABLE':
            yield "ANALYZE"
            # if self.mode:
            #     yield " ", self.mode
            if self.name:
                yield " ", self.name

    def String(self):
        yield convert_string(self.value)

    def Raise(self):
        # yield "RAISE EXCEPTION ",  self.sql_error,
        # yield ", ", self.isam_error, ', ', self.expr
        assert self.sql_error == "-746"
        assert self.isam_error == "0"
        yield "RAISE EXCEPTION 'Error: %', ", self.expr

    def MultiSetType(self):
        # yield 'MULTISET(', self.type,
        # if self.not_null:
        #     yield ' NOT NULL'
        # yield ')'
        yield NotSupported("MULTISET")

    def Interval(self):
        values = [ int(x) for x in re.split(r"\D+", self.value) ]
        units = ('YEAR', 'MONTH', 'DAY', 'HOUR', 'MINUTE', 'SECOND', 'FRACTION')
        parts = []
        i = 0
        ixa = units.index(self.a.writeout())
        while i < len(values) and ixa < len(units):
            value = values[i]
            unit = units[ixa].lower()
            if unit == 'fraction':
                parts.append(NotSupported().writeout())
            if value not in (1,-1):
                unit += 's'
            parts.append('{} {}'.format(value, unit))
            i += 1
            ixa += 1
        yield "INTERVAL '{}'".format(' '.join(parts))

    def SetLockMode(self):
        # yield "SET LOCK MODE TO "
        # if self.seconds:
        #     yield "WAIT ", self.seconds
        # else:
        #     yield "NOT WAIT"
        yield Comment(NotSupported("SET LOCK MODE"))

    def Merge(self):
        br = Br(self)
        ins_column_list = None
        ins_expr_list = None
        upd_set_list = None
        upd_column_list = None
        upd_expr_list = None
        for case in self.case_list:
            if case[0] == "UPDATE_A":
                upd_set_list = case[1]
            elif case[0] == "UPDATE_B":
                upd_column_list, upd_expr_list = case[1], case[2]
            elif case[0] == "INSERT":
                ins_column_list = case[1]
                ins_expr_list = case[2]
        if ins_column_list:
            yield 'INSERT INTO ', self.dst, ' (', ins_column_list, ')', br
            yield 'SELECT ', ins_expr_list, br
            yield 'FROM ', self.src, br
            if upd_set_list:
                yield 'ON CONFLICT DO UPDATE SET', br
                yield join_list(', ', [(a[0], " = ", a[1]) for a in upd_set_list])
            elif upd_column_list:
                yield 'ON CONFLICT DO UPDATE SET (', br
                yield Indented(upd_column_list), br, ') = (', br, Indented(upd_expr_list), br, ')'
            else:
                yield 'ON CONFLICT DO NOTHING'
        elif upd_set_list:
            yield UpdateA(self.dst, upd_set_list, self.src, self.on).writeout()
        elif upd_column_list:
            yield UpdateB(self.dst, upd_column_list, upd_expr_list, self.src, self.on).writeout()

    def ForEach(self):
        # yield 'FOREACH '
        # if self.cursor:
        #     yield self.cursor, ' FOR '
        # yield self.select, '\n'
        # yield self.statements
        # yield 'END FOREACH\n'

        # TODO
        # - "SELECT a, b INTO x, y" -> "SELECT a as x, b as y"
        # - self.record = "__rec__", "__rec2__", ...
        # - self.variables = ["x", "y"]
        # - What about self.cursor ?
        
        yield 'FOR ', self.record, ' IN ', self.select, ' LOOP\n', Indent
        for var in self.variables:
            yield var, ' := ', self.record, '.', var, ';\n'
        yield self.statements
        yield Dedent, 'END LOOP'
        
        # FOR _rec_ IN SELECT a as x, b as y FROM ... LOOP
        # x := _rec_.x;
        # y := _rec_.y;
        # ...
        # END LOOP;

    def Table(self):
        yield self.expr, ' AS ', self.name, ' (', Indented(self.columns), ')'

    def ReturnType(self):
        yield self.type
        if self.name:
            # TODO: Warn about missing support for named return paramaters
            #yield ' AS ', self.name
            pass

    def System(self):
        yield 'PERFORM system_call(', self.expr, ')'

    def DefineGlobal(self):
        yield 'DEFINE GLOBAL ', self.name, ' ', self.type, ' DEFAULT ', self.default, ' ', Comment(NotSupported("DEFINE GLOBAL"))

    def Return(self):
        yield 'RETURN'
        if self.values:
            if len(self.values) > 1:
                yield ' ', BlockComment(NotSupported("RETURN multiple values"))
            yield ' ', self.values
        if self.resume:
            yield ' WITH RESUME', ' ', BlockComment(NotSupported("RETURN WITH RESUME"))

    def BlockComment(self):
        yield '/* ', self.text, ' */'

    def Continue(self):
        yield "CONTINUE"
        #yield ' ', self.loop

    def BeginEnd(self):
        if len(self.declarations):
            yield "DECLARE\n", Indented(self.declarations)
        yield "BEGIN\n", Indented(self.statements), "END\n"

    def CreateAggregate(self):
        br = Br(self)
        def _map(a,f):
            if a == "INIT":
                return "initial_condition = ", NotSupported(f)
            if a == "ITER":
                return "sfunc = ", f
            if a == "COMBINE":
                return None
            if a == "FINAL":
                return "ffunc = ", f 
        yield 'CREATE AGGREGATE ', self.name, ' (', NotSupported('arg_data_type'), ') (', br, Indent,
        yield join_list((',', br), [ _map(a, f) for a, f in self.arglist if _map(a, f) ])
        yield Dedent, br, ')'

    def UnlockTable(self):
        yield Noop(), ' ', BlockComment(NotSupported('UNLOCK TABLE ', self.table)), ''

writer = PostgresWriter
