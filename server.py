"""
PDF Audio Server — Backend
Handles PDF text extraction only.
Translation and TTS are handled by the frontend.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import tempfile
import os

app = Flask(__name__)
CORS(app)

MAX_PAGES = 10  # Max pages per request to avoid timeout


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'Server is running!'})


@app.route('/extract', methods=['POST'])
def extract():
    """
    Extract text from a PDF file.
    Accepts: multipart/form-data with 'pdf' file, 'start_page', 'end_page'
    Returns: JSON with extracted text and pagination info
    """
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF file received'}), 400

    pdf_file   = request.files['pdf']
    start_page = int(request.form.get('start_page', 1))
    end_page   = int(request.form.get('end_page', 9999))

    # Save to temp file
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf_file.save(tmp.name)
            tmp_path = tmp.name

        text_parts = []
        total_pages = 0

        with pdfplumber.open(tmp_path) as pdf:
            total_pages  = len(pdf.pages)
            actual_start = max(0, start_page - 1)           # 0-based
            actual_end   = min(total_pages, end_page)

            # Limit pages per request to avoid timeout
            if (actual_end - actual_start) > MAX_PAGES:
                actual_end = actual_start + MAX_PAGES

            for i in range(actual_start, actual_end):
                page_text = pdf.pages[i].extract_text()
                if page_text and page_text.strip():
                    text_parts.append(page_text.strip())

        full_text = '\n\n'.join(text_parts)

        if not full_text.strip():
            return jsonify({'error': 'No text found. The PDF may be a scanned image.'}), 400

        has_more    = actual_end < min(total_pages, end_page)
        next_start  = actual_end + 1 if has_more else None

        return jsonify({
            'text':            full_text,
            'total_pages':     total_pages,
            'processed_start': actual_start + 1,
            'processed_end':   actual_end,
            'has_more':        has_more,
            'next_start':      next_start,
            'characters':      len(full_text),
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    print("✅ PDF Audio Server running!")
    print("📡 Endpoints: /health  /extract")
    print("🛑 Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=5000, debug=False)
