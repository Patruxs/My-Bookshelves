import { getCatIcon, getCatNum } from "../categories.js";
import { cleanTitle, esc } from "../utils.js";
import { placeholderDataUrl, safeCoverSrc } from "./assets.js";
import { renderRelatedBookCard } from "./cards.js";

export function renderDetailContent({ book, relatedBooks, isArchived, getFormatUrl }) {
    const title = cleanTitle(book.title);
    const badgeNumber = getCatNum(book.category);
    const fallback = placeholderDataUrl(title);
    const cover = safeCoverSrc(book.cover, title);
    const description = book.description || `A book in "${book.topic}" of "${book.category}".`;

    // Escape description for safety, but restore simple <a> tags for clickable links
    let safeDesc = esc(description);
    safeDesc = safeDesc.replace(/&lt;a\s+href=&quot;(https?:\/\/[^&]+)&quot;.*?&gt;(.*?)&lt;\/a&gt;/gi, '<a href="$1" target="_blank" rel="noopener noreferrer" style="color: var(--accent); text-decoration: none;">$2</a>');

    return `
        <div class="dv-hero">
            <div class="dv-cover-wrap">
                <img class="dv-cover" src="${esc(cover)}" alt="${esc(title)}" data-fallback-src="${esc(fallback)}">
            </div>
            <div class="dv-info">
                <h1 class="dv-title">${esc(title)}</h1>
                <div class="dv-tags">
                    <span class="dv-tag badge-${badgeNumber}">${getCatIcon(book.category)} ${esc(book.category)}</span>
                    <span class="dv-tag dv-tag-topic">${esc(book.topic)}</span>
                    ${book.formats.map(format => `<span class="dv-tag dv-tag-fmt">${format.toUpperCase()}</span>`).join("")}
                </div>
                <p class="dv-desc">${safeDesc}</p>
                <div class="dv-actions">
                    ${book.formats.map(format => renderDownloadButton(book.id, format, getFormatUrl(format))).join("")}
                    <button class="btn-secondary" data-action="toggle-archive" data-book-id="${esc(book.id)}" id="dv-archive-btn">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/></svg>
                        ${isArchived ? "Archived ✓" : "Archive"}
                    </button>
                    <button class="btn-secondary" data-action="share-book">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"/></svg>
                        Share
                    </button>
                </div>
            </div>
        </div>
        ${relatedBooks.length ? renderRelatedBooks(relatedBooks) : ""}
    `;
}

function renderDownloadButton(bookId, format, url) {
    return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" class="btn-primary" download data-action="archive-download" data-book-id="${esc(bookId)}">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        Download ${format.toUpperCase()}
    </a>`;
}

function renderRelatedBooks(relatedBooks) {
    return `
        <div class="dv-related">
            <h2 class="dv-related-title">Related Books</h2>
            <div class="dv-related-grid">
                ${relatedBooks.map(renderRelatedBookCard).join("")}
            </div>
        </div>`;
}
