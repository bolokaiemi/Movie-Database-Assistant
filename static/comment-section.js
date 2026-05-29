

/* =====================================
   CinemaBot Comment Section JS
   Scoped + reusable across all pages
===================================== */

document.addEventListener("DOMContentLoaded", function () {

    // Scope only inside comment section
    const commentSection = document.querySelector(".cinema-comments-section");

    if (!commentSection) return;

    const form = commentSection.querySelector("form");
    const usernameInput = commentSection.querySelector("#username");
    const commentInput = commentSection.querySelector("#comment");
    const commentContainer = commentSection.querySelector(".mt-5");

    // =============================
    // Form submit handler (frontend only demo)
    // =============================
    form.addEventListener("submit", function (e) {
        e.preventDefault(); // stop page reload

        const name = usernameInput.value.trim();
        const comment = commentInput.value.trim();

        if (!name || !comment) return;

        // Create new comment box
        const newComment = document.createElement("div");
        newComment.classList.add("comment-box");

        newComment.innerHTML = `
            <div class="comment-user">${name}</div>
            <p class="comment-text">${comment}</p>
        `;

        // Insert at top of comments
        commentContainer.appendChild(newComment);

        // Clear form
        usernameInput.value = "";
        commentInput.value = "";

        // Optional feedback
        alert("Comment added successfully!");
    });

});

