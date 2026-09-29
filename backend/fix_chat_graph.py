import sys

filepath = "app/ai/graph/chat_graph.py"
with open(filepath, encoding="utf-8") as f:
    lines = f.readlines()

# Remove any line that is just '".join(lines)' (stray artifact)
cleaned = []
for line in lines:
    stripped = line.strip()
    if stripped == '".join(lines)':
        print(f"Removed stray line: {repr(line)}")
        continue
    cleaned.append(line)

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(cleaned)

print(f"Done. Lines: {len(cleaned)}")
