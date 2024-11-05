import requests  
import os  
import re  
import time  
from collections import defaultdict  
  
# 合并后的函数，接受URL列表，下载M3U文件，提取并处理频道信息  
def fetch_m3u_channels_and_save(urls, output_file_path):  
    all_channels = defaultdict(list)  # 用于存储所有提取的频道信息，按分组组织  
  
    for url in urls:  
        try:  
            # 下载M3U文件（这里为了简化，不直接保存到磁盘，而是读取内容到内存中）  
            response = requests.get(url, timeout=15)  
            response.raise_for_status()  # 确保请求成功  
  
            m3u_content = response.text  
  
            # 提取当前M3U文件中的频道信息  
            lines = m3u_content.splitlines()  
            current_group = "未分组"  
            current_name = ""  
  
            for i, line in enumerate(lines):  
                line = line.strip()  
                if line.startswith("#EXTINF:-1"):  
                    # 使用正则表达式提取group-title和tvg-name  
                    group_match = re.search(r'group-title="([^"]*)"', line)  
                    if group_match:  
                        current_group = group_match.group(1)  
  
                    name_match = re.search(r'tvg-name="([^"]*)"', line)  
                    if name_match:  
                        current_name = name_match.group(1)  
                    else:  
                        # 如果没有找到tvg-name，则尝试从#EXTINF行获取频道名（可能是最后一个逗号后的内容）  
                        current_name = line.split(',')[-1].split()[0] if ',' in line else ""  
  
                    # 获取URL（假设URL在下一行）  
                    if i + 1 < len(lines):  
                        streaming_url = lines[i + 1].strip()  
                        if streaming_url.startswith(("http://", "https://")):  
                            all_channels[current_group].append((current_name, streaming_url))  
  
        except requests.exceptions.Timeout:  
            print(f"Request to {url} timed out.")  
        except requests.exceptions.RequestException as e:  
            print(f"An error occurred while requesting {url}: {e}")  
  
    # 输出到文件  
    with open(output_file_path, "w", encoding="utf-8") as output_file:  
        prev_group_title = None  
        for group_title, channels_in_group in all_channels.items():  
            if group_title != prev_group_title:  
                if prev_group_title:  
                    output_file.write("\n")  # 在每个分组后添加一个空行  
                if group_title:  
                    output_file.write(f"{group_title},#genre#\n")  
                prev_group_title = group_title  
            for name, url in channels_in_group:  
                output_file.write(f"{name},{url}\n")  
  
    print(f"提取完成,结果已保存到 {output_file_path}")  
  
if __name__ == "__main__":  
    # 定义多个M3U文件的URL  
    urls = [         
        'https://example.com/path/to/your/m3u/file1.m3u',  
        'https://example.com/path/to/your/m3u/file2.m3u',  
    ]  
  
    # 确保输出目录存在  
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)  
  
    # 指定输出文件的名称  
    output_file_path = "TMP/TMP.txt"  
  
    # 调用函数从M3U URLs获取内容，提取频道信息，并保存到TXT文件  
    fetch_m3u_channels_and_save(urls, output_file_path)
