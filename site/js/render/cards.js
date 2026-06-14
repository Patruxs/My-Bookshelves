import { getCatNum } from "../categories.js";
import { cleanTitle, esc } from "../utils.js";
import { placeholderDataUrl, safeCoverSrc } from "./assets.js";

export function renderBookCard(book, index = 0) {
    const delay = Math.min(index * 30, 300);
    const title = cleanTitle(book.title);
    const badgeNumber = getCatNum(book.category);
    const fallback = placeholderDataUrl(title);
    const cover = safeCoverSrc(book.cover, title);

    return `<div class="card fade-in" style="animation-delay:${delay}ms" data-action="open-book" data-book-id="${esc(book.id)}" tabindex="0" role="button" aria-label="${esc(title)}">
        <div class="card-cover">
            <img src="${esc(cover)}" alt="${esc(title)}" loading="lazy" data-fallback-src="${esc(fallback)}">
            <div class="card-overlay">
                <span class="card-view"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>View</span>
            </div>
        </div>
        <div class="card-info">
            <div class="card-title">${esc(title)}</div>
            <div><span class="card-badge badge-${badgeNumber}">${esc(book.topic)}</span></div>
            <div class="card-desc-list">${esc((book.description || "").substring(0, 200))}${book.description && book.description.length > 200 ? "..." : ""}</div>
        </div>
    </div>`;
}

export function renderCollectionBookCard(book) {
    const title = cleanTitle(book.title);
    const fallback = placeholderDataUrl(title);
    const cover = safeCoverSrc(book.cover, title);

    return `<div class="coll-card" data-action="open-book" data-book-id="${esc(book.id)}" tabindex="0" role="button" aria-label="${esc(title)}">
        <div class="coll-card-cover">
            <img src="${esc(cover)}" alt="${esc(title)}" loading="lazy" data-fallback-src="${esc(fallback)}">
        </div>
        <div class="coll-card-title">${esc(title)}</div>
    </div>`;
}

export function renderRelatedBookCard(book) {
    const title = cleanTitle(book.title);
    const badgeNumber = getCatNum(book.category);
    const fallback = placeholderDataUrl(title);
    const cover = safeCoverSrc(book.cover, title);

    return `<div class="card fade-in" data-action="open-book" data-book-id="${esc(book.id)}" tabindex="0" role="button" aria-label="${esc(title)}">
        <div class="card-cover">
            <img src="${esc(cover)}" alt="${esc(title)}" loading="lazy" data-fallback-src="${esc(fallback)}">
        </div>
        <div class="card-info">
            <div class="card-title">${esc(title)}</div>
            <span class="card-badge badge-${badgeNumber}">${esc(book.topic)}</span>
        </div>
    </div>`;
}
