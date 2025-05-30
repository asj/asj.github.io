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

entries = sorted(os.listdir("."))

with open("index.html", "w") as f:
    f.write("""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Index</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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

