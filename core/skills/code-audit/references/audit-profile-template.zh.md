<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 审计画像模板（Audit Profile Template）

当项目没有审计画像（profile），或用户要求定义/修订画像时，使用本模板。

## 目录

1. [字段依据](#field-rationale)
2. [项目审计画像模板](#project-audit-profile-template)

## 字段依据

- NIST CSF Profiles：当前/目标姿态、层级、成果、治理与供应链情境。
- NIST RMF 与 SP 800-53B 裁剪：系统分类、使命/业务情境、影响、风险容忍度与裁剪后的基线。
- NIST SSDF：覆盖 Prepare、Protect、Produce、Respond 的安全开发成果。
- OWASP ASVS：应用安全验证等级与需求标识符。
- SEI ATAM：质量属性场景与架构权衡评估。
- AWS Well-Architected 与 Google SRE：工作负载边界、卓越运营、可靠性、SLO、错误预算、可观测性与改进行动。
- SLSA/OpenSSF：源码、依赖、构建来源（provenance）与工件完整性期望。

## 项目审计画像模板

```markdown
# Project Audit Profile

Status: Draft | Approved
Owner:
Last reviewed:
Review cadence:

## 1. System Context
- Project/workload boundary:
- Primary users and stakeholders:
- Business or mission goals:
- Critical user/business workflows:
- Crown-jewel data, assets, and secrets:
- External systems and third-party dependencies:
- Deployment environments:
- Legal, privacy, regulatory, or contractual constraints:

## 2. Risk And Impact Classification
- Security impact: Low | Moderate | High; rationale:
- Privacy/data impact: Low | Moderate | High; rationale:
- Availability/reliability impact: Low | Moderate | High; rationale:
- Financial/operational impact: Low | Moderate | High; rationale:
- Risk tolerance and explicit non-goals:
- Most expensive failure modes:
- Realistic abuse cases and threat actors:

## 3. Quality Attribute Priorities
| Attribute | Priority | Target or Scenario | Evidence |
| --- | --- | --- | --- |
| Correctness |  |  |  |
| Security |  |  |  |
| Reliability |  |  |  |
| Modifiability |  |  |  |
| Performance |  |  |  |
| Operability |  |  |  |
| Cost |  |  |  |

## 4. Required Audit Coverage
- Always inspect:
- Rotate each audit:
- Recently changed or high-churn areas:
- Public entry points and external interfaces:
- Auth, authorization, tenant/data isolation, and trust boundaries:
- Persistence, migrations, retention, deletion, backup, and restore:
- Background jobs, queues, retries, concurrency, and idempotency:
- Release, deployment, rollback, configuration, and feature flags:
- Observability, alerts, runbooks, and incident recovery:
- Exclusions and rationale:

## 5. Security Verification Baseline
- Target ASVS or equivalent level:
- Required threat model or abuse-case coverage:
- Required security controls:
- Secure-development expectations:
- Vulnerability disclosure, triage, and response expectations:

## 6. Reliability And Operations Baseline
- Critical SLOs/SLIs or equivalent reliability targets:
- Error budget or release-risk policy:
- Backup/restore and disaster-recovery expectations:
- Degraded-mode and emergency-disable expectations:
- Required operational evidence:

## 7. Supply Chain And Build Baseline
- Dependency and license policy:
- Lockfile, vendoring, and generated-code policy:
- Build provenance, artifact integrity, and release-signing expectations:
- CI/CD permission and secret boundaries:
- SBOM or dependency inventory expectations:

## 8. AI-Agent And Tooling Baseline
- Agent/tooling used in this repository:
- Allowed autonomy and required human approval gates:
- Agent identities, tokens, sandboxing, and network/tool permissions:
- MCP/connectors/plugins/hooks policy:
- Untrusted content and prompt-injection boundaries:
- Agent-generated artifact retention and publication policy:

## 9. Sampling And Severity Calibration
- Minimum sampling strategy:
- Must Fix:
- Should Plan:
- Track as Debt:
- No Action:
- Evidence required before a finding can be reported:
```
