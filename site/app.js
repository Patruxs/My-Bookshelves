/**
 * 📚 My Bookshelves — Frontend Application
 * Reads data.json and renders an interactive book gallery.
 */

// ===== CONFIG =====
const CONFIG = {
  githubRepo: "Sora0977/My-Bookshelves",
  branch: "main",
};

// ===== STATE =====
let allBooks = [];
let filteredBooks = [];
let currentSort = null;
let sidebarSelection = { category: "", topic: "" };

// ===== DOM ELEMENTS =====
const $ = (sel) => document.querySelector(sel);
const bookGrid = $("#book-grid");
const loadingSkeleton = $("#loading-skeleton");
const noResults = $("#no-results");
const searchInput = $("#search-input");
const filterFormat = $("#filter-format");
const sortAZ = $("#sort-az");
const sortZA = $("#sort-za");
const modal = $("#book-modal");

// ===== CATEGORY CONFIG =====
const categoryConfig = {
  "Computer Science Fundamentals": { badge: "badge-cs", dot: "dot-cs", icon: "💻" },
  "Software Engineering Disciplines": { badge: "badge-se", dot: "dot-se", icon: "⚙️" },
  "Career and Professional Development": { badge: "badge-career", dot: "dot-career", icon: "🚀" },
  "Miscellaneous": { badge: "badge-misc", dot: "dot-misc", icon: "📦" },
  "University Courses": { badge: "badge-uni", dot: "dot-uni", icon: "🎓" },
};

function getBadgeClass(category) {
  for (const [key, cfg] of Object.entries(categoryConfig)) {
    if (category.includes(key)) return cfg.badge;
  }
  return "badge-cs";
}

function getDotClass(category) {
  for (const [key, cfg] of Object.entries(categoryConfig)) {
    if (category.includes(key)) return cfg.dot;
  }
  return "dot-cs";
}

function getCategoryIcon(category) {
  for (const [key, cfg] of Object.entries(categoryConfig)) {
    if (category.includes(key)) return cfg.icon;
  }
  return "📂";
}

// ===== INITIALIZATION =====
document.addEventListener("DOMContentLoaded", init);

async function init() {
  showLoadingSkeleton();
  try {
    const resp = await fetch("data.json");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    allBooks = await resp.json();
  } catch (err) {
    console.warn("Could not load data.json:", err);
    allBooks = [];
  }

  renderSidebar();
  updateStats();
  applyFilters();
  hideLoadingSkeleton();

  // Event listeners
  searchInput.addEventListener("input", debounce(applyFilters, 200));
  filterFormat.addEventListener("change", applyFilters);
  sortAZ.addEventListener("click", () => toggleSort("az"));
  sortZA.addEventListener("click", () => toggleSort("za"));

  // Sidebar toggle (mobile)
  $("#sidebar-toggle").addEventListener("click", toggleSidebar);

  // Keyboard shortcuts
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      searchInput.focus();
    }
    if (e.key === "Escape") closeModal();
  });
}

// ===== SIDEBAR =====
function renderSidebar() {
  const tree = buildCategoryTree();
  const container = $("#sidebar-tree");
  $("#sidebar-all-count").textContent = allBooks.length;

  let html = "";
  for (const [category, topics] of Object.entries(tree)) {
    const catCount = allBooks.filter((b) => b.category === category).length;
    const dotClass = getDotClass(category);
    const icon = getCategoryIcon(category);

    html += `
      <div class="sidebar-category-group">
        <button
          class="sidebar-category w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] font-medium text-slate-300"
          data-category="${escapeHtml(category)}"
          onclick="sidebarToggleCategory(this)"
        >
          <svg class="category-chevron w-3 h-3 text-slate-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
          <span class="text-base flex-shrink-0">${icon}</span>
          <span class="truncate flex-1 text-left">${escapeHtml(category)}</span>
          <span class="text-[11px] text-slate-600 flex-shrink-0">${catCount}</span>
        </button>
        <div class="topic-list pl-4" data-category="${escapeHtml(category)}">`;

    for (const [topic, count] of Object.entries(topics)) {
      html += `
          <button
            class="sidebar-topic w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] text-slate-500"
            data-category="${escapeHtml(category)}"
            data-topic="${escapeHtml(topic)}"
            onclick="sidebarSelectTopic(this)"
          >
            <span class="w-1.5 h-1.5 rounded-full ${dotClass} opacity-40 flex-shrink-0"></span>
            <span class="truncate flex-1 text-left">${escapeHtml(topic)}</span>
            <span class="text-[11px] text-slate-600 flex-shrink-0">${count}</span>
          </button>`;
    }

    html += `
        </div>
      </div>`;
  }

  container.innerHTML = html;
}

function buildCategoryTree() {
  const tree = {};
  for (const book of allBooks) {
    if (!tree[book.category]) tree[book.category] = {};
    if (!tree[book.category][book.topic]) tree[book.category][book.topic] = 0;
    tree[book.category][book.topic]++;
  }
  return tree;
}

function sidebarToggleCategory(btn) {
  const category = btn.dataset.category;
  const chevron = btn.querySelector(".category-chevron");
  const topicList = btn.nextElementSibling;

  // If clicking the already-selected category, toggle expand/collapse
  if (sidebarSelection.category === category && !sidebarSelection.topic) {
    chevron.classList.toggle("open");
    topicList.classList.toggle("open");
    return;
  }

  // Select this category
  sidebarSelection = { category, topic: "" };
  updateSidebarActive();

  // Expand this category's topics
  chevron.classList.add("open");
  topicList.classList.add("open");

  applyFilters();
}

function sidebarSelectTopic(btn) {
  const category = btn.dataset.category;
  const topic = btn.dataset.topic;

  sidebarSelection = { category, topic };
  updateSidebarActive();
  applyFilters();
}

function sidebarSelectAll() {
  sidebarSelection = { category: "", topic: "" };
  updateSidebarActive();
  applyFilters();
}

function clearAllFilters() {
  searchInput.value = "";
  filterFormat.value = "";
  currentSort = null;
  sortAZ.classList.remove("active");
  sortZA.classList.remove("active");
  sidebarSelectAll();
}

function updateSidebarActive() {
  // All button
  const allBtn = $("#sidebar-all");
  allBtn.classList.toggle("active", !sidebarSelection.category);

  // Category buttons
  document.querySelectorAll(".sidebar-category").forEach((btn) => {
    const isActive = btn.dataset.category === sidebarSelection.category;
    btn.classList.toggle("active", isActive && !sidebarSelection.topic);
  });

  // Topic buttons
  document.querySelectorAll(".sidebar-topic").forEach((btn) => {
    const isActive =
      btn.dataset.category === sidebarSelection.category &&
      btn.dataset.topic === sidebarSelection.topic;
    btn.classList.toggle("active", isActive);
  });

  // Close sidebar on mobile after selection
  if (window.innerWidth < 1024) {
    closeSidebar();
  }
}

function collapseAllCategories() {
  document.querySelectorAll(".category-chevron").forEach((c) => c.classList.remove("open"));
  document.querySelectorAll(".topic-list").forEach((t) => t.classList.remove("open"));
}

function toggleSidebar() {
  const sidebar = $("#sidebar");
  const overlay = $("#sidebar-overlay");
  sidebar.classList.toggle("open");
  overlay.classList.toggle("active");
}

function closeSidebar() {
  $("#sidebar").classList.remove("open");
  $("#sidebar-overlay").classList.remove("active");
}

// ===== LOADING SKELETON =====
function showLoadingSkeleton() {
  let skeletons = "";
  for (let i = 0; i < 10; i++) {
    skeletons += `
        <div class="rounded-2xl overflow-hidden glass border border-slate-700/20">
            <div class="aspect-[3/4] shimmer"></div>
            <div class="p-3">
                <div class="h-3 shimmer rounded mb-2 w-3/4"></div>
                <div class="h-2.5 shimmer rounded w-1/2"></div>
            </div>
        </div>`;
  }
  loadingSkeleton.innerHTML = skeletons;
  loadingSkeleton.style.display = "grid";
}

function hideLoadingSkeleton() {
  loadingSkeleton.style.display = "none";
  bookGrid.style.display = "grid";
}

// ===== UPDATE STATS =====
function updateStats() {
  const categories = new Set(allBooks.map((b) => b.category));
  const topics = new Set(allBooks.map((b) => b.topic));

  animateNumber($("#stat-total"), allBooks.length);
  animateNumber($("#stat-categories"), categories.size);
  animateNumber($("#stat-topics"), topics.size);
}

function animateNumber(el, target) {
  const duration = 800;
  const start = performance.now();

  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(target * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ===== FILTER & SORT =====
function applyFilters() {
  const query = searchInput.value.toLowerCase().trim();
  const formatFilter = filterFormat.value;
  const { category: catFilter, topic: topicFilter } = sidebarSelection;

  filteredBooks = allBooks.filter((book) => {
    const matchSearch = !query || book.title.toLowerCase().includes(query);
    const matchCat = !catFilter || book.category === catFilter;
    const matchTopic = !topicFilter || book.topic === topicFilter;
    const matchFormat = !formatFilter || book.format === formatFilter;
    return matchSearch && matchCat && matchTopic && matchFormat;
  });

  // Apply sort
  if (currentSort === "az") {
    filteredBooks.sort((a, b) => a.title.localeCompare(b.title));
  } else if (currentSort === "za") {
    filteredBooks.sort((a, b) => b.title.localeCompare(a.title));
  }

  renderBooks();
}

function toggleSort(dir) {
  if (currentSort === dir) {
    currentSort = null;
    sortAZ.classList.remove("active");
    sortZA.classList.remove("active");
  } else {
    currentSort = dir;
    sortAZ.classList.toggle("active", dir === "az");
    sortZA.classList.toggle("active", dir === "za");
  }
  applyFilters();
}

// ===== RENDER BOOKS =====
function renderBooks() {
  if (filteredBooks.length === 0) {
    bookGrid.innerHTML = "";
    noResults.classList.add("visible");
    $("#shown-count").textContent = "0";
    return;
  }

  noResults.classList.remove("visible");
  $("#shown-count").textContent = filteredBooks.length;

  const html = filteredBooks
    .map((book, i) => {
      const badgeClass = getBadgeClass(book.category);
      const delay = Math.min(i * 40, 400);
      const coverSrc =
        book.cover ||
        "data:image/svg+xml," +
          encodeURIComponent(generatePlaceholderSVG(book.title));

      return `
        <div class="book-card glass rounded-2xl overflow-hidden border border-slate-700/20 animate-fade-in"
             style="animation-delay: ${delay}ms"
             onclick="openModal(${i})"
             role="button"
             tabindex="0"
             aria-label="View details for ${escapeHtml(book.title)}">
            <div class="book-cover">
                <img src="${escapeHtml(coverSrc)}"
                     alt="${escapeHtml(book.title)}"
                     loading="lazy"
                     onerror="this.src='data:image/svg+xml,${encodeURIComponent(generatePlaceholderSVG(book.title))}'">
                <div class="book-cover-overlay">
                    <span class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/10 backdrop-blur-sm rounded-full text-xs font-medium text-white border border-white/10">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                        View
                    </span>
                </div>
            </div>
            <div class="p-3">
                <h3 class="text-[13px] font-semibold text-slate-200 leading-snug mb-1.5 line-clamp-2">${escapeHtml(book.title)}</h3>
                <span class="${badgeClass} inline-block px-2 py-0.5 rounded-md text-[10px] font-medium">${escapeHtml(book.topic)}</span>
            </div>
        </div>`;
    })
    .join("");

  bookGrid.innerHTML = html;
}

// ===== PLACEHOLDER SVG =====
function generatePlaceholderSVG(title) {
  const colors = ["0ea5e9", "d946ef", "34d399", "f59e0b", "f472b6", "a78bfa"];
  const color = colors[Math.abs(hashCode(title)) % colors.length];
  const initials = title
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400" fill="none">
        <rect width="300" height="400" fill="#0f172a"/>
        <rect x="20" y="20" width="260" height="360" rx="12" fill="#1e293b" stroke="#${color}" stroke-width="2" stroke-opacity="0.3"/>
        <rect x="20" y="20" width="260" height="120" rx="12" fill="#${color}" fill-opacity="0.1"/>
        <text x="150" y="200" text-anchor="middle" fill="#${color}" font-size="64" font-family="system-ui" font-weight="700">${initials}</text>
        <text x="150" y="320" text-anchor="middle" fill="#94a3b8" font-size="14" font-family="system-ui" font-weight="400">
            <tspan x="150">${escapeXml(title.substring(0, 25))}</tspan>
            ${title.length > 25 ? `<tspan x="150" dy="20">${escapeXml(title.substring(25, 50))}...</tspan>` : ""}
        </text>
    </svg>`;
}

// ===== MODAL =====
function openModal(index) {
  const book = filteredBooks[index];
  if (!book) return;

  const coverSrc =
    book.cover ||
    "data:image/svg+xml," +
      encodeURIComponent(generatePlaceholderSVG(book.title));
  const badgeClass = getBadgeClass(book.category);

  $("#modal-cover").src = coverSrc;
  $("#modal-cover").alt = book.title;
  $("#modal-title").textContent = book.title;
  $("#modal-category").className =
    `inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${badgeClass}`;
  $("#modal-category").textContent = book.category;
  $("#modal-topic").textContent = book.topic;
  $("#modal-format").textContent = book.format.toUpperCase();
  $("#modal-description").textContent =
    book.description ||
    `A book in the "${book.topic}" topic of "${book.category}".`;
  $("#modal-download").href = getDownloadUrl(book.file_path);
  $("#modal-download").setAttribute("download", "");

  modal.classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  modal.classList.remove("active");
  document.body.style.overflow = "";
}

// ===== DOWNLOAD URL RESOLVER =====
function getDownloadUrl(filePath) {
  const isLocal =
    location.hostname === "localhost" ||
    location.hostname === "127.0.0.1" ||
    location.protocol === "file:";

  if (isLocal) {
    return "../" + encodeURI(filePath);
  }

  const { githubRepo, branch } = CONFIG;
  return `https://raw.githubusercontent.com/${githubRepo}/${branch}/${encodeURI(filePath)}`;
}

// ===== UTILITIES =====
function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function escapeXml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return hash;
}
