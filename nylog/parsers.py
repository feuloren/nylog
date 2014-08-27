# -*- coding: utf-8 -*-
#
# Parser to transform a post into brower-usable html
#

from .post_parser import *
from flask import url_for

def summary_parser():
    return Parser(NullRule)

def full_post_parser():
    parser = Parser(ParagraphsRule)
    parser.add_rule(image_rule(lambda src : url_for('serve_upload', filename = src)))
    return parser
