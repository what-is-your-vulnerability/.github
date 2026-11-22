#!/usr/bin/env python3
"""PR 규칙 점검과 Slack DM 알림. 표준 라이브러리만 쓴다.

룰셋(필수 검사·직접 push 금지·병합 방식 제한)을 쓸 수 없게 된 저장소에서, 규칙을 어긴 PR을 막지는 못해도
PR 작성자·assignee·reviewer에게만 Slack DM으로 알린다. GitHub Actions에서 돈다(서버 불필요).

환경변수
  GITHUB_TOKEN        Actions가 주는 토큰(읽기 + 커밋 상태 쓰기)
  GITHUB_EVENT_NAME   Actions가 주는 값
  GITHUB_EVENT_PATH   Actions가 주는 값. 이벤트 JSON 경로
  GITHUB_REPOSITORY   Actions가 주는 값
  SLACK_BOT_TOKEN     Slack 앱의 Bot 토큰(Secret). 없으면 알림 없이 결과만 출력
  SLACK_USER_MAP      {"github-login": "Uxxxxxxx", ...} 형식 JSON(Secret)
  DRY_RUN=1           Slack으로 보내지 않고 메시지만 출력
  GRACE_SECONDS       이벤트 뒤 기다릴 시간(기본 120). 작성자가 assignee·reviewer를 바로 붙일 시간을 준다
  IGNORE_LOGINS       점검을 건너뛸 계정(쉼표 구분, 기본 dependabot[bot],taki-jenkins)
  PUSH_CHECK=0        push 점검을 끈다(직접 push가 정상인 저장소)

PR 제목·본문·브랜치 이름은 작성자가 정하는 값이다. 셸에 넣지 않고 이 스크립트가 JSON으로만 읽는다.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

TITLE_KINDS = ("feat", "fix", "refactor", "chore", "ci", "style", "docs", "test")
BRANCH_KINDS = ("feature", "fix", "refactor", "docs", "chore")
TITLE_RE = re.compile(r"^(%s): \S.*$" % "|".join(TITLE_KINDS))
BRANCH_RE = re.compile(r"^(%s)/[A-Za-z0-9][A-Za-z0-9._-]*$" % "|".join(BRANCH_KINDS))
SECTIONS = ("## 관련 작업", "## 변경 내용", "## 검증", "## 영향 및 협업 요청", "## 확인 사항")
STATUS_CONTEXT = "pr-rules"
WATCH_ACTIONS = {
    "opened",
    "reopened",
    "edited",
    "ready_for_review",
    "assigned",
    "unassigned",
    "review_requested",
    "review_request_removed",
}
PROTECTED = ("dev", "main")


# ---------- 규칙(순수 함수: 네트워크 없이 시험한다) ----------


def field_filled(body: str, label: str) -> bool:
    """`- 라벨:` 줄에 값이 있거나, 바로 아래 들여쓴 목록에 값이 있으면 채워진 것으로 본다."""
    lines = body.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^- %s:\s*(.*)$" % re.escape(label), line)
        if not m:
            continue
        if m.group(1).strip():
            return True
        for nxt in lines[i + 1 :]:
            if re.match(r"^- \S", nxt) or nxt.startswith("## "):
                break
            if re.match(r"^\s+- \S", nxt):
                return True
        return False
    return False


def check_open_rules(pr: dict, reviewer_candidates: list[str] | None = None) -> list[str]:
    """열린 PR의 형식 규칙. 어긴 항목을 '무엇을 어떻게 고치면 되는지'와 함께 돌려준다.

    reviewer_candidates가 있으면 그중 1명 이상이 reviewer에 있어야 한다(작성자 본인은 후보에서 제외). 그 밖의 사람은 자유롭게 추가할 수 있다."""
    out: list[str] = []
    title = pr.get("title") or ""
    body = pr.get("body") or ""
    head = (pr.get("head") or {}).get("ref") or ""
    base = (pr.get("base") or {}).get("ref") or ""

    if not TITLE_RE.match(title):
        out.append("제목 형식: `종류: 변경 내용 [KAN-번호]` (종류는 %s)" % ", ".join(TITLE_KINDS))
    if not BRANCH_RE.match(head):
        out.append("브랜치 이름: `종류/번호-설명` (종류는 %s). 현재 `%s`" % (", ".join(BRANCH_KINDS), head))
    if base == "main" and head != "dev":
        out.append("main으로 가는 PR은 dev에서만 보낼 수 있음. 현재 출처 `%s`" % head)

    missing = [s for s in SECTIONS if s not in body]
    if missing:
        out.append("PR 템플릿 섹션 누락: " + ", ".join(m.replace("## ", "") for m in missing))
    else:
        if not re.search(r"Jira:.*KAN-\d+", body):
            out.append("관련 작업의 Jira에 `KAN-번호`가 없음")
        for label in ("변경 이유", "실행한 명령", "확인한 결과"):
            if not field_filled(body, label):
                out.append("`%s` 항목이 비어 있음" % label)
        if re.search(r"^- `변경 파일`\s*$", body, re.M):
            out.append("템플릿 예시 줄(`변경 파일`·`변경 함수`)이 그대로 남아 있음")

    author = ((pr.get("user") or {}).get("login") or "").lower()
    assignees = [(u.get("login") or "").lower() for u in pr.get("assignees") or []]
    if not assignees:
        out.append("Assignees 미지정")
    elif author and author not in assignees:
        out.append("Assignees에 작성자 `%s`가 없음(작성자를 assignee로 지정)" % ((pr.get("user") or {}).get("login")))

    reviewers = [r.lower() for r in (pr.get("_reviewers") or [])]
    eligible = [c for c in (reviewer_candidates or []) if c.lower() != author]
    if not reviewers:
        out.append("Reviewers 미지정" + (" (%s 중 1명 이상)" % ", ".join(eligible) if eligible else ""))
    elif eligible and not {c.lower() for c in eligible} & set(reviewers):
        out.append("Reviewers에 지정 대상 중 1명 이상이 없음: %s (다른 사람은 추가로 지정 가능)" % ", ".join(eligible))
    return out


def check_merge_rules(base: str, parent_count: int | None, check_conclusions: dict[str, str | None]) -> list[str]:
    """병합된 PR 규칙. 룰셋의 필수 검사와 병합 방식 제한을 사후에 확인한다."""
    out: list[str] = []
    required = ["test"] + (["main-source-guard"] if base == "main" else [])
    for name in required:
        res = check_conclusions.get(name)
        if res is None:
            out.append("필수 검사 `%s` 결과 없이 병합됨" % name)
        elif res != "success":
            out.append("필수 검사 `%s`가 `%s`인 채로 병합됨" % (name, res))
    if parent_count is not None:
        if base == "dev" and parent_count != 1:
            out.append("dev 병합은 Squash and merge여야 함(병합 커밋으로 들어감)")
        if base == "main" and parent_count != 2:
            out.append("main 병합은 Create a merge commit이어야 함(squash·rebase로 들어감)")
    return out


def signature(violations: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(violations)).encode()).hexdigest()[:8]


# ---------- GitHub·Slack 호출 ----------


class Api:
    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.token = token

    def _req(self, method: str, url: str, data: dict | None = None):
        req = urllib.request.Request(
            url,
            method=method,
            data=json.dumps(data).encode() if data is not None else None,
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "pr-rule-notify",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 고정된 api.github.com 주소
            raw = r.read()
        return json.loads(raw) if raw else None

    def get(self, path: str):
        return self._req("GET", "https://api.github.com/repos/%s%s" % (self.repo, path))

    def post(self, path: str, data: dict):
        return self._req("POST", "https://api.github.com/repos/%s%s" % (self.repo, path), data)


def reviewers_of(api: Api, number: int, pr: dict) -> list[str]:
    names = [u["login"] for u in pr.get("requested_reviewers") or []]
    names += ["@team:" + t["slug"] for t in pr.get("requested_teams") or []]
    for rv in api.get("/pulls/%d/reviews?per_page=100" % number) or []:
        login = (rv.get("user") or {}).get("login")
        if login and login != (pr.get("user") or {}).get("login"):
            names.append(login)
    return sorted(set(names))


def check_conclusions(api: Api, sha: str) -> dict[str, str | None]:
    runs = (api.get("/commits/%s/check-runs?per_page=100" % sha) or {}).get("check_runs", [])
    res: dict[str, str | None] = {}
    for r in runs:  # 같은 이름이 여러 번이면 가장 나중 결과
        res[r["name"]] = r.get("conclusion")
    return res


def recipients_of(pr: dict, extra: list[str] | None = None) -> list[str]:
    names = [(pr.get("user") or {}).get("login")]
    names += [a["login"] for a in pr.get("assignees") or []]
    names += [u for u in (pr.get("_reviewers") or []) if not u.startswith("@team:")]
    names += extra or []
    return sorted({n for n in names if n})


def send_slack(token: str, user_map: dict[str, str], logins: list[str], text: str, dry: bool) -> None:
    lowered = {k.lower(): v for k, v in user_map.items()}
    for login in logins:
        uid = lowered.get(login.lower())
        if not uid:
            print("  Slack 매핑 없음, 건너뜀: %s" % login)
            continue
        if dry or not token:
            print("  [DRY] DM -> %s\n%s" % (login, text))
            continue
        req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            method="POST",
            data=json.dumps({"channel": uid, "text": text}).encode(),
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 고정된 slack.com 주소
                ok = json.loads(r.read()).get("ok")
        except (urllib.error.URLError, ValueError) as e:
            print("  Slack 호출 실패(%s): %s" % (login, type(e).__name__))
            continue
        print("  DM %s: %s" % (login, "전송" if ok else "실패(응답 ok=false)"))


def build_text(repo: str, title: str, url: str, violations: list[str], heading: str) -> str:
    lines = ["*%s* — %s" % (heading, repo), "<%s|%s>" % (url, title or "(제목 없음)"), ""]
    lines += ["• " + v for v in violations]
    return "\n".join(lines)


def already_notified(api: Api, sha: str, sig: str) -> bool:
    try:
        for st in (api.get("/commits/%s/status" % sha) or {}).get("statuses", []):
            if st.get("context") == STATUS_CONTEXT and (st.get("description") or "").startswith("[%s]" % sig):
                return True
    except urllib.error.URLError:
        pass
    return False


def set_status(api: Api, sha: str, violations: list[str], sig: str, url: str) -> None:
    state = "failure" if violations else "success"
    desc = ("[%s] " % sig + ("; ".join(violations) if violations else "규칙 확인 통과"))[:140]
    try:
        api.post("/statuses/%s" % sha, {"state": state, "context": STATUS_CONTEXT, "description": desc, "target_url": url})
    except urllib.error.URLError as e:
        print("커밋 상태 기록 실패: %s" % type(e).__name__)


# ---------- 이벤트 처리 ----------


def handle_pull_request(api: Api, event: dict, env: dict) -> int:
    action = event.get("action")
    pr = event["pull_request"]
    ignore = {x.strip().lower() for x in env.get("IGNORE_LOGINS", "dependabot[bot],taki-jenkins").split(",") if x.strip()}
    if (pr.get("user") or {}).get("login", "").lower() in ignore:
        print("점검 제외 계정")
        return 0
    number = pr["number"]
    dry = env.get("DRY_RUN") == "1"
    user_map = json.loads(env.get("SLACK_USER_MAP") or "{}")
    token = env.get("SLACK_BOT_TOKEN", "")

    if action == "closed":
        if not pr.get("merged"):
            return 0
        base = pr["base"]["ref"]
        merge_sha = pr.get("merge_commit_sha")
        parents = None
        if merge_sha:
            parents = len((api.get("/commits/%s" % merge_sha) or {}).get("parents", []))
        violations = check_merge_rules(base, parents, check_conclusions(api, pr["head"]["sha"]))
        pr["_reviewers"] = reviewers_of(api, number, pr)
        print("병합 점검 #%d: %s" % (number, violations or "문제 없음"))
        if violations:
            text = build_text(api.repo, pr["title"], pr["html_url"], violations, "병합 규칙 위반")
            send_slack(token, user_map, recipients_of(pr), text, dry)
        return 0

    if action not in WATCH_ACTIONS:
        return 0
    if pr.get("draft"):
        print("Draft PR은 점검하지 않음")
        return 0

    grace = int(env.get("GRACE_SECONDS", "120"))
    if grace > 0:
        print("%d초 기다린 뒤 최신 상태로 점검" % grace)
        time.sleep(grace)
    pr = api.get("/pulls/%d" % number)  # 기다린 사이 바뀐 값(assignee·reviewer·본문)을 반영
    if pr.get("state") != "open" or pr.get("draft"):
        return 0
    pr["_reviewers"] = reviewers_of(api, number, pr)
    candidates = [x.strip() for x in (env.get("REVIEWER_CANDIDATES") or "").split(",") if x.strip()]
    violations = check_open_rules(pr, candidates)
    sig = signature(violations)
    print("점검 #%d: %s" % (number, violations or "문제 없음"))

    sha = pr["head"]["sha"]
    notified = already_notified(api, sha, sig)
    set_status(api, sha, violations, sig, pr["html_url"])
    if violations and not notified:
        text = build_text(api.repo, pr["title"], pr["html_url"], violations, "PR 규칙 확인 필요")
        send_slack(token, user_map, recipients_of(pr), text, dry)
    elif violations:
        print("같은 위반으로 이미 알림을 보냄")
    return 0


def handle_push(api: Api, event: dict, env: dict) -> int:
    if env.get("PUSH_CHECK") == "0":
        return 0
    ref = event.get("ref", "")
    branch = ref.removeprefix("refs/heads/")
    if branch not in PROTECTED:
        return 0
    pusher = (event.get("sender") or {}).get("login", "")
    ignore = {x.strip().lower() for x in env.get("IGNORE_LOGINS", "dependabot[bot],taki-jenkins").split(",") if x.strip()}
    if pusher.lower() in ignore:
        return 0
    violations: list[str] = []
    if event.get("forced"):
        violations.append("`%s`에 force push 됨" % branch)
    sha = event.get("after")
    if sha and not event.get("deleted"):
        prs = api.get("/commits/%s/pulls" % sha) or []
        if not prs:
            violations.append("`%s`에 PR 없이 직접 push 됨(커밋 %s)" % (branch, sha[:7]))
    print("push 점검 %s: %s" % (branch, violations or "문제 없음"))
    if violations:
        url = (event.get("head_commit") or {}).get("url") or ""
        text = build_text(api.repo, "%s push" % branch, url, violations, "브랜치 규칙 위반")
        send_slack(
            env.get("SLACK_BOT_TOKEN", ""),
            json.loads(env.get("SLACK_USER_MAP") or "{}"),
            [pusher],
            text,
            env.get("DRY_RUN") == "1",
        )
    return 0


def main() -> int:
    env = dict(os.environ)
    event = json.load(open(env["GITHUB_EVENT_PATH"], encoding="utf-8"))
    api = Api(env["GITHUB_REPOSITORY"], env.get("GITHUB_TOKEN", ""))
    name = env.get("GITHUB_EVENT_NAME")
    if name == "pull_request":
        return handle_pull_request(api, event, env)
    if name == "push":
        return handle_push(api, event, env)
    print("처리하지 않는 이벤트: %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
