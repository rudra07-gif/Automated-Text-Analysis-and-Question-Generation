// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Highlight selected option in quizzes
    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all options
            document.querySelectorAll('.option-btn').forEach(b => {
                b.classList.remove('active', 'btn-primary');
                b.classList.add('btn-outline-primary');
            });

            // Add active class to clicked option
            this.classList.add('active', 'btn-primary');
            this.classList.remove('btn-outline-primary');
        });
    });

    // Auto-focus first input in forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const firstInput = form.querySelector('input[type="text"], input[type="password"], input[type="email"], textarea');
        if (firstInput) {
            firstInput.focus();
        }
    });
});

// Function to confirm logout
function confirmLogout() {
    return confirm('Are you sure you want to logout?');
}

// Function to format paragraph text (for paragraph quiz)
function formatParagraphText() {
    const paragraphs = document.querySelectorAll('.paragraph-text');
    paragraphs.forEach(p => {
        p.innerHTML = p.textContent.replace(/\n/g, '<br>');
    });
}

// Call formatting function when page loads
window.onload = formatParagraphText;