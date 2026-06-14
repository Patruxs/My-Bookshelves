import { esc } from "../utils.js";

export function renderFilterList({ books, activeFilterTab, fpSearchQuery, pendingFilters }) {
    const sections = buildFilterSections({ books, activeFilterTab, fpSearchQuery, pendingFilters });
    if (sections.every(section => section.items.length === 0)) {
        return `<div style="color:var(--text-tertiary); font-size:14px; padding-top: 10px;">No matches found.</div>`;
    }

    let html = "";
    sections.forEach(section => {
        if (section.items.length === 0) return;
        if (section.title) {
            html += `<div class="fp-section-title">${section.title}</div>`;
        }
        html += `<div class="fp-list-grid">${section.items.map(item => renderFilterItem(item, pendingFilters)).join("")}</div>`;
    });
    return html;
}

function buildFilterSections({ books, activeFilterTab, fpSearchQuery, pendingFilters }) {
    const sections = [];
    const query = fpSearchQuery.toLowerCase();

    if (activeFilterTab === "topic") {
        const selectedCategories = pendingFilters.category;
        const validBooks = selectedCategories.size > 0
            ? books.filter(book => selectedCategories.has(book.category))
            : books;
        const validTopicNames = new Set(validBooks.map(book => book.topic));

        const categoryCounts = {};
        books.forEach(book => {
            categoryCounts[book.category] = (categoryCounts[book.category] || 0) + 1;
        });
        let categoryItems = Object.entries(categoryCounts)
            .map(([name, count]) => ({ name, count, value: name, group: "category" }));

        const topicCounts = {};
        books.forEach(book => {
            topicCounts[book.topic] = (topicCounts[book.topic] || 0) + 1;
        });
        let topicItems = Object.entries(topicCounts)
            .map(([name, count]) => ({
                name,
                count,
                value: name,
                group: "topic",
                disabled: selectedCategories.size > 0 && !validTopicNames.has(name)
            }));

        if (query) {
            categoryItems = categoryItems.filter(item => item.name.toLowerCase().includes(query));
            topicItems = topicItems.filter(item => item.name.toLowerCase().includes(query));
        }

        categoryItems.sort((a, b) => a.name.localeCompare(b.name));
        topicItems.sort((a, b) => a.name.localeCompare(b.name));
        sections.push({ title: "Categories", items: categoryItems });
        sections.push({ title: "Topics", items: topicItems });
    } else if (activeFilterTab === "format") {
        const counts = {};
        books.forEach(book => {
            book.formats.forEach(format => {
                counts[format] = (counts[format] || 0) + 1;
            });
        });
        let items = Object.entries(counts)
            .map(([name, count]) => ({ name: name.toUpperCase(), count, value: name, group: "format" }));
        if (query) items = items.filter(item => item.name.toLowerCase().includes(query));
        items.sort((a, b) => a.name.localeCompare(b.name));
        sections.push({ title: "", items });
    } else if (activeFilterTab === "sort") {
        let items = [
            { name: "A → Z", value: "az", group: "sort" },
            { name: "Z → A", value: "za", group: "sort" }
        ];
        if (query) items = items.filter(item => item.name.toLowerCase().includes(query));
        sections.push({ title: "", items });
    }

    return sections;
}

function renderFilterItem(item, pendingFilters) {
    const isChecked = item.group === "topic" || item.group === "category"
        ? pendingFilters[item.group].has(item.value)
        : pendingFilters[item.group] === item.value;

    return `
        <label class="fp-checkbox ${item.disabled ? "disabled" : ""}">
            <input type="checkbox" data-action="toggle-fp-item" data-group="${esc(item.group)}" data-value="${esc(item.value)}" ${isChecked ? "checked" : ""} ${item.disabled ? "disabled" : ""}>
            <span class="fp-name">${esc(item.name)}</span>
            ${item.count !== undefined ? `<span class="fp-count">${item.count}</span>` : ""}
        </label>
    `;
}
