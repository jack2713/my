#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV文件自动获取与合并工具 v2.1
- 自动从GitHub README获取TXT文件列表
- 自动去除加速地址前缀
- 合并同名文件（去掉数字后缀）
- 支持过滤指定关键词
- 对每个#genre#段进行排序
"""

import requests
from bs4 import BeautifulSoup
import re
import os
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict


class IPTVMerger:
    """IPTV文件合并器"""
    
    def __init__(self, readme_url, exclude_keywords=None):
        self.readme_url = readme_url
        self.exclude_keywords = exclude_keywords or []
        self.url_config = []
        
    def fetch_readme_content(self):
        """获取README.md内容"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                print(f"正在获取README (第 {attempt + 1}/{max_retries} 次)...")
                response = requests.get(self.readme_url, headers=headers, timeout=60)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"第 {attempt + 1} 次失败: {e}")
                    import time
                    time.sleep(3)
                else:
                    print(f"获取失败: {e}")
                    return None
    
    def extract_txt_list(self, content):
        """提取TXT文件列表"""
        txt_start = content.find("## TXT 文件列表")
        if txt_start == -1:
            print("未找到'TXT 文件列表'章节")
            return []
        
        next_section = content.find("\n##", txt_start + 1)
        if next_section != -1:
            txt_section = content[txt_start:next_section]
        else:
            txt_section = content[txt_start:]
        
        soup = BeautifulSoup(txt_section, 'html.parser')
        table = soup.find('table')
        
        if not table:
            return []
        
        results = []
        tbody = table.find('tbody')
        if not tbody:
            return []
        
        rows = tbody.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                file_name = cells[0].get_text(strip=True)
                link_tag = cells[1].find('a')
                if link_tag and link_tag.get('href'):
                    download_link = link_tag.get('href')
                    
                    # 【优化1】去掉加速地址前缀
                    download_link = download_link.replace('https://gh-proxy.org/', '')
                    
                    name_without_ext = re.sub(r'\.txt$', '', file_name)
                    results.append((name_without_ext, download_link))
        
        return results
    
    def normalize_name(self, name):
        """标准化名称（去掉数字后缀）"""
        return re.sub(r'\d+$', '', name)
    
    def fetch_url_content(self, url):
        """获取URL内容"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=30)
            response.encoding = response.apparent_encoding or 'utf-8'
            return response.text.strip()
        except Exception as e:
            print(f"获取失败 {url}: {e}")
            return ""
    
    def filter_content(self, content):
        """过滤内容"""
        if not self.exclude_keywords:
            return content
        
        lines = content.split('\n')
        filtered_lines = []
        excluded_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            should_exclude = False
            for keyword in self.exclude_keywords:
                if keyword.lower() in line.lower():
                    should_exclude = True
                    excluded_count += 1
                    break
            
            if not should_exclude:
                filtered_lines.append(line)
        
        if excluded_count > 0:
            print(f"  已过滤 {excluded_count} 行包含关键词的记录")
        
        return '\n'.join(filtered_lines)
    
    def process_item(self, item):
        """处理单个配置项"""
        name, url = item
        print(f"正在获取: {name}")
        
        content = self.fetch_url_content(url)
        if not content:
            return (None, "")
        
        filtered_content = self.filter_content(content)
        normalized_name = self.normalize_name(name)
        
        return (normalized_name, filtered_content)
    
    def sort_genre_content(self, lines):
        """【优化2】对频道列表进行排序"""
        parsed_lines = []
        for line in lines:
            if ',' in line:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    channel_name = parts[0].strip()
                    url = parts[1].strip()
                    parsed_lines.append((channel_name, url))
        
        import locale
        try:
            locale.setlocale(locale.LC_COLLATE, 'zh_CN.UTF-8')
            sorted_lines = sorted(parsed_lines, key=lambda x: locale.strxfrm(x[0]))
        except:
            sorted_lines = sorted(parsed_lines, key=lambda x: x[0])
        
        return [f"{name},{url}" for name, url in sorted_lines]
    
    def merge_and_save(self):
        """合并并保存结果"""
        print("=" * 80)
        print("步骤1: 获取README内容")
        print("=" * 80)
        content = self.fetch_readme_content()
        if not content:
            print("获取README失败!")
            return
        print("✓ 成功获取README内容\n")
        
        print("=" * 80)
        print("步骤2: 提取TXT文件列表")
        print("=" * 80)
        self.url_config = self.extract_txt_list(content)
        print(f"✓ 找到 {len(self.url_config)} 个TXT文件\n")
        
        if not self.url_config:
            print("未找到任何TXT文件!")
            return
        
        print("URL_CONFIG 配置列表:")
        print("-" * 80)
        for name, url in self.url_config[:5]:
            normalized = self.normalize_name(name)
            print(f"{name} -> {normalized}")
            print(f"  URL: {url}")
        if len(self.url_config) > 5:
            print(f"... 还有 {len(self.url_config) - 5} 个文件")
        print("-" * 80)
        print()
        
        print("=" * 80)
        print("步骤3: 多线程获取内容")
        print("=" * 80)
        
        merged_content = defaultdict(list)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.process_item, item): item for item in self.url_config}
            
            for future in futures:
                normalized_name, content = future.result()
                if normalized_name and content:
                    merged_content[normalized_name].append(content)
        
        print("\n" + "=" * 80)
        print("步骤4: 合并、排序并保存结果")
        print("=" * 80)
        
        os.makedirs("TMP", exist_ok=True)
        
        output_lines = []
        for name, contents in sorted(merged_content.items()):
            combined_content = '\n'.join(contents)
            unique_lines = list(dict.fromkeys(combined_content.split('\n')))
            
            # 【优化2】对频道列表进行排序
            sorted_lines = self.sort_genre_content(unique_lines)
            
            output_lines.append(f"{name},#genre#")
            output_lines.extend(sorted_lines)
            output_lines.append("")
            
            print(f"✓ {name}: 合并了 {len(contents)} 个文件，共 {len(sorted_lines)} 条记录（已排序）")
        
        with open("TMP/new.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        print("\n" + "=" * 80)
        print(f"✓ 完成！已保存到 TMP/new.txt")
        print(f"✓ 共生成 {len(merged_content)} 个分组")
        print(f"✓ 已去除加速地址前缀: https://gh-proxy.org/")
        print(f"✓ 已对每个#genre#段进行排序")
        print("=" * 80)
        
        if self.exclude_keywords:
            print(f"\n排除关键词: {', '.join(self.exclude_keywords)}")


def main():
    """主函数"""
    readme_url = "https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/README.md"
    exclude_keywords = ['SD','sd']
    
    print("=" * 80)
    print("IPTV文件自动获取与合并工具 v2.1")
    print("=" * 80)
    print(f"README地址: {readme_url}")
    print(f"排除关键词: {exclude_keywords}")
    print(f"功能: 自动去除加速地址 | 智能合并 | 关键词过滤 | 频道排序")
    print("=" * 80)
    print()
    
    merger = IPTVMerger(readme_url, exclude_keywords)
    merger.merge_and_save()


if __name__ == "__main__":
    main()
