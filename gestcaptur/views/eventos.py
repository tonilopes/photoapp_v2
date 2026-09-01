# gestcaptur/views/eventos.py
# Views do domínio 'eventos' (extraídas do antigo views.py monolítico).

from io import BytesIO
import os
import zipfile
import unicodedata
import pandas as pd
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from django.urls import reverse
from django.views.decorators.http import require_POST
from gestcaptur.models import Evento, Aluno, Usuario, SessaoFotografica
from gestcaptur.forms import LoginForm, UploadFotoForm, ImportXLSXForm, CriarUsuarioForm, EditarUsuarioForm, EventoForm, AlunoCadastroForm, RoleForm
from gestcaptur.decorators import role_required, group_required, dashboard_gestor_required, coordenador_fotografo_required, evento_permission_required
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def finalizar_captura_gestor(request, evento_id):
    """Finaliza a captura e invalida os fluxos públicos do evento."""
    evento = get_object_or_404(Evento, id=evento_id)

    if evento.status == 'finalizado':
        return JsonResponse({
            'status': 'error',
            'message': 'Este evento já está finalizado.'
        }, status=400)

    evento.status = 'finalizado'
    evento.hora_fim = timezone.now()
    evento.save(update_fields=['status', 'hora_fim', 'updated_at'])

    SessaoFotografica.objects.filter(
        evento=evento,
        finalizado_evento=False,
    ).update(
        finalizado_evento=True,
        finalizado_fotografo=True,
        fim_sessao=timezone.now(),
    )

    return JsonResponse({
        'status': 'ok',
        'message': 'Captura finalizada. Os links públicos e QR codes deste evento foram desativados.',
    })


def alterar_status_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id, coordenador=request.user)

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'iniciar' and evento.status == 'pendente':
            evento.status = 'iniciado'
            evento.save()
            messages.success(request, 'Evento iniciado com sucesso.')
        
        elif acao == 'finalizar' and evento.status == 'iniciado':
            evento.status = 'finalizado'
            evento.save()
            messages.success(request, 'Evento finalizado com sucesso.')

    return redirect('dashboard_coordenador')


def criar_evento(request):
    if request.method == 'POST':
        print("🔍 DEBUG VIEW - Dados POST recebidos:")
        for key, value in request.POST.items():
            print(f"  {key}: '{value}'")
        
        form = EventoForm(request.POST)
        print(f"🔍 DEBUG VIEW - Form criado: {form}")
        if form.is_valid():
            print("✅ Form válido, salvando...")            
            evento = form.save(commit=False)
            
            # ✅ CORRIGIDO: Definir campos adicionais antes de salvar
            if not hasattr(evento, 'created_by'):
                # Se não tem campo created_by, apenas salvar sem gestor
                pass
            
            evento.save()
            form.save_m2m()  # Salva as relações ManyToMany, como fotografos

            # Lógica para atribuir o coordenador como fotógrafo, se marcado
            coordenador_selecionado = form.cleaned_data.get('coordenador')
            coordenador_tambem_fotografo = form.cleaned_data.get('coordenador_tambem_fotografo')

            if coordenador_selecionado and coordenador_tambem_fotografo:
                evento.fotografos.add(coordenador_selecionado)  # Adiciona o coordenador como fotógrafo
            # ✅ CORRIGIDO: Só adicionar gestor se o campo existir
            if hasattr(evento, 'gestores'):
                evento.gestores.add(request.user)
            elif hasattr(evento, 'created_by'):
                evento.created_by = request.user
                evento.save()
            print(f"✅ Evento criado com sucesso: {evento}")
            messages.success(request, f"Evento '{evento.tipo_evento}' criado com sucesso!")

            # Se o evento estiver marcado como para selfie, gerar link público e exibir
            try:
                if getattr(evento, 'para_selfie', False):
                    from django.urls import reverse
                    link = request.build_absolute_uri(reverse('captura_selfie_publico', args=[evento.id]))
                    messages.info(request, f"Link público para captura de selfie: {link}")
            except Exception as e:
                print(f"⚠️ Erro ao gerar link de selfie: {e}")
            return redirect('dashboard')
        else:
            # Debug dos erros quando form é inválido
            print("❌ Form inválido!")
            print(f"🔍 Form errors: {form.errors}")
            print(f"🔍 Form non_field_errors: {form.non_field_errors()}")
            
            # Mostrar erros específicos de cada campo
            for field_name, errors in form.errors.items():
                print(f"🔍 Erro no campo '{field_name}': {errors}")
                for error in errors:
                    messages.error(request, f"Erro no campo {field_name}: {error}")
    else:
        form = EventoForm()
    
    return render(request, 'gestcaptur/criar_evento.html', {'form': form})


def listar_eventos(request):
    """
    Lista todos os eventos para o Gestor com filtros e paginação
    """
    # A verificação de permissão agora é feita pelo decorador @group_required('Gestor')
    
    # Filtros
    eventos = Evento.objects.all().order_by('-data', '-horario')
    
    # Filtro por tipo de evento
    tipo_evento = request.GET.get('tipo_evento', '').strip()
    if tipo_evento:
        eventos = eventos.filter(tipo_evento__icontains=tipo_evento)
    
    # Filtro por empresa
    empresa = request.GET.get('empresa', '').strip()
    if empresa:
        eventos = eventos.filter(empresa__icontains=empresa)
    
    # Filtro por instituição
    instituicao = request.GET.get('instituicao', '').strip()
    if instituicao:
        eventos = eventos.filter(instituicao__icontains=instituicao)
    
    # Filtro por status
    status = request.GET.get('status', '').strip()
    if status:
        eventos = eventos.filter(status=status)
    
    # Filtro por data
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            eventos = eventos.filter(data__gte=data_inicio)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            eventos = eventos.filter(data__lte=data_fim)
        except ValueError:
            pass
    
    # Paginação
    paginator = Paginator(eventos, 20)  # 20 eventos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_eventos = eventos.count()
    eventos_pendentes = eventos.filter(status='pendente').count()
    eventos_andamento = eventos.filter(status='iniciado').count()
    eventos_finalizados = eventos.filter(status='finalizado').count()
    
    context = {
        'page_obj': page_obj,
        'eventos': page_obj.object_list,
        'total_eventos': total_eventos,
        'eventos_pendentes': eventos_pendentes,
        'eventos_andamento': eventos_andamento,
        'eventos_finalizados': eventos_finalizados,
        'filtros': {
            'tipo_evento': tipo_evento,
            'empresa': empresa,
            'instituicao': instituicao,
            'status': status,
            'data_inicio': request.GET.get('data_inicio', ''),
            'data_fim': request.GET.get('data_fim', ''),
        }
    }
    
    return render(request, 'gestcaptur/listar_eventos.html', context)


def editar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.save()
            form.save_m2m() # Salva as relações ManyToMany

            # Lógica para atribuir/remover o coordenador como fotógrafo
            coordenador_selecionado = form.cleaned_data.get('coordenador')
            coordenador_tambem_fotografo = form.cleaned_data.get('coordenador_tambem_fotografo')
            if coordenador_selecionado and coordenador_tambem_fotografo:
                evento.fotografos.add(coordenador_selecionado) # Garante que está adicionado
            elif coordenador_selecionado and not coordenador_tambem_fotografo:
                # Se desmarcou, remove o coordenador da lista de fotógrafos (se ele estava lá)
                if coordenador_selecionado in evento.fotografos.all():
                    evento.fotografos.remove(coordenador_selecionado)

            messages.success(request, "Evento atualizado com sucesso.")
            return redirect('dashboard')
    else:
        form = EventoForm(instance=evento)
    return render(request, 'gestcaptur/editar_evento.html', {
        'form': form,
        'evento': evento,
    })


def importar_eventos(request):
    mensagem = None
    if request.method == 'POST':
        form = ImportXLSXForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['arquivo']
            try:
                df = pd.read_excel(excel_file)
            except Exception as e:
                messages.error(request, f"Erro ao ler o arquivo: {e}")
                return redirect('importar_eventos')

            eventos_criados = 0
            eventos_atualizados = 0
            for index, row in df.iterrows():
                # Pegue todos os campos do modelo
                campos = {
                    'fot': str(row.get('fot', '')).strip(),
                    'instituicao': str(row.get('instituicao', '')).strip(),
                    'curso': str(row.get('curso', '')).strip(),
                    'empresa': str(row.get('empresa', '')).strip(),
                    'tipo_evento': str(row.get('tipo_evento', '')).strip(),
                    'observacoes': str(row.get('observacoes', '')).strip(),
                    'local': str(row.get('local', '')).strip(),
                    'endereco': str(row.get('endereco', '')).strip(),
                    'horario': str(row.get('horario', '')).strip(),
                }
                data_evento_str = str(row.get('data', '')).strip()
                if not campos['tipo_evento'] or not campos['empresa'] or not data_evento_str:
                    messages.warning(request, f"Linha {index+2} ignorada: Dados incompletos.")
                    continue
                try:
                    data_evento = pd.to_datetime(data_evento_str, dayfirst=True, errors='coerce').date()
                    if pd.isna(data_evento):
                        raise ValueError("Data inválida")
                except Exception:
                    messages.warning(request, f"Linha {index+2} ignorada: Data inválida.")
                    continue
                # Adicione a data separadamente
                campos['data'] = data_evento

                evento, created = Evento.objects.update_or_create(
                    tipo_evento=campos['tipo_evento'],
                    empresa=campos['empresa'],
                    data=campos['data'],
                    defaults=campos
                )
                if created:
                    eventos_criados += 1
                else:
                    eventos_atualizados += 1

            messages.success(
                request,
                f"Importação concluída: {eventos_criados} criados, {eventos_atualizados} atualizados."
            )
            return redirect('dashboard')
        else:
            messages.error(request, "Erro no formulário.")
    else:
        form = ImportXLSXForm()

    return render(request, 'gestcaptur/importar_eventos.html', {'form': form})


def exportar_eventos(request):
    tipo_evento_filter = request.GET.get('tipo_evento')
    empresa_filter = request.GET.get('empresa')
    data_filter = request.GET.get('data')

    eventos = Evento.objects.all()

    if tipo_evento_filter:
        eventos = eventos.filter(tipo_evento__icontains=tipo_evento_filter)
    if empresa_filter:
        eventos = eventos.filter(empresa__icontains=empresa_filter)
    if data_filter:
        eventos = eventos.filter(data=data_filter)

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    df_data = []
    for evento in eventos:
        alunos_evento = Aluno.objects.filter(evento=evento).count()
        alunos_com_foto = Aluno.objects.filter(evento=evento, foto__isnull=False).count()
        df_data.append({
            'ID Evento': evento.id,
            'Tipo Evento': evento.tipo_evento,
            'Empresa': evento.empresa,
            'Data Evento': evento.data.strftime('%d/%m/%Y'),
            'Data Criação': evento.created_at.strftime('%d/%m/%Y %H:%M'),
            'Total Alunos': alunos_evento,
            'Alunos com Foto': alunos_com_foto,
            'Status Evento': evento.status,
            'Hora Início': evento.hora_inicio.strftime('%H:%M:%S') if evento.hora_inicio else 'N/A',
            'Hora Fim': evento.hora_fim.strftime('%H:%M:%S') if evento.hora_fim else 'N/A',
        })

    if not df_data:
        df = pd.DataFrame(columns=['ID Evento', 'Tipo Evento', 'Empresa', 'Data Evento',
                                   'Data Criação', 'Total Alunos', 'Alunos com Foto',
                                   'Status Evento', 'Hora Início', 'Hora Fim'])
    else:
        df = pd.DataFrame(df_data)
    df.to_excel(writer, sheet_name='Eventos', index=False)
    writer.close()
    output.seek(0)

    filename = f"eventos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def atribuir_fotografo(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    fotografos = Usuario.objects.filter(groups__name='Fotógrafo').exclude(eventos_atribuidos=evento) # Filtra por grupo
    # Alternativamente, você pode filtrar pelo campo 'role' se preferir:
    # fotografos = Usuario.objects.filter(role='fotografo').exclude(eventos_atribuidos=evento)

    if request.method == 'POST':
        fotografo_id = request.POST.get('fotografo_id')
        fotografo = get_object_or_404(Usuario, id=fotografo_id)
        evento.fotografos.add(fotografo)
        messages.success(request, f"Fotógrafo {fotografo.username} atribuído ao evento.")
        return redirect('dashboard')
    return render(request, 'gestcaptur/atribuir_fotografo.html', {
        'evento': evento,
        'fotografos': fotografos,
    })


def deletar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    if request.method == 'POST':
        evento.delete()
        messages.success(request, "Evento excluído com sucesso.")
        return redirect('dashboard')
    return render(request, 'gestcaptur/deletar_evento.html', {'evento': evento})


def selecionar_evento_para_importar(request):
    eventos = Evento.objects.all().order_by('-data')
    return render(request, 'gestcaptur/selecionar_evento_para_importar.html', {'eventos': eventos})


def iniciar_evento_coordenador(request, evento_id):
    """
    Permite que Coordenador OU Gestor inicie um evento
    """
    print(f"=== INICIAR EVENTO DEBUG ===")
    print(f"User: {request.user.username}")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"User groups: {[g.name for g in request.user.groups.all()]}")
    print(f"Evento ID: {evento_id}")
    print(f"Request method: {request.method}")
    
    if request.method == 'POST':
        try:
            # Verificar permissão usando grupos
            user_groups = [g.name for g in request.user.groups.all()]
            is_gestor = 'Gestor' in user_groups
            is_coordenador = 'Coordenador' in user_groups
            
            print(f"Verificação por grupos - Gestor: {is_gestor}, Coordenador: {is_coordenador}")
            
            if not (is_gestor or is_coordenador):
                print(f"❌ Usuário sem permissão. Grupos: {user_groups}")
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Você não tem permissão para iniciar eventos. Grupos: {user_groups}'
                }, status=403)
            
            print(f"✅ Usuário autorizado")
            
            # Buscar evento
            try:
                evento = get_object_or_404(Evento, id=evento_id)
                print(f"✅ Evento encontrado: {evento.tipo_evento} - Status atual: {evento.status}")
            except Exception as e:
                print(f"❌ Erro ao buscar evento: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Evento não encontrado: {e}'
                }, status=404)
            
            # Verificar se o evento pode ser iniciado
            if evento.status == 'iniciado':
                print(f"❌ Evento já iniciado")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Este evento já foi iniciado.'
                })
            
            if evento.status == 'finalizado':
                print(f"❌ Evento já finalizado")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Este evento já foi finalizado.'
                })
            
            # Iniciar o evento
            try:
                print(f"🔄 Iniciando evento...")
                evento.status = 'iniciado'
                evento.save()
                print(f"✅ Evento {evento.id} salvo com status 'iniciado'")
            except Exception as e:
                print(f"❌ Erro ao salvar evento: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Erro ao salvar evento: {e}'
                }, status=500)
            
            # Criar sessão fotográfica se não existir
            try:
                print(f"🔄 Criando/verificando sessão fotográfica...")
                
                sessao, created = SessaoFotografica.objects.get_or_create(
                    evento=evento,
                    defaults={
                        'inicio_sessao': timezone.now(),  # Campo correto!
                        'finalizado_fotografo': False,
                        'finalizado_evento': False,
                        'qtd_fotos': 0,
                        'numero_cartao': '',
                        'last_activity': timezone.now()
                    }
                )
                
                if created:
                    print(f"✅ Nova sessão fotográfica criada para evento {evento.id}")
                else:
                    print(f"✅ Sessão fotográfica já existia para evento {evento.id}")
                    
            except Exception as sessao_error:
                print(f"⚠️ Erro ao criar/verificar sessão: {sessao_error}")
                # Não retornar erro, apenas logar
            
            # Adicionar mensagem de sucesso
            try:
                print(f"🔄 Adicionando mensagem de sucesso...")
                messages.success(request, f"Evento '{evento.tipo_evento}' marcado como 'Em Andamento'. Fotógrafos já podem iniciar a captura.")
                print(f"✅ Mensagem adicionada")
            except Exception as msg_error:
                print(f"⚠️ Erro ao adicionar mensagem: {msg_error}")
                # Não retornar erro, apenas logar
            
            print(f"✅ Evento {evento.id} iniciado com sucesso por {request.user.username}")
            
            # Retornar sucesso
            response_data = {
                'status': 'ok',
                'message': 'Evento iniciado com sucesso! Fotógrafos já podem fotografar.',
                'new_status': 'iniciado'
            }
            print(f"✅ Retornando resposta: {response_data}")
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"❌ ERRO GERAL: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': f'Erro interno: {str(e)}'
            }, status=500)
    
    print(f"❌ Método não permitido: {request.method}")
    return JsonResponse({
        'status': 'error',
        'message': 'Método não permitido'
    }, status=405)


def encerrar_evento_coordenador(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)

    fotografos_resumo = []
    total_fotos_evento = 0

    for fotografo in evento.fotografos.all():
        # Calcula o total real de fotos deste fotógrafo neste evento
        total_fotos = Aluno.objects.filter(
            evento=evento,
            photographer=fotografo
        ).exclude(foto='').exclude(foto__isnull=True).count()

        # Atualiza todas as sessões deste fotógrafo para este evento
        sessoes_fotografo = SessaoFotografica.objects.filter(fotografo=fotografo, evento=evento)
        for sessao in sessoes_fotografo:
            sessao.qtd_fotos = total_fotos
            sessao.save()
        # Monta os dados dos cartões/sessões
        cards_data = []
        for sessao in sessoes_fotografo:
            cards_data.append({
                'qtd_fotos': sessao.qtd_fotos,
                'inicio_sessao': sessao.inicio_sessao,
                'fim_sessao': sessao.fim_sessao,
            })

        fotografos_resumo.append({
            'fotografo': fotografo,
            'total_fotos': total_fotos,
            'cards': cards_data,
        })
        total_fotos_evento += total_fotos

    context = {
        'evento': evento,
        'fotografos_resumo': fotografos_resumo,
        'total_fotos_evento': total_fotos_evento,
    }
    return render(request, 'gestcaptur/encerrar_evento_coordenador.html', context)


def confirmar_encerrar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    if request.method == 'POST':
        if evento.status == 'iniciado' or evento.status == 'pendente':
            evento.status = 'finalizado'
            evento.hora_fim = timezone.now()
            evento.save()

            SessaoFotografica.objects.filter(evento=evento, finalizado_evento=False).update(
                finalizado_evento=True,
                finalizado_fotografo=True,
                fim_sessao=timezone.now()
            )

            messages.success(request, f"Evento '{evento.tipo_evento}' finalizado com sucesso. Todos os fotógrafos foram notificados do encerramento.")
        else:
            messages.info(request, f"Evento '{evento.tipo_evento}' já está finalizado.")
        return redirect('dashboard_coordenador')
    
    return redirect('encerrar_evento_coordenador', evento_id=evento.id)


def exportar_fotos_evento(request):
    evento_id = request.GET.get('evento_id')
    if not evento_id:
        return HttpResponse("Evento não especificado.", status=400)
    
    evento = get_object_or_404(Evento, id=evento_id)
    alunos = Aluno.objects.filter(evento=evento).exclude(foto__isnull=True).exclude(foto='')

    # Monta o nome da pasta e do zip
    pasta_nome = unicodedata.normalize('NFKD', f"{evento.fot} - {evento.instituicao} - {evento.tipo_evento} - {evento.data.strftime('%d-%m-%Y')}").encode('ascii', 'ignore').decode('utf-8').replace('/', '-')
    zip_filename = f"{pasta_nome}.zip"
    zip_path = os.path.join(settings.MEDIA_ROOT, zip_filename)
    
    # Certifique-se de que o diretório MEDIA_ROOT existe
    if not os.path.exists(settings.MEDIA_ROOT):
        os.makedirs(settings.MEDIA_ROOT)

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for aluno in alunos:
            # Verifica se o arquivo de foto existe antes de tentar adicioná-lo
            if aluno.foto and os.path.exists(aluno.foto.path):
                ext = os.path.splitext(aluno.foto.path)[1]
                # Nome do arquivo dentro do zip
                # Garante que o nome do arquivo não contenha caracteres especiais e seja único
                aluno_nome_seguro = unicodedata.normalize('NFKD', aluno.nome).encode('ascii', 'ignore').decode('utf-8').replace(' ', '_').replace('/', '-')
                arcname = f"{pasta_nome}/{aluno_nome_seguro}_{aluno.id}{ext}"
                zipf.write(aluno.foto.path, arcname)
            else:
                logger.warning(f"Foto não encontrada para o aluno {aluno.nome} (ID: {aluno.id}). Pulando.")

    # Ler arquivo e criar response
    with open(zip_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/force-download')
        response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
        response['Content-Type'] = 'application/force-download'
        response['Content-Transfer-Encoding'] = 'binary'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        response['X-Accel-Buffering'] = 'no'                                                                                                                                                                         
    
    # Limpar arquivo temporário
    os.remove(zip_path)
    return response
