import importlib, os, sys

# === PATH SETUP ===
HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.join(HERE, "modules")
STUMOD_DIR = os.path.join(HERE, "stumod")

# === PLUGIN SYSTEM ===
def list_plugins(path):
    """Return all Python modules (without __init__) inside a folder."""
    return [f[:-3] for f in os.listdir(path) if f.endswith(".py") and not f.startswith("__")]

def load_plugin(path, name):
    """Import a plugin dynamically from a folder path."""
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module(name)

# === CLI FRONTEND ===
def cli():
    print("🧠  BFstudioX Modular CLI (PyQt Edition)")
    print(f"→ modules: {', '.join(list_plugins(MODULE_DIR))}")
    print(f"→ tools  : {', '.join(list_plugins(STUMOD_DIR))}")
    print("Type 'run <dialect> <file>' or 'conv <tool> [args]' or 'quit'")

    while True:
        try:
            cmd = input("studio> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if cmd in ("exit", "quit"):
            break

        if cmd.startswith("run "):
            parts = cmd.split(maxsplit=2)
            if len(parts) < 3:
                print("usage: run <dialect> <file>")
                continue
            _, dialect, file = parts
            try:
                module = load_plugin(MODULE_DIR, dialect)
                with open(file, "r", encoding="utf-8") as f:
                    code = f.read()
                print(f"→ Running '{file}' with dialect '{dialect}'...")
                module.run(code, hooks={})
            except Exception as e:
                print("⚠️ Error:", e)

        elif cmd.startswith("conv "):
            parts = cmd.split(maxsplit=2)
            if len(parts) < 2:
                print("usage: conv <tool> [args]")
                continue
            tool = parts[1]
            rest = parts[2] if len(parts) > 2 else ""
            try:
                toolmod = load_plugin(STUMOD_DIR, tool)
                print(f"→ Converting using '{tool}'...")
                toolmod.main(rest)
            except Exception as e:
                print("⚠️ Error:", e)

        else:
            print("usage: run <dialect> <file> | conv <tool> [args] | quit")


# === ENTRYPOINTS ===
if __name__ == "__main__":
    # if called directly: CLI mode
    cli()
