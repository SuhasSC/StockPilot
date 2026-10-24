import unicodedata

CATEGORY_ALIASES = {
    "electronics": "Electronics",
    "electrónica": "Electronics",
    "electronica": "Electronics",
    "électronique": "Electronics",
    "elektronik": "Electronics",
    "elektronikartikel": "Electronics",
    "elettronica": "Electronics",
    "eletrônicos": "Electronics",
    "eletronicos": "Electronics",
    "elektronica": "Electronics",
    "электроника": "Electronics",
    "الإلكترونيات": "Electronics",
    "الالكترونيات": "Electronics",
    "电子产品": "Electronics",
    "电子设备": "Electronics",
    "電子機器": "Electronics",
    "전자제품": "Electronics",
    "ಇಲೆಕ್ಟ್ರಾನಿಕ್ಸ್": "Electronics",
    "எலக்ட்ரானிக்ஸ்": "Electronics",
    "इलेक्ट्रॉनिक्स": "Electronics",
    "इलेक्ट्रॉनिक": "Electronics",
    "electrÃ³nica": "Electronics",
    "Ã©lectronique": "Electronics",

    "furniture": "Furniture",
    "muebles": "Furniture",
    "meubles": "Furniture",
    "möbel": "Furniture",
    "mobel": "Furniture",
    "arredamento": "Furniture",
    "móveis": "Furniture",
    "moveis": "Furniture",
    "meubels": "Furniture",
    "мебель": "Furniture",
    "الأثاث": "Furniture",
    "اثاث": "Furniture",
    "家具": "Furniture",
    "家具類": "Furniture",
    "가구": "Furniture",
    "ಪೀಠೋಪಕರಣಗಳು": "Furniture",
    "தளபாடங்கள்": "Furniture",
    "फर्नीचर": "Furniture",
}

def normalize_category(value):
    if not isinstance(value, str):
        return value

    key = unicodedata.normalize("NFC", value).strip().casefold()
    return CATEGORY_ALIASES.get(key, value)
