
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt

class TapeView(QWidget):
    def __init__(self, tape, pointer=0, parent=None):
        super().__init__(parent)
        self.tape = tape
        self.pointer = pointer
        self.cell_size = 16
        self.visible = 64
        self.setMinimumHeight(self.cell_size + 10)

    def update_state(self, tape, pointer):
        self.tape = tape
        self.pointer = pointer
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        w = self.cell_size
        start = max(0, self.pointer - self.visible//2)
        for i in range(self.visible):
            idx = start + i
            val = self.tape[idx] if idx < len(self.tape) else 0
            g = min(255, val)
            p.setBrush(QColor(30, 80 + g//2, 60))
            p.setPen(QPen(Qt.GlobalColor.yellow if idx == self.pointer else Qt.GlobalColor.black, 2 if idx == self.pointer else 1))
            p.drawRect(i*w+2, 2, w-4, self.cell_size-4)
        p.end()
