import { getTopicParts } from "../routes.js";
import { esc } from "../utils.js";

export function renderSidebarTree(books) {
    const tree = buildSidebarTree(books);
    const sortedCategories = Object.keys(tree).sort((a, b) => a.localeCompare(b));
    let html = "";

    for (const category of sortedCategories) {
        html += `<div>
            <button class="sb-cat" data-action="sidebar-toggle-cat" data-cat="${esc(category)}" aria-expanded="false">
                <svg class="sb-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                <span class="sb-label">${esc(category)}</span>
                <svg class="sb-chevron" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
            </button>
            <div class="sb-topics" data-cat="${esc(category)}">`;
        html += renderTopicNodes(category, tree[category].topics);
        html += `</div></div>`;
    }

    return html;
}

function buildSidebarTree(books) {
    const tree = {};
    books.forEach(book => {
        if (!tree[book.category]) tree[book.category] = { topics: {}, count: 0 };
        tree[book.category].count++;
        insertTopicNode(tree[book.category].topics, getTopicParts(book.topic));
    });
    return tree;
}

function insertTopicNode(nodes, parts) {
    let current = nodes;
    const full = [];
    parts.forEach(part => {
        full.push(part);
        if (!current[part]) {
            current[part] = { name: part, fullTopic: full.join("/"), children: {} };
        }
        current = current[part].children;
    });
}

function renderTopicNodes(category, nodes, level = 0) {
    return Object.values(nodes)
        .sort((a, b) => a.name.localeCompare(b.name))
        .map(node => {
            const hasChildren = Object.keys(node.children).length > 0;
            const classes = ["sb-topic", hasChildren ? "parent" : "", level > 0 ? "sub" : ""]
                .filter(Boolean)
                .join(" ");
            const action = hasChildren ? "sidebar-toggle-topic" : "sidebar-select-topic";
            let html = `<div>
                <button class="${classes}" data-action="${action}" data-cat="${esc(category)}" data-topic="${esc(node.fullTopic)}" aria-expanded="false">
                    <span class="sb-label">${esc(node.name)}</span>
                    ${hasChildren ? '<svg class="sb-chevron sb-sub-chevron" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>' : ''}
                </button>`;
            if (hasChildren) {
                html += `<div class="sb-subtopics">${renderTopicNodes(category, node.children, level + 1)}</div>`;
            }
            return `${html}</div>`;
        })
        .join("");
}
