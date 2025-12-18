"""
Configuration file parser
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Configuration file handler"""
    
    # Input files
    spectre_netlist: str = ""
    hspice_netlist: str = ""
    result_dir: str = "./results"
    
    # Technology files
    techfile: str = ""
    simple_tech_file: str = ""
    lef: str = ""
    
    # Constraint files
    symnet_file: str = ""
    iopin_file: str = ""
    bound_file: str = ""
    pin_file: str = ""
    
    # Optional files
    power_file: str = ""
    gr_file: str = ""
    gr_spec_file: str = ""
    
    # Parameters
    grid_step: float = 1.0
    database_units: float = 1000.0
    symmetry_axis: Optional[float] = None
    
    # Standard cells
    std_cells: list = field(default_factory=list)
    
    # Additional settings
    debug_mode: bool = False
    verbose: bool = True
    max_iterations: int = 1000
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration"""
        if config_file:
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file: str):
        """Load configuration from JSON file"""
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        # Update configuration with loaded data
        for key, value in config_data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                print(f"Warning: Unknown configuration key: {key}")
    
    def save_to_file(self, config_file: str):
        """Save configuration to JSON file"""
        config_data = self.to_dict()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'spectre_netlist': self.spectre_netlist,
            'hspice_netlist': self.hspice_netlist,
            'result_dir': self.result_dir,
            'techfile': self.techfile,
            'simple_tech_file': self.simple_tech_file,
            'lef': self.lef,
            'symnet_file': self.symnet_file,
            'iopin_file': self.iopin_file,
            'bound_file': self.bound_file,
            'pin_file': self.pin_file,
            'power_file': self.power_file,
            'gr_file': self.gr_file,
            'gr_spec_file': self.gr_spec_file,
            'grid_step': self.grid_step,
            'database_units': self.database_units,
            'symmetry_axis': self.symmetry_axis,
            'std_cells': self.std_cells,
            'debug_mode': self.debug_mode,
            'verbose': self.verbose,
            'max_iterations': self.max_iterations
        }
    
    def validate(self) -> list:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Check required files
        if not self.spectre_netlist and not self.hspice_netlist:
            errors.append("Either spectre_netlist or hspice_netlist must be specified")
        
        if not self.techfile:
            errors.append("techfile must be specified")
        
        if not self.lef:
            errors.append("lef file must be specified")
        
        # Check file existence
        files_to_check = [
            (self.spectre_netlist, "spectre_netlist"),
            (self.hspice_netlist, "hspice_netlist"),
            (self.techfile, "techfile"),
            (self.simple_tech_file, "simple_tech_file"),
            (self.lef, "lef"),
            (self.symnet_file, "symnet_file"),
            (self.iopin_file, "iopin_file"),
        ]
        
        for file_path, file_type in files_to_check:
            if file_path and not os.path.exists(file_path):
                errors.append(f"{file_type} file not found: {file_path}")
        
        # Check parameters
        if self.grid_step <= 0:
            errors.append("grid_step must be positive")
        
        if self.database_units <= 0:
            errors.append("database_units must be positive")
        
        # Check result directory
        if self.result_dir:
            try:
                os.makedirs(self.result_dir, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create result directory {self.result_dir}: {str(e)}")
        
        return errors
    
    def get_netlist_file(self) -> str:
        """Get the netlist file (spectre or hspice)"""
        return self.spectre_netlist or self.hspice_netlist
    
    def get_netlist_type(self) -> str:
        """Get the netlist type ('spectre' or 'hspice')"""
        if self.spectre_netlist:
            return 'spectre'
        elif self.hspice_netlist:
            return 'hspice'
        else:
            return 'unknown'
    
    def resolve_paths(self, base_dir: str = None):
        """Resolve relative paths based on base directory"""
        if base_dir is None:
            # Use directory of config file as base
            base_dir = "."
        
        base_path = Path(base_dir).resolve()
        
        # List of path attributes to resolve
        path_attrs = [
            'spectre_netlist', 'hspice_netlist', 'techfile', 
            'simple_tech_file', 'lef', 'symnet_file', 
            'iopin_file', 'bound_file', 'pin_file', 
            'power_file', 'gr_file', 'gr_spec_file'
        ]
        
        for attr in path_attrs:
            path_value = getattr(self, attr)
            if path_value and not os.path.isabs(path_value):
                # Resolve relative path
                resolved_path = (base_path / path_value).resolve()
                setattr(self, attr, str(resolved_path))
    
    def print_summary(self):
        """Print configuration summary"""
        print("=== Configuration Summary ===")
        print(f"Netlist: {self.get_netlist_file()} ({self.get_netlist_type()})")
        print(f"Technology: {self.techfile}")
        print(f"LEF file: {self.lef}")
        print(f"Result directory: {self.result_dir}")
        print(f"Grid step: {self.grid_step}")
        print(f"Database units: {self.database_units}")
        if self.symmetry_axis:
            print(f"Symmetry axis: {self.symmetry_axis}")
        print("============================")


# Example usage and test
if __name__ == "__main__":
    # Create a sample configuration
    config = Config()
    config.spectre_netlist = "examples/qht10_or/qht10.sp"
    config.techfile = "examples/t40PDK/t40.techfile"
    config.simple_tech_file = "examples/t40PDK/techfile.simple"
    config.lef = "examples/t40PDK/t40.lef"
    config.result_dir = "./results"
    config.grid_step = 0.02
    config.database_units = 1000.0
    
    # Save configuration
    config.save_to_file("sample_config.json")
    print("Sample configuration saved to sample_config.json")
    
    # Load and validate
    new_config = Config("sample_config.json")
    errors = new_config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid")
        new_config.print_summary()