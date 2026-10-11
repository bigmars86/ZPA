"""
Export manager for Zoom Poll Analyzer.
Handles different export formats: CSV, JSON, YAML, XML.
"""

import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List


class ExportManager:
    """Manage data export in different formats"""

    SUPPORTED_FORMATS = {
        "csv": {
            "name": "CSV (Comma Separated)",
            "extension": ".csv",
            "filter": "CSV Files (*.csv);;All Files (*)",
        },
        "json": {
            "name": "JSON",
            "extension": ".json",
            "filter": "JSON Files (*.json);;All Files (*)",
        },
        "yaml": {
            "name": "YAML",
            "extension": ".yaml",
            "filter": "YAML Files (*.yaml *.yml);;All Files (*)",
        },
        "xml": {
            "name": "XML",
            "extension": ".xml",
            "filter": "XML Files (*.xml);;All Files (*)",
        },
    }

    def __init__(self):
        self.csv_separator = ";"

    def set_csv_separator(self, separator: str):
        """Set CSV separator"""
        self.csv_separator = separator

    def export_to_csv(self, data: List[Dict], filename: str) -> bool:
        """Export data to CSV format"""
        try:
            if not data:
                return False

            # Get headers from first row
            headers = list(data[0].keys())

            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=headers, delimiter=self.csv_separator
                )
                writer.writeheader()
                writer.writerows(data)
            return True
        except Exception as e:
            print(f"CSV export error: {e}")
            return False

    def export_to_json(
        self, data: List[Dict], filename: str, metadata: Dict = None
    ) -> bool:
        """Export data to JSON format"""
        try:
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "format": "json",
                    "record_count": len(data),
                    **(metadata or {}),
                },
                "data": data,
            }

            with open(filename, "w", encoding="utf-8") as jsonfile:
                json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"JSON export error: {e}")
            return False

    def export_to_yaml(
        self, data: List[Dict], filename: str, metadata: Dict = None
    ) -> bool:
        """Export data to YAML format"""
        try:
            # Try to import yaml, fall back gracefully if not available
            try:
                import yaml
            except ImportError:
                print(
                    "YAML export requires PyYAML package. Install with: pip install PyYAML"
                )
                return False

            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "format": "yaml",
                    "record_count": len(data),
                    **(metadata or {}),
                },
                "data": data,
            }

            with open(filename, "w", encoding="utf-8") as yamlfile:
                yaml.dump(
                    export_data,
                    yamlfile,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )
            return True
        except Exception as e:
            print(f"YAML export error: {e}")
            return False

    def export_to_xml(
        self, data: List[Dict], filename: str, metadata: Dict = None
    ) -> bool:
        """Export data to XML format"""
        try:
            # Create root element
            root = ET.Element("zoom_poll_export")

            # Add metadata
            info = ET.SubElement(root, "export_info")
            ET.SubElement(info, "timestamp").text = datetime.now().isoformat()
            ET.SubElement(info, "format").text = "xml"
            ET.SubElement(info, "record_count").text = str(len(data))

            if metadata:
                for key, value in metadata.items():
                    ET.SubElement(info, key).text = str(value)

            # Add data
            data_element = ET.SubElement(root, "data")

            for record in data:
                record_element = ET.SubElement(data_element, "record")
                for key, value in record.items():
                    # Clean key name for XML (replace spaces with underscores)
                    clean_key = key.replace(" ", "_").replace("/", "_").lower()
                    field_element = ET.SubElement(record_element, clean_key)
                    field_element.text = str(value) if value is not None else ""

            # Write to file
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)  # Pretty print
            tree.write(filename, encoding="utf-8", xml_declaration=True)
            return True
        except Exception as e:
            print(f"XML export error: {e}")
            return False

    def export_data(
        self, data: List[Dict], filename: str, format_type: str, metadata: Dict = None
    ) -> bool:
        """Export data in specified format"""
        if format_type not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format_type}")

        if format_type == "csv":
            return self.export_to_csv(data, filename)
        elif format_type == "json":
            return self.export_to_json(data, filename, metadata)
        elif format_type == "yaml":
            return self.export_to_yaml(data, filename, metadata)
        elif format_type == "xml":
            return self.export_to_xml(data, filename, metadata)

        return False

    def get_default_filename(
        self, format_type: str, base_name: str = "zoom_poll_results"
    ) -> str:
        """Get default filename for export format"""
        if format_type not in self.SUPPORTED_FORMATS:
            format_type = "csv"

        extension = self.SUPPORTED_FORMATS[format_type]["extension"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}{extension}"
