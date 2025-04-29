$(document).ready(function() {
    // Get token from URL
    var pathParts = window.location.pathname.split('/');
    var token = pathParts[pathParts.length - 1];
    
    // Load attendance data
    loadAttendanceData();
    
    // Add student form submission
    $('#addStudentForm').submit(function(e) {
        e.preventDefault();
        
        var studentId = $('#studentId').val();
        var studentName = $('#studentName').val();
        
        if (!studentId) {
            showAlert('danger', 'Student ID is required');
            return;
        }
        
        $.ajax({
            url: '/admin/update-attendance',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                session_token: token,
                student_id: studentId,
                student_name: studentName,
                status: 'present'
            }),
            success: function(response) {
                if (response.success) {
                    $('#addStudentModal').modal('hide');
                    $('#addStudentForm')[0].reset();
                    showAlert('success', 'Student added successfully');
                    loadAttendanceData();
                } else {
                    showAlert('danger', 'Failed to add student: ' + (response.error || 'Unknown error'));
                }
            },
            error: function(xhr, status, error) {
                showAlert('danger', 'Error adding student: ' + error);
            }
        });
    });
    
    // Export attendance button
    $('#exportAttendance').click(function() {
        exportToCSV();
    });
    
    // Set up refresh interval (every 30 seconds)
    setInterval(loadAttendanceData, 30000);
});

// Function to load attendance data
function loadAttendanceData() {
    var pathParts = window.location.pathname.split('/');
    var token = pathParts[pathParts.length - 1];
    
    $.ajax({
        url: '/admin/attendance-history/' + token,
        type: 'GET',
        success: function(data) {
            var tableBody = $('#attendanceTableBody');
            tableBody.empty();
            
            if (data.length === 0) {
                $('#noDataMessage').show();
                $('#attendanceTable').hide();
                return;
            }
            
            $('#noDataMessage').hide();
            $('#attendanceTable').show();
            
            data.forEach(function(record, index) {
                var date = new Date(record.created_at);
                var formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                
                var statusBadge = record.status === 'present' 
                  ? '<span class="badge bg-success">Present</span>' 
                  : '<span class="badge bg-danger">Absent</span>';
                
                var row = `
                  <tr data-student-id="${record.student_id}" data-student-name="${record.student_name || ''}">
                    <td>${index + 1}</td>
                    <td>${record.student_id}</td>
                    <td>${record.student_name || 'N/A'}</td>
                    <td>${formattedDate}</td>
                    <td>${statusBadge}</td>
                    <td>
                      <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-success" onclick="markAttendance('${record.student_id}', '${record.student_name || ''}', 'present')">
                          Present
                        </button>
                        <button type="button" class="btn btn-sm btn-danger" onclick="markAttendance('${record.student_id}', '${record.student_name || ''}', 'absent')">
                          Absent
                        </button>
                      </div>
                    </td>
                  </tr>
                `;
                
                tableBody.append(row);
            });
        },
        error: function(xhr, status, error) {
            console.error('Error loading attendance data:', error);
            showAlert('danger', 'Failed to load attendance data. Please try again.');
        }
    });
}

// Function to mark attendance
function markAttendance(studentId, studentName, status) {
    var pathParts = window.location.pathname.split('/');
    var token = pathParts[pathParts.length - 1];
    
    $.ajax({
        url: '/admin/update-attendance',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            session_token: token,
            student_id: studentId,
            student_name: studentName,
            status: status
        }),
        success: function(response) {
            if (response.success) {
                showAlert('success', 'Attendance updated successfully');
                loadAttendanceData();
            } else {
                showAlert('danger', 'Failed to update attendance: ' + (response.error || 'Unknown error'));
            }
        },
        error: function(xhr, status, error) {
            showAlert('danger', 'Error updating attendance: ' + error);
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

// Function to export attendance data to CSV
function exportToCSV() {
    var table = document.getElementById('attendanceTable');
    var rows = table.querySelectorAll('tbody tr');
    
    if (rows.length === 0) {
        showAlert('warning', 'No data to export');
        return;
    }
    
    var csv = [];
    var headers = ['No.', 'Student ID', 'Student Name', 'Timestamp', 'Status'];
    csv.push(headers.join(','));
    
    rows.forEach(function(row) {
        var rowData = [];
        row.querySelectorAll('td').forEach(function(cell, index) {
            if (index < 5) { // Skip the action buttons column
                // For status column, get the text content of the badge
                if (index === 4) {
                    rowData.push('"' + cell.textContent.trim() + '"');
                } else {
                    rowData.push('"' + cell.textContent.trim() + '"');
                }
            }
        });
        csv.push(rowData.join(','));
    });
    
    // Download CSV
    var csvContent = csv.join('\n');
    var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    var url = URL.createObjectURL(blob);
    
    var link = document.createElement('a');
    var pathParts = window.location.pathname.split('/');
    var token = pathParts[pathParts.length - 1];
    
    link.setAttribute('href', url);
    link.setAttribute('download', 'attendance_' + token + '.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
