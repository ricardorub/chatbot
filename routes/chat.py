from flask import Blueprint, render_template, session, redirect, request, jsonify
import requests
import os
import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime
import pdfplumber

# ========================
# MODELOS Y DB (Mock si no existen)
# ========================
try:
    from model.models import ChatSession, ChatMessage, User
    from model.db import db
except ImportError:
    class MockModel:
        def _init_(self, **kwargs): pass
    ChatSession = ChatMessage = User = MockModel
    db = type('MockDB', (), {
        'session': type('MockSession', (), {
            'add': lambda x: None,
            'commit': lambda: None,
            'query': lambda x: type('MockQuery', (), {
                'filter_by': lambda **kw: type('MockFilter', (), {
                    'first': lambda: None,
                    'all': lambda: [],
                    'order_by': lambda x: type('MockOrder', (), {'all': lambda: []})()
                })()
            })()
        })()
    })()


# ========================
# PDF PROCESSOR OPTIMIZADO PARA tesis1234.pdf
# ========================
class PDFProcessor:
    def __init__(self, pdf_path, index_path="./faiss_index", metadata_path="./faiss_metadata.npy"):
        self.pdf_path = pdf_path
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        self.chunks_with_metadata = []
        self.index = None
        self.embeddings = None

        self._reset_index_files()
        print("🆕 Regenerando índice. Procesando PDF...")
        self._load_and_index_pdf()

    def _reset_index_files(self):
        for path in [self.index_path, self.metadata_path]:
            if os.path.exists(path):
                os.remove(path)
                print(f"🗑️ Eliminado: {path}")

    def _load_and_index_pdf(self):
        print(f"📄 Cargando: {self.pdf_path}")
        try:
            full_text = ""
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

            if not full_text.strip():
                raise ValueError("PDF vacío o sin texto.")

            # Extraer los 20 puntos con regex robusta
            pattern = r'(\d+)\.\s*(.*?)(?=\n\d+\.\s|\Z)'
            matches = re.findall(pattern, full_text, re.DOTALL)

            punto_a_componente = {
                '1': 'Alcance del Proyecto',
                '2': 'Esquema',
                '3': 'Introducción',
                '4': 'Metodología',
                '5': 'Tipo, enfoque y diseño de investigación',
                '6': 'Variables o categorías',
                '7': 'Unidad de análisis',
                '8': 'Técnicas e instrumentos de recolección de datos',
                '9': 'Métodos para el análisis de datos',
                '10': 'Aspectos éticos',
                '11': 'Resultados',
                '12': 'Diseño de la estructura de Software',
                '13': 'Diagrama de Componentes',
                '14': 'Diagrama de Despliegue',
                '15': 'Desarrollo de Mockups',
                '16': 'Prototipos de Aplicación',
                '17': 'Discusión',
                '18': 'Conclusiones',
                '19': 'Recomendaciones',
                '20': 'Referencias'
            }

            self.chunks_with_metadata = []
            for num, content in matches:
                punto_num = num.strip()
                chunk_text = re.sub(r'\s+', ' ', content.strip())
                if len(chunk_text) < 20:
                    continue

                componente = punto_a_componente.get(punto_num, 'General')
                formatted_text = f"Punto {punto_num}. {chunk_text}"

                self.chunks_with_metadata.append({
                    'text': formatted_text,
                    'metadata': {
                        'source': os.path.basename(self.pdf_path),
                        'componente': componente,
                        'punto': punto_num
                    }
                })

            print(f"✅ Extraídos {len(self.chunks_with_metadata)} puntos.")

            texts = [item['text'] for item in self.chunks_with_metadata]
            self.embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            faiss.normalize_L2(self.embeddings)
            self.index.add(self.embeddings)

            faiss.write_index(self.index, self.index_path)
            np.save(self.metadata_path, self.chunks_with_metadata, allow_pickle=True)
            print(f"✅ Índice guardado en: {self.index_path}")

        except Exception as e:
            print(f"❌ Error al procesar PDF: {e}")
            import traceback
            traceback.print_exc()

    def retrieve_relevant_chunks(self, query, k=3):
        if self.index is None or not self.chunks_with_metadata:
            return ["No se pudo cargar el PDF."]

        try:
            query_for_embedding = "Represent this sentence for searching relevant passages: " + query
            query_embedding = self.model.encode([query_for_embedding], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)

            distances, indices = self.index.search(query_embedding, k)
            results = []

            for i, idx in enumerate(indices[0]):
                if idx == -1:
                    continue
                item = self.chunks_with_metadata[idx]
                score = float((distances[0][i] + 1) / 2)
                meta = item['metadata']
                source_label = f"[{meta['componente']}] [Punto {meta['punto']}]"
                results.append({
                    'text': item['text'],
                    'score': score,
                    'source_label': source_label
                })

            results.sort(key=lambda x: x['score'], reverse=True)
            return [
                f"[Relevancia: {r['score']:.3f}] {r['source_label']}\n{r['text'][:600]}..."
                for r in results
            ]

        except Exception as e:
            print(f"⚠️ Error en búsqueda: {e}")
            return ["Error al buscar en el PDF."]


# Inicializar procesador
PDF_PROCESSOR = PDFProcessor("tesis1234.pdf")


# ========================
# BLUEPRINT
# ========================
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect('/')
    user = {'email': session.get('user_email')}
    chat_sessions = ChatSession.query.filter_by(user_id=session['user_id']).order_by(ChatSession.created_at.desc()).all()
    if not chat_sessions:
        new_session = ChatSession(user_id=session['user_id'], title='Nueva conversación')
        db.session.add(new_session)
        db.session.commit()
        chat_sessions = [new_session]
    current_session = chat_sessions[0]
    return render_template('chat2.html', user=user, chat_sessions=chat_sessions, current_session=current_session)


@chat_bp.route('/api/chat/load/<int:session_id>', methods=['GET'])
def load_chat(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=session['user_id']).first()
    if not chat_session:
        return jsonify({'error': 'Sesión no encontrada'}), 404
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()
    return jsonify({
        'messages': [{
            'id': msg.id,
            'message': msg.message,
            'is_user': msg.is_user,
            'created_at': msg.created_at.isoformat()
        } for msg in messages]
    }), 200


@chat_bp.route('/api/chat/send', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json()
    message = data.get('message')
    session_id = data.get('session_id')

    if not message:
        return jsonify({'error': 'El mensaje no puede estar vacío'}), 400

    if not session_id:
        new_session = ChatSession(
            user_id=session['user_id'],
            title=message[:50] + '...' if len(message) > 50 else message
        )
        db.session.add(new_session)
        db.session.commit()
        session_id = new_session.id

    new_message = ChatMessage(session_id=session_id, message=message, is_user=True)
    db.session.add(new_message)

    # 🔑 CONFIGURACIÓN DE OPENROUTER (COMPLETAR CON TUS DATOS)
    OPENROUTER_API_KEY = "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"  # ← ¡COMPLETAR!
    MODEL = "qwen/qwen3-30b-a3b:free"  # Puedes cambiarlo por: "anthropic/claude-3.5-sonnet", "google/gemini-pro", etc.

    bot_response = "Lo siento, ocurrió un error."
    source_label = "Error"

    if not OPENROUTER_API_KEY:
        bot_response = "Error: No se ha configurado la clave de API de OpenRouter."
    else:
        try:
            relevant_chunks = PDF_PROCESSOR.retrieve_relevant_chunks(message, k=3)
            context_pdf = "\n\n".join(relevant_chunks)

            # ✅ PROMPT OPTIMIZADO PARA tesis1234.pdf
            system_prompt = (
                "Eres 'Sofia', la asistente virtual de tesis. Tu rol es ayudar a estudiantes a entender y cumplir con los requisitos formales del informe de tesis, "
                "basándote EXCLUSIVAMENTE en la guía oficial de 20 puntos proporcionada.\n\n"
                
                "REGLAS ESENCIALES:\n"
                "1. *Cita siempre el PUNTO y el COMPONENTE* cuando respondas. Ejemplo: '[Referencias] [Punto 20]'.\n"
                "2. Si la pregunta se refiere a un punto específico, reproduce el texto exacto del punto y luego explícalo con claridad.\n"
                "3. *NO inventes información*. Si algo no está en los 20 puntos, di: 'Lo siento, eso no está especificado en la guía. Te recomiendo consultar con tu tutor.'\n"
                "4. Sé empática, alentadora y clara. Usa un tono de tutora amable.\n"
                "5. *Formato de respuesta*:\n"
                "   - Máximo 3-4 líneas por párrafo.\n"
                "   - Usa \\n\\n para separar ideas.\n"
                "   - Para listas, usa viñetas con guion (-).\n"
                "   - Nunca bloques de texto densos.\n\n"
                
                "=== GUÍA OFICIAL DE TESIS (20 PUNTOS) ===\n"
                f"{context_pdf}\n"
                "=== FIN DE LA GUÍA ===\n\n"
                
                "Recuerda: Tu conocimiento termina donde termina esta guía."
            )

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",  # ⚠️ Cambia en producción
                "X-Title": "Asistente de Tesis Sofia",
            }

            payload = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            bot_response = response.json()['choices'][0]['message']['content']

            # Post-procesamiento de formato
            bot_response = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', bot_response)
            bot_response = re.sub(r'\n{3,}', '\n\n', bot_response)
            bot_response = "\n".join(line.strip() for line in bot_response.splitlines()).strip()

            source_label = "PDF"
            print(f"✅ Respuesta generada usando OpenRouter + {MODEL}")

        except Exception as e:
            bot_response = f"Lo siento, hubo un error: {str(e)}"
            source_label = "Error"
            print(f"❌ Error en OpenRouter: {e}")

    bot_chat_message = ChatMessage(session_id=session_id, message=bot_response, is_user=False)
    db.session.add(bot_chat_message)
    db.session.commit()

    chat_session = ChatSession.query.get(session_id)

    return jsonify({
        'message': 'Mensaje enviado',
        'session_id': session_id,
        'session_title': chat_session.title,
        'source': source_label
    }), 200


@chat_bp.route('/api/chat/delete/<int:session_id>', methods=['DELETE'])
def delete_chat(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=session['user_id']).first()
    if not chat_session:
        return jsonify({'error': 'Sesión no encontrada'}), 404
    db.session.delete(chat_session)
    db.session.commit()
    return jsonify({'message': 'Sesión eliminada'}), 200


@chat_bp.route('/api/chat/sessions', methods=['GET'])
def get_sessions():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    chat_sessions = ChatSession.query.filter_by(user_id=session['user_id']).order_by(ChatSession.created_at.desc()).all()
    return jsonify({
        'sessions': [{
            'id': s.id,
            'title': s.title,
            'created_at': s.created_at.isoformat(),
            'updated_at': s.updated_at.isoformat()
        } for s in chat_sessions]
    }), 200


@chat_bp.route('/api/chat/switch/<int:session_id>', methods=['POST'])
def switch_chat(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=session['user_id']).first()
    if not chat_session:
        return jsonify({'error': 'Sesión no encontrada'}), 404
    return jsonify({
        'message': 'Sesión cambiada',
        'session': {'id': chat_session.id, 'title': chat_session.title}
    }), 200
