const themeManager = {
    currentTheme: "light",

    initialize() {
        const savedTheme = localStorage.getItem("theme");
        if (savedTheme) {
            this.setTheme(savedTheme);
        } else {
            if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
                this.setTheme("dark");
            } else {
                this.setTheme("light");
            }
        }

        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", e => {
            if (!localStorage.getItem("theme")) {
                this.setTheme(e.matches ? "dark" : "light");
            }
        });
    },

    toggle() {
        this.setTheme(this.currentTheme === "dark" ? "light" : "dark");
    },

    setTheme(theme) {
        this.currentTheme = theme;
        
        document.documentElement.setAttribute("data-theme", theme);
        
        localStorage.setItem("theme", theme);
    }
};

document.addEventListener("DOMContentLoaded", function() {
    themeManager.initialize();
    
    document.getElementById("theme-toggle")?.addEventListener("click", function() {
        themeManager.toggle();
    });
    
    document.getElementById("navbar-toggle")?.addEventListener("click", function() {
        const navbarMenu = document.querySelector(".navbar-menu");
        const navbarActions = document.querySelector(".navbar-actions");
        
        navbarMenu.classList.toggle("active");
        navbarActions.classList.toggle("active");
        this.classList.toggle("active");
    });
    
    document.getElementById("json-file")?.addEventListener("change", function(e) {
        const fileName = e.target.files[0] ? e.target.files[0].name : "Niciun fișier selectat";
        document.getElementById("selected-file").textContent = "Fișier selectat: " + fileName;
    });
    
    document.getElementById("upload-form")?.addEventListener("submit", async function(e) {
        e.preventDefault();
        
        const resultCard = document.getElementById("result");
        const resultContent = document.getElementById("result-content");
        const loader = document.getElementById("loader");

        resultCard.classList.remove("active");
        loader.style.display = "block";
        
        const formData = new FormData(this);
        
        try {
            const response = await fetch("", {
                method: "POST",
                body: formData,
            });
            
            const data = await response.json();
            
            loader.style.display = "none";
            
            if (response.ok) {
                const isPredictionAtypical = data.prediction === 1;
                const label = isPredictionAtypical ? "Atipic" : "Tipic";
                const resultClass = isPredictionAtypical ? "result-atypical" : "result-typical";
                const iconPath = `<svg class="result-icon ${resultClass}" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <circle cx="12" cy="12" r="9" stroke-width="2"/>
                    <text x="12" y="16" text-anchor="middle" font-size="12" font-weight="bold" stroke="none" fill="currentColor">${isPredictionAtypical ? "A" : "T"}</text>
                </svg>`;
                
                resultContent.innerHTML = `
                    ${iconPath}
                    <div class="result-label ${resultClass}">${label}</div>
                    <p>Datele de mișcare încărcate au fost clasificate ca ${label.toLowerCase()}.</p>
                    <div class="confidence-meter">
                        <div class="confidence-bar">
                            <div class="confidence-fill ${resultClass}" style="width: ${data.confidence}%"></div>
                        </div>
                        <div class="confidence-text">
                            Încredere: ${data.confidence}%
                            <span class="info-icon-container">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="info-icon">
                                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                                </svg>
                                <span class="tooltip-text">Acest scor de încredere reflectă certitudinea modelului în predicția sa bazată pe datele de antrenament și nu reprezintă o măsură de diagnostic.</span>
                            </span>
                        </div>
                    </div>
                `;
                
                resultCard.classList.add("active");
                
                const exploreBtnContainer = document.getElementById("explore-btn-container");
                if (exploreBtnContainer && isPredictionAtypical) {
                    exploreBtnContainer.style.display = "block";
                }

            } else {
                resultContent.innerHTML = `
                    <svg class="result-icon result-atypical" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <circle cx="12" cy="12" r="9" stroke-width="2"/>
                        <text x="12" y="16" text-anchor="middle" font-size="12" font-weight="bold" stroke="none" fill="currentColor">!</text>
                    </svg>
                    <div class="result-label result-atypical">Eroare</div>
                    <p class="error-message">${data.error || "A apărut o eroare necunoscută."}</p>
                `;
                
                resultCard.classList.add("active");
            }
        } catch (error) {
            loader.style.display = "none";
            resultContent.innerHTML = `
                <svg class="result-icon result-atypical" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <circle cx="12" cy="12" r="9" stroke-width="2"/>
                    <text x="12" y="16" text-anchor="middle" font-size="12" font-weight="bold" stroke="none" fill="currentColor">!</text>
                </svg>
                <div class="result-label result-atypical">Eroare</div>
                <p class="error-message">A apărut o eroare neașteptată: ${error.message}</p>
            `;
            
            resultCard.classList.add("active");
        }
    });
    
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userMenuDropdown = document.getElementById('userMenuDropdown');

    if (userMenuBtn) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenuDropdown.classList.toggle('open');
        });
    }

    document.addEventListener('click', (e) => {
        if (userMenuDropdown.classList.contains('open') && !userMenuDropdown.contains(e.target)) {
            userMenuDropdown.classList.remove('open');
        }
    });

    function applyUserMenuTextColor() {
        const userMenuBtn = document.getElementById('userMenuBtn');
        if (userMenuBtn) {
            if (document.body.classList.contains('dark-mode')) {
                userMenuBtn.style.color = '#e0e0e0';
            } else {
                userMenuBtn.style.color = '';
            }
        }
    }

    applyUserMenuTextColor();

    const modeToggle = document.getElementById('modeToggle');
    if (modeToggle) {
        modeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            applyUserMenuTextColor();
        });
    }

    const exploreBtn = document.getElementById('exploreMoreBtn');
    const predictionResult = document.getElementById('predictionResult');
    if (exploreBtn) {
        if (predictionResult.textContent.trim() !== 'Atypical') {
            exploreBtn.style.display = 'none';
        }
    }

    document.addEventListener('click', function(e) {
        const toggleBtn = e.target.closest('.user-dropdown-toggle');
        if (toggleBtn) {
            e.stopPropagation();
            const dropdown = toggleBtn.closest('.user-dropdown');
            dropdown.classList.toggle('open');
        } else {
            document.querySelectorAll('.user-dropdown.open').forEach(dd => dd.classList.remove('open'));
        }
    });
});
