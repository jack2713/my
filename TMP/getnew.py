#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV文件自动获取与合并工具 v3.2
- 只下载 txt 目录下的文件，不下整个仓库
- 列目录：jsDelivr API（免认证、无限流）→ 失败降级 GitHub 网页解析
- 下载：jsDelivr CDN → raw.githubusercontent.com
- 合并同名文件（去掉数字后缀）、关键词过滤、分组排序
"""

import json
import os
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import requests


class IPTVMerger:
    def __init__(self, repo_owner, repo_name, txt_dir="txt", branch="main",
                 exclude_keywords=None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.txt_dir = txt_dir.strip("/")
        self.branch = branch
        self.exclude_keywords = exclude_keywords or []
        self.url_config = []

    # ---------- 1. 列文件 ----------
    def _list_jsdelivr(self):
        url = (f"https://data.jsdelivr.com/v1/package/gh/"
               f"{self.repo_owner}/{self.repo_name}@{self.branch}/flat")
        headers = {"User-Agent": "Mozilla/5.0"}
        for attempt in range(2):
            try:
                print(f"正在获取文件列表（jsDelivr，第 {attempt + 1}/2 次）...")
                resp = requests.get(url, headers=headers, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                prefix = f"/{self.txt_dir}/"
                results = []
                for item in data.get("files", []):
                    path = item.get("name", "")
                    if not path.startswith(prefix):
                        continue
                    rel = path[len(prefix):]
                    if "/" in rel or not rel.lower().endswith(".txt"):
                        continue
                    name = re.sub(r"\.txt$", "", rel, flags=re.I)
                    results.append((name, path.lstrip("/")))
                return results
            except Exception as e:
                print(f"  jsDelivr 失败: {e}")
                time.sleep(2)
        return []

    def _list_html(self):
        url = (f"https://github.com/{self.repo_owner}/{self.repo_name}"
               f"/tree/{self.branch}/{self.txt_dir}")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                 "AppleWebKit/537.36 (KHTML, like Gecko) "
                                 "Chrome/120.0 Safari/537.36"}
        try:
            print("正在获取文件列表（GitHub 网页解析）...")
            resp = requests.get(url, headers=headers, timeout=60)
            resp.raise_for_status()
            m = re.search(
                r'<script type="application/json" '
                r'data-target="react-app\.embeddedData">(.*?)</script>',
                resp.text, re.S)
            if not m:
                print("  未找到 embeddedData，网页结构可能变了")
                return []
            data = json.loads(m.group(1))
            items = data.get("payload", {}).get("tree", {}).get("items", [])
            results = []
            for item in items:
                if item.get("contentType") != "file":
                    continue
                name = item.get("name", "")
                if not name.lower().endswith(".txt"):
                    continue
                path = item.get("path") or f"{self.txt_dir}/{name}"
                name_without_ext = re.sub(r"\.txt$", "", name, flags=re.I)
                results.append((name_without_ext, path))
            return results
        except Exception as e:
            print(f"  网页解析失败: {e}")
            return []

    def list_txt_files(self):
        files = self._list_jsdelivr()
        if files:
            return files
        print("jsDelivr 无结果，降级到 GitHub 网页解析")
        return self._list_html()

    # ---------- 2. 下载 ----------
    def _build_urls(self, path):
        return [
            f"https://cdn.jsdelivr.net/gh/{self.repo_owner}/{self.repo_name}@{self.branch}/{path}",
            f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{self.branch}/{path}",
        ]

    @staticmethod
    def decode_bytes(raw):
        for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
            try:
                return raw.decode(enc).strip()
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="ignore").strip()

    def fetch_url_content(self, path):
        for url in self._build_urls(path):
            try:
                resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
                resp.raise_for_status()
                return self.decode_bytes(resp.content)
            except Exception as e:
                print(f"  下载失败 {url}: {e}")
        return ""

    # ---------- 3. 清洗 ----------
    def normalize_name(self, name):
        normalized = re.sub(r"\d+$", "", name).strip()
        return normalized or name

    def filter_content(self, content):
        if not self.exclude_keywords:
            return content
        kept, excluded = [], 0
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            if any(k.lower() in line.lower() for k in self.exclude_keywords):
                excluded += 1
                continue
            kept.append(line)
        if excluded:
            print(f" 已过滤 {excluded} 行包含关键词的记录")
        return "\n".join(kept)

    def process_item(self, item):
        name, path = item
        print(f"正在获取: {name}")
        content = self.fetch_url_content(path)
        if not content:
            return (None, [])
        content = self.filter_content(content)
        lines = [
            ln.strip() for ln in content.splitlines()
            if ln.strip() and "#genre#" not in ln
        ]
        return (self.normalize_name(name), lines)

    # ---------- 4. 排序 ----------
    @staticmethod
    def sort_channel_lines(lines):
        parsed = []
        for line in lines:
            if "," not in line:
                continue
            name, url = line.split(",", 1)
            name, url = name.strip(), url.strip()
            if not name or "://" not in url:
                continue
            parsed.append((name, url))
        try:
            import locale
            locale.setlocale(locale.LC_COLLATE, "zh_CN.UTF-8")
            parsed.sort(key=lambda x: locale.strxfrm(x[0]))
        except Exception:
            parsed.sort(key=lambda x: x[0])
        return [f"{n},{u}" for n, u in parsed]

    # ---------- 5. 主流程 ----------
    def merge_and_save(self, output_file="TMP/new.txt"):
        print("=" * 80)
        print("步骤1: 获取 TXT 文件列表")
        print("=" * 80)
        self.url_config = self.list_txt_files()
        print(f"✓ 找到 {len(self.url_config)} 个 TXT 文件\n")
        if not self.url_config:
            print("未找到任何 TXT 文件，请检查仓库路径/分支/网络。")
            return

        for name, path in self.url_config[:5]:
            print(f"  {name} -> {path}")
        if len(self.url_config) > 5:
            print(f"  ... 还有 {len(self.url_config) - 5} 个文件")

        print("=" * 80)
        print("步骤2: 多线程下载内容")
        print("=" * 80)
        merged = defaultdict(list)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.process_item, item) for item in self.url_config]
            for future in futures:
                name, lines = future.result()
                if name and lines:
                    merged[name].extend(lines)

        print("=" * 80)
        print("步骤3: 合并、排序并保存结果")
        print("=" * 80)
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        output_lines = []
        group_count = 0
        for name in sorted(merged):
            unique_lines = list(dict.fromkeys(merged[name]))
            sorted_lines = self.sort_channel_lines(unique_lines)
            if not sorted_lines:
                continue
            output_lines.append(f"{name},#genre#")
            output_lines.extend(sorted_lines)
            output_lines.append("")
            group_count += 1
            print(f"✓ {name}: 合并 {len(merged[name])} 行，去重后 {len(sorted_lines)} 条（已排序）")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines).rstrip() + "\n")

        print("=" * 80)
        print(f"✓ 完成！已保存到 {output_file}")
        print(f"✓ 共生成 {group_count} 个分组")
        print("=" * 80)
        if self.exclude_keywords:
            print(f"\n排除关键词: {', '.join(self.exclude_keywords)}")


def main():
    merger = IPTVMerger(
        repo_owner="Wang963963",
        repo_name="IPTV-4K-M3U",
        txt_dir="txt",
        branch="main",
        exclude_keywords=["SD", "sd"],
    )
    merger.merge_and_save(output_file="TMP/new.txt")


if __name__ == "__main__":
    main()
