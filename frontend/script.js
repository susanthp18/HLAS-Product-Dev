// HLAS Insurance Assistant Frontend JavaScript

// Configuration
const API_BASE_URL = 'http://localhost:8000';
let sessionId = null;
let sessionStats = {
    totalQueries: 0,
    totalConfidence: 0,
    avgConfidence: 0
};

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const queryForm = document.getElementById('queryForm');
const queryInput = document.getElementById('queryInput');
const submitBtn = document.getElementById('submitBtn');
const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkSystemHealth();
});

function initializeApp() {
    // Focus on input
    queryInput.focus();

    // Update statistics display
    updateStatistics();

    // Try to create conversation session (optional)
    createSession();

    console.log('HLAS Insurance Assistant initialized');
}

function setupEventListeners() {
    // Query form submission
    queryForm.addEventListener('submit', handleQuerySubmit);
    
    // Enter key in input
    queryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleQuerySubmit(e);
        }
    });
}

async function handleQuerySubmit(e) {
    e.preventDefault();
    
    const query = queryInput.value.trim();
    if (!query) return;
    
    // Add user message to chat
    addMessage(query, 'user');
    
    // Clear input and disable form
    queryInput.value = '';
    setFormLoading(true);
    
    // Show loading modal
    loadingModal.show();
    
    try {
        // Send query to API
        const response = await sendQuery(query);
        
        // Hide loading modal
        loadingModal.hide();
        
        // Add assistant response
        addAssistantMessage(response);
        
        // Update statistics
        updateSessionStats(response.confidence_score);
        
    } catch (error) {
        console.error('Error processing query:', error);
        loadingModal.hide();
        addErrorMessage('Sorry, I encountered an error processing your question. Please try again.');
    } finally {
        setFormLoading(false);
        queryInput.focus();
    }
}

async function createSession() {
    try {
        console.log('Creating conversation session...');
        const response = await fetch(`${API_BASE_URL}/conversation/session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: 'frontend_user',
                platform: 'web'
            })
        });

        console.log('Session creation response status:', response.status);

        if (response.ok) {
            const data = await response.json();
            sessionId = data.session_id;
            console.log('✅ Session created successfully:', sessionId);

            // Show session info in UI (optional)
            const sessionInfo = document.createElement('div');
            sessionInfo.className = 'alert alert-info mt-2';
            sessionInfo.innerHTML = `<small><i class="fas fa-info-circle"></i> Session: ${sessionId.substring(0, 8)}...</small>`;
            document.querySelector('.container').insertBefore(sessionInfo, document.querySelector('.row'));
        } else {
            const errorText = await response.text();
            console.error('Failed to create session:', response.status, errorText);
            console.warn('Continuing without session tracking');
        }
    } catch (error) {
        console.error('Error creating session:', error);
        console.warn('Continuing without session tracking');
    }
}

async function sendQuery(query) {
    const requestBody = {
        query: query,
        include_citations: true,
        include_confidence: true,
        max_results: 5
    };

    // Add session_id if available (API will auto-generate if not provided)
    if (sessionId) {
        requestBody.session_id = sessionId;
        console.log('Sending query with session ID:', sessionId);
    } else {
        console.log('Sending query without session ID (API will auto-generate)');
    }

    const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'API request failed');
    }

    return await response.json();
}

function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (type === 'user') {
        contentDiv.innerHTML = `<i class="fas fa-user me-2"></i>${escapeHtml(content)}`;
    } else {
        contentDiv.innerHTML = content;
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addAssistantMessage(response) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Main answer
    let content = `<i class="fas fa-robot me-2"></i>${formatAnswer(response.answer)}`;
    
    // Add confidence badge
    if (response.confidence_score > 0) {
        const confidenceClass = getConfidenceClass(response.confidence_score);
        const confidencePercent = Math.round(response.confidence_score * 100);
        content += `<div class="message-meta mt-2">
            <span class="confidence-badge ${confidenceClass}">
                Confidence: ${confidencePercent}%
            </span>
        </div>`;
    }
    
    // Add citations if available
    if (response.citations && response.citations.length > 0) {
        content += '<div class="citations">';
        content += '<h6><i class="fas fa-book me-1"></i>Sources:</h6>';
        
        response.citations.forEach((citation, index) => {
            const relevancePercent = Math.round(citation.relevance_score * 100);
            content += `<div class="citation-item">
                [${index + 1}] ${citation.product_name} ${citation.document_type}
                ${citation.section_hierarchy.length > 0 ? ' - ' + citation.section_hierarchy.join(' > ') : ''}
                <span class="citation-relevance">${relevancePercent}%</span>
            </div>`;
        });
        
        content += '</div>';
    }
    
    // Add processing info
    if (response.processing_time_ms) {
        content += `<div class="message-meta mt-2">
            <small class="text-muted">
                <i class="fas fa-clock me-1"></i>
                Processed in ${Math.round(response.processing_time_ms)}ms | 
                Used ${response.context_used}/${response.context_available} sources
            </small>
        </div>`;
    }
    
    contentDiv.innerHTML = content;
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addErrorMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content error-message';
    contentDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i>${escapeHtml(message)}`;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatAnswer(answer) {
    // Convert markdown-style citations to HTML
    return escapeHtml(answer)
        .replace(/\[(\d+)\]/g, '<sup class="text-primary">[$1]</sup>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

function getConfidenceClass(confidence) {
    if (confidence >= 0.8) return 'confidence-high';
    if (confidence >= 0.5) return 'confidence-medium';
    return 'confidence-low';
}

function setFormLoading(loading) {
    submitBtn.disabled = loading;
    queryInput.disabled = loading;
    
    if (loading) {
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
    } else {
        submitBtn.innerHTML = '<i class="fas fa-paper-plane me-1"></i>Ask';
    }
}

function updateSessionStats(confidence) {
    sessionStats.totalQueries++;
    sessionStats.totalConfidence += confidence;
    sessionStats.avgConfidence = sessionStats.totalConfidence / sessionStats.totalQueries;
    
    updateStatistics();
}

function updateStatistics() {
    document.getElementById('totalQueries').textContent = sessionStats.totalQueries;
    document.getElementById('avgConfidence').textContent = 
        Math.round(sessionStats.avgConfidence * 100) + '%';
}

async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/agents/status`);
        const status = await response.json();
        
        updateSystemStatus(status);
    } catch (error) {
        console.error('Failed to check system health:', error);
        updateSystemStatus({
            intent_router: 'error',
            retrieval: 'error',
            response_generation: 'error',
            vector_database: 'error'
        });
    }
}

function updateSystemStatus(status) {
    const statusContainer = document.getElementById('systemStatus');
    
    const statusItems = [
        { key: 'intent_router', label: 'Intent Router' },
        { key: 'retrieval', label: 'Retrieval Agent' },
        { key: 'response_generation', label: 'Response Agent' },
        { key: 'vector_database', label: 'Vector Database' }
    ];
    
    let html = '';
    statusItems.forEach(item => {
        const itemStatus = status[item.key] || 'unknown';
        const statusClass = getStatusClass(itemStatus);
        
        html += `<div class="status-item">
            <span>
                <span class="status-indicator ${statusClass}"></span>
                ${item.label}
            </span>
            <span class="text-muted">${itemStatus}</span>
        </div>`;
    });
    
    statusContainer.innerHTML = html;
}

function getStatusClass(status) {
    if (status === 'operational' || status === 'healthy' || status === 'connected') {
        return 'status-healthy';
    } else if (status.includes('error') || status === 'disconnected') {
        return 'status-error';
    } else {
        return 'status-warning';
    }
}

function askQuickQuestion(question) {
    queryInput.value = question;
    queryInput.focus();
    handleQuerySubmit(new Event('submit'));
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility function to show notifications
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Error handling for fetch requests
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showNotification('An unexpected error occurred. Please try again.', 'danger');
});

// Check if API is available on load
fetch(`${API_BASE_URL}/health`)
    .then(response => {
        if (response.ok) {
            console.log('API connection successful');
        } else {
            throw new Error('API health check failed');
        }
    })
    .catch(error => {
        console.error('API connection failed:', error);
        showNotification('Unable to connect to the insurance assistant API. Please check if the server is running.', 'warning');
    });
