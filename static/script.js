document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    const pageTitle = document.getElementById('page-title');
    const contentPages = document.querySelectorAll('.page-content');

    // Function to handle page switching
    function switchPage(pageName) {
        // Update the header title
        pageTitle.textContent = pageName.charAt(0).toUpperCase() + pageName.slice(1);

        // Hide all content pages
        contentPages.forEach(page => {
            page.classList.remove('active');
        });

        // Show the corresponding content page
        const activePage = document.getElementById(`${pageName}-content`);
        if (activePage) {
            activePage.classList.add('active');
        }

        // Update active class on navigation links
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-page') === pageName) {
                item.classList.add('active');
            }
        });
    }

    // Add click listeners to navigation items
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault(); // Stop the link from navigating away
            const pageName = item.getAttribute('data-page');
            switchPage(pageName);
        });
    });

    // Initialize the dashboard on load
    switchPage('dashboard');
});