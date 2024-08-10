"""
Geolocation Service

This module provides a comprehensive geolocation service using WiFi access points
and IP-based geolocation. It supports multiple platforms (Windows, Linux, macOS)
and interacts with the Google Geolocation API.

Usage:
    python geolocation_service.py

Author: LangGang
Date: [Current Date]
Version: 1.0
"""

import subprocess
import json
import logging
import platform
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import requests
import uuid
import re
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
API_KEY = 'YOUR_API_KEY'
GEOLOCATION_API_URL = "https://www.googleapis.com/geolocation/v1/geolocate"

@dataclass
class WifiAccessPoint:
    """
    Represents a WiFi access point with its MAC address and optional signal strength and channel.
    """
    macAddress: str
    signalStrength: Optional[int] = None
    channel: Optional[int] = None

    def __post_init__(self):
        """Ensures the MAC address is properly formatted after initialization."""
        self.macAddress = format_mac_address(self.macAddress)

@dataclass
class GeolocationConfig:
    """
    Configuration for geolocation request, including IP consideration and WiFi access points.
    """
    considerIp: bool = True
    wifiAccessPoints: List[WifiAccessPoint] = field(default_factory=list)

@dataclass
class GeolocationResult:
    """
    Represents the result of a geolocation request, including latitude, longitude, and accuracy.
    """
    latitude: float
    longitude: float
    accuracy: float

class MacAddressFormatter:
    """Utility class for formatting MAC addresses."""

    @staticmethod
    def format(mac: str) -> Optional[str]:
        """
        Formats a MAC address to the standard XX:XX:XX:XX:XX:XX format.

        Args:
            mac (str): The input MAC address.

        Returns:
            Optional[str]: The formatted MAC address, or None if invalid.
        """
        mac = re.sub('[^0-9a-fA-F]', '', mac.upper())
        return ':'.join([mac[i:i+2] for i in range(0, 12, 2)]) if len(mac) == 12 else None

# Use the static method directly
format_mac_address = MacAddressFormatter.format

class WifiScannerBase(ABC):
    """Abstract base class for WiFi scanners."""

    @abstractmethod
    def scan(self) -> List[WifiAccessPoint]:
        """
        Scans for nearby WiFi access points.

        Returns:
            List[WifiAccessPoint]: A list of detected WiFi access points.
        """
        pass

class WindowsWifiScanner(WifiScannerBase):
    """WiFi scanner implementation for Windows."""

    def scan(self) -> List[WifiAccessPoint]:
        """
        Scans for WiFi access points on Windows using WMI.

        Returns:
            List[WifiAccessPoint]: A list of detected WiFi access points.
        """
        try:
            import wmi
            c = wmi.WMI()
            wlan = c.Win32_NetworkAdapter(PhysicalAdapter=True, NetConnectionID="Wi-Fi")[0]
            networks = c.MSNdis_80211_BSSIList(InstanceName=wlan.Name)[0].Ndis80211BSSIList
            return [
                WifiAccessPoint(
                    macAddress=format_mac_address(":".join([f"{b:02x}" for b in network.BSSID])),
                    signalStrength=network.Rssi,
                    channel=network.Configuration.ChannelNumber
                )
                for network in networks
                if format_mac_address(":".join([f"{b:02x}" for b in network.BSSID]))
            ]
        except Exception as e:
            logger.error(f"Failed to scan WiFi access points on Windows: {e}")
        return []

class LinuxWifiScanner(WifiScannerBase):
    """WiFi scanner implementation for Linux."""

    def scan(self) -> List[WifiAccessPoint]:
        """
        Scans for WiFi access points on Linux using iwlist.

        Returns:
            List[WifiAccessPoint]: A list of detected WiFi access points.
        """
        try:
            result = subprocess.run(['sudo', 'iwlist', 'scanning'], capture_output=True, text=True)
            cells = result.stdout.split('Cell ')
            wifi_list = []
            for cell in cells[1:]:
                lines = cell.split('\n')
                mac_address = next((line.split('Address:')[1].strip() for line in lines if 'Address:' in line), None)
                signal_strength = next((int(line.split('Signal level=')[1].split(' ')[0]) 
                                        for line in lines if 'Signal level=' in line), None)
                channel = next((int(line.split('Channel:')[1].strip()) 
                                for line in lines if 'Channel:' in line), None)
                if mac_address:
                    wifi_list.append(WifiAccessPoint(macAddress=mac_address, signalStrength=signal_strength, channel=channel))
            return wifi_list
        except Exception as e:
            logger.error(f"Failed to scan WiFi access points on Linux: {e}")
        return []

class MacWifiScanner(WifiScannerBase):
    """WiFi scanner implementation for macOS."""

    def scan(self) -> List[WifiAccessPoint]:
        """
        Scans for WiFi access points on macOS using airport utility.

        Returns:
            List[WifiAccessPoint]: A list of detected WiFi access points.
        """
        try:
            result = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"],
                capture_output=True, text=True
            )
            lines = result.stdout.split("\n")[1:]  # Skip header
            return [
                WifiAccessPoint(
                    macAddress=parts[1],
                    signalStrength=int(parts[2]) if parts[2].lstrip('-').isdigit() else None,
                    channel=int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else None
                )
                for line in lines
                if (parts := line.split()) and len(parts) > 2
            ]
        except Exception as e:
            logger.error(f"Failed to scan WiFi access points on macOS: {e}")
        return []

class WifiScannerFactory:
    """Factory class for creating appropriate WiFi scanner based on the operating system."""

    @staticmethod
    def get_scanner() -> WifiScannerBase:
        """
        Creates and returns a WiFi scanner appropriate for the current operating system.

        Returns:
            WifiScannerBase: An instance of the appropriate WiFi scanner.
        """
        system = platform.system()
        if system == "Windows":
            return WindowsWifiScanner()
        elif system == "Linux":
            return LinuxWifiScanner()
        elif system == "Darwin":  # macOS
            return MacWifiScanner()
        else:
            logger.warning(f"Unsupported platform: {system}. Using IP-based geolocation.")
            return WifiScannerBase()

class GeolocationAPI:
    """Handles interactions with the Google Geolocation API."""

    def __init__(self, api_key: str):
        """
        Initializes the GeolocationAPI with the provided API key.

        Args:
            api_key (str): The Google Geolocation API key.
        """
        self.api_key = api_key
        self.url = f"{GEOLOCATION_API_URL}?key={self.api_key}"
        self.headers = {"Content-Type": "application/json"}
        
    def geolocation_request(self, config: GeolocationConfig) -> GeolocationResult:
        """
        Sends a geolocation request to the Google Geolocation API.

        Args:
            config (GeolocationConfig): The configuration for the geolocation request.

        Returns:
            GeolocationResult: The result of the geolocation request.

        Raises:
            requests.exceptions.HTTPError: If an HTTP error occurs.
            Exception: For any other errors.
        """
        valid_wifi_aps = [ap for ap in config.wifiAccessPoints if ap.macAddress]
        
        payload = {
            "considerIp": config.considerIp,
            "wifiAccessPoints": [wifi_ap.__dict__ for wifi_ap in valid_wifi_aps]
        }
        
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            logger.info("Sending geolocation request...")
            response = requests.post(self.url, headers=self.headers, json=payload)
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response content: {response.text}")
            response.raise_for_status()
            data = response.json()
            logger.info("Geolocation request successful.")
            return GeolocationResult(
                latitude=data['location']['lat'],
                longitude=data['location']['lng'],
                accuracy=data['accuracy']
            )
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            logger.error(f"Response content: {http_err.response.text}")
            raise
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            raise

class SystemInfo:
    """Utility class for retrieving system information."""

    @staticmethod
    def get_mac_address() -> Optional[str]:
        """
        Retrieves the MAC address of the system's network interface.

        Returns:
            Optional[str]: The formatted MAC address, or None if unavailable.
        """
        return format_mac_address(':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,8*6,8)][::-1]))

    @staticmethod
    def get_public_ip() -> Optional[str]:
        """
        Retrieves the public IP address of the system.

        Returns:
            Optional[str]: The public IP address, or None if unavailable.
        """
        try:
            return requests.get('https://api.ipify.org').text
        except:
            logger.error("Failed to get public IP")
            return None

class GeolocationService:
    """Main service class for handling geolocation requests."""

    def __init__(self, api_key: str):
        """
        Initializes the GeolocationService with the provided API key.

        Args:
            api_key (str): The Google Geolocation API key.
        """
        self.api = GeolocationAPI(api_key)
        self.wifi_scanner = WifiScannerFactory.get_scanner()

    def get_location(self) -> Tuple[GeolocationResult, Dict[str, str]]:
        """
        Retrieves the geolocation based on WiFi access points and/or IP address.

        Returns:
            Tuple[GeolocationResult, Dict[str, str]]: A tuple containing the geolocation result
            and additional information (public IP and MAC address).

        Raises:
            Exception: If geolocation retrieval fails.
        """
        wifi_access_points = self.wifi_scanner.scan()
        logger.info(f"Number of WiFi access points found: {len(wifi_access_points)}")
        
        public_ip = SystemInfo.get_public_ip()
        mac_address = SystemInfo.get_mac_address()
        
        if not mac_address:
            logger.warning("Unable to get a valid MAC address. This might affect geolocation accuracy.")
        
        logger.info(f"Public IP: {public_ip}")
        logger.info(f"MAC Address: {mac_address}")

        config = GeolocationConfig(
            considerIp=True,
            wifiAccessPoints=wifi_access_points
        )

        location = self.api.geolocation_request(config)
        
        additional_info = {
            "public_ip": public_ip,
            "mac_address": mac_address
        }
        
        return location#, additional_info
    


def geolocation_data(API_KEY: str) -> dict:
    """Main function to demonstrate the usage of the GeolocationService."""
    geolocation_service = GeolocationService(API_KEY)
    
    try:
        location = geolocation_service.get_location()
        print("\nEstimated Location:")
        print(f"Latitude: {location.latitude}")
        print(f"Longitude: {location.longitude}")
        return location
    except Exception as e:
        return(f"Failed to get geolocation data: {e}")
