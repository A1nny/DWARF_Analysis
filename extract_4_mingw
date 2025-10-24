from elftools.elf.elffile import ELFFile
from elftools.dwarf.descriptions import describe_DWARF_expr
import subprocess
import json
import os
function_list=[]
# path="/home/ainny/Desktop/project/g3,O2/1.1.1/mingw64/all/sm4.o"
compiler='MinGW-w64'
version='3.0.17'
optimize='O3'
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






def parse_dwarfdump_output(file_path,data):
    """解析 llvm-dwarfdump 文本输出"""
    mapping_list=extract_line_numbers(file_path)

    # print(mapping_list)


    result = subprocess.check_output(['llvm-dwarfdump', '--debug-info', '-'], input=data)
    output=result.decode()
    current_func = {}
    # print(len(output.splitlines()))
    num=1
    for line in output.splitlines():
        # print(line)
        if 'DW_TAG_subprogram' in line:
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
                'if_padded':-1,
                'assembly_code':'',
                'src_code_frag':'',
                'route':''        
            }
        
        if 'DW_AT_name' in line:
            if current_func and current_func['func_name']=='':
                parts = line.split('DW_AT_name')
                if len(parts) > 1:
                    current_func['func_name'] = parts[1].strip().strip('()').strip('"')
        
        if 'DW_AT_decl_file' in line:
            if current_func and current_func['decl_file']=='':
                parts = line.split()
                if len(parts) > 1:
                    current_func['decl_file'] = parts[-1].strip().strip('()').strip('"')
                    
                    current_func['route'] = parts[-1].strip().strip('()').strip('"')
        
        
        if 'DW_AT_low_pc' in line:
            if current_func and current_func['start_addr']==-1:
                parts = line.split()
                if len(parts) > 1:
                    
                    current_func['start_addr'] = int(parts[-1].strip().strip('()'), 16)
        
        if 'DW_AT_high_pc' in line:
            if current_func and current_func['end_addr']==-1:
                parts = line.split()
                if len(parts) > 1:
                    current_func['end_addr'] = int(parts[-1].strip().strip('()'), 16)

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
    # print(function_list)
    


    


for root, dirs, files in os.walk(f"/home/ainny/Desktop/project/g3,{optimize}/{version}/{compiler}/all"):
    for file in files:
        if file.endswith('.o') or file.endswith('.obj'):
            # file_path="/home/ainny/Desktop/project/libcrypto-lib-x509_att.obj"
            file_path=os.path.join(root,file)
            # print(file_path)
            with open(file_path, 'rb') as f:
                f.seek(0)
                # print(f.read())
                
                parse_dwarfdump_output(file_path,f.read())
        
    
with open(f'{compiler}{version}.json','w') as file:
    json.dump(function_list, file, ensure_ascii=False, indent=2)


# '/home/ainny/Desktop/project/g3,O2/1.1.1/MinGW-w64/all/dh_prn.o'





