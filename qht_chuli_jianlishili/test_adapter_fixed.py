#!/usr/bin/env python3
"""
简化的CircuitAdapter测试脚本 - 修正版
"""

import sys
import os
sys.path.append("/install/MAGICAL/qht_chuli_jianlishili")

from core.circuit import Circuit, Device, Net, Pin, DeviceType, NetType, PinDirection
from buju.adapters.circuit_adapter import CircuitAdapter

def create_test_circuit():
    """创建一个测试电路"""
    circuit = Circuit(name="test_circuit")
    
    # 创建网络
    vdd_net = Net(name="VDD", net_type=NetType.POWER)
    vss_net = Net(name="VSS", net_type=NetType.GROUND)
    vin_net = Net(name="VIN", net_type=NetType.SIGNAL)
    vout_net = Net(name="VOUT", net_type=NetType.SIGNAL)
    bias_net = Net(name="BIAS", net_type=NetType.SIGNAL)
    
    circuit.add_net(vdd_net)
    circuit.add_net(vss_net)
    circuit.add_net(vin_net)
    circuit.add_net(vout_net)
    circuit.add_net(bias_net)
    
    # 创建器件
    # M1: NMOS输入管
    m1 = Device(name="M1", device_type=DeviceType.NMOS)
    m1.parameters = {"w": 10.0, "l": 0.18, "nf": 2}
    
    # M2: NMOS输入管（与M1对称）
    m2 = Device(name="M2", device_type=DeviceType.NMOS)
    m2.parameters = {"w": 10.0, "l": 0.18, "nf": 2}
    
    # M3: PMOS负载管
    m3 = Device(name="M3", device_type=DeviceType.PMOS)
    m3.parameters = {"w": 20.0, "l": 0.18, "nf": 1}
    
    # M4: PMOS负载管（与M3对称）
    m4 = Device(name="M4", device_type=DeviceType.PMOS)
    m4.parameters = {"w": 20.0, "l": 0.18, "nf": 1}
    
    # 创建引脚并连接网络
    # M1引脚
    m1_g = Pin(name="G", device=m1, net=vin_net, direction=PinDirection.INPUT)
    m1_d = Pin(name="D", device=m1, net=vout_net, direction=PinDirection.OUTPUT)
    m1_s = Pin(name="S", device=m1, net=vss_net, direction=PinDirection.INPUT)
    m1_b = Pin(name="B", device=m1, net=vss_net, direction=PinDirection.INPUT)
    
    # M2引脚
    m2_g = Pin(name="G", device=m2, net=vin_net, direction=PinDirection.INPUT)
    m2_d = Pin(name="D", device=m2, net=vout_net, direction=PinDirection.OUTPUT)
    m2_s = Pin(name="S", device=m2, net=vss_net, direction=PinDirection.INPUT)
    m2_b = Pin(name="B", device=m2, net=vss_net, direction=PinDirection.INPUT)
    
    # M3引脚
    m3_g = Pin(name="G", device=m3, net=bias_net, direction=PinDirection.INPUT)
    m3_d = Pin(name="D", device=m3, net=vout_net, direction=PinDirection.OUTPUT)
    m3_s = Pin(name="S", device=m3, net=vdd_net, direction=PinDirection.INPUT)
    m3_b = Pin(name="B", device=m3, net=vdd_net, direction=PinDirection.INPUT)
    
    # M4引脚
    m4_g = Pin(name="G", device=m4, net=bias_net, direction=PinDirection.INPUT)
    m4_d = Pin(name="D", device=m4, net=vout_net, direction=PinDirection.OUTPUT)
    m4_s = Pin(name="S", device=m4, net=vdd_net, direction=PinDirection.INPUT)
    m4_b = Pin(name="B", device=m4, net=vdd_net, direction=PinDirection.INPUT)
    
    # 添加引脚到器件
    m1.pins = [m1_g, m1_d, m1_s, m1_b]
    m2.pins = [m2_g, m2_d, m2_s, m2_b]
    m3.pins = [m3_g, m3_d, m3_s, m3_b]
    m4.pins = [m4_g, m4_d, m4_s, m4_b]
    
    # 添加器件到电路
    circuit.add_device(m1)
    circuit.add_device(m2)
    circuit.add_device(m3)
    circuit.add_device(m4)
    
    # 建立网络到引脚的连接
    vdd_net.pins = [m3_s, m3_b, m4_s, m4_b]
    vss_net.pins = [m1_s, m1_b, m2_s, m2_b]
    vin_net.pins = [m1_g, m2_g]
    vout_net.pins = [m1_d, m2_d, m3_d, m4_d]
    bias_net.pins = [m3_g, m4_g]
    
    return circuit

def test_adapter():
    """测试适配器功能"""
    print("=" * 60)
    print("测试CircuitAdapter转换功能")
    print("=" * 60)
    
    # 创建测试电路
    print("1. 创建测试电路...")
    circuit = create_test_circuit()
    print(f"   电路名称: {circuit.name}")
    print(f"   器件数量: {len(circuit.devices)}")
    print(f"   网络数量: {len(circuit.nets)}")
    
    # 创建适配器
    print("\n2. 初始化适配器...")
    adapter = CircuitAdapter(debug_mode=True)
    
    # 获取电路摘要
    print("\n3. 电路摘要:")
    summary = adapter.get_conversion_summary(circuit)
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    # 测试转换
    print("\n4. 测试转换...")
    try:
        devices_dict, nets_dict = adapter.convert_to_symmetry_format(circuit)
        print("   ✅ 转换成功!")
        
        print(f"\n   转换后的器件:")
        for device_name, device_data in devices_dict.items():
            print(f"     {device_name}: {device_data['type']} - {device_data['parameters']}")
        
        print(f"\n   转换后的网络:")
        for net_name, net_data in nets_dict.items():
            connections = [p['device'] + '.' + p['pin'] for p in net_data['pins']]
            print(f"     {net_name}: {connections}")
            
    except Exception as e:
        print(f"   ❌ 转换失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试验证
    print("\n5. 测试验证...")
    try:
        if adapter.test_conversion(circuit):
            print("   ✅ 验证通过!")
        else:
            print("   ❌ 验证失败!")
            return False
    except Exception as e:
        print(f"   ❌ 验证过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("转换功能测试通过! ✅")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_adapter()
    sys.exit(0 if success else 1)
