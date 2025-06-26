// Dashboard functionality
let currentUser = null;
let selectedFile = null;
let extractionResults = [];

// Backend configuration
const BACKEND_URL = 'http://localhost:5000'; // Change this to your Flask server URL

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async function() {
    console.log('=== DASHBOARD INITIALIZATION ===');
    console.log('BACKEND_URL:', BACKEND_URL);
    
    // Test backend connectivity
    await testBackendConnectivity();
    
    // Initialize file upload functionality
    initializeFileUpload();
    
    // Initialize chat functionality
    initializeChat();
    
    // Load user settings
    loadSettings();
    
    // Fetch saved data
    await fetchSavedData();
    
    // Authentication state is handled by Firebase onAuthStateChanged in dashboard.html
});

async function logout() {
    try {
        await window.signOut(window.auth);
        console.log('User signed out successfully');
        // Firebase onAuthStateChanged will handle the redirect
    } catch (error) {
        console.error('Error signing out:', error);
        // Fallback redirect if signOut fails
        window.location.href = 'index.html';
    }
}

// Navigation functions
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.dashboard-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active class from all nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(sectionName + 'Section').classList.add('active');
    
    // Add active class to clicked nav button
    document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
}

// File Upload Functions
function initializeFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.querySelector('.file-drop-zone');
    
    // Handle file input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Handle drag and drop
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('drop', handleFileDrop);
    dropZone.addEventListener('dragleave', handleDragLeave);
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#667eea';
    e.currentTarget.style.background = 'rgba(102, 126, 234, 0.05)';
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#ddd';
    e.currentTarget.style.background = 'transparent';
}

function handleFileDrop(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#ddd';
    e.currentTarget.style.background = 'transparent';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (isValidFile(file)) {
            selectedFile = file;
            displayFile(file);
        } else {
            showError('Please select a valid file (PDF, DOCX, TXT)');
        }
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        const file = files[0];
        if (isValidFile(file)) {
            selectedFile = file;
            displayFile(file);
        } else {
            showError('Please select a valid file (PDF, DOCX, TXT)');
        }
    }
}

function isValidFile(file) {
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'text/plain'];
    const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt'];
    
    return allowedTypes.includes(file.type) || allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
}

function displayFile(file) {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.style.cssText = `
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 8px;
    `;
    
    const fileIcon = getFileIcon(file.name);
    
    fileItem.innerHTML = `
        <div>
            <i class="${fileIcon}" style="color: #667eea; margin-right: 8px;"></i>
            <span>${file.name}</span>
            <small style="color: #999; margin-left: 10px;">(${formatFileSize(file.size)})</small>
        </div>
        <button onclick="clearSelectedFile()" style="background: none; border: none; color: #e74c3c; cursor: pointer;">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    fileList.appendChild(fileItem);
}

function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    switch (extension) {
        case 'pdf':
            return 'fas fa-file-pdf';
        case 'docx':
        case 'doc':
            return 'fas fa-file-word';
        case 'txt':
            return 'fas fa-file-alt';
        default:
            return 'fas fa-file';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function clearSelectedFile() {
    selectedFile = null;
    document.getElementById('fileList').innerHTML = '';
    document.getElementById('fileInput').value = '';
}

async function uploadFiles() {
    if (!selectedFile) {
        showError('Please select a file to upload');
        return;
    }
    
    const contentType = document.getElementById('fileContentType').value;
    if (!contentType) {
        showError('Please select a content type');
        return;
    }
    
    const uploadBtn = document.querySelector('.upload-card .primary-btn');
    const originalText = uploadBtn.innerHTML;
    
    uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    uploadBtn.disabled = true;
    
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('content_type', contentType);
        
        const response = await fetch(`${BACKEND_URL}/api/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            uploadBtn.innerHTML = '<i class="fas fa-check"></i> Processing Complete';
            uploadBtn.style.background = '#28a745';
            
            // Add to results
            extractionResults.unshift(result);
            displayResults();
            
            // Clear file selection
            setTimeout(() => {
                clearSelectedFile();
                uploadBtn.innerHTML = originalText;
                uploadBtn.style.background = '';
                uploadBtn.disabled = false;
            }, 2000);
        } else {
            throw new Error(result.error || 'Upload failed');
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        showError(`Upload failed: ${error.message}`);
        
        uploadBtn.innerHTML = originalText;
        uploadBtn.style.background = '';
        uploadBtn.disabled = false;
    }
}

// URL Scraping Functions
async function scrapeUrl() {
    const url = document.getElementById('scrapeUrl').value.trim();
    if (!url) {
        showError('Please enter a URL to scrape');
        return;
    }
    
    const contentType = document.getElementById('urlContentType').value;
    if (!contentType) {
        showError('Please select a content type');
        return;
    }
    
    const progressBar = document.getElementById('scrapeProgress');
    const processingStatus = document.getElementById('processingStatus');
    const scrapeBtn = document.querySelector('.upload-card:last-child .primary-btn');
    const originalText = scrapeBtn.innerHTML;
    
    progressBar.style.display = 'block';
    processingStatus.style.display = 'block';
    scrapeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Extracting...';
    scrapeBtn.disabled = true;
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/scrape`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                content_type: contentType
            })
        });
        
        const result = await response.json();
        
        progressBar.style.display = 'none';
        processingStatus.style.display = 'none';
        
        if (response.ok) {
            scrapeBtn.innerHTML = '<i class="fas fa-check"></i> Extraction Complete';
            scrapeBtn.style.background = '#28a745';
            
            // Add to results
            extractionResults.unshift(result);
            displayResults();
            
            // Clear URL input
            setTimeout(() => {
                document.getElementById('scrapeUrl').value = '';
                scrapeBtn.innerHTML = originalText;
                scrapeBtn.style.background = '';
                scrapeBtn.disabled = false;
            }, 2000);
        } else {
            throw new Error(result.error || 'Scraping failed');
        }
        
    } catch (error) {
        console.error('Scraping error:', error);
        showError(`Scraping failed: ${error.message}`);
        
        progressBar.style.display = 'none';
        processingStatus.style.display = 'none';
        scrapeBtn.innerHTML = originalText;
        scrapeBtn.style.background = '';
        scrapeBtn.disabled = false;
    }
}

// Results Display Functions
function displayResults() {
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent');
    
    if (extractionResults.length === 0) {
        resultsSection.style.display = 'none';
        return;
    }
    
    resultsSection.style.display = 'block';
    resultsContent.innerHTML = '';
    
    extractionResults.forEach((result, index) => {
        const resultCard = createResultCard(result, index);
        resultsContent.appendChild(resultCard);
    });
}

function createResultCard(result, index) {
    const resultDiv = document.createElement('div');
    resultDiv.className = `result-card ${result.success ? 'success-result' : 'error-result'}`;
    
    const sourceIcon = result.source === 'file' ? 'fas fa-file' : 'fas fa-globe';
    const sourceText = result.source === 'file' ? 'File Upload' : 'URL Scraping';
    
    // Format the data for display with proper indentation
    const formatData = (data) => {
        try {
            return JSON.stringify(data, null, 2);
        } catch (e) {
            return String(data);
        }
    };

    resultDiv.innerHTML = `
        <div class="result-header">
            <div class="result-info">
                <div class="result-source">
                    <i class="${sourceIcon}"></i>
                    ${sourceText}
                </div>
                <div class="result-title">
                    ${result.filename || result.url || 'Unknown Source'}
                </div>
                <div class="result-subtitle">
                    Content Type: ${result.content_type}
                </div>
            </div>
            ${result.stats ? `
                <div class="result-stats">
                    <div><strong>Items:</strong> ${result.stats.items_extracted || 0}</div>
                    <div><strong>Tokens:</strong> ${result.stats.total_tokens || 0}</div>
                    <div><strong>Cost:</strong> $${(result.stats.cost_usd || 0).toFixed(4)}</div>
                </div>
            ` : ''}
        </div>
        
        ${result.success ? `
            <div class="result-data">
                <pre>${formatData(result.data)}</pre>
            </div>
            <div class="result-actions">
                <button class="save-btn" onclick="saveToDatabase(${index})">
                    <i class="fas fa-save"></i>
                    Save to Database
                </button>
            </div>
        ` : `
            <div class="error-message">${result.error}</div>
        `}
    `;
    
    return resultDiv;
}

function exportResults() {
    if (extractionResults.length === 0) {
        showError('No results to export');
        return;
    }
    
    const dataStr = JSON.stringify(extractionResults, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `extraction_results_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
}

function clearResults() {
    if (confirm('Are you sure you want to clear all results?')) {
        extractionResults = [];
        displayResults();
    }
}

// Data Table Functions
function updateDataTable() {
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent');
    
    if (extractionResults.length === 0) {
        resultsSection.style.display = 'none';
        return;
    }
    
    resultsSection.style.display = 'block';
    resultsContent.innerHTML = '';
    
    extractionResults.forEach((result, index) => {
        const resultCard = createResultCard(result, index);
        resultsContent.appendChild(resultCard);
    });
}

function createResultCard(result, index) {
    const resultDiv = document.createElement('div');
    resultDiv.className = `result-card ${result.success ? 'success-result' : 'error-result'}`;
    
    const sourceIcon = result.source === 'file' ? 'fas fa-file' : 'fas fa-globe';
    const sourceText = result.source === 'file' ? 'File Upload' : 'URL Scraping';
    
    // Format the data for display with proper indentation
    const formatData = (data) => {
        try {
            return JSON.stringify(data, null, 2);
        } catch (e) {
            return String(data);
        }
    };

    resultDiv.innerHTML = `
        <div class="result-header">
            <div class="result-info">
                <div class="result-source">
                    <i class="${sourceIcon}"></i>
                    ${sourceText}
                </div>
                <div class="result-title">
                    ${result.filename || result.url || 'Unknown Source'}
                </div>
                <div class="result-subtitle">
                    Content Type: ${result.content_type}
                </div>
            </div>
            ${result.stats ? `
                <div class="result-stats">
                    <div><strong>Items:</strong> ${result.stats.items_extracted || 0}</div>
                    <div><strong>Tokens:</strong> ${result.stats.total_tokens || 0}</div>
                    <div><strong>Cost:</strong> $${(result.stats.cost_usd || 0).toFixed(4)}</div>
                </div>
            ` : ''}
        </div>
        
        ${result.success ? `
            <div class="result-data">
                <pre>${formatData(result.data)}</pre>
            </div>
            <div class="result-actions">
                <button class="save-btn" onclick="saveToDatabase(${index})">
                    <i class="fas fa-save"></i>
                    Save to Database
                </button>
            </div>
        ` : `
            <div class="error-message">${result.error}</div>
        `}
    `;
    
    return resultDiv;
}

function exportResults() {
    if (extractionResults.length === 0) {
        showError('No results to export');
        return;
    }
    
    const dataStr = JSON.stringify(extractionResults, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `extraction_results_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
}

function clearResults() {
    if (confirm('Are you sure you want to clear all results?')) {
        extractionResults = [];
        displayResults();
    }
}

// Data Management Functions
async function fetchData() {
    try {
        const tbody = document.querySelector('#dataTable tbody');
        if (!tbody) {
            console.error('Data table body not found');
            return;
        }

        // Show loading state
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="loading-state">
                    <i class="fas fa-spinner fa-spin"></i>
                    Loading your data...
                </td>
            </tr>
        `;

        console.log('Fetching data from:', `${BACKEND_URL}/api/data`);
        const response = await fetch(`${BACKEND_URL}/api/data`);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch data: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Raw response data:', data);

        // Validate the response data
        if (!Array.isArray(data)) {
            throw new Error('Invalid response format from server');
        }

        // Display the data
        if (data.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <div class="empty-message">No data available</div>
                        <button class="add-btn" onclick="showAddDataModal()">
                            <i class="fas fa-plus"></i> Add New Data
                        </button>
                    </td>
                </tr>
            `;
            return;
        }

        displayData(data);
    } catch (error) {
        console.error('Error fetching data:', error);
        const tbody = document.querySelector('#dataTable tbody');
        if (!tbody) return;

        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="error-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <div class="error-message">${error.message}</div>
                    <button class="retry-btn" onclick="fetchData()">
                        <i class="fas fa-sync-alt"></i> Retry
                    </button>
                </td>
            </tr>
        `;
    }
}

function displayData(data) {
    const tbody = document.querySelector('#dataTable tbody');
    if (!tbody) {
        console.error('Data table body not found');
        return;
    }

    tbody.innerHTML = '';

    // Validate data
    if (!data || !Array.isArray(data)) {
        console.error('Invalid data format:', data);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="error-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <div class="error-message">Invalid data format received</div>
                    <button class="retry-btn" onclick="fetchData()">
                        <i class="fas fa-sync-alt"></i> Retry
                    </button>
                </td>
            </tr>
        `;
        return;
    }

    // Check for empty data
    if (data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <div class="empty-message">No data available</div>
                    <button class="add-btn" onclick="showAddDataModal()">
                        <i class="fas fa-plus"></i> Add New Data
                    </button>
                </td>
            </tr>
        `;
        return;
    }

    // Process each item
    data.forEach((item) => {
        if (!item) {
            console.warn('Skipping null or undefined item');
            return;
        }

        // Get the nested data array
        const products = Array.isArray(item.data) ? item.data : [];
        
        // Create a row for each product in the data array
        products.forEach((product, index) => {
            const row = document.createElement('tr');
            row.dataset.id = item.id || '';
            row.dataset.productIndex = index;
            
            // Store the full product data as a data attribute
            row.setAttribute('data-full', JSON.stringify(product));
            
            // Get all fields from the product object with safe fallbacks
            const name = product.name || '';
            const description = product.description || '';
            const price = product.price || '';
            const category = product.category || '';
            const availability = product.availability || '';
            const sku = product.sku || '';
            
            row.innerHTML = `
                <td>${item.id || ''}</td>
                <td>${item.content_type || ''}</td>
                <td>${name}</td>
                <td class="description-cell" title="${description}">
                    ${truncateText(description, 100)}
                </td>
                <td>${price}</td>
                <td>${category}</td>
                <td>${availability}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn view-btn" onclick="viewDataDetails('${item.id || ''}', ${index})">
                            <i class="fas fa-eye"></i> View
                        </button>
                        <button class="action-btn edit-btn" onclick="showEditDataModal('${item.id || ''}', ${index})">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="action-btn delete-btn" onclick="deleteData('${item.id || ''}')">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </td>
            `;
            
            tbody.appendChild(row);
        });
    });
}

function showAddDataModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Add New Product</h3>
                <button class="close-btn" onclick="this.closest('.modal').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label for="productName">Product Name</label>
                    <input type="text" id="productName" placeholder="Enter product name" required>
                </div>
                <div class="form-group">
                    <label for="description">Description</label>
                    <textarea id="description" placeholder="Enter product description"></textarea>
                </div>
                <div class="form-group">
                    <label for="price">Price</label>
                    <input type="text" id="price" placeholder="Enter price (e.g., $99.99)" required>
                </div>
                <div class="form-group">
                    <label for="category">Category</label>
                    <input type="text" id="category" placeholder="Enter category">
                </div>
                <div class="form-group">
                    <label for="availability">Availability</label>
                    <input type="text" id="availability" placeholder="Enter availability status">
                </div>
                <div class="form-group">
                    <label for="sku">SKU</label>
                    <input type="text" id="sku" placeholder="Enter SKU">
                </div>
            </div>
            <div class="modal-footer">
                <button class="cancel-btn" onclick="this.closest('.modal').remove()">Cancel</button>
                <button class="save-btn" onclick="saveNewData(this)">Save Product</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

async function saveNewData(button) {
    const modal = button.closest('.modal');
    const data = {
        content_type: 'products',
        data: [{
            name: modal.querySelector('#productName').value,
            description: modal.querySelector('#description').value,
            price: modal.querySelector('#price').value,
            category: modal.querySelector('#category').value,
            availability: modal.querySelector('#availability').value,
            sku: modal.querySelector('#sku').value
        }]
    };

    if (!data.data[0].name) {
        showError('Product Name is required');
        return;
    }

    try {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

        const response = await fetch(`${BACKEND_URL}/api/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error('Failed to save data');
        }

        const result = await response.json();
        if (result.success) {
            showSuccess(data.message);
            modal.remove();
            await fetchData(); // Refresh the data
        } else {
            throw new Error(result.error || 'Failed to save data');
        }
    } catch (error) {
        console.error('Save error:', error);
        showError(error.message || 'Failed to save data');
    } finally {
        button.disabled = false;
        button.innerHTML = 'Save Product';
    }
}

function showEditDataModal(id, productIndex) {
    const row = document.querySelector(`tr[data-id="${id}"]`);
    if (!row) {
        console.error('Row not found for ID:', id);
        return;
    }

    // Get the original data from the row's dataset
    const originalData = JSON.parse(row.dataset.originalData || '{}');
    const products = Array.isArray(originalData.data) ? originalData.data : [];
    const product = products[productIndex];

    if (!product) {
        showError('No data found for this item');
        return;
    }

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Edit Product Data</h3>
                <button class="close-btn" onclick="this.closest('.modal').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label for="editName">Product Name</label>
                    <input type="text" id="editName" value="${product.name || ''}" required>
                </div>
                <div class="form-group">
                    <label for="editDescription">Description</label>
                    <textarea id="editDescription" rows="4">${product.description || ''}</textarea>
                </div>
                <div class="form-group">
                    <label for="editPrice">Price</label>
                    <input type="text" id="editPrice" value="${product.price || ''}" placeholder="e.g., $99.99">
                </div>
                <div class="form-group">
                    <label for="editCategory">Category</label>
                    <input type="text" id="editCategory" value="${product.category || ''}">
                </div>
                <div class="form-group">
                    <label for="editAvailability">Availability</label>
                    <input type="text" id="editAvailability" value="${product.availability || ''}">
                </div>
                <div class="form-group">
                    <label for="editSku">SKU</label>
                    <input type="text" id="editSku" value="${product.sku || ''}">
                </div>
            </div>
            <div class="modal-footer">
                <button class="cancel-btn" onclick="this.closest('.modal').remove()">Cancel</button>
                <button class="save-btn" onclick="updateData('${id}', ${productIndex}, this)">Save Changes</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function viewDataDetails(id, productIndex) {
    const row = document.querySelector(`tr[data-id="${id}"][data-product-index="${productIndex}"]`);
    if (!row) return;

    // Get the original data from the row's dataset
    const originalData = JSON.parse(row.dataset.originalData || '{}');
    const products = Array.isArray(originalData.data) ? originalData.data : [];
    const product = products[productIndex];

    if (!product) {
        showError('No data found for this item');
        return;
    }

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Product Details</h3>
                <button class="close-btn" onclick="this.closest('.modal').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="detail-group">
                    <label>ID</label>
                    <div class="detail-value">${originalData.id || ''}</div>
                </div>
                <div class="detail-group">
                    <label>Content Type</label>
                    <div class="detail-value">${originalData.content_type || ''}</div>
                </div>
                <div class="detail-group">
                    <label>Product Name</label>
                    <div class="detail-value">${product.name || ''}</div>
                </div>
                <div class="detail-group">
                    <label>Description</label>
                    <div class="detail-value description">${product.description || ''}</div>
                </div>
                <div class="detail-group">
                    <label>Price</label>
                    <div class="detail-value">${product.price || ''}</div>
                </div>
                <div class="detail-group">
                    <label>Category</label>
                    <div class="detail-value">${product.category || ''}</div>
                </div>
                <div class="detail-group">
                    <label>Availability</label>
                    <div class="detail-value">${product.availability || ''}</div>
                </div>
                <div class="detail-group">
                    <label>SKU</label>
                    <div class="detail-value">${product.sku || ''}</div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="close-btn" onclick="this.closest('.modal').remove()">Close</button>
                <button class="edit-btn" onclick="showEditDataModal('${id}', ${productIndex})">Edit</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

async function updateData(id, productIndex, button) {
    const modal = button.closest('.modal');
    const row = document.querySelector(`tr[data-id="${id}"]`);
    if (!row) {
        showError('Could not find the data to update');
        return;
    }

    // Get the original data
    const originalData = JSON.parse(row.dataset.originalData || '{}');
    const products = Array.isArray(originalData.data) ? originalData.data : [];
    
    // Update the specific product
    products[productIndex] = {
        name: modal.querySelector('#editName').value,
        description: modal.querySelector('#editDescription').value,
        price: modal.querySelector('#editPrice').value,
        category: modal.querySelector('#editCategory').value,
        availability: modal.querySelector('#editAvailability').value,
        sku: modal.querySelector('#editSku').value
    };

    // Prepare the update data
    const updateData = {
        content_type: originalData.content_type,
        data: products
    };

    try {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

        console.log('Sending update request:', {
            url: `${BACKEND_URL}/api/data/${id}`,
            data: updateData
        });

        const response = await fetch(`${BACKEND_URL}/api/data/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });

        console.log('Update response status:', response.status);
        const result = await response.json();
        console.log('Update response:', result);

        if (!response.ok) {
            throw new Error(result.error || 'Failed to update data');
        }

        if (result.success) {
            showSuccess(data.message);
            modal.remove();
            await fetchData(); // Refresh the data
        } else {
            throw new Error(result.error || 'Failed to update data');
        }
    } catch (error) {
        console.error('Update error:', error);
        showError(error.message || 'Failed to update data');
    } finally {
        button.disabled = false;
        button.innerHTML = 'Save Changes';
    }
}

async function deleteData(id) {
    if (!confirm('Are you sure you want to delete this data?')) {
        return;
    }

    try {
        const response = await fetch(`${BACKEND_URL}/api/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id })
        });

        const result = await response.json();

        if (result.success) {
            showSuccess('Data deleted successfully');
            await fetchData(); // Refresh the data
        } else {
            throw new Error(result.error || 'Failed to delete data');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showError(error.message || 'Failed to delete data');
    }
}

// Add event listener for data loading when testing section is shown
document.querySelector('[data-section="testing"]').addEventListener('click', fetchData);

// Initialize data loading when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const testingSection = document.getElementById('testingSection');
    if (testingSection && testingSection.classList.contains('active')) {
        fetchData();
    }
});

// Chat Functions
function testChat() {
    console.log('Test chat function called');
    
    // Get current user ID - use the same logic as sendMessage
    let userId;
    
    // Check if Firebase auth is available and user is logged in
    if (window.auth && window.auth.currentUser) {
        // Use Firebase user ID if available
        userId = window.auth.currentUser.uid;
        console.log('Test using Firebase user ID:', userId);
    } else {
        // Fallback to localStorage user ID (same as storeInChromaDB)
        userId = getCurrentUserId();
        console.log('Test using localStorage user ID:', userId);
    }
    
    // Test message
    const testMessage = "What brownies do you have?";
    
    // Add test message to chat
    addMessage(testMessage, 'user');
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    console.log('Sending test request to:', `${BACKEND_URL}/api/chat`);
    
    // Send test message to backend
    fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            message: testMessage,
            user_id: userId
        })
    })
    .then(response => {
        console.log('Test response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Test response data:', data);
        typingIndicator.remove();
        
        if (data.error) {
            addMessage(`Test Error: ${data.error}`, 'bot');
        } else if (data.response) {
            addMessage(`Test Response: ${data.response}`, 'bot');
        } else {
            addMessage('Test: No response received', 'bot');
        }
    })
    .catch(error => {
        console.error('Test chat error:', error);
        typingIndicator.remove();
        addMessage(`Test Error: ${error.message}`, 'bot');
    });
}

function initializeChat() {
    const chatInput = document.getElementById('chatInput');
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    console.log('=== SEND MESSAGE DEBUG ===');
    console.log('sendMessage called with:', message);
    console.log('BACKEND_URL:', BACKEND_URL);
    
    if (!message) {
        console.log('Empty message, returning');
        return;
    }
    
    // Add user message to chat
    addMessage(message, 'user');
    chatInput.value = '';
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    // Get current user ID - use the same ID as storeInChromaDB
    let userId;
    
    // Check if Firebase auth is available and user is logged in
    if (window.auth && window.auth.currentUser) {
        // Use Firebase user ID if available
        userId = window.auth.currentUser.uid;
        console.log('Using Firebase user ID:', userId);
    } else {
        // Fallback to localStorage user ID (same as storeInChromaDB)
        userId = getCurrentUserId();
        console.log('Using localStorage user ID:', userId);
    }
    
    console.log('Using user ID for chat:', userId);
    console.log('Sending request to:', `${BACKEND_URL}/api/chat`);
    
    const requestBody = { 
        message,
        user_id: userId
    };
    console.log('Request body:', requestBody);
    
    // Send message to backend
    fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        if (!response.ok) {
            return response.json().then(data => {
                console.log('Error response data:', data);
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Success response data:', data);
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add bot response
        if (data.error) {
            console.log('Response contains error:', data.error);
            if (data.error.includes("GEMINI_API_KEY")) {
                addMessage("Hi there! I'm having some technical difficulties right now. Please contact our support team to get me back up and running so I can help you with your bakery questions! 🍰", 'bot');
            } else if (data.error.includes("Failed to retrieve context")) {
                addMessage(data.error, 'bot');
                addMessage("To get started:\n1. Upload your bakery's product data using the 'Upload Data' section\n2. Click 'Store in Database' button in the data table\n3. Then I'll be able to answer all your questions about our delicious treats! 🍰", 'bot');
            } else {
                addMessage(`Oops! I encountered an issue: ${data.error}. Don't worry, I'm here to help once we get this sorted! 😊`, 'bot');
            }
        } else if (data.response.includes("I don't have enough context") || data.response.includes("I couldn't find any relevant information")) {
            // If no data in ChromaDB, provide helpful message
            addMessage(data.response, 'bot');
            addMessage("To get started:\n1. Upload your bakery's product data using the 'Upload Data' section\n2. Click 'Store in Database' button in the data table\n3. Then I'll be able to answer all your questions about our delicious treats! 🍰", 'bot');
        } else {
            // Format the response for better readability
            const formattedResponse = data.response
                .replace(/\n\n/g, '\n') // Remove double newlines
                .replace(/\n/g, '<br>') // Convert newlines to HTML breaks
                .replace(/\d+\.\s/g, '<br><strong>$&</strong>') // Format numbered lists
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Format bold text
                .replace(/\*(.*?)\*/g, '<em>$1</em>'); // Format italic text
                
            addMessage(formattedResponse, 'bot');
            
            // If the response contains metrics or insights, add a suggestion
            if (data.response.includes("$") || data.response.includes("%") || 
                data.response.includes("metric") || data.response.includes("insight")) {
                addMessage("Would you like me to tell you more about any of our products or help you find something specific? I'm here to help! 😊", 'bot');
            }
        }
    })
    .catch(error => {
        console.error('=== FETCH ERROR ===');
        console.error('Error in sendMessage:', error);
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
        removeTypingIndicator();
        addMessage(`Sorry, I encountered an error: ${error.message}. Please check the console for more details.`, 'bot');
    });
}

function addMessage(text, type) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    // Create avatar
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = type === 'user' ? 
        '<i class="fas fa-user"></i>' : 
        '<i class="fas fa-robot"></i>';
    
    // Create message content with proper formatting
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Process the text to handle line breaks and formatting
    let processedText = text
        .replace(/\n\n/g, '</p><p>') // Convert double newlines to paragraph breaks
        .replace(/\n/g, '<br>') // Convert single newlines to line breaks
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Format bold text
        .replace(/\*(.*?)\*/g, '<em>$1</em>') // Format italic text
        .replace(/\d+\.\s/g, '<br><strong>$&</strong>'); // Format numbered lists
    
    // Wrap in paragraph tags if not already wrapped
    if (!processedText.startsWith('<p>') && !processedText.startsWith('<ul>')) {
        processedText = `<p>${processedText}</p>`;
    }
    
    // Set content with strict containment
    contentDiv.innerHTML = processedText;
    contentDiv.style.maxWidth = '100%';
    contentDiv.style.overflow = 'hidden';
    contentDiv.style.wordWrap = 'break-word';
    contentDiv.style.overflowWrap = 'break-word';
    
    // Create timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Assemble message
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timestamp);
    
    // Ensure message doesn't overflow
    messageDiv.style.maxWidth = '75%';
    messageDiv.style.wordWrap = 'break-word';
    messageDiv.style.overflowWrap = 'break-word';
    
    chatMessages.appendChild(messageDiv);
    
    // Smooth scroll to bottom
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
    
    return messageDiv;
}

// Analytics Functions
function getInsights() {
    const query = document.getElementById('insightQuery').value;
    if (!query) {
        showError('Please enter a query to get AI insights');
        return;
    }
    
    const insightBtn = document.querySelector('.insights-card .primary-btn');
    const originalText = insightBtn.innerHTML;
    
    insightBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    insightBtn.disabled = true;
    
    setTimeout(() => {
        insightBtn.innerHTML = originalText;
        insightBtn.disabled = false;
        
        // Generate insight based on extraction results
        addContextualInsight(query);
        document.getElementById('insightQuery').value = '';
    }, 2000);
}

function addContextualInsight(query) {
    const insightsResults = document.getElementById('insightsResults');
    
    let insight;
    if (extractionResults.length > 0) {
        const totalItems = extractionResults.reduce((sum, result) => 
            sum + (result.stats?.items_extracted || 0), 0);
        const totalCost = extractionResults.reduce((sum, result) => 
            sum + (result.stats?.cost_usd || 0), 0);
        
        insight = {
            icon: 'fas fa-chart-bar',
            title: 'Data Analysis Insight',
            description: `Based on your query "${query}" and extracted data: You've processed ${totalItems} items across ${extractionResults.length} extraction(s), with a total processing cost of $${totalCost.toFixed(4)}. This data can provide valuable insights for business optimization and decision-making.`
        };
    } else {
        insight = {
            icon: 'fas fa-lightbulb',
            title: 'Getting Started',
            description: `Regarding "${query}": To provide specific insights, please first upload files or scrape URLs to extract business data. Once you have data, I can analyze patterns, trends, and opportunities relevant to your query.`
        };
    }
    
    const insightDiv = document.createElement('div');
    insightDiv.className = 'insight-card';
    insightDiv.innerHTML = `
        <div class="insight-icon">
            <i class="${insight.icon}"></i>
        </div>
        <div class="insight-content">
            <h5>${insight.title}</h5>
            <p>${insight.description}</p>
        </div>
    `;
    
    insightsResults.insertBefore(insightDiv, insightsResults.firstChild);
}

// Settings Functions
function loadSettings() {
    // Get current user ID - use the same logic as other functions
    let userId;
    
    // Check if Firebase auth is available and user is logged in
    if (window.auth && window.auth.currentUser) {
        // Use Firebase user ID if available
        userId = window.auth.currentUser.uid;
        console.log('Load settings using Firebase user ID:', userId);
    } else {
        // Fallback to localStorage user ID
        userId = getCurrentUserId();
        console.log('Load settings using localStorage user ID:', userId);
    }
    
    fetch(`${BACKEND_URL}/api/settings?user_id=${userId}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const settings = data.settings;
            
            // Telegram settings
            const telegramEnabled = document.getElementById('telegramEnabled');
            const telegramToken = document.getElementById('telegramToken');
            const setupBtn = document.getElementById('setupWebhookBtn');
            const checkBtn = document.getElementById('checkWebhookBtn');
            const testBtn = document.getElementById('testBotBtn');
            const pollBtn = document.getElementById('pollBtn');
            
            if (settings.telegram) {
                telegramEnabled.checked = settings.telegram.enabled || false;
                telegramToken.value = settings.telegram.token || '';
                
                // Show/hide test button based on enabled state
                if (settings.telegram.enabled && settings.telegram.token) {
                    setupBtn.style.display = 'inline-block';
                    checkBtn.style.display = 'inline-block';
                    testBtn.style.display = 'inline-block';
                    pollBtn.style.display = 'inline-block';
                    checkTelegramStatus();
                } else {
                    setupBtn.style.display = 'none';
                    checkBtn.style.display = 'none';
                    testBtn.style.display = 'none';
                    pollBtn.style.display = 'none';
                    hideTelegramStatus();
                }
            }
            
            // WhatsApp settings
            document.getElementById('whatsappEnabled').checked = settings.whatsapp?.enabled || false;
            document.getElementById('whatsappToken').value = settings.whatsapp?.token || '';
            
            // Webhook settings
            document.getElementById('webhookEnabled').checked = settings.webhook?.enabled || false;
            document.getElementById('webhookUrl').value = settings.webhook?.url || '';
            
            // Razorpay settings
            document.getElementById('razorpayEnabled').checked = settings.razorpay?.enabled || false;
            document.getElementById('razorpayKey').value = settings.razorpay?.keyId || '';
            document.getElementById('razorpaySecret').value = settings.razorpay?.secretKey || '';
        }
    })
    .catch(error => {
        console.error('Error loading settings:', error);
    });
}

function saveTelegramSettings() {
    const enabled = document.getElementById('telegramEnabled').checked;
    const token = document.getElementById('telegramToken').value;
    
    // Get current user ID
    let userId;
    if (window.auth && window.auth.currentUser) {
        userId = window.auth.currentUser.uid;
    } else {
        userId = getCurrentUserId();
    }
    
    // Show loading state
    const saveBtn = document.querySelector('.setting-actions .secondary-btn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    saveBtn.disabled = true;
    
    fetch(`${BACKEND_URL}/api/settings/telegram`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            enabled, 
            token, 
            user_id: userId 
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Telegram settings response:', data); // Debug log
        
        if (data.success) {
            showSuccess(data.message);
            
            // Show bot info if available
            if (data.bot_info) {
                document.getElementById('telegramBotName').textContent = `@${data.bot_info.username}`;
                document.getElementById('telegramBotInfo').style.display = 'block';
            }
            
            // Show webhook status
            if (data.webhook_status) {
                const statusText = document.getElementById('telegramStatusText');
                const statusDot = document.getElementById('telegramStatusDot');
                
                if (data.webhook_status.includes('✅')) {
                    statusText.textContent = 'Automatic responses enabled';
                    statusDot.className = 'status-dot online';
                    // Hide polling button when webhook is working
                    document.getElementById('pollBtn').style.display = 'none';
                    document.getElementById('clearBtn').style.display = 'none';
                } else {
                    statusText.textContent = 'Manual polling required';
                    statusDot.className = 'status-dot pending';
                    // Show polling button when webhook fails
                    document.getElementById('pollBtn').style.display = 'inline-flex';
                    document.getElementById('clearBtn').style.display = 'inline-flex';
                }
                document.getElementById('telegramStatus').style.display = 'block';
            }
            
            // Show test button
            document.getElementById('testBotBtn').style.display = 'inline-flex';
            
        } else {
            showError(data.error || 'Failed to save Telegram settings');
        }
    })
    .catch(error => {
        console.error('Error saving Telegram settings:', error);
        showError('Failed to save Telegram settings');
    })
    .finally(() => {
        // Restore button state
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    });
}

// Simplified test function
function testTelegramBot() {
    const token = document.getElementById('telegramToken').value;
    if (!token) {
        showError('Please enter a Telegram bot token first');
        return;
    }
    
    // Get current user ID
    let userId;
    if (window.auth && window.auth.currentUser) {
        userId = window.auth.currentUser.uid;
    } else {
        userId = getCurrentUserId();
    }
    
    // Show loading state
    const testBtn = document.getElementById('testBotBtn');
    const originalText = testBtn.innerHTML;
    testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    testBtn.disabled = true;
    
    // Get chat ID from user with better guidance
    const chatId = prompt(
        '🔧 Enter your Telegram chat ID:\n\n' +
        'To get your chat ID:\n\n' +
        '1. Start a conversation with your bot on Telegram\n' +
        '2. Send any message to your bot\n' +
        '3. Visit this URL in your browser:\n' +
        '   https://api.telegram.org/bot' + token + '/getUpdates\n' +
        '4. Look for "chat":{"id":123456789} in the response\n' +
        '5. Use that number as your chat ID\n\n' +
        '⚠️ IMPORTANT: Use your USER chat ID, not the bot ID!\n\n' +
        'Enter your chat ID:'
    );
    
    if (!chatId) {
        showError('Please provide a chat ID to test the bot');
        testBtn.innerHTML = originalText;
        testBtn.disabled = false;
        return;
    }
    
    const testData = {
        user_id: userId,
        message: "What cakes do you have?",
        chat_id: chatId
    };
    
    fetch(`${BACKEND_URL}/api/telegram/test-message`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(testData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('✅ Bot is working! Check your Telegram for the response.');
            console.log('Bot response:', data.response);
        } else {
            showError(data.error || 'Failed to send test message');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Failed to send test message');
    })
    .finally(() => {
        // Restore button state
        testBtn.innerHTML = originalText;
        testBtn.disabled = false;
    });
}

// Add function to poll for updates (for development)
function pollTelegramUpdates() {
    fetch(`${BACKEND_URL}/api/telegram/poll`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Telegram updates:', data.updates);
            if (data.count > 0) {
                showSuccess(`Found ${data.count} new messages from Telegram`);
                // Process the latest message
                const latestUpdate = data.updates[data.updates.length - 1];
                if (latestUpdate && latestUpdate.message) {
                    console.log('Latest message:', latestUpdate.message);
                }
            } else {
                showError('No new messages found. Make sure to send a message to your bot first.');
            }
        } else {
            showError(data.error || 'Failed to poll updates');
        }
    })
    .catch(error => {
        console.error('Error polling updates:', error);
        showError('Failed to poll updates');
    });
}

function checkTelegramStatus() {
    const statusDiv = document.getElementById('telegramStatus');
    const statusDot = document.getElementById('telegramStatusDot');
    const statusText = document.getElementById('telegramStatusText');
    const botInfo = document.getElementById('telegramBotInfo');
    const botName = document.getElementById('telegramBotName');
    
    statusDiv.style.display = 'block';
    statusText.textContent = 'Checking status...';
    statusDot.className = 'status-dot pending';
    
    fetch(`${BACKEND_URL}/api/telegram/status`)
    .then(response => response.json())
    .then(data => {
        if (data.success && data.bots) {
            const userId = getCurrentUserId();
            const botStatus = data.bots.get(userId);
            
            if (botStatus && botStatus.status === 'active') {
                statusDot.className = 'status-dot online';
                statusText.textContent = 'Bot is active and ready';
                botInfo.style.display = 'block';
                botName.textContent = `@${botStatus.username}`;
            } else if (botStatus && botStatus.status === 'inactive') {
                statusDot.className = 'status-dot offline';
                statusText.textContent = 'Bot is inactive';
                botInfo.style.display = 'none';
            } else {
                statusDot.className = 'status-dot error';
                statusText.textContent = 'Bot not configured';
                botInfo.style.display = 'none';
            }
        } else {
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Failed to check status';
            botInfo.style.display = 'none';
        }
    })
    .catch(error => {
        console.error('Error checking Telegram status:', error);
        statusDot.className = 'status-dot error';
        statusText.textContent = 'Error checking status';
        botInfo.style.display = 'none';
    });
}

function hideTelegramStatus() {
    const statusDiv = document.getElementById('telegramStatus');
    statusDiv.style.display = 'none';
}

function saveWhatsAppSettings() {
    const enabled = document.getElementById('whatsappEnabled').checked;
    const token = document.getElementById('whatsappToken').value;
    
    fetch(`${BACKEND_URL}/api/settings/whatsapp`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ enabled, token })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('WhatsApp settings saved successfully');
        } else {
            showError(data.error || 'Failed to save WhatsApp settings');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Failed to save WhatsApp settings');
    });
}

function saveWebhookSettings() {
    const enabled = document.getElementById('webhookEnabled').checked;
    const url = document.getElementById('webhookUrl').value;
    
    fetch(`${BACKEND_URL}/api/settings/webhook`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ enabled, url })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('Webhook settings saved successfully');
        } else {
            showError(data.error || 'Failed to save webhook settings');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Failed to save webhook settings');
    });
}

function saveRazorpaySettings() {
    const enabled = document.getElementById('razorpayEnabled').checked;
    const keyId = document.getElementById('razorpayKey').value;
    const secretKey = document.getElementById('razorpaySecret').value;
    
    fetch(`${BACKEND_URL}/api/settings/razorpay`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ enabled, keyId, secretKey })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('Razorpay settings saved successfully');
        } else {
            showError(data.error || 'Failed to save Razorpay settings');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Failed to save Razorpay settings');
    });
}

// Utility Functions
function showError(message) {
    // Create a temporary error message
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #e74c3c;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 10000;
        font-weight: 500;
    `;
    errorDiv.textContent = message;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        document.body.removeChild(errorDiv);
    }, 5000);
}

// Add save to database function
async function saveToDatabase(index) {
    const result = extractionResults[index];
    if (!result || !result.success) {
        showError('Cannot save invalid result');
        return;
    }

    const saveBtn = document.querySelector(`.result-card:nth-child(${index + 1}) .save-btn`);
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    saveBtn.disabled = true;

    try {
        // Format the data properly for the backend
        const dataToSave = {
            content_type: result.content_type,
            source: result.source,
            data: result.data,
            url: result.url,
            filename: result.filename,
            stats: result.stats || {}
        };

        const response = await fetch(`${BACKEND_URL}/api/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dataToSave)
        });

        const saveResult = await response.json();

        if (response.ok) {
            saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved!';
            saveBtn.style.background = '#28a745';
            showSuccess('Data saved successfully to database');
            
            // Refresh the data after saving
            await fetchSavedData();
        } else {
            throw new Error(saveResult.error || 'Failed to save data');
        }
    } catch (error) {
        console.error('Save error:', error);
        showError(`Failed to save data: ${error.message}`);
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    }

    // Reset button after 2 seconds
    setTimeout(() => {
        saveBtn.innerHTML = originalText;
        saveBtn.style.background = '';
        saveBtn.disabled = false;
    }, 2000);
}

// Add success message function
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `
        <i class="fas fa-check-circle"></i>
        ${message}
    `;
    document.body.appendChild(successDiv);
    setTimeout(() => successDiv.remove(), 3000);
}

// Add this function to fetch saved data
async function fetchSavedData() {
    try {
        const response = await fetch(`${BACKEND_URL}/api/data`);
        const data = await response.json();
        
        if (response.ok) {
            // Process each item from the database
            extractionResults = data.map(item => ({
                id: item.id,
                content_type: item.content_type,
                source: item.source,
                data: Array.isArray(item.data) ? item.data : [item.data], // Ensure data is always an array
                url: item.url,
                filename: item.filename,
                stats: item.stats,
                created_at: item.created_at,
                success: true
            }));
            
            // Update both the results display and data table
            displayResults();
            updateDataTable();
        } else {
            throw new Error(data.error || 'Failed to fetch data');
        }
    } catch (error) {
        console.error('Error fetching data:', error);
        showError(`Failed to fetch data: ${error.message}`);
    }
}

// Add this function to get the current user ID
function getCurrentUserId() {
    // For now, we'll use a simple user ID from localStorage
    // In a real application, this would come from your authentication system
    let userId = localStorage.getItem('userId');
    if (!userId) {
        userId = 'user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('userId', userId);
    }
    return userId;
}

// Update the storeInChromaDB function
async function storeInChromaDB() {
    const storeBtn = document.querySelector('.store-chroma-btn');
    const originalText = storeBtn.innerHTML;
    
    // Get current user ID - use the same logic as sendMessage
    let userId;
    
    // Check if Firebase auth is available and user is logged in
    if (window.auth && window.auth.currentUser) {
        // Use Firebase user ID if available
        userId = window.auth.currentUser.uid;
        console.log('Store using Firebase user ID:', userId);
    } else {
        // Fallback to localStorage user ID
        userId = getCurrentUserId();
        console.log('Store using localStorage user ID:', userId);
    }
    
    storeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Storing in ChromaDB...';
    storeBtn.disabled = true;
    
    try {
        // Get all data from the table
        const tableData = [];
        const rows = document.querySelectorAll('#dataTable tbody tr');
        
        rows.forEach(row => {
            try {
                // Get the data attribute that contains the full data object
                const dataAttribute = row.getAttribute('data-full');
                if (dataAttribute) {
                    const rowData = JSON.parse(dataAttribute);
                    if (rowData && typeof rowData === 'object') {
                        tableData.push(rowData);
                    }
                } else {
                    // Fallback to cell content if data attribute is not available
                    const cells = row.querySelectorAll('td');
                    const rowData = {};
                    
                    // Skip the last cell (actions)
                    for (let i = 0; i < cells.length - 1; i++) {
                        const header = document.querySelector(`#dataTable th:nth-child(${i + 1})`)?.textContent.toLowerCase();
                        if (header) {
                            const cellContent = cells[i]?.textContent || '';
                            rowData[header] = cellContent.trim();
                        }
                    }
                    
                    if (Object.keys(rowData).length > 0) {
                        tableData.push(rowData);
                    }
                }
            } catch (error) {
                console.error('Error processing row:', error);
            }
        });

        if (tableData.length === 0) {
            throw new Error('No data found in the table to store');
        }

        console.log('Storing data in ChromaDB:', tableData); // Debug log

        const response = await fetch(`${BACKEND_URL}/api/store-chroma`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                data: tableData,
                user_id: userId
            })
        });

        const result = await response.json();

        if (response.ok) {
            storeBtn.innerHTML = '<i class="fas fa-check"></i> Stored in ChromaDB!';
            storeBtn.style.background = '#28a745';
            showSuccess('Data successfully stored in ChromaDB');
        } else {
            throw new Error(result.error || 'Failed to store data in ChromaDB');
        }
    } catch (error) {
        console.error('ChromaDB storage error:', error);
        showError(`Failed to store in ChromaDB: ${error.message}`);
        storeBtn.innerHTML = originalText;
    }

    setTimeout(() => {
        storeBtn.innerHTML = originalText;
        storeBtn.style.background = '';
        storeBtn.disabled = false;
    }, 2000);
}

function filterData() {
    const searchText = document.getElementById('dataSearch').value.toLowerCase();
    const contentType = document.getElementById('contentTypeFilter').value;
    const rows = document.querySelectorAll('#dataTable tbody tr');
    
    rows.forEach(row => {
        const contentTypeCell = row.querySelector('[data-field="contentType"]').textContent.toLowerCase();
        const titleCell = row.querySelector('[data-field="title"]').textContent.toLowerCase();
        const descriptionCell = row.querySelector('[data-field="description"]').textContent.toLowerCase();
        
        const matchesSearch = !searchText || 
            contentTypeCell.includes(searchText) ||
            titleCell.includes(searchText) ||
            descriptionCell.includes(searchText);
            
        const matchesType = !contentType || contentTypeCell === contentType.toLowerCase();
        
        row.style.display = matchesSearch && matchesType ? '' : 'none';
    });
}

function selectAllRows() {
    const tbody = document.querySelector('#dataTable tbody');
    const rows = tbody.querySelectorAll('tr');
    const selectAllBtn = document.querySelector('.bulk-actions .secondary-btn');
    const deleteSelectedBtn = document.querySelector('.bulk-actions .danger-btn');
    
    if (selectAllBtn.textContent.includes('Select All')) {
        rows.forEach(row => row.classList.add('selected'));
        selectAllBtn.innerHTML = '<i class="fas fa-times"></i> Deselect All';
        deleteSelectedBtn.disabled = false;
    } else {
        rows.forEach(row => row.classList.remove('selected'));
        selectAllBtn.innerHTML = '<i class="fas fa-check-square"></i> Select All';
        deleteSelectedBtn.disabled = true;
    }
}

function deleteSelectedRows() {
    const selectedRows = document.querySelectorAll('#dataTable tbody tr.selected');
    const ids = Array.from(selectedRows).map(row => row.dataset.id).filter(id => id);
    
    if (confirm(`Are you sure you want to delete ${selectedRows.length} entries?`)) {
        if (ids.length > 0) {
            // Delete from database
            fetch(`${BACKEND_URL}/api/data/bulk`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ids })
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    selectedRows.forEach(row => row.remove());
                    showSuccess('Selected entries deleted successfully');
                    selectAllRows(); // Reset selection
                } else {
                    showError(result.error || 'Failed to delete entries');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError('Failed to delete entries');
            });
        } else {
            // Remove unsaved rows
            selectedRows.forEach(row => row.remove());
            selectAllRows(); // Reset selection
        }
    }
}

function formatPrice(price) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(price);
}

// Add function to delete user's ChromaDB data
async function deleteChromaData() {
    if (!confirm('Are you sure you want to delete all your data from ChromaDB? This action cannot be undone.')) {
        return;
    }
    
    // Get current user ID - use the same logic as sendMessage
    let userId;
    
    // Check if Firebase auth is available and user is logged in
    if (window.auth && window.auth.currentUser) {
        // Use Firebase user ID if available
        userId = window.auth.currentUser.uid;
        console.log('Delete using Firebase user ID:', userId);
    } else {
        // Fallback to localStorage user ID
        userId = getCurrentUserId();
        console.log('Delete using localStorage user ID:', userId);
    }
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/delete-chroma`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess('Your data has been successfully deleted from ChromaDB');
        } else {
            throw new Error(result.error || 'Failed to delete data from ChromaDB');
        }
    } catch (error) {
        console.error('Delete ChromaDB error:', error);
        showError(`Failed to delete data from ChromaDB: ${error.message}`);
    }
}

// Add function to test backend connectivity
async function testBackendConnectivity() {
    try {
        console.log('Testing backend connectivity...');
        const response = await fetch(`${BACKEND_URL}/api/health`);
        const data = await response.json();
        console.log('Backend health check response:', data);
        
        if (response.ok) {
            console.log('✅ Backend is accessible and healthy');
        } else {
            console.error('❌ Backend health check failed:', data);
        }
    } catch (error) {
        console.error('❌ Backend connectivity test failed:', error);
        console.error('This might be a CORS issue or the backend is not running');
    }
}

function addTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot';
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return typingDiv;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Add function to toggle Telegram settings visibility
function toggleTelegramSettings() {
    const enabled = document.getElementById('telegramEnabled').checked;
    const tokenGroup = document.getElementById('telegramTokenGroup');
    const testBtn = document.getElementById('testBotBtn');
    const pollBtn = document.getElementById('pollBtn');
    const clearBtn = document.getElementById('clearBtn');
    const statusDiv = document.getElementById('telegramStatus');
    
    if (enabled) {
        tokenGroup.style.display = 'block';
        testBtn.style.display = 'inline-block';
        pollBtn.style.display = 'inline-block';
        clearBtn.style.display = 'inline-block';
        statusDiv.style.display = 'block';
    } else {
        tokenGroup.style.display = 'none';
        testBtn.style.display = 'none';
        pollBtn.style.display = 'none';
        clearBtn.style.display = 'none';
        statusDiv.style.display = 'none';
    }
}

// Add function to poll for new Telegram messages
function pollTelegramMessages() {
    const pollBtn = document.getElementById('pollBtn');
    const originalText = pollBtn.innerHTML;
    pollBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Polling...';
    pollBtn.disabled = true;
    
    fetch(`${BACKEND_URL}/api/telegram/poll`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.messages_processed > 0) {
                showSuccess(`✅ Processed ${data.messages_processed} new messages! Check your Telegram bot.`);
                console.log('Processed messages:', data.new_messages);
            } else {
                showError('No new messages found. Send a message to your bot on Telegram first.');
            }
        } else {
            showError(data.error || 'Failed to poll messages');
        }
    })
    .catch(error => {
        console.error('Error polling messages:', error);
        showError('Failed to poll messages');
    })
    .finally(() => {
        // Restore button state
        pollBtn.innerHTML = originalText;
        pollBtn.disabled = false;
    });
}

// Add function to clear Telegram message history
function clearTelegramHistory() {
    if (!confirm('Are you sure you want to clear the message history? This will reset the bot to respond to all messages again.')) {
        return;
    }
    
    const clearBtn = document.getElementById('clearBtn');
    const originalText = clearBtn.innerHTML;
    clearBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Clearing...';
    clearBtn.disabled = true;
    
    fetch(`${BACKEND_URL}/api/telegram/clear-history`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(`✅ ${data.message}`);
            console.log('History cleared:', data);
        } else {
            showError(data.error || 'Failed to clear history');
        }
    })
    .catch(error => {
        console.error('Error clearing history:', error);
        showError('Failed to clear history');
    })
    .finally(() => {
        // Restore button state
        clearBtn.innerHTML = originalText;
        clearBtn.disabled = false;
    });
}