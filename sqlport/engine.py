
import sys
from . import node
from . writers import postgres
from . lexer import SqlLexer
from . parser import SqlParser

node.writer = postgres.writer

def parse(text, outfh=None, verbose=0):
    if not outfh:
        outfh = sys.stdout
    lexer = SqlLexer()
    parser = SqlParser()
    parser.input_text = text
    if verbose:
        outfh.write("-"*80 + '\n')
        outfh.write("{}\n\n".format(text))
    return parser.parse(lexer.tokenize(text))

def parse_file(filepath):
    print("parse {}".format(filepath))
    return parse(open(filepath).read())

def lex(text, outfh=None, verbose=0, quiet=0):
    if not outfh:
        outfh = sys.stdout
    if verbose:
        outfh.write("-"*80 + '\n')
        outfh.write("{}\n\n".format(text))
    for token in lexer.tokenize(text):
        if verbose:
            outfh.write(str(token))
    #print(' '.join([t.value for t in lexer.tokenize(text)]))

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
