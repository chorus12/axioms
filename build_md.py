"""Собирает axioms.md из index.html: текст трактата + карта вывода из JS-данных.

Запуск из корня репозитория (нужен pandoc):
    python3 build_md.py index.html > axioms.md
"""
import json, re, subprocess, sys

src = open(sys.argv[1], encoding="utf-8").read()

# --- карта вывода: данные живут только в <script> ---
script = re.search(r"<script>(.*?)</script>", src, re.S).group(1)
ax_block = re.search(r"const AX = \{(.*?)\n  \};", script, re.S).group(1)
AX = {}
for m in re.finditer(r'(\w+):\{code:"([^"]+)", label:"[^"]*"(?:, from:\[([^\]]*)\])?, tip:"([^"]+)"\}', ax_block):
    AX[m.group(1)] = dict(code=m.group(2), frm=re.findall(r'"(\w+)"', m.group(3) or ""), tip=m.group(4))
PR = [dict(id=m.group(1), label=m.group(2), who=m.group(3), frm=re.findall(r'"(\w+)"', m.group(4)))
      for m in re.finditer(r'\{id:"(\w+)", label:"([^"]+)", who:"([^"]+)", part:\d, from:\[([^\]]*)\]\}', script)]
assert len(AX) == 8 and len(PR) == 15, (len(AX), len(PR))
code = lambda k: AX[k]["code"]
lines = ["", "**Карта вывода** — из чего следует каждая аксиома и каждый принцип:", ""]
for k, a in AX.items():
    if a["frm"]:
        lines.append(f"- {a['code']} ← {', '.join(map(code, a['frm']))}")
for p in PR:
    lines.append(f"- {p['label']} ({p['who']}) ← {', '.join(map(code, p['frm']))}")
derivation_md = "\n".join(lines) + "\n"

# --- чистим HTML перед pandoc ---
h = re.search(r"<main[^>]*>(.*)</main>", src, re.S).group(1)
# ссылка страницы на этот же markdown в самом markdown не нужна
h = re.sub(r' <a href="axioms.md">.*?</a>[^<]*', "", h)
h = re.sub(r'<div class="map-wrap">.*?</div>\s*<p class="map-cap">.*?</p>', "<p>@@DERIVATION@@</p>", h, flags=re.S)

def fig(m):
    label = re.search(r'aria-label="([^"]+)"', m.group(0)).group(1)
    texts = [t for t in re.findall(r"<text[^>]*>([^<]+)</text>", m.group(0))]
    return f"<p><em>{label}.</em> Надписи на схеме: {'; '.join(texts)}.</p>"
h = re.sub(r"<svg.*?</svg>", fig, h, flags=re.S)

# бейджи аксиом в подписи принципа -> «Из: А1, А2»
def byline(m):
    inner = m.group(1)
    badges = re.findall(r'<a class="ax[^"]*"[^>]*>([^<]+)</a>', inner)
    who = re.sub(r"<[^>]+>", "", re.sub(r'<a class="ax.*', "", inner, flags=re.S)).strip()
    return f"<p><em>{who}</em>" + (f" · из {', '.join(badges)}" if badges else "") + "</p>"
h = re.sub(r'<div class="byline">(.*?)</div>', byline, h, flags=re.S)
# тег в чек-листе (аксиома или автор) -> «**А1.**»
h = re.sub(r'<span class="tag">(?:<a class="ax[^"]*"[^>]*>)?([^<]+)(?:</a>)?</span>', r"<strong>\1.</strong> ", h)
# факты и аксиомы: <dt>А1</dt><dd><b>Заголовок</b>текст -> абзац с якорем
h = re.sub(r'<div id="(ax-\w+)"><dt>([^<]+)</dt><dd><b>(.*?)</b>(.*?)</dd></div>',
           r'<p id="\1"><strong>\2. \3.</strong> \4</p>', h, flags=re.S)
h = re.sub(r"</?dl[^>]*>", "", h)
# номер части -> в заголовок: «## I. Границы»
h = re.sub(r'<span class="part-num">([IVX]+)</span>\s*<div><h2>', r"<div><h2>\1. ", h)
# код: вывод mypy — текст, остальное — Python
h = re.sub(r"<pre><code>(?=error:)", '<pre class="text"><code>', h)
h = h.replace("<pre><code>", '<pre class="python"><code>')
h = re.sub(r'<p class="code-tag[^"]*">(.*?)</p>', r"<p><strong>\1</strong></p>", h)
h = re.sub(r'<span class="lead[^"]*">(.*?)</span>', r"<strong>\1</strong>", h)
h = re.sub(r'<aside class="author"[^>]*>\s*<h4>(.*?)</h4>', r"<h4>Об авторе: \1</h4>", h)

md = subprocess.run(["pandoc", "-f", "html", "-t", "gfm-raw_html", "--wrap=none"],
                    input=h, capture_output=True, text=True, check=True).stdout
md = md.replace("@@DERIVATION@@", derivation_md.strip())
md = re.sub(r"\n{3,}", "\n\n", md)
md = re.sub(r"^``` (\w+)$", r"```\1", md, flags=re.M)

header = (
    "<!-- Сгенерировано из index.html скриптом build_md.py. Правится index.html, этот файл пересобирается. -->\n\n"
    "> Текстовая версия трактата для чтения агентами и в редакторе. "
    "Оформленная версия с интерактивной картой вывода: https://chorus12.github.io/axioms/\n\n"
)
sys.stdout.write(header + md)
