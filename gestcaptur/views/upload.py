# gestcaptur/views/upload.py
# Views do domínio 'upload' (extraídas do antigo views.py monolítico).

import re
import os
import base64
import unicodedata
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.files.base import ContentFile
from django.views.decorators.http import require_POST
from gestcaptur.models import Evento, Aluno, Usuario, SessaoFotografica
from gestcaptur.decorators import role_required, group_required, dashboard_gestor_required, coordenador_fotografo_required, evento_permission_required
import logging

logger = logging.getLogger(__name__)

def upload_foto(request, aluno_id):
    logger.info(f"Upload foto - Aluno: {aluno_id}, User: {request.user}, Method: {request.method}")
    try:
        data = json.loads(request.body)
        image_data = data['image'].split(',')[1] # Pega apenas a parte base64
        evento_id = data.get('evento_id')

        if not evento_id:
            logger.warning(f"Tentativa de upload de foto sem evento_id para aluno {aluno_id} por {request.user.username}")
            return JsonResponse({'status': 'error', 'message': 'ID do evento é obrigatório.'}, status=400)

        evento = get_object_or_404(Evento, id=evento_id)

        # Verifica se o evento está iniciado
        if evento.status != 'iniciado':
            logger.warning(f"Tentativa de upload de foto em evento não iniciado (ID: {evento_id}, Status: {evento.status}) por {request.user.username}")
            return JsonResponse({
                'status': 'error',
                'message': f'O evento precisa estar "iniciado" pelo coordenador. Status atual: {evento.status}'
            }, status=400)

        aluno = get_object_or_404(Aluno, id=aluno_id, evento=evento)
        
        # Impede upload se o aluno estiver marcado como faltoso
        if aluno.status_comparecimento == 'faltoso':
            logger.warning(f"Tentativa de upload de foto para aluno faltoso (ID: {aluno_id}) por {request.user.username}")
            return JsonResponse({
                'status': 'error',
                'message': 'Não é possível fotografar um aluno marcado como faltoso.'
            }, status=400)


        foto_content = ContentFile(base64.b64decode(image_data), name=f'{aluno.id}_foto.jpg')

        # O código definido pelo Gestor é o nome oficial da pasta do evento.
        subpasta_base = (evento.codigo_turma or f"{evento.fot} - {evento.instituicao} - {evento.tipo_evento} - {evento.data.strftime('%Y-%m-%d')}").strip()
        subpasta_normalizada = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '-', subpasta_base).strip(' .')
        
        nome_aluno_normalizado = unicodedata.normalize('NFKD', aluno.nome).encode('ASCII', 'ignore').decode('ASCII').replace(' ', '_').replace('/', '-')
        
        nome_arquivo = os.path.join(subpasta_normalizada, f"{nome_aluno_normalizado}.jpg")
        # Sobrescreve a foto anterior, se existir
        if aluno.foto and aluno.foto.name:
            # Garante que o arquivo físico seja removido se não houver outras referências
            # (Note: se usar S3 ou similar, a lógica de exclusão pode ser diferente)
            aluno.foto.delete(save=False) # delete=False evita salvar o modelo novamente aqui

        aluno.foto.save(nome_arquivo, foto_content, save=True) # Salva a nova foto e o modelo

        # Atribui o fotógrafo atual ao aluno
        aluno.photographer = request.user
        aluno.save() # Salva novamente para registrar o fotógrafo

        logger.info(f"Foto do aluno {aluno.id} (Evento: {evento_id}) salva com sucesso por {request.user.username}")
        return JsonResponse({
            'status': 'ok',
            'foto_url': aluno.foto.url if aluno.foto else None
        })
    except Aluno.DoesNotExist:
        logger.error(f"Aluno {aluno_id} ou Evento {evento_id} não encontrado para upload de foto por {request.user.username}.")
        return JsonResponse({'status': 'error', 'message': 'Aluno ou evento não encontrado.'}, status=404)
    except Evento.DoesNotExist:
        logger.error(f"Evento {evento_id} não encontrado para upload de foto de aluno {aluno_id} por {request.user.username}.")
        return JsonResponse({'status': 'error', 'message': 'Evento não encontrado.'}, status=404)
    except json.JSONDecodeError:
        logger.error(f"JSON inválido recebido no upload de foto por {request.user.username}.")
        return JsonResponse({'status': 'error', 'message': 'Requisição JSON inválida.'}, status=400)
    except KeyError:
        logger.error(f"Dados incompletos na requisição de upload de foto por {request.user.username}.")
        return JsonResponse({'status': 'error', 'message': 'Dados de imagem ou evento faltando.'}, status=400)
    except Exception as e:
        logger.error(f"Erro inesperado no upload de foto para aluno {aluno_id} (Evento: {evento_id}) por {request.user.username}: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'Erro inesperado no servidor: {str(e)}'}, status=500)


def finalizar_sessao(request, evento_id):
    if request.method == 'POST':
        evento = get_object_or_404(Evento, id=evento_id)
        fotografo = request.user

        data = json.loads(request.body)
        card_number = data.get('card_number')
        action_type = data.get('action_type')
        qtd_fotos_cartao = data.get('qtd_fotos_cartao') # Captura a quantidade de fotos

        if not card_number:
            return JsonResponse({'status': 'error', 'message': 'Número do cartão SD é obrigatório.'}, status=400)
        # Lógica para Finalizar CARTÃO (apenas para fotógrafos)
        if action_type == 'card':
            if not isinstance(qtd_fotos_cartao, int) or qtd_fotos_cartao < 0:
                return JsonResponse({'status': 'error', 'message': 'Quantidade de fotos inválida.'}, status=400)
            
            # Tenta encontrar uma sessão para o fotógrafo, evento e cartão
            # Que ainda não foi marcada como finalizada pelo fotógrafo.
            # Se não existir, cria uma nova.
            sessao, created = SessaoFotografica.objects.get_or_create(
                fotografo=fotografo,
                evento=evento,
                nome_cartao_sd="cartao_padrao", # Verifique se este campo existe no SessaoFotografica
                finalizado_fotografo=False, # Busca sessão ATIVA para esse cartão
                defaults={
                    'inicio_sessao': timezone.now(), # Inicia a sessão se for a primeira vez
                    'qtd_fotos': 0 # Começa com 0 fotos se for nova
                }
            )
            
            # Atualiza a quantidade de fotos e marca a sessão do cartão como finalizada
            sessao.qtd_fotos = qtd_fotos_cartao
            sessao.fim_sessao = timezone.now()
            sessao.finalizado_fotografo = True # Marca como finalizada pelo fotógrafo
            sessao.save()
            messages.success(request, f"Cartão '{card_number}' finalizado com {qtd_fotos_cartao} fotos para o evento '{evento.tipo_evento}'.")
            return JsonResponse({'status': 'ok', 'message': f"Cartão '{card_number}' finalizado com sucesso."})

    return JsonResponse({'status': 'error', 'message': 'Método não permitido.'}, status=405)


def finalizar_cartao_sd(request, evento_id):
    if request.method == 'POST':
        evento = get_object_or_404(Evento, id=evento_id)
        fotografo = request.user
        nome_cartao_sd = request.POST.get('nome_cartao_sd') # Campo que o fotógrafo preenche
        qtd_fotos_cartao = request.POST.get('qtd_fotos_cartao') # Campo que o fotógrafo preenche (ou calculado)

        if not nome_cartao_sd or not qtd_fotos_cartao:
            messages.error(request, "Nome do cartão e quantidade de fotos são obrigatórios.")
            return redirect('fotografo_dashboard') # Ou a página do evento
        try:
            qtd_fotos_cartao = int(qtd_fotos_cartao)
        except ValueError:
            messages.error(request, "Quantidade de fotos deve ser um número válido.")
            return redirect('fotografo_dashboard')

        # Tenta encontrar uma sessão aberta para o fotógrafo, evento e cartão
        sessao, created = SessaoFotografica.objects.get_or_create(
            fotografo=fotografo,
            evento=evento,
            nome_cartao_sd=nome_cartao_sd, # Verifique se este campo existe no SessaoFotografica
            fim_sessao__isnull=True # Busca sessões ainda não finalizadas pelo fotógrafo
        )

        # Atualiza a quantidade de fotos e finaliza a sessão do cartão
        sessao.qtd_fotos = qtd_fotos_cartao
        sessao.fim_sessao = timezone.now()
        sessao.finalizado_fotografo = True # Marca como finalizada pelo fotógrafo
        sessao.save()
        messages.success(request, f"Cartão '{nome_cartao_sd}' finalizado com {qtd_fotos_cartao} fotos para o evento '{evento.tipo_evento}'.")
        return redirect('fotografo_dashboard') # Redireciona de volta para o dashboard do fotógrafo
    return redirect('fotografo_dashboard')
