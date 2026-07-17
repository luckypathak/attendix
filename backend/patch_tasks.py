with open("../brain/8c751c1f-8e20-4343-aed5-70fda84a3df4/task.md", "r") as f:
    t = f.read()
t = t.replace("- [ ] Step 2:", "- [x] Step 2:")
t = t.replace("- [ ] Step 4:", "- [x] Step 4:")
with open("../brain/8c751c1f-8e20-4343-aed5-70fda84a3df4/task.md", "w") as f:
    f.write(t)
