import json
import os
import logging
from typing import List, Tuple
import warnings

from sshtunnel import SSHTunnelForwarder
import pymysql
from tqdm import tqdm

from credits import (
    SSH_HOST_PORT, SSH_USERNAME, SSH_PKEY_PATH, SSH_PKEY_PASSPHRASE,
    DB_HOST, DB_USR, DB_PSW, DB_NAME
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('writesql.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 抑制 cryptography 关于 Blowfish 的弃用警告  
warnings.filterwarnings('ignore', message='.*Blowfish has been deprecated.*')

# 常量配置
BATCH_SIZE = 1000
JSON_ROOT_FOLDER = '/home/user/Desktop/project/json'


def connect_to_database(ssh_host_port, ssh_username, ssh_pkey_path, remote_bind_address, db_user, db_password, db_name, ssh_pkey_passphrase):
    ssh_host, ssh_port = ssh_host_port.split(':')
    server = SSHTunnelForwarder(
    (ssh_host, int(ssh_port)),
    ssh_username=ssh_username,
    ssh_pkey=ssh_pkey_path,
    ssh_private_key_password=ssh_pkey_passphrase,
    remote_bind_address=remote_bind_address
    )
    server.start()
    db = pymysql.connect(host='127.0.0.1', port=server.local_bind_port, user=db_user, password=db_password, database=db_name)
    print("success")
    return db, server


def extract_json_files(root_folder: str) -> List[str]:
    """递归遍历文件夹，提取所有 JSON 文件路径"""
    json_files = []
    
    if not os.path.exists(root_folder):
        logger.error(f"指定的文件夹不存在: {root_folder}")
        return json_files
    
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith(".json"):
                file_path = os.path.join(dirpath, filename)
                json_files.append(file_path)
    
    logger.info(f"找到 {len(json_files)} 个 JSON 文件")
    return json_files


def get_conf_pair_id_cache(cursor) -> dict:
    """预先加载所有配置 ID，避免重复查询"""
    cache = {}
    sql = "SELECT Conf_pair_id, Compiler, Repo_version, Compile_config, Operation_System FROM Configuration"
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    for row in rows:
        key = (row[1], row[2], row[3], row[4])  # (compiler, version, optimize, os)
        cache[key] = row[0]
    
    logger.info(f"已加载 {len(cache)} 条配置缓存")
    return cache


def normalize_version(version: str) -> str:
    """标准化版本号"""
    if version == '1.1.1':
        return '1.1.1w'
    return version


def determine_operation_system(json_file_path: str) -> str:
    """根据文件路径判断操作系统架构"""
    if 'x86' in json_file_path.lower():
        return 'x86'
    elif 'x64' in json_file_path.lower():
        return 'x64'
    else:
        logger.warning(f"无法从路径判断架构: {json_file_path}，默认使用 x64")
        return 'x64'


def process_json_files(
    json_files: List[str],
    cursor,
    db,
    conf_cache: dict,
    batch_size: int = BATCH_SIZE
) -> None:
    """处理所有 JSON 文件并批量插入数据库"""
    insert_sql = """
        INSERT INTO DWARF_INFO (
            func_name, start_addr, start_line, end_addr, end_line,
            _offset, decl_file, compiler, version, _optimize, if_padded,
            assembly_code, src_code_frag, route, Conf_pair_id
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    
    buffer = []
    record_no = 1
    total_records = 0
    
    # 统计总记录数用于进度条
    logger.info("统计总记录数...")
    for json_file in tqdm(json_files, desc="扫描文件"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_records += len(data)
        except Exception as e:
            logger.error(f"读取文件失败 {json_file}: {e}")
    
    logger.info(f"总共需要处理 {total_records} 条记录")
    
    # 处理数据
    with tqdm(total=total_records, desc="插入数据") as pbar:
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"读取文件失败 {json_file}: {e}")
                continue
            
            operation_system = determine_operation_system(json_file)
            
            for item in data:
                try:
                    # 标准化版本号
                    version = normalize_version(item['version'])
                    
                    # 从缓存获取配置 ID
                    cache_key = (
                        item['compiler'],
                        version,
                        item['optimize'],
                        operation_system
                    )
                    
                    conf_pair_id = conf_cache.get(cache_key)
                    if conf_pair_id is None:
                        logger.warning(f"未找到配置: {cache_key}")
                        pbar.update(1)
                        continue
                    
                    # 构建记录
                    buffer.append((
                        item['func_name'],
                        item['start_addr'],
                        item['start_line'],
                        item['end_addr'],
                        item['end_line'],
                        item['offset'],
                        item['decl_file'],
                        item['compiler'],
                        version,
                        item['optimize'],
                        item['if_padded'],
                        item['assembly_code'],
                        item['src_code_frag'],
                        item['route'],
                        conf_pair_id
                    ))
                    
                    record_no += 1
                    pbar.update(1)
                    
                    # 批量插入
                    if len(buffer) >= batch_size:
                        cursor.executemany(insert_sql, buffer)
                        db.commit()
                        logger.info(f"已插入 {len(buffer)} 条记录，累计: {record_no - 1}")
                        buffer.clear()
                        
                except KeyError as e:
                    logger.error(f"数据格式错误，缺少字段 {e}: {json_file}")
                    pbar.update(1)
                except Exception as e:
                    logger.error(f"处理记录失败: {e}")
                    pbar.update(1)
    
    # 插入剩余数据
    if buffer:
        cursor.executemany(insert_sql, buffer)
        db.commit()
        logger.info(f"已插入最后 {len(buffer)} 条记录")
    
    logger.info(f"数据插入完成，总计: {record_no - 1} 条记录")


def main():
    """主函数"""
    db = None
    server = None
    
    try:
        # 连接数据库
        db, server = connect_to_database(
            ssh_host_port=SSH_HOST_PORT,
            ssh_username=SSH_USERNAME,
            ssh_pkey_path=SSH_PKEY_PATH,
            remote_bind_address=(DB_HOST, 3306),
            db_user=DB_USR,
            db_password=DB_PSW,
            db_name=DB_NAME,
            ssh_pkey_passphrase=SSH_PKEY_PASSPHRASE
        )
        
        cursor = db.cursor()
        
        # 提取 JSON 文件列表
        json_files = extract_json_files(JSON_ROOT_FOLDER)
        if not json_files:
            logger.warning("没有找到 JSON 文件")
            return
        
        # 预加载配置缓存
        conf_cache = get_conf_pair_id_cache(cursor)
        
        # 处理数据
        process_json_files(json_files, cursor, db, conf_cache, BATCH_SIZE)
        
        logger.info("所有操作完成")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        
    finally:
        # 清理资源
        if db:
            try:
                db.close()
                logger.info("数据库连接已关闭")
            except Exception:
                pass
        
        if server:
            try:
                server.stop()
                logger.info("SSH 隧道已停止")
            except Exception:
                pass


if __name__ == "__main__":
    main()
