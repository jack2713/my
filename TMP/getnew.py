#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV文件自动获取与合并工具 v3.0
- 自动遍历 GitHub 仓库指定目录下的所有 TXT 文件
- 自动去除加速地址前缀
- 合并同名文件（去掉数字后缀）
- 支持过滤指定关键词
- 对每个 #genre# 段进行排序
"""

import os
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import requests

GITHUB_API = "https://api.github.com"
RAW_BASE = "https://raw.githubusercontent.com"


class IPTVMerger:
    """IPTV文件合并器"""

    def __init__(self, repo_owner, repo_name, txt_dir="txt", branch="main",
                 exclude_keywords=None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.txt_dir = txt_dir.strip("/")
        self.branch = branch
        self.exclude_keywords = exclude_keywords or []
        self.url_config = []

    # ---------- 1. 列出目录下的 txt 文件 ----------
    def list_txt_files(self):
        """通过 GitHub Contents API 列出 txt 目录下所有 .txt 文件"""
        api_url = f"{GITHUB_API}/repos/{self.repo_owner}/{self.repo_name}/contents/{self.txt_dir}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/vnd.github+json",
        }
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        items = None
        for attempt in range(3):
            try:
                print(f"正在获取目录列表 (第 {attempt + 1}/3 次)...")
                resp = requests.get(api_url, headers=headers,
                                    params={"ref": self.branch}, timeout=60)
                resp.raise_for_status()
                items = resp.json()
                break
            except Exception as e:
                print(f"第 {attempt + 1} 次失败: {e}")
                if attempt == 2:
                    return []
                time.sleep(3)

        if not isinstance(items, list):
            print(f"接口返回异常: {items}")
            return []

        results = []
        for item in items:
            if item.get("type") != "file":
                continue
            file_name = item.get("name", "")
            if not file_name.lower().endswith(".txt"):
                continue
            download_url = item.get("download_url") or (
                f"{RAW_BASE}/{self.repo_owner}/{self.repo_name}/{self.branch}/"
                f"{self.txt_dir}/{file_name}"
            )
            # 去掉可能的加速地址前缀
            download_url = re.sub(r"^https?://[^/]*gh-proxy[^/]*/", "", download_url)
            name_without_ext = re.sub(r"\.txt$", "", file_name, flags=re.I)
            results.append((name_without_ext, download_url))
        return results

    # ---------- 2. 下载与解析 ----------
    @staticmethod
    def decode_content(resp):
        """按 utf-8 -> gbk -> gb18030 依次尝试解码"""
        raw = resp.content
        for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
            try:
                return raw.decode(enc).strip()
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="ignore").strip()

    def fetch_url_content(self, url):
        """获取单个 TXT 文件内容"""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return self.decode_content(resp)
        except Exception as e:
            print(f"获取失败 {url}: {e}")
            return ""

    def normalize_name(self, name):
        """标准化名称（去掉数字后缀）"""
        normalized = re.sub(r"\d+$", "", name).strip()
        return normalized or name

    def filter_content(self, content):
        """过滤包含排除关键词的行"""
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
        """处理单个文件，返回 (标准化名称, 频道行列表)"""
        name, url = item
        print(f"正在获取: {name}")
        content = self.fetch_url_content(url)
        if not content:
            return (None, [])
        content = self.filter_content(content)
        # 去掉文件自带的 #genre# 分组头，避免与合并后的分组头重复
        lines = [
            ln.strip() for ln in content.splitlines()
            if ln.strip() and "#genre#" not in ln
        ]
        return (self.normalize_name(name), lines)

    # ---------- 3. 排序 ----------
    @staticmethod
    def sort_channel_lines(lines):
        """只保留 name,url 形式，按频道名排序"""
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

    # ---------- 4. 主流程 ----------
    def merge_and_save(self, output_file="TMP/new.txt"):
        print("=" * 80)
        print("步骤1: 获取 TXT 文件列表")
        print("=" * 80)
        self.url_config = self.list_txt_files()
        print(f"✓ 找到 {len(self.url_config)} 个 TXT 文件\n")
        if not self.url_config:
            print("未找到任何 TXT 文件，请检查仓库路径/分支/网络。")
            return

        print("URL_CONFIG 配置列表:")
        print("-" * 80)
        for name, url in self.url_config[:5]:
            print(f"{name} -> {self.normalize_name(name)}")
            print(f"   URL: {url}")
        if len(self.url_config) > 5:
            print(f"... 还有 {len(self.url_config) - 5} 个文件")
        print("-" * 80)

        print("=" * 80)
        print("步骤2: 多线程获取内容")
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
            unique_lines = list(dict.fromkeys(merged[name]))   # 去重保序
            sorted_lines = self.sort_channel_lines(unique_lines)
            if not sorted_lines:
                continue
            output_lines.append(f"{name},#genre#")
            output_lines.extend(sorted_lines)
            output_lines.append("")
            group_count += 1
            print(f"✓ {name}: 合并了 {len(merged[name])} 行，去重后 {len(sorted_lines)} 条（已排序）")

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
