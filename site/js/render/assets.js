import { getSiteAssetUrl } from "../routes.js";
import { escXml, hash } from "../utils.js";

export function placeholderDataUrl(title) {
    return "data:image/svg+xml," + encodeURIComponent(placeholderSVG(title));
}

export function safeCoverSrc(cover, title) {
    const fallback = placeholderDataUrl(title);
    if (!cover) return fallback;
    if (cover.startsWith("data:image/svg+xml,")) return cover;
    if (/^assets\/covers\/[-\w.%/]+\.webp$/i.test(cover)) return getSiteAssetUrl(cover);
    return fallback;
}

export function safeDownloadUrl(url) {
    if (!url) return "#";
    try {
        const parsed = new URL(url, location.href);
        const allowedProtocols = new Set(["http:", "https:", "file:"]);
        if (!allowedProtocols.has(parsed.protocol)) return "#";
        return parsed.href;
    } catch {
        return "#";
    }
}

export function placeholderSVG(title) {
    const colors = ["2997ff", "30d158", "ff9f0a", "ff375f", "bf5af2", "64d2ff"];
    const color = colors[Math.abs(hash(title)) % colors.length];
    const initials = String(title || "")
        .split(" ")
        .slice(0, 2)
        .map(word => word[0])
        .join("")
        .toUpperCase();
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400"><rect width="300" height="400" fill="#1c1c1e"/><rect x="16" y="16" width="268" height="368" rx="12" fill="#2c2c2e" stroke="#${color}" stroke-width="1.5" stroke-opacity="0.2"/><text x="150" y="200" text-anchor="middle" fill="#${color}" font-size="56" font-family="system-ui" font-weight="700">${initials}</text><text x="150" y="300" text-anchor="middle" fill="#a1a1a6" font-size="13" font-family="system-ui">${escXml(String(title || "").substring(0, 28))}</text></svg>`;
}
