"""Regenerate architecture.svg for the databricks-genie-agentcore-mcp sample.

The committed architecture.svg embeds its icons as data URIs, so it is
self-contained: it renders in GitHub, in a browser, and through rsvg-convert
with no external assets. This script is the source used to produce it, so a
future icon refresh or layout change is an edit here rather than a rebuild by
hand.

The Amazon Bedrock, Amazon Cognito and Amazon CloudWatch marks come from the
official AWS Architecture Icons toolkit (https://aws.amazon.com/architecture/icons/,
04302026 release). The Amazon Bedrock AgentCore mark is a separate brand export --
the toolkit release used here ships no AgentCore service icon -- and Runtime /
Gateway / Identity each reuse that one mark with a text label, the same convention
as the AgentCore workshops in this repo.

Usage:
    python build_architecture.py             # rebuild from the committed icons_b64.json cache
    python build_architecture.py --icons /path/to/icon-root  # refresh the cache
    rsvg-convert -w 2064 architecture.svg -o architecture.png

The committed icons_b64.json holds every mark as a data URI, so a clean checkout
rebuilds the SVG with no external assets. ICON_SOURCES is used only when that
cache is absent: it maps each AWS mark to its path inside the unpacked toolkit,
and Databricks marks to the Databricks brand icon set.
"""

import argparse
import base64
import json
import os

# The only entry the AWS toolkit release does not ship. A refresh may fall back to the
# committed export for THIS key alone -- falling back for any missing icon turned
# `--icons /wrong/path` into a silent success that rewrote the cache with itself.
OPTIONAL_ICONS = {"agentcore"}

ICON_SOURCES = {
    # Amazon Bedrock AgentCore mark: a standalone brand export, not shipped in the
    # AWS Architecture Icons toolkit release used here. The committed icons_b64.json
    # is its source of truth; this path is a best-effort fallback for a future
    # toolkit release that adds an AgentCore service icon.
    "agentcore": "Architecture-Service-Icons_04302026/Arch_Artificial-Intelligence/64/Arch_Amazon-Bedrock-AgentCore_64.svg",
    # AWS Architecture Icons toolkit (Asset-Package_04302026)
    "bedrock": "Architecture-Service-Icons_04302026/Arch_Artificial-Intelligence/64/Arch_Amazon-Bedrock_64.svg",
    "cognito": "Architecture-Service-Icons_04302026/Arch_Security-Identity/64/Arch_Amazon-Cognito_64.svg",
    "secrets-manager": "Architecture-Service-Icons_04302026/Arch_Security-Identity/64/Arch_AWS-Secrets-Manager_64.svg",
    "cloudwatch": "Architecture-Service-Icons_04302026/Arch_Management-Tools/64/Arch_Amazon-CloudWatch_64.svg",
    # Databricks brand icons
    "connectors": "databricks/connectors.png",
    "chat": "databricks/chat.png",
    "unity-catalog": "databricks/unity-catalog.png",
    "delta-table": "databricks/delta-table.png",
    "sql-warehouse": "databricks/data-warehouse-1.png",
    "data-analyst-persona": "databricks/data-analyst-persona.png",
}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--icons",
    default=None,
    help="Root holding the unpacked AWS toolkit and a databricks/ folder.",
)
parser.add_argument("--cache", default="icons_b64.json", help="Data-URI cache.")
args = parser.parse_args()

# Use argparse's own signal rather than re-scanning sys.argv: a manual scan misses the
# abbreviations argparse accepts (--icon, --ic), which silently took the cache path.
_icons_explicit = args.icons is not None


def load_icons() -> dict:
    """Return {name: data-URI}, reading from source icons or a local cache.

    The cache short-circuit only applies when --icons was not passed explicitly.
    icons_b64.json is committed, so it always exists in a clean checkout, which made
    the documented `--icons /path/to/icon-root` refresh a silent no-op: the user
    got "wrote architecture.svg" and the old icons.
    """
    cached = {}
    if os.path.exists(args.cache):
        try:
            with open(args.cache) as f:
                cached = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            # A truncated or hand-edited cache must not break the documented refresh path,
            # which is exactly the command someone runs to rebuild it.
            print(f"  ignoring unreadable {args.cache}: {exc}")
            cached = {}
        if cached and not _icons_explicit:
            return cached

    icons = {}
    for name, rel in ICON_SOURCES.items():
        path = os.path.join(args.icons or ".", rel)
        if not os.path.exists(path):
            # Only OPTIONAL_ICONS may fall back, and only when the cache actually has it.
            # Anything else missing means the --icons root is wrong, and the run must fail
            # rather than quietly rewrite the cache with its own contents.
            if name in OPTIONAL_ICONS and name in cached:
                print(f"  {name}: not in this toolkit release, keeping the committed icon")
                icons[name] = cached[name]
                continue
            raise SystemExit(
                f"Icon not found: {path}\n--icons must point at a root holding BOTH the unpacked AWS "
                f"Architecture Icons asset package and a databricks/ folder with the Databricks marks."
            )
        mime = "image/svg+xml" if path.endswith(".svg") else "image/png"
        with open(path, "rb") as f:
            blob = base64.b64encode(f.read()).decode()
        icons[name] = f"data:{mime};base64,{blob}"

    with open(args.cache, "w") as f:
        json.dump(icons, f)
    return icons


ICONS = load_icons()

W, H = 1720, 1010

INK = "#232F3E"  # AWS squid ink, body text
MUTED = "#5A6B7B"  # secondary labels
LINE = "#57728B"
BOX_AWS_BG = "#FBF6EF"
BOX_AWS_EDGE = "#ED7100"
BOX_AC_BG = "#F1FAF8"
BOX_AC_EDGE = "#01A88D"
BOX_DBX_BG = "#FEF3F1"
BOX_DBX_EDGE = "#FF3621"

p = []
a = p.append

a(
    f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="Helvetica Neue, Helvetica, Arial, sans-serif">'
)
a(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

a("<defs>")
a(
    f'<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
    f'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{LINE}"/></marker>'
)
a(
    f'<marker id="ahd" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
    f'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{MUTED}"/></marker>'
)
a("</defs>")


def box(x, y, w, h, label, bg, edge, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{bg}" stroke="{edge}" stroke-width="2"{d}/>')
    a(f'<text x="{x + 18}" y="{y + 27}" font-size="17" font-weight="600" fill="{edge}">{label}</text>')


def node(cx, cy, icon, title, sub=None, sub2=None, size=60):
    a(f'<image x="{cx - size / 2}" y="{cy - size / 2}" width="{size}" height="{size}" xlink:href="{ICONS[icon]}"/>')
    ty = cy + size / 2 + 21
    a(f'<text x="{cx}" y="{ty}" font-size="15.5" font-weight="600" fill="{INK}" text-anchor="middle">{title}</text>')
    if sub:
        a(f'<text x="{cx}" y="{ty + 18}" font-size="13.5" fill="{MUTED}" text-anchor="middle">{sub}</text>')
    if sub2:
        a(f'<text x="{cx}" y="{ty + 35}" font-size="13.5" fill="{MUTED}" text-anchor="middle">{sub2}</text>')


def arrow(x1, y1, x2, y2, dashed=False):
    d = ' stroke-dasharray="6 5"' if dashed else ""
    m = "ahd" if dashed else "ah"
    col = MUTED if dashed else LINE
    a(f'<path d="M {x1} {y1} L {x2} {y2}" fill="none" stroke="{col}" stroke-width="2"{d} marker-end="url(#{m})"/>')


def elbow(x1, y1, x2, y2, dashed=False):
    """Right-angle connector: horizontal from the source, then vertical."""
    d = ' stroke-dasharray="6 5"' if dashed else ""
    m = "ahd" if dashed else "ah"
    col = MUTED if dashed else LINE
    a(
        f'<path d="M {x1} {y1} L {x2} {y1} L {x2} {y2}" fill="none" stroke="{col}" '
        f'stroke-width="2"{d} marker-end="url(#{m})"/>'
    )


def label(x, y, text, anchor="middle", mono=False, small=False):
    fam = ' font-family="SFMono-Regular, Menlo, Consolas, monospace"' if mono else ""
    fs = 13 if small else 14
    a(f'<text x="{x}" y="{y}" font-size="{fs}" fill="{INK}" text-anchor="{anchor}"{fam}>{text}</text>')


# ---------------------------------------------------------------- helpers
def badge(cx, cy, n):
    """Numbered call-flow marker. The prose walks these in order."""
    a(f'<circle cx="{cx}" cy="{cy}" r="14" fill="{INK}"/>')
    a(
        f'<text x="{cx}" y="{cy + 5}" font-size="14" font-weight="700" fill="#FFFFFF" '
        f'text-anchor="middle">{n}</text>'
    )


def pill(x, y, w, text_, bg, fg):
    a(f'<rect x="{x}" y="{y}" width="{w}" height="30" rx="15" fill="{bg}"/>')
    a(
        f'<text x="{x + w / 2}" y="{y + 20}" font-size="14" font-weight="700" fill="{fg}" '
        f'text-anchor="middle">{text_}</text>'
    )


# ---------------------------------------------------------------- title
a(
    f'<text x="40" y="46" font-size="24" font-weight="700" fill="{INK}">'
    f"Databricks Genie as a governed MCP tool, via Amazon Bedrock AgentCore</text>"
)
a(
    f'<text x="40" y="73" font-size="15" fill="{MUTED}">'
    f"Machine-to-machine OAuth2 end to end \u2014 Genie executes as a Databricks service principal, "
    f"and Unity Catalog audits it as that principal</text>"
)

# ---------------------------------------------------------------- business analyst
node(80, 330, "data-analyst-persona", "Business", "analyst", size=52)

# ---------------------------------------------------------------- AWS account
box(165, 110, 845, 700, "AWS account", BOX_AWS_BG, BOX_AWS_EDGE)
box(192, 150, 790, 320, "Amazon Bedrock AgentCore", BOX_AC_BG, BOX_AC_EDGE)

node(310, 258, "agentcore", "AgentCore Runtime", "Strands agent")
node(600, 258, "agentcore", "AgentCore Gateway", "mcpServer target")
node(885, 258, "agentcore", "AgentCore Identity", "credential provider")

node(300, 672, "cognito", "Amazon Cognito", "inbound auth \u2014 CUSTOM_JWT", size=52)
node(600, 672, "bedrock", "Amazon Bedrock", "composes the answer", size=52)
node(885, 672, "secrets-manager", "Secrets Manager", "Databricks OAuth secret", size=52)

# ---------------------------------------------------------------- Databricks
box(1062, 110, 628, 700, "Databricks workspace on AWS", BOX_DBX_BG, BOX_DBX_EDGE)

node(1232, 212, "connectors", "Managed MCP server", "Genie Agent endpoint", size=54)
node(1232, 388, "chat", "Genie Agent", "Trusted Assets", size=54)
node(1232, 560, "sql-warehouse", "SQL warehouse", "executes the SQL", size=54)
node(1232, 724, "delta-table", "Delta tables", "governed data", size=54)
node(1568, 560, "unity-catalog", "Unity Catalog", "authorizes + audits", "as the service principal", size=54)

# ---------------------------------------------------------------- call flow
arrow(114, 322, 272, 276)
badge(196, 286, 1)

arrow(300, 344, 300, 634, dashed=True)
label(288, 430, "client_credentials", anchor="end", small=True)
label(288, 450, "grant \u2192 JWT", anchor="end", small=True)
badge(300, 500, 2)

arrow(340, 344, 586, 634, dashed=True)
label(548, 556, "invoke model", anchor="start", small=True)

arrow(352, 250, 556, 250)
label(454, 226, "MCP session \u00b7 Bearer JWT", small=True)
badge(454, 300, 3)

arrow(646, 250, 841, 250)
label(744, 226, "GetResourceOauth2Token", small=True)
badge(744, 300, 4)

a(
    f'<path d="M 885 344 L 885 634" fill="none" stroke="{MUTED}" stroke-width="2" '
    f'stroke-dasharray="6 5" marker-end="url(#ahd)"/>'
)
label(873, 414, "reads the secret, mints an", anchor="end", small=True)
label(873, 434, "OAuth2 M2M token at", anchor="end", small=True)
label(873, 454, "/oidc/v1/token", anchor="end", small=True, mono=True)

a(
    f'<path d="M 630 222 L 630 178 L 1205 178 L 1205 194" fill="none" stroke="{LINE}" '
    f'stroke-width="2" marker-end="url(#ah)"/>'
)
label(800, 168, "MCP / HTTPS \u00b7 the service principal\u2019s access token", small=True)
badge(1120, 178, 5)

arrow(1232, 246, 1232, 350)
badge(1232, 298, 6)

arrow(1232, 426, 1232, 522)
label(1244, 478, "governed SQL", anchor="start", small=True)

arrow(1232, 598, 1232, 686)

arrow(1520, 560, 1300, 560, dashed=True)

a(
    f'<path d="M 1062 782 L 430 782" fill="none" stroke="{LINE}" '
    f'stroke-width="2" marker-end="url(#ah)"/>'
)
label(770, 772, "tool result, returned to the Runtime", small=True)
badge(560, 782, 7)

# ---------------------------------------------------------------- the point
pill(165, 848, 470, "Genie runs as the service principal, not as the person asking", BOX_DBX_BG, BOX_DBX_EDGE)
for i, ln in enumerate(
    [
        "Unity Catalog attributes every statement to the service principal configured in the outbound "
        "OAuth2 credential provider. That is the right",
        "model for a shared, application-level integration, and it is explicitly NOT per-user "
        "authorization. The identity-and-attribution figure",
        "shows which principal lands in which audit log, and what you can and cannot answer from them.",
    ]
):
    a(f'<text x="165" y="{906 + i * 22}" font-size="14" fill="{MUTED}">{ln}</text>')

a("</svg>")

# encoding is explicit: the SVG carries U+2014, U+00B7 and U+2019, so relying on the
# locale default raised UnicodeEncodeError under LC_ALL=C (CI, slim containers) and
# silently wrote non-UTF-8 bytes under a latin-1 locale. The file has no XML
# declaration, so renderers assume UTF-8 per the XML spec.
with open("architecture.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(p))
print("wrote architecture.svg")
