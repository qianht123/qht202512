#!/usr/bin/env python3
"""
测试qht10.sp的可视化解析
"""

import sys
sys.path.insert(0, '/home/icdesign/qianhtical1215')

from magical_flow.parser.netlist import SpectreParser

def test_qht10_visualization():
    """测试qht10.sp的可视化解析"""
    print("🔍 解析qht10.sp文件...")
    
    # 创建解析器
    parser = SpectreParser()
    
    # 解析文件
    circuit = parser.parse("/home/icdesign/qianhtical1215/qht10.sp")
    
    # 额外的分析信息
    print("\n📈 ADDITIONAL ANALYSIS")
    print("-" * 40)
    
    # 分析器件尺寸分布
    widths = []
    lengths = []
    for device in circuit.devices.values():
        if 'w' in device.parameters:
            try:
                w = float(device.parameters['w'].replace('n', '')) * 1e-9  # 转换为米
                widths.append(w)
            except:
                pass
        if 'l' in device.parameters:
            try:
                l = float(device.parameters['l'].replace('n', '')) * 1e-9  # 转换为米
                lengths.append(l)
            except:
                pass
    
    if widths:
        print(f"Width range: {min(widths)*1e9:.1f}n - {max(widths)*1e9:.1f}n")
    if lengths:
        print(f"Length: {lengths[0]*1e9:.1f}n (all devices have same length)")
    
    # 分析网络复杂度
    net_complexity = []
    for net in circuit.nets.values():
        net_complexity.append(len(net.pins))
    
    if net_complexity:
        print(f"Net connection range: {min(net_complexity)} - {max(net_complexity)} pins")
        highly_connected = [net.name for net in circuit.nets.values() if len(net.pins) >= 4]
        if highly_connected:
            print(f"Highly connected nets: {', '.join(highly_connected)}")
    
    # 分析对称性
    print(f"\n🔄 SYMMETRY ANALYSIS")
    print("-" * 40)
    
    # 查找差分对
    diff_pairs = []
    for net_name in circuit.nets:
        if 'ain' in net_name.lower() or 'bin' in net_name.lower():
            if 'ain' in net_name.lower():
                counterpart = net_name.replace('ain', 'bin', 1)
            else:
                counterpart = net_name.replace('bin', 'ain', 1)
            if counterpart in circuit.nets:
                diff_pairs.append((net_name, counterpart))
    
    if diff_pairs:
        print("Differential pairs detected:")
        for net1, net2 in diff_pairs:
            print(f"  {net1} ↔ {net2}")
    else:
        print("No obvious differential pairs found")
    
    return circuit

if __name__ == "__main__":
    circuit = test_qht10_visualization()