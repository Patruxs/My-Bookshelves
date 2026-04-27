/**
 * My Bookshelves — App Logic (SPA Detail View)
 * Zero dependencies · Pure JavaScript · Apple-style UI
 */

// ═══ CONFIG ═══
const CONFIG = { githubRepo: "Patruxs/My-Bookshelves", branch: "main" };

// ═══ STATE ═══
let allBooks = [], filteredBooks = [], currentBookId = null;
let activeFilters = { sort: null, format: null, category: new Set(), topic: new Set() };
let pendingFilters = { sort: null, format: null, category: new Set(), topic: new Set() };
let viewMode = localStorage.getItem("viewMode") || "grid";

function copyFilters(source) {
    return {
        sort: source.sort,
        format: source.format,
        category: new Set(source.category),
        topic: new Set(source.topic)
    };
}
let sidebarSelection = { category: "", topic: "" };
let sidebarViewMode = 'collections'; // 'discover' | 'collections' | 'archive' | 'recent'
let isGlobalSearch = false;
let currentPage = 1;
let booksPerPage = 16;
let savedScrollPos = 0;
let categoriesCollapsed = false;

// ═══ RECENT & ARCHIVE (localStorage) ═══
function getRecentBooks() {
    try { return JSON.parse(localStorage.getItem('recentBooks') || '[]'); } catch { return []; }
}
function addRecentBook(bookId) {
    let recent = getRecentBooks().filter(id => id !== bookId);
    recent.unshift(bookId);
    if (recent.length > 50) recent = recent.slice(0, 50);
    localStorage.setItem('recentBooks', JSON.stringify(recent));
}
function getArchivedBooks() {
    try { return JSON.parse(localStorage.getItem('archivedBooks') || '[]'); } catch { return []; }
}
function addArchivedBook(bookId) {
    let archived = getArchivedBooks();
    if (!archived.includes(bookId)) {
        archived.unshift(bookId);
        localStorage.setItem('archivedBooks', JSON.stringify(archived));
    }
}
function removeArchivedBook(bookId) {
    let archived = getArchivedBooks().filter(id => id !== bookId);
    localStorage.setItem('archivedBooks', JSON.stringify(archived));
}

// ═══ DYNAMIC PAGINATION ═══
const MIN_BOOKS = 30;
function calculateBooksPerPage() {
    const vw = window.innerWidth / 100;
    // Mirror CSS grid: clamp(150px, 12vw, 240px)
    const minColW = Math.max(150, Math.min(12 * vw, 240));
    // Mirror CSS gap: clamp(12px, 2vw, 24px)
    const gap = Math.max(12, Math.min(2 * vw, 24));
    // Sidebar visible on desktop (≥1200px): clamp(260px, 18vw, 340px)
    const sidebarW = window.innerWidth >= 1200 ? Math.max(260, Math.min(18 * vw, 340)) : 0;
    // Main horizontal padding: 16px×2 on ≤1199, clamp(12px,3vw,24px)×2 on desktop
    const padX = window.innerWidth <= 1199 ? 32 : 2 * Math.max(12, Math.min(3 * vw, 24));
    // Available grid width (respecting max-width: 2560px)
    const gridW = Math.min(window.innerWidth, 2560) - sidebarW - padX;
    // Calculate columns
    const cols = Math.max(1, Math.floor((gridW + gap) / (minColW + gap)));
    // Smallest multiple of cols ≥ MIN_BOOKS
    return Math.ceil(MIN_BOOKS / cols) * cols;
}

// ═══ DOM ═══
const $ = s => document.querySelector(s);
const grid = $("#grid"), skeleton = $("#skeleton"), noResults = $("#no-results");
const searchInput = $("#search");
const paginationEl = $("#pagination");
const homeView = $("#home-view"), detailView = $("#detail-view");

// ═══ DYNAMIC CATEGORY CONFIG ═══
const CAT_ICONS = ["💻", "⚙️", "🚀", "📚", "🎓", "🧠", "💡", "🛠️", "📊", "🌐"];
const CAT_ICON_HINTS = { "Computer Science": "💻", "Software Engineering": "⚙️", "Career": "🚀", "Personal Development": "📚", "University": "🎓" };
function getCatNum(cat) { return (Math.abs(hash(cat)) % 5) + 1; }
function getCatIcon(cat) {
    for (const [key, icon] of Object.entries(CAT_ICON_HINTS)) if (cat.includes(key)) return icon;
    return CAT_ICONS[Math.abs(hash(cat)) % CAT_ICONS.length];
}

// ═══ THEME ═══
function initTheme() {
    const saved = localStorage.getItem("theme");
    const prefer = saved || "light";
    document.documentElement.setAttribute("data-theme", prefer);
}
function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
}
initTheme();

// ═══ VIEW MODE ═══
function setViewMode(mode) {
    viewMode = mode;
    localStorage.setItem("viewMode", mode);
    
    const btnGrid = $("#btn-grid");
    const btnList = $("#btn-list");
    if (btnGrid) btnGrid.classList.toggle("active", mode === "grid");
    if (btnList) btnList.classList.toggle("active", mode === "list");
    
    if (mode === "list") {
        grid.classList.add("list-view");
        skeleton.classList.add("list-view");
    } else {
        grid.classList.remove("list-view");
        skeleton.classList.remove("list-view");
    }
}

// ═══ INIT ═══
document.addEventListener("DOMContentLoaded", init);

async function init() {
    if ('scrollRestoration' in history) {
        history.scrollRestoration = 'manual';
    }
    setViewMode(viewMode);
    showSkeleton();
    booksPerPage = calculateBooksPerPage();
    try {
        const r = await fetch("data.json?v=" + new Date().getTime(), { cache: "no-store" });
        if (!r.ok) throw new Error(r.status);
        allBooks = mergeBooks(await r.json());
    } catch (e) { console.warn("data.json:", e); allBooks = []; }

    renderSidebar();
    populateFilterPanel();
    applyFilters();
    hideSkeleton();

    searchInput.addEventListener("input", debounce(handleSearchInput, 200));

    document.addEventListener("keydown", e => {
        if ((e.ctrlKey || e.metaKey) && e.key === "k") { e.preventDefault(); searchInput.focus(); }
        if (e.key === "Escape") {
            if ($("#filter-panel").classList.contains("open")) closeFilterPanel();
            else if (detailView.style.display !== "none") showHomeView();
        }
    });

    // Handle browser back/forward
    window.addEventListener("popstate", handlePopState);

    // Recalculate pagination on resize
    window.addEventListener("resize", debounce(() => {
        const newBpp = calculateBooksPerPage();
        if (newBpp !== booksPerPage) {
            const firstBookIndex = (currentPage - 1) * booksPerPage;
            booksPerPage = newBpp;
            currentPage = Math.max(1, Math.floor(firstBookIndex / booksPerPage) + 1);
            renderBooks();
            renderPagination();
        }
    }, 300));

    // Check URL on load
    checkUrlBookParam();
}

// ═══ SIDEBAR ═══
function renderSidebar() {
    const tree = {};
    allBooks.forEach(b => {
        if (!tree[b.category]) tree[b.category] = {};
        
        const parts = b.topic.split('/');
        const mainTopic = parts[0];
        const subTopic = parts.length > 1 ? parts[1] : null;

        if (!tree[b.category][mainTopic]) {
            tree[b.category][mainTopic] = { count: 0, subtopics: {} };
        }
        
        if (subTopic) {
            if (!tree[b.category][mainTopic].subtopics[subTopic]) {
                tree[b.category][mainTopic].subtopics[subTopic] = 0;
            }
            tree[b.category][mainTopic].subtopics[subTopic]++;
        } else {
            tree[b.category][mainTopic].count++;
        }
    });
    const sbAllCount = $("#sb-all-count");
    if (sbAllCount) sbAllCount.textContent = allBooks.length;

    let html = "";
    const sortedCats = Object.keys(tree).sort((a, b) => a.localeCompare(b));
    for (const cat of sortedCats) {
        const topics = tree[cat];
        const count = allBooks.filter(b => b.category === cat).length;
        const n = getCatNum(cat);
        html += `<div>
            <button class="sb-cat" data-cat="${esc(cat)}" onclick="sidebarToggleCat(this)">
                <svg class="sb-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                <span class="sb-label">${esc(cat)}</span>
                <svg class="sb-chevron" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
            </button>
            <div class="sb-topics" data-cat="${esc(cat)}">`;
        
        const sortedMainTopics = Object.keys(topics).sort((a,b) => a.localeCompare(b));
        for (const mainTopic of sortedMainTopics) {
            const data = topics[mainTopic];
            const hasSub = Object.keys(data.subtopics).length > 0;
            
            if (hasSub) {
                html += `<div>
                    <button class="sb-topic parent" data-cat="${esc(cat)}" data-topic="${esc(mainTopic)}" onclick="sidebarToggleTopic(this)">
                        <span class="sb-label">${esc(mainTopic)}</span>
                        <svg class="sb-chevron sb-sub-chevron" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                    </button>
                    <div class="sb-subtopics">`;
                
                const sortedSubs = Object.keys(data.subtopics).sort((a,b) => a.localeCompare(b));
                for (const sub of sortedSubs) {
                    const fullTopic = `${mainTopic}/${sub}`;
                    html += `<button class="sb-topic sub" data-cat="${esc(cat)}" data-topic="${esc(fullTopic)}" onclick="sidebarSelectTopic(this)">
                        <span class="sb-label">${esc(sub)}</span>
                    </button>`;
                }
                html += `</div></div>`;
            } else {
                html += `<button class="sb-topic" data-cat="${esc(cat)}" data-topic="${esc(mainTopic)}" onclick="sidebarSelectTopic(this)">
                    <span class="sb-label">${esc(mainTopic)}</span>
                </button>`;
            }
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
    sidebarViewMode = 'collections';
    sidebarSelection = { category: cat, topic: "" };
    chevron.classList.add("open");
    topics.classList.add("open");
    updateSidebarUI();
    applyFilters();
}

function sidebarSelectTopic(btn) {
    sidebarViewMode = 'collections';
    sidebarSelection = { category: btn.dataset.cat, topic: btn.dataset.topic };
    updateSidebarUI();
    applyFilters();
}

function sidebarSelectTopicByNames(cat, topic) {
    sidebarViewMode = 'collections';
    sidebarSelection = { category: cat, topic: topic };
    
    // Expand the category in sidebar
    const catBtn = document.querySelector(`.sb-cat-btn[data-cat="${cat}"]`);
    if (catBtn) {
        const chevron = catBtn.querySelector(".sb-chevron");
        const topicsEl = catBtn.nextElementSibling;
        if (chevron) chevron.classList.add("open");
        if (topicsEl) topicsEl.classList.add("open");
    }
    
    // Expand the topic if it's a subtopic
    const topicParts = topic.split('/');
    if (topicParts.length > 1) {
        const parentTopic = topicParts[0];
        const topicBtn = document.querySelector(`.sb-topic-btn[data-cat="${cat}"][data-topic="${parentTopic}"]`);
        if (topicBtn) {
            const chevron = topicBtn.querySelector(".sb-sub-chevron");
            const subtopicsEl = topicBtn.nextElementSibling;
            if (chevron) chevron.classList.add("open");
            if (subtopicsEl) subtopicsEl.classList.add("open");
        }
    }
    
    updateSidebarUI();
    applyFilters();
}

function sidebarToggleTopic(btn) {
    const chevron = btn.querySelector(".sb-sub-chevron");
    const subtopics = btn.nextElementSibling;
    
    if (sidebarSelection.category === btn.dataset.cat && sidebarSelection.topic === btn.dataset.topic) {
        if (chevron) chevron.classList.toggle("open");
        if (subtopics) subtopics.classList.toggle("open");
        return;
    }
    
    sidebarViewMode = 'collections';
    sidebarSelection = { category: btn.dataset.cat, topic: btn.dataset.topic };
    if (chevron) chevron.classList.add("open");
    if (subtopics) subtopics.classList.add("open");
    updateSidebarUI();
    applyFilters();
}

function sidebarSelectAll() {
    sidebarSelection = { category: "", topic: "" };
    sidebarViewMode = 'collections';
    updateSidebarUI();
    applyFilters();
}

function sidebarSelectDiscover() {
    sidebarSelection = { category: "", topic: "" };
    sidebarViewMode = 'discover';
    updateSidebarUI();
    applyFilters();
}

function sidebarSelectArchive() {
    sidebarSelection = { category: "", topic: "" };
    sidebarViewMode = 'archive';
    updateSidebarUI();
    applyFilters();
}

function sidebarSelectRecent() {
    sidebarSelection = { category: "", topic: "" };
    sidebarViewMode = 'recent';
    updateSidebarUI();
    applyFilters();
}

function clearAllFilters() {
    searchInput.value = "";
    activeFilters = { sort: null, format: null, category: new Set(), topic: new Set() };
    pendingFilters = copyFilters(activeFilters);
    isGlobalSearch = false;
    sidebarViewMode = 'collections';
    updateSearchModeUI();
    updateFilterBadge();
    sidebarSelectAll();
}

function updateSidebarUI() {
    const btnCollections = $("#sb-collections");
    const btnDiscover = $("#sb-discover");
    const btnArchive = $("#sb-archive");
    const btnRecent = $("#sb-recent");
    if (btnCollections) btnCollections.classList.toggle("active", sidebarViewMode === 'collections' && !sidebarSelection.category);
    if (btnDiscover) btnDiscover.classList.toggle("active", sidebarViewMode === 'discover');
    if (btnArchive) btnArchive.classList.toggle("active", sidebarViewMode === 'archive');
    if (btnRecent) btnRecent.classList.toggle("active", sidebarViewMode === 'recent');
    document.querySelectorAll(".sb-cat").forEach(b => {
        b.classList.toggle("active", b.dataset.cat === sidebarSelection.category && !sidebarSelection.topic);
    });
    document.querySelectorAll(".sb-topic").forEach(b => {
        b.classList.toggle("active", b.dataset.cat === sidebarSelection.category && b.dataset.topic === sidebarSelection.topic);
    });
    if (window.innerWidth < 1024) closeSidebar();
}

function collapseAllCategories() {
    categoriesCollapsed = !categoriesCollapsed;
    const btn = $("#sb-collapse-btn");
    
    if (categoriesCollapsed) {
        // Close all chevrons and submenus, but don't hide the main tree
        document.querySelectorAll(".sb-chevron, .sb-sub-chevron").forEach(c => c.classList.remove("open"));
        document.querySelectorAll(".sb-topics, .sb-subtopics").forEach(t => t.classList.remove("open"));
        if (btn) btn.textContent = 'Expand';
    } else {
        // Open all main categories
        document.querySelectorAll(".sb-chevron").forEach(c => c.classList.add("open"));
        document.querySelectorAll(".sb-topics").forEach(t => t.classList.add("open"));
        if (btn) btn.textContent = 'Collapse';
    }
}
function toggleSidebar() { 
    if ($("#detail-view").style.display !== "none") {
        showHomeView(false);
    }
    $("#sidebar").classList.toggle("open"); 
    $("#sb-overlay").classList.toggle("active"); 
}
function closeSidebar() { $("#sidebar").classList.remove("open"); $("#sb-overlay").classList.remove("active"); }

// ═══ FILTER PANEL (Modal UI) ═══
let activeFilterTab = 'topic';
let fpSearchQuery = '';

function populateFilterPanel() {
    const panel = $("#filter-panel");
    const title = "Filters";

    let html = `
        <div class="fp-header">
            <div class="fp-title">${title}</div>
            <button class="fp-close" onclick="closeFilterPanel()">
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
        </div>
        <div class="fp-body">
            <div class="fp-sidebar">
                <button class="fp-tab ${activeFilterTab === 'topic' ? 'active' : ''}" onclick="setFilterTab('topic')">Categories & Topics</button>
                <button class="fp-tab ${activeFilterTab === 'format' ? 'active' : ''}" onclick="setFilterTab('format')">Formats</button>
                <button class="fp-tab ${activeFilterTab === 'sort' ? 'active' : ''}" onclick="setFilterTab('sort')">Sort</button>
            </div>
            <div class="fp-content">
                <div class="fp-search" ${(activeFilterTab === 'sort' || activeFilterTab === 'format') ? 'style="display:none;"' : ''}>
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                    <input type="text" id="fp-search-input" placeholder="Search ${activeFilterTab}s..." value="${esc(fpSearchQuery)}" oninput="handleFpSearch(this.value)">
                </div>
                <div class="fp-list" id="fp-list-container">
                    ${renderFpList()}
                </div>
            </div>
        </div>
        <div class="fp-footer">
            <button class="fp-clear" onclick="clearFilterPanel()">Clear All</button>
            <div class="fp-actions">
                <button class="fp-btn fp-btn-apply" onclick="applyFilterPanel()">Show Results</button>
            </div>
        </div>
    `;
    panel.innerHTML = html;
    updateApplyButton();
}

function countPendingResults() {
    const q = searchInput.value.toLowerCase().trim();
    const { format: fmtFilter, category: catSet, topic: topicSet } = pendingFilters;
    const { category: sbCat, topic: sbTopic } = sidebarSelection;
    const hasDropdownFilter = fmtFilter || catSet.size > 0 || topicSet.size > 0;

    let books = allBooks;
    if (q && isGlobalSearch) {
        books = allBooks.filter(b => scoreBook(b, q) > 0);
    } else if (!hasDropdownFilter) {
        books = allBooks.filter(b =>
            (!sbCat || b.category === sbCat) &&
            (!sbTopic || b.topic === sbTopic || b.topic.startsWith(sbTopic + '/'))
        );
    }
    
    if (hasDropdownFilter) {
        books = books.filter(b =>
            (catSet.size === 0 || catSet.has(b.category)) &&
            (topicSet.size === 0 || topicSet.has(b.topic)) &&
            (!fmtFilter || b.formats.includes(fmtFilter))
        );
    }
    return books.length;
}

function updateApplyButton() {
    const applyBtn = document.querySelector(".fp-btn-apply");
    if (applyBtn) {
        applyBtn.innerHTML = `Show Results <span style="opacity: 0.5; margin: 0 8px; font-weight: 300;">|</span> ${countPendingResults()}`;
    }
}

function renderFpList() {
    let sections = [];
    const q = fpSearchQuery.toLowerCase();

    if (activeFilterTab === 'topic') {
        const selectedCats = pendingFilters.category;
        const validBooks = selectedCats.size > 0 ? allBooks.filter(b => selectedCats.has(b.category)) : allBooks;
        const validTopicNames = new Set(validBooks.map(b => b.topic));

        // Categories section
        const catCounts = {};
        allBooks.forEach(b => catCounts[b.category] = (catCounts[b.category] || 0) + 1);
        let catItems = Object.entries(catCounts).map(([name, count]) => ({ name, count, value: name, group: 'category' }));

        // Topics section
        const topCounts = {};
        allBooks.forEach(b => topCounts[b.topic] = (topCounts[b.topic] || 0) + 1);
        let topItems = Object.entries(topCounts).map(([name, count]) => {
            return { name, count, value: name, group: 'topic', disabled: selectedCats.size > 0 && !validTopicNames.has(name) };
        });

        if (q) {
            catItems = catItems.filter(i => i.name.toLowerCase().includes(q));
            topItems = topItems.filter(i => i.name.toLowerCase().includes(q));
        }

        catItems.sort((a, b) => a.name.localeCompare(b.name));
        topItems.sort((a, b) => a.name.localeCompare(b.name));

        sections.push({ title: "Categories", items: catItems });
        sections.push({ title: "Topics", items: topItems });
    } else if (activeFilterTab === 'format') {
        const counts = {};
        allBooks.forEach(b => {
            b.formats.forEach(f => counts[f] = (counts[f] || 0) + 1);
        });
        let items = Object.entries(counts).map(([name, count]) => ({ name: name.toUpperCase(), count, value: name, group: 'format' }));
        if (q) items = items.filter(i => i.name.toLowerCase().includes(q));
        items.sort((a, b) => a.name.localeCompare(b.name));
        sections.push({ title: "", items });
    } else if (activeFilterTab === 'sort') {
        let items = [
            { name: "A → Z", value: "az", group: "sort" },
            { name: "Z → A", value: "za", group: "sort" }
        ];
        if (q) items = items.filter(i => i.name.toLowerCase().includes(q));
        sections.push({ title: "", items });
    }

    if (sections.every(s => s.items.length === 0)) {
        return `<div style="color:var(--text-tertiary); font-size:14px; padding-top: 10px;">No matches found.</div>`;
    }

    let html = '';
    sections.forEach(sec => {
        if (sec.items.length === 0) return;
        if (sec.title) {
            html += `<div class="fp-section-title">${sec.title}</div>`;
        }
        html += `<div class="fp-list-grid">` + sec.items.map(i => {
            let isChecked = false;
            if (i.group === 'topic' || i.group === 'category') {
                isChecked = pendingFilters[i.group].has(i.value);
            } else {
                isChecked = pendingFilters[i.group] === i.value;
            }
            return `
                <label class="fp-checkbox ${i.disabled ? 'disabled' : ''}">
                    <input type="checkbox" ${isChecked ? 'checked' : ''} ${i.disabled ? 'disabled' : ''} onchange="toggleFpItem('${i.group}', '${esc(i.value)}')">
                    <span class="fp-name">${esc(i.name)}</span>
                    ${i.count !== undefined ? `<span class="fp-count">${i.count}</span>` : ''}
                </label>
            `;
        }).join('') + `</div>`;
    });
    return html;
}

function setFilterTab(tab) {
    activeFilterTab = tab;
    fpSearchQuery = '';
    const searchInput = $("#fp-search-input");
    if (searchInput) {
        searchInput.value = '';
        searchInput.placeholder = tab === 'topic' ? `Search Categories & Topics...` : `Search ${tab}s...`;
        searchInput.parentElement.style.display = (tab === 'sort' || tab === 'format') ? 'none' : '';
    }
    
    document.querySelectorAll('.fp-tab').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.toLowerCase().includes(tab));
    });
    
    $("#fp-list-container").innerHTML = renderFpList();
}

function handleFpSearch(q) {
    fpSearchQuery = q;
    $("#fp-list-container").innerHTML = renderFpList();
}

function toggleFpItem(group, value) {
    if (group === "category" || group === "topic") {
        const set = pendingFilters[group];
        if (set.has(value)) {
            set.delete(value);
        } else {
            set.add(value);
        }
        if (group === "category") {
            pruneInvalidTopics();
            if (activeFilterTab === 'topic') {
                $("#fp-list-container").innerHTML = renderFpList();
            }
        }
    } else {
        pendingFilters[group] = pendingFilters[group] === value ? null : value;
        $("#fp-list-container").innerHTML = renderFpList();
    }
    updateApplyButton();
}

function toggleFilterPanel() {
    const panel = $("#filter-panel");
    const overlay = $("#filter-overlay");
    const isOpen = panel.classList.contains("open");
    
    if (!isOpen) {
        pendingFilters = copyFilters(activeFilters);
        populateFilterPanel();
    }
    
    panel.classList.toggle("open");
    overlay.classList.toggle("active", !isOpen);
    document.body.style.overflow = isOpen ? '' : 'hidden';
}

function closeFilterPanel() {
    $("#filter-panel").classList.remove("open");
    $("#filter-overlay").classList.remove("active");
    document.body.style.overflow = '';
}

function clearFilterPanel() {
    pendingFilters = { sort: null, format: null, category: new Set(), topic: new Set() };
    $("#fp-list-container").innerHTML = renderFpList();
    updateApplyButton();
}

function pruneInvalidTopics() {
    if (pendingFilters.category.size === 0) return;
    const validTopics = new Set(
        allBooks.filter(b => pendingFilters.category.has(b.category)).map(b => b.topic)
    );
    for (const t of pendingFilters.topic) {
        if (!validTopics.has(t)) pendingFilters.topic.delete(t);
    }
}

function applyFilterPanel() {
    activeFilters = copyFilters(pendingFilters);
    updateFilterBadge();
    applyFilters();
    closeFilterPanel();
}

function updateFilterBadge() {
    const count = (activeFilters.sort ? 1 : 0) +
                  (activeFilters.format ? 1 : 0) +
                  activeFilters.category.size +
                  activeFilters.topic.size;
    const btn = $("#filter-btn");
    if (btn) btn.classList.toggle("has-active", count > 0);
    
    updateActiveFiltersUI();
}

function updateActiveFiltersUI() {
    let titleHtml = "All Books";
    if (sidebarViewMode === 'discover') {
        titleHtml = '✨ Discover';
    } else if (sidebarViewMode === 'collections' && !sidebarSelection.category) {
        titleHtml = '📚 Collections';
    } else if (sidebarViewMode === 'archive') {
        titleHtml = '📦 Archive';
    } else if (sidebarViewMode === 'recent') {
        titleHtml = '🕐 Recent';
    } else if (sidebarSelection.topic) {
        titleHtml = sidebarSelection.topic.split('/').map(p => esc(p)).join(' <span class="ch-separator">/</span> ');
    } else if (sidebarSelection.category) {
        titleHtml = esc(sidebarSelection.category);
    } else if (isGlobalSearch && searchInput.value.trim()) {
        titleHtml = "Search Results";
    }
    const titleEl = $("#ch-title");
    if (titleEl) titleEl.innerHTML = titleHtml;

    const chipsContainer = $("#active-filters");
    if (!chipsContainer) return;
    
    let html = '';
    
    if (activeFilters.sort) {
        const sortLabels = { "az": "A to Z", "za": "Z to A", "score": "Relevance" };
        html += `<span class="filter-chip" onclick="removeFilter('sort', null)">${sortLabels[activeFilters.sort] || "Sort"} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></span>`;
    }
    if (activeFilters.format) {
        html += `<span class="filter-chip" onclick="removeFilter('format', null)">${activeFilters.format} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></span>`;
    }
    activeFilters.category.forEach(c => {
        html += `<span class="filter-chip" onclick="removeFilter('category', '${esc(c)}')">${esc(c)} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></span>`;
    });
    activeFilters.topic.forEach(t => {
        const tName = t.split('/').pop();
        html += `<span class="filter-chip" onclick="removeFilter('topic', '${esc(t)}')">${esc(tName)} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></span>`;
    });
    
    chipsContainer.innerHTML = html;
}

function removeFilter(type, value) {
    if (type === 'sort') activeFilters.sort = null;
    else if (type === 'format') activeFilters.format = null;
    else if (type === 'category') activeFilters.category.delete(value);
    else if (type === 'topic') activeFilters.topic.delete(value);
    
    pendingFilters = copyFilters(activeFilters);
    updateFilterBadge();
    applyFilters();
}

// ═══ SKELETON ═══
function showSkeleton() {
    let h = "";
    for (let i = 0; i < 12; i++) h += `<div class="skeleton"><div class="shimmer" style="aspect-ratio:3/4"></div><div style="padding:12px"><div class="shimmer" style="height:12px;border-radius:4px;margin-bottom:6px;width:80%"></div><div class="shimmer" style="height:10px;border-radius:4px;width:50%"></div></div></div>`;
    skeleton.innerHTML = h;
    skeleton.style.display = "";
}
function hideSkeleton() { skeleton.style.display = "none"; grid.style.display = ""; }

// ═══ SEARCH MODE ═══
function handleSearchInput() {
    const q = searchInput.value.trim();
    if (q.length > 0) {
        isGlobalSearch = true;
        if (detailView.style.display !== "none") {
            showHomeView();
        }
    } else {
        isGlobalSearch = false;
    }
    updateSearchModeUI();
    applyFilters();
}

function updateSearchModeUI() {
    const indicator = $("#search-global-indicator");
    const clearBtn = $("#search-clear-btn");
    if (isGlobalSearch && searchInput.value.trim()) {
        indicator.classList.add("visible");
        clearBtn.classList.add("visible");
        searchInput.classList.add("global-active");
    } else {
        indicator.classList.remove("visible");
        clearBtn.classList.remove("visible");
        searchInput.classList.remove("global-active");
    }
}

function clearSearch() {
    searchInput.value = "";
    isGlobalSearch = false;
    updateSearchModeUI();
    applyFilters();
    searchInput.focus();
}

// ═══ SMART SEARCH SCORING ═══
function scoreBook(book, query) {
    const q = query.toLowerCase();
    const title = book.title.toLowerCase();
    const cleanedTitle = cleanTitle(book.title).toLowerCase();
    const topic = book.topic.toLowerCase();
    const category = book.category.toLowerCase();
    const desc = (book.description || "").toLowerCase();

    // Tokenize query for multi-word matching
    const tokens = q.split(/\s+/).filter(t => t.length > 0);
    let score = 0;

    // Exact full query match in title → highest score
    if (title.includes(q) || cleanedTitle.includes(q)) score += 100;
    // Exact match in topic
    if (topic.includes(q)) score += 60;
    // Exact match in category
    if (category.includes(q)) score += 40;
    // Exact match in description
    if (desc.includes(q)) score += 20;

    // Token-based matching (each token contributes)
    for (const token of tokens) {
        if (title.includes(token) || cleanedTitle.includes(token)) score += 30;
        if (topic.includes(token)) score += 15;
        if (category.includes(token)) score += 10;
        if (desc.includes(token)) score += 5;
    }

    // Title starts with query → bonus
    if (cleanedTitle.startsWith(q)) score += 50;

    return score;
}

// ═══ FILTER + SORT ═══
function applyFilters() {
    const q = searchInput.value.toLowerCase().trim();
    const { sort: sortDir, format: fmtFilter, category: catSet, topic: topicSet } = activeFilters;
    const { category: sbCat, topic: sbTopic } = sidebarSelection;
    const hasDropdownFilter = fmtFilter || catSet.size > 0 || topicSet.size > 0;

    // Handle special sidebar view modes
    if (sidebarViewMode === 'archive') {
        const archivedIds = getArchivedBooks();
        filteredBooks = archivedIds.map(id => allBooks.find(b => b.id === id)).filter(Boolean);
        currentPage = 1;
        renderBooks();
        renderPagination();
        return;
    }
    if (sidebarViewMode === 'recent') {
        const recentIds = getRecentBooks();
        filteredBooks = recentIds.map(id => allBooks.find(b => b.id === id)).filter(Boolean);
        currentPage = 1;
        renderBooks();
        renderPagination();
        return;
    }

    if (q && isGlobalSearch) {
        // GLOBAL search: search ALL books, then apply panel filters
        const scored = allBooks
            .map(b => ({ book: b, score: scoreBook(b, q) }))
            .filter(item => item.score > 0);

        let filtered = scored;
        if (fmtFilter) filtered = filtered.filter(i => i.book.formats.includes(fmtFilter));
        if (catSet.size > 0) filtered = filtered.filter(i => catSet.has(i.book.category));
        if (topicSet.size > 0) filtered = filtered.filter(i => topicSet.has(i.book.topic));

        if (sortDir === "az") {
            filtered.sort((a, b) => cleanTitle(a.book.title).localeCompare(cleanTitle(b.book.title)));
        } else if (sortDir === "za") {
            filtered.sort((a, b) => cleanTitle(b.book.title).localeCompare(cleanTitle(a.book.title)));
        } else {
            filtered.sort((a, b) => b.score - a.score);
        }
        filteredBooks = filtered.map(item => item.book);
    } else {
        // Panel filters take priority, fallback to sidebar
        if (hasDropdownFilter) {
            filteredBooks = allBooks.filter(b =>
                (catSet.size === 0 || catSet.has(b.category)) &&
                (topicSet.size === 0 || topicSet.has(b.topic)) &&
                (!fmtFilter || b.formats.includes(fmtFilter))
            );
        } else {
            filteredBooks = allBooks.filter(b =>
                (!sbCat || b.category === sbCat) &&
                (!sbTopic || b.topic === sbTopic || b.topic.startsWith(sbTopic + '/'))
            );
        }

        // Discover mode: shuffle
        if (sidebarViewMode === 'discover' && !q) {
            filteredBooks = shuffleArray([...filteredBooks]);
        }

        if (sortDir === "az") {
            filteredBooks.sort((a, b) => cleanTitle(a.title).localeCompare(cleanTitle(b.title)));
        } else if (sortDir === "za") {
            filteredBooks.sort((a, b) => cleanTitle(b.title).localeCompare(cleanTitle(a.title)));
        }
    }

    currentPage = 1;
    renderBooks();
    renderPagination();
}

// ═══ RENDER BOOKS ═══
function renderBooks() {
    if (!filteredBooks.length) {
        grid.innerHTML = "";
        paginationEl.innerHTML = "";
        noResults.classList.add("visible");
        const countEl = $("#ch-count-val");
        if (countEl) countEl.textContent = "0";
        updateActiveFiltersUI();
        return;
    }
    noResults.classList.remove("visible");
    const countEl = $("#ch-count-val");
    if (countEl) countEl.textContent = filteredBooks.length;
    updateActiveFiltersUI();

    // Collections mode: grouped by category → topic
    if (sidebarViewMode === 'collections' && !sidebarSelection.category) {
        renderCollectionsView();
        return;
    }

    const start = (currentPage - 1) * booksPerPage;
    const end = start + booksPerPage;
    const pageBooks = filteredBooks.slice(start, end);

    grid.innerHTML = pageBooks.map((book, i) => {
        const delay = Math.min(i * 30, 300);
        const title = cleanTitle(book.title);
        const n = getCatNum(book.category);
        const cover = book.cover || "data:image/svg+xml," + encodeURIComponent(placeholderSVG(title));
        return `<div class="card fade-in" style="animation-delay:${delay}ms" onclick="showDetailView('${book.id}')" tabindex="0" role="button" aria-label="${esc(title)}">
            <div class="card-cover">
                <img src="${esc(cover)}" alt="${esc(title)}" loading="lazy" onerror="this.src='data:image/svg+xml,${encodeURIComponent(placeholderSVG(title))}'">
                <div class="card-overlay">
                    <span class="card-view"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>View</span>
                </div>
            </div>
            <div class="card-info">
                <div class="card-title">${esc(title)}</div>
                <div><span class="card-badge badge-${n}">${esc(book.topic)}</span></div>
                <div class="card-desc-list">${esc((book.description || "").substring(0, 200))}${book.description && book.description.length > 200 ? "..." : ""}</div>
            </div>
        </div>`;
    }).join("");
}

function renderCollectionsView() {
    // Group books: category → topic → books[]
    const groups = {};
    filteredBooks.forEach(b => {
        if (!groups[b.category]) groups[b.category] = {};
        if (!groups[b.category][b.topic]) groups[b.category][b.topic] = [];
        groups[b.category][b.topic].push(b);
    });

    const sortedCats = Object.keys(groups).sort((a, b) => a.localeCompare(b));
    let html = '';

    for (const cat of sortedCats) {
        const n = getCatNum(cat);
        const topics = groups[cat];
        const sortedTopics = Object.keys(topics).sort((a, b) => a.localeCompare(b));

        html += `<div class="coll-category fade-in">
            <div class="coll-cat-header">
                <svg class="coll-cat-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                <span class="coll-cat-name">${esc(cat)}</span>
                <span class="coll-cat-count">${allBooks.filter(b => b.category === cat).length}</span>
            </div>`;

        for (const topic of sortedTopics) {
            const allBooksInTopic = topics[topic];
            const maxDisplay = 10;
            const books = allBooksInTopic.slice(0, maxDisplay);
            const hasMore = allBooksInTopic.length > maxDisplay;
            const topicDisplay = topic.includes('/') ? topic.split('/').pop() : topic;

            html += `<div class="coll-topic">
                <div class="coll-topic-header">
                    <span class="coll-topic-name">${esc(topicDisplay)}</span>
                    <span class="coll-topic-count">${allBooksInTopic.length} books</span>
                </div>
                <div class="coll-scroll-row">`;

            for (const book of books) {
                const title = cleanTitle(book.title);
                const cover = book.cover || "data:image/svg+xml," + encodeURIComponent(placeholderSVG(title));
                html += `<div class="coll-card" onclick="showDetailView('${book.id}')" tabindex="0" role="button" aria-label="${esc(title)}">
                    <div class="coll-card-cover">
                        <img src="${esc(cover)}" alt="${esc(title)}" loading="lazy" onerror="this.src='data:image/svg+xml,${encodeURIComponent(placeholderSVG(title))}'">
                    </div>
                    <div class="coll-card-title">${esc(title)}</div>
                </div>`;
            }

            if (hasMore) {
                html += `<div class="coll-view-more-card" onclick="sidebarSelectTopicByNames('${esc(cat)}', '${esc(topic)}')">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width:28px;height:28px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                    <span>View All<br>(${allBooksInTopic.length - maxDisplay} more)</span>
                </div>`;
            }

            html += `</div></div>`;
        }

        html += `</div>`;
    }

    grid.innerHTML = html;
    // Hide pagination for collections view
    paginationEl.innerHTML = "";
}

// ═══ PAGINATION ═══
function renderPagination() {
    if (sidebarViewMode === 'collections' && !sidebarSelection.category) {
        paginationEl.innerHTML = "";
        return;
    }
    const total = filteredBooks.length;
    const totalPages = Math.ceil(total / booksPerPage);
    if (totalPages <= 1) { paginationEl.innerHTML = ""; return; }

    let html = '';
    html += `<button class="page-btn page-arrow" ${currentPage===1?'disabled':''} onclick="goToPage(${currentPage-1})" title="Previous">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
    </button>`;

    const pages = getPageNumbers(currentPage, totalPages);
    pages.forEach(p => {
        if (p === '...') {
            html += `<span class="page-ellipsis">…</span>`;
        } else {
            html += `<button class="page-btn ${p===currentPage?'active':''}" onclick="goToPage(${p})">${p}</button>`;
        }
    });

    html += `<button class="page-btn page-arrow" ${currentPage===totalPages?'disabled':''} onclick="goToPage(${currentPage+1})" title="Next">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
    </button>`;

    const startItem = (currentPage - 1) * booksPerPage + 1;
    const endItem = Math.min(currentPage * booksPerPage, total);
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
    const totalPages = Math.ceil(filteredBooks.length / booksPerPage);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderBooks();
    renderPagination();
    // Smooth scroll to top of grid area (toolbar position - small offset)
    const toolbar = document.querySelector('.toolbar');
    const navH = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--nav-h')) || 48;
    const target = toolbar ? toolbar.offsetTop - navH - 8 : 0;
    window.scrollTo({ top: Math.max(0, target), behavior: 'smooth' });
}

// ═══ PLACEHOLDER SVG ═══
function placeholderSVG(title) {
    const colors = ["2997ff", "30d158", "ff9f0a", "ff375f", "bf5af2", "64d2ff"];
    const c = colors[Math.abs(hash(title)) % colors.length];
    const ini = title.split(" ").slice(0, 2).map(w => w[0]).join("").toUpperCase();
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400"><rect width="300" height="400" fill="#1c1c1e"/><rect x="16" y="16" width="268" height="368" rx="12" fill="#2c2c2e" stroke="#${c}" stroke-width="1.5" stroke-opacity="0.2"/><text x="150" y="200" text-anchor="middle" fill="#${c}" font-size="56" font-family="system-ui" font-weight="700">${ini}</text><text x="150" y="300" text-anchor="middle" fill="#a1a1a6" font-size="13" font-family="system-ui">${escXml(title.substring(0, 28))}</text></svg>`;
}

// ═══ DETAIL VIEW (SPA) ═══
function showDetailView(bookId, pushHistory = true) {
    const b = allBooks.find(x => x.id === bookId);
    if (!b) return;
    currentBookId = bookId;
    addRecentBook(bookId);

    const title = cleanTitle(b.title);
    const n = getCatNum(b.category);
    const cover = b.cover || "data:image/svg+xml," + encodeURIComponent(placeholderSVG(title));
    const desc = b.description || `A book in "${b.topic}" of "${b.category}".`;
    const dlUrl = getDownloadUrl(b.file_path, b.download_url);

    // Related books
    const related = getRelatedBooks(b);

    const dv = $("#dv-content");
    dv.innerHTML = `
        <div class="dv-hero">
            <div class="dv-cover-wrap">
                <img class="dv-cover" src="${esc(cover)}" alt="${esc(title)}" onerror="this.src='data:image/svg+xml,${encodeURIComponent(placeholderSVG(title))}'">
            </div>
            <div class="dv-info">
                <h1 class="dv-title">${esc(title)}</h1>
                <div class="dv-tags">
                    <span class="dv-tag badge-${n}">${getCatIcon(b.category)} ${esc(b.category)}</span>
                    <span class="dv-tag dv-tag-topic">${esc(b.topic)}</span>
                    ${b.formats.map(f => `<span class="dv-tag dv-tag-fmt">${f.toUpperCase()}</span>`).join('')}
                </div>
                <p class="dv-desc">${esc(desc)}</p>
                <div class="dv-actions">
                    ${b.formats.map(f => {
                        const fUrl = getDownloadUrl(b.files[f], b.downloads[f]);
                        return `<a href="${esc(fUrl)}" target="_blank" class="btn-primary" download onclick="addArchivedBook('${bookId}')">
                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                            Download ${f.toUpperCase()}
                        </a>`;
                    }).join('')}
                    <button class="btn-secondary" onclick="toggleArchiveBook('${bookId}')" id="dv-archive-btn">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/></svg>
                        ${getArchivedBooks().includes(bookId) ? 'Archived ✓' : 'Archive'}
                    </button>
                    <button class="btn-secondary" onclick="shareBook()">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"/></svg>
                        Share
                    </button>
                </div>
            </div>
        </div>
        ${related.length ? `
        <div class="dv-related">
            <h2 class="dv-related-title">Related Books</h2>
            <div class="dv-related-grid">
                ${related.map(rb => {
                    const rTitle = cleanTitle(rb.title);
                    const rN = getCatNum(rb.category);
                    const rCover = rb.cover || "data:image/svg+xml," + encodeURIComponent(placeholderSVG(rTitle));
                    return `<div class="card fade-in" onclick="showDetailView('${rb.id}')" tabindex="0" role="button" aria-label="${esc(rTitle)}">
                        <div class="card-cover">
                            <img src="${esc(rCover)}" alt="${esc(rTitle)}" loading="lazy" onerror="this.src='data:image/svg+xml,${encodeURIComponent(placeholderSVG(rTitle))}'">
                        </div>
                        <div class="card-info">
                            <div class="card-title">${esc(rTitle)}</div>
                            <span class="card-badge badge-${rN}">${esc(rb.topic)}</span>
                        </div>
                    </div>`;
                }).join("")}
            </div>
        </div>` : ""}
    `;

    // Switch views
    if (homeView.style.display !== "none") {
        savedScrollPos = window.scrollY || document.documentElement.scrollTop;
    }
    homeView.style.display = "none";
    detailView.style.display = "block";
    setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'instant' });
    }, 10);

    // Update URL
    if (pushHistory) {
        const u = new URL(location);
        u.searchParams.set("book", bookId);
        history.pushState({ bookId }, "", u);
    }

    // Update page title
    document.title = `${title} — My Bookshelves`;
}

function showHomeView(pushHistory = true) {
    detailView.style.display = "none";
    homeView.style.display = "";
    setTimeout(() => {
        window.scrollTo({ top: savedScrollPos, behavior: 'instant' });
    }, 10);
    currentBookId = null;
    document.title = "My Bookshelves";

    if (pushHistory) {
        const u = new URL(location);
        u.searchParams.delete("book");
        history.pushState(null, "", u);
    }
}

function handlePopState(e) {
    if (e.state && e.state.bookId) {
        showDetailView(e.state.bookId, false);
    } else {
        showHomeView(false);
    }
}

// ═══ RELATED BOOKS ═══
function getRelatedBooks(book) {
    // Same topic first (exclude self)
    let related = allBooks.filter(b => b.id !== book.id && b.topic === book.topic);
    // Fill with same category if needed
    if (related.length < 5) {
        const catBooks = allBooks.filter(b => b.id !== book.id && b.category === book.category && b.topic !== book.topic);
        related = related.concat(catBooks);
    }
    return related.slice(0, 5);
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

function toggleArchiveBook(bookId) {
    const archived = getArchivedBooks();
    if (archived.includes(bookId)) {
        removeArchivedBook(bookId);
        showToast("Removed from Archive");
    } else {
        addArchivedBook(bookId);
        showToast("Added to Archive");
    }
    // Update button text
    const btn = $("#dv-archive-btn");
    if (btn) {
        const isArchived = getArchivedBooks().includes(bookId);
        btn.innerHTML = `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/></svg> ${isArchived ? 'Archived ✓' : 'Archive'}`;
    }
}

function checkUrlBookParam() {
    const id = new URLSearchParams(location.search).get("book");
    if (id) requestAnimationFrame(() => showDetailView(id, false));
}

function showToast(msg) {
    $("#toast-msg").textContent = msg;
    const t = $("#toast"); t.classList.add("show");
    setTimeout(() => t.classList.remove("show"), 2500);
}

// ═══ DOWNLOAD URL ═══
function getDownloadUrl(fp, downloadUrl) {
    if (downloadUrl) return downloadUrl;
    const local = location.hostname === "localhost" || location.hostname === "127.0.0.1" || location.protocol === "file:";
    if (local) return "../" + encodeURI(fp);
    return `https://raw.githubusercontent.com/${CONFIG.githubRepo}/${CONFIG.branch}/${encodeURI(fp)}`;
}

// ═══ UTILS ═══
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
function escXml(s) { return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
function hash(s) { let h = 0; for (let i = 0; i < s.length; i++) { h = (h << 5) - h + s.charCodeAt(i); h |= 0; } return h; }
function shuffleArray(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}
function cleanTitle(t) {
    const lowerWords = ["a","an","the","and","or","but","in","on","of","to","for","with","by","at","from","as","is"];
    return t.replace(/[-_]/g, " ").replace(/\s+/g, " ").trim()
        .split(" ")
        .map((w, i) => {
            const lower = w.toLowerCase();
            return (i > 0 && lowerWords.includes(lower))
                ? lower
                : lower.charAt(0).toUpperCase() + lower.slice(1);
        })
        .join(" ");
}
function mergeBooks(books) {
    const groups = {};
    books.forEach(b => {
        const key = cleanTitle(b.title);
        if (!groups[key]) {
            groups[key] = { ...b, formats: [b.format], downloads: { [b.format]: b.download_url || '' }, files: { [b.format]: b.file_path } };
        } else {
            groups[key].formats.push(b.format);
            groups[key].downloads[b.format] = b.download_url || '';
            groups[key].files[b.format] = b.file_path;
            if (!groups[key].description && b.description) groups[key].description = b.description;
            if (!groups[key].cover && b.cover) groups[key].cover = b.cover;
            if (!groups[key].download_url && b.download_url) groups[key].download_url = b.download_url;
        }
    });
    return Object.values(groups);
}
