import requests
import os
import re
from collections import defaultdict, OrderedDict
import time

# 文件 URL 列表
urls = [
    'https://bc.188766.xyz/?ip=',
    #'https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt',
    'https://iptv.catvod.com/tv.m3u',
    'https://live.catvod.com/tv.m3u',
    'https://sub.ottiptv.cc/iptv.m3u',
    'https://sub.ottiptv.cc/douyuyqk.m3u',
    'https://sub.ottiptv.cc/huyayqk.m3u',
    'https://sub.ottiptv.cc/yylunbo.m3u',
    'https://live.hacks.tools/iptv/categories/movies.m3u',
]

def get_session():
    """创建配置好的请求会话 - 模拟真实浏览器"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    })
    return session

def extract_channel_name(extinf_line):
    """从EXTINF行提取频道名称"""
    # 首先尝试获取tvg-name
    tvg_name_match = re.search(r'tvg-name="([^"]*)"', extinf_line)
    tvg_name = tvg_name_match.group(1) if tvg_name_match else None
    
    # 如果tvg-name存在且不为null/空，则使用它
    if tvg_name and tvg_name.lower() not in ["null", "none", ""]:
        return tvg_name
    
    # 否则尝试获取最后一个逗号后的内容
    parts = extinf_line.split(',')
    if len(parts) > 1:
        last_part = parts[-1].strip()
        if last_part:
            return last_part
    
    # 如果都失败，返回"未命名频道"
    return "未命名频道"

def fetch_url_content(url, session, retries=3):
    """获取URL内容，支持重试和特殊处理"""
    for attempt in range(retries + 1):
        try:
            print(f"正在获取 {url} (尝试 {attempt + 1}/{retries + 1})")
            
            # 对于特定URL使用更长的超时时间
            timeout = 30 if 'bc.188766.xyz' in url else 15
            
            response = session.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()  # 如果状态码不是200，抛出异常
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            
            # 自动检测编码
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                response.encoding = response.apparent_encoding or 'utf-8'
            
            print(f"成功获取 {url}, 内容长度: {len(response.text)} 字符")
            return response.text
            
        except requests.exceptions.Timeout:
            print(f"请求超时: {url}")
        except requests.exceptions.ConnectionError as e:
            print(f"连接错误: {url} - {e}")
        except requests.exceptions.HTTPError as e:
            print(f"HTTP错误 {e.response.status_code}: {url}")
            # 输出更多调试信息
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应头: {dict(e.response.headers)}")
        except Exception as e:
            print(f"获取 {url} 时出错: {str(e)}")
        
        # 如果不是最后一次尝试，等待后重试
        if attempt < retries:
            wait_time = 3 * (attempt + 1)  # 递增等待时间
            print(f"等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    
    return None

def parse_m3u_content(content, url, all_channels_dict, group_order):
    """解析M3U内容"""
    if not content:
        return
    
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("#EXTINF:"):
            group_title = ""
            tvg_logo = ""
            streaming_url = ""
            
            # 提取属性
            try:
                attr_matches = re.findall(r'(\S+)=(".*?"|\S+)', line)
                attrs = {k: v.strip('"') for k, v in attr_matches}
                
                group_title = attrs.get('group-title', "")
                tvg_logo = attrs.get('tvg-logo', "")
            except Exception as e:
                print(f"解析EXTINF属性时出错: {e}")
                i += 1
                continue
            
            # 获取URL
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line and not next_line.startswith('#'):
                    streaming_url = next_line
                    i += 1
            
            if streaming_url:
                channel_name = extract_channel_name(line)
                
                # 处理分组
                if not group_title or group_title.lower() in ["null", "none", ""]:
                    group_title = "其他"
                
                # 如果URL包含联通标识，则在分组名称后添加"-联通"
                if "http://sc.rrs.169ol.com" in streaming_url:
                    group_title = f"{group_title}-联通"
                
                # 过滤内容
                filter_keywords = ["成人", "4K频道", "直播中国", "列表更新","公告","熊猫"]
                if not any(keyword in group_title for keyword in filter_keywords):
                    # 记录分组出现的顺序
                    if group_title not in all_channels_dict:
                        all_channels_dict[group_title] = []
                        group_order.append(group_title)
                    
                    all_channels_dict[group_title].append({
                        "channel_name": channel_name,
                        "tvg_logo": tvg_logo,
                        "streaming_url": streaming_url,
                        "line_index": i,
                        "source_url": url  # 记录来源URL
                    })
        i += 1

# 使用OrderedDict保持分组顺序
all_channels_dict = OrderedDict()
group_order = []
session = get_session()

print("开始获取IPTV源文件...")

for url in urls:
    print(f"\n处理URL: {url}")
    m3u_content = fetch_url_content(url, session)
    
    if m3u_content is None:
        print(f"跳过无法获取的URL: {url}")
        continue
    
    # 解析内容
    parse_m3u_content(m3u_content, url, all_channels_dict, group_order)

# 输出到文件
output_file_path = "TMP/TMP1.txt"
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

print(f"\n开始写入文件: {output_file_path}")

with open(output_file_path, "w", encoding="utf-8") as output_file:
    # 按照分组在源文件中出现的顺序输出
    for group_title in group_order:
        if group_title in all_channels_dict:
            channels = all_channels_dict[group_title]
            if channels:
                output_file.write(f"{group_title},#genre#\n")
                # 按照频道在源文件中的顺序输出
                for channel in sorted(channels, key=lambda x: (x['source_url'], x['line_index'])):
                    output_file.write(f"{channel['channel_name']},{channel['streaming_url']}\n")
                output_file.write("\n")

print(f"提取完成! 共处理 {len(group_order)} 个分组")
print(f"结果已保存到 {output_file_path}")
