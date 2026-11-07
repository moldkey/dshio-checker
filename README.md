# dshio-checker

**Conformance checker for the DSHIO/T 10 plugin standard.**
**DSHIO/T 10 插件标准的合规检查器。**

Checks whether a DSH plugin satisfies the automatically checkable clauses of
DSHIO/T 10—2026.

[中文说明见下方](#中文说明) · Standard: [github.com/moldkey/dshio.org](https://github.com/moldkey/dshio.org) · [dshio.org](https://dshio.org)

---

## Why open source

When a developer is told "non-conforming", the fair question is: **"On what grounds?"**

This repository is the answer: **look at the code — the check for clause 5.5.3 is right here.**

We do not want you to trust a black box. The checker runs the same way on your
machine, so you can reproduce the same result locally.

---

## Usage

```bash
python3 dshio_checker.py dsh-pet
python3 dshio_checker.py @scope/dsh-foo --json
```

**Requirements:** Python 3.8+, `pyyaml` (optional — full YAML parsing when present,
a built-in minimal parser otherwise)

```bash
pip install pyyaml
```

**No tarball download needed.** The manifest comes from the npm registry; the patch
file is fetched from unpkg / jsDelivr.

---

## Output

```json
{
  "plugin": "dsh-pet",
  "baseline_dsh": "0.2.2-rc.1",
  "resolved": {"version": "1.2.3"},
  "conforming": true,
  "summary": {"pass": 10, "fail": 0, "skip": 5, "manual": 2},
  "results": [
    {"clause": "5.1.1", "title": "Declare as a DSH plugin", "status": "pass"}
  ]
}
```

**Four statuses:**

| Status | Meaning |
|---|---|
| `pass` | Clause satisfied |
| `fail` | Clause not satisfied |
| `skip` | Clause not applicable to this plugin (reason given) |
| `manual` | **Human judgement only** — the checker refuses to conclude |

---

## Clauses covered

Only the **automatically checkable** clauses of DSHIO/T 10:

| Clause | Severity | What is checked |
|---|---|---|
| **5.1.1** | critical | Declares itself a DSH plugin (`package.json` contains `dsh.bundle.patch`) |
| **5.1.2** | critical | Patch file exists and is fetchable from a CDN |
| **5.1.3** | critical | Patch file is valid YAML |
| **5.1.4** | critical | Patch contains an `insert` list |
| **5.1.5** | critical | Every entry has `id` and `name` |
| **5.2.1** | minor | Declares a DSH version range (recommended) |
| **5.2.2** | critical | Version range includes the baseline version |
| **5.2.3** | critical | Has a `main` or `exports` entry |
| **5.3.1** | major | `files` includes what is needed at runtime |
| **5.3.2** | critical | No local absolute-path dependencies |
| **5.4.1–5.4.4** | critical | Install / list / mount / boot (needs sandbox — reported as `skip` here) |
| **5.5.1** | major | Tool `description` states when to use it — **manual only** |
| **5.5.2** | major | Declared permissions match actual behaviour — **manual only** |
| **5.5.3** | major | No red-line permission combination |

---

## Important: the checker does not decide conformance

The checker emits **clause-level** pass/fail/skip/manual only.

The **overall verdict** (conforming / conditionally conforming / non-conforming) must
be composed according to DSHIO/T 10 §7.3.2, and must handle `manual` clauses —
those are deliberately left without a conclusion.

**Therefore:**
- `conforming: true` means "all automatically checkable clauses pass".
  It does **not** mean the manual clauses pass.
- The checker does not replace a full type test.

---

## Current scope

The checker performs **T0 static checks only** (DSHIO/T 10 chapter 6.1).

T1–T4 require a sandbox and are not in this repository.
T5 (model-dependent) is **planned and not offered**.

Web check entry point: https://deepseekbase.com/zh/check/

---

## License

MIT. See [LICENSE](LICENSE).

The standard text is CC BY 4.0 — see the
[dshio.org repository](https://github.com/moldkey/dshio.org).

---

## Independence

DSHIO is an independent third-party standards body with no affiliation to DeepSeek.

This checker is not an official tool, and its verdicts are not official conclusions.

---

# 中文说明

**DSHIO/T 10 插件标准的合规检查器。**

检查一个 DSH 插件是否满足 DSHIO/T 10—2026 中可自动判定的条款。

## 为什么开源

开发者被判定「不符合」时会问：**「你凭什么？」**

这个仓库就是回答：**看代码，5.5.3 条的检查逻辑在这里。**

我们不想让你相信一个黑盒。检查器跟你用同样的工具跑，你可以在本地复现同样的结果。

## 用法

```bash
python3 dshio_checker.py dsh-pet
python3 dshio_checker.py @scope/dsh-foo --json
```

**依赖：** Python 3.8+，`pyyaml`（可选 —— 装了就做完整 YAML 解析，没装用内置简易解析）

**不需要下载 tarball。** 从 npm registry 取 manifest，从 unpkg / jsDelivr 取 patch 文件。

## 输出的四种状态

| 状态 | 含义 |
|---|---|
| `pass` | 满足该条款 |
| `fail` | 不满足 |
| `skip` | 该条款对本插件不适用（附理由） |
| `manual` | **只能人工判断** —— 检查器不给结论 |

## 覆盖的条款

只覆盖 DSHIO/T 10 中**可自动判定**的条款：

| 条款 | 严重度 | 检查内容 |
|---|---|---|
| 5.1.1 | critical | 声明为 DSH 插件（`package.json` 含 `dsh.bundle.patch`）|
| 5.1.2 | critical | patch 文件存在且可从 CDN 取到 |
| 5.1.3 | critical | patch 文件是合法 YAML |
| 5.1.4 | critical | patch 含 `insert` 列表 |
| 5.1.5 | critical | 每个 entry 有 `id` 与 `name` |
| 5.2.1 | minor | 声明 DSH 版本范围（宜）|
| 5.2.2 | critical | 版本范围包含基准版本 |
| 5.2.3 | critical | 有 `main` 或 `exports` 入口 |
| 5.3.1 | major | `files` 含运行所需文件 |
| 5.3.2 | critical | 不依赖本地绝对路径 |
| 5.4.1–5.4.4 | critical | 能安装 / 列装 / 挂载 / 启动（需沙箱，本仓库标 skip）|
| 5.5.1 | major | 工具的 `description` 说清使用场景 —— **只能人工** |
| 5.5.2 | major | 声明的权限与行为一致 —— **只能人工** |
| 5.5.3 | major | 不出现红线权限组合 |

## 重要：检查器不判「符合」

检查器只给出**条款级**的 pass/fail/skip/manual。

**总体判定**（符合 / 有条件符合 / 不符合）需要按 DSHIO/T 10 §7.3.2 的规则组合，
且必须处理 `manual` 条款 —— 那些条款检查器故意不给结论。

**所以：**
- `conforming: true` = 自动可判的条款全过，**不代表人工条款也过**
- 检查器不替代完整型式检验

## 当前实施范围

检查器只做 **T0 静态检查**（DSHIO/T 10 第 6.1 章）。

T1–T4 需要沙箱运行，不在本仓库。T5（模型相关）**待规划**，不提供。

## 许可

MIT。标准文本用 CC BY 4.0。

## 独立性

DSHIO 是独立第三方标准组织，与 DeepSeek 无隶属关系。
本检查器不是官方工具，判定结果不是官方结论。
