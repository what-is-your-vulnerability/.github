# 팀 협업 규칙

TAKI 개발 저장소(엔진 `Threat-Analysis-Knowledge-Intelligence`, 서버 `taki-server`)에 적용하는 규칙입니다. 조직 공통 양식 저장소인 `.github`는 `main`을 기준으로 관리합니다. 아래 표에서 **적용됨**은 GitHub 설정에 이미 걸려 있는 것이고, **합의 필요**는 팀 확인 뒤에 정하는 것입니다.

## 1. 브랜치

```text
작업 브랜치  →  dev  →  main
   (squash)      (merge commit)
```

| 브랜치 | 용도 | 시작점 | PR 대상 |
| --- | --- | --- | --- |
| `main` | 시연·배포 기준 | - | 해당 없음 |
| `dev` | 개발 내용 통합 | `main` | `main` (dev에서만) |
| `feature/이슈번호-설명` | 기능 추가 | `dev` | `dev` |
| `fix/이슈번호-설명` | 오류 수정 | `dev` | `dev` |
| `refactor/이슈번호-설명` | 동작 변경 없는 구조 개선 | `dev` | `dev` |
| `docs/이슈번호-설명` | 문서 | `dev` | `dev` |
| `chore/이슈번호-설명` | 인프라·CI·배포·설정 | `dev` | `dev` |

- 이슈 번호는 GitHub 이슈 번호입니다. 예: `feature/38-path-view`
- 작업 하나당 브랜치 하나를 만들고, 설명은 영문 소문자와 `-`로 씁니다.
- `main`과 `dev`에는 직접 푸시하지 않고 PR로만 반영합니다. **적용됨**(브랜치 룰셋)
- `main`으로 가는 PR은 `dev`에서 온 것만 받습니다. `main-source-guard` 검사가 확인합니다. **적용됨**
- 병합한 작업 브랜치는 자동으로 삭제됩니다. **적용됨**

## 2. 병합

| 경로 | 병합 방식 |
| --- | --- |
| 작업 브랜치 → `dev` | Squash and merge |
| `dev` → `main` | Create a merge commit |

- `dev`는 squash만, `main`은 merge commit만 허용합니다. rebase 병합은 쓰지 않습니다. **적용됨**
- `main`을 squash하면 `dev`와 `main`의 이력이 갈라져 다음 PR에서 매번 충돌이 나기 때문입니다.
- 공유 브랜치(`main`, `dev`)의 force push와 삭제는 막혀 있습니다. **적용됨**

## 3. PR과 리뷰

- 템플릿(`PULL_REQUEST_TEMPLATE.md`)의 관련 이슈, 변경 내용, 검증 결과, 미검증 항목, 다른 파트에 미치는 영향을 채웁니다.
- 미완성 작업은 Draft PR로 공유합니다.
- 병합 조건: CI 검사 `test` 통과. `main` PR은 `main-source-guard`도 통과해야 합니다. **적용됨**
- 리뷰 승인 수: 현재 0입니다. 1명으로 올릴지는 **합의 필요**입니다.
- 인프라·CI·배포 파일(`.github/`, `deploy/`, `Dockerfile`, `Jenkinsfile`)은 `CODEOWNERS`에 따라 인프라 담당이 리뷰합니다. 승인을 필수로 할지는 **합의 필요**입니다.
- 리뷰 지적 사항은 해결한 뒤 병합합니다.

## 4. 커밋 메시지 (제안, 합의 필요)

`종류: 변경 내용 (#이슈번호)` 형식을 제안합니다.

```text
feat: 진단 요청 API 추가 (#38)
fix: 작업 상태 조회 오류 수정 (#41)
chore: CI에 pre-commit 실행 추가 (#45)
```

종류는 `feat`, `fix`, `refactor`, `docs`, `chore`, `test`를 씁니다. 합의되면 이 절을 확정합니다.

## 5. 비밀값과 평가 자료

- API 키, 비밀번호, 토큰, 개인정보는 커밋하지 않습니다. 로그와 스크린샷도 같습니다.
- 로컬 비밀값은 프로젝트 폴더의 `.env`와 `taki.yml`에만 두고 `.gitignore`로 제외합니다. 셸 설정 파일(`~/.zshrc`)에는 `export`하지 않습니다.
- 환경변수는 실제 값 대신 `.env.example`에 항목 이름만 적습니다.
- 저장소가 공개라서 Secret scanning과 Push protection을 켜 두었습니다. **적용됨**
- 평가 정답과 변형 대응 같은 비공개 평가 자료는 이 저장소들에 올리지 않습니다.

## 6. 버전 태그

엔진의 `v*` 태그(예: `v0.2.0`)는 서버가 의존성으로 고정해 받으므로 수정·삭제할 수 없습니다. **적용됨**(엔진·서버 모두) 새 버전은 새 태그로 만듭니다.
