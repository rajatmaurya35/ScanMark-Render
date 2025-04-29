$(document).ready(function() {
    // Load sessions from the server
    loadSessions();
    loadAIInsights();
    loadRiskAlerts();
    
    // Create session form submission
    $('#createSessionForm').submit(function(e) {
        e.preventDefault();
        
        var sessionData = {
            session: $('#sessionName').val(),
            faculty: $('#faculty').val(),
            branch: $('#branch').val(),
            semester: $('#semester').val()
        };
        
        if (!sessionData.session || !sessionData.faculty) {
            showAlert('danger', 'Session name and faculty are required');
            return;
        }
        
        $.ajax({
            url: '/admin/create-session',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(sessionData),
            success: function(response) {
                if (response.success) {
                    $('#createSessionModal').modal('hide');
                    $('#createSessionForm')[0].reset();
                    showAlert('success', 'Session created successfully');
                    loadSessions();
                } else {
                    showAlert('danger', 'Failed to create session: ' + response.error);
                }
            },
            error: function(xhr, status, error) {
                showAlert('danger', 'Error creating session: ' + error);
            }
        });
    });
});

// Function to load sessions
function loadSessions() {
    $.ajax({
        url: '/admin/get-sessions',
        type: 'GET',
        success: function(response) {
            if (response.success) {
                updateSessionsTable(response.sessions);
            } else {
                showAlert('danger', 'Failed to load sessions: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            showAlert('danger', 'Error loading sessions: ' + error);
        }
    });
}

// Function to update sessions table
function updateSessionsTable(sessions) {
    var tableBody = $('#sessionsTableBody');
    tableBody.empty();
    
    if (sessions.length === 0) {
        tableBody.html('<tr><td colspan="4" class="text-center">No sessions found</td></tr>');
        return;
    }
    
    sessions.forEach(function(s, index) {
        var row = `
            <tr>
                <td>${index + 1}</td>
                <td>${s.session}</td>
                <td><span class="badge bg-${s.status==='active'?'success':'danger'}">${s.status.charAt(0).toUpperCase() + s.status.slice(1)}</span></td>
                <td><div class="btn-group">
                    <button class="btn btn-sm btn-primary" onclick="viewQR('${s.token}')"><i class="fas fa-qrcode"></i></button>
                    <button class="btn btn-sm btn-success" onclick="window.location.href='/admin/attendance/${s.token}'">
                        <i class="fas fa-users"></i> Manage
                    </button>
                    <button class="btn btn-sm btn-${s.status==='active'?'warning':'success'}" onclick="toggleSession('${s.token}')"><i class="fas fa-toggle-${s.status==='active'?'on':'off'}"></i></button>
                    <button class="btn btn-sm btn-danger" onclick="deleteSession('${s.token}')"><i class="fas fa-trash"></i></button>
                </div></td>
            </tr>
        `;
        tableBody.append(row);
    });
}

// Function to load AI insights
function loadAIInsights() {
    $.ajax({
        url: '/admin/get-ai-insights',
        type: 'GET',
        success: function(response) {
            if (response.success) {
                var container = $('#ai-insights-container');
                container.empty();
                
                if (response.ai_insights.length === 0) {
                    container.html('<p class="text-muted mb-0">No insights available</p>');
                    return;
                }
                
                response.ai_insights.forEach(function(insight) {
                    container.append(`
                        <div class="alert alert-info mb-2">
                            <i class="fas fa-lightbulb me-2"></i>${insight}
                        </div>
                    `);
                });
            }
        }
    });
}

// Function to load risk alerts
function loadRiskAlerts() {
    $.ajax({
        url: '/admin/get-risk-alerts',
        type: 'GET',
        success: function(response) {
            if (response.success) {
                var container = $('#risk-alerts-container');
                container.empty();
                
                if (response.risk_alerts.length === 0) {
                    container.html('<p class="text-muted mb-0">No risk alerts at this time</p>');
                    return;
                }
                
                response.risk_alerts.forEach(function(alert) {
                    container.append(`
                        <div class="alert alert-warning mb-2">
                            <i class="fas fa-exclamation-triangle me-2"></i><strong>${alert.subject}</strong> by ${alert.faculty} has no attendance records
                        </div>
                    `);
                });
            }
        }
    });
}

// Function to show alert
function showAlert(type, message) {
    var alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    $('#alertContainer').html(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
}

// Function to view QR code
function viewQR(token) {
    $.ajax({
        url: '/admin/view-qr/' + token,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                // Show QR code in modal
                $('#qrModalImage').attr('src', 'data:image/png;base64,' + response.qr);
                $('#qrModalUrl').text(response.url);
                $('#qrModalSession').text(response.session.session);
                
                // Add animated logo
                $('.qr-logo').addClass('animate__animated animate__pulse animate__infinite');
                
                // Show modal
                $('#qrModal').modal('show');
            } else {
                showAlert('danger', 'Failed to load QR code: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            showAlert('danger', 'Error loading QR code: ' + error);
        }
    });
}

// Function to toggle session status
function toggleSession(token) {
    $.ajax({
        url: '/admin/toggle-session/' + token,
        type: 'POST',
        success: function(response) {
            if (response.success) {
                showAlert('success', 'Session status updated successfully');
                loadSessions();
            } else {
                showAlert('danger', 'Failed to update session status: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            showAlert('danger', 'Error updating session status: ' + error);
        }
    });
}

// Function to delete session
function deleteSession(token) {
    if (!confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
        return;
    }
    
    $.ajax({
        url: '/admin/delete-session/' + token,
        type: 'POST',
        success: function(response) {
            if (response.success) {
                showAlert('success', 'Session deleted successfully');
                loadSessions();
            } else {
                showAlert('danger', 'Failed to delete session: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            showAlert('danger', 'Error deleting session: ' + error);
        }
    });
}
