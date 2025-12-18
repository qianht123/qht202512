#!/usr/bin/env python3
"""
qht10.sp网表处理脚本 - 基于mos_yuan和basic_yuan的完整版本
"""

import sys
import os
import re
import gdspy

# 添加mosfet模块路径
sys.path.append('/install/MAGICAL/qht_chuli_jianlishili/mosfet')

def parse_qht10_netlist(filename):
    """解析qht10.sp网表文件"""
    devices = []
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # 提取MOSFET器件信息
    mos_pattern = r'M(\d+)\s*\(([^)]+)\)\s+(\w+)\s+l=([\d.]+)n\s+w=([\d.]+)n\s+m=([\d.]+)\s+nf=([\d.]+)'
    matches = re.findall(mos_pattern, content)
    
    for match in matches:
        name, pins, device_type, l, w, m, nf = match
        pins_list = [p.strip() for p in pins.split()]
        
        device = {
            'name': f'M{name}',
            'type': device_type,
            'is_nmos': 'nch' in device_type,
            'l': float(l) * 1e-9,  # 转换为米
            'w': float(w) * 1e-9,  # 转换为米
            'nf': int(nf),
            'pins': pins_list
        }
        devices.append(device)
    
    return devices

def generate_layout(devices, output_file):
    """生成器件版图"""
    try:
        from mos import Mosfet
        
        # 创建GDS库
        lib = gdspy.GdsLibrary()
        
        for device in devices:
            print(f"
=== 生成器件: {device['name']} ===")
            print(f"类型: {device['type']}")
            print(f"尺寸: l={device['l']*1e9}n, w={device['w']*1e9}n")
            print(f"指数: nf={device['nf']}")
            
            # 创建MOSFET器件
            mosfet = Mosfet(
                device['is_nmos'], 
                device['name'], 
                device['w'], 
                device['l'], 
                device['nf']
            )
            
            # 创建GDS单元
            cell = gdspy.Cell(device['name'])
            for polygon in mosfet.cell.polygons:
                cell.add(polygon)
            for reference in mosfet.cell.references:
                cell.add(reference)
            
            lib.add(cell)
        
        # 写入GDS文件
        lib.write_gds(output_file)
        print(f"
版图已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"生成版图时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    input_file = '/install/MAGICAL/qht_chuli_jianlishili/qht10.sp'
    output_file = '/tmp/qht10_layout_fixed.gds'
    
    print("=== qht10.sp 网表处理流程 ===")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    
    # 1. 解析网表
    print("
1. 解析网表文件...")
    devices = parse_qht10_netlist(input_file)
    print(f"找到 {len(devices)} 个器件")
    
    for device in devices:
        print(f"  {device['name']}: {device['type']}, l={device['l']*1e9}n, w={device['w']*1e9}n, nf={device['nf']}")
    
    # 2. 生成版图
    print("
2. 生成器件版图...")
    success = generate_layout(devices, output_file)
    
    if success:
        print("
=== 处理完成 ===")
        print(f"成功生成版图文件: {output_file}")
        
        # 检查输出文件
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"文件大小: {file_size} bytes")
        return 0
    else:
        print("
=== 处理失败 ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())
