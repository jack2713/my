import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_file: str = "url_config.txt") -> List[Dict[str, str]]:
    """从配置文件加载URL列表"""
    url_list = []
    
    if not os.path.exists(config_file):
        logger.error(f"配置文件 {config_file} 不存在")
        return url_list
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 支持多种分隔符：冒号、逗号、空格
                if ':' in line:
                    parts = line.split(':', 1)
                elif ',' in line:
                    parts = line.split(',', 1)
                elif ' ' in line:
                    parts = line.split(' ', 1)
                else:
                    logger.warning(f"第{line_num}行格式错误: {line}")
                    continue
                
                if len(parts) == 2:
                    name = parts[0].strip()
                    url = parts[1].strip()
                    if name and url:
                        url_list.append({"name": name, "url": url})
                    else:
                        logger.warning(f"第{line_num}行名称或URL为空: {line}")
                else:
                    logger.warning(f"第{line_num}行格式错误: {line}")
        
        logger.info(f"从配置文件加载了 {len(url_list)} 个URL")
        return url_list
        
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        return []

def fetch_url_content(url: str, name: str, max_retries: int = 3) -> str:
    """获取URL内容，支持重试"""
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            # 尝试多种编码方式
            if response.encoding:
                content = response.text
            else:
                # 尝试常见编码
                for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-16']:
                    try:
                        content = response.content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    content = response.content.decode('utf-8', errors='ignore')
            
            return content.strip()
            
        except requests.exceptions.Timeout:
            logger.warning(f"获取 {name} 超时 ({url})，尝试 {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            continue
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取 {name} 失败 ({url}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            continue
            
        except Exception as e:
            logger.error(f"处理 {name} 时发生未知错误 ({url}): {e}")
            break
    
    return ""

def process_url_entry(url_data: Dict[str, str]) -> Dict[str, str]:
    """处理单个URL数据项"""
    url = url_data['url']
    name = url_data['name']
    
    logger.info(f"正在处理: {name}")
    
    # 获取URL内容
    content = fetch_url_content(url, name)
    
    if not content:
        return {"name": name, "content": "", "status": "failed"}
    
    # 准备输出内容
    lines = content.split('\n')
    processed_lines = []
    
    # 添加标题行
    processed_lines.append(f"{name},#genre#")
    
    # 处理每一行内容
    for line in lines:
        line = line.strip()
        # 跳过空行和注释行
        if line and not line.startswith('#'):
            processed_lines.append(line)
    
    result = '\n'.join(processed_lines)
    logger.info(f"完成处理: {name}, 获取到 {len(processed_lines)-1} 行内容")
    
    return {"name": name, "content": result, "status": "success"}

def main():
    """主函数"""
    # 配置文件路径
    config_file = "url_config.txt"
    
    # 加载配置
    url_list = load_config(config_file)
    
    if not url_list:
        logger.error("没有可处理的URL，程序退出")
        return
    
    # 创建输出目录
    output_dir = "TMP"
    output_file = os.path.join(output_dir, "new.txt")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"已创建目录: {output_dir}")
    
    # 使用多线程并行处理
    all_results = []
    successful_count = 0
    failed_count = 0
    
    logger.info(f"开始处理 {len(url_list)} 个URL...")
    
    with ThreadPoolExecutor(max_workers=min(10, len(url_list))) as executor:
        # 提交所有任务
        future_to_name = {executor.submit(process_url_entry, url_data): url_data['name'] 
                         for url_data in url_list}
        
        # 收集结果
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                result = future.result(timeout=30)
                all_results.append(result)
                if result["status"] == "success":
                    successful_count += 1
                else:
                    failed_count += 1
                    logger.warning(f"{name} 处理失败")
            except Exception as e:
                logger.error(f"处理 {name} 时发生异常: {e}")
                failed_count += 1
    
    # 按原始顺序排序结果（保持配置文件中的顺序）
    all_results.sort(key=lambda x: [item['name'] for item in url_list].index(x['name']) 
                     if x['name'] in [item['name'] for item in url_list] else len(url_list))
    
    # 写入文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, result in enumerate(all_results):
                if result["content"]:
                    if i > 0:
                        f.write('\n\n')  # URL内容之间添加两个换行作为分隔
                    f.write(result["content"])
        
        logger.info(f"成功将内容写入: {output_file}")
        logger.info(f"处理完成: 成功 {successful_count}, 失败 {failed_count}, 总计 {len(url_list)}")
        
        # 生成处理报告
        report_file = os.path.join(output_dir, "process_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"配置文件: {config_file}\n")
            f.write(f"输出文件: {output_file}\n")
            f.write(f"处理结果: 成功 {successful_count}, 失败 {failed_count}, 总计 {len(url_list)}\n\n")
            
            f.write("详细结果:\n")
            for result in all_results:
                status = "✓ 成功" if result["status"] == "success" else "✗ 失败"
                f.write(f"{result['name']}: {status}\n")
        
        logger.info(f"处理报告已保存到: {report_file}")
        
    except IOError as e:
        logger.error(f"写入文件失败: {e}")

def create_sample_config():
    """创建示例配置文件"""
    sample_content = "
天津,https://tj.sohu.blog/list.txt
北京,https://bj.sohu.blog/list.txt
上海,https://sh.sohu.blog/list.txt
"

# 更多配置可以继续添加
# 广州:https://gz.sohu.blog/list.txt
"""
    
    if not os.path.exists("url_config.txt"):
        with open("url_config.txt", 'w', encoding='utf-8') as f:
            f.write(sample_content)
        logger.info("已创建示例配置文件: url_config.txt")
        logger.info("请编辑该文件并添加您的URL配置")

if __name__ == "__main__":
    # 检查配置文件是否存在
    if not os.path.exists("url_config.txt"):
        create_sample_config()
        print("请先编辑 url_config.txt 文件，然后重新运行程序")
        exit(1)
    
    # 运行主程序
    main()
