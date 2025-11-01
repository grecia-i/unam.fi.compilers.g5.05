from rply import ParserGenerator
# from parser.src.modules.tree import *
from nltk.tree import *
from collections import defaultdict

class Parser:
    def __init__(self):
        self.tokens = []
        self.token_summary = defaultdict(int)
