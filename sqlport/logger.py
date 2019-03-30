
class Logger(object):
    level = 1
    
    def __init__(self, f):
        self.f = f

    def error(self, msg, *args, **kwargs):
        if self.level > 0:
            self.f.write('ERROR: ' + (msg % args) + '\n')

    def warning(self, msg, *args, **kwargs):
        if self.level > 1:
            self.f.write('WARNING: ' + (msg % args) + '\n')

    def debug(self, msg, *args, **kwargs):
        if self.level > 2:
            self.f.write((msg % args) + '\n')

    info = debug
    critical = debug
