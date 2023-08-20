from pypdf import PdfReader
from uuid import uuid4
import os

# Custom imports

from utils.decorators import dtraia_decorator

@dtraia_decorator("api", None)
def extract_text(pdf_file, out_name = None, out_path = None, selected_pages = [], split_by_page = False, log = None):
    if not os.path.isfile(pdf_file):
        log.info("El archivo PDF {} no existe".format(pdf_file))
        return None
    
    if not out_name:
        out_name = "".join(uuid4().hex.split("-"))[:15]
    if not out_path: 
        out_path = os.getcwd()

    os.makedirs(out_path, exist_ok=True)

    pdf_reader = PdfReader(pdf_file)

    if len(selected_pages) <= 0:
        selected_pages = [ x for x in range(len(pdf_reader.pages)) ]
    
    log.info("Extracting text from pages: {}".format(selected_pages))

    generated_files = []
    
    if split_by_page:
        for page_number in selected_pages:
            actual_page = pdf_reader.pages[page_number]
            text_in_page = actual_page.extract_text(0)
            file_path = "{}/{}_{}.txt".format(out_path, out_name, (page_number + 1))
            with open(file_path, "w", encoding="utf8") as f:
                f.write(text_in_page)
            generated_files.append(file_path)
    else:
        file_path = "{}/{}.txt".format(out_path, out_name)
        with open(file_path, "w", encoding="utf8") as f:
            for page_number in selected_pages:
                actual_page = pdf_reader.pages[page_number]
                text_in_page = actual_page.extract_text(0)
                f.write(text_in_page)
                f.write("\n\n")
        generated_files.append(file_path)

    log.info("Finish processing file {} --> {}".format(pdf_file, generated_files))

    return True

if __name__ == "__main__":

    args = {
        "pdf_file": "/Users/ralvarez20/Documents/Proyects/dtraia_api/documents",
        "out_name": "REDES_C1",
        "out_path": "/Users/ralvarez20/Documents/Proyects/dtraia_api/out_docs",
        "selected_pages": [],
        "split_by_page": False
    }

    for file in os.listdir("documents"):
        args["pdf_file"] = "/Users/ralvarez20/Documents/Proyects/dtraia_api/documents/" + file
        args["out_name"] = "REDES_{}".format( file.split(".")[1].strip().replace(" ", "_") )
        extract_text(**args)