# Codebase Architecture Overview

This document contains the codebase architecture diagram and description for the Stoplight Cinema project. You can copy the Mermaid diagram code directly into tools like [Mermaid Live Editor](https://mermaid.live/) or tools like Github, Notion, or Canva to render it visually.

## Architecture Diagram (Mermaid Format)

```mermaid
graph TD
    User([User / Peer]) -->|Visits /| Homepage[Flask Homepage]
    User -->|Interacts| Chatbot[CinemaBot Chat Window]
    Chatbot -->|Sends message| FlaskApp[Flask Backend app.py]
    FlaskApp -->|Calls OpenAI API| LLM[LLM Engine]
    FlaskApp -->|Queries / Writes| DB[(SQLite movies.db)]
    Streamlit[Streamlit Analytics app.py] -->|Queries| DB
    Admin([Administrator]) -->|Logs in| Dashboard[Flask Dashboard]
    Dashboard -->|Inspects Analytics| Streamlit
```

## Component Descriptions

1. **Frontend:** 
   - Uses Jinja2 HTML5 templates (`templates/index.html`, `templates/dashboard.html`) styled with HSL variables and Outfit/Poppins typography.
   - Communicates asynchronously via fetch/AJAX requests for chatbot messaging and classmate reviews.
2. **Backend (app.py):**
   - Built with Flask. Manages routes, same-origin iframe simulation, chatbot system prompting, and API login validations.
3. **Database (movies.db):**
   - Relational SQLite database. Houses:
     - `movies` (saved watchlists)
     - `movie_catalog` (cinema schedules and details)
     - `classmate_feedback` (peer evaluations)
     - `movie_comments` (customer reviews and ratings)
4. **Analytics (analytics.py):**
   - Concurrently running Streamlit visualization server that displays charts and database metrics.
