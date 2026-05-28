// catalog.js

console.log("Movie Catalog Loaded");

/* OPTIONAL SIMPLE ANIMATION */

const movieCards = document.querySelectorAll(".movie-card");

movieCards.forEach((card, index) => {

    card.style.opacity = "0";
    card.style.transform = "translateY(30px)";

    setTimeout(() => {

        card.style.transition = "0.5s ease";

        card.style.opacity = "1";
        card.style.transform = "translateY(0px)";

    }, index * 120);

});

/* OPTIONAL HOVER SOUND / EFFECT AREA */

const purchaseButtons = document.querySelectorAll(".purchase-btn");

purchaseButtons.forEach(button => {

    button.addEventListener("mouseenter", () => {

        button.style.transform = "scale(1.03)";

    });

    button.addEventListener("mouseleave", () => {

        button.style.transform = "scale(1)";

    });

});