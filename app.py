import os
import io
import json
from flask import Flask, render_template, request, session, redirect, url_for
from pypdf import PdfReader
from generator import generate_quiz_and_review
from werkzeug.utils import secure_filename

# Configuration
app = Flask(__name__)
# NOUVEAU : Récupération de la clé secrète pour les sessions (OBLIGATOIRE !)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_a_changer_en_production') 

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_stream):
    reader = PdfReader(file_stream)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    # Limiter la taille du texte envoyé à l'IA
    return text[:6000] 

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        
        # NOUVEAU : Récupérer la matière sélectionnée
        selected_subject = request.form.get('subject') 
        if not selected_subject:
             return render_template('index.html', error="Veuillez sélectionner une matière.")
             
        if file.filename == '' or not allowed_file(file.filename):
            return redirect(request.url)

        if file:
            try:
                # 1. Extraction du texte
                pdf_stream = io.BytesIO(file.read())
                text_content = extract_text_from_pdf(pdf_stream)
                
                # 2. Génération par l'IA - ENVOI DE LA MATIÈRE
                ia_results = generate_quiz_and_review(text_content, selected_subject) 
                
                # 3. Stockage des réponses correctes dans la session (SÉCURISÉ)
                correct_answers = {}
                for idx, item in enumerate(ia_results.get('quiz', [])):
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
                app.logger.error(f"Erreur de traitement: {e}")
                return render_template('index.html', error=f"Erreur de traitement du fichier ou de l'IA: {e}")

    return render_template('index.html', results=None)

# ROUTE : Traite la soumission du quiz par l'utilisateur
@app.route('/check_quiz', methods=['POST'])
def check_quiz():
    correct_answers = session.get('correct_answers', {})
    user_answers = request.form.to_dict()
    
    correction = []
    
    for q_num, user_answer in user_answers.items():
        if q_num.startswith('q'):
            num = q_num[1:]
            correct_ans = correct_answers.get(num, 'N/A')

            # IMPORTANT : Le back-end vérifie toujours une seule bonne réponse,
            # même si l'utilisateur peut cocher plusieurs cases.
            is_correct = (user_answer == correct_ans)
            
            correction.append({
                'q_num': num,
                'user_answer': user_answer,
                'correct_answer': correct_ans,
                'is_correct': is_correct
            })
    
    return json.dumps({'correction': correction})


if __name__ == '__main__':
    app.run(debug=True)
