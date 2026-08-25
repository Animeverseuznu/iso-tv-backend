import os
import sqlite3
from contextlib import closing

from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


DB = "iso_tv.db"
ADMIN_ID = 8829101708

app = FastAPI(title="ISO TV API")
app.mount("/admin", StaticFiles(directory="admin", html=True), name="admin")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# MODELS
# =========================

class Movie(BaseModel):
    title: str
    genre: str
    year: int
    rating: float = 0
    quality: str = "HD"
    description: str = ""
    poster: str = ""
    video_url: str = ""
    is_vip: bool = False


# =========================
# DATABASE
# =========================

def init_db():

    with closing(sqlite3.connect(DB)) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                genre TEXT NOT NULL,
                year INTEGER,
                rating REAL DEFAULT 0,
                quality TEXT DEFAULT 'HD',
                description TEXT DEFAULT '',
                poster TEXT DEFAULT '',
                video_url TEXT DEFAULT '',
                is_vip INTEGER DEFAULT 0
            )
        """)

        conn.commit()


@app.on_event("startup")
def startup():
    init_db()


# =========================
# ADMIN CHECK
# =========================

def check_admin(x_admin_id):

    if x_admin_id is None:
        raise HTTPException(
            status_code=401,
            detail="Admin ID kerak"
        )

    try:
        user_id = int(x_admin_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Admin ID noto‘g‘ri"
        )

    if user_id != ADMIN_ID:
        raise HTTPException(
            status_code=403,
            detail="Ruxsat berilmagan"
        )


# =========================
# HOME
# =========================

@app.get("/")
def home():

    return {
        "status": "ok",
        "service": "ISO TV API",
        "version": "1.0"
    }


# =========================
# GET MOVIES
# =========================

@app.get("/api/movies")
def get_movies():

    with closing(sqlite3.connect(DB)) as conn:

        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT *
            FROM movies
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


# =========================
# GET SINGLE MOVIE
# =========================

@app.get("/api/movies/{movie_id}")
def get_movie(movie_id: int):

    with closing(sqlite3.connect(DB)) as conn:

        conn.row_factory = sqlite3.Row

        row = conn.execute(
            """
            SELECT *
            FROM movies
            WHERE id = ?
            """,
            (movie_id,)
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Kino topilmadi"
            )

        return dict(row)


# =========================
# ADD MOVIE
# =========================

@app.post("/api/admin/movies")
def add_movie(
    movie: Movie,
    x_admin_id: str | None = Header(default=None)
):

    check_admin(x_admin_id)

    with closing(sqlite3.connect(DB)) as conn:

        cursor = conn.execute(
            """
            INSERT INTO movies
            (
                title,
                genre,
                year,
                rating,
                quality,
                description,
                poster,
                video_url,
                is_vip
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                movie.title,
                movie.genre,
                movie.year,
                movie.rating,
                movie.quality,
                movie.description,
                movie.poster,
                movie.video_url,
                int(movie.is_vip)
            )
        )

        conn.commit()

        return {
            "success": True,
            "id": cursor.lastrowid,
            "message": "Kino qo‘shildi"
        }


# =========================
# DELETE MOVIE
# =========================

@app.delete("/api/admin/movies/{movie_id}")
def delete_movie(
    movie_id: int,
    x_admin_id: str | None = Header(default=None)
):

    check_admin(x_admin_id)

    with closing(sqlite3.connect(DB)) as conn:

        cursor = conn.execute(
            """
            DELETE FROM movies
            WHERE id = ?
            """,
            (movie_id,)
        )

        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Kino topilmadi"
            )

        return {
            "success": True,
            "message": "Kino o‘chirildi"
        }


# =========================
# UPDATE MOVIE
# =========================

@app.put("/api/admin/movies/{movie_id}")
def update_movie(
    movie_id: int,
    movie: Movie,
    x_admin_id: str | None = Header(default=None)
):

    check_admin(x_admin_id)

    with closing(sqlite3.connect(DB)) as conn:

        cursor = conn.execute(
            """
            UPDATE movies
            SET
                title = ?,
                genre = ?,
                year = ?,
                rating = ?,
                quality = ?,
                description = ?,
                poster = ?,
                video_url = ?,
                is_vip = ?
            WHERE id = ?
            """,
            (
                movie.title,
                movie.genre,
                movie.year,
                movie.rating,
                movie.quality,
                movie.description,
                movie.poster,
                movie.video_url,
                int(movie.is_vip),
                movie_id
            )
        )

        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Kino topilmadi"
            )

        return {
            "success": True,
            "message": "Kino yangilandi"
        }


# =========================
# ADMIN V2 - STATISTICS
# =========================

@app.get("/api/admin/stats")
def admin_stats(
    x_admin_id: str | None = Header(default=None)
):
    check_admin(x_admin_id)

    with closing(sqlite3.connect(DB)) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM movies"
        ).fetchone()[0]

        vip = conn.execute(
            "SELECT COUNT(*) FROM movies WHERE is_vip = 1"
        ).fetchone()[0]

        average_rating = conn.execute(
            "SELECT COALESCE(AVG(rating), 0) FROM movies"
        ).fetchone()[0]

        genres = conn.execute("""
            SELECT genre, COUNT(*) AS count
            FROM movies
            GROUP BY genre
            ORDER BY count DESC
        """).fetchall()

        return {
            "total": total,
            "vip": vip,
            "free": total - vip,
            "average_rating": round(average_rating, 1),
            "genres": [
                {
                    "genre": row[0],
                    "count": row[1]
                }
                for row in genres
            ]
        }


# =========================
# ADMIN V2 - SEARCH
# =========================

@app.get("/api/admin/movies/search")
def search_admin_movies(
    q: str = "",
    genre: str = "",
    vip: int | None = None,
    x_admin_id: str | None = Header(default=None)
):
    check_admin(x_admin_id)

    query = """
        SELECT *
        FROM movies
        WHERE 1 = 1
    """

    params = []

    if q:
        query += """
            AND (
                title LIKE ?
                OR description LIKE ?
            )
        """
        value = f"%{q}%"
        params.extend([value, value])

    if genre:
        query += " AND genre = ?"
        params.append(genre)

    if vip is not None:
        query += " AND is_vip = ?"
        params.append(vip)

    query += " ORDER BY id DESC"

    with closing(sqlite3.connect(DB)) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            query,
            params
        ).fetchall()

        return [dict(row) for row in rows]


# =========================
# ADMIN V2 - GENRES
# =========================

@app.get("/api/admin/genres")
def admin_genres(
    x_admin_id: str | None = Header(default=None)
):
    check_admin(x_admin_id)

    with closing(sqlite3.connect(DB)) as conn:
        rows = conn.execute("""
            SELECT genre, COUNT(*) AS count
            FROM movies
            GROUP BY genre
            ORDER BY genre ASC
        """).fetchall()

        return [
            {
                "genre": row[0],
                "count": row[1]
            }
            for row in rows
        ]

# =========================
# VIP V11
# =========================

from datetime import datetime, timedelta, timezone
from fastapi import Request


def init_vip_db():

    with closing(sqlite3.connect(DB)) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                plan TEXT NOT NULL,
                starts_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                payment_id TEXT DEFAULT ''
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                plan TEXT NOT NULL,
                stars INTEGER NOT NULL,
                payload TEXT NOT NULL,
                payment_id TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()


@app.on_event("startup")
def startup_v11():

    init_vip_db()


# =========================
# VIP PLANS
# =========================

VIP_PLANS = {
    "monthly": {
        "name": "VIP 30 kun",
        "days": 30,
        "stars": 150
    }
}


# =========================
# VIP STATUS
# =========================

@app.get("/api/vip/status/{telegram_id}")
def vip_status(telegram_id: int):

    now = datetime.now(timezone.utc)

    with closing(sqlite3.connect(DB)) as conn:

        row = conn.execute("""
            SELECT *
            FROM subscriptions
            WHERE telegram_id = ?
              AND status = 'active'
            ORDER BY expires_at DESC
            LIMIT 1
        """, (telegram_id,)).fetchone()

        if not row:

            return {
                "vip": False,
                "expires_at": None
            }

        expires_at = datetime.fromisoformat(row[4])

        if expires_at <= now:

            conn.execute("""
                UPDATE subscriptions
                SET status = 'expired'
                WHERE id = ?
            """, (row[0],))

            conn.commit()

            return {
                "vip": False,
                "expires_at": None
            }

        return {
            "vip": True,
            "plan": row[2],
            "expires_at": row[4]
        }


# =========================
# WATCH ACCESS
# =========================

@app.get("/api/movies/{movie_id}/watch/{telegram_id}")
def watch_movie(
    movie_id: int,
    telegram_id: int
):

    with closing(sqlite3.connect(DB)) as conn:

        conn.row_factory = sqlite3.Row

        movie = conn.execute("""
            SELECT *
            FROM movies
            WHERE id = ?
        """, (movie_id,)).fetchone()

        if not movie:

            raise HTTPException(
                status_code=404,
                detail="Kino topilmadi"
            )

        movie = dict(movie)

    if movie["is_vip"]:

        status = vip_status(telegram_id)

        if not status["vip"]:

            raise HTTPException(
                status_code=403,
                detail="VIP obuna kerak"
            )

    if not movie["video_url"]:

        raise HTTPException(
            status_code=404,
            detail="Video mavjud emas"
        )

    return {
        "success": True,
        "movie_id": movie_id,
        "video_url": movie["video_url"]
    }
