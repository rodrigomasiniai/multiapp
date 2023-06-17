from streamlit_ace import st_ace
import streamlit as st
from base64 import b64encode
from easyocr_functions import *

_here = Path(__file__).parent

def convert_PDF(pdf_path, language: str = "en", max_pages=20):
    # clear local text cache
    rm_local_text_files()

    st = time.perf_counter()

    if not pdf_path.endswith(".pdf"):
        logging.error(f"File {pdf_path} is not a PDF file")
        return "File is not a PDF file", None

    conversion_stats = convert_PDF_to_Text(pdf_path, max_pages=max_pages)
    converted_txt = conversion_stats["converted_text"]

    rt = round((time.perf_counter() - st) / 60, 2)
    print(f"Runtime: {rt} minutes")

    output_name = f"{Path(pdf_path).stem}_OCR.txt"
    with open(output_name, "w", encoding="utf-8", errors="ignore") as f:
        f.write(converted_txt)

    return converted_txt, output_name

st.set_page_config(page_title="AI writer assistant", page_icon="img/Oxta_MLOpsFactor_logo.png", layout="wide")
hide_decoration_bar_style = '''<style>header {visibility: hidden;}</style>'''
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)
# Design hide "made with streamlit" footer menu area
hide_streamlit_footer = """<style>#MainMenu {visibility: hidden;}
                        footer {visibility: hidden;}</style>"""
st.markdown(hide_streamlit_footer, unsafe_allow_html=True)
st.markdown('''<style>.css-1egvi7u {margin-top: -4rem;}</style>''',
    unsafe_allow_html=True)
st.title('PDF converter')

st.write("""
This app converts PDF files into text, cleans the resulting text, and optionally translates the text to a specified language.
""")

def get_text_download_link(file_path, file_name):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        b64 = b64encode(text.encode()).decode()
        href = f'<a href="data:text/plain;base64,{b64}" download="{file_name}">Click here to Download your Text File</a>'
        return href

def format_text_width(text, max_line_length=120):
    """Inserts a newline character every nth character in a string"""
    lines = text.split('\n')
    formatted_lines = []
    for line in lines:
        while len(line) > max_line_length:
            split_index = line[:max_line_length].rfind(' ')
            if split_index == -1: # no spaces found, we must split on max_line_length
                split_index = max_line_length
            formatted_lines.append(line[:split_index])
            line = line[split_index:].strip()
        formatted_lines.append(line)
    return '\n'.join(formatted_lines)

uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
if uploaded_file is not None:
    with st.spinner('Converting PDF to text...'):
        with open(_here / "temp.pdf", 'wb') as f:
            f.write(uploaded_file.getbuffer())
        pdf_path = str(_here / "temp.pdf")
        converted_txt, output_file = convert_PDF(pdf_path)
        if converted_txt:
            formatted_text = format_text_width(converted_txt.replace('\n', '\n\n'))
            st_ace(formatted_text, language="python", theme="textmate", height=300, key="converted_pdf")
            st.markdown(get_text_download_link(output_file, output_file), unsafe_allow_html=True)
        os.remove(pdf_path)
else:
    st.info('Please upload a PDF file.')
