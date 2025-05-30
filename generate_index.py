import os
import subprocess

IGNORED = {'.git', 'generate_index.py', 'index.html'}

def is_ignored(entry):
    return entry in IGNORED or entry.startswith('.git/')

def convert_markdown_to_html(md_file):
    html_file = os.path.splitext(md_file)[0] + '.html'
    with open(html_file, 'w') as out:
        subprocess.run(['pandoc', md_file, '-f', 'markdown', '-t', 'html'], stdout=out)
    return html_file

def display_name(entry):
    return os.path.splitext(entry)[0] if not os.path.isdir(entry) else entry + '/'

entries = sorted(os.listdir("."))

with open("index.html", "w") as f:
    f.write("""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Index</title>
  <style>
    body {
      font-family: "Cambria (Body)", Cambria, serif;
      max-width: 700px;
      margin: 3em auto;
      padding: 0 1em;
      background: #fefefe;
      color: #222;
    }
    h1 {
      font-size: 1.8em;
      margin-bottom: 0.5em;
    }
    ul {
      list-style-type: none;
      padding-left: 0;
    }
    li {
      margin: 0.4em 0;
    }
    a {
      text-decoration: none;
      color: #0366d6;
    }
    a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <h1>Files</h1>
  <ul>
""")

    for entry in entries:
        if is_ignored(entry):
            continue

        if entry.endswith('.md'):
            html_file = convert_markdown_to_html(entry)
            label = display_name(entry)
            f.write(f'    <li><a href="{html_file}">{label}</a></li>\n')
        elif not entry.endswith('.html'):
            href = entry + "/" if os.path.isdir(entry) else entry
            label = display_name(entry)
            f.write(f'    <li><a href="{href}">{label}</a></li>\n')

    f.write("""  </ul>
</body>
</html>
""")

