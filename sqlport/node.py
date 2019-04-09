
import re
from io import StringIO

writer = None

def writeout(stream, fh):
    while hasattr(stream, "write"):
        stream = stream.write()
    if isinstance(stream, str):
        fh.write(stream)
    else:
        try:
            iterator = iter(stream)
        except TypeError:
            return
        for e in iterator:
            writeout(e, fh)

# private-use unicode space from E000 to F8FF:
Indent = '\ue001'
Dedent = '\ue002'

indent_regex = re.compile('[{}{}\n]|[^{}{}\n]+'.format(Indent, Dedent, Indent, Dedent), re.MULTILINE)

class IndentSub:
    def __init__(self, indent=2):
        self.indent = ' ' * indent
        self.level = 0
        self.current = ''
        self.newline = False

    def __call__(self, match):
        text = match.group()
        if text == '\n':
            self.newline = True
            return '\n'
        elif text == Indent:
            self.level += 1
            self.current = self.indent * self.level
            return ''
        elif text == Dedent:
            self.level -= 1
            self.current = self.indent * self.level
            return ''
        elif self.newline:
            self.newline = False
            return self.current + text
        else:
            return text
    
class Node:    
    def write(self, cls=None):
        if cls is None:
            cls = self.__class__
        return getattr(writer, cls.__name__)(self)

    def render(self, fh=None):
        _fh = StringIO()
        self.writeout(_fh)
        text = indent_regex.sub(IndentSub(), _fh.getvalue())
        if fh:
            fh.write(text)
        else:
            return text

    def writeout(self, fh=None):
        if fh:
            writeout(self.write(), fh)
        else:
            fh = StringIO()
            writeout((self,), fh)
            return fh.getvalue()
    
    @property
    def id(self):
        return None

    @property
    def children(self):
        for key, value in self.__dict__.items():
            if key == "parent":
                continue
            if isinstance(value, Node):
                yield key, value

    def set_parents(self):
        for obj, parents, path in nodewalk(self):
            if len(parents):
                obj.parent = parents[-1]
                obj.parent_key = path[-1]

    def setchild(self, key, value):
        setattr(self, key, value)

    def replace(self, new):
        assert self != new
        self.parent.setchild(self.parent_key, new)
        del self.parent
        del self.parent_key

    def detach(self, cleanup=False):
        parent = self.parent
        self.replace(None)
        if cleanup and parent.is_dead():
            parent.detach(cleanup)

    def is_dead(self):
        return False

    @property
    def width(self):
        if not hasattr(self, '_width'):
            self._width = 0
            self._width = len(self.writeout())
        return self._width
    
class Units(Node):
    def __init__(self, value, unit):
        self.value = value
        self.unit = unit
    
class NodeList(Node, list):
    def __init__(self, *nodes):
        for node in nodes:
            self.append(node)

    @property
    def children(self):
        for key, value in enumerate(self):
            if isinstance(value, Node):
                yield key, value
    
    def push(self, node):
        self.insert(0, node)
        return self

    def append(self, node):
        super().append(node)
        return self

    def setchild(self, key, value):
        self[key] = value

class StatementList(NodeList): pass

class CommaList(NodeList): pass

class Indented(NodeList): pass

class Select(Node):
    def __init__(self, skip, first, distinct, columns, into_vars, table, where, group_by, having, unions=None, order_by=None, into=None):
        self.skip = skip
        self.first = first
        self.distinct = distinct
        self.columns = columns
        self.into_vars = into_vars
        self.table = table
        self.where = where
        self.group_by = group_by
        self.having = having
        self.order_by = order_by
        self.into = into
        self.unions = unions

class Table(Node):
    def __init__(self, expr, name=None, columns=None):
        self.expr = expr
        self.name = name
        self.columns = columns

class OrderByItem(Node):
    def __init__(self, expr, dir):
        self.expr = expr
        self.dir = dir

class Delete(Node):
    def __init__(self, table, where):
        self.table = table
        self.where = where

class Insert(Node):
    def __init__(self, table, columns, values, select):
        self.table = table
        self.columns = columns
        self.values = values
        self.select = select
    
class SubSelect(Select): pass

class SelectColumn(Node):
    def __init__(self, expr, name=None):
        self.expr = expr
        self.name = name

    @property
    def id(self):
        return self.name.id

class TableColumn(Node):
    def __init__(self, table, column):
        self.table = table
        self.column = column

    @property
    def id(self):
        return "{}.{}".format(self.table.id, self.column.id)

class Name(Node):
    def __init__(self, name):
        assert isinstance(name, str)
        self.name = name

    @property
    def id(self):
        return self.name

class EntityRef(Node):
    def __init__(self, name, database=None, server=None):
        self.name = name
        self.database = database
        self.server = server

    @property
    def id(self):
        name = self.name
        if isinstance(name, OwnerDotName):
            name = name.name
        if self.database:
            if self.server:
                return "{}@{}:{}".format(self.database.id, self.server.id, name.id)
            return "{}:{}".format(self.database.id, name.id)
        return name.id
        
class As(Node):
    def __init__(self, obj, name):
        self.obj = obj
        self.name = name

    @property
    def id(self):
        return self.name.id

class SubSelectAsSelectTable(Node):
    def __init__(self, sub_select, name, columns):
        self.sub_select = sub_select
        self.name = name
        self.columns = columns

class Truncate(Node):
    def __init__(self, table):
        self.table = table

class UpdateA(Node):
    def __init__(self, table, assignments, _from, where):
        self.table = table
        self.assignments = assignments
        self._from = _from
        self.where = where

class UpdateB(Node):
    def __init__(self, table, columns, values, _from, where):
        self.table = table
        self.columns = columns
        self.values = values
        self._from = _from
        self.where = where

class Merge(Node):
    def __init__(self, dst, src, on, case_list):
        self.dst = dst
        self.src = src
        self.on = on
        self.case_list = case_list

class UpdateStatistics(Node):
    def __init__(self, mode, type, name):
        self.mode = mode
        self.type = type
        self.name = name

class Join(Node):
    def __init__(self, join, left, right, on):
        self.join = join
        self.left = left
        self.right = right
        self.on = on

class Call(Node):
    def __init__(self, name, args, statement=False, returning=None):
        self.name = name
        self.args = args
        self.statement = statement
        self.returning = returning

class ExecuteImmediate(Node):
    def __init__(self, expr):
        self.expr = expr
        
class System(Node):
    def __init__(self, expr):
        self.expr = expr

class CreateRole(Node):
    def __init__(self, name):
        self.name = name

class CreateTable(Node):
    def __init__(self, name, columns, temp=False, if_not_exists=False):
        self.name = name
        self.columns = columns
        self.temp = temp
        self.if_not_exists = if_not_exists

class CreateTableColumn(Node):
    def __init__(self, name, ctype, default, not_null, primary_key):
        self.name = name
        self.ctype = ctype
        self.default = default
        self.not_null = not_null
        self.primary_key = primary_key

class View(Node):
    def __init__(self, name, columns, select):
        self.name = name
        self.columns = columns
        self.select = select

class AddConstraint(Node):
    def __init__(self, table, constraint):
        self.table = table
        self.constraint = constraint

class AddColumn(Node):
    def __init__(self, table, column):
        self.table = table
        self.column = column

class UniqueConstraint(Node):
    def __init__(self, name, columns):
        self.name = name
        self.columns = columns

class CheckConstraint(Node):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

class PrimaryKeyConstraint(Node):
    def __init__(self, name, columns):
        self.name = name
        self.columns = columns

class ForeignKeyConstraint(Node):
    def __init__(self, name, columns, references):
        self.name = name
        self.columns = columns
        self.references = references

class Type(Node):
    def __init__(self, name, size=None, size2=None):
        self.name = name
        self.size = size
        self.size2 = size2

class DatetimeType(Node):
    def __init__(self, type, a=None, b=None):
        self.type = type
        self.a = a
        self.b = b

class Today(Node): pass

class Current(Node):
    def __init__(self, a=None, b=None):
        self.a = a
        self.b = b

class Interval(Node):
    def __init__(self, value, a, b):
        self.value = value
        self.a = a
        self.b = b

class RowType(Node):
    def __init__(self, type, not_null=False):
        self.type = type
        self.not_null = not_null

class MultiSetType(Node):
    def __init__(self, type, not_null=False):
        self.type = type
        self.not_null = not_null

class SetType(Node):
    def __init__(self, type, not_null=False):
        self.type = type
        self.not_null = not_null

class ListType(Node):
    def __init__(self, type, not_null=False):
        self.type = type
        self.not_null = not_null

class MultiSetValue(Node):
    def __init__(self, select):
        self.select = select

class TimeUnit(Node):
    def __init__(self, name, size=None):
        self.name = name
        self.size = size

class Drop(Node):
    def __init__(self, kind, name, if_exists, arg_types):
        self.kind = kind
        self.name = name
        self.if_exists = if_exists
        self.arg_types = arg_types

class LockTable(Node):
    def __init__(self, table, mode):
        self.table = table
        self.mode = mode

class UnlockTable(Node):
    def __init__(self, table):
        self.table = table

class CreateIndex(Node):
    def __init__(self, name, table, columns, unique, if_not_exists):
        self.name = name
        self.table = table
        self.columns = columns
        self.unique = unique
        self.if_not_exists = if_not_exists

class CreateSynonym(Node):
    def __init__(self, name, dest):
        self.name = name
        self.dest = dest

class CreateSequence(Node):
    def __init__(self, name, increment, start, minvalue, maxvalue, cache, order):
        self.name = name
        self.increment = increment
        self.start = start
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.cache = cache
        self.order = order
        
class AlterSequence(Node):
    def __init__(self, name, restart):
        self.name = name
        self.restart = restart
        
class Operator(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def is_dead(self):
        return self.left is None and self.right is None

class Minus(Node):
    def __init__(self, expr):
        self.expr = expr

class Cast(Node):
    def __init__(self, expr, to):
        self.expr = expr
        self.to = to

class Group(Node):
    def __init__(self, expr):
        self.expr = expr

    def is_dead(self):
        return self.expr is None

class Union(Node):
    def __init__(self, type, select):
        self.type = type
        self.select = select

class Exists(Node):
    def __init__(self, select):
        self.select = select
        
class In(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        
class NotIn(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class IsNull(Node):
    def __init__(self, expr):
        self.expr = expr

class IsNotNull(Node):
    def __init__(self, expr):
        self.expr = expr

class Not(Node):
    def __init__(self, expr):
        self.expr = expr
        
class Outer(Node):
    def __init__(self, expr):
        self.expr = expr

    @property
    def id(self):
        return self.expr.id

class Between(Node):
    def __init__(self, value, a, b):
        self.value = value
        self.a = a
        self.b = b
        
class NotBetween(Between): pass
        
class Slice(Node):
    def __init__(self, value, left, right=None):
        self.value = value
        self.left = left
        self.right = right

class Case(Node):
    def __init__(self, when_list, else_case):
        self.when_list = when_list
        self.else_case = else_case

class WhenThen(Node):
    def __init__(self, when, then):
        self.when = when
        self.then = then

class Cons(Node):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def is_dead(self):
        return self.a is None and self.b is None

class CreateTrigger(Node):
    def __init__(self, name, type, table, old, new, expr, statement):
        self.name = name
        self.type = type
        self.table = table
        self.old = old
        self.new = new
        self.expr = expr
        self.statement = statement
        
class CreateProcedure(Node):
    def __init__(self, type, name, parameters, returning, variant, declarations, statements, doc):
        self.type = type
        self.name = name
        self.parameters = parameters
        self.returning = returning
        self.variant = variant
        self.declarations = declarations
        self.statements = statements
        self.doc = doc
        
class Parameter(Node):
    def __init__(self, name, type, default):
        self.name = name
        self.type = type
        self.default = default

class Define(Node):
    def __init__(self, names, type):
        self.names = names
        self.type = type
        
class DefineGlobal(Node):
    def __init__(self, name, type, default):
        self.name = name
        self.type = type
        self.default = default

class Let(Node):
    def __init__(self, names, values):
        self.names = names
        self.values = values

class Return(Node):
    def __init__(self, values=None, resume=None):
        self.values = values
        self.resume = resume

class ReturnType(Node):
    def __init__(self, type, name):
        self.type = type
        self.name = name

class If(Node):
    def __init__(self, cases, default):
        self.cases = cases
        self.default = default

class For(Node):
    def __init__(self, var, a, b, step, statements):
        self.var = var
        self.a = a
        self.b = b
        self.step = step
        self.statements = statements

class ForEach(Node):
    def __init__(self, cursor, select, statements):
        self.cursor = cursor
        self.select = select
        self.statements = statements
        
class While(Node):
    def __init__(self, expr, statements):
        self.expr = expr
        self.statements = statements
        
class BeginEnd(Node):
    def __init__(self, declarations, statements):
        self.declarations = declarations
        self.statements = statements
        
class Exit(Node):
    def __init__(self, loop):
        self.loop = loop

class Continue(Node):
    def __init__(self, loop):
        self.loop = loop

class OnException(Node):
    def __init__(self, codes, statements, resume):
        self.codes = codes
        self.statements = statements
        self.resume = resume
        
class Raise(Node):
    def __init__(self, sql_error, isam_error, expr):
        self.sql_error = sql_error
        self.isam_error = isam_error
        self.expr = expr
                 
class Trim(Node):
    def __init__(self, type, char, expr):
        self.type = type
        self.char = char
        self.expr = expr

class Count(Node):
    def __init__(self, distinct, expr):
        self.distinct = distinct
        self.expr = expr

class SetLockMode(Node):
    def __init__(self, seconds):
        self.seconds = seconds

class Grant(Node):
    def __init__(self, permission, on, to, _as):
        self.permission = permission
        self.on = on
        self.to = to
        self._as = _as
        
class Revoke(Node):
    def __init__(self, permission, on, _from, _as):
        self.permission = permission
        self.on = on
        self._from = _from
        self._as = _as
        
class CreateAggregate(Node):
    def __init__(self, name, arglist):
        self.name = name
        self.arglist = arglist
        
class FunctionSignature(Node):
    def __init__(self, type, name, arg_types):
        self.type = type
        self.name = name
        self.arg_types = arg_types

class OwnerDotName(Node):
    def __init__(self, owner, name):
        self.owner = owner
        self.name = name

class Nvl(Node):
    def __init__(self, args):
        self.args = args

class Matches(Node):
    def __init__(self, text, pattern, neg):
        self.text = text
        self.pattern = pattern
        self.neg = neg

class Comment(Node):
    def __init__(self, *text):
        self.text = ' '.join([ x.writeout() if isinstance(x, Node) else str(x) for x in text ])

class BlockComment(Comment): pass
    
class NotSupported(Node):
    def __init__(self, *args):
        self.args = args

class String(Node):
    def __init__(self, value):
        self.value = value

class CurrentOf(Node):
    def __init__(self, name):
        self.name = name

class SetConstraints(Node):
    def __init__(self, name, mode):
        self.name = name
        self.mode = mode

class BeginTransaction(Node): pass
class CommitTransaction(Node): pass

class Substring(Node):
    def __init__(self, expr, from_, for_):
        self.expr = expr
        self.from_ = from_
        self.for_ = for_

class ListExpr(Node):
    def __init__(self, expr_list):
        self.expr_list = expr_list

class Noop(Node): pass

class Br(Node):
    def __init__(self, node, *thresholds):
        width = node.width
        self.level = 0
        if not thresholds:
            thresholds = (70,)
        for value in thresholds:
            if width >= value:
                self.level += 1

    def __call__(self, level=1):
        if level <= self.level:
            return '\n'
        else:
            return ' '

# def nodewalk(obj, handler):
#     if handler(obj):
#         for key, value in obj.children:
#             if isinstance(value, (list,dict)) or hasattr(value, "__dict__"):
#                 nodewalk(value, handler)

def nodewalk(obj, depthFirst=False, parents=(), path=(), done=None):
    if done == None:
        done = set()
    _id = id(obj)
    if _id in done:
        return
    done.add(_id)
    if not depthFirst:
        yield obj, parents, path
    for key, value in obj.children:
        yield from nodewalk(value, depthFirst, parents + (obj,), path + (key,))
    if depthFirst:
        yield obj, parents, path

def find_nodes(obj, pred, recurse=False):
    if pred(obj):
        yield obj
        if not recurse:
            return
    if isinstance(obj, Node):
        for key, value in obj.children:
            if callable(recurse) and not recurse(obj, key, value):
                continue
            if isinstance(value, Node):
                yield from find_nodes(value, pred, recurse)
