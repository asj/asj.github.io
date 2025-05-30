import os

IGNORED = {'.git', 'generate_index.py', 'index.html'}

def is_ignored(entry):
    return entry in IGNORED or entry.startswith('.git/')

def display_name(entry):
    if os.path.isdir(entry):
        return entry + '/'
    return os.path.splitext(entry)[0]  # strip extension

with open("index.html", "w") as f:
    f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Index</title></head><body><h1>Files</h1><ul>\n")
    for entry in sorted(os.listdir(".")):
        if is_ignored(entry):
            continue
        href = entry + "/" if os.path.isdir(entry) else entry
        label = display_name(entry)
        f.write(f"<li><a href=\"{href}\">{label}</a></li>\n")
    f.write("</ul></body></html>\n")
