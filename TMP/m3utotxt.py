import requests  
import os  
import time  
from collections import defaultdict  
    
# 合并后的函数，接受URL列表，下载M3U文件，提取并处理频道信息  
def fetch_m3u_channels_and_save(urls, output_file_path):  
    all_channels = []  # 用于存储所有提取的频道信息  
    seen_urls = set()  # 用于跟踪已经遇到过的流媒体URL（全局去重，如果需要）  
  
    for url in urls:  
        try:  
            # 下载M3U文件（这里为了简化，不直接保存到磁盘，而是读取内容到内存中）  
            response = requests.get(url, timeout=15)  
            response.raise_for_status()  # 确保请求成功  
  
            m3u_content = response.text  
  
            # 提取当前M3U文件中的频道信息  
            channels = []  
            group_title = ""  
            for line in m3u_content.splitlines():  
                line = line.strip()  
                if line.startswith("#EXTINF:"):  
                    # 从 #EXTINF: 行提取频道名称和分组信息  
                    channel_info = line.split(",")  
                    channel_name = channel_info[1].split(" ")[0] if len(channel_info) > 1 else ""  
                    # 提取分组标题，注意这里可能需要根据实际的M3U文件内容调整解析逻辑  
                    for item in channel_info:  
                        if "group-title=" in item:  
                            group_title = item.split("group-title=")[-1].strip('"')  
                            break  
                elif line.startswith(("http://", "https://")):  
                    # 处理流媒体 URL 行  
                    streaming_url = line  
                    # 如果需要全局去重，则检查URL是否已经在seen_urls中  
                    if not seen_urls or streaming_url not in seen_urls:  
                        seen_urls.add(streaming_url)  # 添加到已见URL集合中  
                        channels.append({"channel_name": channel_name, "group_title": group_title, "streaming_url": streaming_url})  
  
            # 将当前M3U文件中的频道信息添加到全局列表中  
            all_channels.extend(channels)  
  
        except requests.exceptions.Timeout:  
            print(f"Request to {url} timed out.")  
        except requests.exceptions.RequestException as e:  
            print(f"An error occurred while requesting {url}: {e}")  
  
    # 按照分组对频道进行分组，并在每个分组内部按任意顺序（或按其他逻辑排序）  
    grouped_channels = defaultdict(list)  
    for channel in all_channels:  
        grouped_channels[channel["group_title"]].append(channel)  
  
    # 输出到文件  
    with open(output_file_path, "w", encoding="utf-8") as output_file:  
        prev_group_title = None  
        for group_title, channels_in_group in grouped_channels.items():  
            if group_title != prev_group_title:  
                if prev_group_title:  
                    output_file.write("\n")  # 在每个分组后添加一个空行  
                if group_title:  
                    output_file.write(f"{group_title},#genre#\n")  
                prev_group_title = group_title  
            for channel in channels_in_group:  
                output_file.write(f"{channel['channel_name']},{channel['streaming_url']}\n")  
  
    print(f"提取完成,结果已保存到 {output_file_path}")  
  
if __name__ == "__main__":  
    # 定义多个M3U文件的URL  
    urls = [  
        'https://github.com/YanG-1989/m3u/blob/main/Gather.m3u',  
        'https://mirror.ghproxy.com/raw.githubusercontent.com/suxuang/myIPTV/main/ipv6.m3u',  
    ]  
  
    # 指定输出文件的名称  
    output_file_path = "/TMP/TMP.txt"  
  
    # 调用函数从M3U URLs获取内容，提取频道信息，并保存到TXT文件  
    fetch_m3u_channels_and_save(urls, output_file_path)
