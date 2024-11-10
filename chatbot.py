import os
import requests
from bs4 import BeautifulSoup
import openai
from openai import AzureOpenAI
from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import unicodedata

# Configurarea OpenAI
openai.api_key = os.getenv("6wg18MMZ9VmVnWH3lQB2ziSrmjiAFz1AndPuOOL7v2uzNNVzAXYgJQQJ99AKACfhMk5XJ3w3AAABACOGKhWf")  # Asigură-te că ai setat cheia API corect
client = AzureOpenAI(
    azure_endpoint="https://rbro-openai-hackatlon.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview", 
    api_key="6wg18MMZ9VmVnWH3lQB2ziSrmjiAFz1AndPuOOL7v2uzNNVzAXYgJQQJ99AKACfhMk5XJ3w3AAABACOGKhWf",  # Folosește variabila de mediu pentru API key
    api_version="2024-08-01-preview"
)

# Lista pentru stocarea răspunsurilor chatbotului
chat_history = []

def remove_diacritics(text):
    """Elimină diacriticele dintr-un text."""
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
def get_webpage_text(page_url):
    """Obține textul de pe o pagină web dată."""
    try:
        response = requests.get(page_url, allow_redirects=True)
        response.raise_for_status()  # Aruncă o excepție pentru coduri de stare eronate
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    except requests.exceptions.RequestException as e:
        print(f"Eroare la accesarea paginii web: {e}")
        return None

def answer_question_from_url(user_question, page_url):
    """Răspunde la o întrebare pe baza textului obținut de pe o pagină web."""
    text = get_webpage_text(page_url)
    if not text:
        return "Nu am putut accesa pagina web."

    # Pregătește promptul pentru modelul GPT
    prompt = f"Citește următorul text și răspunde la întrebarea: {user_question}\n\nText: {text[:40000]}\n\nRăspuns:"

    # Trimite cererea către API-ul GPT-4o
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=None,
        temperature=0
    )
    
    answer = response.choices[0].message.content.strip()
    
    chat_history.append(remove_diacritics(answer))  # Salvează răspunsul fără diacritice
    # Adaugă răspunsul în istoric
    #chat_history.append(f"Mirel: {answer}")  # Salvează răspunsul cu prefixul "Mirel"
    
    return answer

# Configurarea Flask
app = Flask(__name__)
app.static_folder = 'static'

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_openai_response")
def get_openai_response():
    user_question = request.args.get('question')
    page_url = request.args.get('url')
    return answer_question_from_url(user_question, page_url)

@app.route("/generate_pdf")
def generate_pdf():
    pdf_path = r"C:\Users\anama\Downloads\ESGINEERS_Hackathon\pythonProject2\pythonProject2\chat_history.pdf"  # Numele fișierului PDF

    # Crează PDF-ul
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Adaugă mesajele în PDF
    y_position = height - 40  # Poziția verticală de început

     # Verifică dacă există mesaje în istoricul chatului
    if chat_history:
        last_message = chat_history[-1]  # Obține doar ultimul mesaj
        y_position = height - 40  # Poziția verticală de început
        text_object = c.beginText(30, y_position)
        #text_object.setFont("DejaVuSans", 12)

        # Împărțirea mesajului în linii
        for line in last_message.splitlines():
            # Asigură-te că linia nu depășește lățimea paginii
            while line:
                # Verifică lungimea liniei și taie dacă este necesar
                if len(line) > 100:  # Ajustează lungimea maximă a liniei după necesitate
                    split_index = line.rfind(' ', 0, 100)  # Găsește ultimul spațiu înainte de limita de 100 caractere
                    if split_index == -1:  # Dacă nu există spațiu, taie la 100 de caractere
                        split_index = 100
                    text_object.textLine(line[:split_index])
                    line = line[split_index:].lstrip()  # Taie liniile procesate
                else:
                    text_object.textLine(line)
                    break

        c.drawText(text_object)
        y_position -= 20  # Scade poziția pentru fiecare mesaj
        
        if y_position < 40:  # Dacă ajunge la marginea paginii, adaugă o pagină nouă
            c.showPage()
            y_position = height - 40

    c.save()

    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)