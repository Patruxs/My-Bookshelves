/**
 * My Bookshelves — App Logic
 * Zero dependencies · Pure JavaScript
 */

// ═══ CONFIG ═══
const CONFIG = { githubRepo: "Patruxs/My-Bookshelves", branch: "main" };

// ═══ STATE ═══
let allBooks = [], filteredBooks = [], currentSort = null, currentBookId = null;
let sidebarSelection = { category: "", topic: "" };
let currentPage = 1;
const BOOKS_PER_PAGE = 15;

// ═══ DOM ═══
const $ = s => document.querySelector(s);
const grid = $("#grid"), skeleton = $("#skeleton"), noResults = $("#no-results");
const searchInput = $("#search"), filterFmt = $("#filter-fmt");
const modal = $("#modal"), paginationEl = $("#pagination");

// ═══ CATEGORY CONFIG ═══
const catMeta = {
    "Computer Science Fundamentals":       { icon: "💻", n: 1 },
    "Software Engineering Disciplines":    { icon: "⚙️", n: 2 },
    "Career and Professional Development": { icon: "🚀", n: 3 },
    "Miscellaneous":                       { icon: "📦", n: 4 },
    "University Courses":                  { icon: "🎓", n: 5 },
};
function getCatNum(cat) { for (const [k, v] of Object.entries(catMeta)) if (cat.includes(k)) return v.n; return 1; }
function getCatIcon(cat) { for (const [k, v] of Object.entries(catMeta)) if (cat.includes(k)) return v.icon; return "📂"; }

// ═══ THEME ═══
function initTheme() {
    const saved = localStorage.getItem("theme");
    const prefer = saved || (matchMedia("(prefers-color-scheme:light)").matches ? "light" : "dark");
    document.documentElement.setAttribute("data-theme", prefer);
}
function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
}
initTheme(); // Run immediately to prevent flash

// ═══ INIT ═══
document.addEventListener("DOMContentLoaded", init);

async function init() {
    showSkeleton();
    try {
        const r = await fetch("data.json");
        if (!r.ok) throw new Error(r.status);
        allBooks = await r.json();
    } catch (e) { console.warn("data.json:", e); allBooks = []; }

    renderSidebar();
    updateStats();
    applyFilters();
    hideSkeleton();

    searchInput.addEventListener("input", debounce(applyFilters, 200));
    filterFmt.addEventListener("change", applyFilters);
    $("#sort-az").addEventListener("click", () => toggleSort("az"));
    $("#sort-za").addEventListener("click", () => toggleSort("za"));

    document.addEventListener("keydown", e => {
        if ((e.ctrlKey || e.metaKey) && e.key === "k") { e.preventDefault(); searchInput.focus(); }
        if (e.key === "Escape") closeModal();
    });

    checkUrlBookParam();
}

// ═══ SIDEBAR ═══
function renderSidebar() {
    const tree = {};
    allBooks.forEach(b => {
        if (!tree[b.category]) tree[b.category] = {};
        if (!tree[b.category][b.topic]) tree[b.category][b.topic] = 0;
        tree[b.category][b.topic]++;
    });
    $("#sb-all-count").textContent = allBooks.length;

    let html = "";
    for (const [cat, topics] of Object.entries(tree)) {
        const count = allBooks.filter(b => b.category === cat).length;
        const n = getCatNum(cat);
        html += `<div>
            <button class="sb-cat" data-cat="${esc(cat)}" onclick="sidebarToggleCat(this)">
                <svg class="sb-chevron" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                <span class="sb-cat-icon">${getCatIcon(cat)}</span>
                <span class="sb-cat-name">${esc(cat)}</span>
                <span class="sb-cat-count">${count}</span>
            </button>
            <div class="sb-topics" data-cat="${esc(cat)}">`;
        for (const [topic, tc] of Object.entries(topics)) {
            html += `<button class="sb-topic" data-cat="${esc(cat)}" data-topic="${esc(topic)}" onclick="sidebarSelectTopic(this)">
                <span class="sb-topic-dot dot-${n}"></span>
                <span class="sb-topic-name">${esc(topic)}</span>
                <span class="sb-topic-count">${tc}</span>
            </button>`;
        }
        html += `</div></div>`;
    }
    $("#sb-tree").innerHTML = html;
}

function sidebarToggleCat(btn) {
    const cat = btn.dataset.cat;
    const chevron = btn.querySelector(".sb-chevron");
    const topics = btn.nextElementSibling;
    if (sidebarSelection.category === cat && !sidebarSelection.topic) {
        chevron.classList.toggle("open");
        topics.classList.toggle("open");
        return;
    }
    sidebarSelection = { category: cat, topic: "" };
    chevron.classList.add("open");
    topics.classList.add("open");
    updateSidebarUI();
    applyFilters();
}

function sidebarSelectTopic(btn) {
    sidebarSelection = { category: btn.dataset.cat, topic: btn.dataset.topic };
    updateSidebarUI();
    applyFilters();
}

function sidebarSelectAll() {
    sidebarSelection = { category: "", topic: "" };
    updateSidebarUI();
    applyFilters();
}

function clearAllFilters() {
    searchInput.value = "";
    filterFmt.value = "";
    currentSort = null;
    $("#sort-az").classList.remove("active");
    $("#sort-za").classList.remove("active");
    sidebarSelectAll();
}

function updateSidebarUI() {
    $("#sb-all").classList.toggle("active", !sidebarSelection.category);
    document.querySelectorAll(".sb-cat").forEach(b => {
        b.classList.toggle("active", b.dataset.cat === sidebarSelection.category && !sidebarSelection.topic);
    });
    document.querySelectorAll(".sb-topic").forEach(b => {
        b.classList.toggle("active", b.dataset.cat === sidebarSelection.category && b.dataset.topic === sidebarSelection.topic);
    });
    if (window.innerWidth < 1024) closeSidebar();
}

function collapseAllCategories() {
    document.querySelectorAll(".sb-chevron").forEach(c => c.classList.remove("open"));
    document.querySelectorAll(".sb-topics").forEach(t => t.classList.remove("open"));
}
function toggleSidebar() { $("#sidebar").classList.toggle("open"); $("#sb-overlay").classList.toggle("active"); }
function closeSidebar() { $("#sidebar").classList.remove("open"); $("#sb-overlay").classList.remove("active"); }

// ═══ SKELETON ═══
function showSkeleton() {
    let h = "";
    for (let i = 0; i < 12; i++) h += `<div class="skeleton"><div class="shimmer" style="aspect-ratio:3/4"></div><div style="padding:12px"><div class="shimmer" style="height:12px;border-radius:4px;margin-bottom:6px;width:80%"></div><div class="shimmer" style="height:10px;border-radius:4px;width:50%"></div></div></div>`;
    skeleton.innerHTML = h;
    skeleton.style.display = "grid";
}
function hideSkeleton() { skeleton.style.display = "none"; grid.style.display = "grid"; }

// ═══ STATS ═══
function updateStats() {
    const cats = new Set(allBooks.map(b => b.category));
    const tops = new Set(allBooks.map(b => b.topic));
    animNum($("#stat-total"), allBooks.length);
    animNum($("#stat-cats"), cats.size);
    animNum($("#stat-topics"), tops.size);
}
function animNum(el, target) {
    const start = performance.now(), dur = 600;
    (function step(now) {
        const p = Math.min((now - start) / dur, 1);
        el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(step);
    })(start);
}

// ═══ FILTER + SORT ═══
function applyFilters() {
    const q = searchInput.value.toLowerCase().trim();
    const fmt = filterFmt.value;
    const { category: cat, topic } = sidebarSelection;

    filteredBooks = allBooks.filter(b =>
        (!q || b.title.toLowerCase().includes(q)) &&
        (!cat || b.category === cat) &&
        (!topic || b.topic === topic) &&
        (!fmt || b.format === fmt)
    );

    if (currentSort === "az") filteredBooks.sort((a, b) => a.title.localeCompare(b.title));
    else if (currentSort === "za") filteredBooks.sort((a, b) => b.title.localeCompare(a.title));

    currentPage = 1;
    renderBooks();
    renderPagination();
}

function toggleSort(dir) {
    currentSort = currentSort === dir ? null : dir;
    $("#sort-az").classList.toggle("active", currentSort === "az");
    $("#sort-za").classList.toggle("active", currentSort === "za");
    applyFilters();
}

// ═══ RENDER BOOKS ═══
function renderBooks() {
    if (!filteredBooks.length) {
        grid.innerHTML = "";
        paginationEl.innerHTML = "";
        noResults.classList.add("visible");
        $("#shown-count").textContent = "0";
        return;
    }
    noResults.classList.remove("visible");
    $("#shown-count").textContent = filteredBooks.length;

    const start = (currentPage - 1) * BOOKS_PER_PAGE;
    const end = start + BOOKS_PER_PAGE;
    const pageBooks = filteredBooks.slice(start, end);

    grid.innerHTML = pageBooks.map((book, i) => {
        const globalIdx = start + i;
        const n = getCatNum(book.category);
        const delay = Math.min(i * 30, 300);
        const title = cleanTitle(book.title);
        const cover = book.cover || "data:image/svg+xml," + encodeURIComponent(placeholderSVG(title));
        return `<div class="card fade-in" style="animation-delay:${delay}ms" onclick="openModal(${globalIdx})" tabindex="0" role="button" aria-label="${esc(title)}">
            <div class="card-cover">
                <img src="${esc(cover)}" alt="${esc(title)}" loading="lazy" onerror="this.src='data:image/svg+xml,${encodeURIComponent(placeholderSVG(title))}'">
                <div class="card-overlay">
                    <span class="card-view"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>View</span>
                </div>
            </div>
            <div class="card-info">
                <div class="card-title">${esc(title)}</div>
                <span class="card-badge badge-${n}">${esc(book.topic)}</span>
            </div>
        </div>`;
    }).join("");
}

// ═══ PAGINATION ═══
function renderPagination() {
    const total = filteredBooks.length;
    const totalPages = Math.ceil(total / BOOKS_PER_PAGE);
    if (totalPages <= 1) { paginationEl.innerHTML = ""; return; }

    let html = '';
    // Prev arrow
    html += `<button class="page-btn page-arrow" ${currentPage===1?'disabled':''} onclick="goToPage(${currentPage-1})" title="Previous">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
    </button>`;

    // Page numbers with ellipsis
    const pages = getPageNumbers(currentPage, totalPages);
    pages.forEach(p => {
        if (p === '...') {
            html += `<span class="page-ellipsis">…</span>`;
        } else {
            html += `<button class="page-btn ${p===currentPage?'active':''}" onclick="goToPage(${p})">${p}</button>`;
        }
    });

    // Next arrow
    html += `<button class="page-btn page-arrow" ${currentPage===totalPages?'disabled':''} onclick="goToPage(${currentPage+1})" title="Next">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
    </button>`;

    // Page info
    const startItem = (currentPage - 1) * BOOKS_PER_PAGE + 1;
    const endItem = Math.min(currentPage * BOOKS_PER_PAGE, total);
    html += `<span class="page-info">${startItem}–${endItem} of ${total}</span>`;

    paginationEl.innerHTML = html;
}

function getPageNumbers(current, total) {
    if (total <= 7) return Array.from({length: total}, (_, i) => i + 1);
    const pages = [];
    pages.push(1);
    if (current > 3) pages.push('...');
    for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i);
    if (current < total - 2) pages.push('...');
    pages.push(total);
    return pages;
}

function goToPage(page) {
    const totalPages = Math.ceil(filteredBooks.length / BOOKS_PER_PAGE);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderBooks();
    renderPagination();
    // Scroll to top of grid area
    grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ═══ PLACEHOLDER SVG ═══
function placeholderSVG(title) {
    const colors = ["2997ff", "30d158", "ff9f0a", "ff375f", "bf5af2", "64d2ff"];
    const c = colors[Math.abs(hash(title)) % colors.length];
    const ini = title.split(" ").slice(0, 2).map(w => w[0]).join("").toUpperCase();
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400"><rect width="300" height="400" fill="#1c1c1e"/><rect x="16" y="16" width="268" height="368" rx="12" fill="#2c2c2e" stroke="#${c}" stroke-width="1.5" stroke-opacity="0.2"/><text x="150" y="200" text-anchor="middle" fill="#${c}" font-size="56" font-family="system-ui" font-weight="700">${ini}</text><text x="150" y="300" text-anchor="middle" fill="#a1a1a6" font-size="13" font-family="system-ui">${escXml(title.substring(0, 28))}</text></svg>`;
}

// ═══ MODAL ═══
function openModal(i) {
    const b = filteredBooks[i];
    if (!b) return;
    const cover = b.cover || "data:image/svg+xml," + encodeURIComponent(placeholderSVG(b.title));
    const n = getCatNum(b.category);

    $("#m-cover").src = cover;
    $("#m-title").textContent = cleanTitle(b.title);
    $("#m-cat").textContent = b.category;
    $("#m-cat").className = `modal-tag badge-${n}`;
    $("#m-topic").textContent = b.topic;
    $("#m-fmt").textContent = b.format.toUpperCase();
    $("#m-desc").textContent = b.description || `A book in "${b.topic}" of "${b.category}".`;
    $("#m-dl").href = getDownloadUrl(b.file_path, b.download_url);
    currentBookId = b.id;

    modal.classList.add("active");
    document.body.style.overflow = "hidden";
}

function openModalById(id) {
    const b = allBooks.find(x => x.id === id);
    if (!b) return;
    if (!filteredBooks.includes(b)) clearAllFilters();
    const i = filteredBooks.indexOf(b);
    if (i !== -1) openModal(i);
}

function closeModal() {
    modal.classList.remove("active");
    document.body.style.overflow = "";
    currentBookId = null;
    const u = new URL(location);
    if (u.searchParams.has("book")) { u.searchParams.delete("book"); history.replaceState(null, "", u); }
}

// ═══ SHARE ═══
function shareBook() {
    if (!currentBookId) return;
    const u = new URL(location);
    u.searchParams.set("book", currentBookId);
    navigator.clipboard.writeText(u.toString())
        .then(() => showToast("Link copied to clipboard!"))
        .catch(() => {
            const inp = document.createElement("input"); inp.value = u.toString();
            document.body.appendChild(inp); inp.select(); document.execCommand("copy");
            document.body.removeChild(inp); showToast("Link copied to clipboard!");
        });
}

function checkUrlBookParam() {
    const id = new URLSearchParams(location.search).get("book");
    if (id) requestAnimationFrame(() => openModalById(id));
}

function showToast(msg) {
    $("#toast-msg").textContent = msg;
    const t = $("#toast"); t.classList.add("show");
    setTimeout(() => t.classList.remove("show"), 2500);
}

// ═══ DOWNLOAD URL ═══
function getDownloadUrl(fp, downloadUrl) {
    // Priority 1: GitHub Releases URL (from upload_releases.py)
    if (downloadUrl) return downloadUrl;
    // Priority 2: Local development
    const local = location.hostname === "localhost" || location.hostname === "127.0.0.1" || location.protocol === "file:";
    if (local) return "../" + encodeURI(fp);
    // Priority 3: Raw GitHub (fallback)
    return `https://raw.githubusercontent.com/${CONFIG.githubRepo}/${CONFIG.branch}/${encodeURI(fp)}`;
}

// ═══ UTILS ═══
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
function escXml(s) { return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
function hash(s) { let h = 0; for (let i = 0; i < s.length; i++) { h = (h << 5) - h + s.charCodeAt(i); h |= 0; } return h; }
function cleanTitle(t) {
    return t.replace(/[-_]/g, " ").replace(/\s+/g, " ").trim()
        .replace(/\w\S*/g, (w, i) => {
            const lower = ["a","an","the","and","or","but","in","on","of","to","for","with","by","at","from","as","is"];
            return (i > 0 && lower.includes(w.toLowerCase())) ? w.toLowerCase() : w.charAt(0).toUpperCase() + w.slice(1);
        });
}
