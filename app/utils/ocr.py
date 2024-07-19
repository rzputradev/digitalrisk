import json
import numpy as np
from doctr.models import ocr_predictor
from pdf2image import convert_from_path
from PIL import Image

def perform_ocr(filename):
    try:
        predictor = ocr_predictor(pretrained=True)
        
        if filename.endswith('.pdf'):
            images = convert_from_path(filename)
        else:
            images = [Image.open(filename)]

        all_text = []
        all_data_json = {"pages": []}

        for idx, image in enumerate(images):
            np_image = np.array(image.convert('RGB'))
            document = predictor([np_image])
            page_data = {"page_idx": idx, "language": "English", "blocks": []}

            for block in document.pages[0].blocks:
                block_data = {"geometry": str(block.geometry), "lines": []}
                for line in block.lines:
                    line_data = {"geometry": str(line.geometry), "words": []}
                    for word in line.words:
                        word_data = {
                            "value": word.value,
                            "confidence": word.confidence,
                            "geometry": str(word.geometry)
                        }
                        line_data["words"].append(word_data)
                    block_data["lines"].append(line_data)
                page_data["blocks"].append(block_data)
            
            all_data_json["pages"].append(page_data)
            
            page_text = ' '.join(
                ' '.join(
                    ' '.join(word.value for word in line.words)
                    for line in block.lines
                )
                for block in document.pages[0].blocks
            )
            all_text.append(page_text)

        result = json.dumps(all_data_json, indent=4)

        return {'error': False, 'result': result}

    except Exception as e:
         return {'error': True, 'result': f'Error: {e}'}
        #  raise Exception(f'Error: {e}')
