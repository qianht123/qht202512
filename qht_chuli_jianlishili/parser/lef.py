"""
LEF (Library Exchange Format) parser
"""

import re
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ..core.technology import TechnologyDB, Layer, ViaRule, LayerType, Direction


class LefParser:
    """LEF file parser"""
    
    def __init__(self):
        self.tech_db = TechnologyDB()
        self.current_section = None
        self.layer_stack = []
        self.units = 1000.0  # Default units per micron
        
    def parse(self, filename: str) -> TechnologyDB:
        """Parse LEF file and return TechnologyDB"""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"LEF file not found: {filename}")
        
        with open(filename, 'r') as f:
            content = f.read()
        
        # Preprocess: remove comments and handle case insensitivity
        content = self._preprocess_content(content)
        
        # Parse sections
        self._parse_units(content)
        self._parse_layers(content)
        self._parse_viarules(content)
        self._parse_properties(content)
        
        # Validate the parsed data
        errors = self.tech_db.validate()
        if errors:
            print(f"Warning: LEF parsing found {len(errors)} issues:")
            for error in errors[:5]:
                print(f"  - {error}")
        
        return self.tech_db
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess LEF content"""
        # Remove comments
        content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
        
        # Convert to uppercase for case-insensitive parsing
        # Keep string literals in quotes as-is
        lines = content.split('\n')
        processed_lines = []
        in_quotes = False
        
        for line in lines:
            processed_line = []
            i = 0
            while i < len(line):
                if line[i] == '"' and (i == 0 or line[i-1] != '\\'):
                    in_quotes = not in_quotes
                    processed_line.append(line[i])
                elif not in_quotes and line[i].isalpha():
                    processed_line.append(line[i].upper())
                else:
                    processed_line.append(line[i])
                i += 1
            processed_lines.append(''.join(processed_line))
        
        return '\n'.join(processed_lines)
    
    def _parse_units(self, content: str):
        """Parse UNITS section"""
        units_pattern = r'UNITS\s*;(.*?)\s*END\s+UNITS'
        units_match = re.search(units_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if units_match:
            units_section = units_match.group(1)
            
            # Parse database units
            db_pattern = r'DATABASE\s+UNITS\s+(\d+(?:\.\d+)?)\s*;'
            db_match = re.search(db_pattern, units_section)
            if db_match:
                self.units = float(db_match.group(1))
                self.tech_db.database_units = self.units
    
    def _parse_layers(self, content: str):
        """Parse LAYER sections"""
        layer_pattern = r'LAYER\s+(\w+)\s*;(.*?)\s*END\s+\1'
        
        for match in re.finditer(layer_pattern, content, re.DOTALL | re.IGNORECASE):
            layer_name = match.group(1)
            layer_section = match.group(2)
            
            layer = self._parse_single_layer(layer_name, layer_section)
            if layer:
                self.tech_db.add_layer(layer)
                self.layer_stack.append(layer_name)
    
    def _parse_single_layer(self, layer_name: str, layer_section: str) -> Optional[Layer]:
        """Parse a single LAYER section"""
        # Determine layer type
        layer_type = LayerType.ROUTING  # Default
        
        if 'TYPE' in layer_section:
            type_pattern = r'TYPE\s+(\w+)'
            type_match = re.search(type_pattern, layer_section)
            if type_match:
                type_str = type_match.group(1).upper()
                if type_str == 'ROUTING':
                    layer_type = LayerType.ROUTING
                elif type_str == 'CUT':
                    layer_type = LayerType.CUT
                elif type_str == 'MASTERSLICE':
                    layer_type = LayerType.MASTERSLICE
                elif type_str == 'OVERLAP':
                    layer_type = LayerType.OVERLAP
                elif type_str == 'IMPLANT':
                    layer_type = LayerType.IMPLANT
        
        # Parse direction for routing layers
        direction = None
        if layer_type == LayerType.ROUTING and 'DIRECTION' in layer_section:
            dir_pattern = r'DIRECTION\s+(\w+)'
            dir_match = re.search(dir_pattern, layer_section)
            if dir_match:
                dir_str = dir_match.group(1).upper()
                if dir_str == 'HORIZONTAL':
                    direction = Direction.HORIZONTAL
                elif dir_str == 'VERTICAL':
                    direction = Direction.VERTICAL
        
        # Parse minimum width
        min_width = 0.0
        if 'WIDTH' in layer_section:
            width_pattern = r'WIDTH\s+(\d+(?:\.\d+)?)'
            width_match = re.search(width_pattern, layer_section)
            if width_match:
                min_width = float(width_match.group(1))
        
        # Parse spacing
        min_spacing = 0.0
        if 'SPACING' in layer_section:
            spacing_pattern = r'SPACING\s+(\d+(?:\.\d+)?)'
            spacing_match = re.search(spacing_pattern, layer_section)
            if spacing_match:
                min_spacing = float(spacing_match.group(1))
        
        # Parse pitch
        pitch = 0.0
        if 'PITCH' in layer_section:
            pitch_pattern = r'PITCH\s+(\d+(?:\.\d+)?)'
            pitch_match = re.search(pitch_pattern, layer_section)
            if pitch_match:
                pitch = float(pitch_match.group(1))
        
        # Parse offset
        offset = 0.0
        if 'OFFSET' in layer_section:
            offset_pattern = r'OFFSET\s+(\d+(?:\.\d+)?)'
            offset_match = re.search(offset_pattern, layer_section)
            if offset_match:
                offset = float(offset_match.group(1))
        
        # Parse resistance and capacitance
        resistance = 0.0
        capacitance = 0.0
        
        if 'RESISTANCE' in layer_section:
            res_pattern = r'RESISTANCE\s+RPERSQ\s+(\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?)'
            res_match = re.search(res_pattern, layer_section)
            if res_match:
                resistance = float(res_match.group(1))
        
        if 'CAPACITANCE' in layer_section:
            cap_pattern = r'CAPACITANCE\s+CPERSQDIST\s+(\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?)'
            cap_match = re.search(cap_pattern, layer_section)
            if cap_match:
                capacitance = float(cap_match.group(1))
        
        return Layer(
            name=layer_name,
            layer_type=layer_type,
            direction=direction,
            min_width=min_width,
            min_spacing=min_spacing,
            pitch=pitch,
            offset=offset,
            resistance=resistance,
            capacitance=capacitance
        )
    
    def _parse_viarules(self, content: str):
        """Parse VIARULE sections"""
        viarule_pattern = r'VIARULE\s+(\w+)\s+(GENERATE\s+DEFAULT|GENERATE|DEFAULT)\s*;(.*?)\s*END\s+\1'
        
        for match in re.finditer(viarule_pattern, content, re.DOTALL | re.IGNORECASE):
            rule_name = match.group(1)
            rule_type = match.group(2)
            rule_section = match.group(3)
            
            via_rule = self._parse_single_viarule(rule_name, rule_section)
            if via_rule:
                self.tech_db.add_via_rule(via_rule)
    
    def _parse_single_viarule(self, rule_name: str, rule_section: str) -> Optional[ViaRule]:
        """Parse a single VIARULE section"""
        layers = []
        enclosure = {}
        spacing = 0.0
        width = 0.0
        height = 0.0
        
        # Parse layers
        layer_pattern = r'LAYER\s+(\w+)\s*;(.*?)(?=LAYER|END)'
        for layer_match in re.finditer(layer_pattern, rule_section, re.DOTALL | re.IGNORECASE):
            layer_name = layer_match.group(1)
            layer_info = layer_match.group(2)
            layers.append(layer_name)
            
            # Parse enclosure for this layer
            enclosure_pattern = r'ENCLOSURE\s+([\d.]+)\s+([\d.]+)'
            enclosure_match = re.search(enclosure_pattern, layer_info)
            if enclosure_match:
                enclosure[layer_name] = {
                    'overhang1': float(enclosure_match.group(1)),
                    'overhang2': float(enclosure_match.group(2))
                }
            
            # Parse width for this layer
            width_pattern = r'WIDTH\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)'
            width_match = re.search(width_pattern, layer_info)
            if width_match:
                enclosure[layer_name]['width_min'] = float(width_match.group(1))
                enclosure[layer_name]['width_max'] = float(width_match.group(2))
        
        # Parse via/cut layer rectangle and spacing
        rect_pattern = r'RECT\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)'
        rect_match = re.search(rect_pattern, rule_section)
        if rect_match:
            x1, y1, x2, y2 = map(float, rect_match.groups())
            width = abs(x2 - x1)
            height = abs(y2 - y1)
        
        # Parse spacing
        spacing_pattern = r'SPACING\s+([\d.]+)\s+BY\s+([\d.]+)'
        spacing_match = re.search(spacing_pattern, rule_section)
        if spacing_match:
            spacing = float(spacing_match.group(1))
        
        return ViaRule(
            name=rule_name,
            layers=layers,
            enclosure=enclosure,
            spacing=spacing,
            width=width,
            height=height
        )
    
    def _parse_properties(self, content: str):
        """Parse other properties and settings"""
        # Parse manufacturing grid
        grid_pattern = r'MANUFACTURINGGRID\s+(\d+(?:\.\d+)?)'
        grid_match = re.search(grid_pattern, content)
        if grid_match:
            grid_value = float(grid_match.group(1))
            self.tech_db.grid_info.grid_step = grid_value
        
        # Parse library name and version
        lib_pattern = r'LIBRARY\s+(\w+)\s*;(.*?)\s*END\s+LIBRARY'
        lib_match = re.search(lib_pattern, content, re.DOTALL | re.IGNORECASE)
        if lib_match:
            self.tech_db.name = lib_match.group(1)
            
            # Look for version in library section
            lib_section = lib_match.group(2)
            version_pattern = r'VERSION\s+"([^"]*)"'
            version_match = re.search(version_pattern, lib_section)
            if version_match:
                self.tech_db.version = version_match.group(1)


# Test function
if __name__ == "__main__":
    # Create a simple test LEF content
    test_lef = """
LIBRARY TEST_LIB VERSION "0.1"

UNITS ;
DATABASE UNITS 1000 ;
END UNITS

LAYER METAL1 TYPE ROUTING ;
DIRECTION HORIZONTAL ;
WIDTH 0.1 ;
SPACING 0.1 ;
PITCH 0.2 ;
END METAL1

LAYER METAL2 TYPE ROUTING ;
DIRECTION VERTICAL ;
WIDTH 0.1 ;
SPACING 0.1 ;
PITCH 0.2 ;
END METAL2

LAYER VIA1 TYPE CUT ;
WIDTH 0.06 ;
SPACING 0.06 ;
END VIA1

VIARULE M1_M2 GENERATE DEFAULT ;
LAYER METAL1 ;
ENCLOSURE 0.03 0.03 ;
LAYER METAL2 ;
ENCLOSURE 0.03 0.03 ;
LAYER VIA1 ;
RECT -0.025 -0.025 0.025 0.025 ;
SPACING 0.13 BY 0.13 ;
END M1_M2

END LIBRARY
"""
    
    # Write test file
    with open("test.lef", "w") as f:
        f.write(test_lef)
    
    # Parse LEF
    parser = LefParser()
    tech_db = parser.parse("test.lef")
    
    print(f"Parsed technology: {tech_db.name} v{tech_db.version}")
    print(f"Database units: {tech_db.database_units}")
    print(f"Layers: {list(tech_db.layers.keys())}")
    print(f"Via rules: {list(tech_db.via_rules.keys())}")
    
    # Clean up
    os.remove("test.lef")