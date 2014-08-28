# -*- coding: utf-8 -*-
#
# Parser to transform a post into brower-usable html
#

from jinja2 import Markup, escape

class Parser:
    def __init__(self, bootstrap_rule = None):
        self.rules = {}
        self.command_marker = ':'
        self.out_lines_separator = '<br/>\n'
        self.bootstrap_rule = bootstrap_rule

    def add_rule(self, rule):
        self.rules[rule.symbol] = rule

    def set_bootstrap_rule(self, rule):
        self.bootstrap_rule = rule

    def __call__(self, text):
        return self.parse(text)

    def parse(self, text):
        elements = []
        current_element = []
        contexts = [self.bootstrap_rule()]

        for line in text.replace('\r', '').split("\n"):
            rule = contexts.pop()
            
            if line and line[0] == self.command_marker:
                # probably a command, let's see if we can handle it
                command = line[1:].split(' ')
                if not(rule.handle(command[0], command[1:])):
                    if command[0] in self.rules.keys():
                        # yes we can !
                        contexts.append(rule)
                        rule = self.rules[command[0]](command[1:])
                else:
                    # let's just append that to the current element then
                    rule.process_line(line)

            else:
                # espace the potentially xss-threat bearing line
                # and add it to the current element
                rule.process_line(line)

            if rule.end():
                elements.append(rule.element())
                if len(contexts) == 0:
                    contexts.append(self.bootstrap_rule())
            else:
                contexts.append(rule)

        contexts.reverse()

        for rule in contexts:
            elements.append(rule.element())

        return Markup('\n'.join(elements))

class NullRule:
    def __init__(self, args = None):
        self.current = []
        self.ended = False

    def handle(self, symbol, args):
        # ParagraphsRule doesn't handle any symbol
        # so it must be the end of a paragraph
        self.ended = True
        return False

    def process_line(self, line):
        if line:
            self.current.append(escape(line))
        else:
            self.ended = True

    def element(self):
        if len(self.current) > 0:
            return "".join(self.current)
        else:
            return ''

    def end(self):
        return self.ended

class ParagraphsRule:
    def __init__(self, args = None):
        self.current = []
        self.ended = False

    def handle(self, symbol, args):
        # ParagraphsRule doesn't handle any symbol
        # so it must be the end of a paragraph
        self.ended = True
        return False

    def process_line(self, line):
        if line:
            self.current.append(escape(line))
        else:
            self.ended = True

    def element(self):
        if len(self.current) > 0:
            return "<p>%s</p>" % "<br/>\n".join(self.current)
        else:
            return ''

    def end(self):
        return self.ended

def image_rule(url_maker):
    class ImageRule:
        symbol = 'image'

        def __init__(self, args):
            self.url_maker = url_maker
            self.src = ' '.join(args)
            self.float = ''
            self.size = 'article-width'
            self.ended = False
    
        def handle(self, symbol, args):
            if symbol == 'size':
                size = ' '.join(args)
    
                if size == 'full width' or size == 'full':
                    self.size = 'full-width'
                elif size == 'half':
                    self.size = 'half-width'
                elif size == 'third':
                    self.size = 'third-width'
                elif size == 'article':
                    self.size = 'article-width'
    
            elif symbol == 'attach':
                if 'left' in args and 'right' in args:
                    pass
                elif 'left' in args:
                    self.float = 'float-left'
                elif 'right' in args:
                    self.float = 'float-right'
    
        def process_line(self, line):
            if not(line):
                self.ended = True
    
        def element(self):
            class_ = self.float + ' ' + self.size
            return '<img src="%s" class="%s"/>' % (url_maker(self.src), class_)
    
        def end(self):
            return self.ended

    return ImageRule
