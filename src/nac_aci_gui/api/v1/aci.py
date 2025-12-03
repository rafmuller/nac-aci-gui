"""
ACI API endpoints
"""
from flask import Blueprint, jsonify, request
from ...aci import get_aci_client, ACIClient

aci_bp = Blueprint('aci', __name__)


@aci_bp.route('/test-connection', methods=['GET', 'POST'])
def test_aci_connection():
    """
    Test connection to ACI
    ---
    tags:
      - ACI
    summary: Test ACI connectivity
    description: Tests the connection to ACI using configured credentials or provided parameters and verifies fabric existence
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            aci_url:
              type: string
              description: ACI URL
              example: "https://10.15.0.122"
            aci_username:
              type: string
              description: ACI username
              example: "admin"
            aci_api_key:
              type: string
              description: ACI API key
              example: "your-api-key"
    responses:
      200:
        description: Connection test result
        schema:
          type: object
          properties:
            status:
              type: string
              enum: [success, error]
              example: success
            message:
              type: string
              example: "Successfully connected to ACI and verified fabric 'nac-tf-fabric1'"
            fabrics_count:
              type: integer
              example: 1
            configured_fabric:
              type: string
              example: "nac-tf-fabric1"
            fabric_found:
              type: boolean
              example: true
      500:
        description: Connection test failed
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: "Connection test failed: Connection timeout"
    """
    try:
        # Check if configuration parameters are provided in request body
        if request.method == 'POST' and request.is_json:
            data = request.get_json()

            # Validate that credentials contain only ASCII/Latin-1 characters
            # Strip whitespace to remove any hidden characters
            username = data.get('aci_username', '').strip()
            password = data.get('aci_password', '').strip()

            try:
                if username:
                    username.encode('latin-1')
                if password:
                    password.encode('latin-1')
            except UnicodeEncodeError:
                return jsonify({
                    'status': 'error',
                    'message': 'Username and password must contain only ASCII/Latin-1 characters. Please remove any special Unicode characters, emojis, or non-ASCII symbols.'
                }), 400

            # Create a temporary client with provided parameters
            client = ACIClient(
                base_url=data.get('aci_url'),
                username=username,
                password=password
            )
        else:
            # Use the singleton client with saved configuration
            client = get_aci_client()

        result = client.test_connection()
        return jsonify(result)
    except ValueError as e:
        # Handle validation errors (e.g., invalid characters in credentials)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Connection test failed: {str(e)}'
        }), 500


@aci_bp.route('/config-status', methods=['GET'])
def get_aci_config_status():
    """
    Get current ACI configuration status (for diagnostics)
    ---
    tags:
      - ACI
    summary: Get configuration status
    description: Returns the current configuration state loaded by the singleton client (sensitive data masked)
    responses:
      200:
        description: Configuration status
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            configured:
              type: boolean
              example: true
            base_url:
              type: string
              example: "https://10.15.0.122"
            username:
              type: string
              example: "admin"
            api_key_set:
              type: boolean
              example: true
    """
    try:
        client = get_aci_client()

        return jsonify({
            'status': 'success',
            'configured': all([client.base_url, client.username, client.api_key]),
            'base_url': client.base_url or '',
            'username': client.username or '',
            'api_key_set': bool(client.api_key),
            'api_key_preview': client.api_key[:10] + '...' if client.api_key else ''
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get config status: {str(e)}'
        }), 500



@aci_bp.route('/tenants', methods=['GET'])
def get_aci_tenants():
    """
    Get all tenants from ACI fabric
    ---
    tags:
      - ACI
    summary: Get ACI tenants
    description: Retrieves list of tenants configured on the ACI fabric
    responses:
      200:
        description: Tenants retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                    example: "common"
                  dn:
                    type: string
                    example: "uni/tn-common"
                  descr:
                    type: string
                    example: "Common tenant"
                  status:
                    type: string
                    example: "created"
      500:
        description: Failed to retrieve tenants
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: "Failed to retrieve tenants: Connection error"
    """
    try:
        client = get_aci_client()
        tenants = client.get('/api/class/fvTenant.json')

        if tenants is not None:
            # Extract tenant data from ACI response format
            tenant_list = []
            if 'imdata' in tenants:
                for item in tenants['imdata']:
                    if 'fvTenant' in item:
                        tenant_attrs = item['fvTenant']['attributes']
                        tenant_list.append({
                            'name': tenant_attrs.get('name', ''),
                            'dn': tenant_attrs.get('dn', ''),
                            'descr': tenant_attrs.get('descr', ''),
                            'status': tenant_attrs.get('status', ''),
                            'uid': tenant_attrs.get('uid', ''),
                            'nameAlias': tenant_attrs.get('nameAlias', ''),
                            'lcOwn': tenant_attrs.get('lcOwn', ''),
                            'modTs': tenant_attrs.get('modTs', ''),
                            'rn': tenant_attrs.get('rn', '')
                        })

            return jsonify({
                'status': 'success',
                'data': tenant_list
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to retrieve tenants from ACI'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve tenants: {str(e)}'
        }), 500


@aci_bp.route('/tenants/<tenant_name>', methods=['GET'])
def get_aci_tenant(tenant_name):
    """
    Get specific tenant details from ACI fabric
    ---
    tags:
      - ACI
    summary: Get specific ACI tenant with subtree
    description: Retrieves detailed information for a specific tenant including counts of child objects
    parameters:
      - in: path
        name: tenant_name
        type: string
        required: true
        description: Name of the tenant to retrieve
        example: "common"
    responses:
      200:
        description: Tenant retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              type: object
              properties:
                name:
                  type: string
                  example: "common"
                dn:
                  type: string
                  example: "uni/tn-common"
                descr:
                  type: string
                  example: "Common tenant"
                counts:
                  type: object
                  properties:
                    epgs:
                      type: integer
                      example: 5
                    bridge_domains:
                      type: integer
                      example: 3
                    vrfs:
                      type: integer
                      example: 2
      404:
        description: Tenant not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: "Tenant 'test' not found"
      500:
        description: Failed to retrieve tenant
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: "Failed to retrieve tenant: Connection error"
    """
    try:
        client = get_aci_client()
        tenant_response = client.get_tenant(tenant_name, include_subtree=True)

        if tenant_response is not None and 'imdata' in tenant_response:
            imdata = tenant_response['imdata']

            if len(imdata) == 0:
                return jsonify({
                    'status': 'error',
                    'message': f"Tenant '{tenant_name}' not found"
                }), 404

            # Extract basic tenant data and children from fvTenant
            tenant_data = {}
            children = []

            if 'fvTenant' in imdata[0]:
                tenant_obj = imdata[0]['fvTenant']
                tenant_attrs = tenant_obj.get('attributes', {})
                tenant_data = {
                    'name': tenant_attrs.get('name', ''),
                    'dn': tenant_attrs.get('dn', ''),
                    'descr': tenant_attrs.get('descr', ''),
                    'status': tenant_attrs.get('status', ''),
                    'uid': tenant_attrs.get('uid', ''),
                    'nameAlias': tenant_attrs.get('nameAlias', ''),
                    'lcOwn': tenant_attrs.get('lcOwn', ''),
                    'modTs': tenant_attrs.get('modTs', ''),
                    'rn': tenant_attrs.get('rn', '')
                }

                # Get children array from tenant
                children = tenant_obj.get('children', [])

            # Count child objects by class
            object_counts = {
                'application_profiles': 0,  # fvAp
                'epgs': 0,                   # fvAEPg
                'bridge_domains': 0,         # fvBD
                'vrfs': 0,                   # fvCtx (Context/VRF)
                'contracts': 0,              # vzBrCP
                'filters': 0,                # vzFilter
                'subnets': 0,                # fvSubnet
                'l3outs': 0,                 # l3extOut
                'external_epgs': 0,          # l3extInstP
            }

            # ACI class name to friendly name mapping
            class_mapping = {
                'fvAp': 'application_profiles',
                'fvAEPg': 'epgs',
                'fvBD': 'bridge_domains',
                'fvCtx': 'vrfs',
                'vzBrCP': 'contracts',
                'vzFilter': 'filters',
                'fvSubnet': 'subnets',
                'l3extOut': 'l3outs',
                'l3extInstP': 'external_epgs',
            }

            # Recursive function to count objects in the tree
            def count_objects_recursive(items):
                for item in items:
                    # Check each possible ACI class
                    for aci_class, friendly_name in class_mapping.items():
                        if aci_class in item:
                            object_counts[friendly_name] += 1
                            # Recursively process children if they exist
                            child_obj = item[aci_class]
                            if 'children' in child_obj:
                                count_objects_recursive(child_obj['children'])

            # Count all objects starting from tenant's children
            count_objects_recursive(children)

            # Add counts to tenant data
            tenant_data['counts'] = object_counts

            return jsonify({
                'status': 'success',
                'data': tenant_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to retrieve tenant from ACI'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve tenant: {str(e)}'
        }), 500
