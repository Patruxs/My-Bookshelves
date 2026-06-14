export function renderPaginationControls({ currentPage, totalPages, total, booksPerPage, pages }) {
    if (totalPages <= 1) return "";

    let html = "";
    html += `<button class="page-btn page-arrow" ${currentPage === 1 ? "disabled" : ""} data-action="go-page" data-page="${currentPage - 1}" title="Previous" aria-label="Previous page">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
    </button>`;

    pages.forEach(page => {
        if (page === "...") {
            html += `<span class="page-ellipsis">…</span>`;
        } else {
            html += `<button class="page-btn ${page === currentPage ? "active" : ""}" data-action="go-page" data-page="${page}" aria-label="Page ${page}">${page}</button>`;
        }
    });

    html += `<button class="page-btn page-arrow" ${currentPage === totalPages ? "disabled" : ""} data-action="go-page" data-page="${currentPage + 1}" title="Next" aria-label="Next page">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
    </button>`;

    const startItem = (currentPage - 1) * booksPerPage + 1;
    const endItem = Math.min(currentPage * booksPerPage, total);
    html += `<span class="page-info">${startItem}–${endItem} of ${total}</span>`;
    return html;
}
