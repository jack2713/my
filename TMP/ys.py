import requests
import re
import os

def download_and_extract_content_regex():
    url = "https://raw.githubusercontent.com/jack2713/my/refs/heads/main/myq.txt"
    output_file = "TMP/ys.txt"
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        # 发送GET请求获取文件内容
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        content = response.text
        
        # 定义要提取的关键词列表
        keywords = [
            "注意事项,#genre#", "MY,#genre#", "广电,#genre#", "电影频道,#genre#",
            "自制明星,#genre#", "自制影院,#genre#", "自制剧场,#genre#",
            "BXTV,#genre#", "央视,#genre#", "卫视,#genre#", "地方,#genre#",
            "影视,#genre#", "一起看,#genre#", "春晚,#genre#"
        ]
        
        # 构建正则表达式模式
        pattern = r'^(' + '|'.join(re.escape(keyword) for keyword in keywords) + r')(?:\n.*?)+?(?=(?:^' + '|'.join(re.escape(keyword) for keyword in keywords) + r')|\Z)'
        
        # 查找所有匹配的内容
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        # 将匹配的内容写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            for match in matches:
                f.write(match.strip() + '\n\n')
        
        print(f"成功提取 {len(matches)} 个段落到 {output_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    # 两种方法任选一种
    download_and_extract_content()  # 推荐使用这个版本
    # download_and_extract_content_regex()
