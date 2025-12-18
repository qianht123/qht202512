import sys
import os
import re
import gdspy

def parse_qht10_netlist(filename):
    devices = []

    with open(filename, 'r') as f:
        content = f.read()

    mos_pattern = r'M(\d+)\s*\(([^)]+)\)\s+(\w+)\s+l=([\d.]+)n\s+w=([\d.]+)n\s+m=([\d.]+)\s+nf=([\d.]+)'
    matches = re.findall(mos_pattern, content)

    for match in matches:
        name, pins, device_type, l, w, m, nf = match
        pins_list = [p.strip() for p in pins.split()]

        device = {
            'name': f'M{name}',
            'type': device_type,
            'is_nmos': 'nch' in device_type,
            'l': float(l) * 1e-9,
            'w': float(w) * 1e-9,
            'nf': int(nf),
            'pins': pins_list
        }
        devices.append(device)

    return devices

def main():
    input_file = '/install/MAGICAL/qht_chuli_jianlishili/qht10.sp'
    output_dir = '/install/MAGICAL/qht_chuli_jianlishili/zhongjiangds'

    print('=== qht10.sp 网表处理流程 ===')

    print('\n1. 解析网表文件...')
    devices = parse_qht10_netlist(input_file)
    print('找到 ' + str(len(devices)) + ' 个器件')

    for device in devices:
        print('  ' + device['name'] + ': ' + device['type'] + ', l=' + str(device['l']*1e9) + 'n, w=' + str(device['w']*1e9) + 'n, nf=' + str(device['nf']))

    print('\n2. 生成器件版图...')
    try:
        from mosfet import Mosfet

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        for device in devices:
            print('\n=== 生成器件: ' + device['name'] + ' ===')
            print('类型: ' + device['type'])
            print('尺寸: l=' + str(device['l']*1e9) + 'n, w=' + str(device['w']*1e9) + 'n')
            print('指数: nf=' + str(device['nf']))

            # 创建独立的GDS库
            lib = gdspy.GdsLibrary(unit=1e-6, precision=1e-9)
            
            # 创建Mosfet实例
            mosfet = Mosfet(device['is_nmos'], device['name'], device['w'], device['l'], device['nf'])

            # 创建单元并添加到库
            cell = gdspy.Cell(device['name'])
            for polygon in mosfet.cell.polygons:
                cell.add(polygon)
            for reference in mosfet.cell.references:
                cell.add(reference)
            
            lib.add(cell)

            # 为每个器件生成独立的GDS文件
            output_file = os.path.join(output_dir, device['name'] + '.gds')
            lib.write_gds(output_file)
            
            print('版图已保存到: ' + output_file)

            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print('文件大小: ' + str(file_size) + ' bytes')

        print('\n=== 处理完成 ===')
        print('所有GDS文件已保存到: ' + output_dir)
        
        # 列出生成的文件
        print('\n生成的文件:')
        for filename in os.listdir(output_dir):
            if filename.endswith('.gds'):
                filepath = os.path.join(output_dir, filename)
                file_size = os.path.getsize(filepath)
                print('  ' + filename + ': ' + str(file_size) + ' bytes')
        
        return 0

    except Exception as e:
        print('生成版图时出错: ' + str(e))
        import traceback
        traceback.print_exc()
        return 1

sys.exit(main())
