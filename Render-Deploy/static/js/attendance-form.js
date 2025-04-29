$(document).ready(function() {
    // Initialize variables
    let stream = null;
    let videoElement = document.getElementById('camera');
    let photoElement = document.getElementById('photo');
    let captureButton = document.getElementById('capture');
    let retakeButton = document.getElementById('retake');
    let submitButton = document.getElementById('submit');
    let loadingSpinner = document.getElementById('loadingSpinner');
    let photoTaken = false;
    let locationData = null;
    
    // Get session token from URL
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (!token) {
        showError('Invalid QR code. Please scan again.');
        return;
    }
    
    // Start camera
    startCamera();
    
    // Get location
    getLocation();
    
    // Capture photo
    captureButton.addEventListener('click', function() {
        if (!stream) {
            showError('Camera not available. Please allow camera access and try again.');
            return;
        }
        
        // Draw video frame to canvas
        const canvas = document.createElement('canvas');
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        
        // Convert to data URL
        const dataUrl = canvas.toDataURL('image/jpeg');
        
        // Display photo
        photoElement.src = dataUrl;
        photoElement.style.display = 'block';
        videoElement.style.display = 'none';
        
        // Show retake button
        captureButton.style.display = 'none';
        retakeButton.style.display = 'inline-block';
        
        // Enable submit button if all data is available
        photoTaken = true;
        checkSubmitButton();
    });
    
    // Retake photo
    retakeButton.addEventListener('click', function() {
        // Hide photo and show video
        photoElement.style.display = 'none';
        videoElement.style.display = 'block';
        
        // Hide retake button and show capture button
        retakeButton.style.display = 'none';
        captureButton.style.display = 'inline-block';
        
        // Disable submit button
        photoTaken = false;
        checkSubmitButton();
    });
    
    // Submit form
    $('#attendanceForm').submit(function(e) {
        e.preventDefault();
        
        // Get form data
        const studentId = $('#studentId').val();
        const studentName = $('#studentName').val();
        
        // Validate form
        if (!studentId) {
            showError('Please enter your student ID');
            return;
        }
        
        if (!photoTaken) {
            showError('Please take a photo');
            return;
        }
        
        if (!locationData) {
            showError('Location data not available. Please allow location access and try again.');
            return;
        }
        
        // Show loading spinner
        loadingSpinner.style.display = 'block';
        submitButton.disabled = true;
        
        // Prepare data for submission
        const formData = {
            token: token,
            student_id: studentId,
            student_name: studentName,
            location: locationData,
            photo: photoElement.src
        };
        
        // Submit data
        $.ajax({
            url: '/submit-attendance',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                loadingSpinner.style.display = 'none';
                
                if (response.success) {
                    // Show success message
                    $('#formContainer').hide();
                    $('#successContainer').show();
                    
                    // Stop camera stream
                    stopCamera();
                } else {
                    showError(response.error || 'Failed to submit attendance');
                    submitButton.disabled = false;
                }
            },
            error: function(xhr, status, error) {
                loadingSpinner.style.display = 'none';
                showError('Error submitting attendance: ' + error);
                submitButton.disabled = false;
            }
        });
    });
});

// Function to start camera
function startCamera() {
    const videoElement = document.getElementById('camera');
    const errorElement = document.getElementById('cameraError');
    
    // Check if browser supports getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        errorElement.textContent = 'Your browser does not support camera access';
        errorElement.style.display = 'block';
        return;
    }
    
    // Get user media
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
        .then(function(mediaStream) {
            stream = mediaStream;
            videoElement.srcObject = mediaStream;
            videoElement.play();
            errorElement.style.display = 'none';
        })
        .catch(function(err) {
            console.error('Error accessing camera:', err);
            errorElement.textContent = 'Error accessing camera: ' + err.message;
            errorElement.style.display = 'block';
        });
}

// Function to stop camera
function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
}

// Function to get location
function getLocation() {
    const locationStatus = document.getElementById('locationStatus');
    
    // Check if browser supports geolocation
    if (!navigator.geolocation) {
        locationStatus.textContent = 'Geolocation is not supported by your browser';
        locationStatus.className = 'text-danger';
        return;
    }
    
    // Get current position
    navigator.geolocation.getCurrentPosition(
        function(position) {
            // Success
            locationData = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy
            };
            
            locationStatus.textContent = 'Location: ' + position.coords.latitude.toFixed(6) + ', ' + position.coords.longitude.toFixed(6);
            locationStatus.className = 'text-success';
            
            // Initialize map
            initMap(position.coords.latitude, position.coords.longitude);
            
            // Enable submit button if all data is available
            checkSubmitButton();
        },
        function(error) {
            // Error
            console.error('Error getting location:', error);
            locationStatus.textContent = 'Error getting location: ' + error.message;
            locationStatus.className = 'text-danger';
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

// Function to initialize map
function initMap(latitude, longitude) {
    const mapElement = document.getElementById('map');
    
    if (!mapElement) return;
    
    // Create map
    const map = L.map(mapElement).setView([latitude, longitude], 15);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Add marker
    L.marker([latitude, longitude]).addTo(map)
        .bindPopup('Your location')
        .openPopup();
}

// Function to check if submit button should be enabled
function checkSubmitButton() {
    const submitButton = document.getElementById('submit');
    const studentId = document.getElementById('studentId').value;
    
    submitButton.disabled = !(studentId && photoTaken && locationData);
}

// Function to show error
function showError(message) {
    const alertContainer = document.getElementById('alertContainer');
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.role = 'alert';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.innerHTML = '';
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        alert.classList.remove('show');
        setTimeout(function() {
            alertContainer.removeChild(alert);
        }, 150);
    }, 5000);
}
