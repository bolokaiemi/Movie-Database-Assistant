# 🌟 Stoplight Cinema Portal & Administrator Console (MovieMania Hub)

An interactive, premium-grade multi-user Cinema Portal and Administrator Console built with **Flask**, **SQLite**, and **Streamlit**. The project features the **MovieMania Home Experience**—a central web hub for browsing films, managing watchlists, locating theater showtimes, and booking tickets. This full-stack system integrates a rich movie catalog, a secure administrator control console, real-time data analytics, and a conversational AI helper.

---

## 🚀 Key Features

### 1. 🏠 MovieMania Home Experience (Central Hub)
The main web portal serves as a premium central experience for cinema enthusiasts:
* **Interactive Navigation:** Allows users to easily jump between catalog grids, active watchlists, real-time analytics graphs, and physical map screens.
* **Unified UI/UX:** Styled in an immersive, high-contrast dark theme with glowing red accents, designed to feel like a modern, state-of-the-art streaming platform.

### 2. 🎠 Dynamic Slider Banner (Carousel)
Located at the header of the MovieMania homepage, this **Swiper-based dynamic slider banner**:
* Displays a rotating spotlight of **new releases, award-winning films, and trending titles**.
* Renders key metadata inline, including audience ratings (e.g., ⭐ 8.8), genre tags (e.g., Action / Sci-Fi), and release dates.
* Employs premium CSS visual effects, including a slow Ken-Burns image zoom on active slides, glassmorphism overlays, and fully padded custom navigation controls to ensure mobile layout responsiveness without element overlaps.

### 3. 💬 AI Cinemachat & 📍 Cinema Map Integration
An advanced multi-turn conversational assistant is integrated on the front-end to streamline booking, navigation, and movie discovery:
* **🎫 Direct Ticket Purchases:** Users can buy tickets directly through the chatbot. The interactive chat flow guides users through selecting showtimes, choosing seat tiers (Standard, VIP, etc.), adding concession snacks, and instantly generating digital tickets with QR codes right inside the chat window.
* **🎙️ Voice Recognition Input:** The chat input field supports voice recognition and Speech-to-Text (STT) for multiple languages, including English, Spanish, French, and German. Transcribed text is populated directly in the chat box, focusing the cursor and allowing users to review and edit their spoken messages before manual submission.
* **🤖 AI Model Selection Dropdown:** A model selection dropdown is positioned at the top of the chatbot interface, letting users choose between different AI versions and model engines—specifically supporting **GPT-4.1-mini, GPT-5-mini, and GPT-4o-mini (GPT-4.0-mini)**—to customize response styling and capabilities.
* **🛡️ Polite Multilingual Fail-safes:** The chatbot catches internal backend exceptions, OpenAI API connectivity issues, or network timeouts, replacing raw technical errors (such as Flask Route or OpenAI error strings) with friendly, localized rephrase requests in the user's detected language.
* **🛑 Instant Halting (Stop Button & Keyword Commands):** Renders a red `🛑 Stop` button next to the send button that appears dynamically when the chatbot is typing, fetching, or reading a response aloud. Users can click this button or type/speak a stop command (e.g., *"stop"*, *"stopp"*, *"alto"*, *"parar"*) to immediately abort the server fetch call, remove typing indicators, terminate speech synthesis narration, and print a localized confirmation without loading the server.
* **🌐 Embedded Cinema Websites Navigation:** Enhances user convenience by allowing the chatbot to present simulated local cinema websites and showtime schedules directly within the chat interface based on the user's preferred **city and country** (e.g., Enugu, Nigeria, or Bochum/Herne, Germany). It embeds responsive same-origin iframes with custom CSS and provides direct clickable links to official external sites for exterior views.
* **🎭 Genre Recommendation Filtering:** To streamline movie recommendations, the assistant includes a genre filtering feature that allows users to filter suggestions based on specific themes like Action, Comedy, Horror, Sci-Fi, and Drama.
* **📤 Share Button:** A built-in share button allows users to share chatbot responses and recommendations. Clicking it opens a sharing panel where users can share content via WhatsApp, email, or by copying the direct link.
* **📍 Cinema Map Integration & Directions:** Once a user purchases a ticket or asks for theater locations, the chatbot embeds a `📍 Open Cinema Map` button. Clicking it displays an interactive Leaflet map showcasing pre-seeded theaters in Enugu (Nigeria), Berlin, Bochum, and Herne (Germany). It features a **Global Geocoding Search Bar** allowing users to search any city or country in the world, fly the map to the location, and dynamically spawn local mock Stoplight Cinema markers.
* **🎠 Homepage Slider Banner Integration:** The chatbot is dynamically connected to the homepage slider banner (carousel). It is aware of any featured trending titles, new releases, classics, and award winners, allowing it to instantly answer questions, provide overviews, display posters, and link directly to details/ticket booking for any movie prominently featured on the site.



### 4. 🔒 Dedicated Administrator Control Console (`/dashboard`)
A central, secure admin interface (authorized via the admin account) displaying:
* **Real-Time Database Metrics:** Live counts of active films in the catalog, user watchlists, and submitted reviews.
* **Add New Movie to Catalog:** A dedicated admin panel allowing administrators to easily add new titles directly to the database. Upon creation, the system automatically seeds default standard/VIP showtimes and ticket tiers. The inputs support metadata auto-fill and voice-to-text.
* **Interactive Movie Catalog Editor:** A secure details expansion block allowing administrators to update any existing movie in the database catalog. Features support metadata auto-filling from OMDb/TMDB, OpenAI-powered plot summarization (`gpt-4.1-mini`), and local poster asset downloads.
* **Voice-Activated Input Fields:** Form input fields support voice recognition (transcribing spoken words in Spanish, French, German, or English) to speed up updates.
* **Classmate Feedback Stream:** A real-time log of peer project feedback and presentations notes.
* **Peer Review Form:** An expandable, interactive feedback submission form that writes classmate feedback into the database and refreshes the panel instantly.
* **Recent Movie Reviews:** A live stream of customer movie reviews showing rating stars, feedback comments, and the associated movie titles.

### 5. 📊 Interactive Analytics Dashboard (`/analytics`)
Separated from the core control panel to ensure speed and focus. Hosts a custom **Streamlit & Plotly** charts dashboard iframe (`http://127.0.0.1:8501/?embed=true`) that visualizes:
* Distribution of interactive movie request volumes.
* NLP-based customer satisfaction scores and review sentiment.
* Ticket tier conversions and peak user interaction times.
* **Dynamic CORS Host Resolution:** Automatically adapts Streamlit iframe host URLs to match the parent window (e.g. localhost, local IP, or 127.0.0.1) to prevent cross-origin policy blocks.

### 6. 🔑 Secure Authentication & Password Reset
* **Hashed Credentials:** Admin logins are authenticated using secure password hashing (`werkzeug.security`) against the `admin_credentials` database table instead of raw environment comparisons.
* **Password Reset Workflow:** Includes a secure Forgot Password flow inside the login modal that issues 6-digit OTP verification codes via SMTP (falling back to server log mocks for local development) to reset access.
* **Race Condition Fix:** Login modal operations are fully asynchronous, resolving double-click responsiveness bugs when toggling views.

### 7. ❌ Secure Ticket Cancellation & Refund System
* **User-Side Cancellation:** Adds a custom **"Cancel Ticket & Refund Booking"** button inside the digital ticket checkout receipt. Customers can cancel their bookings and concessions within the allowed window.
* **Admin Voiding Panel:** Integrates a look-up verification console inside the Administrator Dashboard (`/dashboard`) that allows admins to verify any ticket code in the database and manually void/refund bookings.
* **Hashed Bookkeeping:** Changes the ticket status dynamically in the SQLite database to `'cancelled'` to maintain financial audit trails and prevent double-cancellations.
* **Automated SMTP Confirmation:** Sends a fully customized HTML cancellation receipt detailing the refund processing straight to the customer's email using SMTP.

### 8. 💾 Persistent Digital Receipt State (Session Storage)
* **Session Restoration:** Automatically caches the active ticket receipt data inside browser `sessionStorage` upon successful checkout. If a user refreshes the page, navigates away, or triggers the map popup, their ticket receipt is seamlessly restored.
* **Re-booking Reset:** Adds a **"Book Another Ticket"** action button that appears only after a booking is voided, letting users reset the browser session and return to a clean booking form.

### 9. 🔍 Page-Specific Search Bars (Lobby vs. Home styles)
* **Watchlist Vault Search:** Integrates a search input inside the movie watchlist page styled **identically** to the main Movie Mania homepage search pill.
* **Cinema Portal Search:** Features a **completely unique, lobby-styled search bar** on the Cinema Catalog page. Built with custom glassmorphism, square borders, neon red glows, and uppercase button selectors to distinctively separate catalog scheduling from the default movie home index.
* **Instant Client-Side Filtering:** Employs JavaScript filter scripts to instantly show or hide matching movie cards on key release events, eliminating backend page reloads.

---

## 🛠️ Technology Stack

* **Backend:** Python, Flask, Flask-CORS
* **Frontend:** Vanilla HTML, CSS, JavaScript (Glassmorphism & Sleek Dark Mode with `#ff3c3c` Accent Colors)
* **Database:** SQLite3
* **Analytics & Graphs:** Streamlit, Pandas, Plotly, NumPy
* **AI Engine:** OpenAI API, LangChain (Core & Community)

---

## 📥 Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd mentalmovie
   ```

2. **Set Up the Virtual Environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   TMDB_API_KEY=your_tmdb_api_key_here
   OMDB_API_KEY=your_omdb_api_key_here
   ```

---

## ⚡ How to Run

### Option A: Using the Launcher Script (Recommended on Windows)
Simply double-click the **`run_project.bat`** file in the root folder. It will automatically initialize both server instances in separate console windows:
* **Flask Web App URL:** [http://127.0.0.1:5000](http://127.0.0.1:5000)
* **Streamlit Analytics URL:** [http://127.0.0.1:8501](http://127.0.0.1:8501)

### Option B: Manual Execution

1. **Launch the Flask Web App:**
   ```bash
   python app.py
   ```
2. **Launch the Streamlit Analytics Dashboard:**
   ```bash
   streamlit run analytics.py --server.enableCORS=false --server.enableXsrfProtection=false
   ```

---

## 👥 Classmate & Teacher Presentation Guide

This guide contains instructions on how classmates and teachers can test the portal's interactive features and submit their peer evaluations.

### 💬 How to Submit Peer Feedback
1. **Open the Homepage:** Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000).
2. **Find the Feedback Form:** Scroll to the bottom of the page to find the **💬 Project Review & Classmate Feedback** expander panel (which is open by default).
3. **Write & Submit:** Enter your comments, ratings, or critiques in the text box and click **Submit Feedback**.
4. **View Live Stream:** Once submitted, your feedback is recorded in the SQLite database and instantly appears in the **Classmate Project Reviews** live stream on the homepage, as well as on the **Administrator Dashboard** (`/dashboard`).

---

### 🤖 CinemaBot Interactive Prompt Examples
To motivate discussion and showcase the conversational AI's capability, classmates and teachers are encouraged to try the following interactive prompts:

#### 🎫 1. End-to-End Ticket Booking & Snacking
* **Prompt:** *"I'd like to book a ticket for Deadpool"*
* **Prompt:** *"Show me showtimes for Nosferatu and book a VIP seat with popcorn"*
* *Interactive Flow:* CinemaBot will ask for your preferences, prompt you to select a seat tier, and output a dynamic digital receipt with a scannable barcode and QR code.

#### ❌ 2. Booking Verification & Ticket Cancellation
* **Prompt:** *"Verify my booking [insert ticket code]"*
* **Prompt:** *"Cancel my ticket for booking code [insert ticket code]"*
* *Interactive Flow:* The bot verifies the booking status against the database, processes a refund, updates seat availability, and dispatches a confirmation email.

#### 🌐 3. Simulated Local Cinema Websites
* **Prompt:** *"What local cinemas are in Enugu?"*
* **Prompt:** *"Are there any movie theaters in Bochum?"*
* *Interactive Flow:* CinemaBot embeds a responsive local cinema iframe inside the chat window, letting you explore theater-specific showtimes.

#### 📍 4. Interactive Maps & Physical Directions
* **Prompt:** *"Show me the cinema locator map"*
* **Prompt:** *"How do I get to the theater in Herne?"*
* *Interactive Flow:* CinemaBot renders a `📍 Open Cinema Map` button. Clicking it displays a Leaflet map showing locations, addresses, and route directions.

#### 🎬 5. Playable Movie Trailers
* **Prompt:** *"Can you show me the trailer for Avatar: Fire and Ash?"*
* **Prompt:** *"Do you have the video trailer for Jaws?"*
* *Interactive Flow:* CinemaBot embeds a responsive YouTube trailer player directly inside the conversation thread.

#### 🎠 6. Homepage Carousel Awareness
* **Prompt:** *"What movies are currently trending on the main slider?"*
* **Prompt:** *"Tell me about the classic film featured in the homepage banner"*
* *Interactive Flow:* The chatbot scans the active Swiper slider banner context and answers questions about the featured spotlight films.

#### 🎙️ 7. Hands-Free Voice Input & Model Swap
* **Microphone Input:** Click the microphone icon next to the chat bar to speak your prompts in English, German, French, or Spanish.
* **Model Dropdown:** Use the selector at the top of the chatbot window to toggle between **GPT-4o-mini**, **GPT-4.1-mini**, and **GPT-5-mini** to see how responses change.

#### 🛑 8. Instant Halting & Intercept Commands
* **Prompt:** *"stop"* or *"stopp"* or *"alto"* or *"parar"*
* *Interactive Flow:* CinemaBot halts any active speech output or backend generation immediately, clears the interface, and prints a polite localized confirmation (`⏹️ Response stopped.`) directly in the chat history.

---

## 🎤 Speech-to-Text Permissions Note
Chrome blocks speech-to-text API calls in insecure contexts. To ensure the microphone button works on your system:
* Make sure you access the site via **`http://localhost:5000`** or **`http://127.0.0.1:5000`**.
* Accessing the server via a local network IP address (e.g., `http://192.168.x.x:5000`) will cause Chrome to block microphone access.

---

## 🔮 Future Roadmap & Planned Features
To demonstrate continuous development and highlight the platform's vision, the following features are planned for future releases:

### 1. 🛡️ User Privacy & Data Protection
* **Dedicated Privacy Dashboard:** Integrate a control panel in the user's profile settings allowing users to manage data storage, clear search history, and configure chat logging preferences.
* **Plain-Language Onboarding Policy:** Introduce a simplified, transparent privacy policy displayed during the onboarding process to explain data handling in plain language.
* **Camera-Based Age Verification & Smart Parental Controls:** Implement conversational age-verification prompting (where the chatbot queries the viewer's age to filter recommendations). Integrate secure, camera-based age verification (using privacy-preserving, on-device facial analysis) to prevent children from bypassing age restrictions on 18+ mature content without storing biometric data.


### 2. 👥 Personalization & Social Engagement
* **Actor & Director Watchlist Alerts:** Let users follow their favorite actors or directors and receive automatic email/push alerts when new catalog titles featuring them are released.
* **Collaborative Playlists & Shared Watchlists:** Enable users to share custom movie watchlists with friends, recommend films directly to other users, and collaborate on shared watchlists.
### 3. ⚙️ Technical Scaling & Infrastructure
* **🛡️ Production-Grade User Authentication:** Replace hardcoded credentials with a multi-role user system (Admins, Managers, Customers) using `Flask-Login` and `bcrypt` password hashing.
* **⚡ Live Presentation Interactions:** Integrate WebSockets (`Flask-SocketIO`) so classmate reviews and movie comments appear on everyone’s screen in real-time without refreshing.
* **💳 Real Payment Gateway Mocking:** Connect checkout portals to sandbox Stripe/PayPal checkout APIs for simulated transaction processing.
* **🤖 Machine Learning Recommendations:** Build a collaborative-filtering movie recommendation engine utilizing database ratings history instead of static queries.

---

## ✍️ Authorship & License

* **Authorship:** This project was created and maintained by **Ebi Emmerich-Adehor**.
* **License:** This project is licensed under the [MIT License](file:///c:/Users/Bolokaiemi/PycharmProjects/mentalmovie/LICENSE) - see the [LICENSE](file:///c:/Users/Bolokaiemi/PycharmProjects/mentalmovie/LICENSE) file for details.
