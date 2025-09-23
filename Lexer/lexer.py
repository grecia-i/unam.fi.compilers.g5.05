from rply import LexerGenerator

class Lexer():
    def __init__(self) -> None:
        self.lexer = LexerGenerator()

    def _add_tokens(self):
        #self.lexer.add('NOMBRE_DEL_TOKEN', r'EXPRESION_REGULAR_PARA_IDENTIFICARLO')
        #self.lexer.add()
        self.lexer.add('PROGRAMA', r'programa')

        self.lexer.add('TIPO',r'entero|real|cadena|bool')

        self.lexer.add('LLAV_ABRE', r'\{')
        self.lexer.add('LLAV_CIERRA', r'\}')
        self.lexer.add('PAR_ABRE', r'\(')
        self.lexer.add('PAR_ABRE', r'\)')

        self.lexer.add('OP_ARIT', r'[+\-*/]')
        self.lexer.add('OP_COMP', r'==|<=|>=|<|>')
        self.lexer.add('OP_ASIGN', r'=')
        self.lexer.add('OP_BOOL', r'o|y|no')

        self.lexer.add('MIENTRAS', r'mientras')
        self.lexer.add('SI', r'si')
        self.lexer.add('ENTONCES', r'entonces')
        self.lexer.add('SINO', r'sino')
        self.lexer.add('PARA', r'para')
        self.lexer.add('DESDE', r'desde')
        self.lexer.add('HASTA', r'hasta')

        self.lexer.add('LIT_CADENA', r'"(\\.|[^"\\])*"') #dudoso
        self.lexer.add('LIT_ENTERO', r'-?\d+')
        self.lexer.add('LIT_REAL', r'-?\d+\.\d+') #dudoso punto
        self.lexer.add('LIT_BOOL', r'Verdadero|Falso')
        
        self.lexer.add('OP_LECTURA', r'lee')
        self.lexer.add('OP_ESCRITURA', r'escribe')

        self.lexer.add('ID', r'[A-Za-z][A-Za-z0-9_]*')

        self.lexer.add('PUNTOYCOMA', r'\;')
        self.lexer.add('COMENTARIO',r'#.*')
        


        self.lexer.ignore('\s+')
        #self.lexer.ignore(r'#.*')
        
    def get_lexer(self):
        self._add_tokens()
        return self.lexer.build()