import { hash } from "./utils.js";

const CAT_ICONS = ["💻", "⚙️", "🚀", "📚", "🎓", "🧠", "💡", "🛠️", "📊", "🌐"];
const CAT_ICON_HINTS = {
    "Computer Science": "💻",
    "Software Engineering": "⚙️",
    "Career": "🚀",
    "Personal Development": "📚",
    "University": "🎓"
};

export function getCatNum(category) {
    return (Math.abs(hash(category)) % 5) + 1;
}

export function getCatIcon(category) {
    for (const [key, icon] of Object.entries(CAT_ICON_HINTS)) {
        if (category.includes(key)) return icon;
    }
    return CAT_ICONS[Math.abs(hash(category)) % CAT_ICONS.length];
}
