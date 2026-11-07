# dshio-checker

**DSHIO/T 10 插件标准的合规检查器。**

检查一个 DSH 插件是否满足 DSHIO/T 10—2026 中可自动判定的条款。

标准原文：[github.com/moldkey/dshio.org](https://github.com/moldkey/dshio.org) · 网页版 [dshio.org](https://dshio.org)

---

## 为什么开源

开发者被判定「不符合」时会问：**「你凭什么？」**

这个仓库就是回答：**看代码，第 5.2.2 条的检查逻辑在这里。**

我们不想让你相信一个黑盒。检查器跟你用同样的工具跑，你可以在本地复现同样的结果。

---

## 用法

```bash
python3 dshio_checker.py dsh-pet
python3 dshio_checker.py @scope/dsh-foo --json
```

**依赖：** Python 3.8+，`pyyaml`（可选 —— 装了就做完整 YAML 解析，没装用内置简易解析）

```bash
pip install pyyaml
```

**不需要下载 tarball。** 从 npm registry 取 manifest，从 unpkg / jsDelivr 取 patch 文件。

---

## 输出

```json
{
  "plugin": "dsh-pet",
  "baseline_dsh": "0.2.2-rc.1",
  "resolved": {"version": "1.2.3"},
  "conforming": true,
  "summary": {"pass": 10, "fail": 0, "skip": 5, "manual": 2},
  "results": [
    {"clause": "5.1.3", "title": "package.json 必须含 dsh.bundle.patch", "status": "pass"}
  ]
}
```

**四种状态：**

| 状态 | 含义 |
|---|---|
| `pass` | 满足该条款 |
| `fail` | 不满足 |
| `skip` | 该条款对本插件不适用（附理由） |
| `manual` | **只能人工判断** —— 检查器不给结论 |

---

## 覆盖的条款

检查器只覆盖 DSHIO/T 10 中 **可自动判定** 的条款：

| 条款 | 严重度 | 检查内容 |
|---|---|---|
| **5.1.1** | critical | 声明为 DSH 插件（`package.json` 含 `dsh.bundle.patch`）|
| **5.1.2** | critical | patch 文件存在（可从 CDN 取到）|
| **5.1.3** | critical | patch 文件是合法 YAML |
| **5.1.4** | critical | patch 含 `insert` 列表 |
| **5.1.5** | critical | 每个 entry 有 `id` 与 `name` |
| **5.2.1** | minor | 声明 DSH 版本范围（宜）|
| **5.2.2** | critical | 版本范围包含基准版本 |
| **5.2.3** | critical | 有 `main` 或 `exports` 入口 |
| **5.3.1** | major | `files` 含运行所需文件 |
| **5.3.2** | critical | 不依赖本地绝对路径 |
| **5.4.1–5.4.4** | critical | 能安装 / 列装 / 挂载 / 启动（需沙箱，本仓库只标 skip）|
| **5.5.1** | major | 工具的 `description` 说清使用场景 —— **只能人工** |
| **5.5.2** | major | 声明的权限与行为一致 —— **只能人工** |
| **5.5.3** | major | 不出现红线权限组合 |

---

## 重要：检查器不判「符合」

检查器只给出**条款级的 pass/fail/skip/manual**。

**总体判定（符合 / 有条件符合 / 不符合）需要按 DSHIO/T 10 §7.3.2 的规则组合**，
且必须处理 `manual` 条款 —— 那些条款检查器故意不给结论。

**所以：**
- 检查器说 `conforming: true` = 自动可判的条款全过，**不代表人工条款也过**
- 检查器不替代完整型式检验

---

## 当前实施范围

检查器只做 **T0 静态检查**（DSHIO/T 10 第 6.1 章）。

T1–T4 需要沙箱运行，不在本仓库。T5（模型相关）**待规划**，不提供。

网页版检查入口：https://deepseekbase.com/zh/check/

---

## 许可

MIT。见 [LICENSE](LICENSE)。

标准文本用 CC BY 4.0，见 [dshio.org 仓库](https://github.com/moldkey/dshio.org)。

---

## 独立性

DSHIO 是独立第三方标准组织，与 DeepSeek 无隶属关系。

本检查器不是官方工具，判定结果不是官方结论。
