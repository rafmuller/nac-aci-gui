# ACI API Integration

This document describes the ACI API integration in the NaC API application.

## Overview

The application includes a complete ACI API client (`aci.py`) that handles header-based authentication and API requests to Cisco ACI (Application Centric Infrastructure).

## Authentication Method

The client uses header-based authentication with:
- **X-ACI-Username**: ACI username
- **X-ACI-Apikey**: ACI API key

These headers are automatically added to all requests when you configure the client.

### Example Request Headers

When you make a request, the client automatically includes these headers:

```
GET /api/v1/sites HTTP/1.1
Host: nexus-dashboard.example.com
X-Nd-Username: admin
X-Nd-Apikey: your-api-key-here
Content-Type: application/json
```

No token management or re-authentication is required - the API key is sent with every request.

## Configuration

Configure ACI access through the Admin panel in the web interface:

1. Navigate to the **Admin** page
2. Fill in the following fields:
   - **ACI API Key**: Your API authentication key
   - **ACI URL**: Base URL (e.g., `https://nexus-dashboard.example.com`)
   - **ACI Username**: Your username
   - **Fabric Name** (optional): Specific fabric to manage (e.g., `DC1-Fabric`)
3. Click **Save Configuration**
4. Click **Test ACI Connection** to verify

Configuration is stored in `yaml/config.yaml`:

```yaml
aci:
  api_key: your-api-key
  url: https://nexus-dashboard.example.com
  username: admin
  fabric_name: DC1-Fabric
```

### Fabric Name Configuration

When you configure a fabric name, the application will scope all operations to that specific fabric. This is useful when you want to manage a single fabric in a multi-fabric ACI environment.

**Benefits:**
- Automatically filters operations to your configured fabric
- Simplifies API calls - no need to specify fabric ID repeatedly
- Validates fabric exists during connection test
- Convenience methods automatically use configured fabric

## Python API Client

### ACIClient Class

The `ACIClient` class provides methods for interacting with ACI:

```python
from aci import get_aci_client

# Get singleton client instance (loads config including fabric_name)
client = get_aci_client()

# Or create a new instance with explicit configuration
from aci import ACIClient
client = ACIClient(
    base_url="https://nexus-dashboard.example.com",
    username="admin",
    api_key="your-api-key",
    fabric_name="DC1-Fabric"  # Optional
)
```

### Authentication

Authentication is handled automatically via headers. Once you create the client instance, authentication headers are set for all requests:

```python
# Get singleton client instance (loads config and sets auth headers)
client = get_aci_client()

# Or create a new instance with explicit configuration
from aci import ACIClient
client = ACIClient(
    base_url="https://nexus-dashboard.example.com",
    username="admin",
    api_key="your-api-key"
)
# Headers are automatically set in the constructor
```

### Making API Requests

#### GET Requests

```python
# Get all sites
sites = client.get_sites()

# Get all fabrics
fabrics = client.get_fabrics()

# Get fabric inventory
inventory = client.get_fabric_inventory('fabric-123')

# Custom GET request
data = client.get('/api/v1/custom-endpoint', params={'filter': 'value'})
```

#### POST Requests

```python
# Create a new resource
payload = {
    'name': 'new-vrf',
    'vni': 50000
}
result = client.post('/api/v1/vrfs', data=payload)
```

#### PUT Requests

```python
# Update a resource
update_data = {
    'description': 'Updated description'
}
result = client.put('/api/v1/vrfs/vrf-123', data=update_data)
```

#### DELETE Requests

```python
# Delete a resource
success = client.delete('/api/v1/vrfs/vrf-123')
```

### Convenience Methods

The client includes convenience methods for common operations:

```python
# Test connection
result = client.test_connection()
print(result['message'])

# Get sites
sites = client.get_sites()

# Get fabrics
fabrics = client.get_fabrics()

# Get switches for a fabric
switches = client.get_switches('fabric-123')

# Get VRFs for a fabric
vrfs = client.get_vrfs('fabric-123')

# Get networks for a fabric
networks = client.get_networks('fabric-123')

# Get fabric inventory
inventory = client.get_fabric_inventory('fabric-123')
```

### Configured Fabric Methods

When you configure a fabric name, you can use these convenience methods that automatically work with your configured fabric:

```python
# Get configured fabric details
fabric = client.get_configured_fabric()
if fabric:
    print(f"Fabric: {fabric['name']}, ID: {fabric['id']}")

# Get switches for configured fabric (no need to specify fabric ID)
switches = client.get_configured_fabric_switches()

# Get VRFs for configured fabric
vrfs = client.get_configured_fabric_vrfs()

# Get networks for configured fabric
networks = client.get_configured_fabric_networks()
```

**Example:**
```python
from aci import get_aci_client

# Client loads fabric_name from config.yaml
client = get_aci_client()

# Automatically uses the configured fabric
switches = client.get_configured_fabric_switches()
if switches:
    print(f"Found {len(switches)} switches in configured fabric")
else:
    print("Fabric not found or no switches")
```

## Flask API Endpoints

The application exposes Flask API endpoints that use the ACI client:

### Test Connection

```bash
curl http://localhost:9999/api/aci/test-connection
```

Response:
```json
{
  "status": "success",
  "message": "Successfully connected to ACI",
  "sites_count": 3
}
```

### Get Sites

```bash
curl http://localhost:9999/api/aci/sites
```

Response:
```json
{
  "status": "success",
  "data": {
    "sites": [
      {
        "id": "site-1",
        "name": "DC1",
        "status": "healthy"
      }
    ]
  }
}
```

### Get Fabrics

```bash
curl http://localhost:9999/api/aci/fabrics
```

Response:
```json
{
  "status": "success",
  "data": {
    "fabrics": [
      {
        "id": "fabric-1",
        "name": "DC1-Fabric",
        "type": "VXLAN_EVPN"
      }
    ]
  }
}
```

### Get Switches for a Fabric

```bash
curl http://localhost:9999/api/aci/fabrics/fabric-123/switches
```

### Get VRFs for a Fabric

```bash
curl http://localhost:9999/api/aci/fabrics/fabric-123/vrfs
```

### Get Networks for a Fabric

```bash
curl http://localhost:9999/api/aci/fabrics/fabric-123/networks
```

### Get Fabric Inventory

```bash
curl http://localhost:9999/api/aci/fabrics/fabric-123/inventory
```

### Direct ACI API Testing

You can also test the ACI API directly using curl with the authentication headers:

```bash
# Test connection directly to ACI
curl -k -H "X-Nd-Username: admin" \
     -H "X-Nd-Apikey: your-api-key" \
     -H "Content-Type: application/json" \
     https://nexus-dashboard.example.com/api/v1/sites

# Get fabrics directly
curl -k -H "X-Nd-Username: admin" \
     -H "X-Nd-Apikey: your-api-key" \
     -H "Content-Type: application/json" \
     https://nexus-dashboard.example.com/api/v1/fabrics
```

**Note**: The `-k` flag disables SSL certificate verification (not recommended for production).

## Error Handling

The client includes comprehensive error handling:

```python
client = get_aci_client()

# All methods return None on failure
data = client.get('/api/v1/endpoint')
if data is None:
    print("Request failed - check logs for details")
else:
    print("Success:", data)

# Boolean methods return False on failure
success = client.delete('/api/v1/resource/123')
if not success:
    print("Delete failed")
```

## Header-Based Authentication

The client uses header-based authentication which is simpler than token management:

- Authentication headers (`X-Nd-Username` and `X-Nd-Apikey`) are set during client initialization
- Headers are automatically included in all requests
- No token expiration to manage
- No need for re-authentication during the session

## Logging

The client uses Python's logging module:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific logger
logger = logging.getLogger('aci')
logger.setLevel(logging.INFO)
```

## SSL Certificate Verification

**Note**: The current implementation disables SSL certificate verification (`verify=False`). For production use, enable SSL verification:

```python
# In aci.py, change:
response = self.session.get(url, verify=True, timeout=30)
```

And ensure proper SSL certificates are configured.

## Example Integration

Example of using the ACI client in your Flask application:

```python
from flask import Flask, jsonify
from aci import get_aci_client

app = Flask(__name__)

@app.route('/api/my-custom-endpoint')
def my_custom_endpoint():
    client = get_aci_client()

    # Get fabrics
    fabrics = client.get_fabrics()
    if fabrics is None:
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve fabrics'
        }), 500

    # Process fabrics data
    fabric_list = []
    for fabric in fabrics.get('fabrics', []):
        fabric_list.append({
            'id': fabric['id'],
            'name': fabric['name'],
            'switch_count': len(client.get_switches(fabric['id']))
        })

    return jsonify({
        'status': 'success',
        'fabrics': fabric_list
    })
```

## API Reference

### ACIClient Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `get(endpoint, params)` | `endpoint: str`, `params: dict` (optional) | `dict` or `None` | Make GET request |
| `post(endpoint, data)` | `endpoint: str`, `data: dict` | `dict` or `None` | Make POST request |
| `put(endpoint, data)` | `endpoint: str`, `data: dict` | `dict` or `None` | Make PUT request |
| `delete(endpoint)` | `endpoint: str` | `bool` | Make DELETE request |
| `get_sites()` | None | `dict` or `None` | Get all sites |
| `get_fabrics()` | None | `dict` or `None` | Get all fabrics |
| `get_fabric_inventory(fabric_id)` | `fabric_id: str` | `dict` or `None` | Get fabric inventory |
| `get_switches(fabric_id)` | `fabric_id: str` | `dict` or `None` | Get fabric switches |
| `get_vrfs(fabric_id)` | `fabric_id: str` | `dict` or `None` | Get fabric VRFs |
| `get_networks(fabric_id)` | `fabric_id: str` | `dict` or `None` | Get fabric networks |
| `get_configured_fabric()` | None | `dict` or `None` | Get configured fabric details by name |
| `get_configured_fabric_switches()` | None | `dict` or `None` | Get switches for configured fabric |
| `get_configured_fabric_vrfs()` | None | `dict` or `None` | Get VRFs for configured fabric |
| `get_configured_fabric_networks()` | None | `dict` or `None` | Get networks for configured fabric |
| `test_connection()` | None | `dict` | Test connection and return status |
| `close()` | None | None | Close HTTP session |

## Troubleshooting

### Configuration Not Found

```python
# Error: Configuration file not found
```

**Solution**: Configure ACI via the Admin panel in the web interface.

### Authentication Failed

```python
# Error: GET request failed: 401 - Unauthorized
```

**Solution**: Verify your API key and username in the Admin panel. Ensure the API key has the necessary permissions in ACI.

### Connection Timeout

```python
# Error: GET request failed: Connection timeout
```

**Solution**:
1. Verify the ACI URL is correct
2. Ensure network connectivity to ACI
3. Check firewall rules

### SSL Certificate Errors

```python
# Error: SSL certificate verification failed
```

**Solution**: Either configure proper SSL certificates or use `verify=False` (not recommended for production).

## Security Considerations

1. **API Keys**: Stored in `yaml/config.yaml` (gitignored)
2. **SSL**: Currently disabled - enable for production
3. **Header Authentication**: Username and API key sent in headers (`X-Nd-Username`, `X-Nd-Apikey`)
4. **Session Persistence**: Headers stored in session object for the lifetime of the client
5. **Logging**: Sensitive data should not be logged
6. **Timeout**: All requests have 30-second timeout

## Contributing

When adding new ACI API methods:

1. Add method to `ACIClient` class in `aci.py`
2. Add corresponding Flask endpoint in `app.py`
3. Update this documentation
4. Add example usage
