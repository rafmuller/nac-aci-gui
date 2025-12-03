"""
ACI API Client
Handles authentication and API interactions with Cisco ACI (Application Centric Infrastructure)
"""

import requests
import yaml
import os
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ACIClient:
    """Client for interacting with Cisco ACI API"""

    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Initialize ACI client

        Args:
            base_url: Base URL for ACI APIC (e.g., https://apic.example.com)
            username: Username for authentication
            password: Password for authentication
        """
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = None

        # Load from config if parameters not provided
        if not all([self.base_url, self.username, self.password]):
            self._load_config()

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            # Navigate from src/nac_aci_gui/ up to project root, then to yaml/
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(project_root, 'yaml', 'config.yaml')

            if not os.path.exists(config_path):
                logger.warning("Configuration file not found. Please configure via Admin panel.")
                return

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            if config and 'aci' in config:
                aci_config = config['aci']
                self.base_url = self.base_url or aci_config.get('url', '')
                self.username = self.username or aci_config.get('username', '')
                self.password = self.password or aci_config.get('password', '')

                logger.info("ACI configuration loaded successfully")
                logger.info(f"Base URL: {self.base_url}")
                logger.info(f"Username: {self.username}")
                logger.info(f"Password: {self.password[:3]}..." if self.password else "Password: None")
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")

    def _ensure_config(self) -> bool:
        """Ensure required configuration is present"""
        if not all([self.base_url, self.username, self.password]):
            logger.error("ACI not configured. Please configure via Admin panel.")
            return False
        return True

    def login(self) -> bool:
        """
        Authenticate with ACI APIC and get token

        Returns:
            True if authentication successful, False otherwise
        """
        if not self._ensure_config():
            return False

        try:
            # Prepare login payload
            login_payload = {
                'aaaUser': {
                    'attributes': {
                        'name': self.username,
                        'pwd': self.password
                    }
                }
            }

            # Make login request
            login_url = f"{self.base_url}/api/aaaLogin.json"
            response = self.session.post(login_url, json=login_payload, verify=False, timeout=30)

            if response.status_code == 200:
                response_data = response.json()

                # Extract token from response
                if 'imdata' in response_data and len(response_data['imdata']) > 0:
                    login_attrs = response_data['imdata'][0].get('aaaLogin', {}).get('attributes', {})
                    self.token = login_attrs.get('token')

                    if self.token:
                        # Set the token as a cookie for subsequent requests
                        self.session.cookies.set('APIC-cookie', self.token)
                        logger.info("ACI authentication successful")
                        return True
                    else:
                        logger.error("No token received in login response")
                        return False
                else:
                    logger.error("Invalid login response format")
                    return False
            else:
                logger.error(f"ACI login failed: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"ACI login request failed: {str(e)}")
            return False

    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token"""
        if not self._ensure_config():
            return False

        # Check if we already have a token
        if self.token and 'APIC-cookie' in self.session.cookies:
            return True

        # Try to login and get a new token
        return self.login()

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Make GET request to ACI API

        Args:
            endpoint: API endpoint (e.g., '/api/class/fvTenant.json')
            params: Optional query parameters

        Returns:
            Response JSON data or None if request failed
        """
        if not self._ensure_authenticated():
            return None

        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, verify=False, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"GET request failed: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"GET request failed: {str(e)}")
            return None

    def post(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make POST request to ACI API

        Args:
            endpoint: API endpoint
            data: Request payload

        Returns:
            Response JSON data or None if request failed
        """
        if not self._ensure_authenticated():
            return None

        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.post(url, json=data, verify=False, timeout=30)

            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"POST request failed: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed: {str(e)}")
            return None

    def put(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make PUT request to ACI API

        Args:
            endpoint: API endpoint
            data: Request payload

        Returns:
            Response JSON data or None if request failed
        """
        if not self._ensure_authenticated():
            return None

        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.put(url, json=data, verify=False, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"PUT request failed: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"PUT request failed: {str(e)}")
            return None

    def delete(self, endpoint: str) -> bool:
        """
        Make DELETE request to ACI API

        Args:
            endpoint: API endpoint

        Returns:
            True if deletion successful, False otherwise
        """
        if not self._ensure_authenticated():
            return False

        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.delete(url, verify=False, timeout=30)

            if response.status_code in [200, 204]:
                return True
            else:
                logger.error(f"DELETE request failed: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"DELETE request failed: {str(e)}")
            return False

    # Convenience methods for ACI operations

    def get_tenant(self, tenant_name: str, include_subtree: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get specific tenant details from ACI

        Args:
            tenant_name: Name of the tenant to retrieve
            include_subtree: If True, includes all child objects (EPGs, BDs, VRFs, etc.)

        Returns:
            Tenant details with subtree data or None if request failed
        """
        endpoint = f'/api/mo/uni/tn-{tenant_name}.json'
        params = {}

        if include_subtree:
            # Query parameters to get full subtree including all child objects
            params['rsp-subtree'] = 'full'
            params['rsp-prop-include'] = 'config-only'

        return self.get(endpoint, params=params)

    def get_tenant_bridge_domains(self, tenant_name: str, include_subtree: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get specific tenant details from ACI

        Args:
            tenant_name: Name of the tenant to retrieve
            include_subtree: If True, includes all child objects

        Returns:
            Tenant details with subtree data or None if request failed
        """
        ## endpoint = f'/api/mo/uni/tn-{tenant_name}.json'
        endpoint = f'/api/class/fvBD.json'
        params = {}
        params['query-target-filter']= f'wcard(fvBD.dn,"tn-{tenant_name}")'

        if include_subtree:
            # Query parameters to get full subtree including all child objects
            params['rsp-subtree'] = 'full'
            params['rsp-prop-include'] = 'config-only'

        return self.get(endpoint, params=params)


    def get_fabrics(self) -> Optional[Dict[str, Any]]:
        """Get all fabrics from Nexus Dashboard"""
        return self.get('/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics') 

    def get_fabric(self, fabric_name: str) -> Optional[Dict[str, Any]]:
        """Get specific fabric from Nexus Dashboard"""
        return self.get(f'/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}') 

    def get_fabric_inventory(self, fabric_name: str) -> Optional[Dict[str, Any]]:
        """Get fabric inventory"""
        return self.get(f'/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/inventory/switchesByFabric')

    def get_switches(self, fabric_name: str) -> Optional[Dict[str, Any]]:
        """Get switches for a specific fabric"""
        return self.get(f'/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/inventory/switchesByFabric')

    def get_vrfs(self, fabric_name: str) -> Optional[Dict[str, Any]]:
        """Get VRFs for a specific fabric"""
        return self.get(f'/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs')

    def get_networks(self, fabric_name: str) -> Optional[Dict[str, Any]]:
        """Get networks for a specific fabric"""
        return self.get(f'/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/networks')

    def get_configured_fabric(self) -> Optional[Dict[str, Any]]:
        """
        Get fabric details - returns the first available fabric

        Returns:
            First fabric details if available, None otherwise
        """
        # Get all fabrics
        fabrics_response = self.get_fabrics()
        if fabrics_response is None:
            return None

        # Handle both list and dict responses
        fabrics_list = []
        if isinstance(fabrics_response, list):
            fabrics_list = fabrics_response
        elif isinstance(fabrics_response, dict):
            fabrics_list = fabrics_response.get('fabrics', fabrics_response.get('data', []))

        # Return first fabric if available
        if fabrics_list:
            fabric = fabrics_list[0]
            logger.info(f"Found fabric: {fabric.get('fabricName') or fabric.get('name', 'Unknown')}")
            return fabric

        logger.warning("No fabrics found")
        return None

    def get_configured_fabric_switches(self) -> Optional[Dict[str, Any]]:
        """Get switches for the first available fabric"""
        fabric = self.get_configured_fabric()
        if not fabric:
            logger.warning("No fabric available")
            return None

        fabric_name = fabric.get('fabricName') or fabric.get('name')
        if not fabric_name:
            logger.warning("Fabric name not found")
            return None

        return self.get_switches(fabric_name)

    def get_configured_fabric_vrfs(self) -> Optional[Dict[str, Any]]:
        """Get VRFs for the first available fabric"""
        fabric = self.get_configured_fabric()
        if not fabric:
            logger.warning("No fabric available")
            return None

        fabric_name = fabric.get('fabricName') or fabric.get('name')
        if not fabric_name:
            logger.warning("Fabric name not found")
            return None

        return self.get_vrfs(fabric_name)

    def get_configured_fabric_networks(self) -> Optional[Dict[str, Any]]:
        """Get networks for the first available fabric"""
        fabric = self.get_configured_fabric()
        if not fabric:
            logger.warning("No fabric available")
            return None

        fabric_name = fabric.get('fabricName') or fabric.get('name')
        if not fabric_name:
            logger.warning("Fabric name not found")
            return None

        return self.get_networks(fabric_name)

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to ACI APIC by attempting authentication

        Returns:
            Dictionary with status and message
        """
        if not self._ensure_config():
            return {
                'status': 'error',
                'message': 'ACI not configured. Please configure via Admin panel.'
            }

        try:
            # Test authentication by attempting login
            if self.login():
                return {
                    'status': 'success',
                    'message': "Successfully connected and authenticated to ACI APIC"
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to authenticate. Please check credentials and URL.'
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection test failed: {str(e)}'
            }

    def close(self):
        """Close the session"""
        self.session.close()


# Singleton instance for reuse across the application
_aci_client_instance = None


def get_aci_client() -> ACIClient:
    """
    Get or create singleton ACI client instance

    Returns:
        ACIClient instance
    """
    global _aci_client_instance

    if _aci_client_instance is None:
        _aci_client_instance = ACIClient()

    return _aci_client_instance


def reset_aci_client():
    """
    Reset the singleton ACI client instance.
    This forces a reload of configuration on next access.
    """
    global _aci_client_instance
    if _aci_client_instance is not None:
        _aci_client_instance.close()
        _aci_client_instance = None
        logger.info("ACI client instance reset")
