"""
Technology database structures
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from .geometry import Point, Rectangle


class LayerType(Enum):
    """Layer type enumeration"""
    ROUTING = "routing"
    CUT = "cut"
    MASTERSLICE = "masterslice"
    OVERLAP = "overlap"
    IMPLANT = "implant"


class Direction(Enum):
    """Layer direction enumeration"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    OMNI = "omni"  # No preferred direction


@dataclass
class Layer:
    """Layer representation"""
    name: str
    layer_type: LayerType
    direction: Optional[Direction] = None
    min_width: float = 0.0
    min_spacing: float = 0.0
    pitch: float = 0.0
    offset: float = 0.0
    thickness: float = 0.0
    resistance: float = 0.0  # Ohms per square
    capacitance: float = 0.0  # Farads per square micron
    
    def is_routing_layer(self) -> bool:
        """Check if this is a routing layer"""
        return self.layer_type == LayerType.ROUTING
    
    def is_cut_layer(self) -> bool:
        """Check if this is a cut (via) layer"""
        return self.layer_type == LayerType.CUT
    
    def get_preferred_direction(self) -> Optional[Direction]:
        """Get preferred routing direction"""
        return self.direction
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'type': self.layer_type.value,
            'direction': self.direction.value if self.direction else None,
            'min_width': self.min_width,
            'min_spacing': self.min_spacing,
            'pitch': self.pitch,
            'offset': self.offset,
            'thickness': self.thickness,
            'resistance': self.resistance,
            'capacitance': self.capacitance
        }


@dataclass
class ViaRule:
    """Via rule representation"""
    name: str
    layers: List[str]  # Layer stack [bottom, via, top] or [bottom, top] for cut layers
    enclosure: Dict[str, float] = field(default_factory=dict)  # Enclosure for each layer
    spacing: float = 0.0
    width: float = 0.0
    height: float = 0.0
    resistance: float = 0.0  # Via resistance in Ohms
    
    def get_bottom_layer(self) -> str:
        """Get bottom layer name"""
        return self.layers[0] if self.layers else ""
    
    def get_top_layer(self) -> str:
        """Get top layer name"""
        return self.layers[-1] if self.layers else ""
    
    def get_via_layer(self) -> Optional[str]:
        """Get via/cut layer name"""
        if len(self.layers) >= 3:
            return self.layers[1]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'layers': self.layers,
            'enclosure': self.enclosure,
            'spacing': self.spacing,
            'width': self.width,
            'height': self.height,
            'resistance': self.resistance
        }


@dataclass
class DesignRules:
    """Design rules representation"""
    min_spacing: Dict[str, float] = field(default_factory=dict)  # Layer-wise min spacing
    min_width: Dict[str, float] = field(default_factory=dict)    # Layer-wise min width
    via_spacing: Dict[str, float] = field(default_factory=dict)  # Via spacing rules
    enclosure_rules: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def get_min_spacing(self, layer_name: str) -> float:
        """Get minimum spacing for a layer"""
        return self.min_spacing.get(layer_name, 0.0)
    
    def get_min_width(self, layer_name: str) -> float:
        """Get minimum width for a layer"""
        return self.min_width.get(layer_name, 0.0)
    
    def set_spacing_rule(self, layer1: str, layer2: str, spacing: float):
        """Set spacing rule between two layers"""
        key = f"{layer1}_{layer2}"
        self.min_spacing[key] = spacing
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'min_spacing': self.min_spacing,
            'min_width': self.min_width,
            'via_spacing': self.via_spacing,
            'enclosure_rules': self.enclosure_rules
        }


@dataclass
class GridInfo:
    """Grid information for placement and routing"""
    grid_step: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    symmetry_axis_x: Optional[float] = None
    
    def snap_to_grid(self, point: Point) -> Point:
        """Snap point to grid"""
        if self.grid_step == 0.0:
            return point
        
        x = round((point.x - self.offset_x) / self.grid_step) * self.grid_step + self.offset_x
        y = round((point.y - self.offset_y) / self.grid_step) * self.grid_step + self.offset_y
        return Point(x, y)
    
    def is_on_grid(self, point: Point, tolerance: float = 1e-6) -> bool:
        """Check if point is on grid"""
        if self.grid_step == 0.0:
            return True
        
        x_rem = (point.x - self.offset_x) % self.grid_step
        y_rem = (point.y - self.offset_y) % self.grid_step
        
        return (x_rem < tolerance or x_rem > self.grid_step - tolerance and
                y_rem < tolerance or y_rem > self.grid_step - tolerance)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'grid_step': self.grid_step,
            'offset_x': self.offset_x,
            'offset_y': self.offset_y,
            'symmetry_axis_x': self.symmetry_axis_x
        }


@dataclass
class TechnologyDB:
    """Technology database"""
    name: str = ""
    version: str = ""
    database_units: float = 1000.0  # Units per micron
    layers: Dict[str, Layer] = field(default_factory=dict)
    via_rules: Dict[str, ViaRule] = field(default_factory=dict)
    design_rules: DesignRules = field(default_factory=DesignRules)
    grid_info: GridInfo = field(default_factory=GridInfo)
    
    def add_layer(self, layer: Layer):
        """Add a layer to the technology database"""
        self.layers[layer.name] = layer
    
    def add_via_rule(self, via_rule: ViaRule):
        """Add a via rule to the technology database"""
        self.via_rules[via_rule.name] = via_rule
    
    def get_layer(self, layer_name: str) -> Optional[Layer]:
        """Get layer by name"""
        return self.layers.get(layer_name)
    
    def get_via_rule(self, rule_name: str) -> Optional[ViaRule]:
        """Get via rule by name"""
        return self.via_rules.get(rule_name)
    
    def get_routing_layers(self) -> List[Layer]:
        """Get all routing layers"""
        return [layer for layer in self.layers.values() if layer.is_routing_layer()]
    
    def get_cut_layers(self) -> List[Layer]:
        """Get all cut layers"""
        return [layer for layer in self.layers.values() if layer.is_cut_layer()]
    
    def get_layer_stack(self) -> List[str]:
        """Get layer stack from bottom to top"""
        routing_layers = self.get_routing_layers()
        # Sort by some criteria (e.g., by name or predefined order)
        # For now, return in alphabetical order
        return sorted([layer.name for layer in routing_layers])
    
    def find_via_rule_between_layers(self, layer1: str, layer2: str) -> Optional[ViaRule]:
        """Find via rule that connects two layers"""
        for via_rule in self.via_rules.values():
            if (layer1 in via_rule.layers and layer2 in via_rule.layers):
                return via_rule
        return None
    
    def microns_to_units(self, microns: float) -> float:
        """Convert microns to database units"""
        return microns * self.database_units
    
    def units_to_microns(self, units: float) -> float:
        """Convert database units to microns"""
        return units / self.database_units
    
    def validate(self) -> List[str]:
        """Validate technology database and return list of errors"""
        errors = []
        
        # Check for required layers
        required_layers = ["METAL1", "METAL2", "POLY", "DIFF"]
        for layer_name in required_layers:
            if layer_name not in self.layers:
                errors.append(f"Required layer {layer_name} not found")
        
        # Check for via rules consistency
        for via_rule in self.via_rules.values():
            for layer_name in via_rule.layers:
                if layer_name not in self.layers:
                    errors.append(f"Via rule {via_rule.name} references undefined layer {layer_name}")
        
        # Check for valid grid info
        if self.grid_info.grid_step <= 0:
            errors.append("Invalid grid step value")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'version': self.version,
            'database_units': self.database_units,
            'layers': {name: layer.to_dict() for name, layer in self.layers.items()},
            'via_rules': {name: rule.to_dict() for name, rule in self.via_rules.items()},
            'design_rules': self.design_rules.to_dict(),
            'grid_info': self.grid_info.to_dict()
        }
    
    def save_to_file(self, filename: str):
        """Save technology database to JSON file"""
        data = self.to_dict()
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TechnologyDB':
        """Create technology database from dictionary"""
        tech_db = cls(
            name=data.get('name', ''),
            version=data.get('version', ''),
            database_units=data.get('database_units', 1000.0)
        )
        
        # Load layers
        for layer_data in data.get('layers', {}).values():
            layer = Layer(
                name=layer_data['name'],
                layer_type=LayerType(layer_data['type']),
                direction=Direction(layer_data['direction']) if layer_data.get('direction') else None,
                min_width=layer_data.get('min_width', 0.0),
                min_spacing=layer_data.get('min_spacing', 0.0),
                pitch=layer_data.get('pitch', 0.0),
                offset=layer_data.get('offset', 0.0),
                thickness=layer_data.get('thickness', 0.0),
                resistance=layer_data.get('resistance', 0.0),
                capacitance=layer_data.get('capacitance', 0.0)
            )
            tech_db.add_layer(layer)
        
        # Load via rules
        for rule_data in data.get('via_rules', {}).values():
            via_rule = ViaRule(
                name=rule_data['name'],
                layers=rule_data['layers'],
                enclosure=rule_data.get('enclosure', {}),
                spacing=rule_data.get('spacing', 0.0),
                width=rule_data.get('width', 0.0),
                height=rule_data.get('height', 0.0),
                resistance=rule_data.get('resistance', 0.0)
            )
            tech_db.add_via_rule(via_rule)
        
        # Load design rules
        if 'design_rules' in data:
            dr_data = data['design_rules']
            tech_db.design_rules = DesignRules(
                min_spacing=dr_data.get('min_spacing', {}),
                min_width=dr_data.get('min_width', {}),
                via_spacing=dr_data.get('via_spacing', {}),
                enclosure_rules=dr_data.get('enclosure_rules', {})
            )
        
        # Load grid info
        if 'grid_info' in data:
            gi_data = data['grid_info']
            tech_db.grid_info = GridInfo(
                grid_step=gi_data.get('grid_step', 0.0),
                offset_x=gi_data.get('offset_x', 0.0),
                offset_y=gi_data.get('offset_y', 0.0),
                symmetry_axis_x=gi_data.get('symmetry_axis_x')
            )
        
        return tech_db