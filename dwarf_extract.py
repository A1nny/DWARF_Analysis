from elftools.elf.elffile import ELFFile
from elftools.dwarf.descriptions import describe_DWARF_expr
import sys
import os
import json
import subprocess
function_list=[]
# input_directory = sys.argv[1]
# output_file_path = sys.argv[2]
# version=sys.argv[4]
# compiler=sys.argv[3]

compiler='mingw64'
version='1.1.1'
optimize='O2'


def extract_assembly_with_objdump(binary_path, start_address, end_address):
    start = int(start_address, 16)
    end = int(end_address, 16)
    length = end - start
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


def process_subprogram(DIE,line_program,comp_dir,file_path):
    
    file_entries = line_program['file_entry'] if line_program else []
    
    name_attr=DIE.attributes.get('DW_AT_name', None)
    low_pc_attr=DIE.attributes.get('DW_AT_low_pc', None)
    high_pc_attr=DIE.attributes.get('DW_AT_high_pc', None)
    decl_file_attr=DIE.attributes.get('DW_AT_decl_file', None)
#get name, start_addr end_addr
    if not all([name_attr, low_pc_attr, high_pc_attr]):  #filter the information w/o line message
        return 
    name = name_attr.value.decode('utf-8') if name_attr else '<unknown>'
    low_pc = low_pc_attr.value
    high_pc = high_pc_attr.value
    start_addr = low_pc
    end_addr = low_pc + high_pc
#file_name_get
    decl_file_index = decl_file_attr.value if decl_file_attr else None
    file_name = f"Unknown file ({decl_file_index})"
    if decl_file_index and line_program and 0 < decl_file_index <= len(file_entries):
        file_entry = file_entries[decl_file_index - 1]
        file_name = file_entry.name.decode('utf-8')
    else:
        file_entry = file_entries[decl_file_index]
        file_name = file_entry.name.decode('utf-8')
#code_line_get
    last_addr=0
    pad_tag=1
    for entry in line_programs[CU].get_entries():
        if entry.state is None:
            continue
        if start_addr <= entry.state.address <= end_addr: #entry.state.address means the virtual address in the Mapping Table
            if entry.state.address==start_addr:
                start_line=entry.state.line  #entry.state.line means the real line from src-code in the Mapping Table
            if last_addr==0 or entry.state.address > last_addr:
                last_addr = entry.state.address
                end_line=entry.state.line
            if end_addr==entry.state.address:
                pad_tag=0
            

#code_get
    if hasattr(file_entry, 'dir_index') and file_entry.dir_index >=0:
        
        if hasattr(line_program.header, 'include_directory'):
            include_dirs = line_program.header.include_directory
            
            if 0 <= file_entry.dir_index <= len(include_dirs):
                # 获取目录路径
                
                dir_path = include_dirs[file_entry.dir_index].decode('utf-8')
                # print(dir_path)
    code_path=os.path.join(comp_dir,dir_path,file_name)
    # print(name)
    with open(code_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        # 调整行号索引
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        
        # 提取代码片段
        code=''.join(lines[start_idx:end_idx])
        # print(code)

    assembly_code = extract_assembly_with_objdump(file_path, str(start_addr), str(end_addr))
    func_info = {
        'func_name': name,
        'start_addr': f"0x{start_addr:08x}",
        'start_line':start_line,
        'end_addr': f"0x{end_addr:08x}",
        'end_line':end_line,
        'offset':end_addr-start_addr,
        'decl_file': file_name,
        'compiler':compiler,
        'version':version,
        'optimize':optimize,    #whether linked (in this code this line can't be operated)
        'if_padded':pad_tag,
        'assembly_code':assembly_code,
        'src_code_frag':code,
        'route':f"{code_path}/{name}"
    }
    return func_info

    

# 1. 打开 ELF 文件
for root, dirs, files in os.walk(f"/home/ainny/Desktop/project/g3,{optimize}/{version}/{compiler}/all"):
        for file in files:
            if file.endswith('.o'):
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    # print(f)
                    # 2. 创建 ELFFile 对象
                    elffile = ELFFile(f)
                    # 3. 检查文件是否有 DWARF 信息
                    if not elffile.has_dwarf_info():
                        print('File has no DWARF info')
                        continue
                    
                    # 4. 获取 dwarfinfo 对象！
                    dwarfinfo = elffile.get_dwarf_info()


                    line_programs = {}
                    for CU in dwarfinfo.iter_CUs():
                        line_programs[CU] = dwarfinfo.line_program_for_CU(CU)
                    # for entry in line_programs[CU].get_entries():
                    #     if entry.state is None:
                    #         continue
                    #     print(f"0x{entry.state.address:08x}==>{entry.state.line}")
                        # print(entry)
                    for CU in dwarfinfo.iter_CUs():
                        top_die = CU.get_top_DIE()
                        comp_dir_attr = top_die.attributes.get('DW_AT_comp_dir', None)
                        comp_dir = comp_dir_attr.value.decode('utf-8') if comp_dir_attr else ''
                        die_count=0
                        for DIE in CU.iter_DIEs():
                            
                            if DIE.tag=='DW_TAG_subprogram':
                                die_count+=1
                                if DIE.attributes.get('DW_AT_inline',None)!=None and DIE.attributes.get('DW_AT_inline',None).value!=0:
                                    continue
                                # print(DIE)
                                line_program=line_programs[CU]
                                if process_subprogram(DIE,line_program,comp_dir,file_path):
                                    func_info=process_subprogram(DIE,line_program,comp_dir,file_path)
                                    print(func_info['func_name'])
                                    # print(func_info['src_code_frag'])
                                    function_list.append(func_info)
                # print(len(function_list))
                # break 


            with open(f'{compiler}{version}.json','w') as file:
                json.dump(function_list, file, ensure_ascii=False, indent=2)



