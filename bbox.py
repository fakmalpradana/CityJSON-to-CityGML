#!/usr/bin/env python3
"""
CityGML v1 Bounding Box Calculator with In-Place Insertion
Calculates bounding box and inserts it into the original CityGML file
"""

import xml.etree.ElementTree as ET
import sys
import os
from typing import List, Tuple, Optional
import re
import shutil
from datetime import datetime

class CityGMLBoundingBoxCalculator:
    def __init__(self):
        self.namespaces = {
            'gml': 'http://www.opengis.net/gml',
            'citygml': 'http://www.citygml.org/citygml/1/0/0',
            'bldg': 'http://www.citygml.org/citygml/building/1/0/0',
            'gen': 'http://www.citygml.org/citygml/generics/1/0/0'
        }
        self.coordinates = []
        self.srs_name = None
        self.srs_dimension = "3"

    def extract_coordinates_from_text(self, coord_text: str) -> List[Tuple[float, float, float]]:
        """Extract coordinates from coordinate text strings"""
        coords = []
        values = coord_text.strip().split()
        
        for i in range(0, len(values), 3):
            if i + 2 < len(values):
                try:
                    x = float(values[i])
                    y = float(values[i + 1])
                    z = float(values[i + 2])
                    coords.append((x, y, z))
                except ValueError:
                    continue
        
        return coords

    def extract_coordinates_from_pos_list(self, pos_list_text: str, srs_dimension: int = 3) -> List[Tuple[float, float, float]]:
        """Extract coordinates from gml:posList"""
        coords = []
        values = pos_list_text.strip().split()
        
        for i in range(0, len(values), srs_dimension):
            if i + srs_dimension - 1 < len(values):
                try:
                    x = float(values[i])
                    y = float(values[i + 1])
                    z = float(values[i + 2]) if srs_dimension >= 3 else 0.0
                    coords.append((x, y, z))
                except ValueError:
                    continue
        
        return coords

    def parse_citygml_file(self, file_path: str) -> None:
        """Parse CityGML file and extract all coordinates"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Register namespaces
            for prefix, uri in self.namespaces.items():
                ET.register_namespace(prefix, uri)
            
            # Extract SRS information from first geometry found
            self.extract_srs_info(root)
            
            # Find all coordinate elements
            self.extract_all_coordinates(root)
            
        except ET.ParseError as e:
            print(f"Error parsing XML file: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            sys.exit(1)

    def extract_srs_info(self, root) -> None:
        """Extract SRS name and dimension from geometry elements"""
        # Try with namespaces first
        try:
            srs_elements = root.findall(".//gml:*[@srsName]", self.namespaces)
        except:
            srs_elements = []
        
        # If no elements found with namespaces, try without
        if not srs_elements:
            try:
                srs_elements = root.findall(".//*[@srsName]")
            except:
                srs_elements = []
        
        if srs_elements:
            self.srs_name = srs_elements[0].get('srsName')
            self.srs_dimension = srs_elements[0].get('srsDimension', '3')

    def extract_all_coordinates(self, root) -> None:
        """Extract coordinates from all geometry elements"""
        # Define coordinate element patterns
        coordinate_patterns = [
            ('gml:coordinates', './/gml:coordinates'),
            ('gml:posList', './/gml:posList'),
            ('gml:pos', './/gml:pos'),
            ('coordinates', './/coordinates'),
            ('posList', './/posList'),
            ('pos', './/pos')
        ]
        
        for element_type, xpath_pattern in coordinate_patterns:
            try:
                if 'gml:' in xpath_pattern:
                    # Try with namespace
                    elements = root.findall(xpath_pattern, self.namespaces)
                else:
                    # Try without namespace
                    elements = root.findall(xpath_pattern)
                
                for elem in elements:
                    if elem.text and elem.text.strip():
                        coords = []
                        
                        if 'coordinates' in element_type.lower():
                            coords = self.extract_coordinates_from_coordinates(elem.text)
                        elif 'poslist' in element_type.lower():
                            dim = int(elem.get('srsDimension', self.srs_dimension))
                            coords = self.extract_coordinates_from_pos_list(elem.text, dim)
                        elif 'pos' in element_type.lower():
                            coords = self.extract_coordinates_from_pos_list(elem.text, int(self.srs_dimension))
                        
                        if coords:
                            self.coordinates.extend(coords)
                            
            except Exception as e:
                # Continue with next pattern if this one fails
                continue

    def extract_coordinates_from_coordinates(self, coord_text: str) -> List[Tuple[float, float, float]]:
        """Extract coordinates from gml:coordinates (comma and space separated)"""
        coords = []
        try:
            if ',' in coord_text:
                # Comma-separated coordinates
                coord_groups = coord_text.strip().split()
                for group in coord_groups:
                    values = group.split(',')
                    if len(values) >= 2:
                        try:
                            x = float(values[0])
                            y = float(values[1])
                            z = float(values[2]) if len(values) > 2 else 0.0
                            coords.append((x, y, z))
                        except ValueError:
                            continue
            else:
                # Space-separated coordinates
                coords = self.extract_coordinates_from_text(coord_text)
        except Exception as e:
            print(f"Warning: Error parsing coordinates: {e}")
        
        return coords

    def calculate_bounding_box(self) -> Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]:
        """Calculate the bounding box from all extracted coordinates"""
        if not self.coordinates:
            return None
        
        min_x = min(coord[0] for coord in self.coordinates)
        min_y = min(coord[1] for coord in self.coordinates)
        min_z = min(coord[2] for coord in self.coordinates)
        
        max_x = max(coord[0] for coord in self.coordinates)
        max_y = max(coord[1] for coord in self.coordinates)
        max_z = max(coord[2] for coord in self.coordinates)
        
        return ((min_x, min_y, min_z), (max_x, max_y, max_z))

    def format_envelope_xml(self, bbox: Tuple[Tuple[float, float, float], Tuple[float, float, float]]) -> str:
        """Format bounding box as GML Envelope with proper indentation"""
        lower_corner, upper_corner = bbox
        
        srs_name = self.srs_name or "urn:ogc:def:crs:EPSG::4326"
        srs_dimension = self.srs_dimension or "3"
        
        envelope = f'''    <gml:Envelope srsName="{srs_name}" srsDimension="{srs_dimension}">
      <gml:lowerCorner>{lower_corner[0]} {lower_corner[1]} {lower_corner[2]}</gml:lowerCorner>
      <gml:upperCorner>{upper_corner[0]} {upper_corner[1]} {upper_corner[2]}</gml:upperCorner>
    </gml:Envelope>'''
        
        return envelope

    def insert_bounding_box_into_file(self, file_path: str, bbox_xml: str, backup: bool = True) -> bool:
        """Insert bounding box into CityGML file after line 4"""
        try:
            # Create backup if requested
            if backup:
                backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(file_path, backup_path)
                print(f"Backup created: {backup_path}")
            
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # # Check if bounding box already exists
            # for i, line in enumerate(lines):
            #     if 'gml:Envelope' in line or 'Envelope' in line:
            #         print(f"Bounding box already exists at line {i+1}. Skipping insertion.")
            #         return False
            
            # Find insertion point (after line 4, or after XML declaration and root element)
            insertion_line = self.find_insertion_point(lines)
            
            # Insert the bounding box
            bbox_lines = bbox_xml.split('\n')
            for i, bbox_line in enumerate(bbox_lines):
                lines.insert(insertion_line + i, bbox_line + '\n')
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"Bounding box inserted at line {insertion_line + 1}")
            return True
            
        except Exception as e:
            print(f"Error inserting bounding box: {e}")
            return False

    def find_insertion_point(self, lines: List[str]) -> int:
        """Find the appropriate insertion point for the bounding box"""
        # Strategy 1: Insert after line 4 if it exists and is reasonable
        if len(lines) > 4:
            return 4
        
        # Strategy 2: Find root element and insert after it
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Look for opening root element (not self-closing)
            if (stripped.startswith('<') and 
                not stripped.startswith('<?') and 
                not stripped.startswith('<!--') and
                not stripped.endswith('/>') and
                '>' in stripped):
                return i + 1
        
        # Strategy 3: Insert after XML declaration
        for i, line in enumerate(lines):
            if line.strip().startswith('<?xml'):
                return i + 1
        
        # Fallback: insert at beginning
        return 0

    def debug_file_structure(self, file_path: str) -> None:
        """Debug function to show file structure"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            print(f"Root element: {root.tag}")
            print(f"Root attributes: {root.attrib}")
            
            # Find all unique element names
            all_elements = set()
            for elem in root.iter():
                all_elements.add(elem.tag)
            
            print(f"All element types found: {sorted(all_elements)}")
            
            # Look for coordinate-related elements specifically
            coord_elements = []
            for elem in root.iter():
                if any(coord_type in elem.tag.lower() for coord_type in ['coordinates', 'pos']):
                    coord_elements.append(elem.tag)
            
            print(f"Coordinate elements found: {coord_elements}")
            
        except Exception as e:
            print(f"Debug error: {e}")

    def process_file(self, file_path: str, backup: bool = True, debug: bool = False) -> str:
        """Process a single CityGML file and insert bounding box"""
        print(f"Processing: {file_path}")
        
        if debug:
            print("=== DEBUG INFO ===")
            self.debug_file_structure(file_path)
            print("=== END DEBUG ===")
        
        # Reset coordinates for each file
        self.coordinates = []
        self.srs_name = None
        
        # Parse file and extract coordinates
        self.parse_citygml_file(file_path)
        
        print(f"Found {len(self.coordinates)} coordinate points")
        
        if not self.coordinates:
            return f"No coordinates found in {file_path}"
        
        # Calculate bounding box
        bbox = self.calculate_bounding_box()
        if not bbox:
            return f"Could not calculate bounding box for {file_path}"
        
        # Format as XML
        bbox_xml = self.format_envelope_xml(bbox)
        
        # Insert into file
        success = self.insert_bounding_box_into_file(file_path, bbox_xml, backup)
        
        if success:
            return f"Successfully inserted bounding box into {file_path}\n{bbox_xml}"
        else:
            return f"Failed to insert bounding box into {file_path}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python citygml_bbox_calculator.py <citygml_file> [--no-backup] [--debug]")
        print("       python citygml_bbox_calculator.py <directory> [--no-backup] [--debug]")
        print("\nOptions:")
        print("  --no-backup    Skip creating backup files")
        print("  --debug        Show debug information about file structure")
        print("\nExample:")
        print("  python citygml_bbox_calculator.py building.gml")
        sys.exit(1)
    
    input_path = sys.argv[1]
    backup = '--no-backup' not in sys.argv
    debug = '--debug' in sys.argv
    
    calculator = CityGMLBoundingBoxCalculator()
    
    if os.path.isfile(input_path):
        # Process single file
        result = calculator.process_file(input_path, backup, debug)
        print(f"\nResult:\n{result}")
        
    elif os.path.isdir(input_path):
        # Process all CityGML files in directory
        citygml_files = []
        for root, dirs, files in os.walk(input_path):
            for file in files:
                if file.lower().endswith(('.gml', '.xml', '.citygml')):
                    citygml_files.append(os.path.join(root, file))
        
        if not citygml_files:
            print(f"No CityGML files found in {input_path}")
            sys.exit(1)
        
        print(f"Found {len(citygml_files)} CityGML files to process")
        
        for file_path in citygml_files:
            calculator = CityGMLBoundingBoxCalculator()  # Reset for each file
            result = calculator.process_file(file_path, backup, debug)
            print(f"\n{result}")
            print("-" * 50)
    
    else:
        print(f"Invalid path: {input_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
