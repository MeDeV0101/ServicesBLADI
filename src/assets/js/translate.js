document.addEventListener('DOMContentLoaded', function() {
    // Récupérer le sélecteur de langue
    const languageSelect = document.getElementById('language-select');
    
    // Fonction pour mettre à jour les textes selon la langue sélectionnée
    function updateTexts(lang) {
        const elements = document.querySelectorAll('[data-translate]');
        elements.forEach(element => {
            const key = element.getAttribute('data-translate');
            if (translations[lang] && translations[lang][key]) {
                element.textContent = translations[lang][key];
            }
        });
    }

    // Écouter le changement de langue
    languageSelect.addEventListener('change', function() {
        const selectedLang = this.value;
        localStorage.setItem('selectedLanguage', selectedLang);
        updateTexts(selectedLang);
    });

    // Restaurer la langue sélectionnée au chargement de la page
    const savedLang = localStorage.getItem('selectedLanguage') || 'fr';
    languageSelect.value = savedLang;
    updateTexts(savedLang);
}); 