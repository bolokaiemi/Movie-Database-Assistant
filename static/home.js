
// ==============================
// Smooth Scrolling
// ==============================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();

        const target = document.querySelector(this.getAttribute('href'));

        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});


// ==============================
// Fade-In Animation
// ==============================

const observer = new IntersectionObserver(entries => {

    entries.forEach(entry => {

        if (entry.isIntersecting) {
            entry.target.classList.add('show-section');
        }

    });

}, {
    threshold: 0.15
});

document.querySelectorAll('.card').forEach(card => {

    card.classList.add('hidden-section');

    observer.observe(card);

});


// ==============================
// Navbar Active Link
// ==============================

const navLinks = document.querySelectorAll('.nav-link');

navLinks.forEach(link => {

    link.addEventListener('click', function () {

        navLinks.forEach(item => {
            item.classList.remove('active');
        });

        this.classList.add('active');

    });

});


// ==============================
// Console Message
// ==============================

console.log("CinemaBot UI Loaded Successfully");
