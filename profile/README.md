<div align="center">
  <img src="./taki-banner.svg" alt="TAKI — Threat Analysis & Knowledge Intelligence" width="100%" />

  <h1>Team: 너의 취약점은</h1>
  <p><strong>설계서엔 있는데, 코드엔 없는 보안 통제를 찾습니다.</strong></p>
  
  <p>AI 기반 보안 취약점 진단 에이전트 <strong>TAKI</strong> 개발 팀</p>

  <p>
    <a href="https://github.com/what-is-your-vulnerability">프로젝트 살펴보기</a>
    &nbsp;
  </p>
</div>

---

## Why TAKI?

보안 도구가 경고를 보여줘도, **설계에서 요구한 통제가 실제 코드에 있는지**는 사람이 여러 파일을 따라가며 확인해야 할 때가 많습니다. TAKI는 그 간격을 좁히기 위해 만들고 있습니다.

<p align="center">
  <strong>설계문서 + 소스코드</strong> &nbsp;→&nbsp; <strong>위협과 통제</strong> &nbsp;→&nbsp; <strong>구현 점검</strong> &nbsp;→&nbsp; <strong>근거 있는 리포트</strong>
</p>

| 01 · 위협을 읽다 | 02 · 코드를 따라가다 | 03 · 근거를 남기다 |
| :--- | :--- | :--- |
| 설계문서에서 기능별 위협과 필요한 보안 통제를 도출합니다. | 관련 진입점과 호출 흐름을 살펴 통제의 구현 여부를 점검합니다. | 위치, 위험 사유, 판정 근거, 수정 방향과 위험도를 정리합니다. |

설계문서가 없는 경우에는 코드의 진입점과 기존 보안 패턴을 바탕으로 점검 항목을 도출합니다. 정적 분석 도구의 경고도 프로젝트 맥락과 함께 검토합니다.

## What we're focusing on

|  | 중점 진단 항목 |
| :---: | :--- |
| `01` | **SQL Injection** · 입력값이 SQL 실행에 영향을 주는 경로 |
| `02` | **권한 검증 누락** · 사용자의 권한을 확인하지 않는 기능 |
| `03` | **고객정보 과다 노출** · 필요 이상으로 반환되거나 기록되는 정보 |
| `04` | **개인정보 암호화 누락** · 보호가 필요한 정보의 처리 과정 |

TAKI는 진단 결과마다 **왜 위험한지, 어떤 코드가 근거인지, 어떻게 고칠 수 있는지**를 함께 보여주는 것을 목표로 합니다. 최종 판단은 근거를 확인한 사람이 내릴 수 있도록 설계합니다.



---

<div align="center">
  <sub>TAKI · Threat Analysis &amp; Knowledge Intelligence</sub>
</div>
