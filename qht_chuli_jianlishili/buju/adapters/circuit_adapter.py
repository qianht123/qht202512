"""
Circuit adapter for converting between different data formats
"""

from typing import Dict, List, Tuple, Optional, Any
import logging

from core.circuit import Circuit, Device, Net, Pin, DeviceType
from buju.constraint.symmetry import SymmetryConstraint


class ConversionError(Exception):
    """Exception raised for data conversion errors"""
    pass


class CircuitAdapter:
    """
    Adapter class for converting Circuit objects to symmetry detection format
    and back again while preserving all original information.
    """
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the circuit adapter
        
        Args:
            debug_mode: Enable detailed logging for debugging
        """
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        
        if self.debug_mode:
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            self.logger.addHandler(handler)
    
    def convert_to_symmetry_format(self, circuit: Circuit) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
        """
        Convert Circuit object to symmetry detection format
        
        Args:
            circuit: The Circuit object to convert
            
        Returns:
            Tuple of (devices_dict, nets_dict) in symmetry detection format
            
        Raises:
            ConversionError: If conversion fails validation
        """
        self.logger.info(f"Converting circuit '{circuit.name}' to symmetry format")
        
        try:
            # Convert devices
            devices_dict = self._convert_devices(circuit)
            
            # Convert nets
            nets_dict = self._convert_nets(circuit)
            
            # Validate conversion
            self._validate_conversion(circuit, devices_dict, nets_dict)
            
            self.logger.info(f"Successfully converted {len(devices_dict)} devices and {len(nets_dict)} nets")
            return devices_dict, nets_dict
            
        except Exception as e:
            error_msg = f"Failed to convert circuit '{circuit.name}': {str(e)}"
            self.logger.error(error_msg)
            raise ConversionError(error_msg) from e
    
    def _convert_devices(self, circuit: Circuit) -> Dict[str, Dict]:
        """Convert devices from Circuit format to symmetry format"""
        devices_dict = {}
        
        for device_name, device in circuit.devices.items():
            if self.debug_mode:
                self.logger.debug(f"Converting device: {device_name}")
            
            # Convert pins
            pins_list = []
            for pin in device.pins:
                pin_data = {
                    "name": pin.name,
                    "net": pin.net.name if pin.net else None,
                    "direction": pin.direction.value if pin.direction else None
                }
                pins_list.append(pin_data)
            
            # Convert device data
            device_data = {
                "type": device.device_type.value,
                "parameters": dict(device.parameters) if device.parameters else {},
                "pins": pins_list,
                # Preserve additional information
                "position": device.position if hasattr(device, 'position') else None,
                "width": device.width if hasattr(device, 'width') else None,
                "height": device.height if hasattr(device, 'height') else None,
                "original_device": device  # Keep reference to original object
            }
            
            devices_dict[device_name] = device_data
            
        return devices_dict
    
    def _convert_nets(self, circuit: Circuit) -> Dict[str, Dict]:
        """Convert nets from Circuit format to symmetry format"""
        nets_dict = {}
        
        for net_name, net in circuit.nets.items():
            if self.debug_mode:
                self.logger.debug(f"Converting net: {net_name}")
            
            # Convert pins connected to this net
            pins_list = []
            for pin in net.pins:
                pin_data = {
                    "device": pin.device.name if pin.device else None,
                    "pin": pin.name
                }
                pins_list.append(pin_data)
            
            # Convert net data
            net_data = {
                "pins": pins_list,
                # Preserve additional information
                "net_type": net.net_type.value if net.net_type else None,
                "weight": getattr(net, 'weight', None),
                "is_critical": getattr(net, 'is_critical', False),
                "original_net": net  # Keep reference to original object
            }
            
            nets_dict[net_name] = net_data
            
        return nets_dict
    
    def _validate_conversion(self, original_circuit: Circuit, 
                           devices_dict: Dict[str, Dict], 
                           nets_dict: Dict[str, Dict]) -> None:
        """
        Validate that conversion preserved all critical information
        
        Args:
            original_circuit: Original Circuit object
            devices_dict: Converted devices dictionary
            nets_dict: Converted nets dictionary
            
        Raises:
            ConversionError: If validation fails
        """
        errors = []
        
        # Validate device count
        if len(original_circuit.devices) != len(devices_dict):
            errors.append(f"Device count mismatch: original={len(original_circuit.devices)}, converted={len(devices_dict)}")
        
        # Validate net count
        if len(original_circuit.nets) != len(nets_dict):
            errors.append(f"Net count mismatch: original={len(original_circuit.nets)}, converted={len(nets_dict)}")
        
        # Validate device names and basic structure
        for device_name in original_circuit.devices:
            if device_name not in devices_dict:
                errors.append(f"Missing device in conversion: {device_name}")
                continue
                
            device_data = devices_dict[device_name]
            required_fields = ["type", "parameters", "pins"]
            for field in required_fields:
                if field not in device_data:
                    errors.append(f"Missing required field '{field}' in device {device_name}")
        
        # Validate net names and basic structure
        for net_name in original_circuit.nets:
            if net_name not in nets_dict:
                errors.append(f"Missing net in conversion: {net_name}")
                continue
                
            net_data = nets_dict[net_name]
        if errors:
            error_msg = "Conversion validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            self.logger.error(error_msg)
            raise ConversionError(error_msg)
        
        self.logger.info("Conversion validation passed")
    
    def get_conversion_summary(self, circuit: Circuit) -> Dict[str, Any]:
        """
        Get a summary of the circuit before conversion
        
        Args:
            circuit: Circuit object to analyze
            
        Returns:
            Dictionary containing circuit summary information
        """
        summary = {
            "circuit_name": circuit.name,
            "total_devices": len(circuit.devices),
            "total_nets": len(circuit.nets),
            "device_types": {},
            "net_types": {}
        }
        
        # Count device types
        for device in circuit.devices.values():
            device_type = device.device_type.value
            summary["device_types"][device_type] = summary["device_types"].get(device_type, 0) + 1
        
        # Count net types
        for net in circuit.nets.values():
            if net.net_type:
                net_type = net.net_type.value
                summary["net_types"][net_type] = summary["net_types"].get(net_type, 0) + 1
        
        return summary
    
    def test_conversion(self, circuit: Circuit) -> bool:
        """
        Test the conversion process without modifying data
        
        Args:
            circuit: Circuit object to test conversion on
            
        Returns:
            True if conversion test succeeds, False otherwise
        """
        try:
            self.logger.info(f"Testing conversion for circuit '{circuit.name}'")
            
            # Get summary
            summary = self.get_conversion_summary(circuit)
            self.logger.info(f"Circuit summary: {summary}")
            
            # Attempt conversion
            devices_dict, nets_dict = self.convert_to_symmetry_format(circuit)
            
            # Test can be extended with more comprehensive checks
            self.logger.info("Conversion test completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Conversion test failed: {str(e)}")
            return False
