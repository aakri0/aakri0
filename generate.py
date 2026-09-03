import os
import requests
from pathlib import Path

USERNAME = os.environ["USER_NAME"]
TOKEN = os.environ["ACCESS_TOKEN"]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

def graphql(query, variables):
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]

query = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, first: 1) {
      totalCount
    }
    contributionsCollection {
      contributionCalendar { totalContributions }
    }
    repositoriesContributedTo(
      first: 1
      contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]
    ) {
      totalCount
    }
  }
}
"""

user = graphql(query, {"login": USERNAME})["user"]

repos = user["repositories"]["totalCount"]
followers = user["followers"]["totalCount"]
contributions = user["contributionsCollection"]["contributionCalendar"]["totalContributions"]
contributed = user["repositoriesContributedTo"]["totalCount"]

star_query = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, first: 100, after: $cursor) {
      nodes { stargazerCount }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""

stars = 0
cursor = None

while True:
    page = graphql(star_query, {"login": USERNAME, "cursor": cursor})["user"]["repositories"]
    stars += sum(repo["stargazerCount"] for repo in page["nodes"])

    if not page["pageInfo"]["hasNextPage"]:
        break

    cursor = page["pageInfo"]["endCursor"]


def make_svg(dark=False):
    if dark:
        background, foreground = "#0d1117", "#e6edf3"
        key, value, muted = "#79c0ff", "#a5d6ff", "#8b949e"
    else:
        background, foreground = "#f6f8fa", "#24292f"
        key, value, muted = "#0550ae", "#0a3069", "#57606a"

    rows = [
        ("Repos", str(repos)),
        ("Stars", str(stars)),
        ("Contributions", f"{contributions:,}"),
        ("Contributed to", str(contributed)),
        ("Followers", str(followers)),
    ]

    parts = [
        f'<text x="28" y="38" font-family="monospace" font-size="20" '
        f'font-weight="700" fill="{foreground}">aakri0@github</text>',
        f'<text x="28" y="66" font-family="monospace" font-size="14" '
        f'fill="{muted}">GitHub Stats</text>'
    ]

    y = 96
    for k, v in rows:
        parts.append(
            f'<text x="28" y="{y}" font-family="monospace" font-size="15" fill="{muted}">. </text>'
            f'<text x="48" y="{y}" font-family="monospace" font-size="15" fill="{key}">{k}</text>'
            f'<text x="190" y="{y}" font-family="monospace" font-size="15" fill="{muted}">: </text>'
            f'<text x="205" y="{y}" font-family="monospace" font-size="15" fill="{value}">{v}</text>'
        )
        y += 28

    height = y + 12
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="{height}" '
        f'viewBox="0 0 760 {height}">'
        f'<rect width="760" height="{height}" rx="12" fill="{background}"/>'
        + "".join(parts)
        + "</svg>"
    )


Path("stats-light.svg").write_text(make_svg(False), encoding="utf-8")
Path("stats-dark.svg").write_text(make_svg(True), encoding="utf-8")
