import requests
import os

def download_live_txt():
    url = "http://43.251.226.89:8080/live.txt"
    
    try:
        # 发送GET请求
        response = requests.get(url)
        
        # 检查请求是否成功
        response.raise_for_status()
        
        # 创建目录（如果不存在）
        os.makedirs("TMP", exist_ok=True)
        
        # 保存内容到文件
        file_path = os.path.join("TMP", "1699.txt")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(response.text)
        
        print(f"内容已成功保存到: {file_path}")
        print(f"文件大小: {len(response.text)} 字节")
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
    except Exception as e:
        print(f"保存文件时出错: {e}")

if __name__ == "__main__":
    download_live_txt()
