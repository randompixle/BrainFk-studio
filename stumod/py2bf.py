import ast, os

def str_to_bf(s: str) -> str:
    code = []
    prev = 0
    for ch in s:
        diff = ord(ch) - prev
        code.append(('+' * diff) if diff >= 0 else ('-' * (-diff)))
        code.append('.')
        prev = ord(ch)
    return ''.join(code)

class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.out = []

    def visit_Module(self, node):
        for n in node.body:
            self.visit(n)

    def visit_Expr(self, node):
        # handle print("...") or print(123)
        if isinstance(node.value, ast.Call) and getattr(node.value.func, 'id', '') == 'print':
            if node.value.args:
                arg = node.value.args[0]
                # Python 3.8+ unified constants
                if isinstance(arg, ast.Constant):
                    if isinstance(arg.value, str):
                        self.out.append(str_to_bf(arg.value))
                    elif isinstance(arg.value, (int, float)):
                        self.out.append('+' * int(arg.value) + '.')
                    else:
                        self.out.append('[-]')
                else:
                    self.out.append('[-]')
        else:
            self.out.append('[-]')

def py_to_bf(src: str) -> str:
    try:
        tree = ast.parse(src)
    except Exception:
        # fallback: treat as raw string
        return str_to_bf(src)
    v = Visitor()
    v.visit(tree)
    return "\n".join(v.out)

def main(arg):
    if os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = arg
    print(py_to_bf(text))
