import os
import csv
import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract

# Initiera OpenAI-klient
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("Remissanalys med OCR-stöd")

uploaded_files = st.file_uploader("Ladda upp remisser i PDF-format", type="pdf", accept_multiple_files=True)

def extract_text_from_pdf(pdf_file):
    """Försök extrahera text, använd OCR om det inte går."""
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    
    if text.strip():  # Om vi hittade text, returnera den
        return text

    # Annars: använd OCR på varje sida som bild
    images = convert_from_bytes(pdf_file.read(), dpi=300)
    ocr_text = ""
    for image in images:
        ocr_text += pytesseract.image_to_string(image, lang='swe') + "\n"
    return ocr_text

if uploaded_files:
    referring_doctors = []

    for uploaded_file in uploaded_files:
        pdf_text = extract_text_from_pdf(uploaded_file)

        # Skicka prompt till GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "Du är en medicinsk sekreterare som analyserar remisser. "
                    "Extrahera:\n- Namnet på inremitterande läkare (Doktor)\n"
                    "- Vilken klinik patienten troligen ska remitteras till "
                    "(en av: Kardiologen, Onkologen, Barnmedicin, Lungmedicin, Njurmedicin)\n"
                    "- Hur säker du är på detta (Väldigt säker, Säker, Osäker)\n\n"
                    "Svara i följande format:\n"
                    "Doktor: <namn>\n"
                    "Trolig mottagare: <klinik>\n"
                    "Sannolikhet: <nivå>"
                )},
                {"role": "user", "content": f"Här är remisstexten:\n\n{pdf_text}"}
            ],
            max_tokens=300
        )

        content = response.choices[0].message.content.strip()
        lines = content.splitlines()
        try:
            doktor = lines[0].split(":", 1)[1].strip()
            mottagare = lines[1].split(":", 1)[1].strip()
            sannolikhet = lines[2].split(":", 1)[1].strip()
        except IndexError:
            doktor = mottagare = sannolikhet = "Ej identifierad"

        referring_doctors.append((uploaded_file.name, doktor, mottagare, sannolikhet))

    # Visa resultat
    st.subheader("Remissbedömning")
    df = pd.DataFrame(referring_doctors, columns=["Filnamn", "Remittent", "Lämplig mottagare", "Bedömningens säkerhet"])
    st.table(df)
