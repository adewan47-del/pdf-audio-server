from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import tempfile
import os

app = Flask(__name__)
CORS(app)

@app.route('/extract', methods=['POST'])
def extract_text():
    try:
        if 'pdf' not in request.files:
            return jsonify({'error': 'No PDF file received'}), 400

        pdf_file = request.files['pdf']

        # Get page range from request
        start_page = int(request.form.get('start_page', 1))
        end_page = int(request.form.get('end_page', 9999))

        # Save to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf_file.save(tmp.name)
            tmp_path = tmp.name

        # Extract text with page range
        text_parts = []
        with pdfplumber.open(tmp_path) as pdf:
            total = len(pdf.pages)
            # Clamp to actual page count
            actual_start = max(1, start_page) - 1        # convert to 0-based
            actual_end   = min(total, end_page)           # inclusive

            for i in range(actual_start, actual_end):
                page_text = pdf.pages[i].extract_text()
                if page_text and page_text.strip():
                    text_parts.append(page_text.strip())

        # Clean up temp file
        os.unlink(tmp_path)

        full_text = '\n\n'.join(text_parts)

        if not full_text.strip():
            return jsonify({'error': 'No text found in those pages. The PDF may be a scanned image.'}), 400

        return jsonify({
            'text': full_text,
            'pages': total,
            'extracted_pages': actual_end - actual_start,
            'characters': len(full_text)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'Server is running!'})

if __name__ == '__main__':
    print("✅ PDF Server is running!")
    print("📡 Your phone can now send PDFs to this server")
    print("🛑 Press Ctrl+C to stop the server")
    app.run(host='0.0.0.0', port=5000, debug=False)
