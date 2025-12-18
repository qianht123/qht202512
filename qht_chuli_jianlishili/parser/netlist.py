"""
Netlist parser for Spectre and HSPICE formats
"""

import re
import os
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod

from ..core.circuit import Circuit, Net, Device, Pin, DeviceType, NetType, PinDirection
from ..core.geometry import Point, Rectangle, Shape, RectShape


class NetlistParser(ABC):
    """Abstract base class for netlist parsers"""
    
    @abstractmethod
    def parse(self, filename: str) -> Circuit:
        """Parse netlist file and return Circuit object"""
        pass
    
    @abstractmethod
    def _parse_line(self, line: str) -> Optional[Any]:
        """Parse a single line of the netlist"""
        pass
    
    def visualize_circuit(self, circuit: Circuit):
        """Visualize the parsed circuit in terminal"""
        print("=" * 70)
        print(f"CIRCUIT VISUALIZATION: {circuit.name}")
        print("=" * 70)
        
        # 1. 显示电路统计信息
        self._print_circuit_stats(circuit)
        
        # 2. 显示网络连接图
        self._print_net_connections(circuit)
        
        # 3. 显示器件详情
        self._print_device_details(circuit)
        
        # 4. 显示层次结构
        self._print_hierarchy(circuit)
        
        print("=" * 70)
    
    def _print_circuit_stats(self, circuit: Circuit):
        """Print circuit statistics"""
        print("\n📊 CIRCUIT STATISTICS")
        print("-" * 40)
        
        # 器件统计
        device_stats = {}
        for device in circuit.devices.values():
            dtype = device.device_type.value
            device_stats[dtype] = device_stats.get(dtype, 0) + 1
        
        print(f"Total Devices: {len(circuit.devices)}")
        for dtype, count in sorted(device_stats.items()):
            print(f"  {dtype}: {count}")
        
        # 网络统计
        net_stats = {}
        for net in circuit.nets.values():
            ntype = net.net_type.value
            net_stats[ntype] = net_stats.get(ntype, 0) + 1
        
        print(f"\nTotal Nets: {len(circuit.nets)}")
        for ntype, count in sorted(net_stats.items()):
            print(f"  {ntype}: {count}")
    
    def _print_net_connections(self, circuit: Circuit):
        """Print network connections in a visual format"""
        print("\n🔗 NET CONNECTIONS")
        print("-" * 40)
        
        # 找出关键网络（连接多个器件的网络）
        important_nets = []
        for net in circuit.nets.values():
            if len(net.pins) >= 2:  # 连接多个引脚的网络
                important_nets.append(net)
        
        # 按重要性排序（电源/地优先）
        important_nets.sort(key=lambda n: (n.net_type.value != 'power', 
                                       n.net_type.value != 'ground', 
                                       n.net_type.value))
        
        for net in important_nets[:10]:  # 只显示前10个重要网络
            net_type_icon = {"power": "⚡", "ground": "🔌", "signal": "📡"}.get(net.net_type.value, "📡")
            print(f"\n{net_type_icon} {net.name} ({net.net_type.value.upper()})")
            print("   " + "─" * 30)
            
            connected_devices = {}
            for pin in net.pins:
                if pin.device:
                    device_name = pin.device.name
                    if device_name not in connected_devices:
                        connected_devices[device_name] = []
                    connected_devices[device_name].append(pin.name)
            
            for device_name, pins in connected_devices.items():
                pins_str = ", ".join(pins)
                device = circuit.get_device(device_name)
                if device:
                    dtype = device.device_type.value
                    print(f"   ├─ {device_name} [{dtype}] → {pins_str}")
    
    def _print_device_details(self, circuit: Circuit):
        """Print detailed device information"""
        print("\n🔧 DEVICE DETAILS")
        print("-" * 40)
        
        # 按类型分组显示器件
        devices_by_type = {}
        for device in circuit.devices.values():
            dtype = device.device_type.value
            if dtype not in devices_by_type:
                devices_by_type[dtype] = []
            devices_by_type[dtype].append(device)
        
        for dtype, devices in sorted(devices_by_type.items()):
            print(f"\n{dtype.upper()} DEVICES ({len(devices)})")
            print("   " + "─" * 35)
            
            for device in devices[:5]:  # 每种类型只显示前5个
                # 器件图标
                if 'pmos' in dtype or 'pch' in dtype:
                    icon = "🟫"
                elif 'nmos' in dtype or 'nch' in dtype:
                    icon = "🟪"
                elif 'res' in dtype:
                    icon = "📦"
                elif 'cap' in dtype:
                    icon = "🔋"
                else:
                    icon = "📦"
                
                print(f"   {icon} {device.name}")
                
                # 显示连接的网络
                connections = []
                for pin_name, pin in device.pins.items():
                    net_name = pin.net.name if pin.net else "NC"
                    connections.append(f"{pin_name}→{net_name}")
                
                if connections:
                    print(f"      ├─ Connections: {', '.join(connections)}")
                
                # 显示关键参数
                key_params = []
                for param, value in device.parameters.items():
                    if param.upper() in ['W', 'L', 'M']:
                        key_params.append(f"{param}={value}")
                
                if key_params:
                    print(f"      └─ Parameters: {', '.join(key_params)}")
            
            if len(devices) > 5:
                print(f"   ... and {len(devices) - 5} more {dtype} devices")
    
    def _print_hierarchy(self, circuit: Circuit):
        """Print circuit hierarchy"""
        print("\n🏗️  CIRCUIT HIERARCHY")
        print("-" * 40)
        
        print(f"Top Level: {circuit.name}")
        
        # IO引脚
        io_nets = []
        for net in circuit.nets.values():
            if len(net.pins) == 0:  # 没有连接到内部器件的网络可能是IO
                io_nets.append(net.name)
        
        if io_nets:
            print("├─ IO Pins:")
            for net in sorted(io_nets):
                net_type = circuit.get_net(net).net_type.value
                icon = {"power": "⚡", "ground": "🔌", "signal": "📡"}.get(net_type, "📡")
                print(f"   ├─ {icon} {net}")
        
        # 内部器件
        print(f"└─ Internal Devices ({len(circuit.devices)})")
        
        # 显示第一个器件的连接作为示例
        if circuit.devices:
            first_device = list(circuit.devices.values())[0]
            print(f"   └─ Example: {first_device.name}")
            for pin_name, pin in first_device.pins.items():
                net_name = pin.net.name if pin.net else "NC"
                print(f"      ├─ {pin_name} → {net_name}")
    
    def _classify_net(self, net_name: str) -> NetType:
        """Classify net type based on name"""
        net_name_upper = net_name.upper()
        
        # Power nets
        if net_name_upper in ['VDD', 'VCC', 'POWER', 'VDDA', 'VDDD']:
            return NetType.POWER
        
        # Ground nets
        if net_name_upper in ['GND', 'VSS', 'GROUND', 'VSSA', 'VSSD']:
            return NetType.GROUND
        
        # Clock nets
        if 'CLK' in net_name_upper or 'CLOCK' in net_name_upper:
            return NetType.CLOCK
        
        # Default to signal
        return NetType.SIGNAL
    
    def _determine_device_type(self, model_name: str) -> DeviceType:
        """Determine device type from model name"""
        model_upper = model_name.upper()
        
        # NMOS devices
        if any(nmos in model_upper for nmos in ['NMOS', 'NCH', 'NCH_NA', 'NCH_MAC']):
            return DeviceType.NMOS
        
        # PMOS devices
        if any(pmos in model_upper for pmos in ['PMOS', 'PCH', 'PCH_MAC']):
            return DeviceType.PMOS
        
        # Resistors
        if any(res in model_upper for res in ['RES', 'RPPOLY', 'RPPOLY_M']):
            return DeviceType.RESISTOR
        
        # Capacitors
        if any(cap in model_upper for cap in ['CAP', 'CFMOM', 'CRTMOM']):
            return DeviceType.CAPACITOR
        
        # Diodes
        if 'DIODE' in model_upper:
            return DeviceType.DIODE
        
        # Default to subcircuit
        return DeviceType.SUBCIRCUIT


class SpectreParser(NetlistParser):
    """Spectre netlist parser"""
    
    def __init__(self):
        self.circuit = None
        self.current_subcircuit = None
        self.line_number = 0
    
    def parse(self, filename: str) -> Circuit:
        """Parse Spectre netlist file"""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Netlist file not found: {filename}")
        
        self.circuit = Circuit(name=os.path.splitext(os.path.basename(filename))[0])
        self.current_subcircuit = None
        self.line_number = 0
        
        with open(filename, 'r') as f:
            for line in f:
                self.line_number += 1
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('//') or line.startswith('*'):
                    continue
                
                # Handle line continuation
                while line.endswith('\\'):
                    line = line[:-1]  # Remove backslash
                    next_line = next(f).strip()
                    line += ' ' + next_line
                    self.line_number += 1
                
                self._parse_line(line)
        
        # Validate the circuit
        errors = self.circuit.validate_connections()
        if errors:
            print(f"Warning: Found {len(errors)} connection issues:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
        
        # Visualize the parsed circuit
        self.visualize_circuit(self.circuit)
        
        return self.circuit
    
    def _parse_line(self, line: str):
        """Parse a single line of Spectre netlist"""
        # Remove comments
        if '//' in line:
            line = line[:line.index('//')]
        
        # Split into tokens
        tokens = line.split()
        if not tokens:
            return
        
        # Check for subcircuit definition
        if tokens[0].lower() == 'subckt':
            self._parse_subckt(tokens)
        elif tokens[0].lower() == 'topckt':
            self._parse_topckt(tokens)
        elif tokens[0].lower() == 'ends':
            self._parse_ends(tokens)
        else:
            # Parse instance line
            self._parse_instance(tokens)
    
    def _parse_subckt(self, tokens: List[str]):
        """Parse subcircuit definition"""
        if len(tokens) < 2:
            return
        
        subckt_name = tokens[1]
        io_nets = tokens[2:]  # All remaining tokens are IO nets
        
        # Create subcircuit (for now, we treat it as part of main circuit)
        self.current_subcircuit = subckt_name
        
        # Add IO nets to circuit
        for net_name in io_nets:
            if net_name not in self.circuit.nets:
                net = Net(name=net_name, net_type=self._classify_net(net_name))
                self.circuit.add_net(net)
    
    def _parse_topckt(self, tokens: List[str]):
        """Parse top circuit definition"""
        if len(tokens) < 2:
            return
        
        topckt_name = tokens[1]
        io_nets = tokens[2:]  # All remaining tokens are IO nets
        
        # Set circuit name
        self.circuit.name = topckt_name
        self.current_subcircuit = topckt_name
        
        # Add IO nets to circuit
        for net_name in io_nets:
            if net_name not in self.circuit.nets:
                net = Net(name=net_name, net_type=self._classify_net(net_name))
                self.circuit.add_net(net)
    
    def _parse_ends(self, tokens: List[str]):
        """Parse ends statement"""
        self.current_subcircuit = None
    
    def _parse_instance(self, tokens: List[str]):
        """Parse instance line"""
        if len(tokens) < 3:
            return
        
        instance_name = tokens[0]
        
        # Parse nets and model
        paren_index = None
        for i, token in enumerate(tokens):
            if token == '(':
                paren_index = i
                break
        
        if paren_index is None:
            # Format: name net1 net2 net3 model params...
            # Find model name (last token before parameters)
            model_name = tokens[-1]
            net_names = tokens[1:-1]
            params = {}
        else:
            # Format: name (net1 net2 net3) model params...
            closing_paren = None
            for i in range(paren_index, len(tokens)):
                if tokens[i] == ')':
                    closing_paren = i
                    break
            
            if closing_paren is None:
                return
            
            net_names = tokens[paren_index+1:closing_paren]
            model_name = tokens[closing_paren+1] if closing_paren+1 < len(tokens) else ""
            params = {}
            
            # Parse parameters
            for i in range(closing_paren+2, len(tokens)):
                if '=' in tokens[i]:
                    key, value = tokens[i].split('=', 1)
                    params[key] = value
        
        # Create device
        device_type = self._determine_device_type(model_name)
        device = Device(
            name=instance_name,
            device_type=device_type,
            parameters=params
        )
        
        # Add pins
        pin_names = self._get_pin_names(device_type, len(net_names))
        for i, net_name in enumerate(net_names):
            if i < len(pin_names):
                pin_name = pin_names[i]
            else:
                pin_name = f"pin{i}"
            
            # Get or create net
            if net_name not in self.circuit.nets:
                net = Net(name=net_name, net_type=self._classify_net(net_name))
                self.circuit.add_net(net)
            else:
                net = self.circuit.nets[net_name]
            
            # Create pin
            pin = Pin(name=pin_name, device=device)
            pin.connect_to_net(net)
            device.add_pin(pin)
        
        self.circuit.add_device(device)
    
    def _get_pin_names(self, device_type: DeviceType, num_pins: int) -> List[str]:
        """Get standard pin names for device type"""
        if device_type == DeviceType.NMOS or device_type == DeviceType.PMOS:
            if num_pins >= 3:
                return ['drain', 'gate', 'source']
            elif num_pins >= 2:
                return ['drain', 'gate']
            else:
                return ['drain']
        elif device_type == DeviceType.RESISTOR:
            if num_pins >= 2:
                return ['plus', 'minus']
            else:
                return ['plus']
        elif device_type == DeviceType.CAPACITOR:
            if num_pins >= 2:
                return ['plus', 'minus']
            else:
                return ['plus']
        else:
            return [f"pin{i}" for i in range(num_pins)]


class HSpiceParser(NetlistParser):
    """HSPICE netlist parser"""
    
    def __init__(self):
        self.circuit = None
        self.line_number = 0
    
    def parse(self, filename: str) -> Circuit:
        """Parse HSPICE netlist file"""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Netlist file not found: {filename}")
        
        self.circuit = Circuit(name=os.path.splitext(os.path.basename(filename))[0])
        self.line_number = 0
        
        with open(filename, 'r') as f:
            for line in f:
                self.line_number += 1
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('*') or line.startswith('.'):
                    continue
                
                # Handle line continuation
                while line.endswith('+'):
                    line = line[:-1]  # Remove plus sign
                    next_line = next(f).strip()
                    line += ' ' + next_line
                    self.line_number += 1
                
                self._parse_line(line)
        
        return self.circuit
    
    def _parse_line(self, line: str):
        """Parse a single line of HSPICE netlist"""
        # Remove comments
        if '$' in line:
            line = line[:line.index('$')]
        
        tokens = line.split()
        if not tokens:
            return
        
        # Parse instance line
        self._parse_instance(tokens)
    
    def _parse_instance(self, tokens: List[str]):
        """Parse instance line"""
        if len(tokens) < 3:
            return
        
        instance_name = tokens[0]
        
        # For HSPICE, the last token is usually the model name
        # Nets are everything in between
        model_name = tokens[-1]
        net_names = tokens[1:-1]
        
        # Parse parameters (if any)
        params = {}
        for i, token in enumerate(tokens):
            if '=' in token and i > 0:
                key, value = token.split('=', 1)
                params[key] = value
                # Remove parameter tokens from net_names
                if token in net_names:
                    net_names.remove(token)
        
        # Create device
        device_type = self._determine_device_type(model_name)
        device = Device(
            name=instance_name,
            device_type=device_type,
            parameters=params
        )
        
        # Add pins
        pin_names = self._get_pin_names(device_type, len(net_names))
        for i, net_name in enumerate(net_names):
            if i < len(pin_names):
                pin_name = pin_names[i]
            else:
                pin_name = f"pin{i}"
            
            # Get or create net
            if net_name not in self.circuit.nets:
                net = Net(name=net_name, net_type=self._classify_net(net_name))
                self.circuit.add_net(net)
            else:
                net = self.circuit.nets[net_name]
            
            # Create pin
            pin = Pin(name=pin_name, device=device)
            pin.connect_to_net(net)
            device.add_pin(pin)
        
        self.circuit.add_device(device)
    
    def _get_pin_names(self, device_type: DeviceType, num_pins: int) -> List[str]:
        """Get standard pin names for device type"""
        if device_type == DeviceType.NMOS or device_type == DeviceType.PMOS:
            if num_pins >= 4:
                return ['drain', 'gate', 'source', 'bulk']
            elif num_pins >= 3:
                return ['drain', 'gate', 'source']
            elif num_pins >= 2:
                return ['drain', 'gate']
            else:
                return ['drain']
        elif device_type == DeviceType.RESISTOR:
            if num_pins >= 2:
                return ['plus', 'minus']
            else:
                return ['plus']
        elif device_type == DeviceType.CAPACITOR:
            if num_pins >= 2:
                return ['plus', 'minus']
            else:
                return ['plus']
        else:
            return [f"pin{i}" for i in range(num_pins)]


# Factory function
def create_parser(netlist_type: str) -> NetlistParser:
    """Create appropriate parser based on netlist type"""
    if netlist_type.lower() == 'spectre':
        return SpectreParser()
    elif netlist_type.lower() == 'hspice':
        return HSpiceParser()
    else:
        raise ValueError(f"Unsupported netlist type: {netlist_type}")


# Test function
if __name__ == "__main__":
    # Create a simple test netlist
    test_netlist = """
// Simple test circuit
subckt test_circuit in out vdd vss
M1 out in vss vss nch w=1u l=40n
M2 vdd in out vdd pch w=2u l=40n
ends test_circuit
"""
    
    # Write test file
    with open("test_netlist.scs", "w") as f:
        f.write(test_netlist)
    
    # Parse with Spectre parser
    parser = SpectreParser()
    circuit = parser.parse("test_netlist.scs")
    
    print(f"Parsed circuit: {circuit.name}")
    print(f"Nets: {list(circuit.nets.keys())}")
    print(f"Devices: {list(circuit.devices.keys())}")
    
    # Clean up
    os.remove("test_netlist.scs")