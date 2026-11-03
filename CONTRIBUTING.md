# 팀 협업 규칙

서비스 개발 저장소에 적용할 Gitflow 운영안입니다. 팀 검토 후 확정하며, 실제 브랜치 보호와 CI 설정은 각 개발 저장소에서 별도로 적용합니다. 조직 공통 양식 저장소인 `.github`는 `main`을 기준으로 관리합니다.

## 1. 브랜치

| 브랜치 | 용도 | 시작점 | PR 대상 |
| --- | --- | --- | --- |
| `main` | 시연·배포 기준 | 기존 배포 이력 | 해당 없음 |
| `develop` | 개발 내용 통합 | 최초 `main` | release 생성 기준 |
| `feature/KAN-123-task-name` | 기능 추가 | `develop` | `develop` |
| `fix/KAN-123-task-name` 등 | 오류 수정·문서·환경 작업 | `develop` | `develop` |
| `release/0.1.0` | 배포 전 검증·필수 수정 | `develop` | `main` |
| `hotfix/KAN-123-task-name` | 배포된 버전의 긴급 수정 | `main` | `main` |

`KAN-123`은 예시입니다. 실제 Jira 작업 번호와 영문 소문자 작업명을 사용합니다. 일반 작업 접두사는 `feature`, `fix`, `docs`, `chore`, `ci`, `test`, `refactor`를 사용하며, 작업 하나당 브랜치 하나를 만듭니다.

서비스 개발 저장소의 `main`·`develop`에는 직접 푸시하지 않고 PR로 반영합니다. 브랜치 보호 적용 전에는 팀 규칙으로 준수합니다.

## 2. 커밋과 PR 제목

일반 작업의 커밋과 PR 제목은 `종류: 변경 내용 [KAN-번호]` 형식으로 작성합니다.

```text
feat: 진단 요청 API 추가 [KAN-123]
fix: 작업 상태 조회 오류 수정 [KAN-124]
ci: 백엔드 테스트 실행 추가 [KAN-125]
```

종류는 `feat`, `fix`, `docs`, `chore`, `ci`, `test`, `refactor`를 사용합니다. Jira 번호는 해당 작업 브랜치의 번호와 맞춥니다. release PR은 `release: v0.1.0`, 동기화 PR은 `chore: main 변경 사항 develop 반영`처럼 작성하며 Jira 번호를 필수로 요구하지 않습니다.

## 3. PR과 리뷰

PR에는 관련 Jira 작업, 변경 내용, 검증 결과, 미검증 항목과 이유, 다른 파트에 미치는 영향을 작성합니다. 미완성 작업은 Draft PR로 공유합니다.

작성자 외 최소 1명의 승인을 받고, 리뷰 지적 사항을 해결한 뒤 병합합니다. CI를 구성한 이후에는 필수 검사 통과도 병합 조건으로 적용합니다. API 키·비밀번호·개인정보는 커밋하지 않으며, 환경변수는 실제 값 대신 `.env.example`에 필요한 항목을 기록합니다.

## 4. 병합과 배포

| 경로 | 병합 방식 |
| --- | --- |
| 일반 작업 → `develop` | Squash and merge |
| 배포 준비용 수정 → `release/*` | Squash and merge |
| `release/*` 또는 `hotfix/*` → `main` | Create a merge commit |
| `main` → `develop` | Create a merge commit |

`develop`의 배포 준비가 끝나면 release 브랜치를 만들고, 검증 후 `main`에 병합합니다. release에서는 새 기능 추가를 중단하며, 필요한 수정은 해당 release에서 `fix`, `docs`, `chore`, `ci`, `test` 브랜치를 만들어 PR로 반영합니다.

release·hotfix를 `main`에 반영한 뒤에는 `main` → `develop` PR로 변경을 동기화합니다. hotfix 당시 진행 중인 release가 있으면 해당 수정도 반영하고 검증합니다. 배포 확인 후 `main`의 해당 커밋에 버전 태그를 부여합니다.

병합한 작업 브랜치는 삭제할 수 있지만 `main`·`develop`은 유지합니다. 공유 브랜치의 커밋 기록 재작성은 팀 협의 없이 진행하지 않습니다.
