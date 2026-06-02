# 🌟 Stoplight Cinema Portal & Administrator Console

An interactive, premium-grade multi-user Cinema Portal and Administrator Console built with **Flask**, **SQLite**, and **Streamlit**. The project hosts a fully fledged interactive movie catalog, a secure administrator control console, real-time data analytics pipelines, and an integrated AI Cinemachat assistant with speech-to-text functionality.

---

## 🚀 Key Features

### 1. 🔒 Dedicated Administrator Control Console (`/dashboard`)
A central, secure admin interface (authorized via the `student` profile) displaying:
* **Real-Time Database Metrics:** Counts of active films in the catalog, user watchlists, and submitted reviews.
* **Classmate Feedback Stream:** A real-time log of peer project feedback and presentations notes.
* **Peer Review Form:** An expandable, interactive feedback submission form that writes classmate feedback into the database and refreshes the panel instantly.
* **Recent Movie Reviews:** A live stream of customer movie reviews showing rating stars, feedback comments, and the associated movie titles.

### 2. 📊 Interactive Analytics Dashboard (`/analytics`)
Separated from the core control panel to ensure speed and focus. Hosts a custom **Streamlit & Plotly** charts dashboard iframe (`http://127.0.0.1:8501/?embed=true`) that visualizes:
* Distribution of interactive movie request volumes.
* NLP-based customer satisfaction scores and review sentiment.
* Ticket tier conversions and peak user interaction times.

### 3. 🎬 Rich Cinema Catalog
Contains **35 premium blockbuster movies** complete with:
* High-fidelity movie poster graphics and embedded video trailers.
* 3 daily showtimes (Standard, IMAX, VIP Screenings) and dynamic ticket pricing structures.
* Movie details, concession ordering forms, and user comment/rating forms.

### 4. 💬 AI Cinemachat Assistant
An advanced multi-turn conversational AI helper embedded on the main interface to:
* Recommend movies based on user moods, genres, or actors.
* Guide users through the ticket purchase flow.
* Supports **Speech Recognition (Speech-to-Text)** for voice-activated inputs.

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

## 🎤 Speech-to-Text Permissions Note
Chrome blocks speech-to-text API calls in insecure contexts. To ensure the microphone button works on your system:
* Make sure you access the site via **`http://localhost:5000`** or **`http://127.0.0.1:5000`**.
* Accessing the server via a local network IP address (e.g., `http://192.168.x.x:5000`) will cause Chrome to block microphone access.
