
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt

class RenderWindow(QWidget):
    def __init__(self, width=16, height=16):
        super().__init__()
        self.width_px, self.height_px = width, height
        self.setWindowTitle("BF Render Window")
        self.resize(width*20, height*20)
        self.buffer = [0]*(width*height)

    def update_buffer(self, buf, w=None, h=None):
        if w and h and w*h == len(buf):
            self.width_px, self.height_px = w, h
        self.buffer = list(buf)
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        cw = max(6, self.width() // self.width_px)
        ch = max(6, self.height() // self.height_px)
        for y in range(self.height_px):
            for x in range(self.width_px):
                v = self.buffer[y*self.width_px + x] & 0xFF
                p.setBrush(QColor(v, v, v))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRect(x*cw, y*ch, cw, ch)
        p.end()
