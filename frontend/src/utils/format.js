/**
 * Utility helper to format YYYY-MM-DD or ISO strings to DD-MM-YYYY
 */
export const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  const parts = dateStr.split('-');
  if (parts.length === 3) {
    if (parts[0].length === 4) {
      return `${parts[2]}-${parts[1]}-${parts[0]}`;
    }
  }
  try {
    const d = new Date(dateStr);
    if (!isNaN(d.getTime())) {
      const dd = String(d.getDate()).padStart(2, '0');
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const yyyy = d.getFullYear();
      return `${dd}-${mm}-${yyyy}`;
    }
  } catch (e) {}
  return dateStr;
};

/**
 * Utility helper to format ISO timestamp strings to DD-MM-YYYY HH:MM
 */
export const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return 'N/A';
  try {
    const d = new Date(dateTimeStr);
    if (!isNaN(d.getTime())) {
      const dd = String(d.getDate()).padStart(2, '0');
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const yyyy = d.getFullYear();
      const hh = String(d.getHours()).padStart(2, '0');
      const min = String(d.getMinutes()).padStart(2, '0');
      return `${dd}-${mm}-${yyyy} ${hh}:${min}`;
    }
  } catch (e) {}
  return dateTimeStr;
};
