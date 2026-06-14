const MIN_BOOKS = 30;

export function calculateBooksPerPage() {
    const vw = window.innerWidth / 100;
    const minColumnWidth = Math.max(150, Math.min(12 * vw, 240));
    const gap = Math.max(12, Math.min(2 * vw, 24));
    const sidebarWidth = window.innerWidth >= 1200 ? Math.max(260, Math.min(18 * vw, 340)) : 0;
    const horizontalPadding = window.innerWidth <= 1199 ? 32 : 2 * Math.max(12, Math.min(3 * vw, 24));
    const gridWidth = Math.min(window.innerWidth, 2560) - sidebarWidth - horizontalPadding;
    const columns = Math.max(1, Math.floor((gridWidth + gap) / (minColumnWidth + gap)));
    return Math.ceil(MIN_BOOKS / columns) * columns;
}

export function getPageNumbers(current, total) {
    if (total <= 7) return Array.from({ length: total }, (_, index) => index + 1);

    const pages = [1];
    if (current > 3) pages.push("...");
    for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
        pages.push(i);
    }
    if (current < total - 2) pages.push("...");
    pages.push(total);
    return pages;
}
