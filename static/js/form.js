// Form handling for PolyIngest
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('polymarket-form');
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    const loadingText = document.getElementById('loading-text');
    const resultsSection = document.getElementById('results-section');
    const errorSection = document.getElementById('error-section');
    const resultsContent = document.getElementById('results-content');
    const errorMessage = document.getElementById('error-message');
    const resultTimestamp = document.getElementById('result-timestamp');
    const copyBtn = document.getElementById('copy-btn');
    const downloadBtn = document.getElementById('download-btn');

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const urlInput = document.getElementById('polymarket-url');
        const url = urlInput.value.trim();
        
        if (!url) {
            showError('Please enter a Polymarket URL');
            return;
        }
        
        // Validate URL format
        if (!url.includes('polymarket.com')) {
            showError('Please enter a valid Polymarket URL');
            return;
        }
        
        // Show loading state
        setLoading(true);
        hideResults();
        hideError();
        
        try {
            // Convert polymarket.com URL to local API endpoint
            // Extract the path and query parameters from the Polymarket URL
            const urlObj = new URL(url);
            const pathAndQuery = urlObj.pathname + urlObj.search;
            const apiUrl = `${window.location.origin}${pathAndQuery}`;
            
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.text();
            showResults(data);
            
        } catch (error) {
            console.error('Error:', error);
            showError(error.message || 'Failed to process the URL. Please check the URL and try again.');
        } finally {
            setLoading(false);
        }
    });
    
    // Copy to clipboard
    copyBtn.addEventListener('click', async function() {
        try {
            await navigator.clipboard.writeText(resultsContent.textContent);
            
            // Show feedback
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = `
                <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                Copied!
            `;
            copyBtn.classList.add('text-green-600', 'bg-green-50', 'border-green-300');
            
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
                copyBtn.classList.remove('text-green-600', 'bg-green-50', 'border-green-300');
            }, 2000);
            
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    });
    
    // Download as text file
    downloadBtn.addEventListener('click', function() {
        const content = resultsContent.textContent;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'polymarket-analysis.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    });
    
    function setLoading(loading) {
        if (loading) {
            submitBtn.disabled = true;
            submitText.classList.add('hidden');
            loadingText.classList.remove('hidden');
        } else {
            submitBtn.disabled = false;
            submitText.classList.remove('hidden');
            loadingText.classList.add('hidden');
        }
    }
    
    function showResults(data) {
        resultsContent.textContent = data;
        resultTimestamp.textContent = `Generated at ${new Date().toLocaleString()}`;
        resultsSection.classList.remove('hidden');
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    function hideResults() {
        resultsSection.classList.add('hidden');
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorSection.classList.remove('hidden');
        
        // Scroll to error
        errorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    function hideError() {
        errorSection.classList.add('hidden');
    }
});