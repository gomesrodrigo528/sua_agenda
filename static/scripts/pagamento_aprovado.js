// Funções de validação e interação
function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorDiv = document.getElementById(fieldId + '-error');
    const errorSpan = errorDiv.querySelector('span');
    
    field.classList.add('error');
    errorSpan.textContent = message;
    errorDiv.classList.add('show');
    
    // Limpa o erro quando o usuário começa a corrigir
    field.addEventListener('input', function() {
        this.classList.remove('error');
        errorDiv.classList.remove('show');
    }, { once: true });
}

function clearFieldErrors() {
    document.querySelectorAll('.form-control.error').forEach(field => {
        field.classList.remove('error');
    });
    document.querySelectorAll('.field-error.show').forEach(error => {
        error.classList.remove('show');
    });
}

function showSuccessMessage(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `<i class="bi bi-check-circle-fill"></i>${message}`;
    
    const container = document.querySelector('.form-container');
    container.insertBefore(successDiv, container.firstChild);
    
    setTimeout(() => {
        successDiv.remove();
    }, 5000);
}

function showErrorMessage(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `<i class="bi bi-x-circle-fill"></i>${message}`;
    
    const container = document.querySelector('.form-container');
    container.insertBefore(errorDiv, container.firstChild);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Popup de erro para empresa já cadastrada
function showEmpresaCadastradaPopup() {
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = 0;
    overlay.style.left = 0;
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.background = 'rgba(0,0,0,0.5)';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.zIndex = 99999;

    const popup = document.createElement('div');
    popup.style.background = '#fff';
    popup.style.borderRadius = '16px';
    popup.style.padding = '40px 30px';
    popup.style.maxWidth = '350px';
    popup.style.textAlign = 'center';
    popup.style.boxShadow = '0 8px 32px rgba(0,0,0,0.25)';
    popup.innerHTML = `
        <div style='font-size:48px; color:#dc3545; margin-bottom:16px;'><i class='bi bi-x-circle-fill'></i></div>
        <div style='font-size:20px; font-weight:600; margin-bottom:10px;'>Empresa já cadastrada</div>
        <div style='font-size:16px; color:#555; margin-bottom:24px;'>Já existe uma empresa com este e-mail ou documento.<br>Entre em contato para renovar seu plano ou tente novamente.</div>
        <button id='btnPopupEmpresaCadastrada' style='background:#dc3545; color:#fff; border:none; border-radius:8px; padding:10px 30px; font-size:16px; font-weight:600; cursor:pointer;'>OK</button>
    `;
    overlay.appendChild(popup);
    document.body.appendChild(overlay);
    document.getElementById('btnPopupEmpresaCadastrada').onclick = function() {
        document.body.removeChild(overlay);
        window.location.href = '/adquirir';
    };
}

// Função para validar CPF
function validarCPF(cpf) {
    cpf = cpf.replace(/[^\d]+/g,'');
    if(cpf.length !== 11) return false;
    
    // Validação do primeiro dígito
    let soma = 0;
    for(let i = 0; i < 9; i++) {
        soma += parseInt(cpf.charAt(i)) * (10 - i);
    }
    let resto = 11 - (soma % 11);
    let digitoVerificador1 = resto > 9 ? 0 : resto;
    if(digitoVerificador1 != cpf.charAt(9)) return false;

    // Validação do segundo dígito
    soma = 0;
    for(let i = 0; i < 10; i++) {
        soma += parseInt(cpf.charAt(i)) * (11 - i);
    }
    resto = 11 - (soma % 11);
    let digitoVerificador2 = resto > 9 ? 0 : resto;
    if(digitoVerificador2 != cpf.charAt(10)) return false;

    return true;
}

// Função para validar CNPJ
function validarCNPJ(cnpj) {
    cnpj = cnpj.replace(/[^\d]+/g,'');
    if(cnpj.length !== 14) return false;
    
    // Validação do primeiro dígito
    let soma = 0;
    let multiplicador = 5;
    for(let i = 0; i < 12; i++) {
        soma += parseInt(cnpj.charAt(i)) * multiplicador;
        multiplicador = multiplicador === 2 ? 9 : multiplicador - 1;
    }
    let resto = soma % 11;
    let digitoVerificador1 = resto < 2 ? 0 : 11 - resto;
    if(digitoVerificador1 != cnpj.charAt(12)) return false;

    // Validação do segundo dígito
    soma = 0;
    multiplicador = 6;
    for(let i = 0; i < 13; i++) {
        soma += parseInt(cnpj.charAt(i)) * multiplicador;
        multiplicador = multiplicador === 2 ? 9 : multiplicador - 1;
    }
    resto = soma % 11;
    let digitoVerificador2 = resto < 2 ? 0 : 11 - resto;
    if(digitoVerificador2 != cnpj.charAt(13)) return false;

    return true;
}

function validarEmail(email) {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(email);
}

function validarSenha(senha) {
    const temTamanhoMinimo = senha.length >= 8;
    const temMaiuscula = /[A-Z]/.test(senha);
    const temMinuscula = /[a-z]/.test(senha);
    const temNumero = /[0-9]/.test(senha);

    // Atualiza o visual dos requisitos
    $('#req-tamanho').toggleClass('valid', temTamanhoMinimo).toggleClass('invalid', !temTamanhoMinimo)
        .find('i').toggleClass('bi-check-circle-fill', temTamanhoMinimo).toggleClass('bi-circle', !temTamanhoMinimo);
    
    $('#req-maiuscula').toggleClass('valid', temMaiuscula).toggleClass('invalid', !temMaiuscula)
        .find('i').toggleClass('bi-check-circle-fill', temMaiuscula).toggleClass('bi-circle', !temMaiuscula);
    
    $('#req-minuscula').toggleClass('valid', temMinuscula).toggleClass('invalid', !temMinuscula)
        .find('i').toggleClass('bi-check-circle-fill', temMinuscula).toggleClass('bi-circle', !temMinuscula);
    
    $('#req-numero').toggleClass('valid', temNumero).toggleClass('invalid', !temNumero)
        .find('i').toggleClass('bi-check-circle-fill', temNumero).toggleClass('bi-circle', !temNumero);

    return temTamanhoMinimo && temMaiuscula && temMinuscula && temNumero;
}

async function validarFormularioEmpresa() {
    clearFieldErrors();
    let hasErrors = false;

    // Validação do nome da empresa
    if($('#nome_empresa').val().trim().length < 3) {
        showFieldError('nome_empresa', 'O nome da empresa deve ter pelo menos 3 caracteres');
        hasErrors = true;
    }

    const cnpjCpf = $('#cnpj').val().replace(/[^\d]+/g,'');
    const tipoDocumento = $('#tipo_documento').val();
    
    // Validação do CNPJ/CPF
    if(tipoDocumento === 'cpf') {
        if(!validarCPF(cnpjCpf)) {
            showFieldError('cnpj', 'CPF inválido');
            hasErrors = true;
        }
    } else {
        if(!validarCNPJ(cnpjCpf)) {
            showFieldError('cnpj', 'CNPJ inválido');
            hasErrors = true;
        }
    }

    // Validação do e-mail
    const email = $('#email').val();
    if(!validarEmail(email)) {
        showFieldError('email', 'E-mail inválido');
        hasErrors = true;
    }

    // Validação da descrição
    const descricao = $('#descricao').val().trim();
    if(descricao.length === 0) {
        showFieldError('descricao', 'A descrição é obrigatória');
        hasErrors = true;
    } else if(descricao.length > 30) {
        showFieldError('descricao', 'A descrição deve ter no máximo 30 caracteres');
        hasErrors = true;
    }

    // Validação do setor
    if($('#setor').val() === '') {
        showFieldError('setor', 'Selecione um setor');
        hasErrors = true;
    }

    // Validação do telefone
    const telefone = $('#tel_empresa').val().replace(/[^\d]+/g,'');
    if(telefone.length !== 11) {
        showFieldError('tel_empresa', 'Telefone inválido');
        hasErrors = true;
    }

    // Validação da cidade
    if($('#cidade').val().trim().length < 3) {
        showFieldError('cidade', 'Nome da cidade inválido');
        hasErrors = true;
    }

    // Validação do CEP
    const cep = $('#cep').val().replace(/[^\d]+/g,'');
    if(cep.length !== 8) {
        showFieldError('cep', 'CEP inválido');
        hasErrors = true;
    }

    // Validação do endereço
    if($('#endereco').val().trim().length < 5) {
        showFieldError('endereco', 'Endereço inválido');
        hasErrors = true;
    }

    if(hasErrors) {
        return false;
    }

    // Verificar se empresa já existe antes de enviar
    try {
        showLoading();
        const response = await fetch('/api/verificar-empresa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                cnpj: cnpjCpf
            })
        });

        const data = await response.json();
        
        if (data.existe) {
            if (data.teste_ativo) {
                showSuccessMessage('Empresa já cadastrada com teste ativo. Você pode continuar.');
                hideLoading();
                return true;
            } else {
                showFieldError('email', 'Empresa já cadastrada. Entre em contato para renovar seu plano.');
                hideLoading();
                return false;
            }
        }
        
        hideLoading();
        return true;
    } catch (error) {
        console.error('Erro ao verificar empresa:', error);
        hideLoading();
        return true; // Permite continuar em caso de erro na verificação
    }
}

function validarFormularioUsuario() {
    clearFieldErrors();
    let hasErrors = false;

    // Validação do nome do usuário
    if($('#nome_usuario').val().trim().length < 3) {
        showFieldError('nome_usuario', 'O nome deve ter pelo menos 3 caracteres');
        hasErrors = true;
    }

    // Validação do e-mail
    if(!validarEmail($('#email_usuario').val())) {
        showFieldError('email_usuario', 'E-mail inválido');
        hasErrors = true;
    }

    // Validação do telefone
    const telefone = $('#telefone').val().replace(/[^\d]+/g,'');
    if(telefone.length !== 11) {
        showFieldError('telefone', 'Telefone inválido');
        hasErrors = true;
    }

    // Validação da senha
    const senha = $('#senha').val();
    if(!validarSenha(senha)) {
        showFieldError('senha', 'A senha não atende aos requisitos mínimos de segurança');
        hasErrors = true;
    }

    if(hasErrors) {
        return false;
    }

    showLoading();
    return true;
}

// Event listener para interceptar o submit do formulário de empresa
document.addEventListener('DOMContentLoaded', function() {
    const empresaForm = document.getElementById('empresaForm');
    if (empresaForm) {
        empresaForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Validar formulário
            const isValid = await validarFormularioEmpresa();
            if (!isValid) {
                return false;
            }
            
            // Coletar dados do formulário
            const formData = new FormData(this);
            const dados = Object.fromEntries(formData.entries());
            
            try {
                showLoading();
                const response = await fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(dados)
                });
                
                const data = await response.json();
                hideLoading();
                
                if (data.success) {
                    showSuccessMessage('Empresa cadastrada com sucesso! Agora cadastre o usuário responsável.');
                    // Armazenar ID da empresa para usar no cadastro do usuário
                    window.empresaId = data.empresa_id;
                    
                    // Ocultar formulário de empresa e mostrar formulário de usuário
                    setTimeout(() => {
                        // Ocultar o formulário de empresa
                        const empresaFormContainer = document.getElementById('empresa-form-container');
                        if (empresaFormContainer) {
                            empresaFormContainer.style.display = 'none';
                        }
                        
                        // Mostrar o formulário de usuário
                        const usuarioFormContainer = document.getElementById('usuario-form-container');
                        if (usuarioFormContainer) {
                            usuarioFormContainer.style.display = 'block';
                            
                            // Adicionar o ID da empresa como campo hidden se não existir
                            const usuarioForm = document.getElementById('usuarioForm');
                            if (usuarioForm && !usuarioForm.querySelector('input[name="empresa_id"]')) {
                                const empresaIdInput = document.createElement('input');
                                empresaIdInput.type = 'hidden';
                                empresaIdInput.name = 'empresa_id';
                                empresaIdInput.value = data.empresa_id;
                                usuarioForm.appendChild(empresaIdInput);
                            }
                        }
                    }, 2000);
                } else {
                    showErrorMessage(data.error || 'Erro ao cadastrar empresa.');
                }
            } catch (error) {
                hideLoading();
                console.error('Erro ao cadastrar empresa:', error);
                showErrorMessage('Erro inesperado ao cadastrar empresa.');
            }
        });
    }
    
    // Event listener para interceptar o submit do formulário de usuário
    const usuarioForm = document.getElementById('usuarioForm');
    if (usuarioForm) {
        usuarioForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Validar formulário
            const isValid = validarFormularioUsuario();
            if (!isValid) {
                return false;
            }
            
            // Coletar dados do formulário
            const formData = new FormData(this);
            const dados = Object.fromEntries(formData.entries());
            
            try {
                showLoading();
                const response = await fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(dados)
                });
                
                const data = await response.json();
                hideLoading();
                
                if (data.success) {
                    showSuccessMessage('Usuário cadastrado com sucesso! Você pode fazer login agora.');
                    // Redirecionar para login após 2 segundos
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                } else {
                    showErrorMessage(data.error || 'Erro ao cadastrar usuário.');
                }
            } catch (error) {
                hideLoading();
                console.error('Erro ao cadastrar usuário:', error);
                showErrorMessage('Erro inesperado ao cadastrar usuário.');
            }
        });
    }

    // Máscaras para os campos
    $('#tel_empresa, #telefone').mask('(00) 00000-0000');
    $('#cep').mask('00000-000');
    
    // Máscara inicial como CPF
    $('#cnpj').mask('000.000.000-00');

    // Alternar entre máscaras de CPF e CNPJ
    $('#tipo_documento').on('change', function() {
        var tipo = $(this).val();
        var campo = $('#cnpj');
        campo.val(''); // Limpa o campo ao trocar
        if (tipo === 'cpf') {
            campo.mask('000.000.000-00');
            campo.attr('placeholder', 'Digite o CPF');
        } else {
            campo.mask('00.000.000/0000-00');
            campo.attr('placeholder', 'Digite o CNPJ');
        }
    });

    // Validação em tempo real da senha
    $('#senha').on('input', function() {
        validarSenha($(this).val());
    });

    // Botão para mostrar/ocultar senha
    $('#mostrarSenha').on('click', function() {
        const senhaInput = $('#senha');
        const icon = $(this).find('i');
        
        if (senhaInput.attr('type') === 'password') {
            senhaInput.attr('type', 'text');
            icon.removeClass('bi-eye').addClass('bi-eye-slash');
        } else {
            senhaInput.attr('type', 'password');
            icon.removeClass('bi-eye-slash').addClass('bi-eye');
        }
    });

    // Validação em tempo real dos campos
    $('.form-control').on('input', function() {
        this.classList.remove('error');
        const errorDiv = document.getElementById(this.id + '-error');
        if (errorDiv) {
            errorDiv.classList.remove('show');
        }
    });

    // Validações específicas em tempo real
    $('#nome_empresa').on('input', function() {
        const nome = $(this).val().trim();
        if(nome.length < 3) {
            showFieldError('nome_empresa', 'O nome da empresa deve ter pelo menos 3 caracteres');
        }
    });

    $('#descricao').on('input', function() {
        const desc = $(this).val().trim();
        if(desc.length === 0) {
            showFieldError('descricao', 'A descrição é obrigatória');
        } else if(desc.length > 30) {
            showFieldError('descricao', 'A descrição deve ter no máximo 30 caracteres');
        }
    });

    $('#setor').on('change', function() {
        if($(this).val() === '') {
            showFieldError('setor', 'Selecione um setor');
        }
    });

    $('#cidade').on('input', function() {
        const cidade = $(this).val().trim();
        if(cidade.length < 3) {
            showFieldError('cidade', 'Nome da cidade inválido');
        }
    });

    $('#endereco').on('input', function() {
        const endereco = $(this).val().trim();
        if(endereco.length < 5) {
            showFieldError('endereco', 'Endereço inválido');
        }
    });

    // Exibir popup de erro se empresa já cadastrada
    // Removido temporariamente para evitar redirecionamento indesejado
}); 