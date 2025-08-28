import requests
import os

def extract_sections_from_url(url, output_file, section_markers):
    """
    从URL获取文本并提取多个段落内容到输出文件
    
    参数:
    url: 源文本的URL地址
    output_file: 输出文件完整路径
    section_markers: 要提取的段落标记列表
    """
    try:
        # 从URL获取文本内容
        print(f"正在从URL获取内容: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.text
        lines = content.splitlines()
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")
        
        extracted_content = []
        extracted_sections = set()
        
        # 遍历所有标记，提取每个段落
        for marker in section_markers:
            print(f"正在提取段落: {marker}")
            
            # 查找开始标记的位置
            start_index = -1
            for i, line in enumerate(lines):
                if marker in line:
                    start_index = i
                    break
            
            if start_index == -1:
                print(f"警告: 未找到标记 '{marker}'")
                continue
            
            # 提取从开始标记到下一个标记之前的内容
            section_lines = []
            for i in range(start_index + 1, len(lines)):
                line = lines[i].strip()
                # 如果遇到下一个标记（包含#genre#的行），则停止提取
                if any(m in line for m in section_markers if m != marker) and i != start_index:
                    break
                if line:  # 只添加非空行
                    section_lines.append(lines[i] + '\n')
            
            if section_lines:
                # 添加段落标记作为分隔
                extracted_content.append(f"# {marker}\n")
                extracted_content.extend(section_lines)
                extracted_content.append("\n")  # 添加空行分隔不同段落
                extracted_sections.add(marker)
        
        if not extracted_content:
            print("错误: 未提取到任何内容")
            return False
        
        # 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as f_out:
            f_out.writelines(extracted_content)
        
        print(f"成功提取 {len(extracted_sections)} 个段落到 {output_file}")
        print(f"提取的段落: {', '.join(extracted_sections)}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"网络错误: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False

def extract_sections_from_file(input_file, output_file, section_markers):
    """
    从本地文件提取多个段落内容到输出文件
    
    参数:
    input_file: 本地输入文件路径
    output_file: 输出文件完整路径
    section_markers: 要提取的段落标记列表
    """
    try:
        # 从本地文件读取内容
        print(f"正在读取本地文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f_in:
            lines = f_in.readlines()
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")
        
        extracted_content = []
        extracted_sections = set()
        
        # 遍历所有标记，提取每个段落
        for marker in section_markers:
            print(f"正在提取段落: {marker}")
            
            # 查找开始标记的位置
            start_index = -1
            for i, line in enumerate(lines):
                if marker in line:
                    start_index = i
                    break
            
            if start_index == -1:
                print(f"警告: 未找到标记 '{marker}'")
                continue
            
            # 提取从开始标记到下一个标记之前的内容
            section_lines = []
            for i in range(start_index + 1, len(lines)):
                line = lines[i].strip()
                # 如果遇到下一个标记（包含#genre#的行），则停止提取
                if any(m in line for m in section_markers if m != marker) and i != start_index:
                    break
                if line:  # 只添加非空行
                    section_lines.append(lines[i])
            
            if section_lines:
                # 添加段落标记作为分隔
                extracted_content.append(f"# {marker}\n")
                extracted_content.extend(section_lines)
                extracted_content.append("\n")  # 添加空行分隔不同段落
                extracted_sections.add(marker)
        
        if not extracted_content:
            print("错误: 未提取到任何内容")
            return False
        
        # 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as f_out:
            f_out.writelines(extracted_content)
        
        print(f"成功提取 {len(extracted_sections)} 个段落到 {output_file}")
        print(f"提取的段落: {', '.join(extracted_sections)}")
        return True
        
    except FileNotFoundError:
        print(f"错误: 文件 {input_file} 不存在")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False

# 使用示例
if __name__ == "__main__":
    # 方式1: 从URL提取
    url = "https://raw.githubusercontent.com/jack2713/my/refs/heads/main/myq.txt"  # 替换为实际的URL
    output_path = "TMP/ys.txt"
    markers = ["注意事项,#genre#", "MY,#genre#", "广电,#genre#","电影频道,#genre#",
               "自制明星,#genre#","自制影院,#genre#","自制剧场,#genre#",
               "BXTV,#genre#","央视,#genre#","卫视,#genre#","地方,#genre#",
               "影视,#genre#","一起看,#genre#","春晚,#genre#"
              ]
