import requests
import os

def download_and_extract_content():
    url = "https://raw.githubusercontent.com/jack2713/my/refs/heads/main/myq.txt"
    output_file = "TMP/ys.txt"
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        # 发送GET请求获取文件内容
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        
        content = response.text
        lines = content.split('\n')
        
        # 定义要提取的关键词列表
        keywords = [
            "注意事项,#genre#", "MY,#genre#", "广电,#genre#", "电影频道,#genre#",
            "自制明星,#genre#", "自制影院,#genre#", "自制剧场,#genre#",
            "BXTV,#genre#", "央视,#genre#", "卫视,#genre#", "地方,#genre#",
            "影视,#genre#", "一起看,#genre#", "春晚,#genre#"
        ]
        
        # 将关键词转换为集合以便快速查找
        keyword_set = set(keywords)
        
        extracted_content = []
        current_section = []
        in_target_section = False
        
        # 遍历每一行
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是关键词行
            if line in keyword_set:
                # 如果已经在目标段落中，先保存当前段落
                if in_target_section and current_section:
                    extracted_content.append('\n'.join(current_section))
                    current_section = []
                
                # 开始新的目标段落
                in_target_section = True
                current_section.append(line)
            elif in_target_section:
                # 如果当前在目标段落中，添加行内容
                current_section.append(line)
            else:
                # 不在目标段落中，重置
                if current_section:
                    current_section = []
                in_target_section = False
        
        # 添加最后一个段落
        if in_target_section and current_section:
            extracted_content.append('\n'.join(current_section))
        
        # 将提取的内容写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            for section in extracted_content:
                f.write(section + '\n\n')
        
        print(f"成功提取 {len(extracted_content)} 个段落到 {output_file}")
        
        # 显示提取的段落信息
        for i, section in enumerate(extracted_content, 1):
            first_line = section.split('\n')[0]
            line_count = len(section.split('\n'))
            print(f"段落 {i}: {first_line} (共{line_count}行)")
            
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    download_and_extract_content()
