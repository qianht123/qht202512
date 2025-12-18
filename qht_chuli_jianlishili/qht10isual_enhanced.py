#!/usr/bin/env python3
"""
独立的qht10.sp可视化演示 + 器件版图生成
"""

import re
import os
import sys
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum

# 添加项目路径
sys.path.insert(0, '/home/icdesign/qianhtical1215/magical_flow')

# 简化的数据结构
class DeviceType(Enum):
    NMOS = "nmos"
    PMOS = "pmos"
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"

class NetType(Enum):
    SIGNAL = "signal"
    POWER = "power"
    GROUND = "ground"

@dataclass
class Pin:
    name: str
    net: Optional[str] = None

@dataclass
class Device:
    name: str
    device_type: DeviceType
    pins: Dict[str, Pin]
    parameters: Dict[str, Any]
    position: Optional[Any] = None

@dataclass
class Net:
    name: str
    net_type: NetType
    pins: Set[str]

@dataclass
class Circuit:
    name: str
    devices: Dict[str, Device]
    nets: Dict[str, Net]

class Qht10Visualizer:
    """qht10.sp专用可视化器 + 器件版图生成器"""
    
    def __init__(self):
        self.circuit = None
    
    def parse_and_visualize(self, filename: str):
        """解析并可视化qht10.sp"""
        print("🔍 正在解析qht10.sp...")
        
        # 读取文件内容
        with open(filename, 'r') as f:
            content = f.read()
        
        # 解析电路
        self.circuit = self._parse_qht10(content)
        
        # 可视化输出
        self.visualize_circuit()
        
        # 额外分析
        self._analyze_characteristics()
        
        # 生成器件版图
        self._generate_device_layouts()
    
    def _parse_qht10(self, content: str) -> Circuit:
        """解析qht10特定格式"""
        circuit = Circuit(name="TEST4_06", devices={}, nets={})
        
        # 提取子电路定义
        subckt_match = re.search(r'subckt\s+(\w+)\s+([\w\s]+)', content, re.IGNORECASE)
        if subckt_match:
            circuit.name = subckt_match.group(1)
            io_nets = subckt_match.group(2).split()
            
            # 创建IO网络
            for net_name in io_nets:
                net_type = self._classify_net(net_name)
                circuit.nets[net_name] = Net(name=net_name, net_type=net_type, pins=set())
        
        # 提取器件实例（qht10特殊格式）
        pattern = r'M(\d+)\s+\(([\w\s]+)\)\s+(\w+_\w+)\s+([^)]+)'
        
        for match in re.finditer(pattern, content):
            device_num = match.group(1)
            net_names = [n.strip() for n in match.group(2).split()]
            model_name = match.group(3)
            params_str = match.group(4)
            
            # 确定器件类型
            device_type = DeviceType.PMOS if 'pch' in model_name else DeviceType.NMOS
            
            # 解析参数
            parameters = {}
            for param in params_str.split():
                if '=' in param:
                    key, value = param.split('=', 1)
                    parameters[key] = value
            
            # 创建引脚
            pins = {}
            if len(net_names) >= 4:  # MOSFET有4个引脚
                pin_names = ['drain', 'gate', 'source', 'bulk']
                for i, net_name in enumerate(net_names):
                    if i < len(pin_names):
                        pin_name = pin_names[i]
                        pins[pin_name] = Pin(name=pin_name, net=net_name)
                        
                        # 更新网络
                        if net_name not in circuit.nets:
                            net_type = self._classify_net(net_name)
                            circuit.nets[net_name] = Net(name=net_name, net_type=net_type, pins=set())
                        circuit.nets[net_name].pins.add(f"M{device_num}")
            
            device = Device(name=f"M{device_num}", device_type=device_type, pins=pins, parameters=parameters, position=(0, 0))
            circuit.devices[f"M{device_num}"] = device
        
        return circuit
    
    def _classify_net(self, net_name: str) -> NetType:
        """分类网络类型"""
        net_name_upper = net_name.upper()
        if net_name_upper == 'VDD':
            return NetType.POWER
        elif net_name_upper == 'GND':
            return NetType.GROUND
        return NetType.SIGNAL
    
    def visualize_circuit(self):
        """可视化电路"""
        print("\n" + "=" * 70)
        print("🔬 TEST4_06 CIRCUIT VISUALIZATION")
        print("=" * 70)
        
        # 1. 电路概览
        self._print_overview()
        
        # 2. 器件连接图
        self._print_device_connections()
        
        # 3. 网络拓扑
        self._print_network_topology()
        
        # 4. 器件详情
        self._print_device_details()
        
        print("=" * 70)
    
    def _print_overview(self):
        """打印电路概览"""
        print("\n📊 CIRCUIT OVERVIEW")
        print("-" * 40)
        
        pmos_count = sum(1 for d in self.circuit.devices.values() if d.device_type == DeviceType.PMOS)
        nmos_count = sum(1 for d in self.circuit.devices.values() if d.device_type == DeviceType.NMOS)
        
        print(f"Circuit: {self.circuit.name}")
        print(f"Total Devices: {len(self.circuit.devices)}")
        print(f"  PMOS: {pmos_count} 🟫")
        print(f"  NMOS: {nmos_count} 🟪")
        print(f"Total Nets: {len(self.circuit.nets)}")
        
        power_nets = [n for n in self.circuit.nets.values() if n.net_type == NetType.POWER]
        ground_nets = [n for n in self.circuit.nets.values() if n.net_type == NetType.GROUND]
        signal_nets = [n for n in self.circuit.nets.values() if n.net_type == NetType.SIGNAL]
        
        print(f"  Power: {len(power_nets)} ⚡")
        print(f"  Ground: {len(ground_nets)} 🔌")
        print(f"  Signal: {len(signal_nets)} 📡")
    
    def _print_device_connections(self):
        """打印器件连接图"""
        print("\n🔗 DEVICE CONNECTIONS")
        print("-" * 40)
        
        # 按器件编号排序
        sorted_devices = sorted(self.circuit.devices.items(), key=lambda x: x[0])
        
        for device_name, device in sorted_devices:
            icon = "🟫" if device.device_type == DeviceType.PMOS else "🟪"
            print(f"\n{icon} {device_name} [{device.device_type.value.upper()}]")
            print("   " + "─" * 30)
            
            # 显示连接
            for pin_name, pin in device.pins.items():
                net_name = pin.net
                net = self.circuit.nets.get(net_name)
                if net:
                    net_icon = {"power": "⚡", "ground": "🔌", "signal": "📡"}.get(net.net_type.value, "📡")
                    print(f"   ├─ {pin_name} → {net_icon} {net_name}")
            
            # 显示关键参数
            key_params = []
            for param in ['w', 'l', 'm']:
                if param in device.parameters:
                    key_params.append(f"{param}={device.parameters[param]}")
            
            if key_params:
                print(f"   └─ Parameters: {', '.join(key_params)}")
    
    def _print_network_topology(self):
        """打印网络拓扑"""
        print("\n🌐 NETWORK TOPOLOGY")
        print("-" * 40)
        
        # 找出关键网络
        important_nets = []
        for net in self.circuit.nets.values():
            if len(net.pins) >= 2:
                important_nets.append(net)
        
        # 按重要性排序
        important_nets.sort(key=lambda n: (n.net_type.value != 'power', 
                                       n.net_type.value != 'ground'))
        
        for net in important_nets:
            net_type_icon = {"power": "⚡", "ground": "🔌", "signal": "📡"}.get(net.net_type.value, "📡")
            print(f"\n{net_type_icon} {net.name} ({net.net_type.value.upper()})")
            print("   " + "─" * 30)
            
            connected_devices = {}
            for pin in net.pins:
                if pin in self.circuit.devices:
                    device = self.circuit.devices[pin]
                    if device.name not in connected_devices:
                        connected_devices[device.name] = []
                    connected_devices[device.name].append(device.device_type.value)
            
            for device_name, types in connected_devices.items():
                type_icons = {"pmos": "🟫", "nmos": "🟪"}
                icon = type_icons.get(types[0], "📦")
                print(f"   ├─ {icon} {device_name}")
    
    def _print_device_details(self):
        """打印器件详细信息"""
        print("\n🔧 DEVICE SPECIFICATIONS")
        print("-" * 40)
        
        for device_name, device in sorted(self.circuit.devices.items()):
            icon = "🟫" if device.device_type == DeviceType.PMOS else "🟪"
            print(f"\n{icon} {device_name}")
            print("   " + "─" * 35)
            
            # 所有参数
            print(f"   Parameters:")
            for param, value in sorted(device.parameters.items()):
                print(f"     • {param}: {value}")
            
            # 连接的网络
            print(f"   Connections:")
            for pin_name, pin in device.pins.items():
                net = self.circuit.nets.get(pin.net)
                if net:
                    net_type = net.net_type.value
                    print(f"     • {pin_name}: {pin.net} ({net_type})")
    
    def _analyze_characteristics(self):
        """分析电路特性"""
        print("\n📈 CIRCUIT ANALYSIS")
        print("-" * 40)
        
        # 分析器件尺寸
        widths = []
        lengths = []
        for device in self.circuit.devices.values():
            if 'w' in device.parameters:
                try:
                    w = float(device.parameters['w'].replace('n', ''))
                    widths.append(w)
                except:
                    pass
            if 'l' in device.parameters:
                try:
                    l = float(device.parameters['l'].replace('n', ''))
                    lengths.append(l)
                except:
                    pass
        
        if widths:
            print(f"Device width range: {min(widths)}n - {max(widths)}n")
            print(f"Average width: {sum(widths)/len(widths):.1f}n")
        
        if lengths:
            print(f"Channel length: {lengths[0]}n (uniform)")
        
        # 分析网络复杂度
        net_complexity = [len(net.pins) for net in self.circuit.nets.values()]
        print(f"Connection range: {min(net_complexity)} - {max(net_complexity)} pins/net")
        
        # 分析对称性
        print("\n🔄 SYMMETRY DETECTION")
        print("-" * 40)
        
        # 寻找可能的差分对
        diff_pairs = []
        for net_name in self.circuit.nets:
            if 'ain' in net_name.lower():
                counterpart = net_name.replace('ain', 'bin')
                if counterpart in self.circuit.nets:
                    diff_pairs.append((net_name, counterpart))
        
        if diff_pairs:
            print("Differential pairs found:")
            for net1, net2 in diff_pairs:
                print(f"  {net1} ↔ {net2}")
        else:
            print("No differential pairs detected")
    
    def _generate_device_layouts(self):
        """生成器件版图"""
        print("\n🏗️  GENERATING DEVICE LAYOUTS")
        print("-" * 40)
        
        try:
            # 导入必要的模块
            from core.circuit import Device as CoreDevice, DeviceType as CoreDeviceType
            from core.technology import TechnologyDB, Layer, LayerType, Direction
            from placement.device_generator import DeviceGenerator
            from parser.gds import GdsWriter
            
            print("🔧 初始化工艺数据库...")
            
            # 创建工艺数据库
            tech_db = self._create_tech_db()
            
            print("🔧 初始化器件生成器...")
            generator = DeviceGenerator(tech_db)
            
            # 创建输出目录
            output_dir = "/install/MAGICAL/qht_chuli_jianlishili/zhongjiangds"
            os.makedirs(output_dir, exist_ok=True)
            
            print(f"📁 输出目录: {output_dir}")
            
            # 转换器件格式并生成版图
            success_count = 0
            for device_name, device in self.circuit.devices.items():
                try:
                    # 转换为core.Device格式
                    core_device = self._convert_device(device)
                    
                    # 生成版图
                    layout = generator.generate_device_layout(core_device)
                    
                    if layout:
                        # 创建单器件电路
                        single_device_circuit = self._create_single_device_circuit(core_device, tech_db)
                        
                        # 生成GDS文件
                        gds_writer = GdsWriter()
                        output_file = os.path.join(output_dir, f"{device_name}.gds")
                        
                        gds_writer.write(single_device_circuit, output_file, tech_db)
                        
                        print(f"✅ {device_name}: 版图生成成功 → {device_name}.gds")
                        success_count += 1
                        
                        # 显示版图统计
                        total_shapes = sum(len(shapes) for shapes in layout.values())
                        print(f"   包含 {len(layout)} 层, {total_shapes} 个图形")
                        
                    else:
                        print(f"❌ {device_name}: 版图生成失败")
                        
                except Exception as e:
                    print(f"❌ {device_name}: 生成出错 - {e}")
            
            print(f"\n🎉 完成! 成功生成 {success_count}/{len(self.circuit.devices)} 个器件版图")
            
        except ImportError as e:
            print(f"❌ 导入模块失败: {e}")
            print("   请确保magical_flow模块在Python路径中")
        except Exception as e:
            print(f"❌ 版图生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_tech_db(self):
        """创建工艺数据库"""
        from core.technology import TechnologyDB, Layer, LayerType, Direction
        
        tech_db = TechnologyDB(name="TestTech")
        
        # 添加基础层
        layers = {
            'OD': Layer('OD', LayerType.MASTERSLICE, min_width=0.12, min_spacing=0.12),
            'PO': Layer('PO', LayerType.ROUTING, Direction.HORIZONTAL, min_width=0.04, min_spacing=0.04),
            'M1': Layer('M1', LayerType.ROUTING, Direction.HORIZONTAL, min_width=0.07, min_spacing=0.07),
            'CO': Layer('CO', LayerType.CUT, min_width=0.05, min_spacing=0.05),
            'NP': Layer('NP', LayerType.IMPLANT, min_width=0.12, min_spacing=0.12),
            'PP': Layer('PP', LayerType.IMPLANT, min_width=0.12, min_spacing=0.12),
            'NW': Layer('NW', LayerType.MASTERSLICE, min_width=0.12, min_spacing=0.12),
        }
        
        for layer_name, layer in layers.items():
            layer.layer_number = len(tech_db.layers)
            tech_db.layers[layer_name] = layer
        
        tech_db.grid_step = 0.001
        
        return tech_db
    
    def _convert_device(self, device):
        """转换器件格式"""
        from core.circuit import Device as CoreDevice, DeviceType as CoreDeviceType
        
        # 转换器件类型
        if device.device_type == DeviceType.NMOS:
            core_device_type = CoreDeviceType.NMOS
        elif device.device_type == DeviceType.PMOS:
            core_device_type = CoreDeviceType.PMOS
        else:
            return None
        
        # 创建core.Device
        core_device = CoreDevice(
            name=device.name,
            device_type=core_device_type,
            parameters=device.parameters,
            position=device.position or (0, 0)
        )
        
        return core_device
    
    def _create_single_device_circuit(self, device, tech_db):
        """创建单器件电路"""
        from core.circuit import Circuit, Net, NetType
        
        circuit = Circuit(name=f"{device.name}_layout")
        
        # 添加基本网络
        vdd_net = Net(name="VDD", net_type=NetType.POWER)
        gnd_net = Net(name="GND", net_type=NetType.GROUND)
        circuit.add_net(vdd_net)
        circuit.add_net(gnd_net)
        
        # 添加器件
        circuit.add_device(device)
        
        return circuit

if __name__ == "__main__":
    visualizer = Qht10Visualizer()
    visualizer.parse_and_visualize("qht10.sp")