# 🎯 Recurso de Captura de Selfie - PhotoApp

## 📋 Visão Geral

Um novo recurso foi implementado para capturar selfies de alunos **ANTES** do formulário de cadastro. Isso garante identificação com qualidade através de validações automáticas de iluminação.

### Fluxo de Uso

```
1. Cliente acessa: cliente.photum.com.br:2543/evento/{evento_id}/selfie/
2. Vê página com instruções e webcam
3. Valida iluminação em tempo real
4. Captura selfie
5. Confirma imagem
6. Sistema valida qualidade
7. Redireciona para formulário de cadastro
8. Selfie está pré-preenchida e vinculada ao aluno
```

---

## 🔧 Implementação Técnica

### Arquivos Criados

1. **`gestcaptur/views_selfie.py`**
   - `captura_selfie_publico()` - View para renderizar página de captura
   - `salvar_selfie_publico()` - Endpoint para receber e validar imagem
   - `validar_qualidade_imagem()` - Função para validação de qualidade

2. **`gestcaptur/templates/gestcaptur/captura_selfie.html`**
   - Interface moderna com webcam em tempo real
   - Análise de iluminação contínua
   - Preview da foto capturada
   - Responsivo para mobile

3. **`gestcaptur/templates/gestcaptur/selfie_erro.html`**
   - Página de erro genérica

### URLs Adicionadas

```python
# Captura de selfie pública
path('evento/<int:evento_id>/selfie/', views_selfie.captura_selfie_publico, name='captura_selfie_publico'),
path('selfie/salvar/', views_selfie.salvar_selfie_publico, name='salvar_selfie_publico'),
```

---

## 🚀 Como Usar

### Para Alunos (Link Público)

**URL Public para capturar selfie:**
```
https://cliente.photum.com.br:2543/evento/1/selfie/
```

Onde `1` é o ID do evento.

**Se aluno já existe e tem token:**
```
https://cliente.photum.com.br:2543/evento/1/selfie/?aluno_id=123
```

### Fluxo Completo (Novo Aluno)

1. Aluno acessa link do evento
2. Seleciona "Fazer Selfie para Identificação"
3. Captura foto com webcam
4. Selfie é armazenada temporariamente na sessão
5. Redireciona para `/aluno/cadastro/?evento_id=1`
6. Formulário vê selfie na sessão e pré-preenche
7. Ao salvar o cadastro, selfie é vinculada ao Aluno

---

## ✅ Validações Implementadas

### 1. **Resolução Mínima**
- Mínimo: 320x320 pixels
- Evita fotos muito pequenas/pixeladas

### 2. **Brilho/Iluminação**
- Análise em tempo real durante captura
- Intervalo ideal: 80-230 (escala 0-255)
- **Muito escuro** (< 80): Mensagem "Mude para local mais iluminado"
- **Muito claro** (> 230): Mensagem "Reduza iluminação ou mude de posição"

### 3. **Aspecto (Proporção)**
- Verifica se é mais ou menos quadrado (rosto)
- Ratio entre 0.5 e 2.0

### 4. **Validação Pós-Captura**
- Arquivo base64 válido
- Imagem decodificável
- Dimensões mínimas

---

## 🎨 Interface Responsiva

- ✅ Desktop (600px+)
- ✅ Tablet (600px)
- ✅ Mobile (320px+)
- ✅ Cores vibrantes e intuitivas
- ✅ Instruções claras
- ✅ Indicador de qualidade em tempo real

---

## 🔐 Segurança

- ✅ CSRF exemption apenas para endpoint de upload (`@csrf_exempt`)
- ✅ Validação de tipo de arquivo (apenas imagens)
- ✅ Limite de tamanho base64 implícito (navegador)
- ✅ Sanitização de nomes de arquivo
- ✅ Logs de todas as operações

---

## 📊 Logging

Todas as operações são registradas em `logger`:

```python
logger.info(f"Selfie capturada para aluno {aluno.id} no evento {evento.id}")
logger.error(f"Erro ao processar imagem: {str(e)}")
```

---

## 🔄 Integração com Cadastro Existente

Na view `aluno_cadastro_publico`:

```python
# Verificar se há selfie temporária na sessão
selfie_temporaria = request.session.get('selfie_temporaria')
if selfie_temporaria:
    # Salvar ao cadastro do aluno
    aluno.foto.save(nome_arquivo, ContentFile(base64.b64decode(selfie_temporaria)))
```

---

## 📱 Exemplo de Implementação Completa

### Opção 1: Link Direto (Novo Aluno)
```html
<a href="{% url 'captura_selfie_publico' evento_id=evento.id %}" class="btn btn-primary">
    Fazer Selfie
</a>
```

### Opção 2: Antes do Cadastro (Fluxo Recomendado)
```python
# Na view de seleção de evento
def selecionar_evento(request):
    eventos = Evento.objects.all()
    return render(request, 'selecionar_evento.html', {'eventos': eventos})

# Template oferece duas opções:
# 1. Ir direto para selfie
# 2. Preencher cadastro sem selfie
```

### Opção 3: QR Code
```
Gerar QR Code apontando para:
https://cliente.photum.com.br:2543/evento/1/selfie/
```

---

## 🐛 Troubleshooting

### "Não foi possível acessar a câmera"
- Verificar permissões do navegador
- Usar HTTPS em produção (obrigatório para webcam)
- Testar em navegador moderno (Chrome, Firefox, Safari, Edge)

### "Imagem muito escura"
- Aumentar iluminação frontal
- Mover para próximo de janela/luz
- Ajustar posição

### "Imagem muito clara"
- Reduzir iluminação frontal
- Afastar da luz direta
- Ajustar ângulo

### Selfie não vinculada ao aluno
- Verificar se `aluno_id` foi passado corretamente
- Verificar logs para erros de validação
- Testar salvamento direto sem validação

---

## 📝 Próximas Melhorias (Futuro)

1. **Face Detection**
   - Integrar `face_recognition` ou `OpenCV`
   - Detectar se há rosto na imagem
   - Verificar se rosto é rosto único

2. **Armazenamento Otimizado**
   - Compressão automática de imagens
   - Redimensionamento (ex: 640x480)
   - Armazenamento em CDN (S3/CloudFront)

3. **Retentativas com IA**
   - Sugerir posição de rosto
   - Feedback visual de onde mover câmera
   - Detecção de óculos de sol/chapéu

4. **Múltiplos Eventos**
   - Galeria de selfies capturadas
   - Comparação com selfies anteriores
   - Histórico de tentativas

5. **Autenticação de Dois Fatores**
   - Selfie + Código de SMS/Email
   - Verificação de identidade mais rigorosa

---

## 🎯 Status de Implementação

| Recurso | Status | Notas |
|---------|--------|-------|
| Captura de webcam | ✅ Completo | Funciona em todos os navegadores modernos |
| Validação de iluminação | ✅ Completo | Análise em tempo real |
| Preview | ✅ Completo | Mostra foto antes de enviar |
| Envio para servidor | ✅ Completo | Base64 + validação |
| Vinculação ao aluno | ✅ Completo | Automática se aluno_id fornecido |
| Interface responsiva | ✅ Completo | Mobile, tablet, desktop |
| Logging | ✅ Completo | Rastreamento completo |
| Tratamento de erros | ✅ Completo | Mensagens amigáveis |

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar logs: `/var/log/photoapp/`
2. Testar em navegador console (F12)
3. Validar permissões de câmera do navegador
4. Checar HTTPS em produção

---

**Desenvolvido em:** 19 de fevereiro de 2026  
**Versão:** 1.0.0  
**Compatibilidade:** Django 4.2+ | Python 3.8+

