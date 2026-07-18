import re

with open("../frontend/src/pages/Employees.jsx", "r") as f:
    content = f.read()

helper = """
  const convertTo24Hour = (timeStr) => {
    if (!timeStr) return '';
    if (timeStr.match(/^\d{2}:\d{2}$/)) return timeStr; // already 24h
    const match = timeStr.match(/(\d+):(\d+)\s?(AM|PM)/i);
    if (!match) return timeStr;
    let [_, h, m, period] = match;
    h = parseInt(h);
    if (period.toUpperCase() === 'PM' && h < 12) h += 12;
    if (period.toUpperCase() === 'AM' && h === 12) h = 0;
    return `${h.toString().padStart(2, '0')}:${m}`;
  };

  const handleEditClick = (emp) => {"""

content = content.replace("  const handleEditClick = (emp) => {", helper)

old_time = """      // Format time from "11:00:00" to "11:00"
      setShiftStartTime(emp.shift_start_time.substring(0, 5));
      setShiftEndTime(emp.shift_end_time.substring(0, 5));"""

new_time = """      setShiftStartTime(convertTo24Hour(emp.shift_start_time));
      setShiftEndTime(convertTo24Hour(emp.shift_end_time));"""

content = content.replace(old_time, new_time)

with open("../frontend/src/pages/Employees.jsx", "w") as f:
    f.write(content)
