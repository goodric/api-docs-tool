#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口提取并生成HTML页面脚本
直接访问API文档URL，提取接口信息并生成HTML页面
"""

import json
import requests
import sys
import time
import argparse
import re
import csv
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, List, Any, Tuple


def fetch_api_docs(url: str) -> Dict[str, Any]:
    """
    从URL获取API文档数据
    
    Args:
        url: API文档URL
        
    Returns:
        解析后的JSON数据
    """
    try:
        print(f"正在访问API文档: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 尝试解析JSON
        try:
            return response.json()
        except json.JSONDecodeError:
            # 如果直接解析失败，可能是字符串格式的JSON
            content = response.text.strip()
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1].replace('\\"', '"').replace('\\\\', '\\')
            return json.loads(content)
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        sys.exit(1)


def extract_endpoints(api_docs: Dict[str, Any], api_docs_url: str, api_base_url: str = None) -> List[Dict[str, str]]:
    """
    提取API接口信息
    
    Args:
        api_docs: API文档数据
        api_docs_url: API文档URL，用于提取基础地址
        api_base_url: API基础URL，如果提供则优先使用
        
    Returns:
        接口信息列表
    """
    endpoints = []
    paths = api_docs.get('paths', {})
    servers = api_docs.get('servers', [])
    
    # 优先使用传入的base_url，否则使用API文档中的servers信息
    if api_base_url:
        base_url = api_base_url.rstrip('/')
    elif servers:
        base_url = servers[0].get('url', '').rstrip('/')
    else:
        # 如果没有服务器信息，从API文档URL中提取基础地址
        from urllib.parse import urlparse
        parsed_url = urlparse(api_docs_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                # 构建完整URL，确保路径以/开头
                clean_path = path if path.startswith('/') else f'/{path}'
                full_url = f"{base_url}{clean_path}"
                
                endpoint_info = {
                    'path': path,
                    'full_url': full_url,
                    'method': method.upper(),
                    'summary': details.get('summary', ''),
                    'description': details.get('description', ''),
                    'operationId': details.get('operationId', ''),
                    'tags': details.get('tags', [])
                }
                endpoints.append(endpoint_info)
    
    return endpoints


def parse_methods(method_string: str) -> List[str]:
    """
    解析HTTP方法字符串
    
    Args:
        method_string: 方法字符串，如 "get,post,put"
        
    Returns:
        大写的方法列表
    """
    if not method_string:
        return []
    
    # 分割并清理方法名
    methods = [method.strip().upper() for method in method_string.split(',')]
    
    # 验证方法名
    valid_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}
    invalid_methods = [method for method in methods if method not in valid_methods]
    
    if invalid_methods:
        print(f"警告: 无效的HTTP方法: {', '.join(invalid_methods)}")
        print(f"有效的方法: {', '.join(sorted(valid_methods))}")
        # 只返回有效的方法
        methods = [method for method in methods if method in valid_methods]
    
    return methods


def extract_domain_from_url(url: str) -> str:
    """
    从URL中提取域名并生成安全的文件名
    
    Args:
        url: API文档URL
        
    Returns:
        安全的文件名（不包含特殊字符）
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # 移除端口号
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # 替换特殊字符为下划线
        safe_domain = re.sub(r'[^\w\-\.]', '_', domain)
        
        # 如果域名为空或只包含特殊字符，使用默认名称
        if not safe_domain or safe_domain == '_':
            safe_domain = 'api_docs'
        
        return f"{safe_domain}.html"
        
    except Exception:
        return "api_docs.html"


def request_endpoint(endpoint: Dict[str, str], include_delete: bool = False) -> Tuple[int, int]:
    """
    请求单个接口并获取响应信息
    
    Args:
        endpoint: 接口信息字典
        include_delete: 是否包含DELETE方法
        
    Returns:
        (响应码, 响应内容长度)
    """
    method = endpoint['method'].upper()
    url = endpoint['full_url']
    
    # 根据参数决定是否跳过DELETE方法
    if method == 'DELETE' and not include_delete:
        return 0, 0
    
    try:
        # 设置请求超时时间
        timeout = 10
        
        # 根据不同的HTTP方法发送请求
        if method == 'GET':
            response = requests.get(url, timeout=timeout)
        elif method == 'POST':
            # POST请求发送空的JSON数据
            response = requests.post(url, json={}, timeout=timeout)
        elif method == 'PUT':
            # PUT请求发送空的JSON数据
            response = requests.put(url, json={}, timeout=timeout)
        elif method == 'PATCH':
            # PATCH请求发送空的JSON数据
            response = requests.patch(url, json={}, timeout=timeout)
        elif method == 'HEAD':
            response = requests.head(url, timeout=timeout)
        elif method == 'OPTIONS':
            response = requests.options(url, timeout=timeout)
        else:
            return 0, 0
        
        # 获取响应内容长度
        content_length = len(response.content) if response.content else 0
        
        return response.status_code, content_length
        
    except requests.exceptions.Timeout:
        return -1, 0  # 超时
    except requests.exceptions.ConnectionError:
        return -2, 0  # 连接错误
    except requests.exceptions.RequestException:
        return -3, 0  # 其他请求错误
    except Exception:
        return -4, 0  # 其他未知错误


def request_all_endpoints(endpoints: List[Dict[str, str]], request_limit: int = None, include_delete: bool = False, allowed_methods: List[str] = None) -> List[Dict[str, Any]]:
    """
    请求所有接口并获取响应信息
    
    Args:
        endpoints: 接口信息列表
        request_limit: 请求接口数量限制，None表示请求所有接口
        include_delete: 是否包含DELETE方法
        allowed_methods: 允许的HTTP方法列表，None表示不限制
        
    Returns:
        包含响应结果的接口信息列表
    """
    total = len(endpoints)
    
    # 根据方法过滤接口
    if allowed_methods:
        filtered_endpoints = [ep for ep in endpoints if ep['method'].upper() in allowed_methods]
        print(f"只请求 {', '.join(allowed_methods)} 方法的接口")
    else:
        filtered_endpoints = endpoints
    
    # 如果设置了请求限制，只请求前N个接口
    if request_limit:
        endpoints_to_request = filtered_endpoints[:request_limit]
        print(f"只请求前 {request_limit} 个接口")
    else:
        endpoints_to_request = filtered_endpoints
    
    for i, endpoint in enumerate(endpoints_to_request, 1):
        # 请求接口
        status_code, content_length = request_endpoint(endpoint, include_delete)
        
        # 添加响应结果到接口信息中
        endpoint['status_code'] = status_code
        endpoint['content_length'] = content_length
        
        # 添加延迟避免请求过于频繁
        time.sleep(0.1)
    
    # 为未请求的接口设置默认值
    for endpoint in filtered_endpoints[len(endpoints_to_request):]:
        endpoint['status_code'] = 0  # 跳过
        endpoint['content_length'] = 0
    
    print("接口请求完成！")
    return endpoints


def generate_html(endpoints: List[Dict[str, Any]], api_info: Dict[str, Any]) -> str:
    """
    生成HTML页面
    
    Args:
        endpoints: 接口信息列表
        api_info: API基本信息
        
    Returns:
        HTML字符串
    """
    title = api_info.get('title', 'API接口文档')
    description = api_info.get('description', '')
    version = api_info.get('version', '')
    
    
    # 生成HTML
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        
        .container {{
            max-width: 1600px;
            width: 95%;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        
        .header p {{
            margin: 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 15px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            min-width: 120px;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.8;
        }}
        
        .content {{
            padding: 30px 50px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.5em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        .api-table {{
            width: 100%;
            min-width: 1000px;
            border-collapse: collapse;
            margin: 0 0 20px 0;
            table-layout: auto;
        }}
        
        .table-container {{
            overflow-x: auto;
            margin: 0 -50px;
            padding: 0 50px;
        }}
        
        .api-table th {{
            background: #f8f9fa;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            color: #555;
            border-bottom: 2px solid #e0e0e0;
            height: 40px;
            box-sizing: border-box;
            white-space: nowrap;
        }}
        
        .api-table td {{
            padding: 12px 8px;
            border-bottom: 1px solid #e0e0e0;
            vertical-align: middle;
            height: 40px;
            box-sizing: border-box;
            white-space: nowrap;
        }}
        
        .api-table tr {{
            height: 40px;
        }}
        
        .description-cell {{
            min-width: 300px;
            white-space: nowrap;
        }}
        
        .url-cell {{
            width: 600px;
            max-width: 600px;
            overflow-x: auto;
            white-space: nowrap;
            position: relative;
        }}
        
        .url-cell::-webkit-scrollbar {{
            height: 6px;
        }}
        
        .url-cell::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 3px;
        }}
        
        .url-cell::-webkit-scrollbar-thumb {{
            background: #c1c1c1;
            border-radius: 3px;
        }}
        
        .url-cell::-webkit-scrollbar-thumb:hover {{
            background: #a8a8a8;
        }}
        
        .summary-cell {{
            min-width: 200px;
            white-space: nowrap;
        }}
        
        .status-cell {{
            width: 100px;
            text-align: center;
        }}
        
        .length-cell {{
            width: 120px;
            text-align: center;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }}
        
        .status {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-align: center;
            min-width: 50px;
        }}
        
        .status-success {{
            background: #e8f5e8;
            color: #2e7d32;
        }}
        
        .status-redirect {{
            background: #fff3e0;
            color: #f57c00;
        }}
        
        .status-client-error {{
            background: #ffebee;
            color: #d32f2f;
        }}
        
        .status-server-error {{
            background: #fce4ec;
            color: #c2185b;
        }}
        
        .status-skip {{
            background: #f5f5f5;
            color: #666;
        }}
        
        .status-timeout {{
            background: #fff8e1;
            color: #f9a825;
        }}
        
        .status-error {{
            background: #ffebee;
            color: #d32f2f;
        }}
        
        .status-unknown {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}
        
        .api-table tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .api-table tr.selected {{
            background-color: #e3f2fd;
        }}
        
        .method {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
            min-width: 60px;
            text-align: center;
        }}
        
        .method.get {{ background: #e8f5e8; color: #2e7d32; }}
        .method.post {{ background: #e3f2fd; color: #1976d2; }}
        .method.put {{ background: #fff3e0; color: #f57c00; }}
        .method.delete {{ background: #ffebee; color: #d32f2f; }}
        .method.patch {{ background: #f3e5f5; color: #7b1fa2; }}
        
        .url {{
            color: #1976d2;
            text-decoration: none;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
        }}
        
        .url:hover {{
            text-decoration: underline;
        }}
        
        .summary {{
            font-weight: 500;
            color: #333;
        }}
        
        .tags {{
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }}
        
        .tag {{
            background: #e0e0e0;
            color: #666;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }}
        
        .timestamp {{
            color: #999;
            font-size: 0.9em;
        }}
        
        .footer a {{
            color: #999;
            text-decoration: none;
            transition: color 0.3s ease;
        }}
        
        .footer a:hover {{
            color: #667eea;
            text-decoration: underline;
        }}
        
        @media (max-width: 1024px) {{
            .container {{
                width: 98%;
                max-width: 1000px;
            }}
        }}
        
        @media (max-width: 768px) {{
            .container {{
                margin: 10px;
                border-radius: 0;
                width: calc(100% - 20px);
                max-width: none;
            }}
            
            .header {{
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .content {{
                padding: 20px 30px;
            }}
            
            .api-table {{
                font-size: 0.9em;
                min-width: 800px;
                width: 100%;
                margin: 0 0 20px 0;
            }}
            
            .table-container {{
                overflow-x: auto;
                margin: 0 -30px;
                padding: 0 30px;
            }}
            
            .api-table th,
            .api-table td {{
                padding: 8px 6px;
                height: 35px;
            }}
            
            .api-table tr {{
                height: 35px;
            }}
            
            .description-cell {{
                min-width: 200px;
            }}
            
            .url-cell {{
                width: 400px;
                max-width: 400px;
                overflow-x: auto;
            }}
            
            .summary-cell {{
                min-width: 150px;
            }}
            
            .status-cell {{
                width: 80px;
            }}
            
            .length-cell {{
                width: 100px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>{description}</p>
            <div class="stats">
                <div class="stat-item">
                    <span class="stat-number">{len(endpoints)}</span>
                    <span class="stat-label">总接口数</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{version}</span>
                    <span class="stat-label">版本</span>
                </div>
            </div>
        </div>
        
        <div class="content">
"""
    
    # 添加所有接口的汇总表格
    html += """
            <div class="section">
                <h2 class="section-title">所有接口列表</h2>
                <div class="table-container">
                    <table class="api-table">
                    <thead>
                        <tr>
                            <th style="width: 60px;">序号</th>
                            <th style="width: 80px;">方法</th>
                            <th style="width: 600px;">接口路径</th>
                            <th style="width: 100px;">响应码</th>
                            <th style="width: 120px;">返回长度</th>
                            <th>接口名称</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for i, endpoint in enumerate(endpoints, 1):
        # 处理响应码显示
        status_code = endpoint.get('status_code', 0)
        if status_code == 0:
            status_display = "跳过"
            status_class = "status-skip"
        elif status_code == -1:
            status_display = "超时"
            status_class = "status-timeout"
        elif status_code == -2:
            status_display = "连接错误"
            status_class = "status-error"
        elif status_code == -3:
            status_display = "请求错误"
            status_class = "status-error"
        elif status_code == -4:
            status_display = "未知错误"
            status_class = "status-error"
        elif 200 <= status_code < 300:
            status_display = str(status_code)
            status_class = "status-success"
        elif 300 <= status_code < 400:
            status_display = str(status_code)
            status_class = "status-redirect"
        elif 400 <= status_code < 500:
            status_display = str(status_code)
            status_class = "status-client-error"
        elif 500 <= status_code < 600:
            status_display = str(status_code)
            status_class = "status-server-error"
        else:
            status_display = str(status_code)
            status_class = "status-unknown"
        
        # 处理返回长度显示
        content_length = endpoint.get('content_length', 0)
        status_code = endpoint.get('status_code', 0)
        
        # 如果是跳过或请求失败，显示"/"
        if status_code == 0 or status_code < 0:
            length_display = "/"
        elif content_length == 0:
            length_display = "0"
        elif content_length < 1024:
            length_display = f"{content_length}"
        elif content_length < 1024 * 1024:
            length_display = f"{content_length / 1024:.1f}K"
        else:
            length_display = f"{content_length / (1024 * 1024):.1f}M"
        
        html += f"""
                        <tr onclick="this.classList.toggle('selected')">
                            <td>{i}</td>
                            <td><span class="method {endpoint['method'].lower()}">{endpoint['method']}</span></td>
                            <td class="url-cell"><a href="{endpoint['full_url']}" class="url" target="_blank">{endpoint['path']}</a></td>
                            <td class="status-cell"><span class="status {status_class}">{status_display}</span></td>
                            <td class="length-cell">{length_display}</td>
                            <td class="summary-cell">{endpoint['summary'] or endpoint['operationId']}</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                    </table>
                </div>
            </div>
"""
    
    
    # 添加页脚
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html += f"""
        </div>
        
        <div class="footer">
            <p>生成时间: <span class="timestamp">{current_time}</span></p>
            <p style="margin-top: 15px; font-size: 0.9em; color: #999;">Powered by Goodric | <a href="https://github.com/Goodric" target="_blank">GitHub</a></p>
        </div>
    </div>
    
    <script>
        // 添加一些交互功能
        document.addEventListener('DOMContentLoaded', function() {{
            // 为所有表格行添加点击事件
            const rows = document.querySelectorAll('.api-table tbody tr');
            rows.forEach(row => {{
                row.addEventListener('click', function() {{
                    // 移除同组其他行的选中状态
                    const table = this.closest('table');
                    const otherRows = table.querySelectorAll('tr.selected');
                    otherRows.forEach(r => r.classList.remove('selected'));
                    
                    // 切换当前行的选中状态
                    this.classList.toggle('selected');
                }});
            }});
            
            // 为接口路径单元格添加触摸板水平滚动功能
            const urlCells = document.querySelectorAll('.url-cell');
            urlCells.forEach(cell => {{
                cell.addEventListener('wheel', function(e) {{
                    // 检查是否有水平滚动
                    if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {{
                        // 水平滚动：阻止默认行为并进行水平滚动
                        e.preventDefault();
                        this.scrollLeft += e.deltaX;
                    }}
                    // 垂直滚动：允许默认行为（页面滚动）
                }}, {{ passive: false }});
                
                // 添加鼠标悬停提示
                cell.addEventListener('mouseenter', function() {{
                    if (this.scrollWidth > this.clientWidth) {{
                        this.title = '使用触摸板左右滑动可以查看完整路径';
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>
"""
    
    return html


def generate_csv(endpoints: List[Dict[str, Any]], output_file: str) -> str:
    """
    生成CSV表格文件
    
    Args:
        endpoints: 接口信息列表
        output_file: 输出文件名（HTML）
        
    Returns:
        CSV文件名
    """
    csv_file = output_file.replace('.html', '.csv')
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['方法', '接口路径', '完整URL', '响应码', '返回长度', '接口名称']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for endpoint in endpoints:
                # 处理响应状态码
                status_code = endpoint.get('status_code', 0)
                if status_code == 0:
                    status_display = "跳过"
                elif status_code == -1:
                    status_display = "超时"
                elif status_code == -2:
                    status_display = "连接错误"
                elif status_code == -3:
                    status_display = "请求错误"
                elif status_code == -4:
                    status_display = "未知错误"
                else:
                    status_display = str(status_code)
                
                # 处理响应内容长度
                content_length = endpoint.get('content_length', 0)
                if status_code == 0 or status_code < 0:
                    length_display = "/"
                elif content_length == 0:
                    length_display = "0"
                elif content_length < 1024:
                    length_display = f"{content_length}"
                elif content_length < 1024 * 1024:
                    length_display = f"{content_length / 1024:.1f}K"
                else:
                    length_display = f"{content_length / (1024 * 1024):.1f}M"
                
                writer.writerow({
                    '方法': endpoint['method'],
                    '接口路径': endpoint['path'],
                    '完整URL': endpoint['full_url'],
                    '响应码': status_display,
                    '返回长度': length_display,
                    '接口名称': endpoint.get('summary', '') or endpoint.get('operationId', '')
                })
        
        return csv_file
        
    except Exception as e:
        print(f"生成CSV文件失败: {e}")
        return None


def main():
    """主函数"""
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(
        description='API接口文档提取工具 - 从OpenAPI/Swagger文档生成HTML页面和CSV表格',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python api-get.py -u http://localhost:8080/v2/api-docs
  python api-get.py -u https://api.example.com/swagger.json
  python api-get.py -u http://api.test.com/v2/api-docs -limit 20
  python api-get.py -u http://api.test.com/docs -all
  python api-get.py -u http://api.test.com/docs -method get,post
  python api-get.py -u http://api.test.com/docs -method get -limit 10
  python api-get.py -u http://api.test.com/docs -request-none

参数说明:
  -u URL      : API文档URL (必需)
  -limit N    : 限制请求接口数量，只请求前N个接口
  -all        : 请求所有接口，包含DELETE方法
  -method     : 指定HTTP方法，只请求指定方法的接口，如: get,post,put
  -request-none: 不对接口进行请求，只提取接口信息
  无参数      : 请求除DELETE方法外的所有接口

输出文件:
  自动生成HTML页面和CSV表格两种格式的文件
        """
    )
    
    parser.add_argument(
        '-u', '--url',
        help='API文档URL'
    )
    
    parser.add_argument(
        '-limit',
        type=int,
        help='限制请求接口数量，只请求前N个接口'
    )
    
    parser.add_argument(
        '-all',
        action='store_true',
        help='请求所有接口，包含DELETE方法'
    )
    
    parser.add_argument(
        '-method',
        help='指定HTTP方法，只请求指定方法的接口，多个方法用逗号分隔，如: get,post,put'
    )
    
    parser.add_argument(
        '-request-none',
        action='store_true',
        help='不对接口进行请求，只提取接口信息'
    )
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有提供URL参数，显示帮助信息
    if not args.url:
        parser.print_help()
        return
    
    api_url = args.url
    
    # 从URL中提取域名作为输出文件名
    output_file = extract_domain_from_url(api_url)
    print("开始提取API接口...")
    
    try:
        # 获取API文档
        api_docs = fetch_api_docs(api_url)
        
        # 提取接口信息
        endpoints = extract_endpoints(api_docs, api_url)
        
        print(f"成功提取 {len(endpoints)} 个API接口")
        
        # 解析方法参数
        allowed_methods = None
        if args.method:
            allowed_methods = parse_methods(args.method)
            if not allowed_methods:
                print("错误: 没有有效的HTTP方法")
                sys.exit(1)
        
        # 检查是否跳过请求阶段
        if args.request_none:
            print("跳过接口请求，只提取接口信息...")
            # 为所有接口设置默认值
            for endpoint in endpoints:
                endpoint['status_code'] = 0  # 跳过
                endpoint['content_length'] = 0
        else:
            # 确定请求参数
            if args.all:
                request_limit = None
                include_delete = True
                print("将请求所有接口，包含DELETE方法...")
            elif args.limit:
                request_limit = args.limit
                include_delete = False
                print(f"将请求前 {request_limit} 个接口（跳过DELETE方法）...")
            else:
                request_limit = None
                include_delete = False
                print("将请求除DELETE方法外的所有接口...")
            
            # 请求接口
            endpoints = request_all_endpoints(endpoints, request_limit=request_limit, include_delete=include_delete, allowed_methods=allowed_methods)
        
        # 生成HTML
        html_content = generate_html(endpoints, api_docs.get('info', {}))
        
        # 保存HTML文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 生成CSV文件
        csv_file = generate_csv(endpoints, output_file)
        
        print(f"✅ HTML页面已生成: {output_file}")
        if csv_file:
            print(f"📊 CSV表格已生成: {csv_file}")
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
