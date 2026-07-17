import re

with open("../frontend/src/pages/Dashboard.jsx", "r") as f:
    content = f.read()

# I will append the new Auto Checkout History table directly after the "Top Auto Checkouts" Grid item
old_top_checkouts = """              {/* Auto Checkouts */}
              <Grid item xs={12} sm={6} md={4}>"""

new_history_section = """
          {/* Auto Checkout History Table */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>Recent Auto Checkouts History</Typography>
                {(stats?.attendance?.history || []).length === 0 ? (
                  <Typography variant="body2" color="text.secondary">No recent auto checkouts found.</Typography>
                ) : (
                  <TableContainer>
                    <Table size="small">
                      <TableHead sx={{ bgcolor: 'rgba(0,0,0,0.1)' }}>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 700 }}>Employee</TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>Shift</TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>Checkout Time</TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>Reason</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {(stats?.attendance?.history || []).map((row, idx) => (
                          <TableRow key={idx} hover>
                            <TableCell sx={{ fontWeight: 600 }}>{row.employee}</TableCell>
                            <TableCell>{row.date}</TableCell>
                            <TableCell>{row.shift}</TableCell>
                            <TableCell>{row.checkout_time || '--'}</TableCell>
                            <TableCell>
                              <Chip size="small" color={row.reason === 'AUTO_CHECKOUT_TIMEOUT' ? 'error' : row.reason === 'ADMIN_REJECTED_AUTO_CHECKOUT' ? 'warning' : 'default'} label={row.reason.replace(/_/g, ' ')} />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          </Grid>
"""

# Let's place it after the main attendance overview grid
# It ends at: `</Card>\n          </Grid>\n\n          {/* Reimbursements Analytics */}`
content = content.replace("          {/* Reimbursements Analytics */}", new_history_section + "\n          {/* Reimbursements Analytics */}")

with open("../frontend/src/pages/Dashboard.jsx", "w") as f:
    f.write(content)

