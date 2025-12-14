// --- FONCTIONS LOGIQUES DE BASE ---

/**
 * Gère l'affichage des différents onglets.
 */
function switchTab(tabName, clickedButton) {
    let tabcontent = document.getElementsByClassName("tab-content");
    for (let i = 0; i < tabcontent.length; i++) {
        tabcontent[i].classList.remove('active');
    }

    let tablinks = document.getElementsByClassName("tab-button");
    for (let i = 0; i < tablinks.length; i++) {
        tablinks[i].classList.remove('active');
    }

    document.getElementById(tabName).classList.add('active');
    clickedButton.classList.add('active');
}

/**
 * Envoie les réponses de l'utilisateur au serveur pour vérification (sécurisée).
 */
function checkAnswers() {
    const quizForm = document.getElementById('quiz-form');
    if (!quizForm) return;

    // 1. Collecter les réponses du formulaire (on prend la première case cochée pour chaque question)
    const data = {};
    const questions = document.querySelectorAll('.quiz-item');

    questions.forEach((item, index) => {
        const q_num = index + 1;
        // Cibler les cases à cocher
        const checkedInputs = item.querySelectorAll(`input[name="q${q_num}"]:checked`);
        
        // Comme le back-end ne gère qu'une seule bonne réponse, nous envoyons SEULEMENT la première réponse cochée
        if (checkedInputs.length > 0) {
            data[`q${q_num}`] = checkedInputs[0].value;
        }
    });

    // 2. Réinitialiser l'état visuel avant la correction
    resetQuizVisuals();

    // 3. Envoi de la requête au serveur (route /check_quiz)
    fetch('/check_quiz', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded' 
        },
        body: new URLSearchParams(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        if (result.correction) {
            applyCorrection(result.correction);
        } else {
            console.error("Erreur: Le serveur n'a pas renvoyé de données de correction valides.");
        }
    })
    .catch(error => console.error('Erreur lors de la vérification du quiz:', error));
}

/**
 * Applique la correction reçue du serveur au DOM.
 */
function applyCorrection(correctionData) {
    const quizItems = document.querySelectorAll('.quiz-item');
    
    quizItems.forEach((item, index) => {
        const q_num = index + 1;
        const resultMessage = document.getElementById(`msg-${q_num}`);
        const optionsList = item.querySelectorAll('.option-item');
        
        const correction = correctionData.find(c => c.q_num === String(q_num));

        if (!correction) return; 

        // Afficher le résultat
        if (correction.is_correct) {
            resultMessage.textContent = "✅ Correct !";
            resultMessage.classList.add('correct');
        } else {
            resultMessage.textContent = `❌ Faux. La réponse correcte était : ${correction.correct_answer}`;
            resultMessage.classList.add('incorrect');
        }
        
        // Surligner la bonne réponse
        optionsList.forEach(opt => {
            const input = opt.querySelector('input');
            if (input.value === correction.correct_answer) {
                opt.classList.add('correct-choice');
            }
        });
    });
}

/**
 * Réinitialise UNIQUEMENT l'état visuel des résultats (messages et surlignage).
 */
function resetQuizVisuals() {
    const quizItems = document.querySelectorAll('.quiz-item');

    quizItems.forEach((item) => {
        const resultMessage = item.querySelector('.result-message');
        const optionsList = item.querySelectorAll('.option-item');
        
        resultMessage.textContent = '';
        resultMessage.className = 'result-message';
        
        optionsList.forEach(opt => {
            opt.classList.remove('correct-choice');
        });
    });
}


// --- GESTION DES ÉVÉNEMENTS (Démarrage de la page) ---

document.addEventListener('DOMContentLoaded', () => {
    
    const tabsContainer = document.querySelector('.tabs-container');
    
    if (tabsContainer) {
        
        // 1. GESTION DES ONGLETS
        const tabButtons = document.querySelectorAll('.tab-buttons button');
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabTarget = button.getAttribute('data-tab-target');
                if (tabTarget) {
                    switchTab(tabTarget, button);
                }
            });
        });
        
        const reviewButton = document.querySelector('.tab-buttons button[data-tab-target="review"]');
        if (reviewButton) {
             switchTab('review', reviewButton);
        }
        
        // 2. RETIRER LES MESSAGES DE CORRECTION AU CHANGEMENT DE RÉPONSE
        const quizForm = document.getElementById('quiz-form');
        if (quizForm) {
            // Puisque ce sont des checkboxes, le comportement de désélection est natif
            quizForm.addEventListener('change', resetQuizVisuals);
        }
    }
    
    // 3. GESTION DES BOUTONS DE QUIZ
    
    const checkButton = document.getElementById('verify-button');
    if (checkButton) {
        checkButton.addEventListener('click', checkAnswers);
    }
    
    const generateButton = document.getElementById('generate-new-quiz');
    if (generateButton) {
        generateButton.addEventListener('click', () => {
            const uploadForm = document.querySelector('.upload-form');
            if (uploadForm) {
                if (uploadForm.querySelector('input[type="file"]').files.length > 0) {
                    uploadForm.submit();
                } else {
                    alert("Veuillez sélectionner un fichier PDF avant de générer un nouveau quiz.");
                }
            }
        });
    }
});
