import requests
import time
import concurrent.futures
import os
from typing import List, Dict, Optional, Tuple

class GitIPTVFetcher:
    def __init__(self):
        """
        初始化GitIPTVFetcher（公有仓库模式，无需认证）
        """
        self.session = requests.Session()
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    def fetch_url_content(self, url: str) -> Tuple[str, Optional[str]]:
        """
        获取URL内容，支持GitHub公有仓库
        
        Args:
            url: 要获取的URL
            
        Returns:
            元组 (url, content) - 成功返回内容字符串，失败返回None
        """
        try:
            start_time = time.time()
            
            # 对含有jack2713且包含refs/heads/的URL进行标准化
            if 'jack2713/my' in url:
                url = self._convert_github_url(url)
            
            response = self.session.get(url, headers=self.headers, timeout=15)
            elapsed_time = time.time() - start_time
            
            print(f"Request to {url} took {elapsed_time:.2f} seconds. Status: {response.status_code}")
            
            if response.status_code == 200:
                response.encoding = 'utf-8'
                return (url, response.text)
            else:
                print(f"Failed to retrieve {url} with status code {response.status_code}")
                return (url, None)
                
        except requests.exceptions.Timeout:
            print(f"Request to {url} timed out.")
            return (url, None)
            
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while requesting {url}: {e}")
            return (url, None)
    
    def _convert_github_url(self, url: str) -> str:
        """
        将含有refs/heads/的raw GitHub URL转换为标准格式
        
        Args:
            url: 含有refs/heads/的URL
            
        Returns:
            转换后的URL
        """
        try:
            if 'raw.githubusercontent.com' in url and '/refs/heads/' in url:
                # 去除 /refs/heads 段，例如：
                # https://raw.githubusercontent.com/jack2713/my/refs/heads/main/file.txt
                # -> https://raw.githubusercontent.com/jack2713/my/main/file.txt
                url = url.replace('/refs/heads/', '/')
            return url
        except Exception as e:
            print(f"Error converting GitHub URL {url}: {e}")
            return url
    
    def process_content(self, content: str) -> List[str]:
        """
        处理内容，过滤和清洗行
        
        Args:
            content: 原始内容
            
        Returns:
            处理后的行列表
        """
        processed_lines = []
        
        for line in content.splitlines():
            line = line.rstrip()
            
            filter_keywords = ['更新时间', '关于', '解锁', '公众号', '软件库', '#EXTINF:','权限','广播','订阅地址','➡️','更新日期','chinamobile']
            if any(keyword in line for keyword in filter_keywords):
                continue
            
            if '#genre#' in line.lower():
                line = line.replace('_', '').replace('??', '')
            
            if line.strip():
                processed_lines.append(line)
        
        return processed_lines
    
    def fetch_multiple_urls(self, urls: List[str], max_workers: int = 5) -> List[str]:
        """
        并发获取多个URL的内容，按照原始URL顺序排序
        
        Args:
            urls: URL列表
            max_workers: 最大并发数
            
        Returns:
            所有处理后的行列表，按照URL顺序排序
        """
        all_processed_lines = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {}
            for i, url in enumerate(urls):
                future = executor.submit(self.fetch_url_content, url)
                future_to_index[future] = i
            
            results = [None] * len(urls)
            for future in concurrent.futures.as_completed(future_to_index):
                i = future_to_index[future]
                try:
                    url, content = future.result()
                    results[i] = (url, content)
                    print(f"Successfully fetched {url} (index {i})")
                except Exception as e:
                    print(f"Error processing URL at index {i}: {e}")
                    results[i] = (urls[i], None)
        
        for i, (url, content) in enumerate(results):
            if content:
                processed_lines = self.process_content(content)
                all_processed_lines.extend(processed_lines)
                print(f"Processed {url} (index {i}), got {len(processed_lines)} lines")
            else:
                print(f"Skipped {url} (index {i}) due to fetch failure")
        
        return all_processed_lines
    
    def save_to_file(self, lines: List[str], filename: str = None):
        """
        保存处理后的行到文件
        
        Args:
            lines: 要保存的行列表
            filename: 文件名，默认使用时间戳
        """
        if not filename:
            timestamp = time.strftime("%Y%m%d%H%M%S")
            filename = f'myq.txt'
        
        notice = f"注意事项,#genre#\n{timestamp}仅供测试自用如有侵权请通知,https://live.ottiptv.cc/douyu/3186217\n"
        
        with open(filename, 'w', encoding='UTF-8') as file:
            file.write(notice)
            for line in lines:
                file.write(line + '\n')
        
        print(f"Saved {len(lines)} lines to {filename}")
        return filename


def main():
    """
    主函数，配置和执行获取过程（公有仓库模式）
    """
    fetcher = GitIPTVFetcher()
    
    urls = [
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/mytemp.txt', 
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/mytemp01.txt',
        'https://raw.githubusercontent.com/jack2713/mynew/refs/heads/main/my2.txt',
        'https://raw.githubusercontent.com/jack2713/mynew/refs/heads/main/my3.txt',
        'https://raw.githubusercontent.com/jack2713/mynew/refs/heads/main/my1.txt',
        #'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/1699.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/TMP.txt',
        'https://raw.githubusercontent.com/jack2713/mynew/refs/heads/main/TMP/s.txt',
        'http://iptv.4666888.xyz/FYTV.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/TMP1.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/dy01.txt',
        'https://raw.githubusercontent.com/jack2713/mynew/refs/heads/main/TMP/temp.txt',
        'https://raw.githubusercontent.com/jack2713/mynew/refs/heads/main/ttest.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/new.txt',
        'https://raw.githubusercontent.com/jack2713/mynew/refs/heads/main/zubo.txt',
        #'https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interfaceTXT.txt',
        'https://raw.githubusercontent.com/jack2713/mynew/refs/heads/main/rihou.txt',
        'https://raw.githubusercontent.com/jack2713/mynew/refs/heads/main/TMP/jsontxt.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/ys.txt',
        'https://raw.githubusercontent.com/swhtv/1/refs/heads/main/swtvlive',
    ]
    
    print(f"Starting to fetch {len(urls)} URLs in order...")
    
    all_lines = fetcher.fetch_multiple_urls(urls, max_workers=5)
    
    print(f"Total processed lines: {len(all_lines)}")
    
    saved_file = fetcher.save_to_file(all_lines)
    print(f"Process completed. File saved as: {saved_file}")


if __name__ == "__main__":
    print("=" * 60)
    print("GitHub IPTV Fetcher (Public Repos Mode)")
    print("=" * 60)
    main()
