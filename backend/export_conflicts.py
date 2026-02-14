from collections import defaultdict


def detect_conflicts(items):
    """
    Detect destination collisions.

    Returns list of:
    {
        "destination": "...",
        "sources": [...]
    }
    """

    buckets = defaultdict(list)

    for item in items:
        buckets[item["destination"]].append(item["source"])

    conflicts = []

    for dst, sources in buckets.items():
        if len(sources) > 1:
            conflicts.append({
                "destination": dst,
                "sources": sources,
            })

    return conflicts