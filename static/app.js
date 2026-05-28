// =========================
// WAIT FOR PAGE LOAD
// =========================

document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // ELEMENTS
    // =========================

    const chat =
        document.getElementById("chat");

    const inputEl =
        document.getElementById("input");

    let history = [];
    let isVoiceInput = false;

    // =========================
    // TOGGLE CHAT
    // =========================

    window.toggleChat = function () {

        const popup =
            document.getElementById("popup");

        popup.style.display =
            popup.style.display === "flex"
            ? "none"
            : "flex";
    };

   window.closePopup = function () {
    const popup = document.getElementById("popup");
    popup.style.display = "none";
};

    // =========================
// ADD MESSAGE
// =========================
function addMessage(text, sender) {

    if (!chat) return;

    // Dynamically hide welcome message to free up vertical space once chat starts
    const welcome = document.querySelector(".welcome-message");
    if (welcome) {
        welcome.style.display = "none";
    }

    const msg = document.createElement("div");
    msg.className = "msg " + sender;

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    // IMPORTANT:
    // DO NOT wrap inside template string
    // directly assign HTML so links remain clickable

    bubble.innerHTML = text;

    msg.appendChild(bubble);
    chat.appendChild(msg);

    chat.scrollTop = chat.scrollHeight;
}
    // =========================
    // SHOW TYPING
    // =========================

    function showTyping() {

        const typing =
            document.createElement("div");

        typing.className =
            "msg bot";

        typing.id =
            "typingIndicator";

        typing.innerHTML = `
            <div class="bubble">
                🎬 CinemaBot is typing...
            </div>
        `;

        chat.appendChild(typing);

        chat.scrollTop =
            chat.scrollHeight;
    }

    // =========================
    // REMOVE TYPING
    // =========================

    function removeTyping() {

        const typing =
            document.getElementById(
                "typingIndicator"
            );

        if (typing) {
            typing.remove();
        }
    }

    // =========================
    // SEND MESSAGE
    // =========================

    window.sendMessage =
        async function () {

        if (!inputEl) return;

        const text =
            inputEl.value.trim();

        if (!text) return;

        // USER MESSAGE

        addMessage(text, "user");

        inputEl.value = "";

        // SHOW TYPING

        showTyping();

        try {

            const res =
                await fetch("/chat", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    message: text,
                    history: history
                })
            });

            removeTyping();

            // SERVER ERROR

            if (!res.ok) {

                addMessage(
                    "⚠️ Flask route error.",
                    "bot"
                );

                return;
            }

            const data =
                await res.json();

            addMessage(
                data.reply,
                "bot"
            );

            if (isVoiceInput) {
                speak(stripHtml(data.reply));
            }
            isVoiceInput = false;

            // SAVE MEMORY

            history.push({
                role: "user",
                content: text
            });

            history.push({
                role: "assistant",
                content: data.reply
            });

        } catch (error) {

            console.log(error);

            removeTyping();

            addMessage(
                "⚠️ Server connection failed.",
                "bot"
            );
        }
    };

    // =========================
    // ENTER KEY
    // =========================

    if (inputEl) {

        inputEl.addEventListener(
            "keypress",
            function (e) {

                if (e.key === "Enter") {

                    sendMessage();
                }
            }
        );
    }

    // =========================
    // QUICK TIP
    // =========================

    window.sendTip =
        function (text) {

        inputEl.value = text;

        sendMessage();
    };

    // =========================
    // VOICE RECOGNITION
    // =========================

    let recognition = null;

    if (
        "webkitSpeechRecognition" in window ||
        "SpeechRecognition" in window
    ) {

        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;

        recognition =
            new SpeechRecognition();

        recognition.lang = "en-US";

        recognition.continuous = false;

        recognition.interimResults = false;

        recognition.onstart =
            function () {

            console.log(
                "🎤 Voice started"
            );
        };

        recognition.onresult =
            function (e) {

            const text =
                e.results[0][0].transcript;

            inputEl.value = text;

            isVoiceInput = true;
            sendMessage();
        };

        recognition.onerror =
            function (e) {

            console.log(
                "Voice Error:",
                e.error
            );

            addMessage(
                "🎤 Voice recognition failed.",
                "bot"
            );
        };

        recognition.onend =
            function () {

            console.log(
                "🎤 Voice ended"
            );
        };
    }

    // =========================
    // START VOICE
    // =========================

    window.startVoice =
        function () {

        if (recognition) {

            // Dynamically set recognition language from dropdown selection
            const langDropdown = document.getElementById("languageDropdown");
            const currentLang = langDropdown ? langDropdown.value : "en";

            if (currentLang === "es") {
                recognition.lang = "es-ES";
            } else if (currentLang === "fr") {
                recognition.lang = "fr-FR";
            } else if (currentLang === "de") {
                recognition.lang = "de-DE";
            } else {
                recognition.lang = "en-US";
            }

            isVoiceInput = true;
            recognition.start();

        } else {

            alert(
                "Voice recognition not supported."
            );
        }
    };

    // =========================
    // TEXT TO SPEECH
    // =========================

    function stripHtml(html) {
        const tmp = document.createElement("DIV");
        tmp.innerHTML = html;
        return tmp.textContent || tmp.innerText || "";
    }

    function speak(text) {

        if (
            !("speechSynthesis" in window)
        ) return;

        window.speechSynthesis.cancel();

        // Clean markdown characters from the text before sending to speech engine
        const cleanText = text
            .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // Remove links [text](url) -> text
            .replace(/!\[([^\]]+)\]\([^)]+\)/g, "$1") // Remove images ![alt](url) -> alt
            .replace(/#+\s+/g, "") // Remove headers
            .replace(/^\s*>\s+/gm, "") // Remove blockquotes
            .replace(/^\s*[-*+]\s+/gm, "") // Remove list bullets
            .replace(/[*_`~]/g, "") // Remove bold, italic, code block, strike markers
            .replace(/\s+/g, " ") // Normalize multiple spaces
            .trim();

        const speech =
            new SpeechSynthesisUtterance(
                cleanText
            );

        // Dynamically set language from the selected dropdown value
        const langDropdown = document.getElementById("languageDropdown");
        const currentLang = langDropdown ? langDropdown.value : "en";

        if (currentLang === "es") {
            speech.lang = "es-ES";
        } else if (currentLang === "fr") {
            speech.lang = "fr-FR";
        } else if (currentLang === "de") {
            speech.lang = "de-DE";
        } else {
            speech.lang = "en-US";
        }

        speech.rate = 1;

        window.speechSynthesis.speak(
            speech
        );
    }

(() => {

    // =========================
    // SEARCH MOVIES (BANNER)
    // =========================

    window.searchMovies = function () {

        const inputElement =
            document.getElementById("search");

        if (!inputElement) return;

        const query =
            inputElement.value.toLowerCase();

        const movies =
            document.querySelectorAll(
                ".movie, .movie-card"
            );

        movies.forEach(movie => {

            const text =
                movie.innerText.toLowerCase();

            movie.style.display =
                text.includes(query)
                    ? "block"
                    : "none";
        });
    };


    // =========================
    // ENTER KEY SUPPORT
    // =========================

    const searchInput =
        document.getElementById("search");

    if (searchInput) {

        searchInput.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {
                    searchMovies();
                }
            }
        );
    }

})();

   // =========================
// LOGIN
// =========================

window.login = function () {

    const user =
        document.getElementById(
            "username"
        ).value;

    const pass =
        document.getElementById(
            "password"
        ).value;

    // =========================
    // CLASSMATE LOGIN
    // =========================

    if (
        user === "student" &&
        pass === "cinema123"
    ) {

        // Hide login
        document.getElementById(
            "loginSection"
        ).style.display = "none";

        // Show feedback form
        document.getElementById(
            "feedbackSection"
        ).style.display = "block";

        // Show logout button
        document.getElementById(
            "logoutContainer"
        ).style.display = "block";

        // Toggle Analytics Dashboard Containers
        const lockedContainer = document.getElementById("analyticsLockedContainer");
        const dashboardContainer = document.getElementById("analyticsDashboardContainer");
        if (lockedContainer) lockedContainer.style.display = "none";
        if (dashboardContainer) dashboardContainer.style.display = "block";

        // Save login state
        localStorage.setItem(
            "cinemaLoggedIn",
            "true"
        );

        localStorage.setItem(
            "cinemaUser",
            user
        );

    } else {

        alert(
            "Invalid login"
        );
    }
};

// =========================
// LOGOUT
// =========================

window.logout = function () {

    // Remove login state
    localStorage.removeItem(
        "cinemaLoggedIn"
    );

    localStorage.removeItem(
        "cinemaUser"
    );

    // Show login
    document.getElementById(
        "loginSection"
    ).style.display = "block";

    // Hide feedback
    document.getElementById(
        "feedbackSection"
    ).style.display = "none";

    // Hide logout button
    document.getElementById(
        "logoutContainer"
    ).style.display = "none";

    // Toggle Analytics Dashboard Containers
    const lockedContainer = document.getElementById("analyticsLockedContainer");
    const dashboardContainer = document.getElementById("analyticsDashboardContainer");
    if (lockedContainer) lockedContainer.style.display = "block";
    if (dashboardContainer) dashboardContainer.style.display = "none";
};

// =========================
// FEEDBACK SUBMIT
// =========================

window.submitFeedback =
    function () {

    const feedback =
        document.getElementById(
            "feedbackText"
        ).value;

    if (!feedback.trim()) {

        alert(
            "Please enter feedback."
        );

        return;
    }

    console.log(
        "Feedback Submitted:",
        feedback
    );

    alert(
        "Thank you for your feedback!"
    );

    document.getElementById(
        "feedbackText"
    ).value = "";
};

// =========================
// FOCUS ADMIN LOGIN INPUT
// =========================
window.focusLogin = function () {
    const usernameEl = document.getElementById("username");
    if (usernameEl) {
        usernameEl.focus();
        usernameEl.scrollIntoView({ behavior: "smooth", block: "center" });
    }
};

// =========================
// RESTORE LOGIN STATE
// =========================

window.addEventListener(
    "load",
    () => {

    const loggedIn =
        localStorage.getItem(
            "cinemaLoggedIn"
        );

    if (loggedIn === "true") {

        document.getElementById(
            "loginSection"
        ).style.display = "none";

        document.getElementById(
            "feedbackSection"
        ).style.display = "block";

        document.getElementById(
            "logoutContainer"
        ).style.display = "block";

        // Toggle Analytics Dashboard Containers
        const lockedContainer = document.getElementById("analyticsLockedContainer");
        const dashboardContainer = document.getElementById("analyticsDashboardContainer");
        if (lockedContainer) lockedContainer.style.display = "none";
        if (dashboardContainer) dashboardContainer.style.display = "block";
    }
});
    // =========================
    // MENU DROPDOWN
    // =========================

    window.toggleMenu =
        function () {

        const menu =
            document.getElementById(
                "menuDropdown"
            );

        if (menu) {

            menu.classList.toggle(
                "show"
            );
        }
    };

    // =========================
    // CATEGORY DROPDOWN
    // =========================

    window.toggleCategories =
        function (btn) {

        let targetBtn = btn || (window.event && window.event.currentTarget) || (window.event && window.event.target);
        if (targetBtn && targetBtn.closest) {
            const container = targetBtn.closest('.categories');
            if (container) {
                const dropdown = container.querySelector('.dropdown');
                if (dropdown) {
                    dropdown.classList.toggle('show');
                    return;
                }
            }
        }

        const cat =
            document.getElementById(
                "categoryDropdown"
            );

        if (cat) {

            cat.classList.toggle(
                "show"
            );
        }
    };

    // =========================
    // CLOSE DROPDOWNS
    // =========================

    window.addEventListener(
        "click",
        function (e) {

        const menu =
            document.getElementById(
                "menuDropdown"
            );

        const isHamburger =
            e.target.closest(
                ".hamburger"
            );

        const isCategory =
            e.target.closest(
                ".categories"
            );

        if (
            menu &&
            !isHamburger
        ) {

            menu.classList.remove(
                "show"
            );
        }

        if (!isCategory) {
            document.querySelectorAll('.categories .dropdown').forEach(d => {
                d.classList.remove('show');
            });
        }
    });

    // =========================
    // OPEN MODAL
    // =========================

    window.openModal =
        function (id) {

        const modal =
            document.getElementById(
                "modal" + id
            );

        if (modal) {

            modal.style.display =
                "block";
        }
    };

    // =========================
    // CLOSE MODAL
    // =========================

    window.closeModal =
        function (id) {

        const modal =
            document.getElementById(
                "modal" + id
            );

        if (modal) {

            modal.style.display =
                "none";
        }
    };

    // =========================
    // CLOSE MODAL OUTSIDE CLICK
    // =========================

    window.onclick =
        function (event) {

        const modals =
            document.querySelectorAll(
                ".modal"
            );

        modals.forEach(modal => {

            if (
                event.target === modal
            ) {

                modal.style.display =
                    "none";
            }
        });
    };


document.querySelectorAll(".icon-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const action = btn.dataset.action;

    if (btn.disabled) return;

    switch (action) {
      case "like":
        console.log("User liked the response 👍");
        break;

      case "dislike":
        console.log("User disliked the response 👎");
        break;

      case "share":
        if (navigator.share) {
          navigator.share({
            title: "Movie Chatbot",
            text: "Check out this conversation!",
            url: window.location.href
          });
        } else {
          alert("Sharing not supported in this browser.");
        }
        break;

      case "ticket":
        console.log("Redirecting to ticket purchase flow 🎟️");
        window.location.href = "/catalog";
        break;
    }
  });
});




(() => {

  const languageDropdown =
    document.getElementById("languageDropdown");

  if (!languageDropdown) return;

  // ===== TRANSLATIONS =====

  const mcTranslations = {

    en: {
      placeholder: "Blade Runner 2049...",
      title: "🎬 CinemaBot",
      tagline: "Your personal movie assistant",
      welcome: "🎬 Welcome to CinemaBot!",
      recommendations: "Ask me for movie recommendations..."
    },

    es: {
      placeholder: "Blade Runner 2049...",
      title: "🎬 CinemaBot",
      tagline: "Tu asistente personal de películas",
      welcome: "🎬 ¡Bienvenido a CinemaBot!",
      recommendations: "Pregúntame por recomendaciones de películas..."
    },

    fr: {
      placeholder: "Blade Runner 2049...",
      title: "🎬 CinemaBot",
      tagline: "Votre assistant cinéma personnel",
      welcome: "🎬 Bienvenue sur CinemaBot !",
      recommendations: "Demandez-moi des recommandations de films..."
    },

    de: {
      placeholder: "Blade Runner 2049...",
      title: "🎬 CinemaBot",
      tagline: "Ihr persönlicher Filmassistent",
      welcome: "🎬 Willkommen bei CinemaBot!",
      recommendations: "Fragen Sie mich nach Filmempfehlungen..."
    }
  };

  // ===== APPLY LANGUAGE =====

  function applyLanguage(language) {

    const translations =
      mcTranslations[language];

    if (!translations) return;

    // ===== INPUT PLACEHOLDER =====

    const userInput =
      document.getElementById("input");

    if (userInput) {
      userInput.placeholder =
        translations.placeholder;
    }

    // ===== UPDATE TEXT ELEMENTS =====

    document
      .querySelectorAll("[data-mc-text]")
      .forEach((element) => {

        const key =
          element.getAttribute("data-mc-text");

        if (translations[key]) {
          element.textContent =
            translations[key];
        }

      });

    // Save language
    localStorage.setItem(
      "mcChatbotLanguage",
      language
    );

  }

  // ===== DROPDOWN CHANGE =====

  languageDropdown.addEventListener(
    "change",
    (event) => {

      const selectedLanguage =
        event.target.value;

      console.log(
        "[MovieChatbot] Language:",
        selectedLanguage
      );

      applyLanguage(selectedLanguage);

    }
  );

  // ===== LOAD SAVED LANGUAGE =====

  const savedLanguage =
    localStorage.getItem(
      "mcChatbotLanguage"
    ) || "en";

  languageDropdown.value =
    savedLanguage;

  applyLanguage(savedLanguage);

})();






// =========================
// FOOTER DATE
// =========================

(() => {

    const footerDate =
        document.getElementById(
            "footerDate"
        );

    if (!footerDate) return;

    const now = new Date();

    footerDate.innerText =
        now.toLocaleDateString(
            "en-US",
            {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric"
            }
        );

})();

});


