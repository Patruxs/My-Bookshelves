export function debounce(fn, ms) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), ms);
    };
}

export function esc(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

export function escXml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

export function cssEscape(value) {
    return window.CSS && CSS.escape ? CSS.escape(value) : String(value).replace(/"/g, '\\"');
}

export function hash(value) {
    const text = String(value || "");
    let hashed = 0;
    for (let i = 0; i < text.length; i++) {
        hashed = (hashed << 5) - hashed + text.charCodeAt(i);
        hashed |= 0;
    }
    return hashed;
}

export function shuffleArray(items) {
    for (let i = items.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [items[i], items[j]] = [items[j], items[i]];
    }
    return items;
}

export function cleanTitle(title) {
    const lowerWords = ["a", "an", "the", "and", "or", "but", "in", "on", "of", "to", "for", "with", "by", "at", "from", "as", "is"];
    return String(title || "")
        .replace(/[-_]/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .split(" ")
        .map((word, index) => {
            const lower = word.toLowerCase();
            return index > 0 && lowerWords.includes(lower)
                ? lower
                : lower.charAt(0).toUpperCase() + lower.slice(1);
        })
        .join(" ");
}
