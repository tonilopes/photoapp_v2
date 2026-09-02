# gestcaptur/views_formandos.py
# Views para o fluxo de autoatendimento de formandos

import os
import uuid
import json
import pandas as pd
import logging
import qrcode
import io
import base64
import unicodedata
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings
from PIL import Image, UnidentifiedImageError

from .models import Evento, Aluno, Usuario
from .forms import AlunoCadastroForm
from .decorators import role_required, evento_permission_required

logger = logging.getLogger(__name__)


# ============================================================================
# FUNÇÕES HELPER
# ============================================================================

def _obter_evento(evento_id=None, evento_uuid=None):
    """
    Obtém Evento por UUID (preferível) ou ID numérico (legado)
    
    Prioridade:
    1. evento_uuid (mais seguro)
    2. evento_id (compatibilidade com URLs antigas)
    """
    if evento_uuid:
        return get_object_or_404(Evento, uuid=evento_uuid)
    elif evento_id:
        return get_object_or_404(Evento, id=evento_id)
    else:
        raise ValueError("evento_id ou evento_uuid é obrigatório")


# ============================================================================
# FLUXO PÚBLICO: Selfie + Cadastro de Formandos
# ============================================================================

@csrf_exempt
def formando_selfie_cadastro(request, evento_id=None, evento_uuid=None, token=None):
    """
    View pública para fluxo de autoatendimento de formandos:
    1. Captura de selfie obrigatória
    2. Cadastro com dados pessoais
    3. Salva foto como TURMA-NOME.jpg
    
    Acessível via: 
    - /evento/<uuid>/selfie-cadastro/ (recomendado - seguro)
    - /evento/<id>/selfie-cadastro/ (legado - não recomendado)
    """
    evento = _obter_evento(evento_id=evento_id, evento_uuid=evento_uuid)

    if evento.status == 'finalizado':
        return render(request, 'gestcaptur/erro.html', {
            'titulo': 'Captura finalizada',
            'mensagem': 'Captura finalizada. Entre em contato com a empresa ou comissão de formatura.'
        }, status=410)
    
    # Verificar se evento permite selfie
    if not evento.para_selfie:
        return render(request, 'gestcaptur/erro.html', {
            'titulo': 'Evento não disponível',
            'mensagem': 'Este evento não permite cadastro público no momento.'
        })
    
    # Se houver token, tentar recuperar aluno existente
    aluno = None
    if token:
        try:
            aluno = Aluno.objects.get(evento=evento, token=token)
            # ✅ BLOQUEAR ACESSO SE CADASTRO JÁ COMPLETADO
            if aluno.cadastro_completo:
                return render(request, 'gestcaptur/erro.html', {
                    'titulo': 'Cadastro já realizado',
                    'mensagem': 'Seu cadastro já foi completado. Não é possível acessar novamente.'
                })
        except Aluno.DoesNotExist:
            pass
    
    if request.method == 'POST':
        # Verificar qual etapa está sendo enviada
        etapa = request.POST.get('etapa', 'selfie')
        
        if etapa == 'selfie':
            return _processar_selfie(request, evento)
        
        elif etapa == 'cadastro':
            return _processar_cadastro(request, evento, aluno)
    
    # GET - Verificar se está vindo do passo de selfie ou está no início
    if 'selfie_data' in request.session:
        # Mostrar formulário de cadastro
        context = {
            'evento': evento,
            'form': AlunoCadastroForm(evento=evento),
            'aluno': aluno,
            'passo_atual': 'cadastro',
        }
        return render(request, 'gestcaptur/formando_cadastro.html', context)
    else:
        # Mostrar página inicial de selfie
        context = {
            'evento': evento,
            'aluno': aluno,
            'telefone_obrigatorio': True,
            'selfie_obrigatoria': True,
            'passo_atual': 'selfie',
        }
        return render(request, 'gestcaptur/formando_selfie_cadastro.html', context)


def _processar_selfie(request, evento):
    """Processa o upload da selfie"""
    if evento.status == 'finalizado':
        return JsonResponse({
            'sucesso': False,
            'erro': 'Captura finalizada. Entre em contato com a empresa ou comissão de formatura.'
        }, status=410)

    if 'foto' not in request.FILES:
        return JsonResponse({
            'sucesso': False,
            'erro': 'Nenhuma foto foi enviada'
        }, status=400)
    
    foto = request.FILES['foto']

    try:
        imagem = Image.open(foto)
        largura, altura = imagem.size
        if largura < 320 or altura < 320:
            return JsonResponse({
                'sucesso': False,
                'erro': 'A imagem tem resolução muito baixa. Use a câmera do celular.'
            }, status=400)

        imagem.thumbnail((320, 320))
        brilho = sum(imagem.convert('L').getdata()) / (imagem.width * imagem.height)
        if brilho < 80:
            return JsonResponse({
                'sucesso': False,
                'erro': 'A foto está escura. Procure um local mais iluminado e tente novamente.'
            }, status=400)
        if brilho > 225:
            return JsonResponse({
                'sucesso': False,
                'erro': 'A foto está clara demais. Evite luz direta ou contraluz.'
            }, status=400)
        foto.seek(0)
    except (UnidentifiedImageError, OSError):
        return JsonResponse({
            'sucesso': False,
            'erro': 'O arquivo enviado não é uma imagem válida.'
        }, status=400)
    
    # Gerar nome único para a selfie temporária
    nome_temp = f"selfie-{uuid.uuid4()}.jpg"
    
    try:
        # Salvar foto temporária na sessão ou em arquivo
        request.session['selfie_data'] = {
            'nome_arquivo': nome_temp,
            'timestamp': timezone.now().isoformat(),
        }
        
        # Salvar arquivo em local temporário
        temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', nome_temp)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        with open(temp_path, 'wb') as f:
            for chunk in foto.chunks():
                f.write(chunk)
        
        return JsonResponse({
            'sucesso': True,
            'mensagem': 'Selfie capturada com sucesso!',
            'proximo_passo': 'cadastro'
        })
    
    except Exception as e:
        logger.error(f"Erro ao salvar selfie: {e}")
        return JsonResponse({
            'sucesso': False,
            'erro': 'Erro ao processar a selfie'
        }, status=500)


def _processar_cadastro(request, evento, aluno=None):
    """Processa o formulário de cadastro do formando"""
    if evento.status == 'finalizado':
        return render(request, 'gestcaptur/erro.html', {
            'titulo': 'Captura finalizada',
            'mensagem': 'Captura finalizada. Entre em contato com a empresa ou comissão de formatura.'
        }, status=410)

    if request.method == 'POST':
        # Se não há aluno, criar novo
        if not aluno:
            aluno = Aluno(evento=evento)
        
        form = AlunoCadastroForm(request.POST, request.FILES, instance=aluno, evento=evento)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Salvar formulário
                    aluno = form.save(commit=False)
                    
                    # Garantir que o evento está correto
                    aluno.evento = evento
                    
                    # Aplicar código da turma
                    aluno.codigo_turma = evento.codigo_turma
                    aluno.selfie_realizada = True
                    aluno.cadastro_completo = True
                    
                    # Processar foto da selfie se existir na sessão
                    if 'selfie_data' in request.session:
                        selfie_data = request.session['selfie_data']
                        temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', selfie_data['nome_arquivo'])
                        
                        if os.path.exists(temp_path):
                            # Ler foto temporária
                            with open(temp_path, 'rb') as f:
                                foto_content = f.read()
                            
                            # Gerar nome final: TURMA-NOME.jpg
                            nome_final = aluno.get_nome_arquivo_foto()
                            
                            # Salvar com novo nome
                            aluno.foto.save(nome_final, ContentFile(foto_content), save=False)
                            
                            # Limpar arquivo temporário
                            try:
                                os.remove(temp_path)
                            except:
                                pass
                        
                        # Limpar sessão
                        del request.session['selfie_data']
                    
                    # Salvar aluno
                    aluno.save()
                    
                    # Limpar sessão
                    request.session.flush()
                    
                    return render(request, 'gestcaptur/formando_cadastro_sucesso.html', {
                        'evento': evento,
                        'aluno': aluno,
                    })
            
            except Exception as e:
                logger.error(f"Erro ao salvar cadastro: {e}")
                messages.error(request, f"Erro ao salvar cadastro: {str(e)}")
        
        else:
            # Mostrar form com erros
            context = {
                'evento': evento,
                'form': form,
                'aluno': aluno,
            }
            return render(request, 'gestcaptur/formando_cadastro.html', context)
    
    # GET - Mostrar formulário de cadastro
    context = {
        'evento': evento,
        'form': AlunoCadastroForm(instance=aluno, evento=evento),
        'aluno': aluno,
    }
    return render(request, 'gestcaptur/formando_cadastro.html', context)


# ============================================================================
# PAINEL DE CONTROLE DO GESTOR
# ============================================================================

@login_required
def formandos_status(request, evento_id=None, evento_uuid=None):
    """
    Grade de controle do gestor mostrando:
    - Lista de formandos
    - Status de selfie (✅ / ❌)
    - Status de cadastro (✅ / ❌)
    - Foto (visualizar/download)
    - Ações (editar, reenviar link)
    
    Acessível por:
    - Gestor (acesso completo)
    - Coordenador do evento (acesso completo)
    - Parceiro (leitura apenas)
    
    **SEGURANÇA:**
    - Requer autenticação (@login_required)
    - Parceiros só veem eventos vinculados a eles
    
    URLs suportadas:
    - /evento/<uuid>/formandos-status/ (recomendado)
    - /evento/<id>/formandos-status/ (legado)
    """
    evento = _obter_evento(evento_id=evento_id, evento_uuid=evento_uuid)
    
    # Verificar permissão
    eh_gestor = request.user.is_gestor()
    eh_coordenador = evento.coordenador == request.user
    eh_parceiro = request.user.is_parceiro()
    tem_permissao_evento = any(request.user.has_perm(permissao) for permissao in [
        'gestcaptur.download_fotos_evento',
        'gestcaptur.download_cadastros_evento',
        'gestcaptur.finalizar_captura_evento',
    ])
    
    if not (eh_gestor or eh_coordenador or eh_parceiro or tem_permissao_evento):
        messages.error(request, "Você não tem permissão para acessar este relatório.")
        return redirect('dashboard')
    
    # ✅ NOVO: Se é parceiro, verificar se tem acesso a este evento específico
    if eh_parceiro and not (eh_gestor or eh_coordenador):
        # Parceiro só pode acessar eventos que foram vinculados a ele
        if evento not in request.user.eventos_como_parceiro.all():
            messages.error(request, "Você não tem permissão para acessar este evento.")
            return redirect('dashboard')
    
    # Flag para controlar permissões no template
    eh_leitura = evento.status == 'finalizado' or (
        eh_parceiro and not (eh_gestor or eh_coordenador)
    )
    
    # Filtrar alunos
    alunos = evento.alunos.all().order_by('nome')
    
    # Adicionar badges de status
    alunos_com_status = []
    for aluno in alunos:
        # Usar UUID na URL (SEMPRE - mais seguro)
        url_base = f"/evento/{evento.uuid}/selfie-cadastro/"
        alunos_com_status.append({
            'aluno': aluno,
            'selfie_ok': aluno.selfie_realizada,  # ✅ Apenas selfie realizada (novo fluxo)
            'cadastro_ok': aluno.cadastro_completo,
            'completo': aluno.selfie_realizada and aluno.cadastro_completo,  # ✅ Ambos obrigatórios
            'link_edicao': f"{url_base}?token={aluno.token}",
        })
    
    # Estatísticas
    stats = {
        'total': alunos.count(),
        'com_selfie': sum(1 for a in alunos_com_status if a['selfie_ok']),
        'com_cadastro': sum(1 for a in alunos_com_status if a['cadastro_ok']),
        'completos': sum(1 for a in alunos_com_status if a['completo']),
    }
    
    # Calcular percentuais
    if stats['total'] > 0:
        stats['pct_selfie'] = int((stats['com_selfie'] / stats['total']) * 100)
        stats['pct_cadastro'] = int((stats['com_cadastro'] / stats['total']) * 100)
        stats['pct_completos'] = int((stats['completos'] / stats['total']) * 100)
    
    context = {
        'evento': evento,
        'alunos': alunos_com_status,
        'stats': stats,
        'is_read_only': eh_leitura,  # Flag para parceiros (leitura apenas)
        'captura_finalizada': evento.status == 'finalizado',
        'can_download_fotos': request.user.has_perm('gestcaptur.download_fotos_evento'),
        'can_download_cadastros': request.user.has_perm('gestcaptur.download_cadastros_evento'),
        'can_finalizar_captura': request.user.has_perm('gestcaptur.finalizar_captura_evento'),
        # Permissões granulares para os botões de ação do painel:
        # Gestor e coordenador do evento têm controle total; demais dependem de permissão.
        'can_editar': (
            eh_gestor or eh_coordenador
            or request.user.has_perm('gestcaptur.change_aluno')
        ),
        'can_compartilhar': (
            eh_gestor or eh_coordenador
            or request.user.has_perm('gestcaptur.ver_botao_compartilhar_formandos')
        ),
        'can_gerenciar_parceiros': (
            eh_gestor or eh_coordenador
            or request.user.has_perm('gestcaptur.ver_botao_parceiros_formandos')
        ),
        'can_importar_nomes': (
            eh_gestor
            or request.user.has_perm('gestcaptur.add_aluno')
        ),
    }
    
    # Se solicitado em JSON (para AJAX), retornar dados
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'evento': evento.fot,
            'stats': stats,
            'alunos': [
                {
                    'id': a['aluno'].id,
                    'nome': a['aluno'].nome,
                    'selfie': a['selfie_ok'],
                    'cadastro': a['cadastro_ok'],
                    'completo': a['completo'],
                    'foto_url': a['aluno'].foto.url if a['aluno'].foto else None,
                }
                for a in alunos_com_status
            ]
        })
    
    return render(request, 'gestcaptur/formandos_status.html', context)


@login_required
@role_required('gestor')
def importar_nomes_formandos(request, evento_id=None, evento_uuid=None):
    """
    View para importar lista de nomes de formandos via XLSX
    Espera coluna: "nome" ou "nomes" ou qualquer coluna com nomes
    """
    evento = _obter_evento(evento_id=evento_id, evento_uuid=evento_uuid)
    
    # Verificar se evento permite importação
    if not evento.permite_importacao_nomes:
        messages.error(request, "Este evento não permite importação de nomes.")
        return redirect('formandos_status', evento_id=evento_id)
    
    # Verificar permissão
    if not request.user.is_gestor():
        messages.error(request, "Apenas gestores podem importar nomes.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        if 'arquivo' not in request.FILES:
            messages.error(request, "Nenhum arquivo foi enviado.")
            return redirect(request.path)
        
        arquivo = request.FILES['arquivo']
        
        try:
            # Ler arquivo XLSX
            df = pd.read_excel(arquivo)
            
            # Procurar coluna com nomes
            coluna_nome = None
            for col in df.columns:
                if 'nome' in col.lower():
                    coluna_nome = col
                    break
            
            if not coluna_nome:
                messages.error(request, "Arquivo não contém coluna 'nome'. Verifique o arquivo.")
                return redirect(request.path)
            
            # Processar nomes
            nomes_importados = 0
            nomes_duplicados = 0
            
            with transaction.atomic():
                for idx, row in df.iterrows():
                    nome = str(row[coluna_nome]).strip()
                    
                    if not nome or nome.lower() == 'nan':
                        continue
                    
                    # Verificar se já existe
                    if Aluno.objects.filter(evento=evento, nome=nome).exists():
                        nomes_duplicados += 1
                        continue
                    
                    # Criar novo aluno com nome pré-preenchido
                    Aluno.objects.create(
                        evento=evento,
                        nome=nome,
                        codigo_turma=evento.codigo_turma,
                        whatsapp='',  # Será preenchido no cadastro público
                        selfie_realizada=False,
                        cadastro_completo=False,
                    )
                    nomes_importados += 1
            
            messages.success(request, 
                f"✅ {nomes_importados} nomes importados com sucesso! "
                f"({nomes_duplicados} duplicados ignorados)"
            )
            
            return redirect('formandos_status', evento_id=evento_id)
        
        except Exception as e:
            logger.error(f"Erro ao importar nomes: {e}")
            messages.error(request, f"Erro ao processar arquivo: {str(e)}")
            return redirect(request.path)
    
    # GET - Mostrar formulário de importação
    context = {
        'evento': evento,
        'titulo': f"Importar Nomes - {evento.fot}",
    }
    return render(request, 'gestcaptur/importar_nomes.html', context)


@login_required
@evento_permission_required('download_cadastros_evento')
def exportar_formandos(request, evento_id=None, evento_uuid=None):
    """
    Exportar relatório completo de formandos em CSV ou Excel
    Inclui todos os campos do cadastro
    """
    evento = _obter_evento(evento_id=evento_id, evento_uuid=evento_uuid)
    
    alunos = evento.alunos.all().order_by('nome')
    
    # Criar DataFrame com TODOS os campos
    dados = []
    for aluno in alunos:
        dados.append({
            'Nome': aluno.nome,
            'CPF': aluno.cpf or '',
            'Data Nascimento': aluno.data_nascimento.strftime('%d/%m/%Y') if aluno.data_nascimento else '',
            'Email': aluno.email or '',
            'WhatsApp': aluno.whatsapp or '',
            'Telefone Fixo': aluno.telefone_fixo or '',
            'CEP': aluno.cep or '',
            'Endereço': aluno.endereco or '',
            'Número': aluno.numero or '',
            'Complemento': aluno.complemento or '',
            'Bairro': aluno.bairro or '',
            'Cidade': aluno.cidade or '',
            'Estado': aluno.estado or '',
            'Instagram': aluno.instagram or '',
            'Nome Mãe': aluno.nome_mae or '',
            'WhatsApp Mãe': aluno.whatsapp_mae or '',
            'Nome Pai': aluno.nome_pai or '',
            'WhatsApp Pai': aluno.whatsapp_pai or '',
            'Nome Parente': aluno.nome_parente or '',
            'Grau Parentesco': aluno.grau_parentesco or '',
            'WhatsApp Parente': aluno.whatsapp_parente or '',
            'Turma': aluno.codigo_turma or '',
            'Selfie Realizada': '✅ Sim' if (aluno.selfie_realizada or aluno.ident) else '❌ Não',
            'Cadastro Completo': '✅ Sim' if aluno.cadastro_completo else '❌ Não',
            'Data Cadastro': aluno.created_at.strftime('%d/%m/%Y %H:%M') if aluno.created_at else '',
        })
    
    df = pd.DataFrame(dados)
    
    # Gerar arquivo com nome estruturado: {código}-{instituição}-{turma}
    nome_arquivo_base = f"{evento.fot}-{evento.instituicao}-{evento.codigo_turma}"
    
    # Remover caracteres especiais do nome do arquivo
    nome_arquivo_base = unicodedata.normalize('NFKD', nome_arquivo_base)
    nome_arquivo_base = ''.join([c for c in nome_arquivo_base if not unicodedata.combining(c)])
    
    # Gerar arquivo
    filename = f"{nome_arquivo_base}.xlsx"
    response = HttpResponse(content_type='application/vnd.ms-excel')
    df.to_excel(response, index=False, engine='openpyxl')
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@evento_permission_required('download_fotos_evento')
@evento_permission_required('download_cadastros_evento')
def baixar_tudo_formandos(request, evento_id=None, evento_uuid=None):
    """
    Download completo em ZIP com:
    - Pasta: [código] - [instituição]/
    - Todas as fotos dos formandos
    - Arquivo XLSX com dados completos
    
    URLs suportadas:
    - /evento/<uuid>/formandos-download/ (recomendado)
    - /evento/<id>/formandos-download/ (legado)
    """
    import zipfile
    
    evento = _obter_evento(evento_id=evento_id, evento_uuid=evento_uuid)
    
    alunos = evento.alunos.all().order_by('nome')
    
    # 1. Criar DataFrame com dados
    dados = []
    for aluno in alunos:
        dados.append({
            'Nome': aluno.nome,
            'CPF': aluno.cpf or '',
            'Data Nascimento': aluno.data_nascimento.strftime('%d/%m/%Y') if aluno.data_nascimento else '',
            'Email': aluno.email or '',
            'WhatsApp': aluno.whatsapp or '',
            'Telefone Fixo': aluno.telefone_fixo or '',
            'CEP': aluno.cep or '',
            'Endereço': aluno.endereco or '',
            'Número': aluno.numero or '',
            'Complemento': aluno.complemento or '',
            'Bairro': aluno.bairro or '',
            'Cidade': aluno.cidade or '',
            'Estado': aluno.estado or '',
            'Instagram': aluno.instagram or '',
            'Nome Mãe': aluno.nome_mae or '',
            'WhatsApp Mãe': aluno.whatsapp_mae or '',
            'Nome Pai': aluno.nome_pai or '',
            'WhatsApp Pai': aluno.whatsapp_pai or '',
            'Nome Parente': aluno.nome_parente or '',
            'Grau Parentesco': aluno.grau_parentesco or '',
            'WhatsApp Parente': aluno.whatsapp_parente or '',
            'Turma': aluno.codigo_turma or '',
            'Selfie Realizada': '✅ Sim' if (aluno.selfie_realizada or aluno.ident) else '❌ Não',
            'Cadastro Completo': '✅ Sim' if aluno.cadastro_completo else '❌ Não',
            'Data Cadastro': aluno.created_at.strftime('%d/%m/%Y %H:%M') if aluno.created_at else '',
        })
    
    df = pd.DataFrame(dados)
    
    # 2. Preparar nome da pasta
    nome_pasta = evento.codigo_turma or f"{evento.fot} - {evento.instituicao}"
    # Remover caracteres especiais
    nome_pasta_normalizado = unicodedata.normalize('NFKD', nome_pasta)
    nome_pasta_normalizado = ''.join([c for c in nome_pasta_normalizado if not unicodedata.combining(c)])
    
    # 3. Criar ZIP em memória
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Adicionar XLSX na raiz da pasta
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        zip_file.writestr(f"{nome_pasta_normalizado}/_DADOS.xlsx", excel_buffer.getvalue())
        
        # Adicionar fotos
        for aluno in alunos:
            if aluno.foto:
                # Construir caminho da foto
                foto_path = os.path.join(settings.MEDIA_ROOT, str(aluno.foto))
                
                if os.path.exists(foto_path):
                    # Nome do arquivo: nome do aluno em MAIÚSCULAS + extensão original da foto
                    # (evita duplicar quando o arquivo já é salvo como NOME_DO_ALUNO.JPG)
                    nome_arquivo_foto = os.path.basename(str(aluno.foto))
                    extensao = os.path.splitext(nome_arquivo_foto)[1] or '.JPG'
                    nome_limpo_z = f"{aluno.nome.strip().upper()}{extensao}"
                    nome_no_zip = f"{nome_pasta_normalizado}/{nome_limpo_z}"
                    
                    with open(foto_path, 'rb') as f:
                        zip_file.writestr(nome_no_zip, f.read())
    
    # 4. Preparar resposta
    zip_buffer.seek(0)
    filename = f"{nome_pasta_normalizado}.zip"
    
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@role_required('gestor')
def formandos_link_compartilhamento(request, evento_id=None, evento_uuid=None):
    """
    Mostra o link de acesso público e QRCode para compartilhar com formandos
    """
    evento = _obter_evento(evento_id=evento_id, evento_uuid=evento_uuid)
    
    # Verificar permissão
    if not request.user.is_gestor() and evento.coordenador != request.user:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('dashboard')
    
    # Verificar se evento permite selfie
    if not evento.para_selfie:
        messages.error(request, "Este evento não está configurado para selfie e cadastro público.")
        return redirect('dashboard')
    
    # Gerar URL do link público usando UUID (SEGURO)
    from django.urls import reverse
    from django.http import request as http_request
    link_publico = request.build_absolute_uri(
        reverse('formando_selfie_cadastro_uuid', kwargs={'evento_uuid': evento.uuid})
    )
    
    # Gerar QRCode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(link_publico)
    qr.make(fit=True)
    
    # Converter para imagem PNG em base64
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_base64 = base64.b64encode(buffer.read()).decode()
    
    # Dados para template
    context = {
        'evento': evento,
        'link_publico': link_publico,
        'qr_code': f'data:image/png;base64,{qr_base64}',
        'link_curto': link_publico.replace('http://', '').replace('https://', ''),
    }
    
    return render(request, 'gestcaptur/formandos_link_compartilhamento.html', context)


@login_required
def formando_ver_cadastro(request, evento_id=None, evento_uuid=None, aluno_id=None):
    """
    Visualiza o cadastro completo de um formando
    """
    evento = _obter_evento(evento_id=evento_id, evento_uuid=evento_uuid)
    aluno = get_object_or_404(Aluno, id=aluno_id, evento=evento)

    # Verificar permissão (mesma regra do painel formandos_status):
    # Gestor, coordenador do evento, ou quem tem permissão de download/finalização
    eh_gestor = request.user.is_gestor()
    eh_coordenador = evento.coordenador == request.user
    tem_permissao_evento = any(request.user.has_perm(permissao) for permissao in [
        'gestcaptur.download_fotos_evento',
        'gestcaptur.download_cadastros_evento',
        'gestcaptur.finalizar_captura_evento',
    ])
    if not (eh_gestor or eh_coordenador or tem_permissao_evento):
        messages.error(request, "Você não tem permissão para acessar este cadastro.")
        return redirect('dashboard')
    
    context = {
        'evento': evento,
        'aluno': aluno,
    }
    
    # Se requisitado em AJAX, retornar modal HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = f"""
        <div class="modal-header">
            <h5 class="modal-title">Cadastro de {aluno.nome}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
            <div class="row mb-3">
                <div class="col-md-6">
                    <h6 class="text-muted">📋 DADOS PESSOAIS</h6>
                    <p><strong>Nome:</strong> {aluno.nome}</p>
                    <p><strong>CPF:</strong> {aluno.cpf or '-'}</p>
                    <p><strong>Data Nascimento:</strong> {aluno.data_nascimento.strftime('%d/%m/%Y') if aluno.data_nascimento else '-'}</p>
                    <p><strong>Email:</strong> {aluno.email or '-'}</p>
                    <p><strong>Instagram:</strong> {aluno.instagram or '-'}</p>
                </div>
                <div class="col-md-6">
                    <h6 class="text-muted">📱 CONTATOS</h6>
                    <p><strong>WhatsApp:</strong> {aluno.whatsapp or '-'}</p>
                    <p><strong>Telefone Fixo:</strong> {aluno.telefone_fixo or '-'}</p>
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-12">
                    <h6 class="text-muted">🏠 ENDEREÇO</h6>
                    <p><strong>CEP:</strong> {aluno.cep or '-'}</p>
                    <p><strong>Endereço:</strong> {aluno.endereco or '-'}</p>
                    <p><strong>Número:</strong> {aluno.numero or '-'} | <strong>Complemento:</strong> {aluno.complemento or '-'}</p>
                    <p><strong>Bairro:</strong> {aluno.bairro or '-'} | <strong>Cidade:</strong> {aluno.cidade or '-'} | <strong>Estado:</strong> {aluno.estado or '-'}</p>
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <h6 class="text-muted">👨 INFORMAÇÕES DO PAI</h6>
                    <p><strong>Nome:</strong> {aluno.nome_pai or '-'}</p>
                    <p><strong>WhatsApp:</strong> {aluno.whatsapp_pai or '-'}</p>
                </div>
                <div class="col-md-6">
                    <h6 class="text-muted">👩 INFORMAÇÕES DA MÃE</h6>
                    <p><strong>Nome:</strong> {aluno.nome_mae or '-'}</p>
                    <p><strong>WhatsApp:</strong> {aluno.whatsapp_mae or '-'}</p>
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-12">
                    <h6 class="text-muted">👥 CONTATO DE EMERGÊNCIA (PARENTE)</h6>
                    <p><strong>Nome:</strong> {aluno.nome_parente or '-'}</p>
                    <p><strong>Grau de Parentesco:</strong> {aluno.grau_parentesco or '-'}</p>
                    <p><strong>WhatsApp:</strong> {aluno.whatsapp_parente or '-'}</p>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <h6 class="text-muted">📸 STATUS</h6>
                    <p><strong>Selfie Realizada:</strong> {'✅ Sim' if aluno.selfie_realizada or aluno.ident else '❌ Não'}</p>
                    <p><strong>Cadastro Completo:</strong> {'✅ Sim' if aluno.cadastro_completo else '❌ Não'}</p>
                </div>
                <div class="col-md-6">
                    <h6 class="text-muted">📅 DATAS</h6>
                    <p><strong>Data Cadastro:</strong> {aluno.created_at.strftime('%d/%m/%Y %H:%M') if aluno.created_at else '-'}</p>
                    <p><strong>Turma:</strong> {aluno.codigo_turma or '-'}</p>
                </div>
            </div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
        </div>
        """
        return HttpResponse(html)
    
    return render(request, 'gestcaptur/formando_ver_cadastro.html', context)
