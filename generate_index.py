import os
import subprocess

IGNORED = {'.git', 'generate_index.py', 'index.html'}

def is_ignored(entry):
    return entry in IGNORED or entry.startswith('.git/')

def convert_markdown_to_html(md_file):
    html_file = os.path.splitext(md_file)[0] + '.html'
    subprocess.run(['python3', '-m', 'markdown', md_file], stdout=open(html_file, 'w'))
    return html_file

def display_name(entry):
    return os.path.splitext(entry)[0] if not os.path.isdir(entry) else entry + '/'

# Scan directory and collect entries
entries = sorted(os.listdir("."))

# Prepare index.html
with open("index.html", "w") as f:
    f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Index</title></head><body><h1>Files</h1><ul>\n")

    for entry in entries:
        if is_ignored(entry):
            continue

        # Handle markdown conversion and link to HTML version only
        if entry.endswith('.md'):
            html_file = convert_markdown_to_html(entry)
            label = display_name(entry)
            f.write(f"<li><a href=\"{html_file}\">{label}</a></li>\n")

        elif not entry.endswith('.html'):  # Skip raw .html files like index.html itself
            href = entry + "/" if os.path.isdir(entry) else entry
            label = display_name(entry)
            f.write(f"<li><a href=\"{href}\">{label}</a></li>\n")

    f.write("</ul></body></html>\n")

