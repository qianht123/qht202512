"""
Technology file parser for simple tech file format
"""

import re
import os
from typing import Dict, List, Optional, Any, Tuple

from ..core.technology import TechnologyDB, GridInfo


class TechfileParser:
    """Simple technology file parser"""
    
    def __init__(self):
        self.tech_db = None
        
    def parse(self, filename: str, tech_db: TechnologyDB) -> TechnologyDB:
        """Parse technology file and update TechnologyDB"""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Technology file not found: {filename}")
        
        self.tech_db = tech_db
        
        with open(filename, 'r') as f:
            content = f.read()
        
        # Parse different sections
        self._parse_grid_info(content)
        self._parse_design_rules(content)
        self._parse_layer_rules(content)
        
        return self.tech_db
    
    def _parse_grid_info(self, content: str):
        """Parse grid information"""
        # Look for grid step
        grid_pattern = r'GRID[_\s]*STEP\s*[:=]\s*([\d.]+)'
        grid_match = re.search(grid_pattern, content, re.IGNORECASE)
        if grid_match:
            self.tech_db.grid_info.grid_step = float(grid_match.group(1))
        
        # Look for offset
        offset_x_pattern = r'OFFSET[_\s]*X\s*[:=]\s*([\d.-]+)'
        offset_x_match = re.search(offset_x_pattern, content, re.IGNORECASE)
        if offset_x_match:
            self.tech_db.grid_info.offset_x = float(offset_x_match.group(1))
        
        offset_y_pattern = r'OFFSET[_\s]*Y\s*[:=]\s*([\d.-]+)'
        offset_y_match = re.search(offset_y_pattern, content, re.IGNORECASE)
        if offset_y_match:
            self.tech_db.grid_info.offset_y = float(offset_y_match.group(1))
        
        # Look for symmetry axis
        symmetry_pattern = r'SYMMETRY[_\s]*AXIS[_\s]*X\s*[:=]\s*([\d.-]+)'
        symmetry_match = re.search(symmetry_pattern, content, re.IGNORECASE)
        if symmetry_match:
            self.tech_db.grid_info.symmetry_axis_x = float(symmetry_match.group(1))
    
    def _parse_design_rules(self, content: str):
        """Parse design rules"""
        # Parse minimum spacing rules
        spacing_pattern = r'MIN[_\s]*SPACING\s+(\w+)\s*[:=]\s*([\d.]+)'
        for match in re.finditer(spacing_pattern, content, re.IGNORECASE):
            layer_name = match.group(1)
            spacing = float(match.group(2))
            self.tech_db.design_rules.min_spacing[layer_name] = spacing
        
        # Parse minimum width rules
        width_pattern = r'MIN[_\s]*WIDTH\s+(\w+)\s*[:=]\s*([\d.]+)'
        for match in re.finditer(width_pattern, content, re.IGNORECASE):
            layer_name = match.group(1)
            width = float(match.group(2))
            self.tech_db.design_rules.min_width[layer_name] = width
        
        # Parse via spacing rules
        via_spacing_pattern = r'VIA[_\s]*SPACING\s+(\w+)\s*[:=]\s*([\d.]+)'
        for match in re.finditer(via_spacing_pattern, content, re.IGNORECASE):
            via_name = match.group(1)
            spacing = float(match.group(2))
            self.tech_db.design_rules.via_spacing[via_name] = spacing
    
    def _parse_layer_rules(self, content: str):
        """Parse layer-specific rules"""
        # Parse enclosure rules
        enclosure_pattern = r'ENCLOSURE\s+(\w+)\s+(\w+)\s*[:=]\s*([\d.]+)\s*([\d.]+)'
        for match in re.finditer(enclosure_pattern, content, re.IGNORECASE):
            via_name = match.group(1)
            layer_name = match.group(2)
            overhang1 = float(match.group(3))
            overhang2 = float(match.group(4))
            
            if via_name not in self.tech_db.design_rules.enclosure_rules:
                self.tech_db.design_rules.enclosure_rules[via_name] = {}
            
            self.tech_db.design_rules.enclosure_rules[via_name][layer_name] = {
                'overhang1': overhang1,
                'overhang2': overhang2
            }


# Test function
if __name__ == "__main__":
    # Create a simple test tech file
    test_tech = """
# Technology file for test process
# Grid information
GRID_STEP = 0.02
OFFSET_X = 0.0
OFFSET_Y = 0.0
SYMMETRY_AXIS_X = 159.0

# Design rules
MIN_SPACING METAL1 = 0.1
MIN_SPACING METAL2 = 0.1
MIN_SPACING VIA1 = 0.06

MIN_WIDTH METAL1 = 0.1
MIN_WIDTH METAL2 = 0.1
MIN_WIDTH VIA1 = 0.06

VIA_SPACING VIA1 = 0.13

# Enclosure rules
ENCLOSURE M1_M2 METAL1 = 0.03 0.03
ENCLOSURE M1_M2 METAL2 = 0.03 0.03
"""
    
    # Write test file
    with open("test.tech", "w") as f:
        f.write(test_tech)
    
    # Parse tech file
    from ..core.technology import TechnologyDB
    tech_db = TechnologyDB()
    parser = TechfileParser()
    parser.parse("test.tech", tech_db)
    
    print(f"Grid step: {tech_db.grid_info.grid_step}")
    print(f"Symmetry axis: {tech_db.grid_info.symmetry_axis_x}")
    print(f"Min spacing rules: {tech_db.design_rules.min_spacing}")
    print(f"Enclosure rules: {tech_db.design_rules.enclosure_rules}")
    
    # Clean up
    os.remove("test.tech")