export const REPO_ROUTE_SEGMENT = "My-Bookshelves";

const SITE_ASSET_BASE_URL = new URL("../", import.meta.url).href;

export function getTopicParts(topic) {
    return String(topic || "").split("/").map(part => part.trim()).filter(Boolean);
}

export function getAppBasePath() {
    const firstSegment = location.pathname.split("/").filter(Boolean)[0] || "";
    return firstSegment === REPO_ROUTE_SEGMENT ? `/${REPO_ROUTE_SEGMENT}` : "";
}

export function getHomeUrl() {
    return new URL(`${getAppBasePath() || ""}/`, location.origin).href;
}

export function getSiteAssetUrl(path) {
    const cleanPath = String(path || "").replace(/^\/+/, "");
    return new URL(cleanPath, SITE_ASSET_BASE_URL).href;
}

export function getBrowseUrl(category, topic = "") {
    return new URL(routePathFromSegments([category, ...getTopicParts(topic)]), location.origin).href;
}

export function getBookUrl(book) {
    return new URL(routePathFromSegments([book.category, ...getTopicParts(book.topic), book.id]), location.origin).href;
}

export function routePathFromSegments(segments) {
    const encoded = segments.filter(Boolean).map(encodeRouteSegment).join("/");
    return `${getAppBasePath() || ""}/${encoded}`;
}

export function encodeRouteSegment(segment) {
    return encodeURIComponent(String(segment).trim()).replace(/%2F/gi, "/");
}

export function decodeRouteSegment(segment) {
    try {
        return decodeURIComponent(String(segment).replace(/\+/g, "%20"));
    } catch {
        return String(segment);
    }
}

export function normalizeRouteLabel(value) {
    return String(value || "")
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[_-]+/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .toLowerCase();
}

export function singularRouteKey(value) {
    return normalizeRouteLabel(value)
        .split(" ")
        .map(word => word.length > 3 && word.endsWith("s") ? word.slice(0, -1) : word)
        .join(" ");
}

export function normalizeTopicPath(value) {
    return getTopicParts(value).map(normalizeRouteLabel).join("/");
}

export function singularTopicPath(value) {
    return getTopicParts(value).map(singularRouteKey).join("/");
}

export function matchDisplayName(labels, segment) {
    const exactKey = normalizeRouteLabel(segment);
    const exact = labels.find(label => normalizeRouteLabel(label) === exactKey);
    if (exact) return exact;

    const looseKey = singularRouteKey(segment);
    const looseMatches = labels.filter(label => singularRouteKey(label) === looseKey);
    return looseMatches.length === 1 ? looseMatches[0] : null;
}

export function matchTopic(books, category, segments) {
    const target = segments.map(normalizeRouteLabel).join("/");
    const topics = [...new Set(books.filter(book => book.category === category).map(book => book.topic))];
    const exact = topics.find(topic => normalizeTopicPath(topic) === target);
    if (exact) return exact;

    const looseTarget = segments.map(singularRouteKey).join("/");
    const looseMatches = topics.filter(topic => singularTopicPath(topic) === looseTarget);
    return looseMatches.length === 1 ? looseMatches[0] : null;
}

export function matchNearestTopic(books, category, segments) {
    for (let i = segments.length; i > 0; i--) {
        const topic = matchTopic(books, category, segments.slice(0, i));
        if (topic) return topic;
    }
    return "";
}

export function matchTopicAlias(books, segments) {
    const matches = [];
    const categories = [...new Set(books.map(book => book.category))];
    categories.forEach(category => {
        const topic = matchTopic(books, category, segments);
        if (topic) matches.push({ category, topic });
    });
    return matches.length === 1 ? matches[0] : null;
}

export function getRouteSegmentsInfo() {
    const params = new URLSearchParams(location.search);
    const redirectedRoute = params.get("route");
    if (redirectedRoute) {
        return { segments: splitRoutePath(redirectedRoute), fromRedirect: true };
    }

    const rawSegments = location.pathname.split("/").filter(Boolean);
    if (rawSegments[0] === REPO_ROUTE_SEGMENT) rawSegments.shift();
    const last = rawSegments[rawSegments.length - 1];
    if (last === "index.html" || last === "404.html") rawSegments.pop();
    return { segments: rawSegments.map(decodeRouteSegment), fromRedirect: false };
}

export function splitRoutePath(path) {
    return String(path || "")
        .split("/")
        .filter(Boolean)
        .map(decodeRouteSegment);
}

export function resolveRouteFromPath(books) {
    const { segments, fromRedirect } = getRouteSegmentsInfo();
    if (!segments.length) return null;

    const lastSegment = segments[segments.length - 1];
    const book = books.find(candidate => candidate.id === lastSegment);
    if (book) {
        return { type: "book", book, fromRedirect, canonicalUrl: getBookUrl(book) };
    }

    const categories = [...new Set(books.map(candidate => candidate.category))];
    const category = matchDisplayName(categories, segments[0]);
    if (category) {
        const topicSegments = segments.slice(1);
        if (!topicSegments.length) {
            return { type: "category", category, fromRedirect, canonicalUrl: getBrowseUrl(category) };
        }

        const topic = matchTopic(books, category, topicSegments) || matchNearestTopic(books, category, topicSegments);
        if (topic) {
            return { type: "topic", category, topic, fromRedirect, canonicalUrl: getBrowseUrl(category, topic) };
        }
        return { type: "category", category, fromRedirect, canonicalUrl: getBrowseUrl(category) };
    }

    const alias = matchTopicAlias(books, segments);
    if (alias) {
        return { type: "topic", ...alias, fromRedirect, canonicalUrl: getBrowseUrl(alias.category, alias.topic) };
    }

    return null;
}
