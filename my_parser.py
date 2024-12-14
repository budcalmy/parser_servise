import re
import cppyy
import uuid
import json
from typing import Any, Dict, List

class CppInterpreter:
    def __init__(self, code: str, return_type: str):
        self.code = code
        self.return_type = return_type
        self.tokens = []
        self.actions = []
        self.errors = []
        self.store = {}
        self.output = []
        self.token_index = 0

    def tokenize(self):
        token_patterns = [
            ("TYPE", r"\\b(int|double|string|bool)\\b"),
            ("IDENTIFIER", r"\\b[a-zA-Z_][a-zA-Z0-9_]*\\b"),
            ("ASSIGN", r"="),
            ("NUMBER", r"\\b\\d+(\\.\\d+)?\\b"),
            ("STRING", r'\".*?\"'),
            ("BOOL", r"\\b(true|false)\\b"),
            ("OPERATOR", r"[+\-*/]"),
            ("LPAREN", r"\\("),
            ("RPAREN", r"\\)"),
            ("LCURLY", r"\\{"),
            ("RCURLY", r"\\}"),
            ("SEMICOLON", r";"),
            ("COUT", r"cout"),
            ("ENDL", r"endl"),
            ("IF", r"if"),
            ("ELSE", r"else"),
            ("WHILE", r"while"),
        ]
        token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_patterns)
        for match in re.finditer(token_regex, self.code):
            kind = match.lastgroup
            value = match.group()
            self.tokens.append((kind, value))
        self.actions.append("Tokenized code.")

    def peek_token(self):
        if self.token_index < len(self.tokens):
            return self.tokens[self.token_index]
        return None

    def consume_token(self):
        token = self.peek_token()
        if token:
            self.token_index += 1
        return token

    def parse_expression(self):
        expression = []
        while (token := self.peek_token()) and token[0] not in {"SEMICOLON", "RPAREN"}:
            if token[0] not in {"COUT", "ENDL"}:  # Skip cout and endl in expressions
                expression.append(token[1])
            self.consume_token()
        # Replace C++ boolean literals with Python boolean literals
        expression = ["True" if token == "true" else "False" if token == "false" else token for token in expression]
        return ''.join(expression)

    def execute_expression(self, expression: str) -> Any:
        try:
            result = eval(expression, {}, self.store)
            return result
        except Exception as e:
            self.errors.append(f"Error evaluating expression '{expression}': {e}")
            raise
    def __run(self):
        
        if not re.search(r'\breturn\b', self.code):
            return json.dumps({"status": "error", "message": f"The provided code does not contain a 'return' statement."})
        
        if self.return_type not in ["string", "int", "double", "bool"]:
            return json.dumps({"status": "error", "message": f"Invalid return_type {self.return_type}"})
        
        try:
            unique_name = f"foo_{uuid.uuid4().hex[:8]}"
            cpp_code = f'''
                #include <string>
                using namespace std;
                namespace {unique_name} {{
                    template <typename T>
                    T foo() {{
                        {self.code}
                    }}
                }}
            '''
            cppyy.cppdef(cpp_code)
            result = str(getattr(cppyy.gbl, unique_name).foo[self.return_type]())
            return json.dumps({"status": "success", "result": result})
        
        except TypeError as e:
            return json.dumps({"status": "error", "message": str(e)})
    
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Unexpected error: {str(e)}"})

        

    def parse_statement(self):
        token = self.consume_token()

        if token[0] == "TYPE":
            var_type = token[1]
            identifier = self.consume_token()
            if identifier[0] != "IDENTIFIER":
                self.errors.append("Expected identifier after type declaration.")
                return

            var_name = identifier[1]
            value = None

            if self.peek_token() and self.peek_token()[0] == "ASSIGN":
                self.consume_token()  # consume '='
                value_expr = self.parse_expression()
                value = self.execute_expression(value_expr)

            if var_type == "int":
                self.store[var_name] = int(value) if value is not None else 0
            elif var_type == "double":
                self.store[var_name] = float(value) if value is not None else 0.0
            elif var_type == "string":
                self.store[var_name] = str(value) if value is not None else ""
            elif var_type == "bool":
                self.store[var_name] = bool(value) if value is not None else False

            self.actions.append(f"Defined variable '{var_name}' with value '{self.store[var_name]}'.")

        elif token[0] == "IDENTIFIER":
            var_name = token[1]
            if self.peek_token() and self.peek_token()[0] == "ASSIGN":
                self.consume_token()  # consume '='
                value_expr = self.parse_expression()
                value = self.execute_expression(value_expr)
                self.store[var_name] = value
                self.actions.append(f"Assigned '{var_name}' = '{value}'.")

        elif token[0] == "COUT":
            output = []
            while (token := self.consume_token()) and token[0] != "SEMICOLON":
                if token[0] == "IDENTIFIER" and token[1] in self.store:
                    output.append(str(self.store[token[1]]))
                elif token[0] == "STRING":
                    output.append(token[1].strip('"'))
                elif token[0] == "ENDL":
                    output.append("\n")
            self.output.append(''.join(output))
            self.actions.append(f"Output: {''.join(output)}")

        elif token[0] == "IF":
            condition_expr = self.parse_expression()
            condition = self.execute_expression(condition_expr)
            self.actions.append(f"Evaluated IF condition: {condition}.")

            if condition:
                if self.peek_token() and self.peek_token()[0] == "LCURLY":
                    self.consume_token()  # consume LCURLY
                    while (token := self.peek_token()) and token[0] != "RCURLY":
                        self.parse_statement()
                    self.consume_token()  # consume RCURLY
            else:
                if self.peek_token() and self.peek_token()[0] == "LCURLY":
                    while (token := self.peek_token()) and token[0] != "RCURLY":
                        self.consume_token()  # Skip statements
                    self.consume_token()  # consume RCURLY
                if self.peek_token() and self.peek_token()[0] == "ELSE":
                    self.consume_token()  # consume ELSE
                    if self.peek_token() and self.peek_token()[0] == "LCURLY":
                        self.consume_token()  # consume LCURLY
                        while (token := self.peek_token()) and token[0] != "RCURLY":
                            self.parse_statement()
                        self.consume_token()  # consume RCURLY

        elif token[0] == "WHILE":
            condition_expr = self.parse_expression()
            while self.execute_expression(condition_expr):
                self.actions.append(f"Executing WHILE loop with condition: {condition_expr}.")
                if self.peek_token() and self.peek_token()[0] == "LCURLY":
                    self.consume_token()  # consume LCURLY
                    while (token := self.peek_token()) and token[0] != "RCURLY":
                        self.parse_statement()
                    self.consume_token()  # consume RCURLY
                else:
                    break

        else:
            self.errors.append(f"Unexpected token: {token}")

    def execute(self):
        while self.token_index < len(self.tokens):
            self.parse_statement()

    def run(self):
        if (True):
            return self.__run() 
        else:
            self.tokenize()
            if not self.errors:
                self.execute()

