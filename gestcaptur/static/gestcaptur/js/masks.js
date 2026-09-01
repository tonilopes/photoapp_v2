
// 🔧 JavaScript para Máscaras
// gestcaptur/static/gestcaptur/js/masks.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎭 Máscaras carregadas');

    // 🔧 MÁSCARA DE CPF
    document.querySelectorAll('.cpf-mask').forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
            e.target.value = value;
        });
    });

    // 🔧 MÁSCARA DE CEP
    document.querySelectorAll('.cep-mask').forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/(\d{5})(\d)/, '$1-$2');
            e.target.value = value;
        });
    });

    // 🔧 MÁSCARA DE TELEFONE FIXO
    document.querySelectorAll('.telefone-fixo-mask').forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/(\d{2})(\d)/, '($1) $2');
            value = value.replace(/(\d{4})(\d)/, '$1-$2');
            e.target.value = value;
        });
    });

    // 🔧 MÁSCARA DE WHATSAPP (CELULAR)
    document.querySelectorAll('.whatsapp-mask').forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/(\d{2})(\d)/, '($1) $2');
            value = value.replace(/(\d{5})(\d)/, '$1-$2');
            e.target.value = value;
        });
    });

    // 🔧 BUSCAR CEP AUTOMATICAMENTE
    document.querySelectorAll('.cep-mask').forEach(function(input) {
        input.addEventListener('blur', function(e) {
            const cep = e.target.value.replace(/\D/g, '');
            if (cep.length === 8) {
                buscarCEP(cep);
            }
        });
    });

    // Função para buscar CEP
    function buscarCEP(cep) {
        fetch(`https://viacep.com.br/ws/${cep}/json/`)
            .then(response => response.json())
            .then(data => {
                if (!data.erro) {
                    // Preencher campos automaticamente
                    const endereco = document.querySelector('input[name="endereco"]');
                    const bairro = document.querySelector('input[name="bairro"]');
                    const cidade = document.querySelector('input[name="cidade"]');
                    const estado = document.querySelector('select[name="estado"]');

                    if (endereco && data.logradouro) endereco.value = data.logradouro;
                    if (bairro && data.bairro) bairro.value = data.bairro;
                    if (cidade && data.localidade) cidade.value = data.localidade;
                    if (estado && data.uf) estado.value = data.uf;
                }
            })
            .catch(error => {
                console.log('Erro ao buscar CEP:', error);
            });
    }
});