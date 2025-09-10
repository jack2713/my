import requests
import os
import fnmatch

def extract_segments(url, target_segments, output_file):
    """
    从URL获取文本内容，提取特定段落到输出文件
    
    Args:
        url: 源文件的URL地址
        target_segments: 要提取的段落的列表，支持通配符*，如 ["*地区,#genre#", "MY,#genre#"]
        output_file: 输出文件路径
    """
    try:
        # 发送HTTP请求获取内容
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        
        content = response.text
        lines = content.split('\n')
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 提取目标段落
        extracted_content = []
        in_target_segment = False
        current_segment = None
        
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
                        break
                
                if matched:
                    in_target_segment = True
                    current_segment = line
                    extracted_content.append(line)
                # 如果遇到其他分段标记且当前正在记录目标分段，则停止
                elif in_target_segment:
                    in_target_segment = False
                    current_segment = None
            
            # 如果在目标分段中，记录内容
            elif in_target_segment:
                extracted_content.append(line)
        
        # 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(extracted_content))
            
        print(f"成功提取 {len(extracted_content)} 行内容到 {output_file}")
        
    except requests.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"处理过程中发生错误: {e}")

if __name__ == "__main__":
    # 配置参数
    url = "http://be.is-best.net/i/8/7408578.txt"  # 替换为实际的URL
    target_segments = [
        "*地区,#genre#",  # 匹配所有地区
        "央视,#genre#", "卫视,#genre#", "地方,#genre#",
        "影视,#genre#", "一起看,#genre#", "春晚,#genre#"
    ]
    output_file = "TMP/ys.txt"
    
    # 执行提取
    extract_segments(url, target_segments, output_file)
