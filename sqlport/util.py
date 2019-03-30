
def pretty_print(obj, indent=0, key=None, showNone=True, done=None):
    print('|   ' * indent + (str(key)+": " if key != None else "") + type(obj).__name__ +  ':')
    if done == None:
        done = set()
    _id = id(obj)
    if _id in done:
        return
    done.add(_id)
    indent += 1
    if isinstance(obj, (list,tuple)):
        children = enumerate(obj)
    else:
        children = obj.__dict__.items()
    for key,value in children:
        if hasattr(value, '__dict__') or isinstance(value, (list,tuple)):
            pretty_print(value, indent, key, showNone, done)
        elif value != None or showNone:
            print('|   ' * indent +  str(key) + ': ' + repr(value))

def join_list(e, elements):
    r = []
    ln = len(elements)
    if ln == 0:
        return r
    r.append(elements[0])
    for i in range(1, ln):
        r.append(e)
        r.append(elements[i])
    return r
