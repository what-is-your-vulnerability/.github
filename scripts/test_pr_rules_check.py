"""pr_rules_check의 규칙 시험. 네트워크 없이 돈다. 실행: python3 -m unittest test_pr_rules_check -v"""

import unittest

import pr_rules_check as c

GOOD_BODY = """## 관련 작업
- 작업 번호(브랜치 이름의 번호): KAN-69
- Jira: [KAN-69](https://example.invalid/browse/KAN-69)
- 대상 브랜치: dev

## 변경 내용
- 변경 이유: 이유를 적음
- `src/a.py`
  - `f()`
    - 바꾼 내용

## 검증
- 실행한 명령:
  - `pytest`
- 확인한 결과: 통과
- 미검증 항목과 이유: 없음

## 영향 및 협업 요청
- API·DB·환경변수 변경: 없음
- 다른 파트에서 확인할 내용: 없음

## 확인 사항
- [x] 브랜치 이름이 맞음
"""


def pr(**kw):
    base = {
        "title": "chore: 설정을 추가한다 [KAN-69]",
        "body": GOOD_BODY,
        "head": {"ref": "chore/KAN-69-gitleaks"},
        "base": {"ref": "dev"},
        "assignees": [{"login": "dlkara"}],
        "_reviewers": ["zzl-hyun"],
    }
    base.update(kw)
    return base


class OpenRules(unittest.TestCase):
    def test_good_pr_has_no_violation(self):
        self.assertEqual(c.check_open_rules(pr()), [])

    def test_title_without_kind(self):
        self.assertTrue(any("제목 형식" in v for v in c.check_open_rules(pr(title="[KAN-69] 설정 추가"))))

    def test_title_kan_is_optional(self):
        self.assertEqual(c.check_open_rules(pr(title="docs: 문서를 고친다")), [])

    def test_branch_kind(self):
        v = c.check_open_rules(pr(head={"ref": "KAN-69-gitleaks"}))
        self.assertTrue(any("브랜치 이름" in x for x in v))

    def test_branch_without_number_is_allowed(self):
        self.assertEqual(c.check_open_rules(pr(head={"ref": "chore/pre-commit"})), [])

    def test_main_only_from_dev(self):
        v = c.check_open_rules(pr(base={"ref": "main"}, head={"ref": "chore/x"}))
        self.assertTrue(any("dev에서만" in x for x in v))
        self.assertEqual(c.check_open_rules(pr(base={"ref": "main"}, head={"ref": "dev"})), ["브랜치 이름: `종류/번호-설명` (종류는 feature, fix, refactor, docs, chore). 현재 `dev`"])

    def test_missing_section(self):
        v = c.check_open_rules(pr(body=GOOD_BODY.replace("## 검증", "## 확인")))
        self.assertTrue(any("섹션 누락" in x and "검증" in x for x in v))

    def test_empty_fields(self):
        body = GOOD_BODY.replace("- 변경 이유: 이유를 적음", "- 변경 이유:").replace("- 확인한 결과: 통과", "- 확인한 결과:")
        v = c.check_open_rules(pr(body=body))
        self.assertTrue(any("변경 이유" in x for x in v))
        self.assertTrue(any("확인한 결과" in x for x in v))

    def test_indented_list_counts_as_filled(self):
        self.assertTrue(c.field_filled(GOOD_BODY, "실행한 명령"))

    def test_missing_jira(self):
        v = c.check_open_rules(pr(body=GOOD_BODY.replace("KAN-69](", "x](").replace("Jira: [x]", "Jira: 없음").replace("KAN-69", "")))
        self.assertTrue(any("Jira" in x for x in v))

    def test_template_placeholder_left(self):
        v = c.check_open_rules(pr(body=GOOD_BODY + "\n- `변경 파일`\n"))
        self.assertTrue(any("예시 줄" in x for x in v))

    def test_no_assignee_no_reviewer(self):
        v = c.check_open_rules(pr(assignees=[], _reviewers=[]))
        self.assertIn("Assignees 미지정", v)
        self.assertIn("Reviewers 미지정", v)


class MergeRules(unittest.TestCase):
    def test_squash_on_dev_with_passing_test(self):
        self.assertEqual(c.check_merge_rules("dev", 1, {"test": "success"}), [])

    def test_failed_check_merged(self):
        v = c.check_merge_rules("dev", 1, {"test": "failure"})
        self.assertTrue(any("failure" in x for x in v))

    def test_missing_check(self):
        self.assertTrue(any("결과 없이" in x for x in c.check_merge_rules("dev", 1, {})))

    def test_merge_commit_on_dev(self):
        self.assertTrue(any("Squash" in x for x in c.check_merge_rules("dev", 2, {"test": "success"})))

    def test_main_needs_merge_commit_and_guard(self):
        v = c.check_merge_rules("main", 1, {"test": "success"})
        self.assertTrue(any("main-source-guard" in x for x in v))
        self.assertTrue(any("merge commit" in x for x in v))
        self.assertEqual(c.check_merge_rules("main", 2, {"test": "success", "main-source-guard": "success"}), [])


class Recipients(unittest.TestCase):
    def test_only_author_assignee_reviewer(self):
        p = pr(user={"login": "hj"}, assignees=[{"login": "dlkara"}], _reviewers=["zzl-hyun", "@team:infra"])
        self.assertEqual(c.recipients_of(p), ["dlkara", "hj", "zzl-hyun"])

    def test_duplicates_removed(self):
        p = pr(user={"login": "dlkara"}, assignees=[{"login": "dlkara"}], _reviewers=[])
        self.assertEqual(c.recipients_of(p), ["dlkara"])

    def test_signature_is_stable_and_order_free(self):
        self.assertEqual(c.signature(["a", "b"]), c.signature(["b", "a"]))
        self.assertNotEqual(c.signature(["a"]), c.signature(["b"]))


if __name__ == "__main__":
    unittest.main()
