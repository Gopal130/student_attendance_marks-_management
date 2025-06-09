/**
 * Main JavaScript functionality for Attendance Management System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-close flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
    
    // Validate registration form
    const registerForm = document.querySelector('form[action*="register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const password = document.getElementById('password').value;
            
            if (password.length < 8) {
                event.preventDefault();
                alert('Password must be at least 8 characters long.');
                return false;
            }
            
            return true;
        });
    }

    // Validate login form role
    const loginForm = document.querySelector('form[action*="login"]');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            const role = document.getElementById('role').value;
            if (!role) {
                 event.preventDefault();
                 alert('Please select a role (Student or Teacher).');
        }
     });
    }

    
    // Footer year is now handled by the template with {{ now.year }}
});