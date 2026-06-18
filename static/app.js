// =========================
// WAIT FOR PAGE LOAD
// =========================

document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // ELEMENTS
    // =========================

    const chat =
        document.getElementById("chat");

    if (chat) {
        // Automatically scroll to bottom whenever any image, video, iframe or child loads inside the chat
        chat.addEventListener("load", function () {
            chat.scrollTop = chat.scrollHeight;
        }, true);
    }

    const inputEl =
        document.getElementById("input");

    let history = [];
    let isVoiceInput = false;
    let recognition = null;
    let finalTranscript = "";
    let activeAbortController = null;

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

    window.toggleMaximizeChat = function () {
        const popup = document.getElementById("popup");
        const maxBtn = document.getElementById("maximizeChatBtn");
        if (popup) {
            popup.classList.toggle("maximized");
            const isMaximized = popup.classList.contains("maximized");
            if (maxBtn) {
                maxBtn.innerHTML = isMaximized ? "⤣" : "⤢";
                maxBtn.title = isMaximized ? "Restore" : "Maximize";
            }
            const chatBox = document.getElementById("chat");
            if (chatBox) {
                setTimeout(() => {
                    chatBox.scrollTop = chatBox.scrollHeight;
                }, 50);
                setTimeout(() => {
                    chatBox.scrollTop = chatBox.scrollHeight;
                }, 150);
            }
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

    // Failsafe timeouts to keep chat scrolled to bottom as dynamic styles, images, or elements render
    setTimeout(() => { chat.scrollTop = chat.scrollHeight; }, 50);
    setTimeout(() => { chat.scrollTop = chat.scrollHeight; }, 150);
    setTimeout(() => { chat.scrollTop = chat.scrollHeight; }, 350);
    setTimeout(() => { chat.scrollTop = chat.scrollHeight; }, 750);
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

    // =========================
    // STOP CHATBOT CONTROLLER
    // =========================

    const stoppedMessages = {
        en: "⏹️ Response stopped.",
        es: "⏹️ Respuesta detenida.",
        de: "⏹️ Antwort angehalten.",
        fr: "⏹️ Réponse arrêtée."
    };

    window.updateStopButtonVisibility = function () {
        const stopChatBtn = document.getElementById("stopChatBtn");
        if (!stopChatBtn) return;

        const isFetching = (activeAbortController !== null);
        const isSpeaking = ("speechSynthesis" in window && window.speechSynthesis.speaking);
        const isTyping = (document.getElementById("typingIndicator") !== null);

        if (isFetching || isSpeaking || isTyping) {
            stopChatBtn.style.display = "flex";
        } else {
            stopChatBtn.style.display = "none";
        }
    };

    window.stopChatbot = function () {
        let stoppedSomething = false;

        // 1. Abort active Fetch
        if (activeAbortController) {
            activeAbortController.abort();
            activeAbortController = null;
            stoppedSomething = true;
        }

        // 2. Cancel Speech Synthesis
        if ("speechSynthesis" in window && window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
            stoppedSomething = true;
        }

        // 3. Abort voice recognition if active
        if (recognition) {
            try {
                recognition.abort();
            } catch (e) {
                console.log("Recognition abort error:", e);
            }
        }

        // 4. Remove Typing Indicator
        const typing = document.getElementById("typingIndicator");
        if (typing) {
            removeTyping();
            stoppedSomething = true;
        }

        // 5. Reset voice input state
        isVoiceInput = false;

        // If we stopped speech or typing indicator manually (fetch abort prints its own message)
        if (stoppedSomething && !activeAbortController) {
            const langDropdown = document.getElementById("languageDropdown");
            const currentLang = langDropdown ? langDropdown.value : "en";
            const stoppedMsg = stoppedMessages[currentLang] || stoppedMessages["en"];
            addMessage(stoppedMsg, "bot");
        }

        // 6. Hide Stop button
        updateStopButtonVisibility();
    };

    // =========================
    // SEND MESSAGE
    // =========================

    window.sendMessage =
        async function () {

        if (!inputEl) return;

        const text =
            inputEl.value.trim();

        if (!text) return;

        // Abort voice recognition if active to prevent late transcriptions from lingering in the input field
        if (recognition) {
            try {
                recognition.abort();
            } catch (e) {
                console.log("Recognition abort error:", e);
            }
        }
        finalTranscript = "";

        // Intercept stop keywords
        const stopKeywords = [
            "stop", "stopp", "halt", "silencio", "alto", "parar", "silence", "quiet", "shut up", "shh",
            "arrête", "arrete", "haltet", "ruhe"
        ];
        const cleanText = text.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?]/g, "").trim();
        if (stopKeywords.includes(cleanText)) {
            stopChatbot();
            addMessage(text, "user");
            
            const langDropdown = document.getElementById("languageDropdown");
            const currentLang = langDropdown ? langDropdown.value : "en";
            const stoppedMsg = stoppedMessages[currentLang] || stoppedMessages["en"];
            
            setTimeout(() => {
                addMessage(stoppedMsg, "bot");
            }, 300);
            
            inputEl.value = "";
            return;
        }

        // USER MESSAGE

        addMessage(text, "user");

        inputEl.value = "";

        // SHOW TYPING

        showTyping();
        updateStopButtonVisibility();

        // Cancel any lingering fetch from previous commands
        if (activeAbortController) {
            activeAbortController.abort();
        }
        activeAbortController = new AbortController();

        try {

            const modelEl = document.getElementById("model");
            const selectedModel = modelEl ? modelEl.value : "gpt-4.1-mini";

            const res =
                await fetch("/chat", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    message: text,
                    history: history,
                    model: selectedModel
                }),
                signal: activeAbortController.signal
            });

            // Reset active abort controller as fetch completes
            activeAbortController = null;
            removeTyping();
            updateStopButtonVisibility();

            // SERVER ERROR

            if (!res.ok) {
                const langDropdown = document.getElementById("languageDropdown");
                const currentLang = langDropdown ? langDropdown.value : "en";
                const fallbackMessages = {
                    en: "I didn't quite understand your request, could you please rephrase it?",
                    es: "No he entendido bien su solicitud, ¿podría reformular la pregunta, por favor?",
                    de: "Ich habe Ihre Anfrage nicht ganz verstanden, könnten Sie die Frage bitte anders formulieren?",
                    fr: "Je n'ai pas bien compris votre demande, pourriez-vous reformuler la question, s'il vous plaît ?"
                };
                addMessage(
                    fallbackMessages[currentLang] || fallbackMessages["en"],
                    "bot"
                );

                return;
            }

            const data =
                await res.json();

            // Synchronize the interface language if the chatbot responds in a different language
            if (data.language && (data.language === 'en' || data.language === 'de' || data.language === 'es' || data.language === 'fr')) {
                const currentDropdownLang = document.getElementById("languageDropdown") ? document.getElementById("languageDropdown").value : "en";
                if (data.language !== currentDropdownLang) {
                    console.log(`[Language Sync] Chatbot responded in ${data.language}. Syncing UI dropdown.`);
                    if (typeof window.applyLanguage === "function") {
                        window.applyLanguage(data.language);
                    }
                }
            }

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

            activeAbortController = null;
            removeTyping();
            updateStopButtonVisibility();

            if (error.name === "AbortError") {
                const langDropdown = document.getElementById("languageDropdown");
                const currentLang = langDropdown ? langDropdown.value : "en";
                const stoppedMsg = stoppedMessages[currentLang] || stoppedMessages["en"];
                addMessage(stoppedMsg, "bot");
                return;
            }

            const langDropdown = document.getElementById("languageDropdown");
            const currentLang = langDropdown ? langDropdown.value : "en";
            const fallbackMessages = {
                en: "I didn't quite understand your request, could you please rephrase it?",
                es: "No he entendido bien su solicitud, ¿podría reformular la pregunta, por favor?",
                de: "Ich habe Ihre Anfrage nicht ganz verstanden, könnten Sie die Frage bitte anders formulieren?",
                fr: "Je n'ai pas bien compris votre demande, pourriez-vous reformuler la question, s'il vous plaît ?"
            };
            addMessage(
                fallbackMessages[currentLang] || fallbackMessages["en"],
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
        recognition.continuous = true;
        recognition.interimResults = true;

        let silenceTimer = null;
        const SILENCE_TIMEOUT = 2500; // 2.5 seconds silence timeout to allow for pauses in speech

        recognition.onstart = function () {
            console.log("🎤 Voice started");
            finalTranscript = "";
            if (inputEl) inputEl.value = "";
            if (silenceTimer) clearTimeout(silenceTimer);
            
            const micBtn = document.querySelector(".voice");
            if (micBtn) {
                micBtn.style.color = "#ff3c3c";
                micBtn.style.transform = "scale(1.2)";
                micBtn.style.transition = "transform 0.2s ease";
            }
        };

        recognition.onresult = function (e) {
            let interimTranscript = "";
            let currentFinal = "";
            
            for (let i = e.resultIndex; i < e.results.length; ++i) {
                if (e.results[i].isFinal) {
                    currentFinal += e.results[i][0].transcript + " ";
                } else {
                    interimTranscript += e.results[i][0].transcript;
                }
            }
            
            if (currentFinal) {
                finalTranscript += currentFinal;
            }
            
            if (inputEl) {
                inputEl.value = (finalTranscript + interimTranscript).trim();
            }

            // Clear the previous silence timer and reset it
            if (silenceTimer) clearTimeout(silenceTimer);
            silenceTimer = setTimeout(() => {
                console.log("Silence timeout reached. Stopping recognition and sending message.");
                recognition.stop();
            }, SILENCE_TIMEOUT);
        };

        recognition.onerror = function (e) {
            console.log("Voice Error:", e.error);
            if (silenceTimer) clearTimeout(silenceTimer);

            // Ignore programmatically aborted recognition sessions
            if (e.error === "aborted") {
                return;
            }

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

            addMessage(message, "bot");
        };

        recognition.onend = function () {
            console.log("🎤 Voice ended");
            
            const micBtn = document.querySelector(".voice");
            if (micBtn) {
                micBtn.style.color = "";
                micBtn.style.transform = "";
            }

            if (silenceTimer) clearTimeout(silenceTimer);
            
            if (inputEl) {
                inputEl.focus();
            }
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

            const localeMapping = {
                en: "en-US",
                es: "es-ES",
                fr: "fr-FR",
                de: "de-DE",
                it: "it-IT",
                pt: "pt-PT",
                nl: "nl-NL",
                ru: "ru-RU",
                zh: "zh-CN",
                ja: "ja-JP",
                ko: "ko-KR",
                ar: "ar-SA"
            };
            recognition.lang = localeMapping[currentLang] || `${currentLang}-${currentLang.toUpperCase()}`;

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

        // Clean markdown, strip emojis, and improve pronunciation for numbered points
        let cleanText = text
            // Remove markdown links and images
            .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1") // [text](url) → text
            .replace(/!\[([^\]]+)\]\([^)]*\)/g, "$1") // ![alt](url) → alt
            .replace(/^\s*[A-Za-z0-9_-]+\s*:\s*/, "")
            // Basic markdown cleanup
            .replace(/#+\s+/g, "") // Headers
            .replace(/^\s*\>\s+/gm, "") // Blockquotes
            .replace(/^\s*[-*+]\s+/gm, "") // List bullets
            .replace(/[*_`~]/g, "") // Formatting markers
            // Remove emojis and other non‑text symbols
            .replace(/[\u{1F600}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, "")
            // Remove bracketed stage‑direction metadata
            .replace(/\[.*?\]|\(.*?\)|<.*?>/g, "")
            // Remove forbidden words (case‑insensitive)
            .replace(/clapboard/gi, "")
            .replace(/popcorn/gi, "")
            .replace(/\bmovie\s*camera\b/gi, "")
            // Replace numbered points like "1." with the spoken word (one, two, three, …)
            .replace(/\b(\d)\./g, (m, d) => {
                const map = {"1":"one","2":"two","3":"three","4":"four","5":"five","6":"six","7":"seven","8":"eight","9":"nine"};
                return map[d] || d;
            })
            // Replace plain digit numbers (e.g., "1 " ) with words
            .replace(/\b(\d)\b/g, (m, d) => {
                const map = {"1":"one","2":"two","3":"three","4":"four","5":"five","6":"six","7":"seven","8":"eight","9":"nine"};
                return map[d] || d;
            })
            // Remove the term "Clapperboard"
            .replace(/Clapperboard/gi, "")
            .trim();

        const speech =
            new SpeechSynthesisUtterance(
                cleanText
            );

        speech.onstart = function () {
            if (typeof updateStopButtonVisibility === "function") {
                updateStopButtonVisibility();
            }
        };
        speech.onend = function () {
            if (typeof updateStopButtonVisibility === "function") {
                updateStopButtonVisibility();
            }
        };
        speech.onerror = function () {
            if (typeof updateStopButtonVisibility === "function") {
                updateStopButtonVisibility();
            }
        };

        // Dynamically set language from the selected dropdown value
        const langDropdown = document.getElementById("languageDropdown");
        const currentLang = langDropdown ? langDropdown.value : "en";

        const localeMapping = {
            en: "en-US",
            es: "es-ES",
            fr: "fr-FR",
            de: "de-DE",
            it: "it-IT",
            pt: "pt-PT",
            nl: "nl-NL",
            ru: "ru-RU",
            zh: "zh-CN",
            ja: "ja-JP",
            ko: "ko-KR",
            ar: "ar-SA"
        };
        speech.lang = localeMapping[currentLang] || `${currentLang}-${currentLang.toUpperCase()}`;

        speech.rate = 1;

        window.speechSynthesis.speak(
            speech
        );

        // Update stop button visibility immediately to account for starting state
        setTimeout(() => {
            if (typeof updateStopButtonVisibility === "function") {
                updateStopButtonVisibility();
            }
        }, 50);
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

window.login = async function () {
    const userEl = document.getElementById("adminUsername");
    const passEl = document.getElementById("adminPassword");
    if (!userEl || !passEl) return false;

    const user = userEl.value;
    const pass = passEl.value;

    try {
        const res = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username: user, password: pass })
        });

        if (!res.ok) {
            alert("Connection error during login.");
            return false;
        }

        const data = await res.json();

        if (data.success) {
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
            
            // Close login modal if open
            if (typeof closeLoginModal === "function") {
                closeLoginModal();
            } else {
                const modal = document.getElementById("loginModal");
                if (modal) modal.style.display = "none";
            }
            return true;
        } else {
            alert(data.message || "Invalid login");
            return false;
        }
    } catch (error) {
        console.error("Login Error:", error);
        alert("An error occurred during login.");
        return false;
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
    if (dashboardContainer) document.getElementById("analyticsDashboardContainer").style.display = "none";
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
    const usernameEl = document.getElementById("adminUsername");
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
      placeholder: "Ask something...",
      stop_btn: "🛑 Stop"
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
      placeholder: "Pregunta algo...",
      stop_btn: "🛑 Parar"
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
      placeholder: "Demander quelque chose...",
      stop_btn: "🛑 Arrêter"
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
      placeholder: "Frage etwas...",
      stop_btn: "🛑 Stopp"
    }
  };

  // ===== APPLY LANGUAGE =====

  function applyLanguage(language) {
    // 1. Ensure the language option exists in the dropdowns dynamically (for future languages)
    [mainLanguageDropdown, languageDropdown].forEach(dropdown => {
      if (dropdown && !dropdown.querySelector(`option[value="${language}"]`)) {
        const opt = document.createElement("option");
        opt.value = language;
        const langNames = {
          it: "Italiano",
          pt: "Português",
          nl: "Nederlands",
          ru: "Русский",
          zh: "中文",
          ja: "日本語",
          ko: "한국어",
          ar: "العربية",
          pl: "Polski",
          tr: "Türkçe"
        };
        opt.textContent = langNames[language] || language.toUpperCase();
        dropdown.appendChild(opt);
      }
    });

    // 2. Keep dropdown selectors synchronized
    if (mainLanguageDropdown) mainLanguageDropdown.value = language;
    if (languageDropdown) languageDropdown.value = language;

    // 3. Save language selection to localStorage
    localStorage.setItem("mcChatbotLanguage", language);

    // 4. If translations exist, apply them to the page elements
    const translations = pageTranslations[language];
    if (!translations) {
      console.log(`[Language Sync] No page translations for '${language}', keeping current UI text but synced speech settings.`);
      return;
    }

    // 5. Update text elements labeled with [data-translate]
    document.querySelectorAll("[data-translate]").forEach((element) => {
      const key = element.getAttribute("data-translate");
      if (translations[key]) {
        element.textContent = translations[key];
      }
    });

    // 6. Update text elements labeled with legacy [data-mc-text] for backward compatibility
    document.querySelectorAll("[data-mc-text]").forEach((element) => {
      const key = element.getAttribute("data-mc-text");
      if (translations[key]) {
        element.textContent = translations[key];
      }
    });

    // 7. Update input placeholders labeled with [data-translate-placeholder]
    document.querySelectorAll("[data-translate-placeholder]").forEach((element) => {
      const key = element.getAttribute("data-translate-placeholder");
      if (translations[key]) {
        element.placeholder = translations[key];
      }
    });

    // 8. Update the chatbot input placeholder legacy style
    const chatbotInput = document.getElementById("input");
    if (chatbotInput && translations.placeholder) {
      chatbotInput.placeholder = translations.placeholder;
    }
  }

  // Export applyLanguage globally so other scripts can synchronize language dropdowns
  window.applyLanguage = applyLanguage;

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


