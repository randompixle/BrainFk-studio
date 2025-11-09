
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QTextEdit, QLabel,
    QFileDialog, QSplitter, QToolBar, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont
import sys, os, io, threading

from Studio import MODULE_DIR, STUMOD_DIR, load_plugin
from .tapeview import TapeView
from .renderwindow import RenderWindow
from .highlighter import PyHighlighter, BFHighlighter, C_BG, C_TEXT

class Runner(QThread):
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    done_signal = pyqtSignal()
    update_tape = pyqtSignal(list, int)
    update_render = pyqtSignal(list, int, int)

    def __init__(self, dialect, code, pause_event, step_once_event):
        super().__init__()
        self.dialect = dialect
        self.code = code
        self.pause_event = pause_event
        self.step_once_event = step_once_event

    def run(self):
        try:
            mod = load_plugin(MODULE_DIR, self.dialect)

            def on_output(s): self.output_signal.emit(s)
            def on_step(tape, ptr): self.update_tape.emit(tape[:4096], ptr)
            def on_render(buf, w, h): self.update_render.emit(buf, w, h)

            def tick():
                # if paused, wait until unpaused or step_once used
                if self.pause_event.is_set():
                    # wait for step once or unpause
                    while self.pause_event.is_set():
                        if self.step_once_event.is_set():
                            # consume single step
                            self.step_once_event.clear()
                            break
                        self.msleep(1)

            hooks = {'on_output': on_output, 'on_step': on_step, 'on_render': on_render, 'tick': tick}
            mod.run(self.code, hooks=hooks)
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.done_signal.emit()

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BFstudioX — PyQt IDE (v0.2, Dark)")
        self.resize(1200, 780)

        # Modes: Python (default) or BF
        self.mode = "Python"

        mono = QFont("DejaVu Sans Mono")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(12)

        # Editor & Output
        self.editor = QPlainTextEdit()
        self.editor.setFont(mono)
        self.output = QTextEdit(); self.output.setReadOnly(True); self.output.setFont(mono)

        # Apply dark styles
        self.setStyleSheet(f"""
            QMainWindow {{ background: {C_BG}; color: {C_TEXT}; }}
            QToolBar {{ background: #252526; border:0; padding:6px; }}
            QPlainTextEdit {{ background: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; }}
            QTextEdit {{ background: #1e1e1e; color: #b5cea8; border: 1px solid #3c3c3c; }}
            QLabel {{ color: #cccccc; }}
            QPushButton {{ background: #0e639c; color: white; border: none; padding: 6px 10px; }}
            QPushButton:hover {{ background: #1177bb; }}
            QComboBox {{ background: #252526; color: #d4d4d4; border: 1px solid #3c3c3c; }}
        """)

        # Highlighters
        self.py_highlighter = PyHighlighter(self.editor.document())
        self.bf_highlighter = None  # created when toggled

        # Tape & Render
        self.tape = [0]*4096
        self.tape_view = TapeView(self.tape)
        self.render_win = RenderWindow(16,16)

        # Toolbar
        tb = QToolBar("Main"); self.addToolBar(tb)

        self.combo_dialect = QComboBox()
        dialects = [f[:-3] for f in os.listdir(MODULE_DIR) if f.endswith(".py") and not f.startswith("__")]
        for d in dialects: self.combo_dialect.addItem(d)

        # Mode selector
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Python", "BF"])
        self.combo_mode.currentTextChanged.connect(self.on_mode_change)

        act_run = QAction("Run", self); act_run.setShortcut("F5")
        act_pause = QAction("Pause", self); act_step = QAction("Step", self); act_cont = QAction("Continue", self)
        act_open = QAction("Open", self); act_save = QAction("Save", self)
        act_render = QAction("Render Window", self)

        tb.addAction(act_run); tb.addAction(act_pause); tb.addAction(act_step); tb.addAction(act_cont)
        tb.addSeparator()
        tb.addWidget(QLabel("Mode:")); tb.addWidget(self.combo_mode)
        tb.addSeparator()
        tb.addWidget(QLabel("Dialect:")); tb.addWidget(self.combo_dialect)
        tb.addSeparator()
        tb.addAction(act_open); tb.addAction(act_save); tb.addAction(act_render)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        top = QWidget(); top_l = QVBoxLayout(top)
        top_l.addWidget(self.editor); top_l.addWidget(self.tape_view)
        splitter.addWidget(top); splitter.addWidget(self.output)
        splitter.setStretchFactor(0, 3); splitter.setStretchFactor(1, 1)
        central = QWidget(); lay = QVBoxLayout(central); lay.addWidget(splitter); self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

        # Signals
        act_run.triggered.connect(self.run_code)
        act_pause.triggered.connect(self.pause_code)
        act_step.triggered.connect(self.step_code)
        act_cont.triggered.connect(self.continue_code)
        act_open.triggered.connect(self.open_file)
        act_save.triggered.connect(self.save_file)
        act_render.triggered.connect(lambda: self.render_win.show())

        self.pause_event = threading.Event()
        self.step_once_event = threading.Event()
        self.runner = None

        # Default editor text (Python mode)
        self.editor.setPlainText('print("Hello from Python -> BF!")\n')

    def on_mode_change(self, txt):
        self.mode = txt
        if txt == "Python":
            # switch to Python highlighter
            if self.bf_highlighter:
                self.bf_highlighter.setDocument(None)
                self.bf_highlighter = None
            self.py_highlighter = PyHighlighter(self.editor.document())
        else:
            # BF mode
            if self.py_highlighter:
                self.py_highlighter.setDocument(None)
                self.py_highlighter = None
            from .highlighter import BFHighlighter
            self.bf_highlighter = BFHighlighter(self.editor.document())

    def append_output(self, text, error=False):
        color = "#d7ba7d" if not error else "#f44747"
        self.output.append(f"<span style='color:{color}'>{text}</span>")

    def run_code(self):
        # Resolve source: Python->BF or raw BF
        src = self.editor.toPlainText()
        bf_code = src
        if self.mode == "Python":
            try:
                conv = load_plugin(STUMOD_DIR, "py2bf")
                bf_code = conv.py_to_bf(src)
            except Exception as e:
                QMessageBox.critical(self, "Conversion error", str(e))
                return

        self.output.clear()
        self.pause_event.clear()
        self.step_once_event.clear()
        dialect = self.combo_dialect.currentText()

        self.runner = Runner(dialect, bf_code, self.pause_event, self.step_once_event)
        self.runner.output_signal.connect(lambda t: self.append_output(t))
        self.runner.error_signal.connect(lambda e: self.append_output(e, True))
        self.runner.update_tape.connect(self.on_tape_update)
        self.runner.update_render.connect(self.on_render_update)
        self.runner.start()
        self.statusBar().showMessage("Running…", 2000)

    def pause_code(self):
        if self.runner:
            self.pause_event.set()
            self.statusBar().showMessage("Paused", 1500)

    def step_code(self):
        if self.runner:
            # ensure paused, then release one step
            self.pause_event.set()
            self.step_once_event.set()
            self.statusBar().showMessage("Stepped", 800)

    def continue_code(self):
        if self.runner:
            self.pause_event.clear()
            self.statusBar().showMessage("Continuing…", 1500)

    def on_tape_update(self, tape, ptr):
        n = min(len(tape), len(self.tape))
        self.tape[:n] = tape[:n]
        self.tape_view.update_state(self.tape, ptr)

    def on_render_update(self, buf, w, h):
        self.render_win.update_buffer(buf, w, h)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open", "", "Python (*.py);;Brainfuck (*.bf *.txt);;All files (*)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())
            # auto-mode switch
            if path.endswith(".py"):
                self.combo_mode.setCurrentText("Python")
            else:
                self.combo_mode.setCurrentText("BF")

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save", "", "Python (*.py);;Brainfuck (*.bf)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())

def main():
    app = QApplication(sys.argv)
    win = Main()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
