
# BFstudioX (PyQt6 v0.2 — Dark, Python→BF)

- VS Code–style dark theme
- Default **Python mode** editor (auto converts to BF on Run)
- Mode toggle (Python ↔ BF)
- Step debugger (Run, Pause, Step, Continue)
- Live Tape Visualizer
- BF-controlled Render Window (16×16 grayscale via tape)
- Modular backend (classic BF) + Python→BF converter

## Run
```bash
pip install -r requirements.txt
python3 -m ide_qt.main
```

## Render window protocol
- Framebuffer base: cell **30000**
- Size: **16×16** (cells 30000–30255, grayscale 0–255)
- Flag cell: **30256** — set non-zero to request redraw (auto-clears)
