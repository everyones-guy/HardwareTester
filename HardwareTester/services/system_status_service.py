
import os
import psutil
import platform
from datetime import datetime
from HardwareTester.utils.logger import Logger

logger = Logger(name="SystemStatusCheck", log_file="logs/system_status_check.log", level="INFO")

def get_system_info():
    """
    Retrieve basic system information.
    :return: Dictionary containing system info.
    """
    try:
        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "hostname": platform.node(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
        }
        logger.info("Retrieved system information successfully.")
        return {"success": True, "system_info": system_info}
    except Exception as e:
        logger.error(f"Failed to retrieve system information: {e}")
        return {"success": False, "error": str(e)}

def get_memory_status():
    """
    Retrieve memory usage details.
    :return: Dictionary containing memory status.
    """
    try:
        memory = psutil.virtual_memory()
        memory_status = {
            "total": convert_bytes(memory.total),
            "available": convert_bytes(memory.available),
            "used": convert_bytes(memory.used),
            "percent": f"{memory.percent}%",
        }
        logger.info("Retrieved memory status successfully.")
        return {"success": True, "memory_status": memory_status}
    except Exception as e:
        logger.error(f"Failed to retrieve memory status: {e}")
        return {"success": False, "error": str(e)}

def get_cpu_status():
    """
    Retrieve CPU usage details.
    :return: Dictionary containing CPU status.
    """
    try:
        cpu_status = {
            "cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "usage_percent": f"{psutil.cpu_percent(interval=1)}%",
        }
        logger.info("Retrieved CPU status successfully.")
        return {"success": True, "cpu_status": cpu_status}
    except Exception as e:
        logger.error(f"Failed to retrieve CPU status: {e}")
        return {"success": False, "error": str(e)}

def get_disk_status():
    """
    Retrieve disk usage details.
    :return: Dictionary containing disk status.
    """
    try:
        partitions = psutil.disk_partitions()
        disk_status = []
        for partition in partitions:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_status.append({
                "device": partition.device,
                "mount_point": partition.mountpoint,
                "file_system": partition.fstype,
                "total": convert_bytes(usage.total),
                "used": convert_bytes(usage.used),
                "free": convert_bytes(usage.free),
                "percent": f"{usage.percent}%",
            })
        logger.info("Retrieved disk status successfully.")
        return {"success": True, "disk_status": disk_status}
    except Exception as e:
        logger.error(f"Failed to retrieve disk status: {e}")
        return {"success": False, "error": str(e)}

def get_network_status():
    """
    Retrieve network usage details.
    :return: Dictionary containing network status.
    """
    try:
        net_io = psutil.net_io_counters()
        network_status = {
            "bytes_sent": convert_bytes(net_io.bytes_sent),
            "bytes_received": convert_bytes(net_io.bytes_recv),
            "packets_sent": net_io.packets_sent,
            "packets_received": net_io.packets_recv,
            "errors_in": net_io.errin,
            "errors_out": net_io.errout,
            "dropped_in": net_io.dropin,
            "dropped_out": net_io.dropout,
        }
        logger.info("Retrieved network status successfully.")
        return {"success": True, "network_status": network_status}
    except Exception as e:
        logger.error(f"Failed to retrieve network status: {e}")
        return {"success": False, "error": str(e)}

def convert_bytes(size):
    """
    Convert bytes to a human-readable format.
    :param size: Size in bytes.
    :return: Human-readable size.
    """
    try:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
    except Exception as e:
        logger.error(f"Error converting bytes: {e}")
        return "Unknown"

def get_full_system_status():
    """
    Retrieve a full system status report.
    :return: Dictionary containing all system status information.
    """
    try:
        status = {
            "system_info": get_system_info(),
            "cpu_status": get_cpu_status(),
            "memory_status": get_memory_status(),
            "disk_status": get_disk_status(),
            "network_status": get_network_status(),
        }
        logger.info("Retrieved full system status successfully.")
        return {"success": True, "status": status}
    except Exception as e:
        logger.error(f"Failed to retrieve full system status: {e}")
        return {"success": False, "error": str(e)}

def fetch_system_status():
    """Fetch basic system status information."""
    try:
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        system_info = {
            "hostname": platform.node(),
            "os": platform.system(),
            "os_version": platform.version(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "uptime": str(uptime).split(".")[0], # Remove microseconds
        }
        return {"success": True, "status": system_info}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_detailed_metrics():
    """Fetch detailed metrics for system monitoring."""
    try:
        metrics = {
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_freq": psutil.cpu_freq()._asdict(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "used": psutil.virtual_memory().used,
                "percent": psutil.virtual_memory().percent,
            },
            "disk_partitions": [
                {
                    "device": p.device,
                    "mountpoint": p.mountpoint,
                    "fstype": p.fstype,
                    "usage": psutil.disk_usage(p.mountpoint)._asdict(),
                }
                for p in psutil.disk_partitions()
            ],
            "network": {
                "interfaces": psutil.net_if_addrs(),
                "io_counters": psutil.net_io_counters()._asdict(),
            },
        }
        return {"success": True, "metrics": metrics}
    except Exception as e:
        return {"success": False, "error": str(e)}

