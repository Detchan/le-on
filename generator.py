import os
import json
from google import genai
from google.genai import types

# Initialisation du client Gemini
# Il est préférable de lire la clé depuis les variables d'environnement (GEMINI_API_KEY)
# Cela est nécessaire pour le déploiement sur Render.
try:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
except Exception as e:
    # Gérer l'erreur si la clé n'est pas trouvée (utile en développement)
    print("Erreur : La clé GEMINI_API_KEY n'est pas configurée dans les variables d'environnement.")
    print(f"Détail de l'erreur: {e}")
    client = None


def generate_quiz_and_review(text_content, subject):
    """
    Génère des fiches de révision et un quiz basé sur le contenu textuel fourni
    et la matière sélectionnée.

    Args:
        text_content (str): Le texte extrait du document PDF.
        subject (str): La matière sélectionnée par l'utilisateur (ex: 'Mathématiques').

    Returns:
        dict: Les résultats structurés en JSON (fiches et quiz).
    """
    
    if not client:
        # Renvoyer une structure vide si l'API n'est pas initialisée
        return {"review_sheets": [], "quiz": []}
        
    # --- PROMPT MIS À JOUR AVEC LA MATIÈRE ---
    prompt = f"""
    Vous êtes un expert en {subject} et un assistant pédagogique. Votre tâche est de créer des outils
    de révision à partir du texte suivant. 
    
    Instruction:
    1. Générez au moins 3 fiches de révision (review_sheets) couvrant les points clés du document. 
       Les titres et le contenu des fiches doivent être contextualisés pour la matière '{subject}'.
    2. Générez 10 questions de quiz à choix unique (une seule bonne réponse) basées sur la matière {subject} et ce document.
    
    Utilisez le format JSON strict suivant pour la sortie:
    {{
        "review_sheets": [
            {{"title": "Titre du thème 1 ({subject})", "points": ["Point clé 1", "Point clé 2", "Point clé 3", ... ]}},
            {{"title": "Titre du thème 2 ({subject})", "points": ["Point clé 1", "Point clé 2", "Point clé 3", ... ]}},
            {{"title": "Titre du thème 3 ({subject})", "points": ["Point clé 1", "Point clé 2", "Point clé 3", ... ]}}
        ],
        "quiz": [
            {{"question": "La question...", "options": ["Option A", "Option B", "Option C", "Option D"], "correct_answer": "La bonne option"}},
            ... (9 autres questions)
        ]
    }}
    
    Contenu à analyser:
    ---
    {text_content}
    ---
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        # Le contenu de la réponse est une chaîne JSON valide
        return json.loads(response.text)

    except Exception as e:
        print(f"Erreur lors de l'appel à l'API Gemini : {e}")
        # Renvoyer une structure vide en cas d'échec
        return {"review_sheets": [], "quiz": []}

if __name__ == '__main__':
    # Exemple de test si le script est exécuté directement
    test_content = "Le théorème de Thalès stipule que si deux droites sécantes sont coupées par deux droites parallèles, alors les segments découpés sur les droites sécantes sont proportionnels. Ceci est fondamental en géométrie pour calculer des longueurs inconnues."
    
    # Assurez-vous d'avoir la variable GEMINI_API_KEY dans votre environnement pour tester
    if client:
        print("Génération de contenu test (Mathématiques)...")
        results = generate_quiz_and_review(test_content, "Mathématiques")
        print("\n--- RÉSULTATS GÉNÉRÉS ---")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("Test non exécuté car la clé API n'est pas configurée.")
