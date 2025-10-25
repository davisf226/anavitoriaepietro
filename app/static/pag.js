let pagamentoId = null;

function abrirModal(item, valor) {
  document.getElementById('presenteSelecionado').value = item;
  document.getElementById('valorSelecionado').value = valor;
  new bootstrap.Modal(document.getElementById('modalPagamento')).show();
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('formPagamento');
  const loader = document.getElementById('modalLoader');
  const modalPagamento = document.getElementById('modalPagamento');
  const modalComentario = document.getElementById('modalComentario');

  // ======= ENVIO DE PAGAMENTO =======
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const nome = document.getElementById('nome').value.trim();
    const email = document.getElementById('email').value.trim();
    const cpf = document.getElementById('cpf').value.trim();
    const presente = document.getElementById('presenteSelecionado').value;
    const valor = document.getElementById('valorSelecionado').value;

    if (!nome || !email || !cpf) return alert("Preencha todos os campos!");

    loader.style.display = 'block';

    try {
      const res = await fetch("/pagar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, cpf, email, valor: parseFloat(valor), presente })
      });

      const data = await res.json();

      if (res.ok && data.checkout_url && data.pagamento_id) {
        pagamentoId = data.pagamento_id;
        window.open(data.checkout_url, '_blank');
        loader.style.display = 'block';
      } else {
        loader.style.display = 'none';
        alert("Erro ao iniciar o pagamento.");
      }
    } catch (err) {
      console.error(err);
      loader.style.display = 'none';
      alert("Erro de conexão.");
    }
  });

  // ======= VERIFICAR PAGAMENTO MANUALMENTE =======
  document.getElementById('verificarPagamento').addEventListener('click', async () => {
    if (!pagamentoId) return alert("Nenhum pagamento em andamento.");

    try {
      const res = await fetch(`/pagamento-status/${pagamentoId}`);
      const data = await res.json();

      if (res.ok && data.status === "PAGO") {
        loader.style.display = 'none';
        bootstrap.Modal.getInstance(modalPagamento).hide();
        new bootstrap.Modal(modalComentario).show();
      } else {
        alert("Pagamento ainda não confirmado. Tente novamente em alguns segundos.");
      }
    } catch (err) {
      console.error(err);
      alert("Erro ao verificar status do pagamento.");
    }
  });

  // ======= FORMULÁRIO DE COMENTÁRIO =======
  const formComentario = document.getElementById('formComentario');
  formComentario.addEventListener('submit', async (e) => {
    e.preventDefault();

    const nome = document.getElementById('comentarioNome').value.trim();
    const texto = document.getElementById('comentarioTexto').value.trim();

    if (!nome || !texto) return alert("Escreva seu comentário!");
    if (!pagamentoId) return alert("O pagamento precisa ser concluído antes de comentar.");

    try {
      const res = await fetch("/comentarios", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ convidado_nome: nome, convidado_comentario: texto, pagamento_id: pagamentoId })
      });

      const data = await res.json();
      if (res.ok) {
        alert("Comentário enviado com sucesso!");
        location.reload();
      } else {
        alert(data.error || "Erro ao enviar comentário.");
      }
    } catch (err) {
      console.error(err);
      alert("Erro ao enviar comentário.");
    }
  });

  // ======= CARREGAR COMENTÁRIOS =======
  fetch("/comentarios")
    .then(r => r.json())
    .then(data => {
      const comentarios = Array.isArray(data) ? data : data.comentarios || [];
      const container = document.getElementById("comentariosContainer");
      container.innerHTML = "";

      if (comentarios.length === 0) {
        container.innerHTML = "<p class='text-muted'>Nenhum comentário ainda.</p>";
        return;
      }

      comentarios.forEach(c => {
        const div = document.createElement("div");
        div.classList.add("mb-3", "p-3", "bg-white", "rounded", "shadow-sm");
        div.innerHTML = `<p><strong>${c.convidado_nome}</strong> disse:</p><p>${c.convidado_comentario}</p>`;
        container.appendChild(div);
      });
    })
    .catch(err => {
      console.error("Erro ao carregar comentários:", err);
      document.getElementById("comentariosContainer").innerHTML =
        "<p class='text-danger'>Erro ao carregar comentários.</p>";
    });
});
