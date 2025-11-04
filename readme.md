# WriteSql - JSON 数据批量导入工具

## 项目简介

WriteSql 是一个用于将 JSON 格式的 DWARF 调试信息批量导入到 MySQL 数据库的工具。它通过 SSH 隧道安全连接到远程数据库，支持大批量数据的高效插入。

## 功能特性

- ✅ SSH 隧道安全连接远程数据库
- ✅ 递归扫描指定目录下的所有 JSON 文件
- ✅ 批量插入优化，提高导入速度
- ✅ 配置缓存机制，减少重复查询
- ✅ 进度条实时显示处理进度
- ✅ 完整的日志记录系统
- ✅ 异常处理和资源自动清理

## 环境要求

### Python 版本
- Python 3.7+

### 依赖包
```bash
pip install pymysql
pip install sshtunnel
pip install tqdm
```

## 配置说明

### 1. 创建配置文件

在项目根目录创建 `credits.py` 文件，包含以下配置：

```python
# SSH 连接配置
SSH_HOST_PORT = "your.ssh.host:22"  # SSH 服务器地址和端口
SSH_USERNAME = "your_username"       # SSH 用户名
SSH_PKEY_PATH = "path/to/private_key"  # SSH 私钥文件路径（可选）
SSH_PKEY_PASSPHRASE = "your_passphrase"  # 私钥密码（如果有）

# 数据库配置
DB_HOST = "127.0.0.1"  # 数据库主机（通过 SSH 隧道访问）
DB_USR = "db_username"  # 数据库用户名
DB_PSW = "db_password"  # 数据库密码
DB_NAME = "database_name"  # 数据库名称
```

### 2. 认证方式

支持两种 SSH 认证方式：

#### 方式一：私钥认证（推荐）
- 设置 `SSH_PKEY_PATH` 为私钥文件路径
- 如果私钥有密码，设置 `SSH_PKEY_PASSPHRASE`

#### 方式二：密码认证
- 如果不使用私钥，设置环境变量：
  ```bash
  # Windows
  set SSH_PASSWORD=your_ssh_password
  
  # Linux/Mac
  export SSH_PASSWORD=your_ssh_password
  ```

### 3. 数据目录配置

默认 JSON 文件目录为 `D:/data2sql/json`，可在代码中修改 `JSON_ROOT_FOLDER` 常量：

```python
JSON_ROOT_FOLDER = 'your/json/directory'
```

## 数据库表结构

### DWARF_INFO 表

程序会向 `DWARF_INFO` 表插入数据，表结构如下：

```sql
CREATE TABLE DWARF_INFO (
    No INT PRIMARY KEY,
    func_name VARCHAR(255),
    start_addr VARCHAR(50),
    start_line INT,
    end_addr VARCHAR(50),
    end_line INT,
    _offset INT,
    decl_file VARCHAR(255),
    compiler VARCHAR(50),
    version VARCHAR(50),
    _optimize VARCHAR(50),
    if_padded INT,
    assembly_code LONGTEXT,
    src_code_frag LONGTEXT,
    route VARCHAR(255),
    Conf_pair_id INT,
    FOREIGN KEY (Conf_pair_id) REFERENCES Configuration(Conf_pair_id)
);
```

### Configuration 表

需要预先创建配置表，用于关联编译配置：

```sql
CREATE TABLE Configuration (
    Conf_pair_id INT PRIMARY KEY AUTO_INCREMENT,
    Compiler VARCHAR(50),
    Repo_version VARCHAR(50),
    Compile_config VARCHAR(50),
    Operation_System VARCHAR(20)
);
```

## JSON 文件格式

JSON 文件应包含以下字段：

```json
[
  {
    "func_name": "function_name",
    "start_addr": "0x1000",
    "start_line": 10,
    "end_addr": "0x2000",
    "end_line": 50,
    "offset": 100,
    "decl_file": "source.c",
    "compiler": "gcc",
    "version": "1.1.1",
    "optimize": "O2",
    "if_padded": 0,
    "assembly_code": "assembly instructions...",
    "src_code_frag": "source code fragment...",
    "route": "unique_route_identifier"
  }
]
```

### 文件路径命名规则

- 包含 `x86` 的路径识别为 x86 架构
- 包含 `x64` 的路径识别为 x64 架构
- 例如：`json/x64/gcc/data.json`

## 使用方法

### 基本用法

1. 确保配置文件正确设置
2. 将 JSON 文件放入指定目录
3. 运行程序：

```bash
python writesql.py
```

### 输出示例

```
2024-01-01 10:00:00 - INFO - SSH 隧道已启动，本地端口: 12345
2024-01-01 10:00:01 - INFO - 数据库连接成功
2024-01-01 10:00:02 - INFO - 找到 150 个 JSON 文件
2024-01-01 10:00:05 - INFO - 已加载 48 条配置缓存
扫描文件: 100%|████████████| 150/150 [00:10<00:00, 15.2it/s]
2024-01-01 10:00:15 - INFO - 总共需要处理 25000 条记录
插入数据: 100%|████████████| 25000/25000 [02:30<00:00, 166.7it/s]
2024-01-01 10:02:45 - INFO - 已插入 1000 条记录，累计: 1000
2024-01-01 10:05:20 - INFO - 数据插入完成，总计: 25000 条记录
2024-01-01 10:05:21 - INFO - 所有操作完成
```

## 性能优化

### 批量插入大小

默认批量大小为 1000 条，可根据网络和数据库性能调整：

```python
BATCH_SIZE = 1000  # 可调整为 500, 2000 等
```

### 性能建议

1. **网络延迟高**：减小批量大小（500-800）
2. **网络稳定快速**：增大批量大小（2000-5000）
3. **数据库性能较弱**：减小批量大小，避免超时

## 日志文件

程序运行时会生成 `writesql.log` 日志文件，记录：

- 连接状态
- 文件处理进度
- 错误和警告信息
- 详细的异常堆栈

查看日志：
```bash
tail -f writesql.log  # Linux/Mac
type writesql.log     # Windows
```

## 故障排查

### 常见问题

#### 1. SSH 连接失败
```
ValueError: 没有可用的 SSH 密钥或密码
```
**解决方法**：检查 `credits.py` 中的 SSH 配置，或设置 SSH_PASSWORD 环境变量

#### 2. 数据库连接失败
```
RuntimeError: 数据库连接失败
```
**解决方法**：
- 检查数据库凭据是否正确
- 确认数据库服务正在运行
- 验证 SSH 隧道是否成功建立

#### 3. 找不到配置
```
WARNING - 未找到配置: ('gcc', '1.1.1w', 'O2', 'x64')
```
**解决方法**：在 Configuration 表中添加对应的配置记录

#### 4. JSON 格式错误
```
ERROR - 数据格式错误，缺少字段 'func_name'
```
**解决方法**：检查 JSON 文件格式是否符合要求

## 注意事项

⚠️ **重要提示**：

1. 首次运行前确保数据库表结构已创建
2. Configuration 表需要预先填充配置数据
3. 确保 `route` 字段唯一，避免主键冲突
4. 大批量数据导入建议在非高峰期进行
5. 定期备份数据库，防止意外数据丢失
6. SSH 私钥文件权限应设置为 600（Linux/Mac）

## 版本历史

### v2.0 (2024-01-01)
- ✨ 重构代码结构，提高可维护性
- ✨ 添加配置缓存机制，大幅提升性能
- ✨ 集成 tqdm 进度条
- ✨ 使用 logging 替代 print
- ✨ 增强异常处理和资源管理

### v1.0
- 🎉 初始版本
- ✅ 基本的 JSON 导入功能

## 许可证

本项目仅供内部使用。

## 联系方式

如有问题或建议，请联系开发团队。
