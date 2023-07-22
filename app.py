import os, shutil
from time import sleep
import gradio as gr
import fitz, nltk, ocrmypdf
from googletrans import Translator
from pdf2image import convert_from_path
from tqdm.contrib.telegram import trange as tg_range
from tqdm import trange
from langdetect import detect
from jamspell import TSpellCorrector
#from pytesseract import image_to_pdf_or_hocr

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

translator = Translator()
corrector = TSpellCorrector()
corrector.LoadLangModel('../ru_small.bin')

def is_content(text):
    words = nltk.word_tokenize(text)
    pos_tags = nltk.pos_tag(words)
    # Проверяем, что есть хотя бы одно существительное (NN), или глагол (VB)
    for word, pos in pos_tags:
        if (pos.startswith("NN") or 
            pos.startswith("VB")):
            return True
    return False

def pdf_translation(input_file,
                    token=None,
                    chat_id=None, 
                    t_lang='eng+rus', 
                    clear_save_origin=True, 
                    #progress=gr.Progress(track_tqdm=True) 
                    #rise error https://github.com/gradio-app/gradio/issues/4980
                ):
    input_path = input_file.name
    doc = fitz.open(input_path)
    output_path = input_path.replace('.pdf','_trl.pdf')
    if  os.path.exists(output_path):
        res_doc = fitz.open(output_path)
        if res_doc.page_count - (doc.page_count 
                                 if t_lang == 'eng+rus' 
                                 else 0) == doc.page_count:
            return output_path
        else: 
            s_page = (res_doc.page_count - doc.page_count) * \
                        (2 if t_lang == 'eng+rus' else 1)    
    else:
        if clear_save_origin:
            t_name = input_path.replace('.pdf','_tmp.pdf')
            doc.save(t_name, garbage=4, clean=True, # incremental=True, encryption=0, 
                     deflate=True, deflate_images=True, deflate_fonts=True)
            doc.close(); shutil.move(t_name, input_path) 
            doc = fitz.open(input_path)
        doc.ez_save(output_path, encryption=0) 
        res_doc = fitz.open(output_path)
        s_page = 0
    for k in (tg_range(s_page, doc.page_count, 
                       token=token, chat_id=chat_id,
                       descr="Translate pages") if token 
                           else trange(s_page, doc.page_count)):
        #origin_text.append(doc.get_page_text(k))
        page = doc[k]
        ss = []; ps = []
        sbl = page.get_text("dict")["blocks"]
        for block in sbl:
            ls = 0; lc = 0
            if block['type'] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        ls+=span['size'];lc+=1
                ss.append(ls/lc)
                ps.append(block["lines"][0]["spans"][0]['origin'][1])
            else:
              ss.append(0)
              ps.append(0)
        c = 0
        for i, block in enumerate(page.get_text_blocks()):
            if block[6]!=0 or block[1]<0:
                c+=1; continue
            old_text = block[4].replace("\n", " ")
            if is_content(old_text):
                try:
                    translation = translator.translate(
                        old_text, dest='ru'
                    )  # Переводим текст на указанный язык
                    new_text = translation.text  
                except Exception as error:
                  print(error)
                  continue
            else:
               continue
            if old_text != new_text: # and is_content(new_text):
                dr = sbl[i-c]["lines"][0]['dir'][1]
                if dr<0:
                    continue 
                lp = [0]; fs = ss[i-c]
                #print(dr,old_text)
                while len(lp) != 0:
                    fs -= 0.5
                    tw = fitz.TextWriter(page.rect)
                    pos = block[0],ps[i-c] if dr == 0 else block[1]
                    lp = tw.fill_textbox(
                        block[:4], new_text, fontsize=fs, pos=pos,
                        align=fitz.TEXT_ALIGN_JUSTIFY
                    )
                    if fs <= 0: break
                page.add_redact_annot(block[:4],fill=(1,1,1) if 
                                                 input_path.endswith('ocr.pdf') 
                                                 else None)
                page.apply_redactions()
                tw.write_text(page)
        if t_lang == 'eng+rus':
            res_doc.insert_pdf(doc, from_page=k, to_page=k, start_at=k * 2 + 1, links=False)
    if t_lang == 'eng+rus':
        t_name = output_path.replace('.pdf','_tmp.pdf')
        res_doc.save(t_name, garbage=4, clean=True, #incremental=True, encryption=0, 
                     deflate=True, deflate_images=True, deflate_fonts=True)
        shutil.move(t_name, output_path)
    else:
        doc.save(output_path, garbage=4, clean=True, 
                 deflate=True, deflate_images=True, deflate_fonts=True)
    doc.close(); res_doc.close()
    return output_path 

def ocrpdf(input_file,
           token=None,
           chat_id=None,
           language='eng+rus',
           #progress=gr.Progress(track_tqdm=True)
        ):
    if language=='auto':language='eng+rus'
    input = input_file.name
    output = input_file.name.replace('.pdf','_ocr.pdf')
    if token:
        ocrmypdf.ocr(input, output, 
                     language='eng+rus' if language == 'auto' else language,
                     plugins='../tele_tqdm.py', chat_id=chat_id, token=token)
    else:
        ocrmypdf.ocr(input_file.name, output, 
                     language='eng+rus' if language == 'auto' else language)
    return output

with gr.Blocks() as demo:
    gr.Markdown('## PDF "swiss army knife" (multitool). Translate, OCR, text extraction, etc.')
    #with gr.Row():
    with gr.Tabs() as tabs:
        with gr.TabItem('PDF', id=0): 
            file = gr.File(label="File",file_types=['.pdf'])
        with gr.TabItem('Image',id=1): 
            imge = gr.Image(label="File",type='filepath')
    prev = gr.Gallery(label="Preview", allow_preview=False)
    with gr.Row():
        one_text = gr.Textbox(label="Text one", visible=False)
        two_text = gr.Textbox(label="Text two", visible=False)
    with gr.Row(visible=False): #this setion for api only
        token = gr.Textbox(label='tg token',value=None) 
        chat_id = gr.Textbox(label='chat_id',value=None)  
    with gr.Row():    
        lang = gr.Dropdown(["auto","eng+rus","rus+eng", "eng", "rus"], label='Language', value='auto')
        spell = gr.Checkbox(label="Use spell corrector", visible=False) #temporaly not use
    with gr.Row():
        ocr_btn = gr.Button("OCR")
        tr_btn = gr.Button("Translate (RU)")
        tex_btn = gr.Button("Extract text")
        spl_btn = gr.Button("Spell (RU)")
    
    def extract_text(input_file,
                     token=None,
                     chat_id=None,
                     mode = 'auto',
                     #progress=gr.Progress(track_tqdm=True) 
                     #rise error https://github.com/gradio-app/gradio/issues/4980
                ):
        ru_text = []; en_text = []
        doc = fitz.open(input_file.name)
        for k in (tg_range(doc.page_count, 
                           token=token, chat_id=chat_id,
                           desc="Text extraction") if token 
                               else trange(doc.page_count)):
            origin_text = doc.get_page_text(k)    
            if mode == 'rus' or mode == 'rus+eng':
                ru_text.append(origin_text)
            elif mode == 'eng':
                en_text.append(origin_text)
            elif mode == 'eng+rus':
                if k % 2 == 0:
                    en_text.append(origin_text)
                else:
                    ru_text.append(origin_text)
            else: #auto-detect
                try:
                    lang = detect(origin_text)
                except:
                    continue
                if lang == 'ru':
                    ru_text.append(origin_text)
                elif lang == 'en': 
                    en_text.append(origin_text)   
        doc.close()   
        if len(ru_text) > 0 and len(en_text) == 0:
            return {one_text:gr.update(label="Russian text",value='\n'.join(ru_text),visible=True),
                    two_text:gr.update(label="text",value='',visible=False)}
        elif len(en_text) > 0 and len(ru_text) == 0:
            return {one_text:gr.update(label="English text",value='\n'.join(en_text),visible=True),
                    two_text:gr.update(label="text",value='',visible=False)}
        elif len(en_text) > 0 and len(ru_text) > 0:
            return {one_text:gr.update(label="English text",value='\n'.join(en_text),visible=True),
                    two_text:gr.update(label="Russian text",value='\n'.join(ru_text),visible=True)}
        else:
            return {one_text:gr.update(label="text",value='',visible=False),
                    two_text:gr.update(label="text",value='',visible=False)}

    def mirror(input_file,
               #progress=gr.Progress(track_tqdm=True) 
               #rise error https://github.com/gradio-app/gradio/issues/4980
            ):
        res = input_file.name
        for i in trange(100):
            sleep(.1)
        return res 

    def fileOnChange(input_file):
        images=[]
        if input_file:
            images = convert_from_path(input_file.name)
        return {prev:gr.update(value=images,visible=True),
                one_text:gr.update(label="text",value='',visible=False),
                two_text:gr.update(label="text",value='',visible=False)}

    def imgeOnChange(input_image):
        f_name = input_image
        ext = f_name.split('.')[-1]
        n_name = f_name.replace(ext,'pdf')
        os.system(f'tesseract {f_name} {n_name}')
        return {tabs:gr.update(selected=0),
                file:gr.update(value=n_name), 
                prev:gr.update(value=[f_name],visible=True),
                one_text:gr.update(label="text",value='',visible=False),
                two_text:gr.update(label="text",value='',visible=False)}

    def spellCheck(text1,text2):
        if len(text1)>0 and detect(text1)=='ru':
            text2 = corrector.FixFragment(text1)
        elif len(text2)>0 and detect(text2)=='ru':
            text1 = text2
            text2 = corrector.FixFragment(text2) 
        return {one_text:gr.update(label="Origrin text",value=text1,visible=True),
                two_text:gr.update(label="Checked text",value=text2,visible=True)} 
    
    file.change(fileOnChange,inputs=[file],outputs=[prev, one_text, two_text])
    imge.change(imgeOnChange,inputs=[imge],outputs=[tabs, file, prev, one_text, two_text])
    ocr_btn.click(ocrpdf, inputs=[file, token, chat_id, lang], outputs=[file], api_name='ocr')
    tr_btn.click(pdf_translation, inputs=[file, token, chat_id, lang], outputs=[file], api_name='trl')
    tex_btn.click(extract_text, inputs=[file, token, chat_id, lang], outputs=[one_text, two_text], api_name='tex')
    spl_btn.click(spellCheck, inputs=[one_text, two_text], outputs=[one_text, two_text])

#if __name__ == "__main__":
#    demo.queue().launch()

demo.launch() 
