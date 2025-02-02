import re
import tkinter as tk
from tkinter import messagebox

# Definição dos tokens para a linguagem C
TOKENS = [
    ('IF', r'\bif\b'),
    ('ELSE', r'\belse\b'),
    ('NUMBER', r'\d+'),
    ('PLUS', r'\+'),
    ('MINUS', r'-'),
    ('MULTIPLY', r'\*'),
    ('DIVIDE', r'/'),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),
    ('SEMICOLON', r';'),
    ('EQ', r'=='),
    ('NEQ', r'!='),
    ('LT', r'<'),
    ('GT', r'>'),
    ('LE', r'<='),
    ('GE', r'>='),
    ('ASSIGN', r'='),
    ('IDENTIFIER', r'[a-zA-Z_]\w*'),
    ('WHITESPACE', r'\s+'),
]

TOKEN_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKENS)

def lex(code):
    tokens = []
    for match in re.finditer(TOKEN_REGEX, code):
        token_name = match.lastgroup
        token_value = match.group(token_name)
        if token_name != 'WHITESPACE':
            tokens.append((token_name, token_value))
    return tokens

class ASTNode:
    pass

class BinOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Number(ASTNode):
    def __init__(self, value):
        self.value = value

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name

class Assignment(ASTNode):
    def __init__(self, identifier, value):
        self.identifier = identifier
        self.value = value

class IfStatement(ASTNode):
    def __init__(self, condition, then_branch, else_branch=None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

class Block(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.next_token()

    def next_token(self):
        self.current_token = self.tokens.pop(0) if self.tokens else None

    def parse(self):
        statements = []
        while self.current_token:
            statements.append(self.statement())
        return Block(statements)

    def statement(self):
        if self.current_token[0] == 'IF':
            return self.if_statement()
        elif self.current_token[0] == 'IDENTIFIER' and self.lookahead('ASSIGN'):
            return self.assignment()
        else:
            expr = self.expr()
            self.expect('SEMICOLON')
            return expr

    def if_statement(self):
        self.expect('IF')
        self.expect('LPAREN')
        condition = self.expr()
        self.expect('RPAREN')
        then_branch = self.block_or_statement()
        else_branch = None
        if self.current_token and self.current_token[0] == 'ELSE':
            self.next_token()
            else_branch = self.block_or_statement()
        return IfStatement(condition, then_branch, else_branch)

    def block_or_statement(self):
        if self.current_token and self.current_token[0] == 'LBRACE':
            self.expect('LBRACE')
            statements = []
            while self.current_token and self.current_token[0] != 'RBRACE':
                statements.append(self.statement())
            self.expect('RBRACE')
            return Block(statements)
        else:
            return self.statement()

    def assignment(self):
        identifier = Identifier(self.current_token[1])
        self.expect('IDENTIFIER')
        self.expect('ASSIGN')
        value = self.expr()
        self.expect('SEMICOLON')
        return Assignment(identifier, value)

    def expr(self):
        result = self.term()
        while self.current_token and self.current_token[0] in ('PLUS', 'MINUS', 'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE'):
            op = self.current_token[1]
            self.next_token()
            result = BinOp(result, op, self.term())
        return result

    def term(self):
        result = self.factor()
        while self.current_token and self.current_token[0] in ('MULTIPLY', 'DIVIDE'):
            op = self.current_token[1]
            self.next_token()
            result = BinOp(result, op, self.factor())
        return result

    def factor(self):
        if not self.current_token:
            raise SyntaxError("Erro de sintaxe: token inesperado no final da entrada")
        if self.current_token[0] == 'NUMBER':
            value = int(self.current_token[1])
            self.next_token()
            return Number(value)
        elif self.current_token[0] == 'IDENTIFIER':
            name = self.current_token[1]
            self.next_token()
            return Identifier(name)
        elif self.current_token[0] == 'LPAREN':
            self.next_token()
            result = self.expr()
            self.expect('RPAREN')
            return result
        else:
            raise SyntaxError(f"Erro de sintaxe: token inesperado '{self.current_token[1]}'")

    def expect(self, token_type):
        if self.current_token and self.current_token[0] == token_type:
            self.next_token()
        else:
            raise SyntaxError(f"Esperado '{token_type}' mas encontrado '{self.current_token[1] if self.current_token else 'EOF'}'")

    def lookahead(self, token_type):
        return len(self.tokens) > 0 and self.tokens[0][0] == token_type

def generate_code(node):
    if isinstance(node, Number):
        return str(node.value)
    elif isinstance(node, Identifier):
        return node.name
    elif isinstance(node, BinOp):
        left = generate_code(node.left)
        right = generate_code(node.right)
        return f"({left} {node.op} {right})"
    elif isinstance(node, Assignment):
        return f"{node.identifier.name} = {generate_code(node.value)};"
    elif isinstance(node, IfStatement):
        condition = generate_code(node.condition)
        then_branch = generate_code(node.then_branch)
        else_branch = generate_code(node.else_branch) if node.else_branch else ""
        return f"if ({condition}) {{\n  {then_branch}\n}}{f' else {{\n  {else_branch}\n}}' if else_branch else ''}"
    elif isinstance(node, Block):
        return '\n'.join(generate_code(stmt) for stmt in node.statements)
    else:
        raise ValueError("Nó inválido")

# Interface gráfica
class CompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador C")

        self.label = tk.Label(root, text="Digite a expressão C:")
        self.label.pack()

        self.entry = tk.Text(root, height=10, width=50)
        self.entry.pack()

        self.button = tk.Button(root, text="Compilar", command=self.compile_code)
        self.button.pack()

        self.result_label = tk.Label(root, text="Resultado:")
        self.result_label.pack()

        self.output = tk.Text(root, height=10, width=50)
        self.output.pack()

    def compile_code(self):
        try:
            code = self.entry.get("1.0", tk.END)
            tokens = lex(code)
            parser = Parser(tokens)
            ast = parser.parse()
            generated_code = generate_code(ast)
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, generated_code)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    gui = CompilerGUI(root)
    root.mainloop()
