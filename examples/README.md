# 输出示例

## 通过的插件

```bash
$ python3 dshio_checker.py @liangjiehappy/dsh-dshio
```

```json
{
  "plugin": "@liangjiehappy/dsh-dshio",
  "baseline_dsh": "0.2.2-rc.1",
  "resolved": {"version": "1.0.1"},
  "conforming": true,
  "summary": {"pass": 10, "fail": 0, "skip": 5, "manual": 2}
}
```

## 不符合的插件

检查器会指出哪条 failed，以及证据：

```json
{
  "clause": "5.1.3",
  "title": "package.json 必须含 dsh.bundle.patch",
  "status": "fail",
  "evidence": "manifest 里没有 dsh.bundle.patch 字段"
}
```

## manual 条款长什么样

```json
{
  "clause": "5.5.1",
  "title": "声明的权限必须与行为一致",
  "status": "manual",
  "evidence": "需要人读代码判断权限声明是否与实际行为一致"
}
```

**`manual` 不是「跳过」，是「检查器拒绝下结论」。**
