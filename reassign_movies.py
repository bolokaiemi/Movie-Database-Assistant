import sqlite3


def reassign_movies():

    # =========================================
    # CONNECT TO DATABASE
    # =========================================

    conn = sqlite3.connect("movies.db")

    cursor = conn.cursor()

    try:

        # =========================================
        # TRANSFER MOVIES
        # FROM USER 1 → USER 2
        # =========================================

        query = """
        UPDATE movies
        SET user_id = 1
        WHERE user_id = 2
        """

        cursor.execute(query)

        # =========================================
        # SAVE CHANGES
        # =========================================

        conn.commit()

        print("✅ Movies reassigned successfully.")

    except sqlite3.Error as e:

        print("❌ Database error:", e)

        conn.rollback()

    finally:

        conn.close()


# =========================================
# RUN SCRIPT
# =========================================

reassign_movies()