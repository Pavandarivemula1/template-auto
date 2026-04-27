document.addEventListener("DOMContentLoaded", function () {
    // 1. Mobile Menu Toggle
    const menuToggle = document.getElementById("menu-toggle");
    const mobileNav = document.getElementById("mobile-nav");

    if (menuToggle && mobileNav) {
        menuToggle.addEventListener("click", function () {
            mobileNav.classList.toggle("active");
        });
    }

    // 2. Search Tabs Toggle (For Rent / For Sale)
    const searchTabs = document.querySelectorAll(".s-tab");
    searchTabs.forEach(tab => {
        tab.addEventListener("click", function () {
            searchTabs.forEach(t => t.classList.remove("active"));
            this.classList.add("active");
            window.location.href = "properties.html";
        });
    });

    // 3. Category Pills Toggle (Properties Filter view)
    const categoryPills = document.querySelectorAll(".pill");
    categoryPills.forEach(pill => {
        pill.addEventListener("click", function () {
            categoryPills.forEach(p => p.classList.remove("active"));
            this.classList.add("active");
            window.location.href = "properties.html";
        });
    });

    // 4. Hero Search Redirection
    const searchBtn = document.querySelector('.search-actions .btn-large');
    if (searchBtn) {
        searchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = 'properties.html';
        });
    }

});
