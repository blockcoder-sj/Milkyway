"""Conservative resource pooling for a verified inline XBRL document set."""
import re


def resource_nodes(soup, shared, tag, limit):
    """Exclude every conflicting ID instead of choosing a document's definition."""
    nodes, signatures, conflicts = {}, {}, set()
    for document in (soup,) if shared is None else (soup, shared):
        for node in document.find_all(tag, limit=limit):
            key = node.get('id')
            if not key:
                continue
            signature = re.sub(r'>\s+<', '><', str(node)).strip()
            if key in signatures and signatures[key] != signature:
                conflicts.add(key)
            else:
                nodes[key], signatures[key] = node, signature
    return [node for key, node in nodes.items() if key not in conflicts][:limit]
