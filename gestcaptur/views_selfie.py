# gestcaptur/views_selfie.py
# Views para captura de selfie pública

import base64
import json
import os
import uuid
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from PIL import Image
import io
import logging

from .models import Aluno, Evento

logger = logging.getLogger(__name__)


def captura_selfie_publico(request, evento_id, aluno_id=None):
    """
    View pública para captura de selfie
    Fluxo:
    1. Usuário acessa o link
    2. Vê página com instruções e webcam
    3. Captura selfie
    4. Após validação, redireciona para cadastro
    """
    try:
        evento = get_object_or_404(Evento, id=evento_id)
    except Evento.DoesNotExist:
        messages.error(request, "Evento não encontrado.")
        return render(request, 'gestcaptur/selfie_erro.html', {'erro': 'Evento não encontrado'})

    # Se aluno_id for fornecido, buscar o aluno e verificar se já tem selfie
    if evento.status == 'finalizado':
        return render(request, 'gestcaptur/erro.html', {
            'titulo': 'Captura encerrada',
            'mensagem': 'A captura deste evento já foi finalizada e este link não está mais disponível.'
        }, status=410)

    aluno = None
    if aluno_id:
        aluno = get_object_or_404(Aluno, id=aluno_id, evento=evento)
        # Se aluno já tem foto, pode pular para o cadastro
        if aluno.foto:
            messages.info(request, "Você já tem uma selfie capturada. Atualize seus dados se necessário.")
            return redirect('aluno_cadastro_publico', evento_id=evento.id, aluno_id=aluno.id, token=aluno.token)

    context = {
        'evento': evento,
        'evento_id': evento.id,
        'aluno': aluno,
        'aluno_id': aluno_id,
    }

    return render(request, 'gestcaptur/captura_selfie.html', context)


@csrf_exempt
@require_POST
def salvar_selfie_publico(request):
    """
    Endpoint para salvar a selfie capturada
    Recebe imagem base64 e valida qualidade básica
    """
    try:
        data = json.loads(request.body)
        image_data_base64 = data.get('image')
        evento_id = data.get('evento_id')
        aluno_id = data.get('aluno_id')  # Opcional

        logger.info(f"salvar_selfie_publico recebido: evento_id={evento_id}, aluno_id={aluno_id}, imagem_size={len(image_data_base64) if image_data_base64 else 0}")

        if not image_data_base64 or not evento_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Imagem ou ID do evento não fornecido'
            }, status=400)

        # Buscar evento
        evento = get_object_or_404(Evento, id=evento_id)
        if evento.status == 'finalizado':
            return JsonResponse({
                'status': 'error',
                'message': 'A captura deste evento já foi finalizada.'
            }, status=410)

        # Decodificar imagem base64
        try:
            # Remove o prefixo 'data:image/...' se existir
            if 'base64,' in image_data_base64:
                image_data_base64 = image_data_base64.split('base64,')[1]

            image_bytes = base64.b64decode(image_data_base64)
            image = Image.open(io.BytesIO(image_bytes))

            # Validações básicas da imagem
            # 1. Verificar resolução mínima (selfie deve ter resolução razoável)
            width, height = image.size
            if width < 320 or height < 320:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Imagem com resolução muito baixa. Use câmera melhor iluminada ou aumentar zoom.'
                }, status=400)

            # 2. Verificar contraste básico (para verificar se está bem iluminada)
            # Converter para escala de cinza para análise
            gray_image = image.convert('L')
            pixels = list(gray_image.getdata())
            
            # Calcular brilho médio
            avg_brightness = sum(pixels) / len(pixels)
            
            # Se muito escuro ou muito claro, alertar
            if avg_brightness < 80:
                return JsonResponse({
                    'status': 'warning',
                    'message': 'Imagem muito escura. Mude-se para um local melhor iluminado.',
                    'brightness': avg_brightness
                }, status=400)
            
            if avg_brightness > 230:
                return JsonResponse({
                    'status': 'warning',
                    'message': 'Imagem muito clara/superexposta. Reduza a iluminação ou mude de posição.',
                    'brightness': avg_brightness
                }, status=400)

            # Se aluno_id fornecido, tentar ligar selfie ao aluno
            if aluno_id:
                aluno = Aluno.objects.get(id=aluno_id, evento=evento)
                
                # Gerar nome do arquivo
                nome_arquivo = f"selfie_{aluno.id}_{uuid.uuid4().hex[:8]}.jpg"
                
                # Salvar selfie no modelo
                foto_content = ContentFile(image_bytes, name=nome_arquivo)
                aluno.foto = foto_content
                aluno.selfie_realizada = True
                aluno.save()

                logger.info(f"Selfie capturada para aluno {aluno.id} no evento {evento.id}")

                return JsonResponse({
                    'status': 'ok',
                    'message': 'Selfie capturada com sucesso!',
                    'aluno_id': aluno.id,
                    'token': aluno.token,
                    'redirect_url': reverse('aluno_cadastro_publico', kwargs={
                        'evento_id': evento.id,
                        'aluno_id': aluno.id,
                        'token': aluno.token
                    })
                })
            else:
                # Selfie será salva quando aluno preencher o cadastro
                # Armazena em sessão temporariamente
                request.session['selfie_temporaria_base64'] = image_data_base64
                request.session['selfie_evento_id'] = str(evento_id)
                request.session['selfie_tipo'] = 'publico'  # Marcador para identificar tipo de selfie
                request.session.modified = True

                logger.info(f"Selfie temporária capturada e armazenada em sessão para evento {evento.id}")

                return JsonResponse({
                    'status': 'ok',
                    'message': 'Selfie capturada com sucesso! Redirecionando para cadastro...',
                    'redirect_url': f'/aluno/cadastro/?evento={evento_id}',
                    'aluno_id': None,
                    'token': None
                })

        except Image.UnidentifiedImageError:
            logger.error("Arquivo enviado não é uma imagem válida")
            return JsonResponse({
                'status': 'error',
                'message': 'Arquivo não é uma imagem válida'
            }, status=400)
        except Aluno.DoesNotExist:
            logger.error(f"Aluno {aluno_id} não encontrado no evento {evento_id}")
            return JsonResponse({
                'status': 'error',
                'message': 'Aluno não encontrado neste evento'
            }, status=404)
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': f'Erro ao processar imagem: {str(e)}'
            }, status=500)

    except Evento.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Evento não encontrado'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Requisição JSON inválida'
        }, status=400)
    except Exception as e:
        logger.error(f"Erro inesperado ao salvar selfie: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Erro no servidor: {str(e)}'
        }, status=500)


def validar_qualidade_imagem(image):
    """
    Valida a qualidade da imagem capturada
    Retorna: (True/False, mensagem)
    """
    try:
        width, height = image.size
        
        # Verificar resolução
        if width < 320 or height < 320:
            return False, "Resolução muito baixa"

        # Verificar aspecto (deve ser rosto)
        aspect_ratio = width / height
        if aspect_ratio < 0.5 or aspect_ratio > 2:
            return False, "Proporcionalidade incorreta para um rosto"

        # Verificar iluminação
        gray = image.convert('L')
        pixels = list(gray.getdata())
        brightness = sum(pixels) / len(pixels)

        if brightness < 80:
            return False, "Imagem muito escura"
        elif brightness > 230:
            return False, "Imagem muito clara"

        return True, "Qualidade OK"

    except Exception as e:
        logger.error(f"Erro ao validar imagem: {str(e)}")
        return False, f"Erro na validação: {str(e)}"


# ========================================
# 🔒 NOVO FLUXO: SELFIE OBRIGATÓRIA PÓS-CADASTRO
# ========================================

def aluno_selfie_obrigatoria(request, aluno_id, token):
    """
    NOVO FLUXO: Após cadastro completo, aluno DEVE capturar selfie
    - Recebe aluno_id e token para validação
    - Exibe interface de captura obrigatória
    - Após captura, salva e redireciona para sucesso
    
    URL: /aluno/selfie/<aluno_id>/<token>/
    """
    try:
        aluno = get_object_or_404(Aluno, id=aluno_id, token=token)
    except Aluno.DoesNotExist:
        messages.error(request, "Acesso inválido. Link expirado ou incorreto.")
        return render(request, 'gestcaptur/erro.html', {'mensagem': 'Link inválido ou expirado'})

    if aluno.evento.status == 'finalizado':
        return render(request, 'gestcaptur/erro.html', {
            'titulo': 'Captura encerrada',
            'mensagem': 'A captura deste evento já foi finalizada e este link não está mais disponível.'
        }, status=410)
    
    context = {
        'aluno': aluno,
        'aluno_id': aluno.id,
        'aluno_token': token,
        'evento': aluno.evento,
        'titulo': f'Capte sua Selfie - {aluno.nome}',
        'obrigatoria': True,  # Indica que é obrigatória
    }
    
    return render(request, 'gestcaptur/aluno_selfie_obrigatoria.html', context)


def salvar_selfie_obrigatoria(request):
    """
    Salva selfie capturada no novo fluxo (após cadastro completo)
    
    POST com: aluno_id, token, image_data (base64)
    Retorna: JSON com sucesso e redirect_url
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)
    
    try:
        aluno_id = request.POST.get('aluno_id')
        token = request.POST.get('token')
        image_data = request.POST.get('image_data')
        
        logger.info(f"🤳 Salvando selfie obrigatória para aluno {aluno_id}")
        
        # Validar tokens
        if not aluno_id or not token or not image_data:
            return JsonResponse({
                'success': False,
                'error': 'Dados incompletos'
            }, status=400)
        
        # Buscar aluno com token para segurança
        aluno = get_object_or_404(Aluno, id=aluno_id, token=token)
        
        # Decodificar imagem base64
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Validar qualidade da imagem
        img = Image.open(io.BytesIO(image_bytes))
        is_valid, msg = validar_qualidade_imagem(img)
        
        if not is_valid:
            logger.warning(f"⚠️ Selfie rejeitada para {aluno.nome}: {msg}")
            return JsonResponse({
                'success': False,
                'error': f'Selfie rejeitada: {msg}. Tente novamente.'
            }, status=400)
        
        # Salvar foto no aluno
        # 🔒 NOVO: "NOME COMPLETO.JPG" (maiúsculas com espaços)
        nome_arquivo = f"{aluno.nome.strip().upper()}.JPG"
        
        aluno.foto = ContentFile(image_bytes, name=nome_arquivo)
        aluno.selfie_realizada = True
        aluno.save()
        
        logger.info(f"✅ Selfie salva com sucesso para {aluno.nome} (arquivo: {nome_arquivo})")
        
        return JsonResponse({
            'success': True,
            'message': 'Selfie capturada com sucesso!',
            'redirect_url': reverse('aluno_cadastro_sucesso')
        })
        
    except Aluno.DoesNotExist:
        logger.error(f"❌ Aluno não encontrado: {aluno_id}")
        return JsonResponse({
            'success': False,
            'error': 'Aluno não encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"❌ Erro ao salvar selfie obrigatória: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Erro ao processar selfie: {str(e)}'
        }, status=500)
