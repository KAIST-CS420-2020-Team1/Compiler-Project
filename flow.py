class BasicBlock:
    def __init__(self, lines):
        self.lines = lines

class Line:
    def __init__(self, lineNum, ast):
        self.lineNum = lineNum
        self.ast = ast

