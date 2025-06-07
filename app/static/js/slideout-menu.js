document.addEventListener('DOMContentLoaded', function() {
    const menuIcon = document.getElementById('menu-icon');
    const slideoutMenu = document.getElementById('slideout-menu');
    const header = document.querySelector('.modern-header');

    // Toggle slideout menu
    menuIcon.addEventListener('click', function() {
        slideoutMenu.classList.toggle('active');
        menuIcon.classList.toggle('active'); // Rotate the hamburger icon
    });

    // Add 'scrolled' class to header on scroll
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) { // Adjust this value based on your header height
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
});