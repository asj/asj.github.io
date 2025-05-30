import os

with open("index.html", "w") as f:
    f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Index</title></head><body><h1>Files</h1><ul>\n")
    for entry in sorted(os.listdir(".")):
        if entry == "index.html":
            continue
        href = entry + "/" if os.path.isdir(entry) else entry
        f.write(f"<li><a href=\"{href}\">{href}</a></li>\n")
    f.write("</ul></body></html>\n")
