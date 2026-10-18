"""Build server.mcpb for japan-ec-apify-mcp."""
import fnmatch, json, os, zipfile

ROOT = "/home/atushi/.hermes/kanban/boards/kensho-ai-team/workspaces/t_562989ef"
OUTPUT = os.path.join(ROOT, "server.mcpb")

def load_ignore(root):
    path = os.path.join(root, ".mcpbignore")
    patterns = []
    if not os.path.exists(path):
        return patterns
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line.rstrip("/"))
    return patterns

def ignored(rel, is_dir, patterns):
    rel = rel.replace(os.sep, "/")
    for p in patterns:
        if rel == p or rel.startswith(p + "/"):
            return True
        if fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(os.path.basename(rel), p):
            return True
        if is_dir and fnmatch.fnmatch(rel + "/", p + "/"):
            return True
    return False

manifest = json.load(open(os.path.join(ROOT, "manifest.json"), encoding="utf-8"))
tools = manifest.get("tools") or []
bad = [t.get("name") for t in tools if not isinstance(t.get("inputSchema"), dict)]
if bad:
    raise SystemExit("Missing inputSchema: " + ", ".join(bad))

patterns = load_ignore(ROOT)
entries = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    rel_dir = os.path.relpath(dirpath, ROOT)
    rel_dir = "" if rel_dir == "." else rel_dir
    dirnames[:] = [d for d in dirnames if not ignored(os.path.join(rel_dir, d), True, patterns)]
    for fn in filenames:
        rel = os.path.join(rel_dir, fn) if rel_dir else fn
        if ignored(rel, False, patterns):
            continue
        entries.append(rel)
entries.sort()

if "manifest.json" not in entries:
    raise SystemExit("manifest.json missing from bundle")

with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for rel in entries:
        z.write(os.path.join(ROOT, rel), rel)

size = os.path.getsize(OUTPUT)
with zipfile.ZipFile(OUTPUT) as z:
    unpacked = sum(i.file_size for i in z.infolist())
print(f"Output: {OUTPUT}")
print(f"Files: {len(entries)} / Packaged: {round(size/1024, 1)} KB / Unpacked: {round(unpacked/1024/1024, 1)} MB")
print(f"Tools: {[t['name'] for t in tools]}")
for rel in entries:
    print(f"  {rel}")
