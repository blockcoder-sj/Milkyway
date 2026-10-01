"""Exact SEC legal-name recognition with a bounded token trie.

No fuzzy/brand-name guesses. Ambiguous names and multi-ticker issuers stay out;
the separately vetted alias catalogue handles those cases. Shared identities come
only from the official ticker/CIK index, not proximity or a relation's role.
"""
import re
from collections import defaultdict, deque
from itertools import islice

TOKEN = re.compile(r"[A-Za-z0-9]+")
TICKER = re.compile(r"[A-Z0-9][A-Z0-9.-]{0,19}")


class SecNameIndex:
    def __init__(self, rows):
        names, tickers = defaultdict(list), defaultdict(set)
        for row in islice(rows, 15000):
            if not isinstance(row, dict):
                continue
            name, symbol, cik = row.get('title'), row.get('ticker'), str(row.get('cik_str', ''))
            if not (isinstance(name, str) and isinstance(symbol, str) and TICKER.fullmatch(symbol)
                    and re.fullmatch(r'\d{1,10}', cik) and 4 <= len(name) <= 120):
                continue
            cik = str(int(cik))
            tokens = tuple(token.lower() for token in TOKEN.findall(name))
            if not 2 <= len(tokens) <= 24:
                continue
            names[tokens].append((name, symbol, cik))
            tickers[cik].add(symbol)
        self.ciks = {symbol:cik for cik, symbols in tickers.items() for symbol in symbols}
        self.nodes, self.fail, self.outputs = [{}], [0], [[]]
        for tokens, candidates in names.items():
            identities = {(symbol, cik) for _, symbol, cik in candidates}
            if len(identities) != 1 or len(tickers[candidates[0][2]]) != 1:
                continue
            current = 0
            for token in tokens:
                if token not in self.nodes[current]:
                    self.nodes[current][token] = len(self.nodes)
                    self.nodes.append({}); self.fail.append(0); self.outputs.append([])
                current = self.nodes[current][token]
            self.outputs[current].append((len(tokens), *candidates[0]))
        pending = deque(self.nodes[0].values())
        while pending:
            parent = pending.popleft()
            for token, child in self.nodes[parent].items():
                pending.append(child)
                ancestor = self.fail[parent]
                while ancestor and token not in self.nodes[ancestor]:
                    ancestor = self.fail[ancestor]
                self.fail[child] = self.nodes[ancestor].get(token, 0)
                self.outputs[child].extend(self.outputs[self.fail[child]])

    def mentions(self, text, issuer_symbol=None):
        tokens = list(TOKEN.finditer(text[:10000]))
        current, found = 0, []
        for index, token in enumerate(tokens):
            word = token.group().lower()
            while current and word not in self.nodes[current]:
                current = self.fail[current]
            current = self.nodes[current].get(word, 0)
            for length, name, symbol, cik in self.outputs[current]:
                if symbol == issuer_symbol or (cik == self.ciks.get(issuer_symbol)):
                    continue
                start = tokens[index - length + 1].start()
                # Punctuation in a legal name is fine; HTML/sentence separators are
                # not. A name cannot be assembled across two separate clauses.
                span = text[start:token.end()]
                if re.search(r'[;:<>\n]', span):
                    continue
                found.append((start, token.end(), name, symbol))
        # Prefer the longest full name when a shorter issuer name is a substring.
        chosen = []
        for row in sorted(found, key=lambda item: (-(item[1]-item[0]), item[0])):
            if any(row[0] < other[1] and other[0] < row[1] for other in chosen):
                continue
            chosen.append(row)
            if len(chosen) == 20:
                break
        return sorted(chosen)

    def named(self, text, issuer_symbol):
        return [(name, symbol) for _, _, name, symbol in self.mentions(text, issuer_symbol)]
