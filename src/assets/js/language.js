// Fonction pour changer la langue
function changeLanguage(lang) {
  // Mettre à jour la direction du texte pour l'arabe
  if (lang === 'ar') {
    document.documentElement.dir = 'rtl';
    document.documentElement.lang = 'ar';
  } else {
    document.documentElement.dir = 'ltr';
    document.documentElement.lang = lang;
  }

  // Traduire tous les éléments avec l'attribut data-translate
  const elements = document.querySelectorAll('[data-translate]');
  elements.forEach(element => {
    const key = element.getAttribute('data-translate');
    if (translations[lang] && translations[lang][key]) {
      element.textContent = translations[lang][key];
    }
  });

  // Mettre à jour les attributs alt des images
  const images = document.querySelectorAll('img[data-translate-alt]');
  images.forEach(img => {
    const key = img.getAttribute('data-translate-alt');
    if (translations[lang] && translations[lang][key]) {
      img.alt = translations[lang][key];
    }
  });

  // Mettre à jour les placeholders des inputs
  const inputs = document.querySelectorAll('input[data-translate-placeholder]');
  inputs.forEach(input => {
    const key = input.getAttribute('data-translate-placeholder');
    if (translations[lang] && translations[lang][key]) {
      input.placeholder = translations[lang][key];
    }
  });

  // Sauvegarder la langue sélectionnée
  localStorage.setItem('selectedLanguage', lang);

  // Mettre à jour l'icône de langue active
  document.querySelectorAll('.lang-option').forEach(option => {
    if (option.getAttribute('data-lang') === lang) {
      option.classList.add('active');
    } else {
      option.classList.remove('active');
    }
  });
}

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