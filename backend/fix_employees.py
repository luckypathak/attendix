import re

with open("../frontend/src/pages/Employees.jsx", "r") as f:
    content = f.read()

old_firm_cell = """                      <TableCell>
                        <Chip 
                          label={emp.firm_name || 'No Branch'} 
                          size="small" 
                          variant="outlined"
                          color={emp.firm_name ? "primary" : "default"}
                          sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                        />
                      </TableCell>"""

new_firm_cell = """                      <TableCell>
                        {emp.firm_allocations && emp.firm_allocations.length > 0 ? (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                            {emp.firm_allocations.map(alloc => (
                              <Chip 
                                key={alloc.id}
                                label={alloc.firm_name || 'No Branch'} 
                                size="small"
                                variant="outlined" 
                                color="primary"
                                sx={{ 
                                  fontWeight: 600, 
                                  fontSize: '0.7rem',
                                  width: 'fit-content'
                                }} 
                              />
                            ))}
                          </Box>
                        ) : (
                          <Chip 
                            label={emp.firm_name || 'No Branch'} 
                            size="small" 
                            variant="outlined"
                            color={emp.firm_name ? "primary" : "default"}
                            sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                          />
                        )}
                      </TableCell>"""

content = content.replace(old_firm_cell, new_firm_cell)

with open("../frontend/src/pages/Employees.jsx", "w") as f:
    f.write(content)

