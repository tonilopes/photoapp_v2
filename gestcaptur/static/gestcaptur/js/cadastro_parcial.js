// gestcaptur/static/gestcaptur/js/cadastro_parcial.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('📧 Script cadastro parcial carregado');

    // Função para pegar CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // 📧 BOTÃO "FAZER DEPOIS"
    const btnFazerDepois = document.getElementById('btn-fazer-depois');
    if (btnFazerDepois) {
        btnFazerDepois.addEventListener('click', function() {
            console.log('🔄 Processando cadastro parcial...');
            
            // Desabilitar botão e mostrar loading
            btnFazerDepois.disabled = true;
            btnFazerDepois.classList.add('btn-loading');
            btnFazerDepois.innerHTML = '<i class="bi bi-hourglass-split"></i> Enviando...';
            
            // Coletar dados do formulário
            const formData = coletarDadosFormulario();
            
            // Verificar se tem email
            if (!formData.email || !formData.email.includes('@')) {
                mostrarErro('Email válido é obrigatório para salvar cadastro parcial.');
                restaurarBotao();
                return;
            }
            
            // Enviar requisição AJAX
            fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    acao: 'salvar_parcial',
                    form_data: formData
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('📨 Resposta do servidor:', data);
                
                if (data.status === 'success') {
                    // Fechar modal atual
                    const modalParcial = bootstrap.Modal.getInstance(document.getElementById('modalCadastroparcial'));
                    modalParcial.hide();
                    
                    // Mostrar modal de confirmação
                    setTimeout(() => {
                        const modalEmail = new bootstrap.Modal(document.getElementById('modalEmailEnviado'));
                        modalEmail.show();
                    }, 300);
                    
                } else if (data.status === 'warning') {
                    mostrarAviso(data.message);
                    setTimeout(() => {
                        window.location.reload();
                    }, 3000);
                    
                } else {
                    mostrarErro(data.message || 'Erro ao salvar dados.');
                    restaurarBotao();
                }
            })
            .catch(error => {
                console.error('❌ Erro na requisição:', error);
                mostrarErro('Erro de conexão. Tente novamente.');
                restaurarBotao();
            });
        });
    }

    // 📋 COLETAR DADOS DO FORMULÁRIO
    function coletarDadosFormulario() {
        const form = document.getElementById('cadastro-form');
        const formData = {};
        
        // Coletar todos os campos do formulário
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.name && input.name !== 'csrfmiddlewaretoken') {
                formData[input.name] = input.value || '';
            }
        });
        
        console.log('📋 Dados coletados:', formData);
        return formData;
    }

    // 🔄 RESTAURAR BOTÃO
    function restaurarBotao() {
        if (btnFazerDepois) {
            btnFazerDepois.disabled = false;
            btnFazerDepois.classList.remove('btn-loading');
            btnFazerDepois.innerHTML = '<i class="bi bi-envelope"></i> Fazer Depois';
        }
    }

    // ⚠️ MOSTRAR ERRO
    function mostrarErro(mensagem) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const modalBody = document.querySelector('#modalCadastroparcial .modal-body');
        modalBody.insertBefore(alertDiv, modalBody.firstChild);
        
        // Remover após 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // ⚠️ MOSTRAR AVISO
    function mostrarAviso(mensagem) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-warning alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const modalBody = document.querySelector('#modalCadastroparcial .modal-body');
        modalBody.insertBefore(alertDiv, modalBody.firstChild);
    }

    // 🎯 MÁSCARAS DOS CAMPOS (reutilizar do script existente)
    aplicarMascaras();

    function aplicarMascaras() {
        // CPF
        const cpfInput = document.querySelector('input[name="cpf"]');
        if (cpfInput) {
            cpfInput.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
                e.target.value = value;
            });
        }

        // CEP
        const cepInput = document.querySelector('input[name="cep"]');
        if (cepInput) {
            cepInput.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                value = value.replace(/(\d{5})(\d)/, '$1-$2');
                e.target.value = value;
            });
            
            // Buscar endereço por CEP
            cepInput.addEventListener('blur', buscarEnderecoPorCep);
        }

        // Telefones
        const telefoneInputs = document.querySelectorAll('input[name*="telefone"], input[name*="whatsapp"]');
        telefoneInputs.forEach(input => {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length <= 10) {
                    value = value.replace(/(\d{2})(\d)/, '($1) $2');
                    value = value.replace(/(\d{4})(\d)/, '$1-$2');
                } else {
                    value = value.replace(/(\d{2})(\d)/, '($1) $2');
                    value = value.replace(/(\d{5})(\d)/, '$1-$2');
                }
                e.target.value = value;
            });
        });
    }

    // 🔍 BUSCAR ENDEREÇO POR CEP
    function buscarEnderecoPorCep() {
        const cep = this.value.replace(/\D/g, '');
        
        if (cep.length === 8) {
            console.log('🔍 Buscando CEP:', cep);
            
            fetch(`https://viacep.com.br/ws/${cep}/json/`)
                .then(response => response.json())
                .then(data => {
                    if (!data.erro) {
                        document.querySelector('input[name="endereco"]').value = data.logradouro || '';
                        document.querySelector('input[name="bairro"]').value = data.bairro || '';
                        document.querySelector('input[name="cidade"]').value = data.localidade || '';
                        document.querySelector('input[name="estado"]').value = data.uf || '';
                        
                        console.log('✅ Endereço preenchido automaticamente');
                    }
                })
                .catch(error => {
                    console.log('⚠️ Erro ao buscar CEP:', error);
                });
        }
    }

    console.log('✅ Script cadastro parcial inicializado');
});