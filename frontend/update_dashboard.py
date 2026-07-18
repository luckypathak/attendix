import re

with open('src/pages/Dashboard.jsx', 'r') as f:
    content = f.read()

# Add MUI imports for Dialog, Accordion, etc.
if "Dialog," not in content:
    content = content.replace("CircularProgress", "CircularProgress, Dialog, DialogTitle, DialogContent, Accordion, AccordionSummary, AccordionDetails, Table, TableBody, TableCell, TableHead, TableRow, TableContainer, Paper, IconButton")

if "ExpandMore" not in content and "lucide-react" in content:
    content = content.replace("Hourglass", "Hourglass, ChevronDown, X")

# Add state for modal
if "autoCheckoutModalOpen" not in content:
    content = content.replace(
        "const [loading, setLoading] = useState(true);",
        "const [loading, setLoading] = useState(true);\n  const [autoCheckoutModalOpen, setAutoCheckoutModalOpen] = useState(false);"
    )

# Modify Auto Checkouts Card
old_card = """              {/* Auto Checkouts */}
              <Grid item xs={12} sm={6} md={4}>
                <Card onClick={() => navigate('/attendance')} sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }, transition: 'all 0.2s', background: 'linear-gradient(135deg, rgba(231, 76, 60, 0.1) 0%, rgba(255, 159, 67, 0.1) 100%)' }}>
                  <CardContent sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <MonitorOff size={18} color="#e74c3c" />
                        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Auto Checkouts</Typography>
                      </Box>
                      <Typography variant="h4" sx={{ fontWeight: 800, color: '#e74c3c' }}>{stats?.attendance?.auto_checkouts_today ?? 0}</Typography>
                      <Typography variant="caption" color="text.secondary">Today</Typography>
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="h5" sx={{ fontWeight: 800 }}>{stats?.attendance?.auto_checkouts_month ?? 0}</Typography>
                      <Typography variant="caption" color="text.secondary">This Month</Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>"""

new_card = """              {/* Auto Checkouts */}
              <Grid item xs={12} sm={12} md={4}>
                <Card onClick={() => setAutoCheckoutModalOpen(true)} sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }, transition: 'all 0.2s', background: 'linear-gradient(135deg, rgba(231, 76, 60, 0.05) 0%, rgba(255, 159, 67, 0.05) 100%)' }}>
                  <CardContent sx={{ display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <MonitorOff size={18} color="#e74c3c" />
                      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Auto Checkouts</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="h4" sx={{ fontWeight: 800, color: '#e74c3c' }}>{stats?.attendance?.auto_checkouts_today ?? 0}</Typography>
                        <Typography variant="caption" color="text.secondary">Today</Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h5" sx={{ fontWeight: 800 }}>{stats?.attendance?.auto_checkouts_yesterday ?? 0}</Typography>
                        <Typography variant="caption" color="text.secondary">Yesterday</Typography>
                      </Box>
                      <Box sx={{ textAlign: 'right' }}>
                        <Typography variant="h5" sx={{ fontWeight: 800 }}>{stats?.attendance?.auto_checkouts_month ?? 0}</Typography>
                        <Typography variant="caption" color="text.secondary">This Month</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>"""

if old_card in content:
    content = content.replace(old_card, new_card)

# Inject the Modal at the end, just inside the main Container/Box, before the final </div> or </Box>
# The component ends with: `</Box> \n  );\n}`
modal_jsx = """
      {/* Auto Checkouts Details Modal */}
      <Dialog 
        open={autoCheckoutModalOpen} 
        onClose={() => setAutoCheckoutModalOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <DialogTitle sx={{ m: 0, p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: 'rgba(231, 76, 60, 0.05)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <MonitorOff size={20} color="#e74c3c" />
            <Typography variant="h6" sx={{ fontWeight: 700 }}>Auto Checkouts Details</Typography>
          </Box>
          <IconButton onClick={() => setAutoCheckoutModalOpen(false)}>
            <X size={20} />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers sx={{ p: 0 }}>
          <Accordion defaultExpanded disableGutters elevation={0} sx={{ borderBottom: '1px solid #eee', '&:before': { display: 'none' } }}>
            <AccordionSummary expandIcon={<ChevronDown />} sx={{ bgcolor: '#fafafa' }}>
              <Typography sx={{ fontWeight: 600 }}>Today's Auto Checkouts ({stats?.attendance?.auto_checkouts_today ?? 0})</Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ p: 0 }}>
              <TableContainer>
                <Table size="small">
                  <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Employee</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Shift</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Check-Out Time</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Reason</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {stats?.attendance?.history?.filter(h => h.date === new Date().toISOString().split('T')[0]).map((row, idx) => (
                      <TableRow key={idx} hover>
                        <TableCell>{row.employee}</TableCell>
                        <TableCell>
                          <Chip label={row.shift} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>{row.checkout_time || 'N/A'}</TableCell>
                        <TableCell>
                          <Chip label={row.reason} size="small" color="warning" sx={{ fontWeight: 500 }} />
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!stats?.attendance?.history || stats?.attendance?.history?.filter(h => h.date === new Date().toISOString().split('T')[0]).length === 0) && (
                      <TableRow>
                        <TableCell colSpan={4} align="center" sx={{ py: 3, color: 'text.secondary' }}>No auto checkouts today</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>

          <Accordion disableGutters elevation={0} sx={{ '&:before': { display: 'none' } }}>
            <AccordionSummary expandIcon={<ChevronDown />} sx={{ bgcolor: '#fafafa' }}>
              <Typography sx={{ fontWeight: 600 }}>Yesterday's Auto Checkouts ({stats?.attendance?.auto_checkouts_yesterday ?? 0})</Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ p: 0 }}>
              <TableContainer>
                <Table size="small">
                  <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Employee</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Shift</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Check-Out Time</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Reason</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {stats?.attendance?.history?.filter(h => {
                      const d = new Date();
                      d.setDate(d.getDate() - 1);
                      return h.date === d.toISOString().split('T')[0];
                    }).map((row, idx) => (
                      <TableRow key={idx} hover>
                        <TableCell>{row.employee}</TableCell>
                        <TableCell>
                          <Chip label={row.shift} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>{row.checkout_time || 'N/A'}</TableCell>
                        <TableCell>
                          <Chip label={row.reason} size="small" color="warning" sx={{ fontWeight: 500 }} />
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!stats?.attendance?.history || stats?.attendance?.history?.filter(h => {
                      const d = new Date();
                      d.setDate(d.getDate() - 1);
                      return h.date === d.toISOString().split('T')[0];
                    }).length === 0) && (
                      <TableRow>
                        <TableCell colSpan={4} align="center" sx={{ py: 3, color: 'text.secondary' }}>No auto checkouts yesterday</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        </DialogContent>
      </Dialog>
    </Box>
  );
}
"""

if "Auto Checkouts Details Modal" not in content:
    content = content.replace("    </Box>\n  );\n}", modal_jsx)

with open('src/pages/Dashboard.jsx', 'w') as f:
    f.write(content)

print("Dashboard updated successfully.")
