/**
 * My Bookshelves — App Logic (SPA Detail View)
 * Zero dependencies · Pure JavaScript · Apple-style UI
 */

import { mergeBooks, getDownloadUrl } from "./js/data.js";
import { $ } from "./js/dom.js";
import { copyFilters, createEmptyFilters } from "./js/filters.js";
import { calculateBooksPerPage, getPageNumbers } from "./js/pagination.js";
import { safeDownloadUrl } from "./js/render/assets.js";
import { renderBookCard } from "./js/render/cards.js";
import { renderCollectionsView as renderCollectionsHtml } from "./js/render/collections.js";
import { renderDetailContent } from "./js/render/detail.js";
import { renderFilterList } from "./js/render/filters.js";
import { renderPaginationControls } from "./js/render/pagination.js";
import { renderSidebarTree } from "./js/render/sidebar.js";
import { countFilteredBooks, getFilteredBooks } from "./js/search.js";
import {
    getArchivedBooks,
    addArchivedBook,
    removeArchivedBook,
    addRecentBook,
    getRecentBooks,
    getStoredTheme,
    setStoredTheme,
    getStoredViewMode,
    setStoredViewMode
} from "./js/storage.js";
import {
    getBookUrl,
    getBrowseUrl,
    getHomeUrl,
    getSiteAssetUrl,
    resolveRouteFromPath
} from "./js/routes.js";
import { cleanTitle, cssEscape, debounce, esc } from "./js/utils.js";

// ═══ CONFIG ═══

// ═══ STATE ═══
let allBooks = [], filteredBooks = [], currentBookId = null;
let activeFilters = createEmptyFilters();
let pendingFilters = createEmptyFilters();
let viewMode = getStoredViewMode();
let sidebarSelection = { category: "", topic: "" };
let sidebarViewMode = 'discover'; // 'discover' | 'collections' | 'archive' | 'recent'
let isGlobalSearch = false;
let currentPage = 1;
let booksPerPage = 16;
let savedScrollPos = 0;
let categoriesCollapsed = false;
let sidebarFilterRenderToken = 0;
const SIDEBAR_DISCLOSURE_MS = 70;

// ═══ DOM ═══
const grid = $("#grid"), skeleton = $("#skeleton"), noResults = $("#no-results");
const searchInput = $("#search");
const paginationEl = $("#pagination");
const homeView = $("#home-view"), detailView = $("#detail-view");

// ═══ THEME ═══
function initTheme() {
    const saved = getStoredTheme();
    const prefer = saved || "light";
    document.documentElement.setAttribute("data-theme", prefer);
}
function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    setStoredTheme(next);
}
initTheme();

// ═══ VIEW MODE ═══
function setViewMode(mode) {
    viewMode = mode;
    setStoredViewMode(mode);
    
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
    setupEventDelegation();
    setViewMode(viewMode);
    showSkeleton();
    booksPerPage = calculateBooksPerPage();
    try {
        const r = await fetch(getSiteAssetUrl("data.json") + "?v=" + new Date().getTime(), { cache: "no-store" });
        if (!r.ok) throw new Error(r.status);
        allBooks = mergeBooks(await r.json());
    } catch {
        allBooks = [];
        const emptyText = $("#no-results p");
        if (emptyText) emptyText.textContent = "Library data could not be loaded";
    }

    renderSidebar();
    populateFilterPanel();
    applyFilters();
    hideSkeleton();

    searchInput.addEventListener("input", debounce(handleSearchInput, 200));

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
    applyUrlRoute(false);
}

let eventDelegationReady = false;

function setupEventDelegation() {
    if (eventDelegationReady) return;
    eventDelegationReady = true;
    document.addEventListener("click", handleDelegatedClick);
    document.addEventListener("change", handleDelegatedChange);
    document.addEventListener("input", handleDelegatedInput);
    document.addEventListener("keydown", handleDelegatedKeydown);
    document.addEventListener("error", handleImageError, true);
}

function handleDelegatedClick(e) {
    if (!(e.target instanceof Element)) return;
    const actionEl = e.target.closest("[data-action]");
    if (!actionEl) return;
    const action = actionEl.dataset.action;

    if (action === "home") {
        e.preventDefault();
        showHomeView();
        clearAllFilters();
    } else if (action === "toggle-sidebar") {
        toggleSidebar();
    } else if (action === "close-sidebar") {
        closeSidebar();
    } else if (action === "clear-search") {
        clearSearch();
    } else if (action === "toggle-theme") {
        toggleTheme();
    } else if (action === "sidebar-discover") {
        sidebarSelectDiscover();
    } else if (action === "sidebar-all") {
        sidebarSelectAll();
    } else if (action === "sidebar-archive") {
        sidebarSelectArchive();
    } else if (action === "sidebar-recent") {
        sidebarSelectRecent();
    } else if (action === "collapse-categories") {
        collapseAllCategories();
    } else if (action === "toggle-filter") {
        toggleFilterPanel();
    } else if (action === "close-filter") {
        closeFilterPanel();
    } else if (action === "set-view") {
        setViewMode(actionEl.dataset.mode || "grid");
    } else if (action === "show-home") {
        showHomeView();
    } else if (action === "sidebar-toggle-cat") {
        sidebarToggleCat(e, actionEl);
    } else if (action === "sidebar-toggle-topic") {
        sidebarToggleTopic(e, actionEl);
    } else if (action === "sidebar-select-topic") {
        sidebarSelectTopic(actionEl);
    } else if (action === "filter-tab") {
        setFilterTab(actionEl.dataset.tab || "topic");
    } else if (action === "clear-filter-panel") {
        clearFilterPanel();
    } else if (action === "apply-filter-panel") {
        applyFilterPanel();
    } else if (action === "remove-filter") {
        removeFilter(actionEl.dataset.filterType, actionEl.dataset.filterValue || null);
    } else if (action === "open-book") {
        showDetailView(actionEl.dataset.bookId);
    } else if (action === "view-topic") {
        sidebarSelectTopicByNames(actionEl.dataset.cat, actionEl.dataset.topic);
    } else if (action === "go-page") {
        goToPage(Number(actionEl.dataset.page));
    } else if (action === "archive-download") {
        addArchivedBook(actionEl.dataset.bookId);
    } else if (action === "toggle-archive") {
        toggleArchiveBook(actionEl.dataset.bookId);
    } else if (action === "share-book") {
        shareBook();
    }
}

function handleDelegatedChange(e) {
    if (!(e.target instanceof Element)) return;
    const actionEl = e.target.closest("[data-action]");
    if (!actionEl) return;
    if (actionEl.dataset.action === "toggle-fp-item") {
        toggleFpItem(actionEl.dataset.group, actionEl.dataset.value);
    }
}

function handleDelegatedInput(e) {
    if (!(e.target instanceof Element)) return;
    const actionEl = e.target.closest("[data-action]");
    if (!actionEl) return;
    if (actionEl.dataset.action === "fp-search") {
        handleFpSearch(actionEl.value);
    }
}

function handleDelegatedKeydown(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        searchInput.focus();
        return;
    }
    if (e.key === "Escape") {
        if ($("#filter-panel").classList.contains("open")) closeFilterPanel();
        else if (detailView.style.display !== "none") showHomeView();
        return;
    }
    if (e.key === "Tab" && $("#filter-panel").classList.contains("open")) {
        trapFilterFocus(e);
        return;
    }
    if (e.key !== "Enter" && e.key !== " ") return;
    if (!(e.target instanceof Element)) return;
    const actionEl = e.target.closest("[data-action]");
    if (!actionEl) return;
    const keyboardActions = new Set(["open-book", "view-topic"]);
    if (keyboardActions.has(actionEl.dataset.action)) {
        e.preventDefault();
        actionEl.click();
    }
}

function trapFilterFocus(e) {
    const panel = $("#filter-panel");
    const focusables = Array.from(panel.querySelectorAll("button, input, [href], [tabindex]:not([tabindex='-1'])"))
        .filter(el => !el.disabled && el.offsetParent !== null);
    if (!focusables.length) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
    }
}

function handleImageError(e) {
    const img = e.target;
    if (!(img instanceof HTMLImageElement) || !img.dataset.fallbackSrc) return;
    img.src = img.dataset.fallbackSrc;
    delete img.dataset.fallbackSrc;
}

// ═══ SIDEBAR ═══
function renderSidebar() {
    const sbAllCount = $("#sb-all-count");
    if (sbAllCount) sbAllCount.textContent = allBooks.length;
    $("#sb-tree").innerHTML = renderSidebarTree(allBooks);
}

function setSidebarDisclosure(btn, panel, chevron, open) {
    if (!panel) return;
    if (open) {
        panel.style.setProperty("--sb-open-height", `${panel.scrollHeight}px`);
    } else if (panel.classList.contains("open")) {
        panel.style.setProperty("--sb-open-height", `${panel.scrollHeight}px`);
        panel.offsetHeight;
    } else {
        panel.style.removeProperty("--sb-open-height");
    }
    if (chevron) chevron.classList.toggle("open", open);
    panel.classList.toggle("open", open);
    if (btn) btn.setAttribute("aria-expanded", String(open));
    refreshOpenSidebarHeights(panel);
    scheduleSidebarDisclosureRefresh(panel, open);
}

function toggleSidebarDisclosure(btn, panel, chevron) {
    if (!panel) return;
    setSidebarDisclosure(btn, panel, chevron, !panel.classList.contains("open"));
}

function refreshOpenSidebarHeights(el) {
    if (el.classList.contains("open")) {
        el.style.setProperty("--sb-open-height", `${el.scrollHeight}px`);
    }
    let parent = el.parentElement && el.parentElement.closest(".sb-topics.open, .sb-subtopics.open");
    while (parent) {
        parent.style.setProperty("--sb-open-height", `${parent.scrollHeight}px`);
        parent = parent.parentElement && parent.parentElement.closest(".sb-topics.open, .sb-subtopics.open");
    }
}

function unlockSidebarDisclosureHeights(el) {
    if (el.classList.contains("open")) {
        el.style.setProperty("--sb-open-height", "none");
    }
    let parent = el.parentElement && el.parentElement.closest(".sb-topics.open, .sb-subtopics.open");
    while (parent) {
        parent.style.setProperty("--sb-open-height", "none");
        parent = parent.parentElement && parent.parentElement.closest(".sb-topics.open, .sb-subtopics.open");
    }
}

function scheduleSidebarDisclosureRefresh(panel, open) {
    requestAnimationFrame(() => {
        refreshOpenSidebarHeights(panel);
    });
    window.setTimeout(() => {
        if (open) {
            unlockSidebarDisclosureHeights(panel);
        } else {
            refreshOpenSidebarHeights(panel);
        }
    }, SIDEBAR_DISCLOSURE_MS + 20);
}


function applyFiltersAfterSidebarPaint() {
    const token = ++sidebarFilterRenderToken;
    window.setTimeout(() => {
        requestAnimationFrame(() => {
            if (token === sidebarFilterRenderToken) applyFilters();
        });
    }, SIDEBAR_DISCLOSURE_MS);
}

function sidebarToggleCat(e, btn, pushHistory = true) {
    const isChevronClick = e && e.target && e.target.closest && e.target.closest('.sb-chevron');
    const cat = btn.dataset.cat;
    const chevron = btn.querySelector(".sb-chevron");
    const topics = btn.nextElementSibling;
    
    if (isChevronClick) {
        e.stopPropagation();
        toggleSidebarDisclosure(btn, topics, chevron);
        return;
    }

    if (sidebarSelection.category === cat && !sidebarSelection.topic) {
        toggleSidebarDisclosure(btn, topics, chevron);
        return;
    }
    sidebarViewMode = 'collections';
    sidebarSelection = { category: cat, topic: "" };
    setSidebarDisclosure(btn, topics, chevron, true);
    updateSidebarUI();
    updateBrowseRoute(cat, "", pushHistory);
    applyFiltersAfterSidebarPaint();
}

function sidebarSelectTopic(btn, pushHistory = true) {
    sidebarViewMode = 'collections';
    sidebarSelection = { category: btn.dataset.cat, topic: btn.dataset.topic };
    updateSidebarUI();
    updateBrowseRoute(sidebarSelection.category, sidebarSelection.topic, pushHistory);
    applyFilters();
}

function sidebarSelectTopicByNames(cat, topic, pushHistory = true) {
    sidebarViewMode = 'collections';
    sidebarSelection = { category: cat, topic: topic };
    
    // Expand the category in sidebar
    const catBtn = document.querySelector(`.sb-cat[data-cat="${cssEscape(cat)}"]`);
    if (catBtn) {
        const chevron = catBtn.querySelector(".sb-chevron");
        const topicsEl = catBtn.nextElementSibling;
        setSidebarDisclosure(catBtn, topicsEl, chevron, true);
    }
    
    const topicParts = topic.split('/');
    for (let i = 1; i <= topicParts.length; i++) {
        const topicPrefix = topicParts.slice(0, i).join('/');
        const topicBtn = document.querySelector(`.sb-topic[data-cat="${cssEscape(cat)}"][data-topic="${cssEscape(topicPrefix)}"]`);
        if (topicBtn) {
            const chevron = topicBtn.querySelector(".sb-sub-chevron");
            const subtopicsEl = topicBtn.nextElementSibling;
            setSidebarDisclosure(topicBtn, subtopicsEl, chevron, true);
        }
    }
    
    updateSidebarUI();
    updateBrowseRoute(cat, topic, pushHistory);
    applyFilters();
}

function sidebarToggleTopic(e, btn, pushHistory = true) {
    const isChevronClick = e && e.target && e.target.closest && e.target.closest('.sb-chevron');
    const chevron = btn.querySelector(".sb-sub-chevron");
    const subtopics = btn.nextElementSibling;
    
    if (isChevronClick) {
        e.stopPropagation();
        toggleSidebarDisclosure(btn, subtopics, chevron);
        return;
    }

    if (subtopics) {
        toggleSidebarDisclosure(btn, subtopics, chevron);
        return;
    }

    if (sidebarSelection.category === btn.dataset.cat && sidebarSelection.topic === btn.dataset.topic) {
        toggleSidebarDisclosure(btn, subtopics, chevron);
        return;
    }
    
    sidebarViewMode = 'collections';
    sidebarSelection = { category: btn.dataset.cat, topic: btn.dataset.topic };
    setSidebarDisclosure(btn, subtopics, chevron, true);
    updateSidebarUI();
    updateBrowseRoute(sidebarSelection.category, sidebarSelection.topic, pushHistory);
    applyFiltersAfterSidebarPaint();
}

function sidebarSelectAll(pushHistory = true) {
    sidebarSelection = { category: "", topic: "" };
    sidebarViewMode = 'collections';
    updateSidebarUI();
    updateHomeRoute(pushHistory);
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
    activeFilters = createEmptyFilters();
    pendingFilters = copyFilters(activeFilters);
    isGlobalSearch = false;
    sidebarViewMode = 'discover';
    updateSearchModeUI();
    updateFilterBadge();
    sidebarSelectDiscover();
    updateHomeRoute(false);
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
        document.querySelectorAll(".sb-topics, .sb-subtopics").forEach(t => {
            t.style.removeProperty("--sb-open-height");
            t.classList.remove("open");
        });
        document.querySelectorAll(".sb-chevron, .sb-sub-chevron").forEach(c => c.classList.remove("open"));
        document.querySelectorAll(".sb-cat, .sb-topic.parent").forEach(b => b.setAttribute("aria-expanded", "false"));
        if (btn) btn.textContent = 'Expand';
    } else {
        // Open all main categories
        document.querySelectorAll(".sb-cat").forEach(catBtn => {
            setSidebarDisclosure(catBtn, catBtn.nextElementSibling, catBtn.querySelector(".sb-chevron"), true);
        });
        if (btn) btn.textContent = 'Collapse';
    }
}
function toggleSidebar() { 
    if ($("#detail-view").style.display !== "none") {
        showHomeView(false);
    }
    $("#sidebar").classList.toggle("open"); 
    $("#sb-overlay").classList.toggle("active"); 
    const menuBtn = $("#menu-btn");
    if (menuBtn) menuBtn.setAttribute("aria-expanded", String($("#sidebar").classList.contains("open")));
}
function closeSidebar() {
    $("#sidebar").classList.remove("open");
    $("#sb-overlay").classList.remove("active");
    const menuBtn = $("#menu-btn");
    if (menuBtn) menuBtn.setAttribute("aria-expanded", "false");
}

// ═══ FILTER PANEL (Modal UI) ═══
let activeFilterTab = 'topic';
let fpSearchQuery = '';
let lastFilterTrigger = null;

function populateFilterPanel() {
    const panel = $("#filter-panel");
    const title = "Filters";

    let html = `
        <div class="fp-header">
            <div class="fp-title">${title}</div>
            <button class="fp-close" data-action="close-filter" aria-label="Close filters">
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
        </div>
        <div class="fp-body">
            <div class="fp-sidebar">
                <button class="fp-tab ${activeFilterTab === 'topic' ? 'active' : ''}" data-action="filter-tab" data-tab="topic">Categories & Topics</button>
                <button class="fp-tab ${activeFilterTab === 'format' ? 'active' : ''}" data-action="filter-tab" data-tab="format">Formats</button>
                <button class="fp-tab ${activeFilterTab === 'sort' ? 'active' : ''}" data-action="filter-tab" data-tab="sort">Sort</button>
            </div>
            <div class="fp-content">
                <div class="fp-search" ${(activeFilterTab === 'sort' || activeFilterTab === 'format') ? 'style="display:none;"' : ''}>
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                    <input type="text" id="fp-search-input" data-action="fp-search" placeholder="Search ${activeFilterTab}s..." value="${esc(fpSearchQuery)}">
                </div>
                <div class="fp-list" id="fp-list-container">
                    ${renderFpList()}
                </div>
            </div>
        </div>
        <div class="fp-footer">
            <button class="fp-clear" data-action="clear-filter-panel">Clear All</button>
            <div class="fp-actions">
                <button class="fp-btn fp-btn-apply" data-action="apply-filter-panel">Show Results</button>
            </div>
        </div>
    `;
    panel.innerHTML = html;
    updateApplyButton();
}

function countPendingResults() {
    return countFilteredBooks({
        books: allBooks,
        query: searchInput.value,
        isGlobalSearch,
        filters: pendingFilters,
        sidebarSelection
    });
}

function updateApplyButton() {
    const applyBtn = document.querySelector(".fp-btn-apply");
    if (applyBtn) {
        applyBtn.innerHTML = `Show Results <span style="opacity: 0.5; margin: 0 8px; font-weight: 300;">|</span> ${countPendingResults()}`;
    }
}

function renderFpList() {
    return renderFilterList({
        books: allBooks,
        activeFilterTab,
        fpSearchQuery,
        pendingFilters
    });
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
        lastFilterTrigger = document.activeElement;
        pendingFilters = copyFilters(activeFilters);
        populateFilterPanel();
    }
    
    panel.classList.toggle("open");
    overlay.classList.toggle("active", !isOpen);
    const btn = $("#filter-btn");
    if (btn) btn.setAttribute("aria-expanded", String(!isOpen));
    document.body.style.overflow = isOpen ? '' : 'hidden';
    if (!isOpen) {
        const firstField = $("#filter-panel").querySelector("button, input, [tabindex]:not([tabindex='-1'])");
        if (firstField) firstField.focus();
    }
}

function closeFilterPanel() {
    $("#filter-panel").classList.remove("open");
    $("#filter-overlay").classList.remove("active");
    const btn = $("#filter-btn");
    if (btn) btn.setAttribute("aria-expanded", "false");
    document.body.style.overflow = '';
    if (lastFilterTrigger && lastFilterTrigger.focus) lastFilterTrigger.focus();
}

function clearFilterPanel() {
    pendingFilters = createEmptyFilters();
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
        html += `<button class="filter-chip" data-action="remove-filter" data-filter-type="sort">${sortLabels[activeFilters.sort] || "Sort"} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>`;
    }
    if (activeFilters.format) {
        html += `<button class="filter-chip" data-action="remove-filter" data-filter-type="format">${activeFilters.format} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>`;
    }
    activeFilters.category.forEach(c => {
        html += `<button class="filter-chip" data-action="remove-filter" data-filter-type="category" data-filter-value="${esc(c)}">${esc(c)} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>`;
    });
    activeFilters.topic.forEach(t => {
        const tName = t.split('/').pop();
        html += `<button class="filter-chip" data-action="remove-filter" data-filter-type="topic" data-filter-value="${esc(t)}">${esc(tName)} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>`;
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

// ═══ FILTER + SORT ═══
function applyFilters() {
    if (detailView.style.display !== "none") {
        showHomeView(false);
    }
    filteredBooks = getFilteredBooks({
        books: allBooks,
        query: searchInput.value,
        isGlobalSearch,
        filters: activeFilters,
        sidebarSelection,
        sidebarViewMode,
        archivedIds: getArchivedBooks(),
        recentIds: getRecentBooks()
    });
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

    grid.innerHTML = pageBooks.map(renderBookCard).join("");
}

function renderCollectionsView() {
    grid.innerHTML = renderCollectionsHtml({ books: filteredBooks, allBooks });
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
    const pages = getPageNumbers(currentPage, totalPages);
    paginationEl.innerHTML = renderPaginationControls({ currentPage, totalPages, total, booksPerPage, pages });
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

// ═══ SAFE URLS & PLACEHOLDER SVG ═══
// ═══ DETAIL VIEW (SPA) ═══
function showDetailView(bookId, pushHistory = true) {
    const b = allBooks.find(x => x.id === bookId);
    if (!b) return;
    currentBookId = bookId;
    addRecentBook(bookId);

    const title = cleanTitle(b.title);
    const related = getRelatedBooks(b);

    const dv = $("#dv-content");
    dv.innerHTML = renderDetailContent({
        book: b,
        relatedBooks: related,
        isArchived: getArchivedBooks().includes(bookId),
        getFormatUrl: format => safeDownloadUrl(getDownloadUrl(b.files[format], b.downloads[format]))
    });

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
        history.pushState({ bookId }, "", getBookUrl(b));
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
        history.pushState(null, "", getHomeUrl());
    }
}

function handlePopState() {
    applyUrlRoute(false);
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
    const book = allBooks.find(b => b.id === currentBookId);
    const url = book ? getBookUrl(book) : location.href;
    navigator.clipboard.writeText(url)
        .then(() => showToast("Link copied to clipboard!"))
        .catch(() => {
            const inp = document.createElement("input"); inp.value = url;
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

function resetBrowseFilters() {
    searchInput.value = "";
    activeFilters = createEmptyFilters();
    pendingFilters = copyFilters(activeFilters);
    isGlobalSearch = false;
    updateSearchModeUI();
    updateFilterBadge();
}

function selectCategoryByName(category, pushHistory = true) {
    sidebarViewMode = 'collections';
    sidebarSelection = { category, topic: "" };
    const catBtn = document.querySelector(`.sb-cat[data-cat="${cssEscape(category)}"]`);
    if (catBtn) {
        setSidebarDisclosure(catBtn, catBtn.nextElementSibling, catBtn.querySelector(".sb-chevron"), true);
    }
    updateSidebarUI();
    updateBrowseRoute(category, "", pushHistory);
    applyFilters();
}

function updateHomeRoute(pushHistory = true) {
    if (pushHistory) history.pushState(null, "", getHomeUrl());
}

function updateBrowseRoute(category, topic = "", pushHistory = true) {
    if (!pushHistory) return;
    history.pushState({ category, topic }, "", getBrowseUrl(category, topic));
}

function applyUrlRoute(pushHistory = false) {
    const id = new URLSearchParams(location.search).get("book");
    if (id) {
        requestAnimationFrame(() => showDetailView(id, pushHistory));
        return;
    }

    const route = resolveRouteFromPath(allBooks);
    if (!route) {
        requestAnimationFrame(() => {
            resetBrowseFilters();
            sidebarSelectDiscover();
            showHomeView(false);
        });
        return;
    }

    requestAnimationFrame(() => {
        resetBrowseFilters();
        if (route.type === "book") {
            showDetailView(route.book.id, pushHistory);
            if (route.fromRedirect && !pushHistory) history.replaceState({ bookId: route.book.id }, "", route.canonicalUrl);
            return;
        }
        if (route.type === "category") {
            selectCategoryByName(route.category, pushHistory);
            if (route.fromRedirect && !pushHistory) history.replaceState({ category: route.category, topic: "" }, "", route.canonicalUrl);
            return;
        }
        if (route.type === "topic") {
            sidebarSelectTopicByNames(route.category, route.topic, pushHistory);
            if (route.fromRedirect && !pushHistory) history.replaceState({ category: route.category, topic: route.topic }, "", route.canonicalUrl);
        }
    });
}

function showToast(msg) {
    $("#toast-msg").textContent = msg;
    const t = $("#toast"); t.classList.add("show");
    setTimeout(() => t.classList.remove("show"), 2500);
}
