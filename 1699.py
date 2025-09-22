import requests
import json
import os
from typing import List, Dict, Any

class JSONParser:
    def __init__(self):
        self.output_dir = "TMP"
        self.output_file = os.path.join(self.output_dir, "169.txt")
        self.ensure_output_directory()
    
    def ensure_output_directory(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def fetch_json_from_url(self, url: str) -> Any:
        """从URL获取JSON数据"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取数据时出错: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return None
    
    def extract_data(self, data: Any) -> List[Dict[str, str]]:
        """从JSON数据中提取name和url字段"""
        result = []
        
        if isinstance(data, list):
            # 处理数组
            for item in data:
                result.extend(self.extract_data(item))
        elif isinstance(data, dict):
            # 处理对象
            if "name" in data and "url" in data:
                result.append({
                    "name": data["name"],
                    "url": data["url"]
                })
            
            # 递归处理嵌套对象
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    result.extend(self.extract_data(value))
        
        return result
    
    def save_to_file(self, data: List[Dict[str, str]]):
        """将数据保存到文件"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(f"{item['name']},{item['url']}\n")
            print(f"数据已成功保存到 {self.output_file}")
            print(f"共提取了 {len(data)} 条记录")
        except IOError as e:
            print(f"保存文件时出错: {e}")
    
    def process_urls(self, urls: List[str]):
        """处理多个URL"""
        all_data = []
        
        for url in urls:
            print(f"正在处理: {url}")
            json_data = self.fetch_json_from_url(url)
            
            if json_data is not None:
                extracted_data = self.extract_data(json_data)
                all_data.extend(extracted_data)
                print(f"从该URL提取了 {len(extracted_data)} 条记录")
            else:
                print(f"无法处理URL: {url}")
        
        # 保存所有数据
        if all_data:
            self.save_to_file(all_data)
        else:
            print("没有提取到任何数据")

def main():
    # 创建解析器实例
    parser = JSONParser()
    
    # 定义要处理的URL列表
    urls = [
        "https://raw.githubusercontent.com/bugsfreeweb/LiveTVCollector/refs/heads/main/LiveTV/China/LiveTV.json",
        # 可以添加更多URL
        # "https://example.com/data1.json",
        # "https://example.com/data2.json",
    ]
    
    # 处理URL
    parser.process_urls(urls)

if __name__ == "__main__":
    main()
