// ACI specific JavaScript
// Handles all ACI API related tables and visualizations

/**
 * Initialize ACI table for a specific page
 */
function initializeAciTableForPage(page, commonConfig, tableInstances) {
    // Initialize ACI Tenants Table
    if (page === 'aci-tenants' && document.getElementById('aciTenantsTable') && !tableInstances['aciTenantsTable']) {
        tableInstances['aciTenantsTable'] = new Tabulator("#aciTenantsTable", {
            ...commonConfig,
            ajaxURL: '/api/v1/aci/tenants',
            columns: [
                {
                    title: "Tenant Name",
                    field: "name",
                    formatter: (cell) => `<strong>${cell.getValue()}</strong>`,
                    sorter: "string",
                    headerFilter: "input"
                },
                {
                    title: "Distinguished Name",
                    field: "dn",
                    sorter: "string",
                    headerFilter: "input"
                },
                {
                    title: "Description",
                    field: "descr",
                    sorter: "string",
                    formatter: (cell) => {
                        const value = cell.getValue();
                        return value || '<em class="text-muted">No description</em>';
                    }
                },
                {
                    title: "Name Alias",
                    field: "nameAlias",
                    sorter: "string",
                    formatter: (cell) => {
                        const value = cell.getValue();
                        return value || '<em class="text-muted">No alias</em>';
                    }
                },
                {
                    title: "Status",
                    field: "status",
                    sorter: "string",
                    formatter: (cell) => {
                        const value = cell.getValue();
                        const badgeClass = value === 'created' ? 'bg-success' :
                                          value === 'modified' ? 'bg-warning' :
                                          value === 'deleted' ? 'bg-danger' : 'bg-secondary';
                        return `<span class="badge ${badgeClass}">${value || 'N/A'}</span>`;
                    }
                },
                {
                    title: "Modified Time",
                    field: "modTs",
                    sorter: "string",
                    formatter: (cell) => {
                        const value = cell.getValue();
                        if (value) {
                            // ACI timestamps are in format like "2024-01-15T10:30:45.123+00:00"
                            try {
                                return new Date(value).toLocaleString();
                            } catch (e) {
                                return value;
                            }
                        }
                        return '<em class="text-muted">N/A</em>';
                    }
                },
                {
                    title: "Actions",
                    field: "name",
                    headerSort: false,
                    formatter: (cell) => {
                        const tenantName = cell.getValue();
                        return `<button class="btn btn-sm btn-primary view-tenant-details" data-tenant-name="${tenantName}">
                                    <i class="bi bi-eye"></i> View Details
                                </button>`;
                    },
                    width: 150
                }
            ],
            initialSort: [{ column: "name", dir: "asc" }]
        });
    }

    console.log(`ACI Tabulator table initialized for page: ${page}`);
}


/**
 * Handle view tenant details button clicks
 * Uses event delegation since buttons are dynamically created by Tabulator
 */
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('view-tenant-details') ||
        event.target.closest('.view-tenant-details')) {

        const button = event.target.classList.contains('view-tenant-details') ?
                       event.target : event.target.closest('.view-tenant-details');
        const tenantName = button.getAttribute('data-tenant-name');

        if (tenantName) {
            viewAciTenantDetails(tenantName);
        }
    }
});


/**
 * Fetch and display ACI tenant details
 * @param {string} tenantName - Name of the tenant to retrieve
 */
async function viewAciTenantDetails(tenantName) {
    try {
        // Show loading indicator
        const loadingToast = createToast('Loading tenant details...', 'info');

        // Fetch tenant details from API
        const response = await fetch(`/api/v1/aci/tenants/${tenantName}`);
        const result = await response.json();

        // Remove loading toast
        if (loadingToast && loadingToast.hide) {
            loadingToast.hide();
        }

        if (response.ok && result.status === 'success') {
            // Display tenant details in a modal
            displayTenantDetailsModal(result.data);
        } else {
            // Show error message
            createToast(result.message || 'Failed to retrieve tenant details', 'error');
        }
    } catch (error) {
        console.error('Error fetching tenant details:', error);
        createToast('Error fetching tenant details: ' + error.message, 'error');
    }
}


/**
 * Display tenant details in a Bootstrap modal
 * @param {Object} tenantData - Tenant data object
 */
function displayTenantDetailsModal(tenantData) {
    // Generate object counts HTML if available
    let countsHtml = '';
    if (tenantData.counts) {
        const counts = tenantData.counts;
        countsHtml = `
            <div class="row mt-3">
                <div class="col-12">
                    <div class="card border-primary">
                        <div class="card-header bg-primary text-white">
                            <h6 class="mb-0"><i class="bi bi-bar-chart"></i> Tenant Object Counts</h6>
                        </div>
                        <div class="card-body">
                            <div class="row g-3">
                                ${createCountCard('Application Profiles', counts.application_profiles, 'bi-app', 'primary')}
                                ${createCountCard('EPGs', counts.epgs, 'bi-diagram-3', 'success')}
                                ${createCountCard('Bridge Domains', counts.bridge_domains, 'bi-hdd-network', 'info')}
                                ${createCountCard('VRFs/Contexts', counts.vrfs, 'bi-router', 'warning')}
                                ${createCountCard('Contracts', counts.contracts, 'bi-file-earmark-text', 'secondary')}
                                ${createCountCard('Filters', counts.filters, 'bi-funnel', 'dark')}
                                ${createCountCard('Subnets', counts.subnets, 'bi-globe2', 'cyan')}
                                ${createCountCard('L3 Outs', counts.l3outs, 'bi-arrow-left-right', 'purple')}
                                ${createCountCard('External EPGs', counts.external_epgs, 'bi-cloud', 'orange')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    const modalHtml = `
        <div class="modal fade" id="tenantDetailsModal" tabindex="-1" aria-labelledby="tenantDetailsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title" id="tenantDetailsModalLabel">
                            <i class="bi bi-building"></i> Tenant Details: ${tenantData.name || 'N/A'}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-body">
                                        <h6 class="card-subtitle mb-2 text-muted"><i class="bi bi-info-circle"></i> Basic Information</h6>
                                        <table class="table table-sm table-borderless">
                                            <tr>
                                                <td class="fw-bold">Name:</td>
                                                <td>${tenantData.name || 'N/A'}</td>
                                            </tr>
                                            <tr>
                                                <td class="fw-bold">Distinguished Name:</td>
                                                <td><code class="text-primary">${tenantData.dn || 'N/A'}</code></td>
                                            </tr>
                                            <tr>
                                                <td class="fw-bold">Description:</td>
                                                <td>${tenantData.descr || '<em class="text-muted">No description</em>'}</td>
                                            </tr>
                                            <tr>
                                                <td class="fw-bold">Name Alias:</td>
                                                <td>${tenantData.nameAlias || '<em class="text-muted">No alias</em>'}</td>
                                            </tr>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-body">
                                        <h6 class="card-subtitle mb-2 text-muted"><i class="bi bi-clock-history"></i> Status Information</h6>
                                        <table class="table table-sm table-borderless">
                                            <tr>
                                                <td class="fw-bold">Status:</td>
                                                <td>
                                                    <span class="badge ${
                                                        tenantData.status === 'created' ? 'bg-success' :
                                                        tenantData.status === 'modified' ? 'bg-warning' :
                                                        tenantData.status === 'deleted' ? 'bg-danger' : 'bg-secondary'
                                                    }">${tenantData.status || 'N/A'}</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td class="fw-bold">Modified Time:</td>
                                                <td>${tenantData.modTs ? new Date(tenantData.modTs).toLocaleString() : 'N/A'}</td>
                                            </tr>
                                            <tr>
                                                <td class="fw-bold">UID:</td>
                                                <td><code class="text-secondary">${tenantData.uid || 'N/A'}</code></td>
                                            </tr>
                                            <tr>
                                                <td class="fw-bold">RN:</td>
                                                <td><code class="text-secondary">${tenantData.rn || 'N/A'}</code></td>
                                            </tr>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                        ${countsHtml}
                        <div class="row mt-3">
                            <div class="col-12">
                                <div class="card">
                                    <div class="card-body">
                                        <h6 class="card-subtitle mb-2 text-muted"><i class="bi bi-code-square"></i> Raw JSON Data</h6>
                                        <pre class="rounded" style="max-height: 300px; overflow-y: auto;"><code id="tenantJsonContent" class="language-json">${JSON.stringify(tenantData, null, 2)}</code></pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x-circle"></i> Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('tenantDetailsModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Apply syntax highlighting to JSON content
    const jsonCodeElement = document.getElementById('tenantJsonContent');
    if (jsonCodeElement && typeof hljs !== 'undefined') {
        hljs.highlightElement(jsonCodeElement);
    }

    // Show the modal using Bootstrap 5 Modal API
    const modalElement = document.getElementById('tenantDetailsModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();

    // Clean up modal after it's hidden
    modalElement.addEventListener('hidden.bs.modal', function () {
        modalElement.remove();
    });
}


/**
 * Create a count card HTML for display
 * @param {string} label - Label for the object type
 * @param {number} count - Count of objects
 * @param {string} icon - Bootstrap icon class
 * @param {string} color - Color theme
 * @returns {string} HTML for the count card
 */
function createCountCard(label, count, icon, color) {
    // Custom color classes for non-standard Bootstrap colors
    const colorStyles = {
        'cyan': 'border-info bg-info bg-opacity-10',
        'purple': 'border-primary bg-primary bg-opacity-10',
        'orange': 'border-warning bg-warning bg-opacity-10'
    };

    const cardClass = colorStyles[color] || `border-${color}`;
    const textClass = color === 'cyan' ? 'text-info' :
                      color === 'purple' ? 'text-primary' :
                      color === 'orange' ? 'text-warning' :
                      `text-${color}`;

    return `
        <div class="col-md-4 col-sm-6">
            <div class="card ${cardClass} h-100">
                <div class="card-body text-center">
                    <i class="bi ${icon} ${textClass}" style="font-size: 2rem;"></i>
                    <h3 class="mt-2 mb-0 ${textClass}">${count}</h3>
                    <p class="text-muted small mb-0">${label}</p>
                </div>
            </div>
        </div>
    `;
}


/**
 * Create a toast notification (helper function)
 * @param {string} message - Toast message
 * @param {string} type - Toast type (success, error, info, warning)
 * @returns {Object} Toast instance
 */
function createToast(message, type = 'info') {
    // This is a placeholder - you may have a different toast implementation in app.js
    // If app.js has a toast function, use that instead
    console.log(`[${type.toUpperCase()}] ${message}`);

    // If Bootstrap toast container exists, use it
    const toastContainer = document.querySelector('.toast-container');
    if (toastContainer) {
        const toastId = 'toast-' + Date.now();
        const bgClass = type === 'success' ? 'bg-success' :
                       type === 'error' ? 'bg-danger' :
                       type === 'warning' ? 'bg-warning' : 'bg-info';

        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();

        return toast;
    }

    return null;
}


