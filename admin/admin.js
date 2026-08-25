const API = "https://iso-tv-backend.fastapicloud.dev";
const ADMIN_ID = "8829101708";

let movies = [];

async function api(url, options = {}) {

    options.headers = {
        "Content-Type": "application/json",
        "x-admin-id": ADMIN_ID,
        ...(options.headers || {})
    };

    const response = await fetch(API + url, options);

    if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `HTTP ${response.status}`);
    }

    return response.json();
}

async function loadMovies() {

    try {
        movies = await api("/api/movies");

        updateStats();
        renderMovies(movies);

    } catch (error) {

        alert("API xatosi:\n" + error.message);
        console.error(error);
    }
}

function updateStats() {

    document.getElementById("totalMovies").textContent =
        movies.length;

    document.getElementById("vipMovies").textContent =
        movies.filter(movie => movie.is_vip).length;
}

function renderMovies(list) {

    const box = document.getElementById("movieList");

    box.innerHTML = "";

    if (!list.length) {
        box.innerHTML =
            `<p style="color:#777">Kino topilmadi.</p>`;
        return;
    }

    list.forEach(movie => {

        const item = document.createElement("div");

        item.className = "movie";

        item.innerHTML = `
            <div class="movie-title">
                ${escapeHtml(movie.title)}
                ${movie.is_vip ? " 👑" : ""}
            </div>

            <div class="movie-meta">
                ID: ${movie.id}
                • ${escapeHtml(movie.genre || "")}
                • ${movie.year || ""}
                • ⭐ ${movie.rating || 0}
                • ${escapeHtml(movie.quality || "")}
            </div>

            <button onclick="editMovie(${movie.id})">
                ✏️ Tahrirlash
            </button>

            <button class="delete"
                    onclick="deleteMovie(${movie.id})">
                🗑️ O‘chirish
            </button>
        `;

        box.appendChild(item);
    });
}

async function saveMovie() {

    const data = {
        title: document.getElementById("title").value.trim(),
        genre: document.getElementById("genre").value.trim(),
        year: Number(document.getElementById("year").value),
        rating: Number(document.getElementById("rating").value || 0),
        quality:
            document.getElementById("quality").value.trim() || "HD",
        description:
            document.getElementById("description").value.trim(),
        poster:
            document.getElementById("poster").value.trim(),
        video_url:
            document.getElementById("video_url").value.trim(),
        is_vip:
            document.getElementById("is_vip").checked
    };

    if (!data.title) {
        alert("Kino nomini kiriting.");
        return;
    }

    if (!data.genre) {
        alert("Janrni kiriting.");
        return;
    }

    try {

        const id =
            document.getElementById("movieId").value;

        if (id) {

            await api(
                `/api/admin/movies/${id}`,
                {
                    method: "PUT",
                    body: JSON.stringify(data)
                }
            );

            alert("✅ Kino yangilandi.");

        } else {

            await api(
                "/api/admin/movies",
                {
                    method: "POST",
                    body: JSON.stringify(data)
                }
            );

            alert("✅ Kino qo‘shildi.");
        }

        resetForm();
        await loadMovies();

    } catch (error) {

        alert("Saqlashda xato:\n" + error.message);
        console.error(error);
    }
}

function editMovie(id) {

    const movie =
        movies.find(item => item.id === id);

    if (!movie) return;

    document.getElementById("movieId").value = movie.id;
    document.getElementById("title").value = movie.title || "";
    document.getElementById("genre").value = movie.genre || "";
    document.getElementById("year").value = movie.year || "";
    document.getElementById("rating").value = movie.rating || "";
    document.getElementById("quality").value = movie.quality || "";
    document.getElementById("description").value =
        movie.description || "";
    document.getElementById("poster").value =
        movie.poster || "";
    document.getElementById("video_url").value =
        movie.video_url || "";
    document.getElementById("is_vip").checked =
        Boolean(movie.is_vip);

    document.getElementById("formTitle").textContent =
        "✏️ Kino tahrirlash";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}

async function deleteMovie(id) {

    const movie =
        movies.find(item => item.id === id);

    if (!movie) return;

    if (!confirm(
        `"${movie.title}" filmini o‘chirishni tasdiqlaysizmi?`
    )) {
        return;
    }

    try {

        await api(
            `/api/admin/movies/${id}`,
            {
                method: "DELETE"
            }
        );

        await loadMovies();

    } catch (error) {

        alert("O‘chirishda xato:\n" + error.message);
        console.error(error);
    }
}

function resetForm() {

    document.getElementById("movieId").value = "";

    [
        "title",
        "genre",
        "year",
        "rating",
        "quality",
        "description",
        "poster",
        "video_url"
    ].forEach(id => {
        document.getElementById(id).value = "";
    });

    document.getElementById("is_vip").checked = false;

    document.getElementById("formTitle").textContent =
        "🎬 Kino qo‘shish";
}

function filterMovies() {

    const value =
        document.getElementById("search")
            .value
            .trim()
            .toLowerCase();

    if (!value) {
        renderMovies(movies);
        return;
    }

    renderMovies(
        movies.filter(movie =>
            String(movie.title || "")
                .toLowerCase()
                .includes(value)
        )
    );
}

function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

loadMovies();
