export function createEmptyFilters() {
    return { sort: null, format: null, category: new Set(), topic: new Set() };
}

export function copyFilters(source) {
    return {
        sort: source.sort,
        format: source.format,
        category: new Set(source.category),
        topic: new Set(source.topic)
    };
}
