/* AgroPedidos - comportamento das telas (JavaScript puro, sem bibliotecas) */
(function () {
  // Fecha mensagens
  document.addEventListener("click", function (e) {
    if (e.target.classList.contains("fechar")) e.target.parentElement.remove();
  });

  // Confirmação antes de ações importantes (inativar, cancelar, entregar)
  document.querySelectorAll("form[data-confirmar]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.dataset.confirmar)) e.preventDefault();
    });
  });

  // Máscara de CPF/CNPJ conforme o tipo de pessoa
  var tipo = document.getElementById("tipo_pessoa");
  var doc = document.querySelector("[data-mascara-doc]");
  function mascararDoc() {
    if (!doc) return;
    var d = doc.value.replace(/\D/g, "");
    var pj = tipo && tipo.value === "J";
    d = d.slice(0, pj ? 14 : 11);
    if (pj) {
      d = d.replace(/^(\d{2})(\d)/, "$1.$2").replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
           .replace(/\.(\d{3})(\d)/, ".$1/$2").replace(/(\d{4})(\d)/, "$1-$2");
    } else {
      d = d.replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d{1,2})$/, "$1-$2");
    }
    doc.value = d;
    var rotulo = document.getElementById("rotulo_doc");
    if (rotulo) rotulo.textContent = pj ? "CNPJ" : "CPF";
  }
  if (doc) { doc.addEventListener("input", mascararDoc); mascararDoc(); }
  if (tipo) tipo.addEventListener("change", function () { doc.value = ""; mascararDoc(); doc.focus(); });

  // Máscara de telefone
  document.querySelectorAll("[data-mascara-telefone]").forEach(function (campo) {
    campo.addEventListener("input", function () {
      var d = campo.value.replace(/\D/g, "").slice(0, 11);
      campo.value = d.length > 10 ? d.replace(/^(\d{2})(\d{5})(\d{0,4})/, "($1) $2-$3")
                                  : d.replace(/^(\d{2})(\d{4})(\d{0,4})/, "($1) $2-$3").replace(/^(\d{0,2})$/, "$1");
    });
  });
})();

function formatarMoeda(valor) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

/* Tela de pedido: adicionar/remover itens e calcular o total em tempo real */
function iniciarFormularioPedido(catalogo) {
  var corpo = document.getElementById("linhas-itens");
  var modelo = corpo.querySelector(".linha-item").cloneNode(true);

  function lerNumero(texto) {
    texto = (texto || "").trim();
    if (texto.indexOf(",") >= 0) texto = texto.replace(/\./g, "").replace(",", ".");
    var n = parseFloat(texto);
    return isNaN(n) ? 0 : n;
  }

  function recalcular() {
    var total = 0;
    corpo.querySelectorAll(".linha-item").forEach(function (linha) {
      var prod = catalogo[linha.querySelector(".produto").value];
      var qtd = lerNumero(linha.querySelector(".quantidade").value);
      var sub = prod ? prod.preco * qtd : 0;
      linha.querySelector(".unidade").textContent = prod ? prod.unidade : "—";
      linha.querySelector(".preco").textContent = prod ? formatarMoeda(prod.preco) : "—";
      linha.querySelector(".subtotal").textContent = prod ? formatarMoeda(sub) : "—";
      total += sub;
    });
    document.getElementById("total").textContent = formatarMoeda(total);
  }

  document.getElementById("adicionar-item").addEventListener("click", function () {
    var nova = modelo.cloneNode(true);
    nova.querySelector(".produto").value = "";
    nova.querySelector(".quantidade").value = "";
    corpo.appendChild(nova);
    nova.querySelector(".produto").focus();
    recalcular();
  });

  corpo.addEventListener("click", function (e) {
    if (!e.target.classList.contains("remover")) return;
    var linhas = corpo.querySelectorAll(".linha-item");
    if (linhas.length > 1) e.target.closest(".linha-item").remove();
    else { linhas[0].querySelector(".produto").value = ""; linhas[0].querySelector(".quantidade").value = ""; }
    recalcular();
  });
  corpo.addEventListener("input", recalcular);
  corpo.addEventListener("change", recalcular);

  // Sugere previsão de entrega (+7 dias) se estiver vazia
  var dataPedido = document.getElementById("data_pedido");
  var prevista = document.getElementById("data_prevista");
  if (!prevista.value && dataPedido.value) {
    var d = new Date(dataPedido.value + "T00:00:00");
    d.setDate(d.getDate() + 7);
    prevista.value = d.toISOString().slice(0, 10);
  }
  prevista.min = dataPedido.value;
  dataPedido.addEventListener("change", function () { prevista.min = dataPedido.value; });

  recalcular();
}
