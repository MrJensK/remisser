import os
import csv
import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import pandas as pd

# Initiera OpenAI-klient
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Streamlit app
st.title("Remissanalys")

uploaded_files = st.file_uploader("Ladda upp remisser i PDF-format", type="pdf", accept_multiple_files=True)

# Kör analysen
if uploaded_files:
    referring_doctors = []
    for uploaded_file in uploaded_files:
        # Läs PDF-innehåll
        pdf_reader = PdfReader(uploaded_file)
        pdf_text = "\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())

        # Skicka prompt till OpenAI
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

        # Extrahera svar
        content = response.choices[0].message.content.strip()
        lines = content.splitlines()
        doktor = lines[0].split(":", 1)[1].strip() if len(lines) > 0 else "Okänd"
        mottagare = lines[1].split(":", 1)[1].strip() if len(lines) > 1 else "Okänd"
        sannolikhet = lines[2].split(":", 1)[1].strip() if len(lines) > 2 else "Okänd"

        referring_doctors.append((doktor, mottagare, "High"))  # Example: Adding a placeholder for "Bedömningens säkerhet"

    # Spara till CSV
    csv_file = "referring_doctors.csv"
    with open(csv_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Remittent", "Lämplig mottagare", "Bedömningens säkerhet"])
        writer.writerows(referring_doctors)

    # Läs och visa CSV
    with open(csv_file, mode="r") as file:
        reader = csv.reader(file)
        next(reader)
        referring_doctors = list(reader)

    # Add table column headings explicitly
    st.subheader("Referring Doctors")
    if referring_doctors:
        st.write("### Tabell med remissdata")
        st.table(pd.DataFrame(referring_doctors, columns=["Remittent", "Lämplig mottagare", "Bedömningens säkerhet"]))
    else:
        st.write("No referring doctors found.")
