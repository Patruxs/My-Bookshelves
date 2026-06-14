import { cleanTitle, shuffleArray } from "./utils.js";

const searchIndexCache = new WeakMap();

export function scoreBook(book, query) {
    const normalizedQuery = String(query || "").toLowerCase();
    const { title, cleanedTitle, topic, category, description } = getSearchIndex(book);
    const tokens = normalizedQuery.split(/\s+/).filter(Boolean);
    let score = 0;

    if (title.includes(normalizedQuery) || cleanedTitle.includes(normalizedQuery)) score += 100;
    if (topic.includes(normalizedQuery)) score += 60;
    if (category.includes(normalizedQuery)) score += 40;
    if (description.includes(normalizedQuery)) score += 20;

    for (const token of tokens) {
        if (title.includes(token) || cleanedTitle.includes(token)) score += 30;
        if (topic.includes(token)) score += 15;
        if (category.includes(token)) score += 10;
        if (description.includes(token)) score += 5;
    }

    if (cleanedTitle.startsWith(normalizedQuery)) score += 50;
    return score;
}

function getSearchIndex(book) {
    const cached = searchIndexCache.get(book);
    if (cached) return cached;

    const index = {
        title: String(book.title || "").toLowerCase(),
        cleanedTitle: cleanTitle(book.title).toLowerCase(),
        topic: String(book.topic || "").toLowerCase(),
        category: String(book.category || "").toLowerCase(),
        description: String(book.description || "").toLowerCase()
    };
    searchIndexCache.set(book, index);
    return index;
}

export function getFilteredBooks({
    books,
    query,
    isGlobalSearch,
    filters,
    sidebarSelection,
    sidebarViewMode,
    archivedIds = [],
    recentIds = []
}) {
    if (sidebarViewMode === "archive") {
        return archivedIds.map(id => books.find(book => book.id === id)).filter(Boolean);
    }
    if (sidebarViewMode === "recent") {
        return recentIds.map(id => books.find(book => book.id === id)).filter(Boolean);
    }

    const normalizedQuery = String(query || "").toLowerCase().trim();
    const hasDropdownFilter = hasActiveDropdownFilter(filters);
    const { sort: sortDir } = filters;

    if (normalizedQuery && isGlobalSearch) {
        const scoredBooks = books
            .map(book => ({ book, score: scoreBook(book, normalizedQuery) }))
            .filter(item => item.score > 0);

        const filtered = applyPanelFiltersToScored(scoredBooks, filters);
        if (sortDir === "az") {
            filtered.sort((a, b) => cleanTitle(a.book.title).localeCompare(cleanTitle(b.book.title)));
        } else if (sortDir === "za") {
            filtered.sort((a, b) => cleanTitle(b.book.title).localeCompare(cleanTitle(a.book.title)));
        } else {
            filtered.sort((a, b) => b.score - a.score);
        }
        return filtered.map(item => item.book);
    }

    let filteredBooks;
    if (hasDropdownFilter) {
        filteredBooks = applyPanelFilters(books, filters);
    } else {
        filteredBooks = applySidebarSelection(books, sidebarSelection);
    }

    if (sidebarViewMode === "discover" && !normalizedQuery) {
        filteredBooks = shuffleArray([...filteredBooks]);
    }

    if (sortDir === "az") {
        filteredBooks.sort((a, b) => cleanTitle(a.title).localeCompare(cleanTitle(b.title)));
    } else if (sortDir === "za") {
        filteredBooks.sort((a, b) => cleanTitle(b.title).localeCompare(cleanTitle(a.title)));
    }
    return filteredBooks;
}

export function countFilteredBooks({ books, query, isGlobalSearch, filters, sidebarSelection }) {
    const normalizedQuery = String(query || "").toLowerCase().trim();
    const hasDropdownFilter = hasActiveDropdownFilter(filters);

    let candidates = books;
    if (normalizedQuery && isGlobalSearch) {
        candidates = books.filter(book => scoreBook(book, normalizedQuery) > 0);
    } else if (!hasDropdownFilter) {
        candidates = applySidebarSelection(books, sidebarSelection);
    }

    return hasDropdownFilter ? applyPanelFilters(candidates, filters).length : candidates.length;
}

function hasActiveDropdownFilter(filters) {
    return Boolean(filters.format || filters.category.size > 0 || filters.topic.size > 0);
}

function applyPanelFilters(books, filters) {
    const { format, category, topic } = filters;
    return books.filter(book =>
        (category.size === 0 || category.has(book.category)) &&
        (topic.size === 0 || topic.has(book.topic)) &&
        (!format || book.formats.includes(format))
    );
}

function applyPanelFiltersToScored(scoredBooks, filters) {
    const { format, category, topic } = filters;
    return scoredBooks.filter(item =>
        (!format || item.book.formats.includes(format)) &&
        (category.size === 0 || category.has(item.book.category)) &&
        (topic.size === 0 || topic.has(item.book.topic))
    );
}

function applySidebarSelection(books, sidebarSelection) {
    const { category, topic } = sidebarSelection;
    return books.filter(book =>
        (!category || book.category === category) &&
        (!topic || book.topic === topic || book.topic.startsWith(topic + "/"))
    );
}
