
from .. node import *
from .. util import join_list

class InformixWriter:
    def StatementList(self):
        for s in self:
            if s != None:
                yield s
                if not hasattr(s, "EXPR_STMT"):
                    yield ';'
                yield '\n\n'

    def CommaList(self):
        br = Br(self, 60)
        return join_list((',', br), [ c for c in self ])

    def Select(self):
        yield "SELECT "
        if self.skip:
            yield 'SKIP ', self.skip, ' '
        if self.first:
            yield 'FIRST ', self.first, ' '
        if self.distinct:
            yield "DISTINCT "
        yield Indented(self.columns)
        if self.into_vars:
            yield ' INTO ', self.into_vars
        yield " FROM ", self.table
        if self.where:
            yield ' WHERE ', self.where
        if self.group_by:
            yield ' GROUP BY ', self.group_by
        if self.having:
            yield ' HAVING ', self.having
        if self.order_by:
            yield ' ORDER BY ', self.order_by
        if self.into:
            yield ' INTO TEMP ', self.into
        if self.unions:
            for union in self.unions:
                yield union

    def Union(self):
        yield '\n', self.type, ' ', self.select

    def Table(self):
        yield 'TABLE(', self.expr, ')'
        if self.name:
            yield ' AS ', self.name, ' (', Indented(self.columns), ')'

    def OrderByItem(self):
        yield self.expr
        if self.dir:
            yield ' ', self.dir
        
    def Delete(self):
        yield "DELETE FROM ", self.table
        if self.where:
            yield ' WHERE ', self.where

    def Insert(self):
        br = Br(self, 60)
        yield "INSERT INTO ", self.table
        if self.columns:
            yield ' (', br, Indented(self.columns), br, ')'
        if self.values:
            yield ' VALUES (', br, Indented(self.values), br, ')'
        else:
            yield br, self.select

    def SubSelect(self):
        yield '('
        yield self.write(Select)
        yield ')'

    def SelectColumn(self):
        yield self.expr
        if self.name:
            yield " AS ", self.name

    def TableColumn(self):
        return self.table, '.', self.column

    def Name(self):
        return self.name
    
    def EntityRef(self):
        if self.database:
            yield self.database
            if self.server:
                yield '@', self.server
            yield ':'
        yield self.name
        
    def As(self):
        yield self.obj
        if self.name:
            yield " AS ", self.name

    def SubSelectAsSelectTable(self):
        yield self.sub_select
        if self.name:
            yield " AS ", self.name
        yield ' (', Indented(self.columns), ')'

    def Truncate(self):
        yield "TRUNCATE ", self.table

    def UpdateA(self):
        yield "UPDATE ", self.table, " SET "
        yield join_list(', ', [(a[0], " = ", a[1]) for a in self.assignments])
        if self._from:
            yield ' FROM ', self._from
        if self.where:
            yield ' WHERE ', self.where
        
    def UpdateB(self):
        yield "UPDATE ", self.table, " SET "
        yield "(", Indented(self.columns), ') = (', Indented(self.values), ')'
        if self._from:
            yield ' FROM ', self._from
        if self.where:
            yield ' WHERE ', self.where

    def Merge(self):
        yield "MERGE INTO ", self.dst, " USING ", self.src, " ON ", self.on
        for case in self.case_list:
            if case[0] == "UPDATE_A":
                yield " WHEN MATCHED THEN UPDATE SET "
                yield join_list(', ', [(a[0], " = ", a[1]) for a in case[1]])
            elif case[0] == "UPDATE_B":
                yield " WHEN MATCHED THEN UPDATE SET ("
                yield case[1], ") = (", case[2], ")"
            elif case[0] == "INSERT":
                yield " WHEN NOT MATCHED THEN INSERT ("
                yield case[1], ') VALUES (', case[2], ')'

    def UpdateStatistics(self):
        yield "UPDATE STATISTICS"
        if self.mode:
            yield " ", self.mode
        if self.name:
            yield " FOR ", self.type, " ", self.name

    def Join(self):
        br = Br(self)
        yield self.left, br, self.join, ' JOIN ', self.right
        if self.on:
            yield ' ON ', self.on

    def Call(self):
        br = Br(self)
        if self.statement:
            yield 'CALL '
        yield self.name, '(', br, self.args, br, ')'
        if self.returning:
            yield ' RETURNING ', self.returning

    def Nvl(self):
        yield 'nvl(', self.args, ')'

    def ExecuteImmediate(self):
        yield 'EXECUTE IMMEDIATE ', self.expr
        
    def System(self):
        yield 'SYSTEM ', self.expr
        
    def Units(self):
        return self.value, " UNITS ", self.unit

    def CreateTable(self):
        br = Br(self)
        yield "CREATE "
        if self.temp:
            yield "TEMP "
        yield "TABLE "
        if self.if_not_exists:
            yield "IF NOT EXISTS "
        yield self.name, " ("
        yield br, Indented(self.columns), br
        yield ")"

    def CreateTableColumn(self):
        yield self.name, ' ', self.ctype
        if self.default:
            yield " DEFAULT ", self.default
        if self.not_null:
            yield " NOT NULL"
        if self.primary_key:
            yield " PRIMARY KEY"

    def View(self):
        return 'CREATE VIEW ', self.name, ' (', Indented(self.columns), ') AS ', self.select

    def AddConstraint(self):
        yield 'ALTER TABLE ', self.table
        yield ' ADD CONSTRAINT ', self.constraint

    def AddColumn(self):
        yield 'ALTER TABLE ', self.table
        yield ' ADD ', self.column

    def CheckConstraint(self):
        yield 'CHECK (', self.expr, ')'
        if self.name:
            yield ' CONSTRAINT ', self.name

    def PrimaryKeyConstraint(self):
        yield 'PRIMARY KEY (', Indented(self.columns), ')'
        if self.name:
            yield ' CONSTRAINT ', self.name

    def ForeignKeyConstraint(self):
        yield 'FOREIGN KEY (', Indented(self.columns), ')',
        yield ' REFERENCES ', self.references
        if self.name:
            yield ' CONSTRAINT ', self.name

    def UniqueConstraint(self):
        yield 'UNIQUE (', self.columns, ')'
        if self.name:
            yield ' CONSTRAINT ', self.name

    def Type(self):
        yield self.name
        if self.size:
            yield '(', self.size
            if self.size2:
                yield ',', self.size2
            yield ')'

    def DatetimeType(self):
        yield self.type, ' ', self.a, ' TO ', self.b
    
    def Current(self):
        yield 'CURRENT'
        if self.a:
            yield ' ', self.a, ' TO ', self.b

    def Today(self):
        yield 'TODAY'
        
    def Interval(self):
        yield 'INTERVAL (', self.value, ') ', self.a, ' TO ', self.b
        
    def RowType(self):
        yield 'ROW(', self.type,
        if self.not_null:
            yield ' NOT NULL'
        yield ')'
        
    def MultiSetType(self):
        yield 'MULTISET(', self.type,
        if self.not_null:
            yield ' NOT NULL'
        yield ')'

    def SetType(self):
        yield 'SET(', self.type,
        if self.not_null:
            yield ' NOT NULL'
        yield ')'
        
    def ListType(self):
        yield 'LIST(', self.type,
        if self.not_null:
            yield ' NOT NULL'
        yield ')'
        
    def MultiSetValue(self):
        yield 'MULTISET(', self.select, ')'

    def TimeUnit(self):
        yield self.name
        if self.size:
            yield '(', self.size
            yield ')'

    def Drop(self):
        yield 'DROP ', self.kind
        if self.if_exists:
            yield ' IF EXISTS'
        yield ' ', self.name
        if self.arg_types:
            yield "(", self.arg_types, ")"
        
    def LockTable(self):
        yield 'LOCK TABLE ', self.table, ' IN ', self.mode, ' MODE'
        
    def UnlockTable(self):
        yield 'UNLOCK TABLE ', self.table
        
    def CreateIndex(self):
        br = Br(self)
        yield 'CREATE'
        if self.unique:
            yield ' UNIQUE'
        yield ' INDEX '
        if self.if_not_exists:
            yield 'IF NOT EXISTS '
        yield self.name, ' ON ', self.table, ' (', br, Indented(self.columns), br, ')'

    def CreateSynonym(self):
        yield 'CREATE SYNONYM ', self.name, ' FOR ', self.dest

    def CreateSequence(self):
        yield 'CREATE SEQUENCE ', self.name
        if self.increment:
            yield ' INCREMENT BY ', self.increment
        if self.start:
            yield ' START WITH ', self.start
        if self.maxvalue:
            yield ' MAXVALUE ', self.maxvalue
        if self.minvalue:
            yield ' MINVALUE ', self.minvalue
        if self.cache:
            yield ' ', self.cache
        if self.order:
            yield ' ', self.order

    def AlterSequence(self):
        yield 'ALTER SEQUENCE', self.name
        yield ' RESTART WITH ', self.restart
        
    def Operator(self):
        yield self.left, ' ', self.op, ' ', self.right

    def Minus(self):
        yield '-', self.expr

    def Outer(self):
        yield 'OUTER(', Indented(self.expr), ')'
        
    def Cast(self):
        yield self.expr, '::', self.to

    def Group(self):
        br = Br(self)
        yield '(', br, Indented(self.expr), br, ')'

    def Exists(self):
        yield 'EXISTS (', Indented(self.select), ')'
        
    def In(self):
        yield self.left, ' IN (', Indented(self.right), ')'

    def NotIn(self):
        yield self.left, ' NOT IN (', Indented(self.right), ')'


    def IsNull(self):
        yield self.expr, ' IS NULL'
        
    def IsNotNull(self):
        yield self.expr, ' IS NOT NULL'
        
    def Not(self):
        yield 'NOT ', self.expr
        
    def Between(self):
        yield self.value, ' BETWEEN ', self.a, ' AND ', self.b

    def NotBetween(self):
        yield self.value, ' NOT BETWEEN ', self.a, ' AND ', self.b
        
    def Slice(self):
        yield self.value, '[', self.left
        if self.right:
            yield ',', self.right
        yield ']'

    def Case(self):
        br = Br(self)
        yield 'CASE', Indent,
        for c in self.when_list:
            yield br, 'WHEN ', c.when, ' THEN', br, Indented(c.then)
        if self.else_case:
            yield br, 'ELSE ', br, Indented(self.else_case)
        yield Dedent, br, 'END'

    def Cons(self):
        yield self.a, ', ', self.b

    def CreateTrigger(self):
        yield 'CREATE TRIGGER ', self.name
        yield ' ', self.type, ' ON ', self.table
        yield ' REFERENCING'
        if self.old:
            yield ' OLD AS ', self.old
        yield ' NEW AS ', self.new
        yield ' FOR EACH ROW WHEN ', self.expr, " (", self.statement, ")"

    def CreateProcedure(self):
        yield 'CREATE ', self.type, ' ', self.name,
        yield '(', join_list(', ', self.parameters), ')\n'
        if self.returning:
            yield ' RETURNING ', join_list(', ', self.returning), '\n'
        if self.variant != None:
            yield ' WITH ('
            if not self.variant:
                yield 'NOT '
            yield 'VARIANT)\n'
        yield Indented(self.declarations)
        yield 'END ', self.type,
        if self.doc:
            yield ' DOCUMENT ', self.doc
        yield '\n'
        
    def Parameter(self):
        yield self.name, ' ', self.type
        if self.default:
            yield ' DEFAULT ', self.default

    def Define(self):
        yield 'DEFINE ', self.names, ' ', self.type
            
    def DefineGlobal(self):
        yield 'DEFINE GLOBAL ', self.name, ' ', self.type, ' DEFAULT ', self.default
        
    def Let(self):
        yield 'LET ', self.names, ' = ', self.values
        
    def Return(self):
        yield 'RETURN'
        if self.values:
            yield ' ', self.values
        if self.resume:
            yield ' WITH RESUME'

    def ReturnType(self):
        yield self.type
        if self.name:
            yield ' AS ', self.name

    def If(self):
        yield 'IF ', self.cases[0].when, ' THEN ', Indented(self.cases[0].then)
        for case in self.cases[1:]:
            yield 'ELIF ', case.when, ' THEN ', Indented(case.then)
        if self.default != None:
            yield 'ELSE ', Indented(self.default)
        yield 'END IF'
        
    def For(self):
        yield 'FOR ', self.var, ' = ', self.a, ' TO ', self.b
        if self.step:
            yield ' STEP ', self.step
        yield '\n', Indented(self.statements), 'END FOR'

    def ForEach(self):
        yield 'FOREACH '
        if self.cursor:
            yield self.cursor, ' FOR '
        yield self.select, '\n', Indented(self.statements), 'END FOREACH\n'

    def While(self):
        yield 'WHILE ', self.expr, '\n', Indented(self.statements), 'END WHILE\n'
        
    def BeginEnd(self):
        yield "BEGIN\n", Indent
        if len(self.declarations):
            yield self.declarations
        yield self.statements, Dedent, "END\n"

    def Exit(self):
        yield "EXIT ", self.loop
        
    def Continue(self):
        yield "CONTINUE ", self.loop
        
    def OnException(self):
        yield "ON EXCEPTION "
        if self.codes:
            yield "IN (", self.codes, ")"
        yield "\n"
        yield self.statements
        yield "\nEND EXCEPTION"
        if self.resume:
            yield " WITH RESUME"
        yield "\n"
        
    def Raise(self):
        yield "RAISE EXCEPTION ",  self.sql_error,
        yield ", ", self.isam_error, ', ', self.expr

    def Trim(self):
        yield "TRIM("
        if self.type:
            yield self.type
            if self.char:
                yield ' ', self.char
            yield ' FROM '
        yield self.expr, ")"
        
    def Count(self):
        yield "COUNT("
        if self.distinct:
            yield "DISTINCT "
        yield self.expr, ")"
        
    def SetLockMode(self):
        yield "SET LOCK MODE TO "
        if self.seconds:
            yield "WAIT ", self.seconds
        else:
            yield "NOT WAIT"

    def Grant(self):
        yield 'GRANT ', self.permission
        if self.on:
            yield ' ON ', self.on
        yield ' TO ', self.to
        if self._as:
            yield ' AS ', self._as

    def Revoke(self):
        yield 'REVOKE ', self.permission
        if self.on:
            yield ' ON ', self.on
        yield ' FROM ', self._from
        if self._as:
            yield ' AS ', self._as
            
    def CreateAggregate(self):
        br = Br(self)
        yield 'CREATE AGGREGATE ', self.name, ' WITH (', br, Indent,
        yield join_list((',', br), [ (a, ' = ', f) for a, f in self.arglist ])
        yield Dedent, br, ')'

    def FunctionSignature(self):
        yield self.type, ' ', self.name, '(', join_list(', ', self.arg_types), ')'

    def OwnerDotName(self):
        yield self.owner, '.', self.name

    def Matches(self):
        yield self.text
        if self.neg:
            yield ' NOT'
        yield ' MATCHES ', self.pattern

    def NotSupported(self):
        yield "NOT_SUPPORTED:"
        if self.args:
            yield " ", self.args

    def Comment(self):
        for line in self.text.split('\n'):
            yield '-- ', line, '\n'

    def BlockComment(self):
        yield '{ ', self.text, ' }'

    def String(self):
        yield self.value

    def Noop(self):
        pass

    def Indented(self):
        yield Indent
        yield from self
        yield Dedent

    def Br(self):
        yield self()

    def CreateRole(self):
        yield 'CREATE ROLE ', self.name

    def BeginTransaction(self):
        yield 'BEGIN TRANSACTION'

    def CommitTransaction(self):
        yield 'COMMIT TRANSACTION'

    def CurrentOf(self):
        yield 'CURRENT OF ', self.name

    def SetConstraints(self):
        yield 'SET CONSTRAINTS ', self.name
        if self.mode:
            yield ' ', self.mode

    def Substring(self):
        yield 'SUBSTRING(', self.expr, ' FROM ', self.from_
        if self.for_:
            yield ' FOR ', self.for_
        yield ')'

    def ListExpr(self):
        yield 'LIST {', self.expr_list, '}'

writer = InformixWriter
