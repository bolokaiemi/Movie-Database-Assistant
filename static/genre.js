
// ==============================
// Genre Card Animation
// ==============================

const genreObserver = new IntersectionObserver(entries => {

    entries.forEach(entry => {

        if (entry.isIntersecting) {
            entry.target.classList.add('show-card');
        }

    });

}, {
    threshold: 0.2
});

document.querySelectorAll('.card').forEach(card => {

    card.classList.add('hidden-card');

    genreObserver.observe(card);

});


// ==============================
// Button Click Effect
// ==============================

const buttons = document.querySelectorAll('.btn-primary');

buttons.forEach(button => {

    button.addEventListener('click', () => {

        button.innerText = "Loading...";

        setTimeout(() => {
            button.innerText = "View Movie";
        }, 1500);

    });

});


// ==============================
// Console Message
// ==============================

console.log("Genre Pages Loaded Successfully");

