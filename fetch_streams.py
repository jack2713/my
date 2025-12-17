import requests
import time
import concurrent.futures
import os
from typing import List, Dict, Optional, Tuple

class GitIPTVFetcher:
    def __init__(self, github_token: Optional[str] = None):
        """
        初始化GitIPTVFetcher
        
        Args:
            github_token: GitHub个人访问令牌（用于访问私有仓库）
        """
        self.github_token = "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"
        self.session = requests.Session()
        
        # 设置请求头
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        # 如果有GitHub token，添加到请求头
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
    
    def fetch_url_content(self, url: str) -> Tuple[str, Optional[str]]:
        """
        获取URL内容，支持GitHub私有仓库
        
        Args:
            url: 要获取的URL
            
        Returns:
            元组 (url, content) - 成功返回内容字符串，失败返回None
        """
        try:
            start_time = time.time()
            
            # 处理GitHub raw URL，将 /refs/heads/ 转换为特定格式
            if 'raw.githubusercontent.com' in url and '/refs/heads/' in url:
                # 转换为API URL以支持私有仓库
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
        将GitHub raw URL转换为API URL
        
        Args:
            url: GitHub raw URL
            
        Returns:
            转换后的URL
        """
        try:
            # 解析GitHub raw URL
            # 例如: https://raw.githubusercontent.com/user/repo/refs/heads/main/path/file.txt
            parts = url.replace('https://raw.githubusercontent.com/jack2713/', '').split('/')
            
            if len(parts) >= 4:
                user = parts[0]
                repo = parts[1]
                # 跳过 refs/heads/
                branch_start = parts.index('refs') if 'refs' in parts else 2
                # 查找实际的分支名（通常是 refs/heads/ 之后的部分）
                if branch_start + 3 < len(parts):
                    # 重构为直接的 raw URL
                    file_path = '/'.join(parts[branch_start+3:])
                    # 使用直接的 raw URL，因为 GitHub token 可以在 headers 中传递
                    return f"https://raw.githubusercontent.com/{user}/{repo}/main/{file_path}"
            
            # 如果无法转换，返回原URL
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
            # 去除行尾空格
            line = line.rstrip()
            
            # 过滤不需要的行
            filter_keywords = ['更新时间', '关于', '解锁', '公众号', '软件库', '#EXTINF:']
            if any(keyword in line for keyword in filter_keywords):
                continue
            
            # 处理包含#genre#的行
            if '#genre#' in line.lower():
                # 替换下划线和??
                line = line.replace('_', '').replace('??', '')
            
            # 添加非空行
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
            # 提交所有任务，并保持原始顺序
            future_to_index = {}
            for i, url in enumerate(urls):
                future = executor.submit(self.fetch_url_content, url)
                future_to_index[future] = i
            
            # 按照URL顺序收集结果
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
        
        # 按照原始顺序处理结果
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
            filename: 文件名，如果为None则使用时间戳
        """
        if not filename:
            timestamp = time.strftime("%Y%m%d%H%M%S")
            filename = f'myq.txt'
        
        # 添加注意事项
        notice = f"注意事项,#genre#\n{timestamp if 'timestamp' in locals() else time.strftime('%Y%m%d%H%M%S')}仅供测试自用如有侵权请通知,http://zzy789.xyz/douyu1.php?id=3186217\n"
        
        # 保存文件
        with open(filename, 'w', encoding='UTF-8') as file:
            file.write(notice)
            for line in lines:
                file.write(line + '\n')
        
        print(f"Saved {len(lines)} lines to {filename}")
        return filename


def main():
    """
    主函数，配置和执行获取过程
    """
    # 从环境变量获取GitHub Token（推荐方式）
    # 或者在代码中直接设置：github_token = "your_token_here"
    github_token = os.getenv('GITHUB_TOKEN')
    
    # 初始化fetcher
    fetcher = GitIPTVFetcher(github_token=github_token)
    
    # 定义URL列表
    urls = [
        # GitHub URLs (将自动处理为支持私有仓库的格式)
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/mytemp.txt', 
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/mytemp01.txt',
        'http://156.238.248.80/2099.php',
        'http://bxtv.3a.ink/live.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/TMP1.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/dy01.txt',
        'http://rihou.cc:555/gggg.nzk',
        'https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/bbxx.txt',
        #'https://raw.githubusercontent.com/wwb521/live/main/tv.txt',
        'https://live.hacks.tools/tv/iptv4.txt',
        'http://iptv.4666888.xyz/FYTV.txt',
    ]
    
    print(f"Starting to fetch {len(urls)} URLs in order...")
    
    # 获取并处理所有URL（保持顺序）
    all_lines = fetcher.fetch_multiple_urls(urls, max_workers=5)
    
    print(f"Total processed lines: {len(all_lines)}")
    
    # 保存到文件
    saved_file = fetcher.save_to_file(all_lines)
    print(f"Process completed. File saved as: {saved_file}")


if __name__ == "__main__":
    # 环境变量设置说明
    print("=" * 60)
    print("GitHub IPTV Fetcher")
    print("=" * 60)
    print("Note: To access private GitHub repositories,")
    print("set the GITHUB_TOKEN environment variable.")
    print("Example: export GITHUB_TOKEN='your_personal_access_token'")
    print("=" * 60)
    
    # 运行主函数
    main()
