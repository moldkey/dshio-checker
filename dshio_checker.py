#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DSHIO 标准检查器

对插件执行 DSHIO/T 10 的 auto 类条款检查。
不需要下载 tarball：npm registry + unpkg/jsdelivr 取文件。

用法：
  python3 checker.py dsh-pet
  python3 checker.py @lianglee/dsh-foo --json
"""
import json
import re
import sys

try:
    import yaml as _yaml
except ImportError:
    _yaml = None
import urllib.parse
import urllib.request

CLAUSES_PATH = "/root/dshio/standards/DSHIO-T-10.json"
BASELINE_DSH = "0.2.2-rc.1"
TIMEOUT = 20
UA = "dshio-checker/1.0 (+https://dshio.org)"

CDN_TEMPLATES = [
    "https://unpkg.com/{pkg}@{ver}/{path}",
    "https://cdn.jsdelivr.net/npm/{pkg}@{ver}/{path}",
    "https://registry.npmmirror.com/{pkg}/{ver}/files/{path}",
]


# ── semver 简易实现 ──
def parse_ver(v):
    v = v.strip().lstrip("v")
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+.*)?$", v)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4) or "")


def cmp_ver(a, b):
    """-1 / 0 / 1，遵循 semver 预发布优先序"""
    for i in range(3):
        if a[i] != b[i]:
            return -1 if a[i] < b[i] else 1
    pa, pb = a[3], b[3]
    if pa == pb:
        return 0
    if not pa:
        return 1      # 正式版 > 预发布
    if not pb:
        return -1
    A, B = pa.split("."), pb.split(".")
    for x, y in zip(A, B):
        if x == y:
            continue
        xn, yn = x.isdigit(), y.isdigit()
        if xn and yn:
            return -1 if int(x) < int(y) else 1
        if xn:
            return -1
        if yn:
            return 1
        return -1 if x < y else 1
    return -1 if len(A) < len(B) else (1 if len(A) > len(B) else 0)


def range_includes(range_str, version):
    """判断 npm range 是否包含某版本

    语义说明（重要）：
      纯 semver 规则下，带预发布标识的版本只在与它 [major,minor,patch]
      完全相同的比较器出现预发布标识时才可能被满足。
      strict 语义下 0.2.2-rc.1 不满足 >=0.2.0-rc.2。

      但 DSH 实际用 includePrerelease=true（已实测：
      engines.dsh=">=0.2.0" 的包能在 dsh 0.2.2-rc.1 上安装成功）。
      本函数按 includePrerelease 语义实现 —— 与 DSH 的实际判定一致。
      如果将来 DSH 改成 strict，本函数必须同步改。
    """
    if not range_str:
        return None
    s = range_str.strip()
    v = parse_ver(version)
    if not v:
        return None
    if s in ("*", "", "x", "latest"):
        return True

    # 拆成多个比较项（空格或 || 分隔；|| 视为任一满足）
    for alt in s.split("||"):
        alt = alt.strip()
        if not alt:
            continue
        ok = True
        for tok in alt.split():
            tok = tok.strip()
            if not tok:
                continue
            m = re.match(r"^(>=|<=|>|<|=|\^|~)?\s*v?([0-9][0-9A-Za-z.\-+]*)$", tok)
            if not m:
                ok = False
                break
            op, vs = m.group(1) or "=", m.group(2)
            b = parse_ver(vs)
            if not b:
                ok = False
                break
            if op == "^":
                # ^0.2.2 → >=0.2.2 <0.3.0 ; ^1.2.3 → >=1.2.3 <2.0.0
                lo = b
                if b[0] > 0:
                    hi = (b[0] + 1, 0, 0, "")
                elif b[1] > 0:
                    hi = (0, b[1] + 1, 0, "")
                else:
                    hi = (0, 0, b[2] + 1, "")
                if not (cmp_ver(v, lo) >= 0 and cmp_ver(v, hi) < 0):
                    ok = False
                    break
            elif op == "~":
                lo = b
                hi = (b[0], b[1] + 1, 0, "")
                if not (cmp_ver(v, lo) >= 0 and cmp_ver(v, hi) < 0):
                    ok = False
                    break
            else:
                c = cmp_ver(v, b)
                if op == ">=" and c < 0:
                    ok = False
                elif op == ">" and c <= 0:
                    ok = False
                elif op == "<=" and c > 0:
                    ok = False
                elif op == "<" and c >= 0:
                    ok = False
                elif op == "=" and c != 0:
                    ok = False
            if not ok:
                break
        if ok:
            return True
    return False


# ── HTTP ──
def fetch(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        return None


def registry_url(pkg):
    return "https://registry.npmjs.org/" + urllib.parse.quote(pkg, safe="@").replace("/", "%2F")


def get_manifest(pkg):
    raw = fetch(registry_url(pkg))
    if not raw:
        return None, "registry unreachable"
    try:
        d = json.loads(raw.decode("utf-8", "ignore"))
    except Exception as e:
        return None, "registry json invalid"
    tags = d.get("dist-tags") or {}
    latest = tags.get("latest")
    versions = d.get("versions") or {}
    if not latest or latest not in versions:
        if not versions:
            return None, "no versions"
        # 取 semver 最大的
        best = None
        for k in versions:
            pv = parse_ver(k)
            if pv and (best is None or cmp_ver(pv, best[0]) > 0):
                best = (pv, k)
        latest = best[1] if best else list(versions)[-1]
    return {"name": pkg, "version": latest,
            "manifest": versions.get(latest) or {},
            "dist_tags": tags}, None


def get_file(pkg, ver, path):
    path = path.lstrip("./").lstrip("/")
    for tpl in CDN_TEMPLATES:
        url = tpl.format(pkg=pkg, ver=ver, path=path)
        raw = fetch(url, timeout=15)
        if raw:
            return raw.decode("utf-8", "ignore"), url
    return None, None


# ── 简易 YAML 检查（不依赖 pyyaml）──
def _parse_yaml(text):
    """用 pyyaml 解析；不可用时返回 (None, 原因)"""
    if _yaml is None:
        return None, "pyyaml not installed"
    try:
        return _yaml.safe_load(text), None
    except Exception as e:
        msg = str(e).replace("\n", " ")[:200]
        return None, msg


def yaml_basic_check(text):
    """返回 (ok, reason, info)

    info: {"parsed": True/False, "top_is_list": bool, "has_insert": bool,
           "entry_count": int, "entries": [...]}
    """
    if text is None:
        return False, "file not readable", None
    doc, err = _parse_yaml(text)
    if err:
        return False, err, None
    if doc is None:
        return False, "file is empty", None
    if not isinstance(doc, list):
        return False, "top level is %s, expected a list" % type(doc).__name__,                {"parsed": True, "top_is_list": False, "has_insert": False,
                "entry_count": 0, "entries": []}
    has_insert = any(isinstance(x, dict) and "insert" in x for x in doc)
    entries = yaml_entries(text)
    return True, "ok", {
        "parsed": True,
        "top_is_list": True,
        "has_insert": has_insert,
        "entry_count": len(entries),
        "entries": entries,
    }


def yaml_entries(text):
    """从 patch 中提取 insert 列表里的 entry（用 pyyaml，准确）"""
    if not text:
        return []
    doc, err = _parse_yaml(text)
    if err or not isinstance(doc, list):
        return []
    out = []
    for item in doc:
        if not isinstance(item, dict):
            continue
        ins = item.get("insert")
        if not isinstance(ins, list):
            continue
        for e in ins:
            if isinstance(e, dict):
                nm = e.get("name")
                out.append({
                    "id": e.get("id"),
                    "name": str(nm) if nm is not None else None,
                })
    return out


# ── 条款执行 ──
def run_checks(pkg, verbose=False):
    clauses = json.load(open(CLAUSES_PATH, encoding="utf-8"))["clauses"]
    meta, err = get_manifest(pkg)
    result = {
        "plugin": pkg,
        "baseline_dsh": BASELINE_DSH,
        "resolved": None,
        "results": [],
        "summary": {"pass": 0, "fail": 0, "skip": 0, "manual": 0},
    }
    if err:
        result["error"] = err
        result["conforming"] = False
        return result

    mf = meta["manifest"]
    ver = meta["version"]
    result["resolved"] = {"version": ver, "dist_tags": meta["dist_tags"]}

    # 取 patch 文件
    patch_rel = ((mf.get("dsh") or {}).get("bundle") or {}).get("patch")
    patch_text = None
    patch_url = None
    if patch_rel:
        patch_text, patch_url = get_file(pkg, ver, patch_rel)
    result["patch_file"] = {"path": patch_rel, "url": patch_url}

    def add(cid, status, evidence="", fix=""):
        c = next((x for x in clauses if x["id"] == cid), {})
        result["results"].append({
            "clause": cid,
            "title": c.get("title", ""),
            "severity": c.get("severity", ""),
            "status": status,
            "evidence": evidence,
            "fix": fix or c.get("fix", ""),
        })
        result["summary"][status] = result["summary"].get(status, 0) + 1

    # 5.1.1
    if patch_rel:
        add("5.1.1", "pass", "dsh.bundle.patch = %s" % patch_rel)
    else:
        add("5.1.1", "fail", "package.json 没有 dsh.bundle.patch")

    # 5.1.2
    if patch_rel and patch_text:
        add("5.1.2", "pass", "已从 %s 取到文件" % (patch_url or ""))
    elif patch_rel:
        add("5.1.2", "fail", "声明了 %s 但取不到该文件" % patch_rel)
    else:
        add("5.1.2", "skip", "无 patch 声明")

    # 5.1.3
    if patch_text:
        ok, reason, info = yaml_basic_check(patch_text)
        add("5.1.3", "pass" if ok else "fail", reason)
    else:
        add("5.1.3", "skip", "无 patch 文件")

    # 5.1.4
    if patch_text:
        ok, reason, info = yaml_basic_check(patch_text)
        if ok and info and info.get("top_is_list") and info.get("has_insert"):
            add("5.1.4", "pass", "顶层为数组且含 insert")
        elif ok and info:
            add("5.1.4", "fail",
                "top_is_list=%s has_insert=%s" % (info.get("top_is_list"), info.get("has_insert")))
        else:
            add("5.1.4", "fail", reason)
    else:
        add("5.1.4", "skip", "无 patch 文件")

    # 5.1.5
    if patch_text:
        entries = yaml_entries(patch_text)
        bad = [e for e in entries if not e.get("id") or not e.get("name")]
        if entries and not bad:
            add("5.1.5", "pass", "%d 个 entry 均含 id/name" % len(entries))
        elif not entries:
            add("5.1.5", "fail", "未能从 patch 中提取到 entry")
        else:
            add("5.1.5", "fail", "%d 个 entry 缺 id 或 name" % len(bad))
    else:
        add("5.1.5", "skip", "无 patch 文件")

    # 5.2.1
    eng = ((mf.get("engines") or {}).get("dsh"))
    if eng:
        add("5.2.1", "pass", "engines.dsh = %s" % eng)
    else:
        peers = mf.get("peerDependencies") or {}
        dsh_peers = {k: v for k, v in peers.items() if k.startswith("@deepseek-ai/")}
        if dsh_peers:
            add("5.2.1", "pass", "无 engines.dsh，按 peerDependencies 判定（%d 个 DSH 包）"
                % len(dsh_peers))
        else:
            add("5.2.1", "fail", "既无 engines.dsh 也无 DSH peerDependencies")

    # 5.2.2
    if eng:
        inc = range_includes(eng, BASELINE_DSH)
        if inc is True:
            add("5.2.2", "pass", "%s 包含 %s" % (eng, BASELINE_DSH))
        elif inc is False:
            add("5.2.2", "fail", "%s 不包含基准版本 %s" % (eng, BASELINE_DSH))
        else:
            add("5.2.2", "skip", "无法解析版本范围: %s" % eng)
    else:
        add("5.2.2", "skip", "无 engines.dsh")

    # 5.2.3
    main = mf.get("main")
    exports = mf.get("exports")
    if main or exports:
        add("5.2.3", "pass", "main=%s exports=%s" % (main, "有" if exports else "无"))
    else:
        add("5.2.3", "fail", "既无 main 也无 exports")

    # 5.3.1
    files = mf.get("files")
    if not files:
        add("5.3.1", "pass", "未声明 files（默认包含全部）")
    else:
        has_lib = any(f == "lib" or f.startswith("lib/") for f in files)
        has_patch = bool(patch_rel) and any(
            patch_rel.lstrip("./") == f or f.startswith(patch_rel.lstrip("./"))
            for f in files)
        if has_lib and has_patch:
            add("5.3.1", "pass", "files 含 lib 与 patch")
        else:
            add("5.3.1", "fail",
                "files 缺 %s" % (", ".join(x for x, ok in (("lib", has_lib), ("patch", has_patch)) if not ok)))

    # 5.3.2 只看会进运行时的依赖声明，不扫 scripts / bin 之类的普通字符串
    # devDependencies 不随包发布，装机时不会被安装，故不纳入判定
    dep_fields = ("dependencies", "optionalDependencies", "peerDependencies", "dsh")
    bad_hits = []
    for fld in dep_fields:
        sub = mf.get(fld)
        if not isinstance(sub, dict):
            continue
        for k, v in sub.items():
            if isinstance(v, str) and (v.startswith("file:") or v.startswith("/")):
                bad_hits.append("%s[%s] = %s" % (fld, k, v[:60]))
    if bad_hits:
        add("5.3.2", "fail", "依赖声明里有本地路径: %s" % "; ".join(bad_hits[:3]))
    else:
        add("5.3.2", "pass", "依赖声明未引用 file: 或绝对路径")

    # 6.2.1 红线
    caps = set()
    capsrc = mf.get("dsh", {})
    for k in ("capabilities", "permissions"):
        v = capsrc.get(k)
        if isinstance(v, list):
            caps |= set(v)
    caps |= set(mf.get("permissions") or [])
    if ("network" in caps) and ({"shell", "fs-write"} & caps):
        add("6.2.1", "fail", "红线组合: %s" % ", ".join(sorted(caps)))
    elif caps:
        add("6.2.1", "pass", "无红线组合（%s）" % ", ".join(sorted(caps)))
    else:
        add("6.2.1", "skip", "manifest 未声明 capabilities")

    # manual 条款只登记
    for c in clauses:
        if c.get("checkability") == "manual":
            result["results"].append({
                "clause": c["id"], "title": c.get("title", ""),
                "severity": c.get("severity", ""),
                "status": "manual", "evidence": "",
                "guidance": (c.get("guidance") or {}).get("zh-Hans", ""),
            })
            result["summary"]["manual"] += 1

    # test 条款登记（未执行）
    for c in clauses:
        if c.get("checkability") == "test":
            result["results"].append({
                "clause": c["id"], "title": c.get("title", ""),
                "severity": c.get("severity", ""),
                "status": "skip", "evidence": "需要沙箱测试（阶段 %s）" % c.get("stage", "?"),
            })
            result["summary"]["skip"] += 1

    crit_fail = any(r["status"] == "fail" and r["severity"] == "critical"
                    for r in result["results"])
    any_fail = any(r["status"] == "fail" for r in result["results"])
    result["conforming"] = (not any_fail)
    result["conforming_static"] = (not crit_fail)
    return result


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        print("用法: python3 checker.py <npm包名或 github:owner/repo> [--json]")
        sys.exit(1)
    pkg = args[0]
    r = run_checks(pkg)
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    # 人类可读
    icon = {"pass": "✅", "fail": "❌", "skip": "⏭️", "manual": "👁️"}
    print("═" * 66)
    print("  DSHIO/T 10 插件标准 · 静态检查")
    print("═" * 66)
    print("  插件: %s" % r["plugin"])
    if r.get("resolved"):
        print("  版本: %s" % r["resolved"]["version"])
    print("  基准 DSH: %s" % r["baseline_dsh"])
    if r.get("error"):
        print("  ❌ 无法解析: %s" % r["error"])
        return
    print()
    for x in r["results"]:
        print("  %s %-8s %s" % (icon.get(x["status"], "?"), x["clause"], x["title"]))
        if x["status"] in ("fail",) and x.get("evidence"):
            print("      证据: %s" % x["evidence"])
        if x["status"] == "fail" and x.get("fix"):
            print("      修法: %s" % str(x["fix"]).split("\n")[0])
        if x["status"] == "manual" and x.get("guidance"):
            print("      自查: %s" % x["guidance"][:100])
    s = r["summary"]
    print()
    print("  ── 汇总 ──")
    print("  通过 %d / 失败 %d / 跳过 %d / 待人工 %d"
          % (s.get("pass", 0), s.get("fail", 0), s.get("skip", 0), s.get("manual", 0)))
    print("  静态符合: %s" % ("是" if r.get("conforming_static") else "否"))
    print()


if __name__ == "__main__":
    main()
