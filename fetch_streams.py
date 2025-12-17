import requests
import time
import os
import base64

class SimpleIPTVFetcher:
    def __init__(self, github_token=None):
        self.github_token = "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"
        if not self.github_token:
            print("⚠️  警告: 未设置GITHUB_TOKEN，私有仓库可能无法访问")
            print("    设置方法: export GITHUB_TOKEN='your_personal_access_token'")
        
    def fetch_github_private(self, url):
        """使用GitHub API获取私有仓库文件"""
        try:
            # 从raw URL转换为API URL
            # 例如: https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/mytemp.txt
            # 转换为: https://api.github.com/repos/jack2713/my/contents/TMP/mytemp.txt?ref=main
            
            # 提取仓库信息和文件路径
            url = url.replace('/refs/heads/', '/')
            parts = url.replace('https://raw.githubusercontent.com/', '').split('/')
            
            if len(parts) >= 3:
                owner = parts[0]  # jack2713
                repo = parts[1]   # my
                branch = parts[2] # main
                file_path = '/'.join(parts[3:])  # TMP/mytemp.txt
                
                api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
                
                headers = {
                    'Authorization': f'token {self.github_token}',
                    'Accept': 'application/vnd.github.v3.raw',
                    'User-Agent': 'Mozilla/5.0'
                }
                
                print(f"使用GitHub API请求私有文件: {file_path}")
                response = requests.get(api_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # 对于私有仓库，我们直接获取文件内容
                    try:
                        # 如果是API返回的JSON，包含base64编码的内容
                        data = response.json()
                        if 'content' in data:
                            content = base64.b64decode(data['content']).decode('utf-8')
                            return content
                        else:
                            # 如果设置了Accept头部为raw，直接返回内容
                            return response.text
                    except:
                        # 如果已经是原始文本，直接返回
                        return response.text
                else:
                    print(f"GitHub API请求失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"GitHub私有仓库访问错误: {e}")
            return None
    
    def fetch_url(self, url):
        """获取URL内容"""
        try:
            start = time.time()
            
            # 如果是jack2713/my私有仓库，使用GitHub API
            if 'github.com/jack2713/my' in url:
                if not self.github_token:
                    print("❌ 错误: 需要GITHUB_TOKEN来访问私有仓库")
                    return None
                
                content = self.fetch_github_private(url)
                if content:
                    print(f"私有仓库获取成功，耗时: {time.time()-start:.1f}秒")
                    return content
                else:
                    print(f"私有仓库获取失败")
                    return None
            else:
                # 其他URL使用普通请求
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=15)
                
                print(f"公开URL获取: {response.status_code}, 耗时: {time.time()-start:.1f}秒")
                
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    return response.text
                return None
                
        except Exception as e:
            print(f"获取失败: {e}")
            return None
    
    def process_line(self, line):
        """处理单行内容"""
        line = line.rstrip()
        
        # 过滤不需要的行
        if any(keyword in line for keyword in ['更新时间', '关于', '解锁', '公众号', '软件库', '#EXTINF:']):
            return None
        
        # 处理包含#genre#的行
        if '#genre#' in line.lower():
            line = line.replace('_', '').replace('??', '')
        
        return line if line.strip() else None
    
    def fetch_all(self, urls):
        """获取所有URL内容"""
        all_lines = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] 正在获取: {url}")
            content = self.fetch_url(url)
            
            if content:
                lines_added = 0
                for line in content.splitlines():
                    processed = self.process_line(line)
                    if processed:
                        all_lines.append(processed)
                        lines_added += 1
                print(f"  成功添加 {lines_added} 行")
            else:
                print(f"  获取失败，跳过")
        
        return all_lines
    
    def save_to_file(self, lines):
        """保存到myq.txt文件"""
        timestamp = time.strftime("%Y%m%d%H%M%S")
        
        with open('myq.txt', 'w', encoding='UTF-8') as f:
            # 写入注意事项
            f.write("注意事项,#genre#\n")
            f.write(f"{timestamp}仅供测试自用如有侵权请通知,http://zzy789.xyz/douyu1.php?id=3186217\n\n")
            
            # 写入内容
            for line in lines:
                f.write(line + '\n')
        
        print(f"\n✅ 已保存 {len(lines)} 行到 myq.txt")
        return 'myq.txt'


def main():
    """主函数"""
    # 检查GitHub Token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("=" * 60)
        print("重要: 需要设置GITHUB_TOKEN环境变量来访问私有仓库")
        print("获取Token: https://github.com/settings/tokens")
        print("设置Token:")
        print("  Linux/Mac: export GITHUB_TOKEN='your_token_here'")
        print("  Windows: set GITHUB_TOKEN=your_token_here")
        print("=" * 60)
    
    # URL列表
    urls = [
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/mytemp.txt', 
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/mytemp01.txt',
        'http://156.238.248.80/2099.php',
        'http://bxtv.3a.ink/live.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/TMP1.txt',
        'https://raw.githubusercontent.com/jack2713/my/refs/heads/main/TMP/dy01.txt',
        'http://rihou.cc:555/gggg.nzk',
        'https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/bbxx.txt',
        'https://live.hacks.tools/tv/iptv4.txt',
        'http://iptv.4666888.xyz/FYTV.txt',
    ]
    
    print("\n开始获取IPTV源文件...")
    print(f"共 {len(urls)} 个URL (其中4个来自私有仓库)")
    print("-" * 60)
    
    # 初始化fetcher
    fetcher = SimpleIPTVFetcher(github_token)
    
    # 获取所有内容
    start_time = time.time()
    all_lines = fetcher.fetch_all(urls)
    
    # 保存文件
    if all_lines:
        fetcher.save_to_file(all_lines)
        print(f"\n总耗时: {time.time() - start_time:.1f}秒")
    else:
        print("\n❌ 未获取到任何内容")


if __name__ == "__main__":
    main()
