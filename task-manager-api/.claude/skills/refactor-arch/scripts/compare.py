#!/usr/bin/env python3
"""Compara dois diretórios de respostas gravadas (baseline x after).

Uso:
    python compare.py <dir_baseline> <dir_after> [--ignore campo1,campo2]

Cada chamada é gravada como <nome>.status (código HTTP) e <nome>.body (corpo).
Para cada <nome> o script compara o status e o corpo, removendo campos voláteis
antes. Listas JSON são comparadas sem considerar a ordem (implementações antigas
sem ORDER BY têm ordem não determinística). Corpos que não são JSON são
comparados como texto.

Campos voláteis ignorados por padrão: criado_em, created_at, updated_at,
atualizado_em, updatedAt, createdAt, timestamp, token. Acrescente outros com --ignore.

Saída: uma linha DIFF por endpoint divergente e um resumo. Código de saída 1 se
houver divergência, 0 caso contrário. Requer apenas Python 3 (sem dependências).
"""
import json
import os
import sys

DEFAULT_VOLATILE = {"criado_em", "created_at", "updated_at", "atualizado_em",
                    "updatedAt", "createdAt", "timestamp", "token"}


def strip(obj, volatile):
    if isinstance(obj, dict):
        return {k: strip(v, volatile) for k, v in obj.items() if k not in volatile}
    if isinstance(obj, list):
        items = [strip(v, volatile) for v in obj]
        return sorted(items, key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
    return obj


def load_body(path, volatile):
    if not os.path.exists(path):
        return "AUSENTE"
    text = open(path, encoding="utf-8", errors="replace").read()
    try:
        return strip(json.loads(text), volatile)
    except ValueError:
        return text


def load_status(path):
    return open(path).read().strip() if os.path.exists(path) else "AUSENTE"


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    volatile = set(DEFAULT_VOLATILE)
    if "--ignore" in argv:
        volatile |= set(argv[argv.index("--ignore") + 1].split(","))
        args = [a for a in args if a != argv[argv.index("--ignore") + 1]]
    if len(args) != 2:
        print(__doc__)
        return 2
    a, b = args
    names = sorted({f.rsplit(".", 1)[0] for d in (a, b) for f in os.listdir(d)})
    bad = 0
    for n in names:
        sa, sb = load_status(f"{a}/{n}.status"), load_status(f"{b}/{n}.status")
        ba, bb = load_body(f"{a}/{n}.body", volatile), load_body(f"{b}/{n}.body", volatile)
        if sa != sb or ba != bb:
            bad += 1
            print(f"DIFF {n}: status {sa} -> {sb}; corpo {'igual' if ba == bb else 'diferente'}")
    print(f"{len(names)} endpoints comparados, {bad} diferença(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
