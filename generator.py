import os
import json
from google import genai
from google.genai import types

# La clé d'API est lue automatiquement à partir de la variable d'environnement GEMINI_API_KEY
try:
    client = genai.Client()
except Exception as e:
    print(f"Erreur d'initialisation de l'IA : Assurez-vous que la variable GEMINI_API_KEY est définie. {e}")
    client = None


def generate_quiz_and_review(text_content):
    if not client:
        return {
            "review_sheets": [{"title": "ERREUR DE CONFIGURATION", "points": ["L'API Gemini n'est pas configurée. Voir l'étape d'installation de la clé."]}],
            "quiz": [{"question": "Configuration de l'IA manquante.", "options": ["A", "B"], "correct_answer": "N/A"}]
        }

    # Nouvelle consigne : demander 10 questions QCM et 3 fiches de révisions avec titres.
    prompt = f"""
    En tant qu'outil pédagogique avancé, analyse le texte ci-dessous pour créer deux structures distinctes, complètes et bien détaillées :
    1. 'review_sheets': Une liste de 3 fiches de révision séparées. Chaque fiche doit avoir un 'title' unique et pertinent et une liste de 5 à 7 'points' clés (points concis pour la mémorisation).
    2. 'quiz': Une liste de 10 questions à choix multiples (QCM). Chaque question doit avoir 3 options (options) et la réponse correcte (correct_answer) doit être une des options.

    Le résultat DOIT être un seul objet JSON valide et complet respectant la structure suivante :
    {{
        "review_sheets": [
            {{
                "title": "Titre du premier thème",
                "points": ["Point 1", "Point 2", ...]
            }},
            {{
                "title": "Titre du deuxième thème",
                "points": ["Point 1", "Point 2", ...]
            }}
        ],
        "quiz": [
            {{
                "question": "Votre question ici",
                "options": ["Choix A", "Choix B", "Choix C"],
                "correct_answer": "Choix B"
            }},
            ... (10 questions au total)
        ]
    }}
    
    TEXTE À ANALYSER :
    ---
    {text_content[:6000]}
    ---
    """
    
    # Configuration pour obtenir une réponse JSON structurée
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema={
            "type": "object",
            "properties": {
                "review_sheets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "points": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["title", "points"]
                    }
                },
                "quiz": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "options": {"type": "array", "items": {"type": "string"}},
                            "correct_answer": {"type": "string"}
                        },
                        "required": ["question", "options", "correct_answer"]
                    }
                }
            },
            "required": ["review_sheets", "quiz"]
        },
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=config,
        )
        
        return json.loads(response.text)

    except Exception as e:
        print(f"Erreur lors de l'appel à l'API Gemini : {e}")
        # Retourne une structure compatible en cas d'erreur
        return {
            "review_sheets": [{"title": "ERREUR AI", "points": [f"Détails de l'erreur : {e}"]}],
            "quiz": []
        }