# cece-agent

`cece-agent` 是基于 **HKUDS/nanobot** 扩展的“测试专家能力包”，专注：

1. 测试用例设计（Test Case Generation）
2. 测试用例评审（Test Case Review）

> 设计原则：不重造 agent 框架，仅通过 nanobot 原生机制（skill + prompt + workflow + memory）扩展。

---

## 1. nanobot 架构分析（简要）

### 1.1 Agent Loop
- 主循环由 `AgentLoop` 组织：构建上下文 → 调用模型 → 执行工具 → 回写结果 → 迭代直到完成。
- `AgentRunner` 把这套循环封装为可复用执行器，子任务也可复用该 runner。

### 1.2 Tool / Skill 扩展
- **Tool**：通过 `ToolRegistry` 注册，提供 schema + execute；由模型函数调用触发。
- **Skill**：通过 `SKILL.md` 定义角色、流程与约束；可在运行时按需读取。

### 1.3 Memory
- `MEMORY.md`：长期稳定策略（如测试策略、质量准则）。
- `HISTORY.md`：历史执行记录（如已评审用例、缺陷模式）。

### 1.4 Prompt 注入
- system instruction 由 identity、skills summary、memory、runtime context 等拼装。

### 1.5 子 Agent / 任务分解
- 支持子任务管理，可将“用例生成”与“用例评审”拆分为两个子 agent 工作流。

---

## 2. cece-agent 设计方案

### 2.1 推荐实现方式
- 用 `skills/cece_agent/SKILL.md` 约束行为和输出结构。
- 用 `skills/cece_agent/prompts.py` 管理 prompt 模板（system/generation/review）。
- 用轻量 Python 模块提供输入校验与结构化输出：
  - `test_case_generator.py`
  - `test_case_reviewer.py`

### 2.2 能力定义

#### A. 用例生成
输入：PRD / 用户故事 / 接口文档 / 功能描述。
输出：结构化 JSON，用例字段：
- id
- feature
- title
- preconditions
- steps
- test_data
- expected_result
- priority
- case_type

覆盖维度：
- normal
- error
- edge
- validation
- state transition
- permission（如适用）
- frontend 页面场景（如适用）：渲染、交互反馈、导航跳转、兼容性

#### B. 用例 Review
输入：已有测试用例（JSON 或表格）。
输出：
- 总体评价
- 问题分类（严重 / 一般 / 优化）
- 缺失测试点
- 改进建议
- 可选优化示例

---

## 3. 目录结构

```text
skills/
  cece_agent/
    SKILL.md
    prompts.py
    test_case_generator.py
    test_case_reviewer.py
```

---

## 4. Prompt 模板

已实现三类模板：
1. `SYSTEM_PROMPT`（测试专家 persona + 质量标准）
2. `GENERATION_PROMPT`（生成结构与强制覆盖项）
3. `REVIEW_PROMPT`（评审结构与必查清单）

见：`skills/cece_agent/prompts.py`。

---

## 5. 使用示例

### 5.1 输入需求 → 输出测试用例

```python
from skills.cece_agent.test_case_generator import TestCaseGenerator

feature = """
用户可以通过手机号+验证码登录。验证码 60 秒有效，错误 5 次锁定 10 分钟。
未注册手机号不可登录，管理员账号不可使用手机号登录。
"""

prompt = TestCaseGenerator.build_prompt(feature)
print(prompt)  # 交给 LLM

cases = [
    {
        "id": "TC-001",
        "feature": "登录",
        "title": "手机号验证码登录成功",
        "preconditions": ["用户已注册", "验证码未过期"],
        "steps": ["输入手机号", "输入正确验证码", "点击登录"],
        "test_data": {"phone": "13800000000", "otp": "123456"},
        "expected_result": ["登录成功", "创建会话", "跳转首页"],
        "priority": "P0",
        "case_type": "normal",
    }
]

issues = TestCaseGenerator.validate_cases(cases)
print(issues)
enriched = TestCaseGenerator.enrich_frontend_scenarios(feature, cases)
print(TestCaseGenerator.to_json(enriched))
```

### 5.2 输入测试用例 → 输出 review

```python
from skills.cece_agent.test_case_reviewer import TestCaseReviewer

existing_cases = [
    {
        "id": "TC-003",
        "feature": "登录",
        "title": "验证码错误",
        "preconditions": ["用户已注册"],
        "steps": ["输入手机号", "输入错误验证码", "点击登录"],
        "test_data": {"phone": "13800000000", "otp": "111111"},
        "expected_result": ["提示验证码错误"],
        "priority": "P1",
        "case_type": "error",
    }
]

prompt = TestCaseReviewer.build_prompt(test_cases=str(existing_cases), feature_context="登录模块")
print(prompt)  # 交给 LLM
print(TestCaseReviewer.quick_diagnostics(existing_cases))
```

---

## 6. 与 nanobot 集成建议

1. 将 `skills/cece_agent` 放入 nanobot 的 skill 搜索路径。
2. 在 agent 配置中启用该 skill（可 always_on 或按需激活）。
3. 将评审结论写入 `HISTORY.md`，将稳定测试策略沉淀到 `MEMORY.md`。
4. 若任务复杂，启用子 agent：
   - generator 子 agent：生成候选用例
   - reviewer 子 agent：做质量审查
   - 主 agent 汇总并输出最终结果
