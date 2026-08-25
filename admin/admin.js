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
        throw new Error(await response.text());
    }

    return response.json();
}


function toast(message) {

    const box = document.getElementById("toast");

    box.textContent = message;
    box.classList.add("show");

    setTimeout(() => {
        box.classList.remove("show");
    }, 2200);
}


async function loadDashboard() {

    try {

        const stats =
            await api("/api/admin/stats");

        document.getElementById("totalMovies").textContent =
            stats.total;

        document.getElementById("vipMovies").textContent =
            stats.vip;

        document.getElementById("freeMovies").textContent =
            stats.free;

        document.getElementById("averageRating").textContent =
            stats.average_rating;

        loadGenres(stats.genres);

        await loadMovies();

        toast("✓ Yangilandi");

    } catch (error) {

        alert("Dashboard xatosi:\n" + error.message);
    }
}


async function loadMovies() {

    try {

        movies = await api("/api/movies");

        renderMovies(movies);

        document.getElementById("movieCount").textContent =
            `${movies.length} ta kino`;

    } catch (error) {

        alert("Kinolarni yuklashda xato:\n" + error.message);
    }
}


function loadGenres(genres) {

    const select =
        document.getElementById("genreFilter");

    select.innerHTML =
        `<option value="">Barcha janrlar</option>`;

    genres.forEach(item => {

        const option =
            document.createElement("option");

        option.value = item.genre;
        option.textContent =
            `${item.genre} (${item.count})`;

        select.appendChild(option);
    });
}


function renderMovies(list) {

    const box =
        document.getElementById("movieList");

    box.innerHTML = "";

    if (!list.length) {

        box.innerHTML =
            `<p style="padding:20px;text-align:center">
                🎬 Kino topilmadi
            </p>`;

        return;
    }

    list.forEach(movie => {

        const item =
            document.createElement("div");

        item.className = "movie";

        item.innerHTML = `
            <div class="movie-title">
                ${escapeHtml(movie.title)}

                ${
                    movie.is_vip
                    ? `<span class="badge">VIP</span>`
                    : ""
                }
            </div>

            <div class="movie-meta">
                ID ${movie.id}
                • ${escapeHtml(movie.genre)}
                • ${movie.year}
                • ⭐ ${movie.rating}
                • ${escapeHtml(movie.quality)}
            </div>

            <div class="movie-actions">

                <button onclick="editMovie(${movie.id})">
                    ✏️ Tahrirlash
                </button>

                <button class="delete"
                        onclick="deleteMovie(${movie.id})">
                    🗑 O‘chirish
                </button>

            </div>
        `;

        box.appendChild(item);
    });
}


function filterMovies() {

    const search =
        document.getElementById("search")
            .value
            .trim()
            .toLowerCase();

    const genre =
        document.getElementById("genreFilter").value;

    const vip =
        document.getElementById("vipFilter").value;

    const result =
        movies.filter(movie => {

            const title =
                String(movie.title || "")
                    .toLowerCase();

            const matchSearch =
                !search ||
                title.includes(search);

            const matchGenre =
                !genre ||
                movie.genre === genre;

            const matchVip =
                vip === "" ||
                String(Number(movie.is_vip)) === vip;

            return (
                matchSearch &&
                matchGenre &&
                matchVip
            );
        });

    renderMovies(result);
}


async function saveMovie() {

    const data = {

        title:
            document.getElementById("title")
                .value.trim(),

        genre:
            document.getElementById("genre")
                .value.trim(),

        year:
            Number(
                document.getElementById("year")
                    .value
            ),

        rating:
            Number(
                document.getElementById("rating")
                    .value || 0
            ),

        quality:
            document.getElementById("quality")
                .value.trim() || "HD",

        description:
            document.getElementById("description")
                .value.trim(),

        poster:
            document.getElementById("poster")
                .value.trim(),

        video_url:
            document.getElementById("video_url")
                .value.trim(),

        is_vip:
            document.getElementById("is_vip")
                .checked
    };


    if (!data.title || !data.genre) {

        alert("Kino nomi va janrini kiriting.");
        return;
    }


    try {

        const id =
            document.getElementById("movieId")
                .value;

        if (id) {

            await api(
                `/api/admin/movies/${id}`,
                {
                    method: "PUT",
                    body: JSON.stringify(data)
                }
            );

            toast("✓ Kino yangilandi");

        } else {

            await api(
                "/api/admin/movies",
                {
                    method: "POST",
                    body: JSON.stringify(data)
                }
            );

            toast("✓ Kino qo‘shildi");
        }

        resetForm();

        await loadDashboard();

    } catch (error) {

        alert("Saqlashda xato:\n" + error.message);
    }
}


function editMovie(id) {

    const movie =
        movies.find(item => item.id === id);

    if (!movie) return;

    document.getElementById("movieId").value =
        movie.id;

    document.getElementById("title").value =
        movie.title || "";

    document.getElementById("genre").value =
        movie.genre || "";

    document.getElementById("year").value =
        movie.year || "";

    document.getElementById("rating").value =
        movie.rating || "";

    document.getElementById("quality").value =
        movie.quality || "";

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

        toast("✓ Kino o‘chirildi");

        await loadDashboard();

    } catch (error) {

        alert("O‘chirishda xato:\n" + error.message);
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


function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


loadDashboard();
