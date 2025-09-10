import requests
import os
import fnmatch
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retry(retries=3, backoff_factor=0.3):
    """
    创建带有重试机制的会话
    
    Args:
        retries: 重试次数
        backoff_factor: 重试间隔因子
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def extract_segments(url, target_segments, output_file, max_retries=3, filter_patterns=None):
    """
    从URL获取文本内容，提取特定段落到输出文件
    
    Args:
        url: 源文件的URL地址
        target_segments: 要提取的段落的列表，支持通配符*，如 ["*地区,#genre#", "MY,#genre#"]
        output_file: 输出文件路径
        max_retries: 最大重试次数
        filter_patterns: 需要过滤的字符串列表，包含这些字符串的行将被移除
    """
    # 设置默认过滤模式
    if filter_patterns is None:
        filter_patterns = ["chinamobile.com"]
    
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            print(f"开始从 {url} 提取内容 (尝试 {retry_count + 1}/{max_retries + 1})...")
            
            # 创建带有重试机制的会话
            session = create_session_with_retry()
            
            # 设置请求头，模拟浏览器访问
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 发送HTTP请求获取内容
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()  # 检查请求是否成功
            
            content = response.text
            lines = content.split('\n')
            print(f"获取到 {len(lines)} 行原始内容")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # 提取目标段落
            extracted_content = []
            in_target_segment = False
            current_segment = None
            matched_segments = set()
            filtered_count = 0
            
            print("正在分析内容并匹配目标段落...")
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 检查是否为分段标记
                if line.endswith(',#genre#'):
                    # 检查是否匹配任何目标分段（支持通配符）
                    matched = False
                    for pattern in target_segments:
                        if fnmatch.fnmatch(line, pattern):
                            matched = True
                            matched_segments.add(line)
                            break
                    
                    if matched:
                        in_target_segment = True
                        current_segment = line
                        # 分段标记本身不过滤
                        extracted_content.append(line)
                        print(f"找到匹配段落: {line}")
                    # 如果遇到其他分段标记且当前正在记录目标分段，则停止
                    elif in_target_segment:
                        in_target_segment = False
                        current_segment = None
                
                # 如果在目标分段中，记录内容（过滤指定模式）
                elif in_target_segment:
                    # 检查是否包含需要过滤的字符串
                    should_filter = any(pattern in line for pattern in filter_patterns)
                    
                    if not should_filter:
                        extracted_content.append(line)
                    else:
                        filtered_count += 1
                        if filtered_count <= 10:  # 只显示前10个过滤记录，避免输出过多
                            print(f"过滤掉包含过滤模式的行: {line[:50]}...")
            
            # 写入输出文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(extracted_content))
                
            print(f"成功提取 {len(extracted_content)} 行内容到 {output_file}")
            print(f"过滤掉 {filtered_count} 行包含指定模式的内容")
            
            if matched_segments:
                print(f"匹配到的段落: {', '.join(sorted(matched_segments))}")
            else:
                print("警告: 没有找到任何匹配的段落")
            
            return True
            
        except requests.exceptions.ConnectionError as e:
            retry_count += 1
            if retry_count <= max_retries:
                wait_time = 2 ** retry_count  # 指数退避策略
                print(f"连接错误: {e}")
                print(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"连接错误，已达到最大重试次数: {e}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"网络请求错误: {e}")
            return False
            
        except Exception as e:
            print(f"处理过程中发生错误: {e}")
            return False
    
    return False

if __name__ == "__main__":
    # 配置参数
    url = "http://be.is-best.net/i/8/7408578.txt"  # 替换为实际的URL
    target_segments = [
        "*地区,#genre#",  # 匹配所有地区
        "央视,#genre#", "卫视,#genre#", "地方,#genre#",
        "影视,#genre#", "一起看,#genre#", "春晚,#genre#"
    ]
    output_file = "TMP/ys.txt"
    
    # 需要过滤的模式列表
    filter_patterns = ["chinamobile.com"]
    
    # 执行提取
    success = extract_segments(
        url=url,
        target_segments=target_segments,
        output_file=output_file,
        max_retries=3,
        filter_patterns=filter_patterns
    )
    
    if not success:
        print("程序执行失败，请检查网络连接或URL是否正确")
