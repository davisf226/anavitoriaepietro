from flask import jsonify, request, render_template
from app import app, db
from app.models import Comentario, Pagamento, NotificacaoPagBank
import requests
import uuid
import os
from dotenv import load_dotenv
load_dotenv()
# --- Página inicial ---
@app.route('/')
def index():
    return render_template('index.html')


# --- Inicia pagamento ---
@app.route('/pagar', methods=['POST'])
def pagar():
    from traceback import format_exc
    from app.models import Pagamento

    try:
        data = request.json
        print("📦 Dados recebidos:", data)
        reference_id = str(uuid.uuid4())
        TOKEN = os.getenv('TOKEN')
        url_api = "https://sandbox.api.pagseguro.com/checkouts"

        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "items": [
                {
                    "reference_id": reference_id,
                    "name": data.get("presente", "produto"),
                    "quantity": 1,
                    "unit_amount": int(float(data["valor"]) * 100)
                }
            ],
            "redirect_urls": {
                "success": "https://anavitoriaepietro.onrender.com/sucesso",
                "cancel": "https://anavitoriaepietro.onrender.com/cancelado"
            },
            "customer": {
                "name": data["nome"],
                "email": data["email"],
                "tax_id": data.get("cpf", "")
            }
        }

        resp = requests.post(url_api, headers=headers, json=payload)
        print("Status:", resp.status_code)
        print("Resposta:", resp.text)
        resp.raise_for_status()

        resp_json = resp.json()

        link_checkout = next((link["href"] for link in resp_json.get("links", []) if link.get("rel") == "PAY"), None)
        if not link_checkout:
            return jsonify({"error": "Link de checkout não encontrado", "response": resp_json}), 500

        # 💾 Salva o pagamento no banco
        novo_pagamento = Pagamento(
        nome=data["nome"],
        email=data["email"],
        cpf=data["cpf"],
        presente=data.get("presente", "produto"),
        valor=float(data["valor"]),
        status="PENDENTE",
        id_pagbank=reference_id  # <-- Aqui, assumindo que id_pagbank é a coluna que guarda esse código
    )
        db.session.add(novo_pagamento)
        db.session.flush()
        db.session.commit()

        print("✅ Link encontrado:", link_checkout,"======================================", novo_pagamento.id)
        return jsonify({
            "checkout_url": link_checkout,
            "pagamento_id": novo_pagamento.id
        }), 200

    except Exception:
        print("🔥 ERRO INTERNO EM /pagar:")
        print(format_exc())
        return jsonify({"error": "Erro interno no servidor"}), 500


# --- Verifica o status do pagamento ---
@app.route('/pagamento-status/<int:id_pagamento>', methods=['GET'])
def verificar_status_pagamento(id_pagamento):
    try:
        # Busca o pagamento pelo ID
        pagamento = Pagamento.query.filter_by(id = id_pagamento).first()


        if not pagamento:
            return jsonify({"error": "Pagamento não encontrado"}), 404

        # Caso o pagamento tenha sido confirmado como 'PAGO'
        if pagamento.status == "PAID":
            return jsonify({
                "status": "PAGO",
                "valor": pagamento.valor,
                "nome": pagamento.nome
            }), 200
        
        # Se o pagamento ainda estiver pendente
        return jsonify({
            "id": pagamento.id_pagbank,
            "status": "PENDENTE",
            "valor": pagamento.valor,
            "nome": pagamento.nome
        }), 200

    except Exception as e:
        print("🔥 ERRO INTERNO EM /pagamento-status:", e)
        return jsonify({"error": "Erro ao verificar status do pagamento"}), 500
    

# --- Página de sucesso (após redirecionamento) ---
@app.route('/sucesso', methods=['GET'])
def sucesso():
    return '<h1>Pagamento Ok.</h1>'


# --- Página de cancelamento ---
@app.route('/cancelado', methods=['GET'])
def cancelado():
    return "<h1>Pagamento cancelado.</h1>"

# --- Recebe notificação do PagBank ---
@app.route('/notificacaopagbank', methods=['POST'])
def notificacao_pagbank():
    try:
        # Captura corpo e cabeçalhos
        payload = request.get_json(silent=True)
        if not payload:
            payload = request.data.decode('utf-8')

        headers = dict(request.headers)

        # 🔹 Salva a notificação completa (auditoria)
        notificacao = NotificacaoPagBank(payload=payload, headers=headers)
        db.session.add(notificacao)
        db.session.commit()

        # --- Extrai o reference_id ---
        uuid_retorno = None
        try:
            # Normalmente vem dentro de payload["items"][0]["reference_id"]
            items = payload.get("items", [])
            if items and isinstance(items, list):
                uuid_retorno = items[0].get("reference_id")
        except Exception as e:
            print("⚠️ Erro ao extrair reference_id:", e)

        # --- Se tiver um reference_id, atualiza o pagamento correspondente ---
        if uuid_retorno:
            pagamento = Pagamento.query.filter_by(id_pagbank=uuid_retorno).first()

            if pagamento:
                # Atualiza status se vier no JSON (ex: PAID, CANCELED etc.)
                novo_status = payload.get("charges", [{}])[0].get("status", "pendente")
                pagamento.status = novo_status
                db.session.commit()
                print(f"✅ Pagamento {uuid_retorno} atualizado para status: {novo_status}")
            else:
                print(f"⚠️ Nenhum pagamento encontrado com id_pagbank={uuid_retorno}")

        return jsonify({
            "message": "Notificação registrada com sucesso",
            "uuid": uuid_retorno
        }), 200

    except Exception as e:
        print("❌ Erro ao processar notificação:", e)
        return jsonify({"error": str(e)}), 200  # ainda responde 200 pra não bloquear o reenvio

# --- Lista todos os comentários ---
@app.route("/comentarios", methods=["GET"])
def get_comentarios():
    comentarios = Comentario.query.order_by(Comentario.data_criacao.desc()).all()
    return jsonify([{
        "id": c.id,
        "convidado_nome": c.convidado_nome,
        "convidado_comentario": c.convidado_comentario,
        "data_criacao": c.data_criacao.strftime("%d/%m/%Y %H:%M")
    } for c in comentarios])


# --- Adiciona comentário manual ---
@app.route("/comentarios", methods=["POST"])
def criar_comentario():
    data = request.json
    pagamento_id = data.get("pagamento_id")
    nome = data.get("convidado_nome")
    texto = data.get("convidado_comentario")

    # Busca o pagamento
    pagamento = Pagamento.query.filter_by(id = pagamento_id).first()

    if not pagamento:
        return jsonify({"erro": "Pagamento não encontrado"}), 404

    # Verifica se o pagamento foi concluído
    if pagamento.status != "PAID":
        return jsonify({"erro": "O pagamento ainda não foi concluído"}), 403

    # Cria o comentário
    comentario = Comentario(
        convidado_nome=nome,
        convidado_comentario=texto,
        pagamento_id=pagamento_id
    )
    db.session.add(comentario)
    db.session.commit()

    return jsonify({"mensagem": "Comentário enviado com sucesso!"}), 201
