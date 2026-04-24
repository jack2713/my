#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV文件自动获取与合并工具
- 自动从GitHub README获取TXT文件列表
- 合并同名文件（去掉数字后缀）
- 支持过滤指定关键词
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
        """
        初始化
        
        Args:
            readme_url: README.md的URL
            exclude_keywords: 要排除的关键词列表，如 ['SD', 'HD']
        """
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
        """
        提取TXT文件列表
        
        Args:
            content: README内容
            
        Returns:
            list: [(name, url), ...]
        """
        # 查找TXT文件列表章节
        txt_start = content.find("## TXT 文件列表")
        if txt_start == -1:
            print("未找到'TXT 文件列表'章节")
            return []
        
        # 查找下一个章节
        next_section = content.find("\n##", txt_start + 1)
        if next_section != -1:
            txt_section = content[txt_start:next_section]
        else:
            txt_section = content[txt_start:]
        
        # 解析表格
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
                    # 去掉.txt扩展名
                    name_without_ext = re.sub(r'\.txt$', '', file_name)
                    results.append((name_without_ext, download_link))
        
        return results
    
    def normalize_name(self, name):
        """
        标准化名称（去掉数字后缀）
        
        Args:
            name: 原始名称，如"上海电信1"
            
        Returns:
            str: 标准化后的名称，如"上海电信"
        """
        # 去掉末尾的数字
        return re.sub(r'\d+$', '', name)
    
    def fetch_url_content(self, url):
        """
        获取URL内容
        
        Args:
            url: URL地址
            
        Returns:
            str: 内容文本
        """
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=30)
            response.encoding = response.apparent_encoding or 'utf-8'
            return response.text.strip()
        except Exception as e:
            print(f"获取失败 {url}: {e}")
            return ""
    
    def filter_content(self, content):
        """
        过滤内容
        
        Args:
            content: 原始内容
            
        Returns:
            str: 过滤后的内容
        """
        if not self.exclude_keywords:
            return content
        
        lines = content.split('\n')
        filtered_lines = []
        excluded_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否包含排除关键词
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
        """
        处理单个配置项
        
        Args:
            item: (name, url)
            
        Returns:
            tuple: (normalized_name, content)
        """
        name, url = item
        print(f"正在获取: {name}")
        
        content = self.fetch_url_content(url)
        if not content:
            return (None, "")
        
        # 过滤内容
        filtered_content = self.filter_content(content)
        
        # 标准化名称
        normalized_name = self.normalize_name(name)
        
        return (normalized_name, filtered_content)
    
    def merge_and_save(self):
        """合并并保存结果"""
        # 1. 获取README内容
        print("=" * 80)
        print("步骤1: 获取README内容")
        print("=" * 80)
        content = self.fetch_readme_content()
        if not content:
            print("获取README失败!")
            return
        
        print("✓ 成功获取README内容\n")
        
        # 2. 提取TXT文件列表
        print("=" * 80)
        print("步骤2: 提取TXT文件列表")
        print("=" * 80)
        self.url_config = self.extract_txt_list(content)
        print(f"✓ 找到 {len(self.url_config)} 个TXT文件\n")
        
        if not self.url_config:
            print("未找到任何TXT文件!")
            return
        
        # 显示配置列表
        print("URL_CONFIG 配置列表:")
        print("-" * 80)
        for name, url in self.url_config:
            normalized = self.normalize_name(name)
            print(f"{name} -> {normalized}")
        print("-" * 80)
        print()
        
        # 3. 多线程获取内容
        print("=" * 80)
        print("步骤3: 多线程获取内容")
        print("=" * 80)
        
        # 使用字典存储合并后的内容
        merged_content = defaultdict(list)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.process_item, item): item for item in self.url_config}
            
            for future in futures:
                normalized_name, content = future.result()
                if normalized_name and content:
                    merged_content[normalized_name].append(content)
        
        # 4. 合并同名内容并写入文件
        print("\n" + "=" * 80)
        print("步骤4: 合并并保存结果")
        print("=" * 80)
        
        os.makedirs("TMP", exist_ok=True)
        
        output_lines = []
        for name, contents in sorted(merged_content.items()):
            # 合并所有同名内容
            combined_content = '\n'.join(contents)
            # 去重
            unique_lines = list(dict.fromkeys(combined_content.split('\n')))
            
            # 添加分组标题
            output_lines.append(f"{name},#genre#")
            output_lines.extend(unique_lines)
            output_lines.append("")  # 空行分隔
            
            print(f"✓ {name}: 合并了 {len(contents)} 个文件，共 {len(unique_lines)} 条记录")
        
        # 写入文件
        with open("TMP/new.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        print("\n" + "=" * 80)
        print(f"✓ 完成！已保存到 TMP/new.txt")
        print(f"✓ 共生成 {len(merged_content)} 个分组")
        print("=" * 80)
        
        # 显示过滤关键词
        if self.exclude_keywords:
            print(f"\n排除关键词: {', '.join(self.exclude_keywords)}")


def main():
    """主函数"""
    # 配置
    readme_url = "https://raw.githubusercontent.com/jack2713/4K-IPTV-M3U/refs/heads/main/README.md"
    
    # 设置要排除的关键词（可根据需要修改）
    # 例如: exclude_keywords = ['SD', '高清', '测试']
    exclude_keywords = ['SD','sd']  # 排除包含SD的行
    
    print("=" * 80)
    print("IPTV文件自动获取与合并工具")
    print("=" * 80)
    print(f"README地址: {readme_url}")
    print(f"排除关键词: {exclude_keywords}")
    print("=" * 80)
    print()
    
    # 创建合并器并执行
    merger = IPTVMerger(readme_url, exclude_keywords)
    merger.merge_and_save()


if __name__ == "__main__":
    main()
