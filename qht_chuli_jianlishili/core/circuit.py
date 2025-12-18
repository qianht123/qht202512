"""
Core circuit data structures
"""

from typing import Dict, List, Set, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json

from .geometry import Point, Rectangle, Shape, RectShape


class DeviceType(Enum):
    """Device type enumeration"""
    NMOS = "nmos"
    PMOS = "pmos"
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    DIODE = "diode"
    SUBCIRCUIT = "subcircuit"


class NetType(Enum):
    """Net type enumeration"""
    SIGNAL = "signal"
    POWER = "power"
    GROUND = "ground"
    CLOCK = "clock"
    ANALOG = "analog"
    DIGITAL = "digital"


class PinDirection(Enum):
    """Pin direction enumeration"""
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"
    POWER = "power"
    GROUND = "ground"


@dataclass
class Pin:
    """Pin representation"""
    name: str
    device: 'Device' = field(repr=False)  # Back reference to device
    net: Optional['Net'] = None
    direction: PinDirection = PinDirection.INOUT
    shape: Optional[Shape] = None
    access_points: List[Point] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize access points if shape is provided"""
        if self.shape and not self.access_points:
            # Default access point at shape center
            self.access_points.append(self.shape.get_bbox().center)
    
    def connect_to_net(self, net: 'Net'):
        """Connect this pin to a net"""
        if self.net:
            self.net.disconnect_pin(self)
        self.net = net
        net.connect_pin(self)
    
    def disconnect(self):
        """Disconnect from current net"""
        if self.net:
            self.net.disconnect_pin(self)
            self.net = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'direction': self.direction.value,
            'net': self.net.name if self.net else None
        }


@dataclass
class Device:
    """Device representation"""
    name: str
    device_type: DeviceType
    pins: Dict[str, Pin] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    position: Optional[Point] = None
    orientation: float = 0.0  # Rotation angle in degrees
    width: Optional[float] = None
    height: Optional[float] = None
    is_flipped: bool = False
    
    def __post_init__(self):
        """Initialize pins with back reference"""
        for pin in self.pins.values():
            pin.device = self
    
    def add_pin(self, pin: Pin):
        """Add a pin to this device"""
        self.pins[pin.name] = pin
        pin.device = self
    
    def get_pin(self, pin_name: str) -> Optional[Pin]:
        """Get pin by name"""
        return self.pins.get(pin_name)
    
    def connect_pin(self, pin_name: str, net: 'Net'):
        """Connect a pin to a net"""
        if pin_name in self.pins:
            self.pins[pin_name].connect_to_net(net)
        else:
            raise ValueError(f"Pin {pin_name} not found in device {self.name}")
    
    def get_bounding_box(self) -> Optional[Rectangle]:
        """Get device bounding box"""
        if self.position is None:
            return None
        
        if self.width and self.height:
            # Simple rectangular device
            half_w = self.width / 2
            half_h = self.height / 2
            return Rectangle(
                Point(self.position.x - half_w, self.position.y - half_h),
                Point(self.position.x + half_w, self.position.y + half_h)
            )
        
        # Calculate from pin shapes
        if any(pin.shape for pin in self.pins.values()):
            bboxes = [pin.shape.get_bbox() for pin in self.pins.values() if pin.shape]
            if bboxes:
                bbox = bboxes[0]
                for other_bbox in bboxes[1:]:
                    bbox = bbox.union(other_bbox)
                return bbox
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'type': self.device_type.value,
            'parameters': self.parameters,
            'position': self.position.to_tuple() if self.position else None,
            'orientation': self.orientation,
            'width': self.width,
            'height': self.height,
            'pins': {name: pin.to_dict() for name, pin in self.pins.items()}
        }


@dataclass
class Net:
    """Net representation"""
    name: str
    net_type: NetType = NetType.SIGNAL
    pins: Set[Pin] = field(default_factory=set)
    weight: float = 1.0
    symmetry_group: Optional[str] = None
    is_critical: bool = False
    
    def connect_pin(self, pin: Pin):
        """Connect a pin to this net"""
        self.pins.add(pin)
        pin.net = self
    
    def disconnect_pin(self, pin: Pin):
        """Disconnect a pin from this net"""
        self.pins.discard(pin)
        if pin.net == self:
            pin.net = None
    
    def get_connected_devices(self) -> Set[Device]:
        """Get all devices connected to this net"""
        return {pin.device for pin in self.pins}
    
    def get_bounding_box(self) -> Optional[Rectangle]:
        """Get bounding box of all connected pins"""
        if not self.pins:
            return None
        
        positions = []
        for pin in self.pins:
            if pin.device and pin.device.position:
                positions.append(pin.device.position)
            elif pin.shape:
                bbox = pin.shape.get_bbox()
                positions.extend([bbox.lower_left, bbox.upper_right])
        
        if positions:
            min_x = min(p.x for p in positions)
            max_x = max(p.x for p in positions)
            min_y = min(p.y for p in positions)
            max_y = max(p.y for p in positions)
            return Rectangle(Point(min_x, min_y), Point(max_x, max_y))
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'type': self.net_type.value,
            'weight': self.weight,
            'symmetry_group': self.symmetry_group,
            'is_critical': self.is_critical,
            'pins': [pin.name for pin in self.pins]
        }


@dataclass
class Circuit:
    """Circuit representation"""
    name: str
    nets: Dict[str, Net] = field(default_factory=dict)
    devices: Dict[str, Device] = field(default_factory=dict)
    pins: Dict[str, Pin] = field(default_factory=dict)  # IO pins
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    def add_net(self, net: Net):
        """Add a net to the circuit"""
        self.nets[net.name] = net
    
    def add_device(self, device: Device):
        """Add a device to the circuit"""
        self.devices[device.name] = device
    
    def add_pin(self, pin: Pin):
        """Add an IO pin to the circuit"""
        self.pins[pin.name] = pin
    
    def get_net(self, net_name: str) -> Optional[Net]:
        """Get net by name"""
        return self.nets.get(net_name)
    
    def get_device(self, device_name: str) -> Optional[Device]:
        """Get device by name"""
        return self.devices.get(device_name)
    
    def get_power_nets(self) -> List[Net]:
        """Get all power nets"""
        return [net for net in self.nets.values() if net.net_type == NetType.POWER]
    
    def get_ground_nets(self) -> List[Net]:
        """Get all ground nets"""
        return [net for net in self.nets.values() if net.net_type == NetType.GROUND]
    
    def get_signal_nets(self) -> List[Net]:
        """Get all signal nets"""
        return [net for net in self.nets.values() if net.net_type == NetType.SIGNAL]
    
    def get_devices_by_type(self, device_type: DeviceType) -> List[Device]:
        """Get all devices of a specific type"""
        return [device for device in self.devices.values() 
                if device.device_type == device_type]
    
    def get_bounding_box(self) -> Optional[Rectangle]:
        """Get circuit bounding box"""
        if not self.devices:
            return None
        
        bboxes = []
        for device in self.devices.values():
            bbox = device.get_bounding_box()
            if bbox:
                bboxes.append(bbox)
        
        if bboxes:
            circuit_bbox = bboxes[0]
            for bbox in bboxes[1:]:
                circuit_bbox = circuit_bbox.union(bbox)
            return circuit_bbox
        
        return None
    
    def validate_connections(self) -> List[str]:
        """Validate circuit connections and return list of errors"""
        errors = []
        
        # Check for unconnected pins
        for device in self.devices.values():
            for pin_name, pin in device.pins.items():
                if pin.net is None:
                    errors.append(f"Pin {device.name}.{pin_name} is not connected")
        
        # Check for nets with no connections
        for net in self.nets.values():
            if len(net.pins) == 0:
                errors.append(f"Net {net.name} has no connections")
            elif len(net.pins) == 1:
                errors.append(f"Net {net.name} has only one connection")
        
        # Check for floating devices (no power/ground connections)
        for device in self.devices.values():
            connected_nets = {pin.net for pin in device.pins if pin.net}
            power_nets = {net for net in connected_nets if net.net_type in [NetType.POWER, NetType.GROUND]}
            if not power_nets and device.device_type in [DeviceType.NMOS, DeviceType.PMOS]:
                errors.append(f"Device {device.name} has no power/ground connection")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'nets': {name: net.to_dict() for name, net in self.nets.items()},
            'devices': {name: device.to_dict() for name, device in self.devices.items()},
            'pins': {name: pin.to_dict() for name, pin in self.pins.items()},
            'constraints': self.constraints
        }
    
    def save_to_file(self, filename: str):
        """Save circuit to JSON file"""
        data = self.to_dict()
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Circuit':
        """Create circuit from dictionary"""
        circuit = cls(name=data['name'])
        
        # TODO: Implement full deserialization
        # This would require recreating the object graph
        
        return circuit