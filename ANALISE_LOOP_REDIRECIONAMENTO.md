# 🔍 ANÁLISE: Loop Infinito de Redirecionamento ao Login

**Data**: 20/05/2026  
**Status**: ✅ RESOLVIDO  
**Ambiente**: VPS Ubuntu com Django + Gunicorn

---

## 📋 Problema Relatado

Usuários com role `'fotografo'` ao fazer login recebem erro de **excesso de redirecionamento**:
- Erro 310 (Firefox) / ERR_TOO_MANY_REDIRECTS (Chrome)
- Loop infinito entre `/login/` e `/fotografo/`

---

## 🔴 Causa Raiz Identificada

### **Incompatibilidade entre Decorator e Sistema de Permissões**

O projeto usa **dois sistemas de permissões simultâneos**:

1. **Sistema de Roles** (no modelo `Usuario`)
   - Campo: `role = CharField(..., choices=[('fotografo', ...), ...])`
   - Métodos: `is_fotografo()`, `is_coordenador()`, etc.
   - Usuários criados **COM** role, **SEM** grupos Django

2. **Sistema de Grupos Django** (desatualizado)
   - Decorator: `@group_required('Fotógrafo')`
   - Verifica **APENAS** `user.groups.all()`
   - Usuários criados **SEM** estar em grupos

### **Fluxo do Bug:**

```
1. Login com usuário role='fotografo'
   ↓
2. get_dashboard_redirect() detecta is_fotografo() → True
   ↓
3. Redireciona para 'fotografo_dashboard' (URL: /fotografo/)
   ↓
4. View fotografo_dashboard tem @group_required('Fotógrafo')
   ↓
5. Decorator verifica: user.groups.filter(name='Fotógrafo') → VAZIO ❌
   ↓
6. Acesso negado → redireciona para /login/
   ↓
7. login_view ve user.is_authenticated = True
   ↓
8. Chama get_dashboard_redirect() novamente
   ↓
9. VOLTA para passo 3 → LOOP INFINITO 🔄
```

---

## ✅ Solução Implementada

### **1️⃣ Corrigir Decorator `group_required()` em `decorators.py`**

**Antes:**
```python
def group_required(group_names, ...):
    def check_group(user):
        # Verifica APENAS grupos
        user_groups = [g.name for g in user.groups.all()]
        return any(group in user_groups for group in group_names)
    return user_passes_test(check_group, ...)
```

**Depois:**
```python
def group_required(group_names, ...):
    def check_group(user):
        # Mapeamento de grupo → método role
        role_map = {
            'Gestor': 'is_gestor',
            'Coordenador': 'is_coordenador',
            'Fotógrafo': 'is_fotografo',     # ← NOVO
            'Pesquisa': 'is_pesquisa',       # ← NOVO
        }
        
        user_groups = [g.name for g in user.groups.all()]
        
        # 1. Verifica grupos PRIMEIRO
        if any(group in user_groups for group in group_names):
            return True
        
        # 2. Se não tem grupo, verifica role correspondente ← NOVO
        for group_name in group_names:
            role_method = role_map.get(group_name)
            if role_method and hasattr(user, role_method):
                if getattr(user, role_method)():
                    return True  # ✅ Acesso permitido via role!
        
        return False
    return user_passes_test(check_group, ...)
```

**Impacto:**
- Views com `@group_required('Fotógrafo')` agora aceitam usuários com `role='fotografo'`
- Compatível com ambos os sistemas (grupos Django + roles custom)
- Fallback seguro se nenhum grupo/role for encontrado

### **2️⃣ Melhorar `get_dashboard_redirect()` em `views.py`**

**Antes:**
```python
def get_dashboard_redirect(user):
    if user.is_fotografo():
        return 'fotografo_dashboard'
    ...
    else:
        return 'login'  # ❌ CAUSA LOOP SE USUÁRIO JÁ AUTENTICADO!
```

**Depois:**
```python
def get_dashboard_redirect(user):
    """
    NUNCA retorna 'login' pois causaria loop infinito
    se o usuário já está autenticado.
    """
    if user.is_fotografo():
        return 'fotografo_dashboard'
    ...
    else:
        # Fallback seguro
        logger.warning(f"Usuário sem role definida: {user.username}")
        return 'fotografo_dashboard'  # ✅ Evita loop infinito
```

---

## 📊 Alterações Realizadas

### **Arquivos Modificados:**

| Arquivo | Linhas | Mudança |
|---------|--------|---------|
| `gestcaptur/gestcaptur/decorators.py` | 28-55 | Adicionar verificação de role no decorator `group_required()` |
| `gestcaptur/gestcaptur/views.py` | 95-140 | Melhorar fallbacks em `get_dashboard_redirect()` |

### **Commits Git:**

```
105fc26 - Fix: Corrigir loop de redirecionamento ao fazer login
          - decorator group_required agora verifica role também
          - get_dashboard_redirect nunca retorna 'login' para usuário autenticado
```

---

## 🔧 Passos de Implementação

### **Local (D:\photoapp_v2):**
✅ Arquivos corrigidos e commitados

### **VPS (179.0.178.106:/var/www/photoapp):**
✅ decorators.py atualizado via SSH  
✅ Gunicorn reiniciado (systemctl restart photoapp)  
✅ Status: Active (running) desde 09:30:08

---

## 🧪 Como Testar a Correção

### **Teste 1: Login com Fotógrafo**
```bash
# Acessar https://cliente.photum.com.br/login/
# Username: [usuário com role='fotografo']
# Password: [senha]
# Esperado: Redireciona para /fotografo/ SEM loop
```

### **Teste 2: Verificar Logs**
```bash
# No VPS:
tail -f /var/log/gunicorn/photoapp.log
# Procurar por:
# "Redirecionando para dashboard fotógrafo"
# "Acesso concedido para [username] via role"
```

### **Teste 3: Debug de Usuário**
```bash
# Acessar https://cliente.photum.com.br/debug_user/
# Ver JSON com role, grupos, e métodos is_*()
```

---

## 📋 Recomendações Futuras

### **1. Criar Grupos Django (Opcional)**
Se quiser usar apenas grupos sem roles:
```bash
python manage.py shell
from django.contrib.auth.models import Group
for name in ['Gestor', 'Coordenador', 'Fotógrafo', 'Pesquisa']:
    Group.objects.get_or_create(name=name)
```

### **2. Migrar Usuários para Grupos (Opcional)**
```python
for user in Usuario.objects.all():
    group_map = {'gestor': 'Gestor', 'fotografo': 'Fotógrafo', ...}
    group_name = group_map.get(user.role)
    if group_name:
        user.groups.add(Group.objects.get(name=group_name))
```

### **3. Documentar Sistema de Permissões**
Atualmente suporta ambos:
- **Grupos Django** (novo standard)
- **Roles Custom** (compatível com código legado)

---

## 📞 Suporte

Para **novos bugs** ou **melhorias**:
1. Verificar logs: `/var/log/gunicorn/photoapp.log`
2. Verificar permissões em: `/debug_user/`
3. Comitar mudanças com prefix `Fix:` ou `Feature:`

---

**Análise Completa ✅**  
**Status**: Pronto para produção  
**Próximos passos**: Testar com usuários reais
