window.addEventListener('scroll', function() {
    var navbar = document.getElementById('navbar-marketing');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled-nav');
        navbar.classList.remove('bg-white')
    } else {
        navbar.classList.remove('scrolled-nav');
        navbar.classList.add('bg-white')
    }
});