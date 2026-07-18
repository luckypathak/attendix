import re

with open("../frontend/src/components/EditAttendanceModal.jsx", "r") as f:
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

  useEffect(() => {"""

content = content.replace("  useEffect(() => {", helper)

old_effect = """      setCheckInTime(session.check_in_time || '');
      setCheckOutTime(session.check_out_time || '');"""

new_effect = """      setCheckInTime(convertTo24Hour(session.check_in_time) || '');
      setCheckOutTime(convertTo24Hour(session.check_out_time) || '');"""

content = content.replace(old_effect, new_effect)

with open("../frontend/src/components/EditAttendanceModal.jsx", "w") as f:
    f.write(content)
