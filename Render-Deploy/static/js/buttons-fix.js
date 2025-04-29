// This file contains fixes for the active session buttons in the ScanMark application

// Function to toggle session status
async function toggleSessionStatus(token) {
    try {
        console.log(`Toggling session with token: ${token}`);
        
        // Show loading indicator
        Swal.fire({
            title: 'Processing...',
            text: 'Updating session status',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
        
        // Make the API call with proper headers
        const response = await fetch(`/admin/toggle-session/${token}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
            cache: 'no-cache' // Prevent caching
        });
        
        // Parse the response
        const data = await response.json();
        console.log('Toggle response:', data);
        
        // Handle the response
        if (data.success) {
            Swal.fire({
                title: 'Success',
                text: `Session status changed to ${data.status}`,
                icon: 'success',
                timer: 1500,
                showConfirmButton: false
            });
            
            // Refresh the sessions list
            fetchSessions();
        } else {
            console.error('Failed to toggle session:', data.error);
            Swal.fire('Error', data.error || 'Failed to toggle session status', 'error');
        }
    } catch (error) {
        console.error('Error toggling session:', error);
        Swal.fire('Error', 'Unable to toggle session status', 'error');
    }
}

// Function to fetch sessions from the server
async function fetchSessions() {
    try {
        console.log('Fetching sessions...');
        
        // Make the API call
        const response = await fetch('/admin/get-sessions', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            cache: 'no-cache' // Prevent caching
        });
        
        // Parse the response
        const data = await response.json();
        console.log('Sessions response:', data);
        
        // Handle the response
        if (data.success) {
            updateSessionsTable(data.sessions);
        } else {
            console.error('Failed to fetch sessions:', data.error);
            Swal.fire('Error', 'Failed to load sessions', 'error');
        }
    } catch (error) {
        console.error('Error fetching sessions:', error);
        Swal.fire('Error', 'Failed to load sessions', 'error');
    }
}

// Function to update the sessions table
function updateSessionsTable(sessions) {
    const tbody = document.getElementById('sessionsTable');
    if (!tbody) {
        console.error('Sessions table not found');
        return;
    }
    
    let html = '';
    
    if (sessions.length === 0) {
        html = '<tr><td colspan="6" class="text-center">No sessions found</td></tr>';
    } else {
        sessions.forEach((session, index) => {
            const subject = session.subject || session.session;
            const faculty = session.faculty || 'N/A';
            const branch = session.branch || 'N/A';
            const semester = session.semester || 'N/A';
            
            html += `
                <tr>
                    <td>${subject}</td>
                    <td>${faculty}</td>
                    <td>${branch}</td>
                    <td>${semester}</td>
                    <td>
                        <span class="badge bg-${session.status === 'active' ? 'success' : 'danger'}">
                            ${session.status.charAt(0).toUpperCase() + session.status.slice(1)}
                        </span>
                    </td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-primary" onclick="viewQR('${session.token}')">
                                <i class="fas fa-qrcode"></i>
                            </button>
                            <button class="btn btn-sm btn-${session.status === 'active' ? 'warning' : 'success'}" 
                                    onclick="toggleSessionStatus('${session.token}')">
                                <i class="fas fa-toggle-${session.status === 'active' ? 'on' : 'off'}"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteSession('${session.token}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });
    }
    
    tbody.innerHTML = html;
}

// Function to delete a session
async function deleteSession(token) {
    try {
        // Confirm deletion
        const result = await Swal.fire({
            title: 'Are you sure?',
            text: "You won't be able to revert this!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes, delete it!'
        });
        
        if (!result.isConfirmed) {
            return;
        }
        
        // Show loading indicator
        Swal.fire({
            title: 'Processing...',
            text: 'Deleting session',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
        
        // Make the API call
        const response = await fetch(`/admin/delete-session/${token}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
            cache: 'no-cache' // Prevent caching
        });
        
        // Parse the response
        const data = await response.json();
        console.log('Delete response:', data);
        
        // Handle the response
        if (data.success) {
            Swal.fire({
                title: 'Deleted!',
                text: 'Session has been deleted.',
                icon: 'success',
                timer: 1500,
                showConfirmButton: false
            });
            
            // Refresh the sessions list
            fetchSessions();
        } else {
            console.error('Failed to delete session:', data.error);
            Swal.fire('Error', data.error || 'Failed to delete session', 'error');
        }
    } catch (error) {
        console.error('Error deleting session:', error);
        Swal.fire('Error', 'Unable to delete session', 'error');
    }
}

// Initialize the page when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing buttons-fix.js');
    
    // Fetch sessions on page load
    fetchSessions();
    
    // Set up interval to refresh sessions every 30 seconds
    setInterval(fetchSessions, 30000);
});
