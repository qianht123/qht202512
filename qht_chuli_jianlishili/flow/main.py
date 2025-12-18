"""
Main flow controller for Magical Flow
"""

import os
import time
from typing import Optional

from ..parser.config import Config
from ..parser.netlist import create_parser
from ..parser.lef import LefParser
from ..parser.techfile import TechfileParser
from ..parser.gds import GdsWriter
from ..core.circuit import Circuit
from ..core.technology import TechnologyDB
from ..buju.adapters.circuit_adapter import CircuitAdapter
from ..buju.constraint.symmetry import AdvancedSymmetryDetector
from ..buju.constraint.parser_fixed import SymmetryParser


class MagicalFlow:
    """Main flow controller"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the flow"""
        self.config = Config(config_file) if config_file else Config()
        self.circuit = None
        self.technology_db = None
        self.start_time = None
        self.symmetry_constraint = None
        
    def run(self) -> bool:
        """Run the complete flow"""
        self.start_time = time.time()
        
        try:
            # Step 1: Validate configuration
            print("Step 1: Validating configuration...")
            errors = self.config.validate()
            if errors:
                print("Configuration errors found:")
                for error in errors:
                    print(f"  - {error}")
                return False
            
            # Step 2: Parse inputs
            print("\nStep 2: Parsing input files...")
            if not self._parse_inputs():
                return False
            
            # Step 3: Preprocess
            print("\nStep 3: Preprocessing...")
            if not self._preprocess():
                return False
            
            # Step 4: Symmetry Detection
            print("\nStep 4: Performing symmetry detection...")
            if not self._perform_symmetry_detection():
                return False
            
            # Step 5: Placement
            print("\nStep 5: Performing placement...")
            if not self._perform_placement():
                return False
            
            # Step 6: Routing
            print("\nStep 6: Performing routing...")
            if not self._perform_routing():
                return False
            
            # Step 7: Generate output
            print("\nStep 7: Generating output...")
            if not self._generate_output():
                return False
            
            # Success
            elapsed_time = time.time() - self.start_time
            print(f"\nFlow completed successfully in {elapsed_time:.2f} seconds")
            return True
            
        except Exception as e:
            print(f"\nFlow failed with error: {str(e)}")
            if self.config.debug_mode:
                import traceback
                traceback.print_exc()
            return False
    
    def _parse_inputs(self) -> bool:
        """Parse all input files"""
        try:
            # Parse netlist
            netlist_file = self.config.get_netlist_file()
            netlist_type = self.config.get_netlist_type()
            
            print(f"  Parsing netlist: {netlist_file} ({netlist_type})")
            parser = create_parser(netlist_type)
            self.circuit = parser.parse(netlist_file)
            
            print(f"  Parsed circuit: {self.circuit.name}")
            print(f"  Devices: {len(self.circuit.devices)}")
            print(f"  Nets: {len(self.circuit.nets)}")
            
            # Parse LEF file
            print(f"  Parsing LEF file: {self.config.lef}")
            lef_parser = LefParser()
            self.technology_db = lef_parser.parse(self.config.lef)
            
            print(f"  Parsed technology: {self.technology_db.name}")
            print(f"  Layers: {len(self.technology_db.layers)}")
            print(f"  Via rules: {len(self.technology_db.via_rules)}")
            
            # Parse technology files
            if self.config.techfile and os.path.exists(self.config.techfile):
                print(f"  Parsing tech file: {self.config.techfile}")
                tech_parser = TechfileParser()
                tech_parser.parse(self.config.techfile, self.technology_db)
            
            if self.config.simple_tech_file and os.path.exists(self.config.simple_tech_file):
                print(f"  Parsing simple tech file: {self.config.simple_tech_file}")
                tech_parser = TechfileParser()
                tech_parser.parse(self.config.simple_tech_file, self.technology_db)
            
            return True
            
        except Exception as e:
            print(f"  Error parsing inputs: {str(e)}")
            return False
    
    def _preprocess(self) -> bool:
        """Preprocess the design"""
        try:
            # Validate circuit connections
            print("  Validating circuit connections...")
            errors = self.circuit.validate_connections()
            if errors:
                print(f"  Found {len(errors)} connection issues:")
                for error in errors[:5]:  # Show first 5
                    print(f"    - {error}")
                if len(errors) > 5:
                    print(f"    ... and {len(errors) - 5} more")
            
            # Classify nets
            print("  Classifying nets...")
            power_nets = self.circuit.get_power_nets()
            ground_nets = self.circuit.get_ground_nets()
            signal_nets = self.circuit.get_signal_nets()
            
            print(f"    Power nets: {len(power_nets)}")
            print(f"    Ground nets: {len(ground_nets)}")
            print(f"    Signal nets: {len(signal_nets)}")
            
            # Set net weights
            for net in power_nets + ground_nets:
                net.weight = 10.0  # Higher weight for power/ground nets
                net.is_critical = True
            
            # Validate technology database
            print("  Validating technology database...")
            tech_errors = self.technology_db.validate()
            if tech_errors:
                print(f"  Found {len(tech_errors)} technology issues:")
                for error in tech_errors[:5]:
                    print(f"    - {error}")
            
            return True
            
        except Exception as e:
            print(f"  Error in preprocessing: {str(e)}")
            return False
    
    def _perform_symmetry_detection(self) -> bool:
        """Perform symmetry detection using the new adapter"""
        try:
            print("  Initializing circuit adapter...")
            adapter = CircuitAdapter(debug_mode=self.config.debug_mode)
            
            # Get circuit summary
            summary = adapter.get_conversion_summary(self.circuit)
            print(f"  Circuit summary: {summary['total_devices']} devices, {summary['total_nets']} nets")
            print(f"  Device types: {summary['device_types']}")
            
            # Test conversion first
            print("  Testing circuit conversion...")
            if not adapter.test_conversion(self.circuit):
                print("  Warning: Circuit conversion test failed, but continuing...")
            
            # Convert circuit to symmetry format
            print("  Converting circuit to symmetry format...")
            devices_dict, nets_dict = adapter.convert_to_symmetry_format(self.circuit)
            
            # Perform symmetry detection
            print("  Detecting symmetry constraints...")
            detector = AdvancedSymmetryDetector()
            self.symmetry_constraint = detector.detect(devices_dict, nets_dict)
            
            # Report results
            symmetry_pairs = len(self.symmetry_constraint.symmetry_pairs)
            print(f"  Detected {symmetry_pairs} symmetry pairs")
            
            if symmetry_pairs > 0:
                print("  Symmetry pairs found:")
                for i, pair in enumerate(self.symmetry_constraint.symmetry_pairs[:5]):  # Show first 5
                    print(f"    {i+1}. {pair.device1} <-> {pair.device2} ({pair.symmetry_type.value}, score: {pair.score:.2f})")
                if symmetry_pairs > 5:
                    print(f"    ... and {symmetry_pairs - 5} more")
                
                # Generate symmetry file
                os.makedirs(self.config.result_dir, exist_ok=True)
                symmetry_file = os.path.join(self.config.result_dir, "symmetry.sym")
                
                parser = SymmetryParser()
                parser.generate_symmetry_file(self.symmetry_constraint, symmetry_file)
                print(f"  Symmetry constraints saved to: {symmetry_file}")
            else:
                print("  No symmetry constraints detected")
            
            return True
            
        except Exception as e:
            print(f"  Error in symmetry detection: {str(e)}")
            if self.config.debug_mode:
                import traceback
                traceback.print_exc()
            # Continue without symmetry constraints
            self.symmetry_constraint = None
            return True
    
    def _perform_placement(self) -> bool:
        """Perform placement with symmetry constraints"""
        try:
            print("  Initializing placement...")
            
            if self.symmetry_constraint and len(self.symmetry_constraint.symmetry_pairs) > 0:
                print("  Performing symmetry-aware placement...")
                # TODO: Implement symmetry-aware placement algorithm
                # For now, use simple placement with symmetry consideration
                
                # Group symmetric pairs
                symmetric_groups = []
                processed_devices = set()
                
                for pair in self.symmetry_constraint.symmetry_pairs:
                    if pair.device1 not in processed_devices and pair.device2 not in processed_devices:
                        symmetric_groups.append((pair.device1, pair.device2, pair.symmetry_type))
                        processed_devices.add(pair.device1)
                        processed_devices.add(pair.device2)
                
                print(f"  Found {len(symmetric_groups)} symmetry groups")
                
                # Simple symmetric placement (placeholder)
                grid_size = 10.0  # Grid spacing in microns
                x, y = 0, 0
                devices_placed = 0
                
                # Place symmetric groups first
                for device1_name, device2_name, symmetry_type in symmetric_groups:
                    if device1_name in self.circuit.devices and device2_name in self.circuit.devices:
                        device1 = self.circuit.devices[device1_name]
                        device2 = self.circuit.devices[device2_name]
                        
                        # Simple symmetric placement
                        if symmetry_type.value in ["vertical", "differential"]:
                            # Place devices symmetrically around vertical axis
                            device1.position = Point(x - grid_size/2, y)
                            device2.position = Point(x + grid_size/2, y)
                        else:
                            # Default placement
                            device1.position = Point(x, y)
                            device2.position = Point(x + grid_size, y)
                        
                        # Set device sizes
                        for device in [device1, device2]:
                            if device.device_type in [DeviceType.NMOS, DeviceType.PMOS]:
                                device.width = 2.0
                                device.height = 1.0
                            else:
                                device.width = 1.0
                                device.height = 1.0
                        
                        x += grid_size * 2
                        devices_placed += 2
                        
                        # Move to next row if needed
                        if x > 50:  # Max width
                            x = 0
                            y += grid_size
                
                # Place remaining devices
                for device_name, device in self.circuit.devices.items():
                    if device_name not in processed_devices:
                        device.position = Point(x, y)
                        
                        if device.device_type in [DeviceType.NMOS, DeviceType.PMOS]:
                            device.width = 2.0
                            device.height = 1.0
                        else:
                            device.width = 1.0
                            device.height = 1.0
                        
                        x += grid_size
                        devices_placed += 1
                        
                        if x > 50:
                            x = 0
                            y += grid_size
                
                print(f"  Placed {devices_placed} devices with symmetry constraints")
                
            else:
                print("  Performing standard placement (no symmetry constraints)...")
                # Simple placement: place devices in a grid
                grid_size = 10.0  # Grid spacing in microns
                x, y = 0, 0
                devices_placed = 0
                
                for device in self.circuit.devices.values():
                    # Simple grid placement
                    device.position = Point(x, y)
                    
                    # Set device size (for demonstration)
                    if device.device_type in [DeviceType.NMOS, DeviceType.PMOS]:
                        device.width = 2.0
                        device.height = 1.0
                    else:
                        device.width = 1.0
                        device.height = 1.0
                    
                    x += grid_size
                    devices_placed += 1
                    
                    # Move to next row if needed
                    if x > 50:  # Max width
                        x = 0
                        y += grid_size
                
                print(f"  Placed {devices_placed} devices")
            
            # Calculate circuit bounding box
            bbox = self.circuit.get_bounding_box()
            if bbox:
                print(f"  Circuit bounding box: ({bbox.lower_left.x}, {bbox.lower_left.y}) to ({bbox.upper_right.x}, {bbox.upper_right.y})")
            
            return True
            
        except Exception as e:
            print(f"  Error in placement: {str(e)}")
            return False
    
    def _perform_routing(self) -> bool:
        """Perform routing (placeholder)"""
        try:
            print("  Initializing routing...")
            
            # For now, just report routing statistics
            nets_to_route = len(self.circuit.nets)
            critical_nets = sum(1 for net in self.circuit.nets.values() if net.is_critical)
            
            print(f"  Nets to route: {nets_to_route}")
            print(f"  Critical nets: {critical_nets}")
            
            # Placeholder routing would go here
            print("  Routing completed (placeholder)")
            
            return True
            
        except Exception as e:
            print(f"  Error in routing: {str(e)}")
            return False
    
    def _generate_output(self) -> bool:
        """Generate output files"""
        try:
            # Create result directory
            os.makedirs(self.config.result_dir, exist_ok=True)
            
            # Generate GDS file
            output_gds = os.path.join(self.config.result_dir, "output.gds")
            print(f"  Generating GDS file: {output_gds}")
            
            writer = GdsWriter()
            writer.write(self.circuit, output_gds, self.technology_db)
            
            # Generate report
            report_file = os.path.join(self.config.result_dir, "report.txt")
            print(f"  Generating report: {report_file}")
            
            with open(report_file, 'w') as f:
                f.write("Magical Flow Report\n")
                f.write("==================\n\n")
                f.write(f"Circuit: {self.circuit.name}\n")
                f.write(f"Devices: {len(self.circuit.devices)}\n")
                f.write(f"Nets: {len(self.circuit.nets)}\n\n")
                
                f.write("Device Summary:\n")
                for device_type in [DeviceType.NMOS, DeviceType.PMOS, DeviceType.RESISTOR, DeviceType.CAPACITOR]:
                    devices = self.circuit.get_devices_by_type(device_type)
                    f.write(f"  {device_type.value}: {len(devices)}\n")
                
                f.write("\nNet Summary:\n")
                f.write(f"  Power nets: {len(self.circuit.get_power_nets())}\n")
                f.write(f"  Ground nets: {len(self.circuit.get_ground_nets())}\n")
                f.write(f"  Signal nets: {len(self.circuit.get_signal_nets())}\n")
                
                # Add symmetry information
                if self.symmetry_constraint:
                    f.write(f"\nSymmetry Constraints:\n")
                    f.write(f"  Symmetry pairs: {len(self.symmetry_constraint.symmetry_pairs)}\n")
                    if hasattr(self.symmetry_constraint, 'symmetry_axis') and self.symmetry_constraint.symmetry_axis:
                        f.write(f"  Symmetry axis: {self.symmetry_constraint.symmetry_axis}\n")
                    
                    if len(self.symmetry_constraint.symmetry_pairs) > 0:
                        f.write(f"  Symmetry pairs:\n")
                        for i, pair in enumerate(self.symmetry_constraint.symmetry_pairs):
                            f.write(f"    {i+1}. {pair.device1} <-> {pair.device2} ({pair.symmetry_type.value}, score: {pair.score:.2f})\n")
                else:
                    f.write(f"\nSymmetry Constraints: None detected\n")
                
                if self.start_time:
                    elapsed_time = time.time() - self.start_time
                    f.write(f"\nTotal runtime: {elapsed_time:.2f} seconds\n")
            
            print("  Output generation completed")
            return True
            
        except Exception as e:
            print(f"  Error generating output: {str(e)}")
            return False


# Import required modules
from ..core.geometry import Point
from ..core.circuit import DeviceType
