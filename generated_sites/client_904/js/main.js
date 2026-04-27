document.addEventListener('DOMContentLoaded', () => {
    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navList = document.querySelector('.nav-list');

    if (menuToggle && navList) {
        menuToggle.addEventListener('click', () => {
            const isVisible = navList.style.display === 'flex';
            if (isVisible) {
                navList.style.display = '';
                // Clear inline styles so css media queries work again if resized
                navList.removeAttribute('style');
            } else {
                navList.style.display = 'flex';
                navList.style.flexDirection = 'column';
                navList.style.position = 'absolute';
                navList.style.top = '100%';
                navList.style.left = '0';
                navList.style.right = '0';
                navList.style.backgroundColor = 'var(--clr-bg-primary)';
                navList.style.padding = '20px';
                navList.style.zIndex = '99';
                navList.style.gap = '20px';
            }
        });
    }

    // Sticky Header effect setup (optional if scrolling behavior is needed)
    const header = document.querySelector('.header');
    if (header) {
        const isHomePage = window.location.pathname.endsWith('index.html') || window.location.pathname === '/';
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                header.style.backgroundColor = 'var(--clr-bg-primary)';
                header.style.boxShadow = '0 4px 20px rgba(0,0,0,0.1)';
            } else {
                if (isHomePage) {
                    header.style.backgroundColor = 'transparent';
                }
                header.style.boxShadow = 'none';
            }
        });
    }
});
