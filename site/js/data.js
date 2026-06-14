import { CONFIG } from "./config.js";
import { cleanTitle } from "./utils.js";

export function mergeBooks(books) {
    const groups = {};
    books.forEach(book => {
        const key = cleanTitle(book.title);
        if (!groups[key]) {
            groups[key] = {
                ...book,
                formats: [book.format],
                downloads: { [book.format]: book.download_url || "" },
                files: { [book.format]: book.file_path }
            };
            return;
        }

        groups[key].formats.push(book.format);
        groups[key].downloads[book.format] = book.download_url || "";
        groups[key].files[book.format] = book.file_path;
        if (!groups[key].description && book.description) groups[key].description = book.description;
        if (!groups[key].cover && book.cover) groups[key].cover = book.cover;
        if (!groups[key].download_url && book.download_url) groups[key].download_url = book.download_url;
    });
    return Object.values(groups);
}

export function getDownloadUrl(filePath, downloadUrl) {
    if (downloadUrl) return downloadUrl;
    const local = location.hostname === "localhost" || location.hostname === "127.0.0.1" || location.protocol === "file:";
    if (local) return "../" + encodeURI(filePath);
    return `https://raw.githubusercontent.com/${CONFIG.githubRepo}/${CONFIG.branch}/${encodeURI(filePath)}`;
}
