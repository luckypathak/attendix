import re

with open("../frontend/src/pages/Employees.jsx", "r") as f:
    content = f.read()

old_import = "import { UserPlus, Shield, Landmark, Calendar, Mail, User, Clock, Settings, Trash2, ArrowRightLeft } from 'lucide-react';"
new_import = "import { UserPlus, Shield, Landmark, Calendar, Mail, User, Clock, Settings, Trash2, ArrowRightLeft, CheckCircle } from 'lucide-react';"

content = content.replace(old_import, new_import)

with open("../frontend/src/pages/Employees.jsx", "w") as f:
    f.write(content)
