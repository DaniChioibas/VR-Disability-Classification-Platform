document.addEventListener("DOMContentLoaded", function() {
    const fileInput = document.getElementById("json-files-batch");
    const selectedFilesDisplay = document.getElementById("selected-files-batch-display");
    const uploadForm = document.getElementById("batch-upload-form");
    const loader = document.getElementById("batch-loader");
    const resultsContainer = document.getElementById("batch-results-container");

    if (fileInput && selectedFilesDisplay) {
        fileInput.addEventListener("change", function() {
            if (this.files.length > 0) {
                let fileNames = Array.from(this.files).map(file => file.name).join(', ');
                selectedFilesDisplay.innerHTML = `<p class="text-muted"><small>Selected: ${this.files.length} file(s) - ${fileNames}</small></p>`;
            } else {
                selectedFilesDisplay.innerHTML = '';
            }
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener("submit", function() {
            if (loader) loader.style.display = "block";
            if (resultsContainer) resultsContainer.innerHTML = ''; 
        });
    }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').forEach(cookie => {
            const [key, val] = cookie.trim().split('=');
            if (key === name) cookieValue = decodeURIComponent(val);
        });
    }
    return cookieValue;
}

document.addEventListener('click', function(e) {
    const btn = e.target.closest('.explore-btn');
    if (!btn) return;
    let featuresObj, rawObj;
    try {
        featuresObj = JSON.parse(btn.dataset.features);
        rawObj = JSON.parse(btn.dataset.raw);
    } catch (parseErr) {
        return alert('Could not parse explore data: ' + parseErr.message);
    }

    const filename = btn.dataset.filename;
    const prediction_label = btn.dataset.prediction_label;
    const confidence = btn.dataset.confidence;

    const payload = new URLSearchParams();
    payload.append('features', JSON.stringify(featuresObj));
    payload.append('raw_json_content', JSON.stringify(rawObj));
    payload.append('filename', filename);
    payload.append('prediction_label', prediction_label);
    payload.append('confidence', confidence);

    fetch('/api/set-explore-session/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: payload
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.href = '/explore-more/';
        } else {
            alert('Error setting explore session: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(err => {
        console.error('Explore session error', err);
        alert('Failed to set explore session.');
    });
});
