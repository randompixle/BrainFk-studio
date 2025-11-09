
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

# VS Code-ish colors
C_BG = "#1e1e1e"
C_TEXT = "#d4d4d4"
C_COMMENT = "#6a9955"
C_STRING = "#ce9178"
C_NUMBER = "#b5cea8"
C_KEYWORD = "#4ec9b0"
C_BFOP = "#8be9fd"
C_MISC = "#c586c0"

class PyHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.rules = []

        def fmt(color, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold: f.setFontWeight(QFont.Weight.Bold)
            if italic: f.setFontItalic(True)
            return f

        keywords = r"\b(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b"
        self.rules.append((QRegularExpression(keywords), fmt(C_KEYWORD, True)))
        self.rules.append((QRegularExpression(r'#[^\n]*'), fmt(C_COMMENT, italic=True)))
        self.rules.append((QRegularExpression(r'".*?"'), fmt(C_STRING)))
        self.rules.append((QRegularExpression(r"'.*?'") , fmt(C_STRING)))
        self.rules.append((QRegularExpression(r'\b\d+(\.\d+)?\b'), fmt(C_NUMBER)))
        self.rules.append((QRegularExpression(r'\b(print)\b'), fmt(C_MISC, True)))

    def highlightBlock(self, text):
        for rx, form in self.rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), form)

class BFHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.f_op = QTextCharFormat()
        self.f_op.setForeground(QColor(C_BFOP))
        self.f_op.setFontWeight(QFont.Weight.Bold)

        self.f_comment = QTextCharFormat()
        self.f_comment.setForeground(QColor(C_COMMENT))

    def highlightBlock(self, text):
        # highlight only ><+-,.[]
        i = 0
        while i < len(text):
            if text[i] in '><+-,.[]':
                self.setFormat(i, 1, self.f_op)
            else:
                self.setFormat(i, 1, self.f_comment)
            i += 1
