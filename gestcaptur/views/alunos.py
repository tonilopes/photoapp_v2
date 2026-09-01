# gestcaptur/views/alunos.py
# Views do domínio 'alunos' (extraídas do antigo views.py monolítico).

import re
from io import BytesIO
import base64
import unicodedata
import uuid
import pandas as pd
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from django.db.models import F, Sum, Count, Q, Avg, ExpressionWrapper, DurationField
from django.db.models import Case, When, Value, CharField
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from gestcaptur.models import Evento, Aluno, Usuario, SessaoFotografica
from gestcaptur.forms import LoginForm, UploadFotoForm, ImportXLSXForm, CriarUsuarioForm, EditarUsuarioForm, EventoForm, AlunoCadastroForm, RoleForm
from gestcaptur.decorators import role_required, group_required, dashboard_gestor_required, coordenador_fotografo_required, evento_permission_required
import logging

logger = logging.getLogger(__name__)

def exportar_fichas(request):
    evento_id = request.GET.get('evento_id')
    alunos = Aluno.objects.filter(token__isnull=False)
    
    # Buscar o objeto Evento usando o evento_id
    evento = None
    if evento_id:
        try:
            evento = Evento.objects.get(id=evento_id)
            alunos = alunos.filter(evento_id=evento_id)
        except Evento.DoesNotExist:
            evento = None
    
    data = []
    for aluno in alunos:
        data.append({
            'Nome': aluno.nome,
            'CPF': aluno.cpf,
            'CEP': aluno.cep,
            'Endereco': aluno.endereco,
            'Numero': aluno.numero,
            'Bairro': aluno.bairro,
            'Complemento': aluno.complemento,
            'Cidade': aluno.cidade,
            'Estado': aluno.estado,
            'Data Nascimento': aluno.data_nascimento.strftime('%d/%m/%Y') if aluno.data_nascimento else '',
            'Telefone Fixo': aluno.telefone_fixo,
            'WhatsApp': aluno.whatsapp,
            'Email': aluno.email,
            'Instagram': aluno.instagram,
            'Nome Pai': aluno.nome_pai,
            'WhatsApp Pai': aluno.whatsapp_pai,
            'Nome Mãe': aluno.nome_mae,
            'WhatsApp Mãe': aluno.whatsapp_mae,
            'Nome Parente': aluno.nome_parente,
            'Grau Parentesco': aluno.grau_parentesco,
            'WhatsApp Parente': aluno.whatsapp_parente,
            'Evento': aluno.evento.tipo_evento,
            'Foto': request.build_absolute_uri(aluno.foto.url) if aluno.foto else '',
            'Status Comparecimento': aluno.status_comparecimento, # NOVO CAMPO
        })
    
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # Gerar nome do arquivo no formato: ano-dia-mês-Fot-Instituicao-tipo_evento.xlsx
    if evento:
        data_evento = evento.data.strftime('%Y-%d-%m')
        
        # Usar o valor real do campo 'fot' do evento
        fot_valor = evento.fot if evento.fot else 'Fot'
        
        # Limpar caracteres especiais
        instituicao = unicodedata.normalize('NFKD', evento.instituicao).encode('ascii', 'ignore').decode('utf-8').replace(' ', '').replace('-', '').replace('_', '').replace('/', '')
        tipo_evento = unicodedata.normalize('NFKD', evento.tipo_evento).encode('ascii', 'ignore').decode('utf-8').replace(' ', '').replace('-', '').replace('_', '').replace('/', '')
        
        # Montar o nome final
        filename = f"{data_evento}-{fot_valor}-{instituicao}-{tipo_evento}.xlsx"
    else:
        filename = "fichas_cadastradas.xlsx"
    
    # Forçar download com explorador
    response = HttpResponse(content_type='application/force-download')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Type'] = 'application/force-download'
    response['Content-Transfer-Encoding'] = 'binary'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Accel-Buffering'] = 'no'
    
    df.to_excel(response, index=False)
    return response


def evento_alunos(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    # Alunos filtrados por evento e ordenados (faltosos no final ou início)
    alunos = Aluno.objects.filter(evento=evento).order_by(
        Case(
            When(status_comparecimento='faltoso', then=1),
            default=0,
            output_field=models.IntegerField()
        ),
        F('foto').asc(nulls_first=True),
        'nome'
    )
    evento_status_message = ""
    can_upload_photos = False

    if evento.status == 'pendente':
        evento_status_message = "Evento ainda não iniciado pelo Coordenador."
    elif evento.status == 'iniciado':
        evento_status_message = "Evento em andamento. Você pode capturar fotos."
        can_upload_photos = True
    elif evento.status == 'finalizado':
        evento_status_message = "Evento encerrado pelo Coordenador. Nenhuma foto pode ser capturada."

    return render(request, 'gestcaptur/evento_alunos.html', {
        'evento': evento,
        'alunos': alunos,
        'evento_status_message': evento_status_message,
        'can_upload_photos': can_upload_photos,
    })


def importar_alunos(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)

    if request.method == 'POST':
        form = ImportXLSXForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['arquivo']

            try:
                df = pd.read_excel(excel_file)
            except Exception as e:
                messages.error(request, f"Erro ao ler o arquivo: {e}")
                return redirect('importar_alunos', evento_id=evento.id)

            # Mapear colunas ignorando maiúsculas, espaços e acentos
            colunas = {col.strip().lower(): col for col in df.columns}

            nome_coluna = colunas.get('nome')

            if not nome_coluna:
                messages.error(request, "Coluna 'nome' não encontrada na planilha.")
                return redirect('importar_alunos', evento_id=evento.id)
            alunos_criados = 0
            alunos_atualizados = 0

            for index, row in df.iterrows():
                nome_aluno = str(row.get(nome_coluna, '')).strip()

                if not nome_aluno:
                    continue

                aluno, created = Aluno.objects.update_or_create(
                    evento=evento,
                    nome=nome_aluno,
                    defaults={'ident': False, 'foto': None, 'status_comparecimento': 'presente'} # NOVO: default para presente
                )

                if created:
                    alunos_criados += 1
                else:
                    alunos_atualizados += 1

            messages.success(request, f"Importação concluída: {alunos_criados} alunos criados, {alunos_atualizados} atualizados.")
            return redirect('evento_alunos', evento_id=evento.id)
    else:
        form = ImportXLSXForm()

    return render(request, 'gestcaptur/importar_alunos.html', {
        'form': form,
        'evento': evento
    })


def confirmar_importacao_alunos(request, evento_id):
    excel_data_b64 = request.session.get('excel_data')
    session_evento_id = request.session.get('evento_id_para_importacao')

    if not excel_data_b64 or session_evento_id != evento_id:
        messages.error(request, "Nenhum arquivo de importação encontrado ou evento inválido. Por favor, reinicie a importação.")
        return redirect('selecionar_evento_para_importar')

    excel_file_bytes = base64.b64decode(excel_data_b64)
    df = pd.read_excel(BytesIO(excel_file_bytes))

    preview_data = []
    for index, row in df.head(10).iterrows():
        preview_data.append({
            'nome': str(row.get('Nome do Aluno', 'N/A')),
        })
    context = {
        'evento_id': evento_id,
        'preview_data': preview_data,
        'total_linhas': len(df),
        'columns': df.columns.tolist()
    }
    return render(request, 'gestcaptur/confirmar_importacao_alunos.html', context)


def salvar_importacao_alunos(request):
    if request.method == 'POST':
        evento_id = request.session.get('evento_id_para_importacao')
        excel_data_b64 = request.session.get('excel_data')

        if not excel_data_b64 or not evento_id:
            messages.error(request, "Erro: Dados de importação não encontrados. Por favor, reinicie o processo.")
            return redirect('selecionar_evento_para_importar')

        evento = get_object_or_404(Evento, id=evento_id)
        excel_file_bytes = base64.b64decode(excel_data_b64)
        df = pd.read_excel(BytesIO(excel_file_bytes))

        alunos_criados = 0
        alunos_atualizados = 0

        for index, row in df.iterrows():
            nome_aluno = str(row.get('Nome do Aluno', '')).strip()
            if not nome_aluno:
                messages.warning(request, f"Linha {index+2} ignorada: Nome do Aluno ausente.")
                continue

            aluno, created = Aluno.objects.update_or_create(
                evento=evento,
                nome=nome_aluno,
                defaults={
                    'ident': False,
                    'foto': None,
                    'status_comparecimento': 'presente' # NOVO: default para presente
                }
            )
            if created:
                alunos_criados += 1
            else:
                alunos_atualizados += 1

        messages.success(request, f"Importação concluída. {alunos_criados} alunos criados, {alunos_atualizados} alunos atualizados para o evento '{evento.tipo_evento}'.")

        del request.session['excel_data']
        del request.session['evento_id_para_importacao']

        return redirect('evento_alunos', evento_id=evento.id)
    return redirect('selecionar_evento_para_importar')


def alunos_crud(request):
    alunos = Aluno.objects.all()
    return render(request, 'gestcaptur/alunos_crud.html', {'alunos': alunos})


def aluno_editar(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    if request.method == 'POST':
        form = AlunoCadastroForm(request.POST, instance=aluno)
        if form.is_valid():
            form.save()
            messages.success(request, "Dados do aluno atualizados.")
            return redirect('alunos_crud')
    else:
        form = AlunoCadastroForm(instance=aluno)
    return render(request, 'gestcaptur/aluno_editar.html', {'form': form, 'aluno': aluno})


def aluno_novo(request):
    evento_id = request.GET.get('evento')
    evento = get_object_or_404(Evento, id=evento_id)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        aluno = Aluno.objects.create(
            nome=nome,
            evento=evento,
            photographer=request.user,
            foto='',  # vazio, será preenchido depois
            status_comparecimento='presente' # NOVO: default para presente
        )
        return redirect('evento_alunos', evento_id=evento.id)
    return render(request, 'gestcaptur/aluno_novo.html', {'evento': evento})


def aluno_visualizar(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    return render(request, 'gestcaptur/aluno_visualizar.html', {'aluno': aluno})


def aluno_excluir(request, aluno_id):
    if not request.user.is_superuser:
        messages.error(request, "Apenas superusuário pode excluir alunos.")
        return redirect('dashboard')

    aluno = get_object_or_404(Aluno, id=aluno_id)
    evento_id = aluno.evento_id
    nome_aluno = aluno.nome

    # Remove arquivo de foto físico antes de excluir o registro
    if aluno.foto:
        try:
            aluno.foto.delete(save=False)
        except Exception:
            pass

    aluno.delete()
    messages.success(request, f"Aluno '{nome_aluno}' excluído com sucesso.")
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('evento_alunos', evento_id=evento_id)


def marcar_aluno_faltoso(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)

    # Verifica permissão do usuário logado para alterar este aluno/evento
    # Gestor pode tudo
    # Coordenador só pode se for coordenador do evento do aluno
    # Fotógrafo só pode se for fotógrafo atribuído ao evento do aluno
    if not (request.user.is_gestor() or
            (request.user.is_coordenador() and aluno.evento.coordenador == request.user) or
            (request.user.is_fotografo() and aluno.evento.fotografos.filter(id=request.user.id).exists())):
        return JsonResponse({'status': 'error', 'message': 'Você não tem permissão para alterar este aluno.'}, status=403)


    if aluno.status_comparecimento == 'faltoso':
        aluno.status_comparecimento = 'presente' # Alternar para presente
        message = f'Aluno {aluno.nome} marcado como PRESENTE novamente.'
    else:
        aluno.status_comparecimento = 'faltoso' # Alternar para faltoso
        message = f'Aluno {aluno.nome} marcado como FALTOSO para este evento.'
    
    aluno.save()
    return JsonResponse({'status': 'ok', 'new_status': aluno.status_comparecimento, 'message': message})


def verificar_cpf_evento(request):
    """Retorna JSON {exists: bool} indicando se CPF já existe no evento."""
    cpf = re.sub(r'\D', '', request.POST.get('cpf', ''))
    evento_id = request.POST.get('evento_id', '').strip()
    aluno_id = request.POST.get('aluno_id', '').strip()  # excluir o próprio aluno ao editar

    if not cpf or not evento_id:
        return JsonResponse({'exists': False})

    try:
        evento = Evento.objects.get(pk=evento_id)
    except (Evento.DoesNotExist, ValueError):
        return JsonResponse({'exists': False})

    if evento.status == 'finalizado':
        return JsonResponse({'exists': False, 'error': 'Evento encerrado'}, status=410)

    qs = Aluno.objects.filter(evento=evento, cpf=cpf)
    if aluno_id:
        try:
            qs = qs.exclude(pk=int(aluno_id))
        except ValueError:
            pass

    return JsonResponse({'exists': qs.exists()})


def gerar_novo_token(request, aluno_id):
    try:
        aluno = get_object_or_404(Aluno, id=aluno_id)
        
        # Só gera novo token se o cadastro estiver completo
        if aluno.cadastro_completo:
            # Gerar novo token
            aluno.token = uuid.uuid4().hex
            aluno.save()
            
            logger.info(f"Novo token gerado para aluno {aluno_id} (cadastro completo)")
            
            return JsonResponse({
                'success': True,
                'novo_token': aluno.token
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Cadastro não está completo'
            })
            
    except Exception as e:
        logger.error(f"Erro ao gerar novo token para aluno {aluno_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
