import re

with open("../frontend/src/pages/Employees.jsx", "r") as f:
    content = f.read()

# 1. Update the table rendering for Branch and Salary
table_pattern = r"(<TableCell>.*?)<Chip\s+label=\{emp\.firm_name \|\| 'Unassigned'\}(.*?)/>\s*</TableCell>.*?<TableCell>(.*?)</TableCell>\s*<TableCell>(.*?)</TableCell>\s*<TableCell>(.*?)</TableCell>\s*<TableCell>.*?₹\{emp\.base_salary.*?</TableCell>\s*<TableCell>.*?₹\{emp\.hourly_rate.*?</TableCell>"

def table_replace(match):
    # This is a bit complex to regex correctly because of the nested tags, let's just find the TableRow map.
    pass

# We will manually replace the inner part of the map
# From `<TableRow key={emp.id} hover sx={{ '& > *': { borderBottom: '1px solid rgba(255,255,255,0.05)' } }}>`
# to `</TableRow>`

row_pattern = r"(<TableRow key=\{emp\.id\}.*?>)(.*?)(</TableRow>)"
# wait, better to just replace the specific cells.

# Firm/Branch column:
old_firm_cell = """                        <TableCell>
                          <Chip 
                            label={emp.firm_name || 'Unassigned'} 
                            size="small" 
                            sx={{ 
                              bgcolor: 'rgba(124, 77, 255, 0.1)', 
                              color: '#b388ff',
                              border: '1px solid rgba(124, 77, 255, 0.3)'
                            }} 
                          />
                        </TableCell>"""

new_firm_cell = """                        <TableCell>
                          {emp.firm_allocations && emp.firm_allocations.length > 0 ? (
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              {emp.firm_allocations.map(alloc => (
                                <Chip 
                                  key={alloc.id}
                                  label={alloc.firm_name || 'Unassigned'} 
                                  size="small" 
                                  sx={{ 
                                    bgcolor: 'rgba(124, 77, 255, 0.1)', 
                                    color: '#b388ff',
                                    border: '1px solid rgba(124, 77, 255, 0.3)',
                                    width: 'fit-content'
                                  }} 
                                />
                              ))}
                            </Box>
                          ) : (
                            <Chip 
                              label={emp.firm_name || 'Unassigned'} 
                              size="small" 
                              sx={{ 
                                bgcolor: 'rgba(124, 77, 255, 0.1)', 
                                color: '#b388ff',
                                border: '1px solid rgba(124, 77, 255, 0.3)'
                              }} 
                            />
                          )}
                        </TableCell>"""

content = content.replace(old_firm_cell, new_firm_cell)

# Salary Column:
old_salary_cell = """                        <TableCell sx={{ fontWeight: 600 }}>₹{emp.base_salary}</TableCell>"""
new_salary_cell = """                        <TableCell sx={{ fontWeight: 600 }}>
                          {emp.firm_allocations && emp.firm_allocations.length > 0 ? (
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              {emp.firm_allocations.map(alloc => (
                                <Typography key={alloc.id} variant="body2" sx={{ fontWeight: 600 }}>
                                  ₹{alloc.base_salary}
                                </Typography>
                              ))}
                            </Box>
                          ) : (
                            `₹${emp.base_salary}`
                          )}
                        </TableCell>"""

content = content.replace(old_salary_cell, new_salary_cell)

# PF Deduction Column:
old_pf_cell = """                        <TableCell>
                          {emp.pf_type === 'disabled' || !emp.pf_type ? (
                            <Chip size="small" label="No PF" sx={{ bgcolor: 'rgba(255,255,255,0.05)' }} />
                          ) : (
                            <Chip size="small" label={emp.pf_type === 'percentage' ? `${emp.pf_value}%` : `₹${emp.pf_value}`} color="primary" variant="outlined" />
                          )}
                        </TableCell>"""
new_pf_cell = """                        <TableCell>
                          {emp.firm_allocations && emp.firm_allocations.length > 0 ? (
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              {emp.firm_allocations.map(alloc => (
                                <Box key={alloc.id}>
                                  {alloc.pf_type === 'disabled' || !alloc.pf_type ? (
                                    <Chip size="small" label="No PF" sx={{ bgcolor: 'rgba(255,255,255,0.05)', width: 'fit-content' }} />
                                  ) : (
                                    <Chip size="small" label={alloc.pf_type === 'percentage' ? `${alloc.pf_value}%` : `₹${alloc.pf_value}`} color="primary" variant="outlined" sx={{ width: 'fit-content' }} />
                                  )}
                                </Box>
                              ))}
                            </Box>
                          ) : (
                            emp.pf_type === 'disabled' || !emp.pf_type ? (
                              <Chip size="small" label="No PF" sx={{ bgcolor: 'rgba(255,255,255,0.05)' }} />
                            ) : (
                              <Chip size="small" label={emp.pf_type === 'percentage' ? `${emp.pf_value}%` : `₹${emp.pf_value}`} color="primary" variant="outlined" />
                            )
                          )}
                        </TableCell>"""

content = content.replace(old_pf_cell, new_pf_cell)


# Edit Modal - Add to Branch 
# We replace the select logic to filter out assigned branches
old_add_branch = """                <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', mt: 2 }}>
                  <TextField
                    select
                    label="Add to Branch"
                    size="small"
                    value=""
                    onChange={(e) => {
                      const fId = parseInt(e.target.value);
                      if (!allocations.find(a => a.firm === fId)) {
                        setAllocations([...allocations, { firm: fId, base_salary: 0, pf_type: 'disabled', pf_value: 0 }]);
                      }
                    }}
                    sx={{ minWidth: 200 }}
                  >
                    <MenuItem value="" disabled>Select Branch...</MenuItem>
                    {firms.map(f => (
                      <MenuItem key={f.id} value={f.id}>{f.name}</MenuItem>
                    ))}
                  </TextField>
                  <Typography variant="caption" color="text.secondary">
                    Add branch splits if employee splits shifts or duties.
                  </Typography>
                </Box>"""

new_add_branch = """                {(() => {
                  const unassignedFirms = firms.filter(f => !allocations.some(a => a.firm === f.id));
                  if (unassignedFirms.length === 0) {
                    return (
                      <Typography variant="body2" color="success.main" sx={{ mt: 2, fontWeight: 600 }}>
                        <CheckCircle size={14} style={{ marginRight: 4, verticalAlign: 'text-bottom' }} />
                        Employee is already assigned to all available branches.
                      </Typography>
                    );
                  }
                  return (
                    <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', mt: 2 }}>
                      <TextField
                        select
                        label="Add to Branch"
                        size="small"
                        value=""
                        onChange={(e) => {
                          const fId = parseInt(e.target.value);
                          if (!allocations.find(a => a.firm === fId)) {
                            setAllocations([...allocations, { firm: fId, base_salary: 0, pf_type: 'disabled', pf_value: 0 }]);
                          }
                        }}
                        sx={{ minWidth: 200 }}
                      >
                        <MenuItem value="" disabled>Select Branch...</MenuItem>
                        {unassignedFirms.map(f => (
                          <MenuItem key={f.id} value={f.id}>{f.name}</MenuItem>
                        ))}
                      </TextField>
                      <Typography variant="caption" color="text.secondary">
                        Add branch splits if employee splits shifts or duties.
                      </Typography>
                    </Box>
                  );
                })()}"""

content = content.replace(old_add_branch, new_add_branch)

# Also fix the shift parsing which was expecting string time:
# In handleEditClick:
#    if (emp.shift_start_time && emp.shift_end_time) {
#      // Convert "11:00:00" to "11:00" if necessary for the input type="time" wait, the TextField uses `type="time"`? No, it's a string. Wait, if it's a TimeField from django it comes as "11:00:00"

old_shift_handle = """    if (emp.shift_start_time && emp.shift_end_time) {
      setShiftStartTime(emp.shift_start_time);
      setShiftEndTime(emp.shift_end_time);
      setShiftId('CUSTOM');
    } else {"""
new_shift_handle = """    if (emp.shift_start_time && emp.shift_end_time) {
      // Format time from "11:00:00" to "11:00"
      setShiftStartTime(emp.shift_start_time.substring(0, 5));
      setShiftEndTime(emp.shift_end_time.substring(0, 5));
      setShiftId('CUSTOM');
    } else {"""

content = content.replace(old_shift_handle, new_shift_handle)

with open("../frontend/src/pages/Employees.jsx", "w") as f:
    f.write(content)
