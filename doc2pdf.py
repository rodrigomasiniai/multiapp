import streamlit as st
from docx import Document
import re
from cleantext import clean
from spellchecker import SpellChecker
from fpdf import FPDF
import os
from base64 import b64encode

st.set_page_config(page_title="Text to PDF Converter", layout="wide")
hide_streamlit_footer = """<style>#MainMenu {visibility: hidden;}
                        footer {visibility: hidden;}</style>"""
st.markdown(hide_streamlit_footer, unsafe_allow_html=True)

st.title('Doc to PDF converter')

class TextProcessor:
    def __init__(self):
        pass

    def corr(self, s: str, add_space_when_numerics=False, exceptions=["e.g.", "i.e.", "etc.", "cf.", "vs.", "p."]) -> str:
        if add_space_when_numerics:
            s = re.sub(r"(\d)\.(\d)", r"\1. \2", s)
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r'\s([?.!"](?:\s|$))', r"\1", s)
        s = re.sub(r"\s\'", r"'", s)
        s = re.sub(r"'\s", r"'", s)
        s = re.sub(r"\s,", r",", s)
        for e in exceptions:
            expected_sub = re.sub(r"\s", "", e)
            s = s.replace(expected_sub, e)
        return s

    def fix_punct_spaces(self, string):
        fix_spaces = re.compile(r"\s*([?!.,]+(?:\s+[?!.,]+)*)\s*")
        string = fix_spaces.sub(lambda x: "{} ".format(x.group(1).replace(" ", "")), string)
        string = string.replace(" ' ", "'")
        string = string.replace(' " ', '"')
        return string.strip()

    def cleantxt_ocr(self, ugly_text, lower=False, lang: str = "en") -> str:
        cleaned_text = clean(
            ugly_text,
            fix_unicode=True,
            to_ascii=True,
            lower=lower,
            no_urls=True,
            no_emails=True,
            no_phone_numbers=False,
            no_numbers=False,
            no_digits=False,
            no_currency_symbols=False,
            replace_with_punct="",
            replace_with_url="<URL>",
            replace_with_email="<EMAIL>",
            replace_with_phone_number="<PHONE>",
            replace_with_number="<NUM>",
            replace_with_digit="0",
            replace_with_currency_symbol="<CUR>",
            lang=lang,
        )
        return cleaned_text

    def check_word_spelling(self, word) -> bool:
        spell = SpellChecker()
        misspelled = spell.unknown([word])
        return len(misspelled) == 0

    def eval_and_replace(self, text: str, match_token: str = "- ") -> str:
        if match_token not in text:
            return text
        else:
            while True:
                full_before_text = text.split(match_token, maxsplit=1)[0]
                split_before_text = full_before_text.split()
                before_text = "".join([char for char in split_before_text[-1]] if split_before_text else "")

                full_after_text = text.split(match_token, maxsplit=1)[-1]
                split_after_text = full_after_text.split()
                after_text = "".join([char for char in split_after_text[0]] if split_after_text else "")

                full_text = before_text + after_text
                if self.check_word_spelling(full_text):
                    text = full_before_text + full_after_text
                else:
                    text = full_before_text + " " + full_after_text
                if match_token not in text:
                    break
        return text


def process_text(file):
    text_processor = TextProcessor()
    document = Document(file)
    result = []
    for paragraph in document.paragraphs:
        if paragraph.style.name.startswith('Heading'):
            result.append('\n' + paragraph.text + '\n')
        else:
            processed_paragraph = text_processor.corr(paragraph.text)
            processed_paragraph = text_processor.cleantxt_ocr(processed_paragraph)
            processed_paragraph = text_processor.fix_punct_spaces(processed_paragraph)
            processed_paragraph = text_processor.eval_and_replace(processed_paragraph)
            result.append(processed_paragraph)
    return "\n".join(result)

def create_pdf(text, filename):
    pdf = FPDF(format='letter')
    pdf.add_page()
    pdf.set_font("Arial", size = 12)
    pdf.set_auto_page_break(auto=True, margin=15)
    lines = text.split('\n')
    for line in lines:
        pdf.multi_cell(0, 10, txt = line, align = 'L')
    pdf.output(filename)

def get_pdf_download_link(file_path, file_name):
    with open(file_path, "rb") as f:
        bytes = f.read()
        b64 = b64encode(bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{file_name}">Click here to Download your PDF</a>'
        return href

uploaded_file = st.file_uploader("Choose a Word document", type="docx")
if uploaded_file is not None:
    with st.spinner('Processing the document...'):
        # Write the uploaded file to disk
        file_name = uploaded_file.name
        base_file_name = os.path.splitext(file_name)[0]
        pdf_file_name = f"{base_file_name}.pdf"

        with open(file_name, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        # Process the document
        text = process_text(file_name)

        # Create the PDF
        create_pdf(text, pdf_file_name)

        # Provide the download link for the PDF
        st.markdown(get_pdf_download_link(pdf_file_name, pdf_file_name), unsafe_allow_html=True)

        # Remove the temporary files
        os.remove(file_name)
        os.remove(pdf_file_name)

        st.success('Done!')
else:
    st.info('Please upload a Word document.')