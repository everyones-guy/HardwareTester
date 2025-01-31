import os
import json
import socket
import platform
import requests
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.models.device_models import Blueprint, Device, db

logger = CustomLogger.get_logger("blueprint_service")

class BlueprintService:
    @staticmethod
    def scan_machine(machine_address: str) -> dict:
        """
        Scan the given machine address and retrieve hardware information.

        :param machine_address: IP, URL, or local path
        :return: Dictionary representing the machine blueprint
        """
        blueprint_data = {
            "name": f"Blueprint-{machine_address}",
            "description": f"Auto-generated blueprint for {machine_address}",
            "devices": []
        }

        try:
            # Check if it's a URL (assume REST API response contains system info)
            if machine_address.startswith("http"):
                response = requests.get(machine_address, timeout=5)
                if response.status_code == 200:
                    blueprint_data["devices"] = response.json()
                else:
                    logger.error(f"Failed to retrieve info from {machine_address}")
                    return {"error": "Failed to retrieve data from machine."}
            
            # Check if it's a local machine (ping test)
            elif machine_address.startswith("/") or os.path.exists(machine_address):
                blueprint_data["devices"].append({
                    "type": "Local Machine",
                    "os": platform.system(),
                    "cpu": platform.processor(),
                    "architecture": platform.architecture()[0]
                })
            
            # Assume it's an IP address (check if reachable)
            else:
                try:
                    socket.gethostbyname(machine_address)
                    blueprint_data["devices"].append({
                        "type": "Remote Machine",
                        "ip": machine_address,
                        "reachable": True
                    })
                except socket.error:
                    logger.error(f"Could not resolve {machine_address}")
                    return {"error": "Invalid machine address"}

            # Save to database
            new_blueprint = Blueprint(
                name=blueprint_data["name"],
                description=blueprint_data["description"],
                data=json.dumps(blueprint_data)
            )
            db.session.add(new_blueprint)
            db.session.commit()

            logger.info(f"Generated blueprint for {machine_address}")
            return blueprint_data

        except Exception as e:
            logger.error(f"Error scanning machine {machine_address}: {e}")
            return {"error": str(e)}
