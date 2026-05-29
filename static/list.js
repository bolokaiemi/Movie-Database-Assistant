

/* =====================================
   CinemaBot Movie List JS
   Scoped & safe for all pages
===================================== */

document.addEventListener("DOMContentLoaded", function () {

    const page = document.querySelector(".cinema-list-page");

    if (!page) return;

    const cards = page.querySelectorAll(".cinema-movie-card");

    // =============================
    // Fade-in animation on scroll
    // =============================
    const observer = new IntersectionObserver(entries => {

        entries.forEach(entry => {

            if (entry.isIntersecting) {
                entry.target.classList.add("show-card");
            }

        });

    }, {
        threshold: 0.15
    });

    cards.forEach(card => {
        card.classList.add("hidden-card");
        observer.observe(card);
    });

    // =============================
    // Button click effect
    // =============================
    const buttons = page.querySelectorAll(".btn-primary");

    buttons.forEach(btn => {
        btn.addEventListener("click", function () {
            btn.innerText = "Loading...";
            setTimeout(() => {
                btn.innerText = "View Details";
            }, 1000);
        });
    });

});
