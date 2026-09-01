# gestcaptur/views/publico.py
# Views do domínio 'publico' (extraídas do antigo views.py monolítico).

import os
import base64
import uuid
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.urls import reverse
from gestcaptur.models import Evento, Aluno, Usuario, SessaoFotografica
from gestcaptur.forms import LoginForm, UploadFotoForm, ImportXLSXForm, CriarUsuarioForm, EditarUsuarioForm, EventoForm, AlunoCadastroForm, RoleForm
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def aluno_cadastro_publico(request, aluno_id=None, token=None, evento_id=None):
    # ========================================
    # CAPTURAR EVENTO DE MÚLTIPLAS FONTES
    # ========================================
    evento = None
    
    # Prioridade: URL parameter > GET parameter > POST parameter
    if evento_id:
        # Veio da URL (se implementado)
        try:
            evento = Evento.objects.get(id=evento_id)
            logger.info(f"✅ Evento {evento.id} capturado via URL parameter")
        except Evento.DoesNotExist:
            return render(request, 'gestcaptur/erro.html', {'mensagem': 'Evento não encontrado'})
    else:
        # Tentar GET parameter (do QR Code)
        evento_id_get = request.GET.get('evento')
        if evento_id_get:
            try:
                evento = Evento.objects.get(id=evento_id_get)
                logger.info(f"✅ Evento {evento.id} capturado via GET parameter")
            except Evento.DoesNotExist:
                return render(request, 'gestcaptur/erro.html', {'mensagem': 'Evento não encontrado'})
        else:
            # Fallback: POST parameter
            evento_id_post = request.POST.get('evento_id')
            if evento_id_post:
                try:
                    evento = Evento.objects.get(id=evento_id_post)
                    logger.info(f"✅ Evento {evento.id} capturado via POST parameter")
                except Evento.DoesNotExist:
                    return render(request, 'gestcaptur/erro.html', {'mensagem': 'Evento não encontrado'})

    if evento and evento.status == 'finalizado':
        return render(request, 'gestcaptur/erro.html', {
            'titulo': 'Evento encerrado',
            'mensagem': 'A captura e os links deste evento foram encerrados.'
        }, status=410)
    # ========================================
    # INICIALIZAÇÃO
    # ========================================
    start_time = time.time()
    logger.info(f"[INICIO] aluno_cadastro_publico - aluno_id: {aluno_id}, token: {token}, evento: {evento.id if evento else 'None'}")

    link_continuacao = None
    mostrar_modal_parcial = False
    campos_vazios_para_salvamento = []
    campos_faltando_labels = []
    aluno_salvo = None

    labels = {
        'nome': 'Nome Completo',
        'cpf': 'CPF',
        'data_nascimento': 'Data de Nascimento',
        'email': 'Email',
        'cep': 'CEP',
        'endereco': 'Endereço',
        'numero': 'Número',
        'bairro': 'Bairro',
        'cidade': 'Cidade',
        'estado': 'Estado',
        'whatsapp': 'WhatsApp',
        'nome_mae': 'Nome da Mãe',
        'whatsapp_mae': 'WhatsApp da Mãe'
    }
    # ========================================
    # BUSCAR ALUNO EXISTENTE (SE EDITANDO)
    # ========================================
    aluno = None
    if aluno_id and token:
        aluno = get_object_or_404(Aluno, id=aluno_id, token=token)

    # Se cadastro ja foi concluido e usuario recarrega a pagina (GET), redirecionar
    if aluno and aluno.cadastro_completo and request.method == 'GET':
        return redirect('aluno_cadastro_sucesso')

    # ========================================
    # PROCESSAR POST
    # ========================================
    if request.method == 'POST':
        logger.info(f"POST recebido para aluno {aluno_id if aluno else 'novo'}. Dados brutos: {request.POST}")
        logger.info(f"🚀 INICIANDO VALIDAÇÃO PERSONALIZADA") 
        
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        form = AlunoCadastroForm(request.POST, instance=aluno, evento=evento)

        # ========================================
        # VALIDAÇÃO PERSONALIZADA
        # ========================================
        
        # Campos estritamente obrigatórios (mínimo para salvar)
        campos_minimos = ['nome', 'whatsapp']
        
        # Campos para cadastro completo
        campos_completos = [
            'nome', 'cpf', 'data_nascimento', 'email', 'whatsapp',
            'nome_mae', 'whatsapp_mae'
        ]

        logger.info(f"🔍 Verificando campos mínimos: {campos_minimos}")
        
        # Verificar campos mínimos
        campos_minimos_faltando = []
        for campo in campos_minimos:
            valor = request.POST.get(campo, '').strip()
            if not valor:
                campos_minimos_faltando.append(campo)
        
        logger.info(f"🔍 Campos mínimos faltando: {campos_minimos_faltando}")
        # Se campos mínimos estão faltando, não pode salvar
        if campos_minimos_faltando:
            campos_minimos_labels = [labels.get(c, c) for c in campos_minimos_faltando]
            error_message = f'Para salvar o cadastro, é obrigatório preencher: {", ".join(campos_minimos_labels)}'

            logger.info(f"❌ Bloqueando salvamento. Erro: {error_message}")
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_message,
                    'campos_obrigatorios': campos_minimos_faltando
                })
            else:
                messages.error(request, error_message)
                context = {
                    'form': form,
                    'aluno': aluno,
                    'evento': evento,
                    'erro_campos_minimos': True,
                    'campos_obrigatorios_faltando': campos_minimos_labels,
                }
                return render(request, 'gestcaptur/aluno_cadastro_publico.html', context)
        
        # Verificar campos para cadastro completo
        campos_completos_faltando = []
        for campo in campos_completos:
            valor = request.POST.get(campo, '').strip()
            if not valor:
                campos_completos_faltando.append(campo)
        
        campos_faltando_labels = [labels.get(c, c) for c in campos_completos_faltando]
        
        # Forçar validação básica do formulário
        form_valido = form.is_valid()
        
        # ========================================
        # SALVAMENTO COMPLETO
        # ========================================
        if not campos_completos_faltando and form_valido:
            logger.info("Todos os campos completos preenchidos. Salvando COMPLETO.")
            try:
                aluno_salvo = form.save(commit=False)
                
                # Associar evento para novos alunos
                if not aluno_id:
                    if evento:
                        aluno_salvo.evento = evento
                        logger.info(f"✅ Evento {evento.id} associado ao novo aluno")
                    else:
                        logger.error("❌ ERRO: Nenhum evento encontrado!")
                        messages.error(request, 'Erro: Evento não identificado. Tente novamente.')
                        return render(request, 'gestcaptur/aluno_cadastro_publico.html', {'form': form, 'evento': evento})
                    
                    import uuid
                    aluno_salvo.token = str(uuid.uuid4())
                
                aluno_salvo.cadastro_completo = True
                aluno_salvo.status_comparecimento = 'presente' # NOVO: Marcar como presente ao completar
                
                # ✅ NOVO: Salvar selfie armazenada em sessão, se existir
                selfie_base64 = request.session.pop('selfie_temporaria_base64', None)
                if selfie_base64:
                    try:
                        # Decodificar e salvar selfie
                        if 'base64,' in selfie_base64:
                            selfie_base64 = selfie_base64.split('base64,')[1]
                        
                        import base64
                        image_bytes = base64.b64decode(selfie_base64)
                        nome_arquivo = f"selfie_{aluno_salvo.id}_{uuid.uuid4().hex[:8]}.jpg"
                        foto_content = ContentFile(image_bytes, name=nome_arquivo)
                        aluno_salvo.foto = foto_content
                        
                        logger.info(f"✅ Selfie capturada em sessão foi associada ao aluno {aluno_salvo.id}")
                    except Exception as e:
                        logger.error(f"⚠️ Erro ao processar selfie de sessão: {str(e)}")
                        # Continua mesmo se não conseguir salvar a selfie
                
                aluno_salvo.save()
                
                # Limpar variáveis de sessão
                request.session.pop('selfie_evento_id', None)
                request.session.pop('selfie_tipo', None)
                request.session.modified = True
                
                logger.info(f"✅ Cadastro COMPLETO salvo: {aluno_salvo.id}")
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'cadastro_completo': True,
                        'redirect_url': reverse('aluno_cadastro_sucesso'),
                        'message': 'Cadastro realizado com sucesso!'
                    })
                else:
                    messages.success(request, 'Cadastro realizado com sucesso!')
                    return redirect('aluno_cadastro_sucesso')
                
            except Exception as e:
                logger.error(f"❌ Erro ao salvar cadastro completo: {str(e)}")
                messages.error(request, f'Erro ao salvar cadastro: {str(e)}')
                context = {
                    'form': form,
                    'aluno': aluno,
                    'evento': evento,
                }
                return render(request, 'gestcaptur/aluno_cadastro_publico.html', context)
        # ========================================
        # SALVAMENTO PARCIAL
        # ========================================
        else:
            logger.info(f"Campos faltando para cadastro completo: {campos_completos_faltando}")

            # Se o form tem erros de validacao (ex: WhatsApp duplicado),
            # mostrar erros independente de campos faltando.
            if not form_valido:
                for field_name, error_list in form.errors.items():
                    for error in error_list:
                        if field_name == '__all__':
                            messages.error(request, str(error))
                        else:
                            field_label = form.fields[field_name].label if field_name in form.fields else field_name
                            messages.error(request, f'{field_label}: {error}')
                context = {
                    'form': form,
                    'aluno': aluno,
                    'evento': evento,
                }
                return render(request, 'gestcaptur/aluno_cadastro_publico.html', context)

            # Verificar se usuário confirmou salvar parcial
            confirmar_parcial = request.POST.get('confirmar_parcial', False)
            
            if not confirmar_parcial:
                # Mostrar modal de confirmação
                mensagem_confirmacao = f"Campos necessários não foram preenchidos: {', '.join(campos_faltando_labels)}. Deseja salvar assim mesmo e completar mais tarde?"
                
                context = {
                    'form': form,
                    'aluno': aluno,
                    'evento': evento,
                    'mostrar_confirmacao_parcial': True,
                    'campos_faltando': campos_faltando_labels,
                    'mensagem_confirmacao': mensagem_confirmacao,
                    'dados_form': request.POST,  # Para manter os dados preenchidos
                }
                return render(request, 'gestcaptur/aluno_cadastro_publico.html', context)
            
            # Usuário confirmou → salvar parcial
            try:
                # Criar formulário sem validação obrigatória para salvar parcial
                aluno_salvo = form.save(commit=False) if form_valido else (aluno or Aluno())
                
                # Aplicar dados manualmente se form não é válido
                if not form_valido:
                    for field_name in form.fields:
                        valor = request.POST.get(field_name, '').strip()
                        if valor:
                            setattr(aluno_salvo, field_name, valor)
                
                # Associar evento para novos alunos
                if not aluno_id:
                    if evento:
                        aluno_salvo.evento = evento
                        logger.info(f"✅ Evento {evento.id} associado ao novo aluno (PARCIAL)")
                    else:
                        logger.error("❌ ERRO: Nenhum evento encontrado!")
                        messages.error(request, 'Erro: Evento não identificado.')
                        return render(request, 'gestcaptur/aluno_cadastro_publico.html', {'form': form, 'evento': evento})
                    
                    import uuid
                    aluno_salvo.token = str(uuid.uuid4())
                
                aluno_salvo.cadastro_completo = False
                aluno_salvo.status_comparecimento = 'presente' # NOVO: Marcar como presente por padrão
                
                # ✅ NOVO: Salvar selfie armazenada em sessão, se existir (PARCIAL também)
                selfie_base64 = request.session.get('selfie_temporaria_base64', None)
                if selfie_base64:
                    try:
                        # Decodificar e salvar selfie
                        if 'base64,' in selfie_base64:
                            selfie_base64_clean = selfie_base64.split('base64,')[1]
                        else:
                            selfie_base64_clean = selfie_base64
                        
                        import base64
                        image_bytes = base64.b64decode(selfie_base64_clean)
                        nome_arquivo = f"selfie_{aluno_salvo.id}_{uuid.uuid4().hex[:8]}.jpg"
                        foto_content = ContentFile(image_bytes, name=nome_arquivo)
                        aluno_salvo.foto = foto_content
                        
                        logger.info(f"✅ Selfie capturada em sessão foi associada ao aluno {aluno_salvo.id} (PARCIAL)")
                        
                        # Limpar da sessão após salvar
                        request.session.pop('selfie_temporaria_base64', None)
                    except Exception as e:
                        logger.error(f"⚠️ Erro ao processar selfie de sessão no parcial: {str(e)}")
                        # Continua mesmo se não conseguir salvar a selfie
                
                aluno_salvo.save()
                
                # Limpar demais variáveis de sessão
                request.session.pop('selfie_evento_id', None)
                request.session.pop('selfie_tipo', None)
                request.session.modified = True
                
                logger.info(f"✅ Cadastro PARCIAL salvo: {aluno_salvo.id}")
                
                # Gerar link de continuação
                link_continuacao = request.build_absolute_uri(
                    reverse('aluno_cadastro_publico_editar', args=[aluno_salvo.id, aluno_salvo.token])
                )
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'cadastro_completo': False,
                        'nome': aluno_salvo.nome or 'Usuário',
                        'link_continuacao': link_continuacao,
                        'campos_faltando': campos_faltando_labels,
                        'message': 'Cadastro incompleto salvo! Complete quando puder.'
                    })
                else:
                    # Mostrar página de sucesso parcial
                    context = {
                        'aluno': aluno_salvo,
                        'cadastro_parcial_salvo': True,
                        'link_continuacao': link_continuacao,
                        'campos_faltando': campos_faltando_labels,
                        'evento': evento,
                        'mensagem_sucesso': f'Cadastro salvo com sucesso! Para completar os dados faltantes ({", ".join(campos_faltando_labels)}), use o link abaixo:'
                    }
                    return render(request, 'gestcaptur/aluno_cadastro_publico.html', context)
                
            except Exception as e:
                logger.error(f"❌ Erro ao salvar cadastro parcial: {str(e)}")
                messages.error(request, f'Erro ao salvar cadastro: {str(e)}')
                context = {
                    'form': form,
                    'aluno': aluno,
                    'evento': evento,
                }
                return render(request, 'gestcaptur/aluno_cadastro_publico.html', context)
    # ========================================
    # GET REQUEST
    # ========================================
    else:
        form = AlunoCadastroForm(instance=aluno, evento=evento)

    # ========================================
    # CONTEXTO E RESPOSTA
    # ========================================
    context = {
        'form': form,
        'aluno': aluno_salvo if 'aluno_salvo' in locals() else aluno,
        'mostrar_modal_parcial': mostrar_modal_parcial,
        'link_continuacao': link_continuacao,
        'campos_faltando': campos_faltando_labels,
        'evento': evento,
    }

    end_time = time.time()
    logger.info(f"[FIM] aluno_cadastro_publico - Tempo total: {end_time - start_time:.2f}s")

    return render(request, 'gestcaptur/aluno_cadastro_publico.html', context)


def salvar_info_cadastro_incompleto(aluno, link):
    """Salvar informações do cadastro incompleto para backup"""
    try:
        import os
        from datetime import datetime
        
        backup_dir = '/tmp/photoapp-cadastros-incompletos'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{backup_dir}/cadastro_{aluno.id}_{timestamp}.txt"
        
        conteudo = f"""
=== CADASTRO INCOMPLETO PHOTOAPP ===
Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
ID: {aluno.id}
Nome: {aluno.nome or 'Não informado'}
Email: {aluno.email or 'Não informado'}
WhatsApp: {aluno.whatsapp or 'Não informado'}
Nome da Mãe: {aluno.nome_mae or 'Não informado'}
WhatsApp da Mãe: {aluno.whatsapp_mae or 'Não informado'}

LINK DE CONTINUAÇÃO:
{link}

INSTRUÇÕES:
- Usuário pode salvar este link nos favoritos
- Ou copiar o link para usar depois
- Não há envio de email

=== FIM ===
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(conteudo)
            
        print(f"📁 Cadastro incompleto salvo: {filename}")
        print(f"👤 Usuário: {aluno.nome} ({aluno.email})")
        print(f"🔗 Link: {link}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar backup: {e}")


def aluno_cadastro_sucesso(request):
    return render(request, 'gestcaptur/aluno_cadastro_sucesso.html')
