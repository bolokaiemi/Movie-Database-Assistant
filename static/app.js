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
    // TOGGLE CHAT (SMOOTH POP-UP)
    // =========================

    window.toggleChat = function () {

        const popup =
            document.getElementById("popup");

        if (popup) {
            popup.classList.toggle("show");
        }
    };

    window.closePopup = function () {
        const popup = document.getElementById("popup");
        if (popup) {
            popup.classList.remove("show");
        }
    };

    // =========================
    // AUTO POPUP ON SCROLL
    // =========================
    let chatOpenedByScroll = false;
    window.addEventListener("scroll", function () {
        if (!chatOpenedByScroll && window.scrollY > 300) {
            const popup = document.getElementById("popup");
            if (popup && !popup.classList.contains("show")) {
                popup.classList.add("show");
                chatOpenedByScroll = true;
            }
        }
    });

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
            "keydown",
            function (e) {

                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
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

            let message = "🎤 Voice recognition failed.";
            if (e.error === "not-allowed") {
                message = "🎤 Microphone permission denied. Please click the camera/mic icon in the browser address bar and allow microphone access.";
            } else if (e.error === "no-speech") {
                message = "🎤 No speech detected. Please try again and speak clearly into your microphone.";
            } else if (e.error === "network") {
                message = "🎤 Network connection error. Speech recognition requires an active internet connection on Chrome.";
            } else if (e.error === "audio-capture") {
                message = "🎤 No recording device detected. Please plug in a microphone.";
            } else {
                message = `🎤 Voice recognition error (${e.error}). Please try again.`;
            }

            addMessage(
                message,
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
    const userEl = document.getElementById("username");
    const passEl = document.getElementById("password");
    if (!userEl || !passEl) return;

    const user = userEl.value;
    const pass = passEl.value;

    if (user === "student" && pass === "cinema123") {
        // Hide login
        const loginEl = document.getElementById("loginSection");
        if (loginEl) loginEl.style.display = "none";

        // Show feedback form
        const feedbackEl = document.getElementById("feedbackSection");
        if (feedbackEl) feedbackEl.style.display = "block";

        // Show logout button
        const logoutEl = document.getElementById("logoutContainer");
        if (logoutEl) logoutEl.style.display = "block";

        // Toggle Analytics Dashboard Containers
        const lockedContainer = document.getElementById("analyticsLockedContainer");
        const dashboardContainer = document.getElementById("analyticsDashboardContainer");
        if (lockedContainer) lockedContainer.style.display = "none";
        if (dashboardContainer) dashboardContainer.style.display = "block";

        // Save login state
        localStorage.setItem("cinemaLoggedIn", "true");
        localStorage.setItem("cinemaUser", user);
    } else {
        alert("Invalid login");
    }
};

// =========================
// LOGOUT
// =========================

window.logout = function () {
    // Remove login state
    localStorage.removeItem("cinemaLoggedIn");
    localStorage.removeItem("cinemaUser");

    // Show login
    const loginEl = document.getElementById("loginSection");
    if (loginEl) loginEl.style.display = "block";

    // Hide feedback
    const feedbackEl = document.getElementById("feedbackSection");
    if (feedbackEl) feedbackEl.style.display = "none";

    // Hide logout button
    const logoutEl = document.getElementById("logoutContainer");
    if (logoutEl) logoutEl.style.display = "none";

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
    if (typeof openLoginModal === 'function') {
        openLoginModal();
    } else {
        const modal = document.getElementById('loginModal');
        if (modal) modal.style.display = 'flex';
    }
    const usernameEl = document.getElementById("username");
    if (usernameEl) {
        usernameEl.focus();
    }
};

// =========================
// RESTORE LOGIN STATE
// =========================

window.addEventListener(
    "load",
    () => {
    const loggedIn = localStorage.getItem("cinemaLoggedIn");

    if (loggedIn === "true") {
        const loginEl = document.getElementById("loginSection");
        if (loginEl) loginEl.style.display = "none";

        const feedbackEl = document.getElementById("feedbackSection");
        if (feedbackEl) feedbackEl.style.display = "block";

        const logoutEl = document.getElementById("logoutContainer");
        if (logoutEl) logoutEl.style.display = "block";

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
        const shareMenu = document.getElementById("shareMenu");
        if (shareMenu) {
          shareMenu.classList.toggle("show");
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

  const mainLanguageDropdown = document.getElementById("mainLanguageDropdown");
  const languageDropdown = document.getElementById("languageDropdown");

  // ===== TRANSLATIONS =====

  const pageTranslations = {
    en: {
      brand: "🎬 MovieMania",
      cinema_portal: "🍿 Cinema Portal",
      analytics: "📊 Analytics",
      genres: "Genres ▼",
      home: "Home",
      movie_list: "Movie-List",
      trending: "Trending",
      series: "Series",
      dashboard: "📊 Dashboard",
      recommend: "Recommend",
      action: "Action",
      comedy: "Comedy",
      horror: "Horror",
      sci_fi: "Sci-Fi",
      welcome_title: "Welcome",
      welcome_subtitle: "Millions of movies, cinema showtimes, and people to discover. Explore now!",
      search_btn: "Search",
      search_placeholder: "🔍 Search movies...",
      
      // Chatbot specific elements
      title: "🎬 CinemaBot",
      tagline: "Your personal movie assistant",
      welcome: "🎬 Welcome to CinemaBot!",
      recommendations: "Ask me for movie recommendations...",
      placeholder: "Ask something..."
    },
    es: {
      brand: "🎬 MovieMania",
      cinema_portal: "🍿 Portal de Cine",
      analytics: "📊 Análisis",
      genres: "Géneros ▼",
      home: "Inicio",
      movie_list: "Lista de Pelis",
      trending: "Tendencias",
      series: "Series",
      dashboard: "📊 Tablero",
      recommend: "Recomendado",
      action: "Acción",
      comedy: "Comedia",
      horror: "Terror",
      sci_fi: "Ciencia Ficción",
      welcome_title: "Bienvenido",
      welcome_subtitle: "Millones de películas, horarios de cine y personas por descubrir. ¡Explora ahora!",
      search_btn: "Buscar",
      search_placeholder: "🔍 Buscar películas...",
      
      // Chatbot specific elements
      title: "🎬 CinemaBot",
      tagline: "Tu asistente personal de películas",
      welcome: "🎬 ¡Bienvenido a CinemaBot!",
      recommendations: "Pregúntame por recomendaciones de películas...",
      placeholder: "Pregunta algo..."
    },
    fr: {
      brand: "🎬 MovieMania",
      cinema_portal: "🍿 Portail Cinéma",
      analytics: "📊 Analyses",
      genres: "Genres ▼",
      home: "Accueil",
      movie_list: "Liste de Films",
      trending: "Tendances",
      series: "Séries",
      dashboard: "📊 Tableau de bord",
      recommend: "Recommander",
      action: "Action",
      comedy: "Comédie",
      horror: "Horreur",
      sci_fi: "Sci-Fi",
      welcome_title: "Bienvenue",
      welcome_subtitle: "Des millions de films, de séances de cinéma et de personnes à découvrir. Explorez maintenant !",
      search_btn: "Rechercher",
      search_placeholder: "🔍 Rechercher des films...",
      
      // Chatbot specific elements
      title: "🎬 CinemaBot",
      tagline: "Votre assistant cinéma personnel",
      welcome: "🎬 Bienvenue sur CinemaBot !",
      recommendations: "Demandez-moi des recommandations de films...",
      placeholder: "Demander quelque chose..."
    },
    de: {
      brand: "🎬 MovieMania",
      cinema_portal: "🍿 Kino-Portal",
      analytics: "📊 Analysen",
      genres: "Genres ▼",
      home: "Startseite",
      movie_list: "Filmliste",
      trending: "Trends",
      series: "Serien",
      dashboard: "📊 Dashboard",
      recommend: "Empfehlen",
      action: "Action",
      comedy: "Komödie",
      horror: "Horror",
      sci_fi: "Sci-Fi",
      welcome_title: "Willkommen",
      welcome_subtitle: "Millionen von Filmen, Kinoprogrammen und Menschen zu entdecken. Jetzt erkunden!",
      search_btn: "Suchen",
      search_placeholder: "🔍 Filme suchen...",
      
      // Chatbot specific elements
      title: "🎬 CinemaBot",
      tagline: "Ihr persönlicher Filmassistent",
      welcome: "🎬 Willkommen bei CinemaBot!",
      recommendations: "Fragen Sie mich nach Filmempfehlungen...",
      placeholder: "Frage etwas..."
    }
  };

  // ===== APPLY LANGUAGE =====

  function applyLanguage(language) {
    const translations = pageTranslations[language];
    if (!translations) return;

    // 1. Update text elements labeled with [data-translate]
    document.querySelectorAll("[data-translate]").forEach((element) => {
      const key = element.getAttribute("data-translate");
      if (translations[key]) {
        element.textContent = translations[key];
      }
    });

    // 2. Update text elements labeled with legacy [data-mc-text] for backward compatibility
    document.querySelectorAll("[data-mc-text]").forEach((element) => {
      const key = element.getAttribute("data-mc-text");
      if (translations[key]) {
        element.textContent = translations[key];
      }
    });

    // 3. Update input placeholders labeled with [data-translate-placeholder]
    document.querySelectorAll("[data-translate-placeholder]").forEach((element) => {
      const key = element.getAttribute("data-translate-placeholder");
      if (translations[key]) {
        element.placeholder = translations[key];
      }
    });

    // 4. Update the chatbot input placeholder legacy style
    const chatbotInput = document.getElementById("input");
    if (chatbotInput && translations.placeholder) {
      chatbotInput.placeholder = translations.placeholder;
    }

    // 5. Keep dropdown selectors synchronized
    if (mainLanguageDropdown) mainLanguageDropdown.value = language;
    if (languageDropdown) languageDropdown.value = language;

    // 6. Save language selection to localStorage
    localStorage.setItem("mcChatbotLanguage", language);
  }

  // ===== BIND EVENTS ON SELECT CHANGE =====

  if (mainLanguageDropdown) {
    mainLanguageDropdown.addEventListener("change", (e) => {
      applyLanguage(e.target.value);
    });
  }

  if (languageDropdown) {
    languageDropdown.addEventListener("change", (e) => {
      applyLanguage(e.target.value);
    });
  }

  // ===== AUTOMATIC COUNTRY-BASED OR LOCALSTORAGE LOAD =====
  
  let currentLanguage = localStorage.getItem("mcChatbotLanguage");

  if (!currentLanguage) {
    // Determine browser country/language settings automatically
    const browserLang = (navigator.language || navigator.userLanguage || "en").toLowerCase();
    if (browserLang.startsWith("es")) {
      currentLanguage = "es";
    } else if (browserLang.startsWith("fr")) {
      currentLanguage = "fr";
    } else if (browserLang.startsWith("de")) {
      currentLanguage = "de";
    } else {
      currentLanguage = "en"; // Default fallback
    }
    console.log("[Language Detector] Automatically set language to:", currentLanguage);
  }

  // Apply resolved language initial state
  applyLanguage(currentLanguage);

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

// =========================================
// PREMIUM SHARE MENU ACTIONS
// =========================================
window.shareOnWhatsApp = function() {
  const shareText = encodeURIComponent("Check out this amazing CinemaBot movie assistant! 🎬🍿\n" + window.location.href);
  window.open(`https://api.whatsapp.com/send?text=${shareText}`, '_blank');
  const shareMenu = document.getElementById("shareMenu");
  if (shareMenu) shareMenu.classList.remove("show");
};

window.shareViaEmail = function() {
  const subject = encodeURIComponent("You've got to check out this CinemaBot!");
  const body = encodeURIComponent("Hey! I was just using this awesome CinemaBot movie assistant to find the latest films and buy tickets. You should check it out here:\n\n" + window.location.href);
  window.open(`mailto:?subject=${subject}&body=${body}`, '_self');
  const shareMenu = document.getElementById("shareMenu");
  if (shareMenu) shareMenu.classList.remove("show");
};

window.shareCopyLink = function() {
  navigator.clipboard.writeText(window.location.href).then(() => {
    window.showToast("Link copied to clipboard! 🔗");
  }).catch(err => {
    alert("Failed to copy link: " + err);
  });
  const shareMenu = document.getElementById("shareMenu");
  if (shareMenu) shareMenu.classList.remove("show");
};

window.showToast = function(message) {
  let toast = document.getElementById("shareToast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "shareToast";
    toast.style.cssText = `
      position: fixed;
      bottom: 30px;
      left: 50%;
      transform: translateX(-50%) translateY(20px);
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid var(--accent);
      color: white;
      padding: 12px 24px;
      border-radius: 12px;
      font-size: 14px;
      font-weight: 600;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      z-index: 100000;
      opacity: 0;
      transition: opacity 0.3s, transform 0.3s;
      pointer-events: none;
    `;
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  setTimeout(() => {
    toast.style.opacity = "1";
    toast.style.transform = "translateX(-50%) translateY(0)";
  }, 50);
  
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(-50%) translateY(20px)";
  }, 3000);
};

// Close share menu if clicked outside
document.addEventListener("click", (event) => {
  const shareMenu = document.getElementById("shareMenu");
  const shareBtn = document.querySelector('[data-action="share"]');
  if (shareMenu && shareMenu.classList.contains("show")) {
    if (!shareMenu.contains(event.target) && event.target !== shareBtn && !shareBtn.contains(event.target)) {
      shareMenu.classList.remove("show");
    }
  }
});


