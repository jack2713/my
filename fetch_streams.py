import requests
import pandas as pd
import re
import os

# 多个网站 URL 列表
urls = [
    "https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/merged_output.m3u",
    "https://raw.githubusercontent.com/suxuang/myIPTV/main/ipv6.m3u",
]

# 区分IPv4和IPv6的正则表达式
ipv4_pattern = re.compile(r'^http://(\d{1,3}\.){3}\d{1,3}')
ipv6_pattern = re.compile(r'^http://\[([a-fA-F0-9:]+)\]')

# 提示信息和容错处理
def fetch_streams_from_url(url):
    print(f"正在爬取网站源: {url}")
    try:
        response = requests.get(url, timeout=10)  # 增加超时处理
        response.encoding = 'utf-8'  # 确保使用utf-8编码
        if response.status_code == 200:
            content = response.text
            print(f"成功获取源自: {url}")
            return content
        else:
            print(f"从 {url} 获取数据失败，状态码: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"请求 {url} 时发生错误: {e}")
        return None

# 获取所有源，并处理错误
def fetch_all_streams():
    all_streams = []
    for url in urls:
        content = fetch_streams_from_url(url)
        if content:
            all_streams.append(content)
        else:
            print(f"跳过来源: {url}")
    return "\n".join(all_streams)

# 处理M3U文件的内容
def parse_m3u(content):
    lines = content.splitlines()
    streams = []
    current_program = None

    for line in lines:
        if line.startswith("#EXTINF"):
            # 提取节目名称（假设tvg-name="节目名"）
            program_match = re.search(r'tvg-name="([^"]+)"', line)
            if program_match:
                current_program = program_match.group(1).strip()
        elif line.startswith("http"):  # 流地址
            stream_url = line.strip()
            if current_program:
                streams.append({"program_name": current_program, "stream_url": stream_url})

    return streams

# 处理普通TXT格式的内容
def parse_txt(content):
    lines = content.splitlines()
    streams = []

    for line in lines:
        if (match := re.match(r"(.+?),\s*(http.+)", line)) or (match := re.match(r"(.+?),\s*(p3p.+)", line)) or (match := re.match(r"(.+?),\s*(P3p.+)", line)):  
            # 注意：这里使用了Python 3.8+的“海象运算符”(:=)，它允许在表达式内部进行赋值  
            program_name = match.group(1).strip()  
            stream_url = match.group(2).strip()  
            streams.append({"program_name": program_name, "stream_url": stream_url})  
  
    return streams

def organize_streams(content):
    # 检查是否是 M3U 格式并解析
    if content.startswith("#EXTM3U"):
        streams = parse_m3u(content)
    else:
        # 非 M3U 格式处理
        streams = parse_txt(content)

    # 使用 pandas 整理相同节目的源，并去除重复链接
    df = pd.DataFrame(streams)
    df = df.drop_duplicates(subset=['program_name', 'stream_url'])  # 删除重复的节目和链接
    grouped = df.groupby('program_name')['stream_url'].apply(list).reset_index()

    return grouped

def save_to_txt(grouped_streams, filename="final_streams.txt"):
    filepath = os.path.join(os.getcwd(), filename)  # 使用绝对路径
    print(f"保存文件的路径是: {filepath}")  # 输出文件保存路径
    ipv4_lines = []
    ipv6_lines = []
    iptv_lines = []

    for _, row in grouped_streams.iterrows():
        program_name = row['program_name']
        stream_urls = row['stream_url']

        for url in stream_urls:
            if ipv4_pattern.match(url):
                ipv4_lines.append(f"{program_name},{url}")
            elif ipv6_pattern.match(url):
                ipv6_lines.append(f"{program_name},{url}")
            else:
                iptv_lines.append(f"{program_name},{url}")

    with open(filepath, 'w', encoding='utf-8') as output_file:
        output_file.write("# IPv4 Streams\n")
        output_file.write("\n".join(ipv4_lines))
        output_file.write("\n\n# IPv6 Streams\n")
        output_file.write("\n".join(ipv6_lines))
        output_file.write("\n\n# iptv Streams\n")
        output_file.write("\n".join(iptv_lines))

    print(f"所有源已保存到 {filepath}")

if __name__ == "__main__":
    print("开始抓取所有源...")
    all_content = fetch_all_streams()
    if all_content:
        print("开始整理源...")
        organized_streams = organize_streams(all_content)
        save_to_txt(organized_streams)
    else:
        print("未能抓取到任何源。")
