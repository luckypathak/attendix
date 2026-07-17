with open("../frontend/src/pages/Dashboard.jsx", "r") as f:
    content = f.read()

old_effect = """  useEffect(() => {
    fetchDashboardData();
  }, [isAdmin, selectedFirm]);"""

new_effect = """  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(() => {
      fetchDashboardData(true);
    }, 5000);
    return () => clearInterval(interval);
  }, [isAdmin, selectedFirm]);"""

content = content.replace(old_effect, new_effect)
content = content.replace("const fetchDashboardData = async () => {", "const fetchDashboardData = async (isPolling = false) => {")
content = content.replace("setLoading(true);", "if (!isPolling) setLoading(true);")

with open("../frontend/src/pages/Dashboard.jsx", "w") as f:
    f.write(content)

