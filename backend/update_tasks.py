with open("../brain/8c751c1f-8e20-4343-aed5-70fda84a3df4/task.md", "r") as f:
    t = f.read()
for step in ["Step 2", "Step 3", "Step 4", "Step 5"]:
    t = t.replace(f"- [ ] {step}", f"- [x] {step}")
with open("../brain/8c751c1f-8e20-4343-aed5-70fda84a3df4/task.md", "w") as f:
    f.write(t)
