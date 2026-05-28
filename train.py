import pandas as pd

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# =========================
# LOAD MOVIE DATASET
# =========================

df = pd.read_csv("data/movies.csv")


# =========================
# CONVERT MOVIES TO DOCUMENTS
# =========================

documents = []

for _, row in df.iterrows():

    title = str(row.get("title", ""))
    genre = str(row.get("genre", ""))
    overview = str(row.get("overview", ""))
    rating = str(row.get("rating", ""))

    movie_text = f"""
    Title: {title}

    Genre: {genre}

    Overview:
    {overview}

    Rating:
    {rating}
    """

    documents.append(
        Document(page_content=movie_text)
    )


# =========================
# LOAD EMBEDDING MODEL
# =========================

print("Loading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# =========================
# CREATE VECTOR DATABASE
# =========================

print("Creating vector database...")

db = FAISS.from_documents(
    documents,
    embeddings
)


# =========================
# SAVE VECTOR DATABASE
# =========================

db.save_local("vector_store")


# =========================
# DONE
# =========================

print("✅ Training completed successfully!")
print(f"✅ Movies indexed: {len(documents)}")