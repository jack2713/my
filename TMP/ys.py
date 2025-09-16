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
    
    print(f"目标输出文件: {output_file}")
    print(f"目标段落模式: {target_segments}")
    print(f"过滤模式: {filter_patterns}")
    
    while retry_count <= max_retries:
        try:
            print(f"\n开始从 {url} 提取内容 (尝试 {retry_count + 1}/{max_retries + 1})...")
            
            # 创建带有重试机制的会话
            session = create_session_with_retry()
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 发送HTTP请求获取内容
            print("发送请求...")
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            content = response.text
            lines = content.split('\n')
            print(f"获取到 {len(lines)} 行原始内容")
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir:  # 确保目录不为空
                os.makedirs(output_dir, exist_ok=True)
                print(f"已创建/确认目录: {output_dir}")
            
            # 提取目标段落
            extracted_content = []
            in_target_segment = False
            current_segment = None
            matched_segments = set()
            filtered_count = 0
            total_lines_processed = 0
            
            print("正在分析内容并匹配目标段落...")
            
            for line in lines:
                line = line.strip()
                total_lines_processed += 1
                
                if not line:
                    continue
                    
                # 检查是否为分段标记
                if line.endswith(',#genre#'):
                    # 检查是否匹配任何目标分段
                    matched = False
                    for pattern in target_segments:
                        if fnmatch.fnmatch(line, pattern):
                            matched = True
                            matched_segments.add(line)
                            break
                    
                    if matched:
                        in_target_segment = True
                        current_segment = line
                        extracted_content.append(line)
                        print(f"找到匹配段落: {line}")
                    elif in_target_segment:
                        in_target_segment = False
                        current_segment = None
                        print(f"离开段落，遇到新分段: {line}")
                
                # 如果在目标分段中，记录内容
                elif in_target_segment:
                    # 检查是否包含需要过滤的字符串
                    should_filter = any(pattern in line for pattern in filter_patterns)
                    
                    if not should_filter:
                        extracted_content.append(line)
                    else:
                        filtered_count += 1
                        if filtered_count <= 5:
                            print(f"过滤掉: {line[:60]}...")
            
            # 写入输出文件
            if extracted_content:
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(extracted_content))
                    
                    print(f"成功写入 {len(extracted_content)} 行到 {output_file}")
                    print(f"处理了 {total_lines_processed} 行原始数据")
                    print(f"过滤掉 {filtered_count} 行包含指定模式的内容")
                    
                    if matched_segments:
                        print(f"匹配到的段落: {', '.join(sorted(matched_segments))}")
                    else:
                        print("警告: 没有找到任何匹配的段落")
                    
                    # 验证文件是否真的写入
                    if os.path.exists(output_file):
                        file_size = os.path.getsize(output_file)
                        print(f"输出文件已创建，大小: {file_size} 字节")
                        
                        # 显示文件前几行作为验证
                        with open(output_file, 'r', encoding='utf-8') as f:
                            first_lines = f.readlines()[:3]
                        print("文件前3行内容:")
                        for i, line in enumerate(first_lines, 1):
                            print(f"  {i}: {line.strip()}")
                    else:
                        print("错误: 文件未成功创建")
                        return False
                    
                    return True
                    
                except IOError as e:
                    print(f"文件写入错误: {e}")
                    return False
            else:
                print("没有提取到任何内容")
                # 显示一些原始内容的前几行以帮助调试
                print("原始内容前10行:")
                for i, line in enumerate(lines[:10], 1):
                    print(f"  {i}: {line.strip()}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            retry_count += 1
            if retry_count <= max_retries:
                wait_time = 2 ** retry_count
                print(f"连接错误: {e}")
                print(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"连接错误，已达到最大重试次数: {e}")
                return False
                
        except requests.exceptions.Timeout as e:
            retry_count += 1
            if retry_count <= max_retries:
                wait_time = 2 ** retry_count
                print(f"请求超时: {e}")
                print(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"请求超时，已达到最大重试次数: {e}")
                return False
                
        except requests.exceptions.HTTPError as e:
            print(f"HTTP错误: {e}")
            print(f"状态码: {e.response.status_code if hasattr(e, 'response') else '未知'}")
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"网络请求错误: {e}")
            return False
            
        except Exception as e:
            print(f"处理过程中发生未知错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return False

def main():
    """主函数"""
    # 配置参数
    url = "http://be.is-best.net/i/8/7408578.txt"
    target_segments = [
        "*地区,#genre#",  # 匹配所有地区
        "央视,#genre#", "卫视,#genre#", "地方,#genre#",
        "影视,#genre#", "一起看,#genre#", "春晚,#genre#"
    ]
    output_file = "https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/ys.txt"
    
    # 需要过滤的模式列表
    filter_patterns = ["chinamobile.com"]
    
    print("=" * 60)
    print("开始执行提取程序")
    print("=" * 60)
    
    # 检查当前工作目录
    current_dir = os.getcwd()
    print(f"当前工作目录: {current_dir}")
    
    # 执行提取
    success = extract_segments(
        url=url,
        target_segments=target_segments,
        output_file=output_file,
        max_retries=3,
        filter_patterns=filter_patterns
    )
    
    print("=" * 60)
    if success:
        print("✅ 程序执行成功")
        
        # 显示文件统计信息
        try:
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                print(f"输出文件行数: {len(lines)}")
                print(f"输出文件大小: {os.path.getsize(output_file)} 字节")
                
                # 显示文件内容摘要
                print("\n文件内容摘要:")
                genre_sections = [line for line in lines if line.strip().endswith(',#genre#')]
                print(f"包含的段落数量: {len(genre_sections)}")
                for section in genre_sections[:5]:  # 显示前5个段落
                    print(f"  - {section.strip()}")
                if len(genre_sections) > 5:
                    print(f"  - ... 还有 {len(genre_sections) - 5} 个段落")
                    
        except Exception as e:
            print(f"读取输出文件时出错: {e}")
    else:
        print("❌ 程序执行失败")
        print("可能的原因:")
        print("  - 网络连接问题")
        print("  - URL不可访问")
        print("  - 文件写入权限问题")
        print("  - 没有匹配的目标段落")
        
        # 检查目录权限
        output_dir = os.path.dirname(output_file)
        if output_dir:
            if os.path.exists(output_dir):
                if os.access(output_dir, os.W_OK):
                    print(f"  ✓ 目录 {output_dir} 有写入权限")
                else:
                    print(f"  ✗ 目录 {output_dir} 无写入权限")
            else:
                print(f"  ? 目录 {output_dir} 不存在")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
