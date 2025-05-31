# management_ai_services.py

import google.generativeai as genai
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.middleware.csrf import get_token
import logging
import json
import base64
from PIL import Image
import io
from difflib import get_close_matches
import traceback

logger = logging.getLogger(__name__)

# Kategori Kualifikasi Medis
KATEGORI_KUALIFIKASI_CHOICES = [
    # --- Kategori Umum Profesi ---
    ('Perawat Umum', 'Perawat Umum'),
    ('Perawat Gigi', 'Perawat Gigi'),
    ('Perawat Anestesi', 'Perawat Anestesi'),
    ('Perawat Bedah', 'Perawat Bedah'),
    ('Dokter Umum', 'Dokter Umum'),
    ('Dokter Gigi', 'Dokter Gigi'),
    ('Bidan', 'Bidan'),
    ('Analis Kesehatan', 'Analis Kesehatan'),
    ('Pranata Laboratorium Kesehatan', 'Pranata Laboratorium Kesehatan'),
    ('Apoteker', 'Apoteker'),
    ('Fisioterapis', 'Fisioterapis'),
    ('Radiografer', 'Radiografer'),
    ('Nutrisionis', 'Nutrisionis'),
    ('Dietisien', 'Dietisien'),
    ('Perekam Medis', 'Perekam Medis'),
    ('Tenaga Kesehatan Lingkungan', 'Tenaga Kesehatan Lingkungan'),
    ('Tenaga Promosi Kesehatan', 'Tenaga Promosi Kesehatan'),
    ('Tenaga Teknis Biomedika', 'Tenaga Teknis Biomedika'),
    ('Asisten Tenaga Kesehatan', 'Asisten Tenaga Kesehatan'),
    ('Volunteer Medis', 'Volunteer Medis'),

    # --- Kategori Spesialisasi Dokter/Profesi Lainnya ---
    ('Spesialis Anak', 'Spesialis Anak'),
    ('Spesialis Penyakit Dalam', 'Spesialis Penyakit Dalam'),
    ('Spesialis Bedah Umum', 'Spesialis Bedah Umum'),
    ('Spesialis Bedah Ortopedi', 'Spesialis Bedah Ortopedi'),
    ('Spesialis Bedah Plastik', 'Spesialis Bedah Plastik'),
    ('Spesialis Bedah Saraf', 'Spesialis Bedah Saraf'),
    ('Spesialis Obstetri & Ginekologi', 'Spesialis Obstetri & Ginekologi'),
    ('Spesialis Mata', 'Spesialis Mata'),
    ('Spesialis THT', 'Spesialis THT'),
    ('Spesialis Jantung & Pembuluh Darah', 'Spesialis Jantung & Pembuluh Darah'),
    ('Spesialis Saraf', 'Spesialis Saraf'),
    ('Spesialis Kulit & Kelamin', 'Spesialis Kulit & Kelamin'),
    ('Spesialis Anestesiologi & Terapi Intensif', 'Spesialis Anestesiologi & Terapi Intensif'),
    ('Spesialis Paru', 'Spesialis Paru'),
    ('Spesialis Kedokteran Fisik & Rehabilitasi', 'Spesialis Kedokteran Fisik & Rehabilitasi'),
    ('Spesialis Patologi Klinik', 'Spesialis Patologi Klinik'),
    ('Spesialis Radiologi', 'Spesialis Radiologi'),
    ('Spesialis Forensik & Medikolegal', 'Spesialis Forensik & Medikolegal'),
    ('Spesialis Kesehatan Jiwa', 'Spesialis Kesehatan Jiwa'),
    ('Spesialis Gizi Klinik', 'Spesialis Gizi Klinik'),
    ('Spesialis Farmakologi Klinik', 'Spesialis Farmakologi Klinik'),
    ('Spesialis Gigi Anak', 'Spesialis Gigi Anak'),
    ('Spesialis Orthodonsia', 'Spesialis Orthodonsia'),
    ('Spesialis Konservasi Gigi', 'Spesialis Konservasi Gigi'),
    ('Spesialis Periodonsia', 'Spesialis Periodonsia'),
    ('Spesialis Penyakit Mulut', 'Spesialis Penyakit Mulut'),
    ('Spesialis Bedah Mulut', 'Spesialis Bedah Mulut'),

    # --- Kategori Kompetensi & Sertifikasi Khusus ---
    ('Basic Life Support (BLS)', 'Basic Life Support (BLS)'),
    ('Advanced Cardiac Life Support (ACLS)', 'Advanced Cardiac Life Support (ACLS)'),
    ('Basic Trauma Life Support (BTLS)', 'Basic Trauma Life Support (BTLS)'),
    ('Advanced Trauma Life Support (ATLS)', 'Advanced Trauma Life Support (ATLS)'),
    ('Pelatihan Triase IGD', 'Pelatihan Triase IGD'),
    ('Sertifikasi Perawat ICU', 'Sertifikasi Perawat ICU'),
    ('Sertifikasi Perawat IGD', 'Sertifikasi Perawat IGD'),
    ('Sertifikasi Perawat Kamar Bedah', 'Sertifikasi Perawat Kamar Bedah'),
    ('Sertifikasi Perawat Hemodialisa', 'Sertifikasi Perawat Hemodialisa'),
    ('Sertifikasi Perawat Luka', 'Sertifikasi Perawat Luka'),
    ('Sertifikasi Phlebotomy', 'Sertifikasi Phlebotomy'),
    ('Sertifikasi EKG', 'Sertifikasi EKG'),
    ('Sertifikasi USG Dasar', 'Sertifikasi USG Dasar'),
    ('Pelatihan Resusitasi Neonatus', 'Pelatihan Resusitasi Neonatus'),
    ('Manajemen Nyeri', 'Manajemen Nyeri'),
    ('K3 Faskes', 'Kesehatan dan Keselamatan Kerja di Faskes'),
    ('Penanganan Bencana Medis', 'Penanganan Bencana Medis'),
    ('Pengendalian Infeksi (PPI)', 'Pengendalian Infeksi (PPI)'),
    ('Komunikasi Efektif', 'Komunikasi Efektif (untuk konseling pasien)'),
    ('Bahasa Inggris Medis', 'Keahlian Bahasa Inggris Medis'),
    ('Bahasa Mandarin Medis', 'Keahlian Bahasa Mandarin Medis'),

    # --- Kategori Manajemen / Administrasi ---
    ('Manajemen Faskes', 'Manajemen Faskes'),
    ('Quality Assurance Medis', 'Quality Assurance Medis'),
    ('Edukator Klinis', 'Edukator Klinis'),
]

# Ekstrak hanya nama kategori untuk matching
KATEGORI_LIST = [choice[0] for choice in KATEGORI_KUALIFIKASI_CHOICES]

def get_gemini_image_response(image_data, prompt_text: str, model_name: str = "gemini-1.5-flash"):
    """
    Mendapatkan respons dari model Gemini untuk analisis image.
    """
    if not (hasattr(settings, 'GOOGLE_API_KEY') and settings.GOOGLE_API_KEY):
        logger.error("Google API key (for Gemini) not configured.")
        return {"error": "AI service not configured.", "status_code": 503}

    try:
        model = genai.GenerativeModel(model_name)
        
        # Convert bytes to proper format for Gemini API
        # Option 1: Using dict format with mime_type and data
        image_blob = {
            "mime_type": "image/jpeg",
            "data": image_data
        }
        
        # Generate content dengan image dan text
        response = model.generate_content([prompt_text, image_blob])

        if response.parts:
            logger.debug(f"Gemini image response text: {response.text[:500]}...")
            return response.text
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason_message = response.prompt_feedback.block_reason_message or "Unknown block reason"
            logger.warning(f"Gemini request blocked. Reason: {response.prompt_feedback.block_reason} - {block_reason_message}")
            return {"error": f"Request blocked by AI. Reason: {block_reason_message}", "status_code": 403}
        else:
            candidate_info = "No parts or specific block reason found."
            if response.candidates:
                candidate_info = f"Finish reason: {response.candidates[0].finish_reason}. Safety ratings: {response.candidates[0].safety_ratings}"
            logger.warning(f"Gemini response did not contain any parts. Candidate info: {candidate_info}")
            return {"error": f"No content generated by AI. Details: {candidate_info}", "status_code": 500}

    except Exception as e:
        error_message = str(e)
        status_code = 500
        logger.error(f"Google Generative AI (Gemini) API error: {error_message}", exc_info=True)
        return {"error": f"Error communicating with AI service: {error_message}", "status_code": status_code}

def categorize_certificate(ai_response: str):
    """
    Mengkategorikan hasil AI response ke dalam kategori yang tersedia.
    """
    try:
        # Coba parse JSON jika AI response dalam format JSON
        if ai_response.strip().startswith('{'):
            parsed_response = json.loads(ai_response)
            detected_category = parsed_response.get('kategori', '')
        else:
            # Jika bukan JSON, ambil dari text biasa
            detected_category = ai_response.strip()
        
        # Cari kategori yang paling cocok
        close_matches = get_close_matches(
            detected_category, 
            KATEGORI_LIST, 
            n=3, 
            cutoff=0.6
        )
        
        if close_matches:
            return {
                'matched_category': close_matches[0],
                'confidence': 'high' if len(close_matches) == 1 else 'medium',
                'alternatives': close_matches[1:] if len(close_matches) > 1 else [],
                'original_text': detected_category
            }
        else:
            # Cari dengan kata kunci
            detected_lower = detected_category.lower()
            for category in KATEGORI_LIST:
                if any(word in detected_lower for word in category.lower().split()):
                    return {
                        'matched_category': category,
                        'confidence': 'low',
                        'alternatives': [],
                        'original_text': detected_category
                    }
        
        return {
            'matched_category': None,
            'confidence': 'none',
            'alternatives': [],
            'original_text': detected_category
        }
        
    except Exception as e:
        logger.error(f"Error in categorizing certificate: {e}")
        return {
            'matched_category': None,
            'confidence': 'error',
            'alternatives': [],
            'original_text': ai_response,
            'error': str(e)
        }

def upload_certificate_form(request):
    """
    View untuk menampilkan form upload sertifikat.
    """
    # Provide CSRF token to template
    csrf_token = get_token(request)
    return render(request, 'upload_form.html', {
        'categories': KATEGORI_KUALIFIKASI_CHOICES,
        'csrf_token': csrf_token
    })

@csrf_exempt  # Untuk testing, nanti bisa dihapus
def process_certificate_image(request):
    """
    View untuk memproses image sertifikat yang diupload.
    """
    # DEBUGGING: Log semua request info
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request content type: {request.content_type}")
    logger.info(f"Request files: {list(request.FILES.keys())}")
    logger.info(f"Request POST: {list(request.POST.keys())}")
    
    try:
        # Pastikan ini adalah POST request
        if request.method != 'POST':
            return JsonResponse({
                'error': f'Method {request.method} not allowed. Use POST.',
                'status': 'error'
            }, status=405)
        
        # Validasi file upload
        if 'certificate_image' not in request.FILES:
            return JsonResponse({
                'error': 'No image file provided',
                'status': 'error',
                'debug_info': {
                    'files_received': list(request.FILES.keys()),
                    'post_data': list(request.POST.keys())
                }
            }, status=400)
        
        image_file = request.FILES['certificate_image']
        
        # Validasi tipe file
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
        if image_file.content_type not in allowed_types:
            return JsonResponse({
                'error': f'Invalid file type: {image_file.content_type}. Please upload JPEG, PNG, or WebP image.',
                'status': 'error'
            }, status=400)
        
        # Validasi ukuran file (max 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'error': f'File too large: {image_file.size} bytes. Maximum size is 10MB.',
                'status': 'error'
            }, status=400)
        
        # Baca dan proses image
        try:
            image_data = image_file.read()
            image = Image.open(io.BytesIO(image_data))
            
            # Konversi ke RGB jika diperlukan
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize jika terlalu besar untuk menghemat API quota
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Konversi kembali ke bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=85)
            processed_image_data = img_byte_arr.getvalue()
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return JsonResponse({
                'error': f'Error processing image: {str(e)}',
                'status': 'error'
            }, status=400)
        
        # Check if Google API is configured
        if not (hasattr(settings, 'GOOGLE_API_KEY') and settings.GOOGLE_API_KEY):
            return JsonResponse({
                'error': 'Google AI API not configured. Please set GOOGLE_API_KEY in settings.',
                'status': 'error'
            }, status=503)
        
        # Prompt untuk AI
        prompt = f"""
Analisis gambar sertifikat ini dan identifikasi jenis sertifikat/kualifikasi medis apa yang tertera.

Fokus pada:
1. Jenis profesi atau spesialisasi medis
2. Nama sertifikasi atau pelatihan
3. Institusi yang mengeluarkan

Berdasarkan kategori berikut yang tersedia:
{', '.join(KATEGORI_LIST[:20])}... (dan {len(KATEGORI_LIST)-20} kategori lainnya)

Berikan respons dalam format JSON:
{{
    "kategori": "nama kategori yang paling sesuai",
    "confidence": "tinggi/sedang/rendah",
    "detail_teks": "teks yang terdeteksi dari sertifikat",
    "alasan": "penjelasan kenapa kategori ini dipilih"
}}

Jika tidak ada yang cocok persis, pilih yang paling mendekati.
        """
        
        # Panggil Gemini API
        ai_response = get_gemini_image_response(processed_image_data, prompt)
        
        # Handle error response dari AI
        if isinstance(ai_response, dict) and 'error' in ai_response:
            return JsonResponse({
                'error': ai_response['error'],
                'status': 'error'
            }, status=ai_response.get('status_code', 500))
        
        # Kategorikan hasil
        categorization = categorize_certificate(ai_response)
        
        # Return successful response
        return JsonResponse({
            'status': 'success',
            'ai_response': ai_response,
            'categorization': categorization,
            'available_categories': KATEGORI_LIST[:10],  # Limit untuk menghindari response terlalu besar
            'debug_info': {
                'image_size': f"{image.size[0]}x{image.size[1]}",
                'file_size': image_file.size,
                'content_type': image_file.content_type
            }
        })
        
    except Exception as e:
        # Log full traceback untuk debugging
        error_traceback = traceback.format_exc()
        logger.error(f"Unexpected error in process_certificate_image: {e}")
        logger.error(f"Full traceback: {error_traceback}")
        
        return JsonResponse({
            'error': f'Internal server error: {str(e)}',
            'status': 'error',
            'debug_info': {
                'traceback': error_traceback if settings.DEBUG else 'Check server logs'
            }
        }, status=500)

@require_http_methods(["GET"])
def get_categories(request):
    """
    API endpoint untuk mendapatkan daftar kategori yang tersedia.
    """
    try:
        return JsonResponse({
            'categories': KATEGORI_KUALIFIKASI_CHOICES,
            'category_list': KATEGORI_LIST,
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error in get_categories: {e}")
        return JsonResponse({
            'error': f'Error retrieving categories: {str(e)}',
            'status': 'error'
        }, status=500)

def certificate_results(request):
    """
    View untuk menampilkan hasil analisis sertifikat.
    """
    # Ambil data dari session atau parameter
    result_data = request.session.get('certificate_result', {})
    
    return render(request, 'results.html', {
        'result': result_data,
        'categories': KATEGORI_KUALIFIKASI_CHOICES
    })

# Tambahkan fungsi ini ke dalam management_ai_services.py

# Tambahkan fungsi ini ke dalam management_ai_services.py

def get_gemini_summary(comments_data, nakes_name):
    """
    Menggenerate rangkuman komentar performance menggunakan Gemini AI dengan format HTML yang bagus.
    """
    if not (hasattr(settings, 'GOOGLE_API_KEY') and settings.GOOGLE_API_KEY):
        logger.error("Google API key (for Gemini) not configured.")
        return None

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Format komentar untuk prompt
        comments_text = ""
        for i, comment in enumerate(comments_data, 1):
            comments_text += f"""
{i}. Faskes: {comment['faskes']} - {comment['departemen']}
   Tanggal: {comment['tanggal']}
   Rating: {comment['rating']}/5 ⭐
   Komentar: "{comment['komentar']}"
   
"""
        
        # Prompt untuk AI dengan instruksi formatting yang jelas
        prompt = f"""
Buatlah rangkuman analisis performa untuk tenaga kesehatan atas nama "{nakes_name}" berdasarkan {len(comments_data)} komentar review berikut:

{comments_text}

PENTING: Berikan output dalam format HTML yang rapi dengan struktur berikut. Gunakan HTML tags untuk formatting yang baik:

<div class="ai-summary-content">
<div class="summary-section">
<h3><i class="fas fa-chart-bar"></i> Ringkasan Performa</h3>
<div class="summary-grid">
<div class="summary-item strength">
<h4><i class="fas fa-thumbs-up"></i> Poin Kuat</h4>
<ul>
[3-4 poin kekuatan utama dalam format list]
</ul>
</div>
<div class="summary-item improvement">
<h4><i class="fas fa-arrow-up"></i> Area Pengembangan</h4>
<ul>
[2-3 area yang perlu ditingkatkan dalam format list]
</ul>
</div>
</div>
</div>

<div class="summary-section">
<h3><i class="fas fa-lightbulb"></i> Insight Utama</h3>
<div class="insight-box">
[2-3 insight paling penting tentang performa dalam format paragraf singkat]
</div>
</div>

<div class="summary-section">
<h3><i class="fas fa-target"></i> Rekomendasi</h3>
<ol class="recommendation-list">
[3 saran konkret untuk meningkatkan performa dalam format numbered list]
</ol>
</div>

<div class="summary-section highlight">
<h3><i class="fas fa-star"></i> Highlight Pencapaian</h3>
<div class="highlight-box">
[1-2 pencapaian atau feedback terbaik yang menonjol]
</div>
</div>
</div>

JANGAN gunakan markdown (**, ##, dll). Gunakan HANYA HTML tags. Pastikan content singkat, padat, dan actionable. Fokus pada data faktual dari komentar yang ada.
        """
        
        # Generate content
        response = model.generate_content(prompt)
        
        if response.parts:
            logger.info(f"AI summary generated successfully for {nakes_name}")
            # Clean up response jika ada markdown yang tersisa
            cleaned_response = response.text.replace('**', '').replace('##', '')
            return cleaned_response
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
            logger.warning(f"Gemini request blocked for summary generation")
            return None
        else:
            logger.warning(f"Gemini response empty for summary generation")
            return None

    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return None