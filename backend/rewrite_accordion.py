import re

with open("../frontend/src/pages/Attendance.jsx", "r") as f:
    content = f.read()

# We need to replace the entire <Grid item xs={12} md={isAdmin ? 12 : 7}>...
# which starts around line 629 and ends around line 796
# We'll use regex to match from `{/* History Table */}` to `        {/* Overtime Approval Registry`

# The new Admin Accordion Component:
new_history_section = """        {/* History Table */}
        <Grid item xs={12} md={isAdmin ? 12 : 7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                {isAdmin ? 'Team Attendance Records' : 'My Attendance History'}
              </Typography>

              {isAdmin && (
                <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
                  <TextField 
                    size="small" 
                    type="date" 
                    name="date" 
                    label="Date" 
                    InputLabelProps={{ shrink: true }}
                    value={filters.date} 
                    onChange={handleFilterChange} 
                  />
                  <TextField 
                    size="small" 
                    name="employee" 
                    label="Employee Name" 
                    value={filters.employee} 
                    onChange={handleFilterChange} 
                  />
                  <FormControl size="small" sx={{ minWidth: 150 }}>
                    <InputLabel>Status</InputLabel>
                    <Select name="status" value={filters.status} label="Status" onChange={handleFilterChange}>
                      <MenuItem value="">All</MenuItem>
                      <MenuItem value="PRESENT">Present</MenuItem>
                      <MenuItem value="LATE">Late</MenuItem>
                      <MenuItem value="HALF_DAY">Half Day</MenuItem>
                      <MenuItem value="ABSENT">Absent</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl size="small" sx={{ minWidth: 150 }}>
                    <InputLabel>Auto Checkout</InputLabel>
                    <Select name="autoCheckout" value={filters.autoCheckout} label="Auto Checkout" onChange={handleFilterChange}>
                      <MenuItem value="">All</MenuItem>
                      <MenuItem value="true">Yes</MenuItem>
                      <MenuItem value="false">No</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
              )}

              {/* ACCORDION IMPLEMENTATION */}
              {isAdmin ? (
                <Box>
                  {Object.keys(groupedRecords).length === 0 ? (
                    <Typography color="text.secondary">No attendance logs available.</Typography>
                  ) : (
                    Object.keys(groupedRecords).sort((a, b) => new Date(b) - new Date(a)).map(dateStr => {
                      const dayRecords = groupedRecords[dateStr];
                      const presentCount = dayRecords.filter(r => r.status === 'PRESENT').length;
                      const lateCount = dayRecords.filter(r => r.status === 'LATE').length;
                      const halfDayCount = dayRecords.filter(r => r.status === 'HALF_DAY').length;
                      const absentCount = dayRecords.filter(r => r.status === 'ABSENT').length;
                      const isDateExpanded = expandedDates[dateStr];

                      return (
                        <Accordion 
                          key={dateStr} 
                          expanded={!!isDateExpanded} 
                          onChange={() => toggleDate(dateStr)}
                          sx={{ mb: 1, bgcolor: 'background.neutral', '&:before': { display: 'none' }, borderRadius: '8px !important' }}
                        >
                          <AccordionSummary expandIcon={<ChevronDown />}>
                            <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                              <Typography sx={{ fontWeight: 700, color: 'primary.main', mb: 1 }}>
                                {formatDate(dateStr)} ({dayRecords.length} Employees)
                              </Typography>
                              {!isDateExpanded && (
                                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                                  <Typography variant="caption">Present: {presentCount}</Typography>
                                  <Typography variant="caption">Late: {lateCount}</Typography>
                                  <Typography variant="caption">Half Day: {halfDayCount}</Typography>
                                  <Typography variant="caption">Absent: {absentCount}</Typography>
                                </Box>
                              )}
                            </Box>
                          </AccordionSummary>
                          <AccordionDetails sx={{ p: 0, bgcolor: 'background.default' }}>
                            {isDateExpanded && dayRecords.map(empRec => {
                              const empKey = `${dateStr}_${empRec.id}`;
                              const isEmpExpanded = expandedEmployees[empKey];
                              
                              return (
                                <Accordion 
                                  key={empRec.id} 
                                  expanded={!!isEmpExpanded}
                                  onChange={() => toggleEmployee(dateStr, empRec.id)}
                                  sx={{ m: 1, boxShadow: 'none', border: '1px solid rgba(255,255,255,0.05)', '&:before': { display: 'none' } }}
                                >
                                  <AccordionSummary expandIcon={<ChevronDown />}>
                                    <Box sx={{ display: 'flex', gap: 3, alignItems: 'center', width: '100%' }}>
                                      <Typography sx={{ fontWeight: 600, minWidth: 150 }}>{empRec.employee_name}</Typography>
                                      <Chip label={empRec.status} size="small" color={getStatusChipColor(empRec.status)} sx={{ fontWeight: 600, fontSize: '0.7rem' }} />
                                      <Typography variant="body2" color="text.secondary">Total: {empRec.total_worked_hours || '0.00'} Hrs</Typography>
                                      <Button size="small" variant="outlined" onClick={(e) => { e.stopPropagation(); handleOpenOtModal(empRec); }} sx={{ ml: 'auto', fontSize: '0.7rem' }}>
                                        Pre-Approve OT
                                      </Button>
                                    </Box>
                                  </AccordionSummary>
                                  <AccordionDetails sx={{ p: 2, pt: 0 }}>
                                    {isEmpExpanded && empRec.sessions && empRec.sessions.length > 0 ? (
                                      empRec.sessions.map((sess, idx) => (
                                        <Box key={sess.id} sx={{ p: 1.5, mb: 1, borderRadius: 2, bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
                                          <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                                            
                                            {/* Session Core Info */}
                                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 120 }}>
                                              <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 700 }}>Session {idx + 1}</Typography>
                                              <Typography variant="body2"><strong>In:</strong> {sess.check_in_time || '--'}</Typography>
                                              <Typography variant="body2"><strong>Out:</strong> {sess.check_out_time || 'Active'}</Typography>
                                              <Typography variant="caption" color="primary.main">Duration: {sess.working_hours || '--'}</Typography>
                                            </Box>
                                            
                                            {/* Photos */}
                                            <Box sx={{ display: 'flex', gap: 2 }}>
                                              <Box sx={{ textAlign: 'center' }}>
                                                <Typography variant="caption" color="text.secondary">Check In</Typography>
                                                <Box sx={{ mt: 0.5 }}>
                                                  {sess.captured_image ? (
                                                    <img src={getMediaUrl(sess.captured_image)} alt="Check In" onClick={() => setPreviewImage(getMediaUrl(sess.captured_image))} style={{ width: 40, height: 40, borderRadius: 4, cursor: 'pointer', objectFit: 'cover' }} />
                                                  ) : '--'}
                                                </Box>
                                              </Box>
                                              <Box sx={{ textAlign: 'center' }}>
                                                <Typography variant="caption" color="text.secondary">Check Out</Typography>
                                                <Box sx={{ mt: 0.5 }}>
                                                  {sess.check_out_captured_image ? (
                                                    <img src={getMediaUrl(sess.check_out_captured_image)} alt="Check Out" onClick={() => setPreviewImage(getMediaUrl(sess.check_out_captured_image))} style={{ width: 40, height: 40, borderRadius: 4, cursor: 'pointer', objectFit: 'cover' }} />
                                                  ) : '--'}
                                                </Box>
                                              </Box>
                                            </Box>
                                            
                                            {/* Location */}
                                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, maxWidth: 200 }}>
                                              {sess.check_in_address && (
                                                <Tooltip title={sess.check_in_address} placement="top">
                                                  <Typography variant="caption" sx={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>📍 <strong>In:</strong> {sess.check_in_address}</Typography>
                                                </Tooltip>
                                              )}
                                              {sess.check_out_address && (
                                                <Tooltip title={sess.check_out_address} placement="bottom">
                                                  <Typography variant="caption" sx={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>📍 <strong>Out:</strong> {sess.check_out_address}</Typography>
                                                </Tooltip>
                                              )}
                                              {sess.checkout_reason === 'AUTO_CHECKOUT' && (
                                                <Chip size="small" color="error" label="Auto Checkout" sx={{ mt: 0.5 }} />
                                              )}
                                            </Box>
                                            
                                            {/* Actions */}
                                            <Box sx={{ display: 'flex', gap: 1, ml: 'auto' }}>
                                              <Button size="small" variant="outlined" onClick={() => {
                                                const sessWithParentStatus = { ...sess, parent_status: empRec.status };
                                                setSelectedSessionForEdit(sessWithParentStatus);
                                                setEditModalOpen(true);
                                              }}>Edit</Button>
                                              <Button size="small" color="error" variant="outlined" onClick={() => handleDeleteSession(sess.id)}>Delete</Button>
                                            </Box>
                                            
                                          </Box>
                                        </Box>
                                      ))
                                    ) : (
                                      <Typography variant="caption" color="text.secondary">No sessions recorded.</Typography>
                                    )}
                                  </AccordionDetails>
                                </Accordion>
                              );
                            })}
                          </AccordionDetails>
                        </Accordion>
                      );
                    })
                  )}
                  
                  {totalRecords > pageSize && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                      <Pagination count={Math.ceil(totalRecords / pageSize)} page={page} onChange={(e, v) => setPage(v)} color="primary" />
                    </Box>
                  )}
                </Box>
              ) : (
                /* Non-Admin Employee View */
                <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                  <Table>
                    <TableBody>
                      {history.length === 0 ? (
                        <TableRow>
                          <TableCell align="center" sx={{ py: 4, color: 'text.secondary' }}>No attendance logs available.</TableCell>
                        </TableRow>
                      ) : (
                        history.map((rec) => (
                          <TableRow key={rec.id}>
                            <TableCell colSpan={1} sx={{ p: 0 }}>
                              <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2, pb: 1.5, borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                  <Typography variant="subtitle1" sx={{ fontWeight: 700, color: 'primary.main' }}>
                                    {formatDate(rec.date)}
                                  </Typography>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                                    <Typography variant="body2"><strong>Daily Total:</strong> {rec.total_worked_hours || '0.00'} Hours</Typography>
                                    <Chip label={rec.status} size="small" color={getStatusChipColor(rec.status)} sx={{ fontWeight: 600, fontSize: '0.75rem' }} />
                                  </Box>
                                </Box>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                                  {rec.sessions && rec.sessions.length > 0 ? (
                                    rec.sessions.map((sess, idx) => (
                                      <Box key={sess.id} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 1.5, borderRadius: '8px', bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', flexWrap: 'wrap', gap: 2 }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, minWidth: '250px' }}>
                                          <Typography variant="body2" sx={{ fontWeight: 700, minWidth: '80px', color: 'text.secondary' }}>Session {idx + 1}</Typography>
                                          <Box>
                                            <Typography variant="body2" sx={{ fontWeight: 600 }}>🌅 {sess.check_in_time || '--'} &rarr; 🌇 {sess.check_out_time || 'Active'}</Typography>
                                            <Typography variant="caption" color="text.secondary">Duration: {sess.working_hours || '--'}</Typography>
                                          </Box>
                                        </Box>
                                        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                                          <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="caption" display="block" color="text.secondary" sx={{ mb: 0.5 }}>Check In</Typography>
                                            {sess.captured_image ? (
                                              <img src={getMediaUrl(sess.captured_image)} alt="Checkin" onClick={() => setPreviewImage(getMediaUrl(sess.captured_image))} style={{ width: 48, height: 48, borderRadius: '6px', objectFit: 'cover', cursor: 'pointer', border: '1px solid rgba(255,255,255,0.1)' }} />
                                            ) : '--'}
                                          </Box>
                                          <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="caption" display="block" color="text.secondary" sx={{ mb: 0.5 }}>Check Out</Typography>
                                            {sess.check_out_captured_image ? (
                                              <img src={getMediaUrl(sess.check_out_captured_image)} alt="Checkout" onClick={() => setPreviewImage(getMediaUrl(sess.check_out_captured_image))} style={{ width: 48, height: 48, borderRadius: '6px', objectFit: 'cover', cursor: 'pointer', border: '1px solid rgba(255,255,255,0.1)' }} />
                                            ) : '--'}
                                          </Box>
                                        </Box>
                                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, maxWidth: '300px' }}>
                                          {sess.check_in_address && <Typography variant="caption" sx={{ display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }} title={sess.check_in_address}>📍 <strong>In:</strong> {sess.check_in_address}</Typography>}
                                          {sess.check_out_address && <Typography variant="caption" sx={{ display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }} title={sess.check_out_address}>📍 <strong>Out:</strong> {sess.check_out_address}</Typography>}
                                        </Box>
                                      </Box>
                                    ))
                                  ) : (
                                    <Typography variant="caption" color="text.secondary">No sessions recorded.</Typography>
                                  )}
                                </Box>
                              </Box>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

            </CardContent>
          </Card>
        </Grid>
"""

# Regex replacement
pattern = r"        \{\/\* History Table \*\/\}.*?(?=        \{\/\* Overtime Approval Registry)"
content = re.sub(pattern, new_history_section, content, flags=re.DOTALL)

with open("../frontend/src/pages/Attendance.jsx", "w") as f:
    f.write(content)

