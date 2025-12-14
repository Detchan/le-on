import os
import io
import json
from flask import Flask, render_template, request, session, redirect, url_for
from pypdf import PdfReader
from generator import generate_quiz_and_review
from werkzeug.utils import secure_filename

# Configuration
app = Flask(__name__)
# Clé secrète nécessaire pour utiliser les sessions (stockage temporaire côté serveur)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_for_dev')

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_stream):
    reader = PdfReader(file_stream)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    # Limiter la taille du texte envoyé à l'IA pour éviter les coûts/délais excessifs
    return text[:6000] 

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return redirect(request.url)

        if file:
            try:
                # 1. Extraction du texte
                pdf_stream = io.BytesIO(file.read())
                text_content = extract_text_from_pdf(pdf_stream)
                
                # 2. Génération par l'IA
                ia_results = generate_quiz_and_review(text_content)
                
                # 3. Stockage des réponses correctes dans la session (SÉCURISÉ)
                # On crée un dictionnaire simple {indice_question: réponse_correcte}
                correct_answers = {}
                for idx, item in enumerate(ia_results.get('quiz', [])):
                    # idx commence à 0, le numéro de question dans le formulaire est idx+1
                    correct_answers[str(idx + 1)] = item.get('correct_answer')
                
                session['correct_answers'] = correct_answers
                
                # 4. Nettoyage du quiz avant de l'envoyer au client (ON ENLÈVE LES RÉPONSES)
                clean_quiz = []
                for item in ia_results.get('quiz', []):
                    clean_quiz.append({
                        "question": item.get('question'),
                        "options": item.get('options')
                        # 'correct_answer' N'EST PLUS INCLUS
                    })

                # On envoie les résultats propres au template
                display_results = {
                    'review_sheets': ia_results.get('review_sheets', []),
                    'quiz': clean_quiz
                }
                
                return render_template('index.html', results=display_results)

            except Exception as e:
                # Gérer les erreurs de fichier ou d'API
                app.logger.error(f"Erreur de traitement: {e}")
                return render_template('index.html', error=f"Erreur de traitement du fichier ou de l'IA: {e}")

    return render_template('index.html', results=None)

# NOUVELLE ROUTE : Traite la soumission du quiz par l'utilisateur
@app.route('/check_quiz', methods=['POST'])
def check_quiz():
    # 1. Récupérer les réponses correctes stockées côté serveur
    correct_answers = session.get('correct_answers', {})
    
    # 2. Récupérer les réponses soumises par l'utilisateur
    user_answers = request.form.to_dict()
    
    # 3. Comparer et construire le résultat de la correction
    correction = []
    
    for q_num, user_answer in user_answers.items():
        if q_num.startswith('q'):
            # Extrait le numéro de question (ex: 'q1' -> '1')
            num = q_num[1:]
            
            # Récupère la réponse correcte pour cette question
            correct_ans = correct_answers.get(num, 'N/A')

            is_correct = (user_answer == correct_ans)
            
            correction.append({
                'q_num': num,
                'user_answer': user_answer,
                'correct_answer': correct_ans,
                'is_correct': is_correct
            })
    
    # Renvoyer la correction au client au format JSON
    return json.dumps({'correction': correction})


if __name__ == '__main__':
    # REMPLACEZ 'default_secret_key_for_dev' par une clé aléatoire forte en production
    # Lancez avec python app.py
    app.run(debug=True)