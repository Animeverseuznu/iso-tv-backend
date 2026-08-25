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
