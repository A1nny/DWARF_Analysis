#!/home/user/Desktop/myenv/bin/env python3

from elftools.elf.elffile import ELFFile
from elftools.dwarf.descriptions import describe_DWARF_expr
import subprocess
import json
import sys
import logging
import os
from tqdm import tqdm
from sshtunnel import SSHTunnelForwarder
import pymysql
from credits import (
    SSH_HOST_PORT, SSH_USERNAME, SSH_PKEY_PATH, SSH_PKEY_PASSPHRASE,
    DB_HOST, DB_USR, DB_PSW, DB_NAME
)
function_list=[]
# compiler='gcc'
# version='1.1.1'
# optimize='O3'
input_directory=sys.argv[1]
output_file_path=sys.argv[2]
compiler=sys.argv[3]
version=sys.argv[4]
optimize=sys.argv[5]
operating_system=sys.argv[6]
VoC=sys.argv[7]
# compiler,version,optimize,operating_system,compiler_version='MinGW-w64','3.0.17', 'O0', 'x64','13.3.0'
# input_directory=f'/home/ainny/Desktop/project/{operating_system}/g3,{optimize}/{version}/{compiler}/all'
# output_file_path=f'/home/ainny/Desktop/project/json/{operating_system} (json)/g3,{optimize}/{compiler}{version}.json'


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('writesql.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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


def extract_assembly_with_objdump(binary_path, start_address, end_address):

    # start = int(start_address, 16)
    # end = int(end_address, 16)
    # length = end - start
    
    cmd = [
        "objdump",
        "-d",  # 反汇编
        "--start-address", start_address,
        "--stop-address", end_address,
        binary_path
    ]
    
    try:
        # 执行命令并捕获输出
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def extract_line_numbers(obj_file):
    """提取行号表信息（需要编译时带 -g 选项）"""
    cmd = ['x86_64-w64-mingw32-objdump', '--dwarf=decodedline', obj_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Error running objdump:", result.stderr)
        return []
    
    line_entries = []
    # 状态机跟踪当前文件名
    current_file = None
    # print(result)
    for line in result.stdout.splitlines():
        # print(line)
        # 检测文件行: "CU: /path/to/file.c:"
        if line.startswith("CU:"):
            current_file = line.split(':', 1)[1].strip(': ').strip()
            continue
        
        # 检测行号条目: "0x0000000000000010      5       /path/to/file.c"
        parts = line.split()
        if len(parts) >= 3 and (parts[2].startswith('0x') or parts[2]=='0'):
            try:
                address = parts[2]
                line_num = int(parts[1])
                # 如果当前文件已设置，优先使用
                file_path = current_file if current_file else ''.join(parts[0])
                # print(obj_file)
                line_entries.append({
                    'address': address,
                    'line': line_num,
                    'file': file_path
                })
            except (ValueError, IndexError):
                continue
    
    return line_entries


def extract_code(mapping_list,current_func):
    start_addr=current_func['start_addr']
    end_addr=current_func['end_addr']
    # print(f"0x{start_addr:08x}")
    # print(f"0x{end_addr:08x}")
    last_addr=0
    pad_tag=1
    line=0
    for line_entry in mapping_list:
        add=int(line_entry['address'],16)
        if start_addr<=add<end_addr:
            if add==start_addr:
                start_line=line_entry['line']
            if last_addr==0 or add>last_addr:
                last_addr=add
                end_line=max(line,line_entry['line'])
                line=end_line
            
    # print(current_func['decl_file'])
    with open(current_func['decl_file'], 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        # 调整行号索引
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        
        # 提取代码片段
        code=''.join(lines[start_idx:end_idx])
        if lines[end_idx-1]=='}\n':
            pad_tag=0
    return start_line, end_line, code,pad_tag

def extract_rawline_info(file_path):
    cmd = ['x86_64-w64-mingw32-objdump', '--dwarf=rawline', file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # print(result)
    output=result.stdout
    DT=[]
    FNT=[]
    EDN={}
    DT_log=0
    FNT_log=0
    for line in output.splitlines():
        # print(line)
        if DT_log and 'Entry\tName' not in line:
            if line=='':
                DT_log=0
                continue
            parts = line.split(':')
            DT.append(parts[-1].strip())
            # print(type(parts[-1]))
            
        if "The Directory Table" in line:
            DT_log=1

        if FNT_log and 'Entry\tDir' not in line:
            if line=='':
                FNT_log=0
                continue
            
            parts = line.split('\t')
            entry=parts[0].strip()
            name_idx=parts[1].split(' ')[0]
            name=parts[-1].split(':')[-1].strip()
            # print(name_idx,name)
            EDN={'name':name,'idx':name_idx}
            FNT.append(EDN)
            # print(FNT)
        if "The File Name Table" in line:
            FNT_log=1
    return DT,FNT

def parse_dwarfdump_output(file_path):
    """解析 llvm-dwarfdump 文本输出"""
    mapping_list=extract_line_numbers(file_path)
    DT,FNT=extract_rawline_info(file_path)
    # print(FNT[0]['name'])
    # print(DT)
    cmd = ['x86_64-w64-mingw32-objdump', '--dwarf=info', file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # print(result)
    output=result.stdout
    current_func = {}
    
    num=1
    route=''
    src_code_route='' 
    src_code_name=''
    for line in output.splitlines():
        # print(line)
        if src_code_route and src_code_name:
            route=src_code_route+'/'+src_code_name
            comp_info_tag=0
        if 'DW_TAG_compile_unit' in line:
            comp_info_tag=1
        if 'DW_TAG_subprogram' in line:
            comp_info_tag=0
            if current_func and current_func['func_name']!='' and current_func['start_addr']!=-1 and current_func['end_addr']!=-1 and current_func['decl_file']!='':
                
                bicode=extract_assembly_with_objdump(file_path, str(current_func['start_addr']), str(current_func['end_addr']))
                start_line, end_line, code,pad_tag=extract_code(mapping_list,current_func)
                current_func['start_line']=start_line
                current_func['end_line']=end_line
                current_func['src_code_frag']=code
                current_func['if_padded']=pad_tag
                current_func['offset']=current_func['end_addr']-current_func['start_addr']
                current_func['assembly_code']=bicode
                current_func['start_addr']=f"0x{current_func['start_addr']:08x}"
                current_func['end_addr']=f"0x{current_func['end_addr']:08x}"
                current_func['route']=route
                print(current_func['func_name'])
                function_list.append(current_func)
                # print(bicode)
            current_func = {
                'func_name': '', 
                'start_addr': -1,
                'start_line':-1,
                'end_addr': -1,
                'end_line':-1,
                'offset':0,
                'decl_file': '',
                'compiler':compiler,
                'version':version,
                'optimize':optimize,
                'VoC':VoC,    
                'if_padded':-1,
                'assembly_code':'',
                'src_code_frag':'',
                'route':''        
            }
        
        if 'DW_AT_comp_dir' in line:
            if comp_info_tag==1:
                parts = line.split(':')
                if len(parts) > 1:
                    src_code_route = parts[-1].strip().strip('()').strip('"')

        if 'DW_AT_name' in line:
            if comp_info_tag==1:
                parts = line.split(':')
                if len(parts) > 1:
                    src_code_name = parts[-1].strip().strip('()').strip('"')
            elif current_func and current_func['func_name']=='':
                parts = line.split(':')
                if len(parts) > 1:
                    current_func['func_name'] = parts[-1].strip().strip('()').strip('"')
        
        if 'DW_AT_decl_file' in line:
            if current_func and current_func['decl_file']=='':
                parts = line.split(':')
                if len(parts) > 1:
                    decl_file_index = int(parts[-1].strip().strip('()'))
                    if DT[int(FNT[decl_file_index]['idx'])].startswith('/'):
                        file_entry = DT[int(FNT[decl_file_index]['idx'])]
                        file_name = FNT[decl_file_index]['name']
                        dir_path=os.path.join(file_entry,file_name)
                        current_func['decl_file']=dir_path
                    else:
                        base=DT[0]
                        relative=DT[int(FNT[decl_file_index]['idx'])]
                        file_entry=os.path.join(base,relative)
                        file_name=FNT[decl_file_index]['name']
                        dir_path=os.path.join(file_entry,file_name)
                        current_func['decl_file']=dir_path
        
        
        if 'DW_AT_low_pc' in line:
            if current_func and current_func['start_addr']==-1:
                parts = line.split()
                if len(parts) > 1:
                    
                    current_func['start_addr'] = int(parts[-1].strip().strip('()'), 16)
        
        if 'DW_AT_high_pc' in line:

            if current_func and current_func['end_addr']==-1:
                parts = line.split()
                if len(parts) > 1:
                    current_func['end_addr'] = current_func['start_addr'] + int(parts[-1].strip().strip('()'), 16)

    if current_func and current_func['func_name']!='' and current_func['start_addr']!=-1 and current_func['end_addr']!=-1 and current_func['decl_file']!='':
        bicode=extract_assembly_with_objdump(file_path, str(current_func['start_addr']), str(current_func['end_addr']))
        start_line, end_line, code,pad_tag=extract_code(mapping_list,current_func)
        current_func['start_line']=start_line
        current_func['end_line']=end_line
        current_func['src_code_frag']=code
        current_func['if_padded']=pad_tag
        current_func['offset']=current_func['end_addr']-current_func['start_addr']
        current_func['assembly_code']=bicode
        current_func['start_addr']=f"0x{current_func['start_addr']:08x}"
        current_func['end_addr']=f"0x{current_func['end_addr']:08x}"
        function_list.append(current_func)
        print(current_func['func_name'])
    
BATCH_SIZE = 1000
def get_conf_pair_id_cache(cursor) -> dict:
    """预先加载所有配置 ID，避免重复查询"""
    cache = {}
    sql = "SELECT Conf_pair_id, Compiler, Repo_version, Compile_config, Operation_System, Compiler_Version FROM Configuration"
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    for row in rows:
        key = (row[1], row[2], row[3], row[4],row[5])  # (compiler, version, optimize, os,version of compiler)
        cache[key] = row[0]
    
    logger.info(f"已加载 {len(cache)} 条配置缓存")
    return cache


def normalize_VoC(VoC):
    """标准化版本号"""
    if VoC == 'gcc10':
        return '10.5.0'
    elif VoC == 'gcc12':
        return '12.4.0'
    elif VoC == 'gcc13':
        return '13.3.0'
    elif VoC == 'gcc14':
        return '14.2.0'
    elif VoC == 'clang14':
        return '14.0.6'
    elif VoC == 'clang16':
        return '16.0.6'
    elif VoC == 'clang18':
        return '18.1.3'
    
    return VoC

def normalize_version(version: str) -> str:
    """标准化版本号"""
    if version == '1.1.1':
        return '1.1.1w'
    return version
    
def process_data(
    cursor,
    db,
    conf_cache: dict,
    batch_size: int = BATCH_SIZE
) -> None:
    """处理所有 JSON 文件并批量插入数据库"""
    insert_sql = """
        INSERT INTO INFO (
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
    data = function_list
    try:
        total_records = len(data)
    except Exception as e:
        logger.error(f"读取失败: {e}")
    
    logger.info(f"总共需要处理 {total_records} 条记录")
    
    # 处理数据
    with tqdm(total=total_records, desc="插入数据") as pbar:
        Operating_System = operating_system
        for item in data:
            try:
                # 标准化版本号
                version = normalize_version(item['version'])
                Compiler_Version = normalize_VoC(VoC)
                # 从缓存获取配置 ID
                cache_key = (
                    item['compiler'],
                    version,
                    item['optimize'],
                    Operating_System,
                    Compiler_Version
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
                logger.error(f"数据格式错误，缺少字段 {e}:")
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
    # for root, dirs, files in os.walk(f"/home/ainny/Desktop/project/x64/g3,{optimize}/{version}/{compiler}/all"):
    #     for file in files:
    #         if file.endswith('.o') or file.endswith('.obj'):
                
    #             file_path=os.path.join(root,file)
    #             # file_path="/home/ainny/Desktop/project/x86/g3,O2/1.1.1/gcc/all/sm3.o"
    #             # print(file_path)
                    
    #             parse_dwarfdump_output(file_path)
    #         # break
    
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.endswith('.o') or file.endswith('.obj'):
                file_path=os.path.join(root,file)
                # print(file_path)
                parse_dwarfdump_output(file_path)
    db = None
    server = None
    with open(output_file_path,'w') as file:
        json.dump(function_list, file, ensure_ascii=False, indent=2)
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


        
        # 预加载配置缓存
        conf_cache = get_conf_pair_id_cache(cursor)
        
        # 处理数据
        process_data(cursor, db, conf_cache, BATCH_SIZE)
        
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




