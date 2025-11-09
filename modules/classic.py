
import sys, time

RENDER_WIDTH = 16
RENDER_HEIGHT = 16
RENDER_BASE = 30000
RENDER_SIZE = RENDER_WIDTH * RENDER_HEIGHT
RENDER_FLAG = RENDER_BASE + RENDER_SIZE

def run(code: str, hooks=None, cells=31000, step_delay=0.0, step_hook_rate=1):
    """Classic BF interpreter.
    hooks:
      - on_step(tape, ptr)            : called every instruction
      - on_output(text)               : buffered stdout
      - on_render(buf, w, h)          : render window buffer
      - tick()                        : may block; used for pause/step
    """
    hooks = hooks or {}
    on_step = hooks.get("on_step")
    on_output = hooks.get("on_output")
    on_render = hooks.get("on_render")
    tick = hooks.get("tick")

    code = "".join(c for c in code if c in "><+-,.[]")

    # bracket pairs
    stack = []
    br = {}
    for i, c in enumerate(code):
        if c == '[':
            stack.append(i)
        elif c == ']':
            if not stack:
                raise SyntaxError(f"Unmatched ']' at {i}")
            j = stack.pop()
            br[i], br[j] = j, i
    if stack:
        raise SyntaxError(f"Unmatched '[' at {stack[-1]}")

    tape = [0] * cells
    ptr = 0
    ip = 0
    out_buf = []

    def flush_output():
        if out_buf:
            s = bytes(out_buf).decode('utf-8', 'replace')
            if on_output: on_output(s)
            else: print(s, end="")
            out_buf.clear()

    while ip < len(code):
        if tick: tick()  # may pause/step
        c = code[ip]
        if c == '>':
            ptr += 1
            if ptr >= len(tape): tape.append(0)
        elif c == '<':
            ptr -= 1
            if ptr < 0: raise RuntimeError("Pointer moved left of tape start")
        elif c == '+':
            tape[ptr] = (tape[ptr] + 1) & 0xFF
        elif c == '-':
            tape[ptr] = (tape[ptr] - 1) & 0xFF
        elif c == '.':
            out_buf.append(tape[ptr])
            if len(out_buf) >= 64: flush_output()
        elif c == ',':
            try:
                ch = sys.stdin.read(1)
                tape[ptr] = ord(ch) & 0xFF if ch else 0
            except Exception:
                tape[ptr] = 0
        elif c == '[':
            if tape[ptr] == 0: ip = br[ip]
        elif c == ']':
            if tape[ptr] != 0: ip = br[ip]

        ip += 1

        # render
        if on_render and tape[RENDER_FLAG] != 0:
            buf = tape[RENDER_BASE:RENDER_BASE+RENDER_SIZE]
            on_render(list(buf), RENDER_WIDTH, RENDER_HEIGHT)
            tape[RENDER_FLAG] = 0

        if on_step: on_step(tape, ptr)
        if step_delay > 0.0: time.sleep(step_delay)

    flush_output()
    if on_step: on_step(tape, ptr)
