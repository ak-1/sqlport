
import sys
from . import node
from . writers import postgres
from . lexer import SqlLexer, TooManyErrors
from . parser import SqlParser

node.writer = postgres.writer

def parse(text, outfh=None, verbose=0, onerror=None, maxerrors=1000000):
    if not outfh:
        outfh = sys.stdout
    lexer = SqlLexer()
    parser = SqlParser()
    parser.input_text = text
    if verbose:
        outfh.write("-"*80 + '\n')
        outfh.write("{}\n\n".format(text))
    return parser.parse(lexer.tokenize(text, onerror, maxerrors), onerror, maxerrors)

def parse_file(filepath):
    print("parse {}".format(filepath))
    return parse(open(filepath).read())

def lex(text, outfh=None, verbose=0, quiet=0, onerror=None):
    if not outfh:
        outfh = sys.stdout
    if verbose > 1:
        outfh.write("-"*80 + '\n')
        outfh.write("{}\n\n".format(text))
    lexer = SqlLexer()
    for token in lexer.tokenize(text, onerror):
        if verbose:
            outfh.write(str(token)+'\n')

def lex_file(filepath):
    print("lex {}".format(filepath))
    lex(open(filepath).read())
    
def repl():
    while True:
        try:
            text = input('sql > ')
        except EOFError:
            break
        if text:
            parse(text).render()
