# API接口文档提取工具

一个强大的Python脚本，用于从OpenAPI/Swagger文档中提取API接口信息，并生成美观的HTML页面和CSV表格。

在遇到/docs、/v3/api-docs、/v2/api-docs、/v2/swagger.json等openAPI接口文档路径时，api json信息堆在一起无法处理。
<img width="1226" height="1060" alt="image" src="https://github.com/user-attachments/assets/9edae0d9-5f92-4f37-b504-d5937dd260a3" />

使用此工具可将文档中的接口全部提取出来并进行请求，输出为接口列表。
<img width="2498" height="1470" alt="image" src="https://github.com/user-attachments/assets/6d7c102f-4cab-489e-a5c4-529df7167d20" />


## 功能特性

- 🔍 **自动提取**：从OpenAPI/Swagger文档URL自动提取所有API接口信息
- 📊 **双重输出**：同时生成HTML页面和CSV表格两种格式
- 🎨 **美观界面**：生成响应式、现代化的HTML页面，支持移动端
- 🚀 **接口测试**：可选择性对接口进行实际请求测试
- ⚡ **灵活配置**：支持多种参数配置，满足不同使用场景
- 📱 **移动友好**：HTML页面完全响应式设计，支持各种设备

## 安装要求

### Python版本
- Python 3.6+

### 依赖包
```bash
pip install requests
```

## 使用方法

### 基本用法

```bash
# 最简单的使用方式
python api-get.py -u http://localhost:8080/v2/api-docs

# 使用外部API文档
python api-get.py -u https://api.example.com/swagger.json
```

### 高级用法

```bash
# 限制请求接口数量
python api-get.py -u http://api.test.com/v2/api-docs -limit 20

# 请求所有接口（包含DELETE方法）
python api-get.py -u http://api.test.com/docs -all

# 只请求指定HTTP方法的接口
python api-get.py -u http://api.test.com/docs -method get,post

# 只请求GET方法的接口，限制10个
python api-get.py -u http://api.test.com/docs -method get -limit 10

# 不进行接口请求，只提取接口信息
python api-get.py -u http://api.test.com/docs -request-none
```

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `-u, --url` | API文档URL（必需） | `-u http://localhost:8080/v2/api-docs` |
| `-limit` | 限制请求接口数量 | `-limit 20` |
| `-all` | 请求所有接口，包含DELETE方法 | `-all` |
| `-method` | 指定HTTP方法，多个用逗号分隔 | `-method get,post,put` |
| `-request-none` | 不对接口进行请求，只提取信息 | `-request-none` |

## 输出文件

工具会自动生成两个文件：

1. **HTML页面**：`{域名}.html`
   - 美观的响应式界面
   - 完整的接口信息展示
   - 支持点击查看详情
   - 移动端友好

2. **CSV表格**：`{域名}.csv`
   - 包含所有接口的详细信息
   - 可用于Excel等工具进一步分析

## 功能详解

### 接口信息提取
- 自动解析OpenAPI/Swagger文档
- 提取接口路径、HTTP方法、描述等信息
- 智能构建完整的API URL

### 接口测试功能
- 可选择性对接口进行实际请求
- 显示响应状态码和内容长度
- 支持超时和错误处理
- 自动跳过DELETE方法（除非使用`-all`参数）

### HTML页面特性
- **响应式设计**：完美适配桌面和移动设备
- **交互功能**：点击行高亮、触摸板滚动支持
- **状态标识**：不同颜色标识不同的响应状态
- **统计信息**：显示接口总数、版本等统计信息

### 状态码说明
- **2xx**：成功响应（绿色）
- **3xx**：重定向（橙色）
- **4xx**：客户端错误（红色）
- **5xx**：服务器错误（紫色）
- **超时**：请求超时（黄色）
- **错误**：连接错误等（红色）
- **跳过**：未请求的接口（灰色）

## 使用场景

1. **API文档整理**：将分散的API接口整理成统一格式
2. **接口测试**：快速测试API接口的可用性
3. **文档生成**：为团队生成统一的API接口文档
4. **接口分析**：分析API接口的响应情况
5. **移动端查看**：在移动设备上方便地查看API文档

## 注意事项

1. **网络访问**：确保能够访问目标API文档URL
2. **请求频率**：工具会在请求间添加延迟，避免过于频繁的请求
3. **超时设置**：每个接口请求超时时间为10秒
4. **DELETE方法**：默认跳过DELETE方法，避免误删数据
5. **文件覆盖**：输出文件会覆盖同名的现有文件

## 错误处理

工具包含完善的错误处理机制：

- **网络错误**：自动重试和错误提示
- **JSON解析错误**：智能处理各种JSON格式
- **超时处理**：设置合理的超时时间
- **用户中断**：支持Ctrl+C优雅退出

## 技术特点

- **类型提示**：完整的Python类型注解
- **模块化设计**：功能模块清晰分离
- **异常处理**：全面的异常捕获和处理
- **代码规范**：遵循PEP 8编码规范

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进这个工具！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持OpenAPI/Swagger文档解析
- 生成HTML和CSV两种格式输出
- 支持接口请求测试功能
- 响应式HTML界面设计

---

**GitHub**: [https://github.com/Goodric](https://github.com/Goodric)
