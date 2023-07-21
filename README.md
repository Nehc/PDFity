# PDFity
PDF “swiss army knife” (multitool). Translate, OCR, text extraction, etc.

### Install 
```
git clone https://github.com/Nehc/PDFity.git
cd PDFity
docker-compose up
```
![image](https://github.com/Nehc/PDFity/assets/8426195/a14fb3fc-12ba-463f-aad1-b984fc203b5e)


### How to use 
1. You have a document in PDF scan. You can get its OCR-text. Upload the file and click **OCR**. You can set the language if needed.
2. You receive PDF with OCR (or you have a regular pdf with text conent). You want to translate it into russian. You can do this in two ways:
   - Just klick **Translate (RU)**. But... It's not good idea because... Automatic translate is not very good: formulas, same else...
   - You сan got original and translated document in one: page by page. Select *eng+rus* option in language and make a translate!
3. You may extract text for... I don't know for what purpose, but it might come in handy! Just do it with **Extract text** option.
4. For the best quality, the russian text can be corrected with a with spell cheker (jamspell).
5. And last (for now), you can upload image, which will be automatically converted to pdf for all operations with it!       

