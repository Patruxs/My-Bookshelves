function readJsonArray(key) {
    try {
        const value = JSON.parse(localStorage.getItem(key) || "[]");
        return Array.isArray(value) ? value : [];
    } catch {
        return [];
    }
}

function writeJsonArray(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

export function getStoredTheme() {
    return localStorage.getItem("theme");
}

export function setStoredTheme(theme) {
    localStorage.setItem("theme", theme);
}

export function getStoredViewMode() {
    return localStorage.getItem("viewMode") || "grid";
}

export function setStoredViewMode(mode) {
    localStorage.setItem("viewMode", mode);
}

export function getRecentBooks() {
    return readJsonArray("recentBooks");
}

export function addRecentBook(bookId) {
    let recent = getRecentBooks().filter(id => id !== bookId);
    recent.unshift(bookId);
    if (recent.length > 50) recent = recent.slice(0, 50);
    writeJsonArray("recentBooks", recent);
}

export function getArchivedBooks() {
    return readJsonArray("archivedBooks");
}

export function addArchivedBook(bookId) {
    const archived = getArchivedBooks();
    if (!archived.includes(bookId)) {
        archived.unshift(bookId);
        writeJsonArray("archivedBooks", archived);
    }
}

export function removeArchivedBook(bookId) {
    writeJsonArray("archivedBooks", getArchivedBooks().filter(id => id !== bookId));
}
