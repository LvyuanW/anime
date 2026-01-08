# LLM 调用服务开发计划（实体抽取工序，独立服务）

## 1. 背景与现状
- 数据库与后端：当前后端仅提供项目/剧本/运行记录/候选实体/资产/别名的 CRUD 与查询接口，不包含任何 LLM 调用逻辑。
- 业务决定：已去除 evidence（不维护 `candidate_evidence`，候选仅存 `candidate_entity`），长文本上下文不在业务表中膨胀。
- 工序需求：实体抽取仍然需要 Step1～Step3 的“输入→LLM→输出→落库/流转”，因此 LLM 调用应由独立服务承担。

## 2. 目标与非目标
### 目标
- 提供可部署的独立 LLM 调用服务，串联 Step 1～Step 3，并把结果写回当前数据库/后端接口体系。
- 将提示词版本化与可追溯化，保证“同样输入 + 同样提示词版本”可复现。
- 长剧本可处理：支持分片、重试、断点续跑与幂等写入。

### 非目标
- 不在本计划阶段直接实现服务代码、不改动后端以外的生产部署。
- 不实现 Step4（资产卡生成）等扩展能力，除非后续明确需求。

## 3. 工序与数据契约（无证据口径）
### Step 1：剧本标准化
- 输入：`script.content`（原始剧本文本）
- 输出：写入 `normalized_script.content_json`（JSON 数组，含 `line_id`、`text`、`type`）
- 提示词：`documnts/01-资产抽取/提示词/资产抽取工序01.txt`

### Step 2：候选实体抽取（无证据）
- 输入：标准化剧本分片（按 scene 或按 token/行数分片）
- 输出：
  - 写入 `candidate_entity`（`raw_name`、`entity_type`、`confidence` 可选）
  - 写入 `artifact_snapshot`（可选但建议：保存分片级原始输出与聚合后的最终输出）
- 提示词：`documnts/01-资产抽取/提示词/资产抽取工序02.txt`

### Step 3：归一化与落库（无证据）
- 输入：
  - 某个 `run_uid` 下的候选实体集合（包含 `uid/raw_name/entity_type/confidence`）
  - 标准化剧本
  - 项目已有资产/别名（可选，用于增量归并）
- 输出：
  - 创建/更新 `canonical_asset` 与 `canonical_asset_alias`
  - 回填 `candidate_entity.canonical_asset_uid`
  - 产物存档到 `artifact_snapshot`
- 提示词：`documnts/01-资产抽取/提示词/资产抽取工序03.txt`

## 4. 系统架构选型（只做计划）
### 推荐架构（最小改动、可控演进）
- 独立服务（LLM Orchestrator）负责：
  - 拉取输入（通过后端 API）
  - 调用 LLM（可插拔 provider）
  - 解析/校验输出（JSON schema 校验 + 规则校验）
  - 写回结果（通过后端 API 或直连 DB）
  - 记录运行状态与产物快照

### 写回方式的两种方案
- 方案 A：直连数据库写入（最快落地）
  - 优点：不需要新增后端写入接口即可写 `normalized_script/candidate_entity/artifact_snapshot`
  - 风险：需要共享 DB 凭据、绕开后端约束与鉴权边界，运维与安全复杂
- 方案 B：补充后端“内部写入 API”（推荐）
  - 优点：统一数据校验与权限边界，便于审计与演进
  - 代价：需要后续在后端新增少量 internal endpoints

本计划默认以方案 B 为目标，早期 PoC 可用方案 A 快速验证效果，但需要明确迁移路径。

## 5. LLM 服务 API 设计（草案）
### 对外（给前端/运营/任务触发器）
- `POST /jobs/step1`：参数 `{project_uid, script_uid}`，返回 `{job_uid, run_uid}`
- `POST /jobs/step2`：参数 `{project_uid, script_uid}`，返回 `{job_uid, run_uid}`
- `POST /jobs/step3`：参数 `{project_uid, script_uid, source_run_uid}`，返回 `{job_uid, run_uid}`
- `GET /jobs/{job_uid}`：返回状态、进度、错误信息、关联 run_uid

### 对内（写回后端或数据库）
如果采用方案 B，后端需要补充：
- `POST /internal/normalized-scripts/`（写 Step1 产物）
- `POST /internal/candidates/bulk`（批量写候选实体）
- `POST /internal/artifacts/`（写 snapshot）
- 这些接口仅允许服务间鉴权访问

## 6. 运行与幂等策略
- 运行记录：
  - 每次 Step 1/2/3 先创建 `extraction_run`（status=running）
  - 完成后更新 status=completed；失败写 error_message
- 幂等写入：
  - Step1：以 `(script_uid, version)` 做幂等键（版本策略见下）
  - Step2：建议按 `(run_uid, raw_name, entity_type)` 做去重策略（由服务聚合，不依赖 DB 唯一约束）
  - Step3：以“cluster 输出 + 现有资产/别名”做增量合并，尽量避免重复创建资产
- 版本策略：
  - Step1 版本可采用 `v1/v2` 或使用内容 hash（推荐 hash），保证重跑可复用

## 7. 提示词管理与版本化
- 提示词位置：继续放在 `documnts/01-资产抽取/提示词`，以文件名作为基准入口。
- 版本化建议：
  - 将提示词文件内容做 hash（例如 sha256），写入 `extraction_run.model_config` 或 `artifact_snapshot`
  - 产物快照保存：输入摘要、提示词 hash、模型参数、原始输出、解析后的结构化输出

## 8. 输出校验与安全策略
- 输出校验：
  - 强制 JSON 输出；失败即重试（有限次数）
  - 针对字段枚举（entity_type/type）做白名单校验
  - raw_name 必须来源于输入文本（可选：抽样校验或严格校验）
- 安全：
  - API Key/密钥通过环境变量注入，不落库、不写日志
  - 服务间鉴权（mTLS 或 HMAC）用于 internal write API

## 9. 里程碑与交付物
### M0：设计冻结（本阶段交付）
- 提示词与数据契约冻结
- LLM 服务的 API 草案与写回方案决策

### M1：PoC（后续开发阶段）
- 支持 Step2：长剧本分片抽取候选并落库
- 产物快照可追溯（artifact_snapshot）

### M2：生产化
- 支持 Step1/Step3
- 断点续跑、幂等、重试、监控告警
- 内部写入 API（若采用方案 B）与服务间鉴权

## 10. 风险清单与应对
- 长文本与重复实体：通过分片 + 片段内去重 + 服务聚合去重缓解
- 误合并资产：Step3 先保守拆分，后续靠人工归并与别名调整
- 可复现性：强制记录提示词 hash、模型参数、输入摘要与原始输出

## 11. 当前提示词状态
- 已按“无证据口径”更新：
  - 工序01：标准化输出包含 `type`
  - 工序02：输出仅 candidates（raw_name/entity_type/confidence）
  - 工序03：输出为 clusters（name/type/description/aliases/candidate_uids）
