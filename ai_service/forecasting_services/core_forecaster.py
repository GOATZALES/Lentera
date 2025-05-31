from ..client import get_langchain_gemini_llm # Menggunakan LLM dari Langchain
from .tools import FaskesDataProviderTool, ExternalDataProviderTool
from ..models import AiForecastRequestLog
from django.utils import timezone
import json
import logging
import re

from langchain.agents import AgentExecutor, create_react_agent
# Jika ingin menggunakan agen yang lebih baru atau berbeda, sesuaikan impornya
# Misalnya, untuk create_structured_chat_agent atau create_openai_tools_agent jika pakai OpenAI
from langchain_core.prompts import PromptTemplate # Bisa juga ChatPromptTemplate
# from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.messages import AIMessage, HumanMessage, SystemMessage # Untuk ChatPromptTemplate

logger = logging.getLogger(__name__)

DEFAULT_RATES_PER_SHIFT = {
    "Dokter Umum": {"min": 500000, "max": 1000000},
    "Dokter Spesialis": {"min": 750000, "max": 1500000},
    "Perawat": {"min": 250000, "max": 500000},
    "Bidan": {"min": 250000, "max": 450000},
    "Volunteer Medis (Supervised)": {"min": 100000, "max": 200000}
}

# Template prompt untuk ReAct Agent. Ini adalah bagian yang paling krusial dan perlu di-tune.
# Untuk model Gemini, format few-shot atau instruksi yang sangat jelas seringkali lebih baik.
# Pertimbangkan juga menggunakan ChatPromptTemplate jika LLM Anda lebih cocok dengan format chat.
REACT_PROMPT_TEMPLATE = """
Anda adalah "Lentera AI Forecaster", seorang spesialis perencana kebutuhan tenaga medis di Indonesia.
Tugas Anda adalah menganalisis data yang tersedia untuk Fasilitas Kesehatan (Faskes) dan membuat prediksi kebutuhan staf untuk periode yang ditentukan.

ALAT YANG TERSEDIA:
Anda memiliki akses ke alat berikut:
{tools}

Untuk menggunakan alat, Anda HARUS menggunakan format berikut dalam satu blok teks tunggal:
Thought: [Pemikiran Anda di sini langkah demi langkah untuk memutuskan alat dan inputnya]
Action: [Nama alat dari daftar: {tool_names}]
Action Input: [Input untuk alat tersebut, berupa string atau JSON string jika alat mengharapkannya. Jika JSON string, pastikan valid. Contoh untuk get_external_weather_event_mudik_data: {{"city_name": "Nama Kota", "target_date_or_range": "YYYY-MM-DD"}}]]

Setelah Anda mendapatkan Observation dari alat, ulangi proses Thought/Action/Action Input jika perlu informasi lebih lanjut.

Ketika Anda yakin memiliki semua informasi yang diperlukan untuk membuat prediksi akhir, Anda HARUS merespons HANYA dengan "Final Answer:" diikuti oleh objek JSON yang valid pada baris berikutnya.
JANGAN menambahkan teks atau penjelasan tambahan sebelum "Final Answer:" atau sebelum dan sesudah blok JSON.

FORMAT JAWABAN AKHIR (JSON WAJIB SETELAH "Final Answer:"):
{{
  "faskes_id_processed": "ID Faskes yang dianalisis (Contoh: FKS001-JKTSEL)",
  "forecasting_period": "Periode forecast (Contoh: 2024-07-01 hingga 2024-07-07)",
  "predicted_staffing_demand": {{
    "Dokter Umum": "<integer>",
    "Perawat": "<integer>",
    "Bidan": "<integer_atau_0_jika_tidak_relevan>",
    "Dokter Spesialis Anak": "<integer_atau_0_jika_tidak_relevan>",
    "Dokter Spesialis Penyakit Dalam": "<integer_atau_0_jika_tidak_relevan>",
    "Volunteer Medis": "<integer_atau_0_jika_tidak_relevan>"
  }},
  "estimated_cost_range_rp": {{
    "min_cost": "<float>",
    "max_cost": "<float>",
    "currency": "IDR",
    "notes": "Estimasi berdasarkan tarif {rates_info_str_for_json_notes} dan asumsi 1 shift/hari/nakes."
  }},
  "peak_period_alerts_and_recommendations": "<String analisis mengenai potensi periode puncak, risiko, dan rekomendasi singkat. Jika tidak ada, tulis 'Tidak ada periode puncak signifikan yang teridentifikasi dari data yang tersedia.'>"
}}

INFORMASI TARIF (untuk perhitungan estimasi biaya):
{rates_info_str_for_prompt}

PERMINTAAN SAAT INI:
Buat prediksi kebutuhan staf untuk Faskes dengan ID: {faskes_id}.
Periode peramalan: {period_start} hingga {period_end}.
Informasi awal yang diberikan (gunakan sebagai konteks, verifikasi atau cari detail lebih lanjut dengan alat jika perlu):
- Ringkasan Data Historis Awal: {historical_summary}
- Pola Penyakit Musiman Awal: {seasonal_patterns}

CONTOH INTERAKSI SINGKAT (Anda mungkin perlu lebih banyak langkah Thought/Action/Observation):
Question: {input}
Thought: Saya perlu mendapatkan data detail untuk Faskes ID {faskes_id}. Saya akan menggunakan alat `get_faskes_partner_data`.
Action: get_faskes_partner_data
Action Input: {faskes_id}
Observation: [Di sini sistem akan mengisi hasil dari get_faskes_partner_data, misalnya: {{"faskes_id": "{faskes_id}", "nama_faskes": "Nama Faskes Contoh", "kota_kabupaten": "Kota Contoh", ...}}]
Thought: Sekarang saya punya data Faskes. Saya perlu data eksternal untuk 'Kota Contoh' pada periode {period_start} hingga {period_end}. Saya akan menggunakan `get_external_weather_event_mudik_data`.
Action: get_external_weather_event_mudik_data
Action Input: {{"city_name": "Kota Contoh", "target_date_or_range": "{period_start} hingga {period_end}"}}
Observation: [Di sini sistem akan mengisi hasil dari get_external_weather_event_mudik_data, misalnya: {{"weather_forecast": "Cerah", "local_events": "Tidak ada", ...}}]
Thought: Saya sekarang memiliki semua informasi yang dibutuhkan dari data Faskes dan data eksternal untuk membuat prediksi akhir. Saya akan menyusun jawaban dalam format JSON yang diminta.
Final Answer:
{{
  "faskes_id_processed": "{faskes_id}",
  "forecasting_period": "{period_start} hingga {period_end}",
  "predicted_staffing_demand": {{ ...data prediksi... }},
  "estimated_cost_range_rp": {{ ...data biaya... }},
  "peak_period_alerts_and_recommendations": "Analisis periode puncak..."
}}

INGAT: Patuhi format dengan ketat, terutama untuk `Thought:`, `Action:`, `Action Input:`, dan format `Final Answer:` yang hanya berisi JSON.
JANGAN ada ```json di sekitar Final Answer. Final Answer HANYA berisi objek JSON.

Mulai!

Question: {input}
Thought:{agent_scratchpad}
"""

def generate_staffing_demand_forecast_with_langchain(
    caller_ref_id: str,
    input_data_for_initial_prompt: dict,
    input_payload_for_log: dict,
    ai_model_name: str = "gemini-1.5-flash-latest"
    ) -> tuple[dict | None, str | None, int | None]:

    log_entry = AiForecastRequestLog.objects.create(
        caller_reference_id=caller_ref_id,
        service_type="staffing_demand_forecast_langchain",
        input_payload_json=input_payload_for_log,
        ai_model_name_used=ai_model_name,
        processing_status="processing",
        requested_at=timezone.now()
    )

    try:
        llm = get_langchain_gemini_llm(model_name=ai_model_name, temperature=0.3) # Suhu lebih rendah
        tools = [FaskesDataProviderTool(), ExternalDataProviderTool()] # Instance dari tools

        rates_prompt_str = "\n".join([f"- {role}: Rp {rate['min']:,} - Rp {rate['max']:,}" for role, rate in DEFAULT_RATES_PER_SHIFT.items()])
        rates_json_notes_str = ", ".join([f"{role} ({rate['min']}-{rate['max']})" for role, rate in DEFAULT_RATES_PER_SHIFT.items()])


        # Membuat prompt dengan PromptTemplate
        prompt_for_agent = PromptTemplate.from_template(REACT_PROMPT_TEMPLATE)
        
        # Inisialisasi agen ReAct
        # Untuk create_react_agent, prompt harus memiliki variabel input 'input', 'tools', 'tool_names', dan 'agent_scratchpad'
        # Kita akan memformat prompt agar sesuai.
        agent = create_react_agent(llm, tools, prompt_for_agent)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True, # Sangat berguna saat debugging
            handle_parsing_errors="Mohon berikan jawaban dalam format JSON yang benar atau gunakan tool lagi jika perlu.", # Custom message
            max_iterations=10 # Batasi iterasi
        )
        
        # Input awal untuk agent. "input" adalah key standar yang diharapkan.
        # Variabel lain (faskes_id, dll.) akan di-passing untuk memformat template prompt.
        initial_agent_query = (
            f"Buat prediksi kebutuhan staf untuk Faskes ID: {caller_ref_id} "
            f"untuk periode {input_data_for_initial_prompt['period_start']} "
            f"hingga {input_data_for_initial_prompt['period_end']}."
        )

        agent_inputs = {
            "input": initial_agent_query,
            "faskes_id": caller_ref_id,
            "period_start": input_data_for_initial_prompt['period_start'],
            "period_end": input_data_for_initial_prompt['period_end'],
            "historical_summary": input_data_for_initial_prompt['historical_summary'],
            "seasonal_patterns": input_data_for_initial_prompt['seasonal_patterns'],
            "rates_info_str_for_prompt": rates_prompt_str,
            "rates_info_str_for_json_notes": rates_json_notes_str,
            # agent_scratchpad, tools, tool_names akan diisi otomatis oleh AgentExecutor
        }

        logger.info(f"Invoking Langchain ReAct agent for Faskes ID: {caller_ref_id}")
        
        # Jalankan agent executor
        response_dict = agent_executor.invoke(agent_inputs)
        agent_final_output_str = response_dict.get("output", "")

        log_entry.raw_ai_response_text = agent_final_output_str 

        try:
            clean_output = agent_final_output_str.strip()
            if clean_output.startswith("```json"):
                # Lebih aman menggunakan find dan slicing jika ```json selalu ada
                start_index = clean_output.find("```json") + len("```json")
                end_index = clean_output.rfind("```")
                if start_index != -1 and end_index != -1 and end_index > start_index:
                    clean_output = clean_output[start_index:end_index].strip()
                else: # Jika format ```json tidak standar, coba cara lain
                    clean_output = clean_output.replace("```json", "").replace("```", "").strip()
            elif clean_output.startswith("{") and clean_output.endswith("}"):
                pass # Sudah terlihat seperti JSON
            else:
                # Menggunakan modul 're' yang sudah diimpor
                match = re.search(r'\{.*\}', clean_output, re.DOTALL) # <--- UBAH BARIS INI
                if match:
                    clean_output = match.group(0)
                else:
                    raise json.JSONDecodeError("Tidak ada blok JSON yang valid ditemukan dalam output agen.", clean_output, 0)

            parsed_json_result = json.loads(clean_output)
            log_entry.parsed_ai_output_json = parsed_json_result
            log_entry.processing_status = "completed"
            logger.info(f"Langchain agent successfully processed forecast for {caller_ref_id}, Log ID: {log_entry.id}")
            return parsed_json_result, None, log_entry.id
        except json.JSONDecodeError as e:
            err_msg = f"Gagal mem-parse Final Answer JSON dari Langchain agent: {e}. Output Agen: {agent_final_output_str[:500]}"
            log_entry.processing_status = "failed"
            log_entry.error_message = err_msg
            logger.error(err_msg, exc_info=False) # exc_info=False karena output agen bisa panjang
            return None, err_msg, log_entry.id
        finally:
            log_entry.completed_at = timezone.now()
            log_entry.save()

    except Exception as e:
        err_msg = f"Error selama eksekusi Langchain agent untuk {caller_ref_id}: {str(e)}"
        log_entry.processing_status = "failed"
        log_entry.error_message = err_msg
        log_entry.completed_at = timezone.now()
        log_entry.save()
        logger.error(err_msg, exc_info=True)
        return None, err_msg, log_entry.id