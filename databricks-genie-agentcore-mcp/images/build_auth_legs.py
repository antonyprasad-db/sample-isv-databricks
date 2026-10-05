"""Regenerate auth-legs.svg: the two independent auth legs of this sample.

Companion to build_architecture.py and deliberately styled to match it, so the
figures in the README and in the write-up read as one set. No icons are needed,
so unlike build_architecture.py this script has no --icons path and no cache: it
is self-contained and reproducible from a clean checkout.

    python build_auth_legs.py
    rsvg-convert -w 1872 auth-legs.svg -o auth-legs.png

1872 is twice the 936px width AWS Builder Center serves images at, so the PNG
stays crisp on a high-density display without shipping wasted pixels.
"""

W, H = 1720, 1080

INK = "#232F3E"
MUTED = "#5A6B7B"
LINE = "#57728B"
TEAL = "#01A88D"
RED = "#FF3621"
TEAL_BG = "#F1FAF8"
RED_BG = "#FEF3F1"

p = []
a = p.append

a(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="Helvetica Neue, Helvetica, Arial, sans-serif">'
)
a(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
a("<defs>")
a(
    f'<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
    f'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{LINE}"/></marker>'
)
a("</defs>")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=14, fill=INK, weight=None, anchor="start", mono=False):
    w = f' font-weight="{weight}"' if weight else ""
    fam = ' font-family="SFMono-Regular, Menlo, Consolas, monospace"' if mono else ""
    a(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}"{w} text-anchor="{anchor}"{fam}>{esc(s)}</text>')


# ------------------------------------------------------------------ title
text(40, 46, "Two independent auth legs, and the grant each one needs", 24, INK, "700")
text(
    40,
    73,
    "Inbound authorizes the caller into the Gateway. Outbound decides which Databricks identity runs "
    "the SQL. Neither implies the other.",
    15,
    MUTED,
)

# ------------------------------------------------------------------ lifelines
COLS = [
    (160, "MCP client", "invoke.py or", "AgentCore Runtime"),
    (505, "Amazon Cognito", "user pool", "token endpoint"),
    (850, "AgentCore Gateway", "mcpServer", "target"),
    (1195, "AgentCore Identity", "OAuth2 credential", "provider"),
    (1545, "Databricks", "workspace", "/oidc + Genie MCP"),
]
TOP, BOT = 215, 835
for x, name, s1, s2 in COLS:
    text(x, 136, name, 15.5, INK, "600", "middle")
    text(x, 156, s1, 13.5, MUTED, None, "middle")
    text(x, 174, s2, 13.5, MUTED, None, "middle")
    a(f'<path d="M {x} {TOP} L {x} {BOT}" stroke="#C8D2DC" stroke-width="1.5"/>')

X = {k: c[0] for k, c in zip(["client", "cognito", "gw", "id", "dbx"], COLS)}


def band(y, tone, bg, word, gloss):
    a(f'<rect x="96" y="{y - 19}" width="124" height="28" rx="14" fill="{bg}"/>')
    text(158, y, word, 14, tone, "700", "middle")
    text(238, y, gloss, 14, tone)


def msg(y, x1, x2, caption, n, mono=False):
    a(f'<path d="M {x1} {y} L {x2} {y}" stroke="{LINE}" stroke-width="2" marker-end="url(#ah)"/>')
    mid = (x1 + x2) / 2
    text(mid, y - 11, caption, 13.5, INK, None, "middle", mono)
    a(f'<circle cx="{mid}" cy="{y + 25}" r="13" fill="{INK}"/>')
    text(mid, y + 30, str(n), 13.5, "#FFFFFF", "700", "middle")


def note(x, y, s):
    text(x, y, s, 13.5, MUTED)


# ------------------------------------------------------------------ inbound
band(258, TEAL, TEAL_BG, "INBOUND", "who may call the Gateway at all")
msg(305, X["client"], X["cognito"], "client_credentials grant", 1, mono=True)
msg(368, X["cognito"], X["client"], "short-lived JWT access token", 2)
msg(431, X["client"], X["gw"], "MCP initialize + tools/list, Bearer JWT", 3)
note(
    X["gw"] + 30,
    486,
    "Gateway validates the JWT against the pool's OIDC discovery URL (CUSTOM_JWT authorizer)",
)

# ------------------------------------------------------------------ outbound
band(548, RED, RED_BG, "OUTBOUND", "which Databricks identity actually runs the SQL")
msg(595, X["gw"], X["id"], "GetResourceOauth2Token", 4, mono=True)
msg(658, X["id"], X["dbx"], "client_credentials, scope=genie, at /oidc/v1/token", 5, mono=True)
msg(721, X["dbx"], X["gw"], "service principal access token", 6)
msg(784, X["gw"], X["dbx"], "tools/call -> Genie Agent MCP endpoint", 7, mono=True)

# ------------------------------------------------------------------ what bites
a(f'<rect x="96" y="886" width="232" height="30" rx="15" fill="{RED_BG}"/>')
text(212, 906, "Two things that bite here", 14, RED, "700", "middle")

LEFT = [
    "Measured in this sample, not documented: the secret is read per gateway",
    "SESSION, not per token lifetime. One question that called query_space and",
    "then poll_response produced two GetSecretValue calls 21 seconds apart, from",
    "two different gateway-session role sessions. Budget KMS Decrypt per tool",
    "call, not per hour, on a customer-managed key.",
]
RIGHT = [
    "The grant step fails closed, and late. Omit the gateway role's",
    "GetResourceOauth2Token or GetSecretValue grant and the target still reaches",
    "READY, then every tool call fails immediately. A READY target is not",
    "evidence that the outbound leg works, only a real query is.",
]
for i, ln in enumerate(LEFT):
    note(100, 948 + i * 22, ln)
for i, ln in enumerate(RIGHT):
    note(900, 948 + i * 22, ln)

a("</svg>")

with open("auth-legs.svg", "w") as f:
    f.write("\n".join(p))
print("wrote auth-legs.svg")
