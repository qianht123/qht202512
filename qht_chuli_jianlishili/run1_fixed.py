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
    output_file = '/tmp/qht10_layout.gds'

    print('=== qht10.sp 网表处理流程 ===')

    print('\n1. 解析网表文件...')
    devices = parse_qht10_netlist(input_file)
    print(f'找到 {len(devices)} 个器件')

    for device in devices:
        print(f'  {device["name"]}: {device["type"]}, l={device["l"]*1e9}n, w={device["w"]*1e9}n, nf={device["nf"]}')

    print('\n2. 生成器件版图...')
    try:
        from mosfet import Mosfet

        lib = gdspy.GdsLibrary()

        for device in devices:
            print(f'\n=== 生成器件: {device["name"]} ===')
            print(f'类型: {device["type"]}')
            print(f'尺寸: l={device["l"]*1e9}n, w={device["w"]*1e9}n')
            print(f'指数: nf={device["nf"]}')

            mosfet = Mosfet(device['is_nmos'], device['name'], device['w'], device['l'], device['nf'])

            cell = gdspy.Cell(device['name'])
            for polygon in mosfet.cell.polygons:
                cell.add(polygon)
            for reference in mosfet.cell.references:
                cell.add(reference)

            lib.add(cell)

        lib.write_gds(output_file)
        print(f'\n版图已保存到: {output_file}')

        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f'文件大小: {file_size} bytes')

        print('\n=== 处理完成 ===')
        return 0

    except Exception as e:
        print(f'生成版图时出错: {e}')
        return 1

sys.exit(main())