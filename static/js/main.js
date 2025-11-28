/**
 * Netflix Churn Prediction - Main JavaScript
 */

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Format number as currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const container = document.querySelector('.flash-container') || createFlashContainer();
    
    const flash = document.createElement('div');
    flash.className = `flash flash-${type}`;
    flash.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="flash-close">×</button>
    `;
    
    container.appendChild(flash);
    
    // Auto remove after 5 seconds
    setTimeout(() => flash.remove(), 5000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-container';
    document.body.appendChild(container);
    return container;
}

// ============================================================================
// API CALLS
// ============================================================================

/**
 * Make prediction API call
 */
async function predictChurn(customerData) {
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(customerData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Prediction error:', error);
        showNotification('Prediction failed: ' + error.message, 'error');
        throw error;
    }
}

/**
 * Batch prediction from CSV
 */
async function batchPredict(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/batch_predict', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Batch prediction error:', error);
        showNotification('Batch prediction failed: ' + error.message, 'error');
        throw error;
    }
}

/**
 * Get customer segments
 */
async function getSegments() {
    try {
        const response = await fetch('/api/segments');
        const result = await response.json();
        return result.segments;
    } catch (error) {
        console.error('Error fetching segments:', error);
        return [];
    }
}

/**
 * Get system metrics
 */
async function getMetrics() {
    try {
        const response = await fetch('/api/metrics');
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error fetching metrics:', error);
        return null;
    }
}

// ============================================================================
// FORM HANDLING
// ============================================================================

/**
 * Handle prediction form submission
 */
function setupPredictionForm() {
    const form = document.getElementById('predictionForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Collect form data
        const formData = new FormData(form);
        const data = {};
        
        // Convert form data to object
        for (const [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        // Handle checkboxes
        data.streaming_tv = form.querySelector('[name="streaming_tv"]').checked ? 1 : 0;
        data.streaming_movies = form.querySelector('[name="streaming_movies"]').checked ? 1 : 0;
        data.tech_support = form.querySelector('[name="tech_support"]').checked ? 1 : 0;
        data.online_security = form.querySelector('[name="online_security"]').checked ? 1 : 0;
        
        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Predicting...';
        
        try {
            // Make prediction
            const result = await predictChurn(data);
            
            // Display results
            if (result.success) {
                displayPredictionResults(result);
                showNotification('Prediction completed successfully!', 'success');
            } else {
                showNotification(result.error || 'Prediction failed', 'error');
            }
        } catch (error) {
            showNotification('An error occurred during prediction', 'error');
        } finally {
            // Reset button
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
}

/**
 * Display prediction results
 */
function displayPredictionResults(result) {
    const resultsCard = document.getElementById('resultsCard');
    if (!resultsCard) return;
    
    // Show results card
    resultsCard.style.display = 'block';
    
    // Update churn probability
    const churnValue = document.getElementById('churnValue');
    const probability = (result.churn_probability * 100).toFixed(1);
    churnValue.textContent = probability + '%';
    
    // Animate gauge
    const gaugeProgress = document.getElementById('gaugeProgress');
    if (gaugeProgress) {
        const circumference = 565.48;
        const offset = circumference - (result.churn_probability * circumference);
        gaugeProgress.style.strokeDashoffset = offset;
    }
    
    // Update risk badge
    const riskBadge = document.getElementById('riskBadge');
    riskBadge.textContent = result.risk_level + ' Risk';
    riskBadge.className = 'risk-badge';
    
    // Set badge color
    if (result.risk_level === 'Low') {
        riskBadge.style.background = 'rgba(34, 197, 94, 0.2)';
        riskBadge.style.color = '#22c55e';
        riskBadge.style.border = '2px solid #22c55e';
    } else if (result.risk_level === 'Medium') {
        riskBadge.style.background = 'rgba(251, 191, 36, 0.2)';
        riskBadge.style.color = '#fbbf24';
        riskBadge.style.border = '2px solid #fbbf24';
    } else {
        riskBadge.style.background = 'rgba(239, 68, 68, 0.2)';
        riskBadge.style.color = '#ef4444';
        riskBadge.style.border = '2px solid #ef4444';
    }
    
    // Update recommendations
    const recList = document.getElementById('recommendationsList');
    if (recList && result.recommendations) {
        recList.innerHTML = '';
        result.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            recList.appendChild(li);
        });
    }
    
    // Scroll to results
    resultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ============================================================================
// FILE UPLOAD
// ============================================================================

/**
 * Handle batch file upload
 */
function setupFileUpload() {
    const uploadInput = document.getElementById('batchUpload');
    if (!uploadInput) return;
    
    uploadInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        // Validate file type
        if (!file.name.endsWith('.csv')) {
            showNotification('Please upload a CSV file', 'error');
            return;
        }
        
        // Show loading notification
        showNotification('Processing batch predictions...', 'info');
        
        try {
            const result = await batchPredict(file);
            
            if (result.success) {
                showBatchResults(result);
                showNotification(
                    `Batch processing complete! Processed ${result.summary.total_customers} customers`,
                    'success'
                );
            } else {
                showNotification(result.error || 'Batch processing failed', 'error');
            }
        } catch (error) {
            showNotification('Batch upload failed', 'error');
        }
        
        // Reset input
        uploadInput.value = '';
    });
}

/**
 * Show batch prediction results
 */
function showBatchResults(result) {
    const summary = result.summary;
    
    // Create modal or summary display
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Batch Prediction Results</h2>
                <button onclick="this.closest('.modal').remove()" class="btn-close">×</button>
            </div>
            <div class="modal-body">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Customers</div>
                        <div class="stat-value">${summary.total_customers}</div>
                    </div>
                    <div class="stat-card stat-red">
                        <div class="stat-label">High Risk</div>
                        <div class="stat-value">${summary.high_risk}</div>
                    </div>
                    <div class="stat-card stat-yellow">
                        <div class="stat-label">Medium Risk</div>
                        <div class="stat-value">${summary.medium_risk}</div>
                    </div>
                    <div class="stat-card stat-green">
                        <div class="stat-label">Low Risk</div>
                        <div class="stat-value">${summary.low_risk}</div>
                    </div>
                </div>
                <p class="text-center">
                    Average Churn Probability: 
                    <strong>${(summary.avg_churn_probability * 100).toFixed(1)}%</strong>
                </p>
            </div>
            <div class="modal-footer">
                <button onclick="downloadResults(${JSON.stringify(result.results)})" class="btn btn-primary">
                    📥 Download Results
                </button>
                <button onclick="this.closest('.modal').remove()" class="btn btn-secondary">
                    Close
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

/**
 * Download results as CSV
 */
function downloadResults(results) {
    // Convert to CSV
    const headers = Object.keys(results[0]);
    const csv = [
        headers.join(','),
        ...results.map(row => headers.map(h => row[h]).join(','))
    ].join('\n');
    
    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'churn_predictions_' + new Date().toISOString().split('T')[0] + '.csv';
    a.click();
    URL.revokeObjectURL(url);
}

// ============================================================================
// CHARTS
// ============================================================================

/**
 * Initialize dashboard charts
 */
async function initializeDashboardCharts() {
    const metrics = await getMetrics();
    if (!metrics) return;
    
    // Update charts with real data
    // This would be implemented based on actual data structure
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize app on DOM load
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎬 Netflix Churn Prediction App initialized');
    
    // Setup forms
    setupPredictionForm();
    setupFileUpload();
    
    // Initialize charts if on dashboard
    if (document.querySelector('.dashboard-page')) {
        initializeDashboardCharts();
    }
    
    // Auto-hide flash messages
    setTimeout(() => {
        document.querySelectorAll('.flash').forEach(flash => {
            flash.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => flash.remove(), 300);
        });
    }, 5000);
});

// ============================================================================
// GLOBAL FUNCTIONS (for inline onclick handlers)
// ============================================================================

window.refreshTable = function() {
    location.reload();
};

window.handleBatchUpload = async function(input) {
    if (!input.files[0]) return;
    
    const formData = new FormData();
    formData.append('file', input.files[0]);
    
    try {
        showNotification('Processing batch predictions...', 'info');
        
        const response = await fetch('/api/batch_predict', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showBatchResults(result);
            showNotification(
                `Batch complete! Processed ${result.summary.total_customers} customers`,
                'success'
            );
        } else {
            showNotification(result.error || 'Batch processing failed', 'error');
        }
    } catch (error) {
        showNotification('Upload failed: ' + error.message, 'error');
    }
    
    input.value = '';
};

// Export for use in other scripts
window.NetflixChurn = {
    predictChurn,
    batchPredict,
    getSegments,
    getMetrics,
    formatCurrency,
    formatDate,
    showNotification
};