import { esc } from "../utils.js";
import { renderCollectionBookCard } from "./cards.js";

export function renderCollectionsView({ books, allBooks }) {
    const groups = groupBooksByCategoryAndTopic(books);
    const sortedCategories = Object.keys(groups).sort((a, b) => a.localeCompare(b));
    let html = "";

    for (const category of sortedCategories) {
        const topics = groups[category];
        const sortedTopics = Object.keys(topics).sort((a, b) => a.localeCompare(b));

        html += `<div class="coll-category fade-in">
            <div class="coll-cat-header">
                <svg class="coll-cat-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                <span class="coll-cat-name">${esc(category)}</span>
                <span class="coll-cat-count">${allBooks.filter(book => book.category === category).length}</span>
            </div>`;

        for (const topic of sortedTopics) {
            html += renderCollectionTopic(category, topic, topics[topic]);
        }

        html += `</div>`;
    }

    return html;
}

function groupBooksByCategoryAndTopic(books) {
    const groups = {};
    books.forEach(book => {
        if (!groups[book.category]) groups[book.category] = {};
        if (!groups[book.category][book.topic]) groups[book.category][book.topic] = [];
        groups[book.category][book.topic].push(book);
    });
    return groups;
}

function renderCollectionTopic(category, topic, booksInTopic) {
    const maxDisplay = 10;
    const books = booksInTopic.slice(0, maxDisplay);
    const hasMore = booksInTopic.length > maxDisplay;
    const topicDisplay = topic.includes("/") ? topic.split("/").pop() : topic;

    let html = `<div class="coll-topic">
        <div class="coll-topic-header">
            <span class="coll-topic-name">${esc(topicDisplay)}</span>
            <span class="coll-topic-count">${booksInTopic.length} books</span>
        </div>
        <div class="coll-scroll-row">`;

    for (const book of books) {
        html += renderCollectionBookCard(book);
    }

    if (hasMore) {
        html += `<div class="coll-view-more-card" data-action="view-topic" data-cat="${esc(category)}" data-topic="${esc(topic)}" tabindex="0" role="button">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width:28px;height:28px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
            <span>View All<br>(${booksInTopic.length - maxDisplay} more)</span>
        </div>`;
    }

    return `${html}</div></div>`;
}
