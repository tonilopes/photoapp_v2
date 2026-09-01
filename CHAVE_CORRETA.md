# 🔑 Usando a Chave SSH Correta

## ❌ Problema Identificado

Você tem **duas chaves SSH diferentes**:

1. **Chave no servidor** (`~/.ssh/authorized_keys`):
   ```
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOOd8Icj0Ociy7PdrrRnJwye4K0Lps9FglhK0zIaUNGT autossh-tunnel-ubuntu-digisac
   ```
   - Tipo: **Ed25519**
   - Nome: `autossh-tunnel-ubuntu-digisac`

2. **Chave que você está tentando usar**:
   ```
   ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC9US4... seu_email@email.com
   ```
   - Tipo: **RSA**
   - Arquivo: `toni@photum.com.br`

**Elas não correspondem!** Por isso o SSH pede senha.

---

## 🔧 Soluções

### Solução 1: Encontrar a Chave Privada Correta

Você precisa encontrar o arquivo da chave privada que corresponde à chave Ed25519 no servidor.

#### Procure por arquivos como:
- `autossh-tunnel-ubuntu-digisac`
- `autossh-tunnel-ubuntu-digisac.key`
- Algum arquivo na pasta `.ssh` ou em `~/.ssh/`

#### No Windows, procure em:
```
C:\Users\SeuUsuario\.ssh\
d:\photoapp_v2\
```

Se encontrar o arquivo, use-o:
```powershell
ssh -i "caminho\da\chave\autossh-tunnel-ubuntu-digisac" toni@photum.com.br
```

---

### Solução 2: Adicionar a Chave RSA ao Servidor

Se você **não tem** a chave Ed25519, mas quer usar a chave RSA (`toni@photum.com.br`), precisa adicioná-la ao servidor.

#### Passo 1: Copiar a Chave Pública RSA
O conteúdo de `toni@photum.com.br.pub` é:
```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC9US4seRKCblvxMgp8u7jvNVPsBBaPV7xYn6zEPP2cS3PljvaFO+hgvCJBkaKC6E6Up9VJro7WguGvHNJZB5Bl8UnX0u3OuNb25c0gHxbm8lGl86kqewEdVklv2Xfu2Kf0vv0gfQaWoL4wdToCWs+XrFhv+RvaVFdCY48Zv97VxXm5xpDTJ2j3RU8VHkq2hBG2FkGP6L+SYVGptMG7wziBDGYzHnQYiIsFMTFoUFRjqSXgpzdALE/S/SDDJCJiB1NEcsy33fQ80fS+NbUaZObI+pMfihtrRPcWUTF69xnOi0/vriu7Le9pEm8RR5coZDDn/p8ToiL+44pVSHbIArAWywUXQMctN2opqLH/wOSwdJ6ygczDC7ACLPzWNGKi4H8eWmIUCH0x47QXzEoTr6MgRmCTg5GMoY3psZZcR1PHUyVcP6hWSIJo09e2VF/HvA25TE5nCCvhHLVcrpjjFQDifRGLYmJCis297WkEjT0KWz6eucSJeL2/4u90O2aX1zG2Rpa06a+c76UrrZvKhvqCf1hF03w5htIeN8bg9qh8YxKbc6LW9ZoXd8gcufBiPXZ1e+2dIwP9Q690XfZ2oJt1HopyKe4q+6fwEzg7b3ZbdG8Vk8xa2XGFQpQnM6WRXBOzjEhmUEbTSThv+KifW3Ie0r/I21o5CpTiGvHaQsDJvQ== seu_email@email.com
```

#### Passo 2: Acessar a VPS
Use o **Console Web** do provedor da VPS (não é Locaweb, descubra qual é).

#### Passo 3: Adicionar a Chave RSA
No console da VPS:

```bash
# 1. Adicione a chave RSA ao authorized_keys
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC9US4seRKCblvxMgp8u7jvNVPsBBaPV7xYn6zEPP2cS3PljvaFO+hgvCJBkaKC6E6Up9VJro7WguGvHNJZB5Bl8UnX0u3OuNb25c0gHxbm8lGl86kqewEdVklv2Xfu2Kf0vv0gfQaWoL4wdToCWs+XrFhv+RvaVFdCY48Zv97VxXm5xpDTJ2j3RU8VHkq2hBG2FkGP6L+SYVGptMG7wziBDGYzHnQYiIsFMTFoUFRjqSXgpzdALE/S/SDDJCJiB1NEcsy33fQ80fS+NbUaZObI+pMfihtrRPcWUTF69xnOi0/vriu7Le9pEm8RR5coZDDn/p8ToiL+44pVSHbIArAWywUXQMctN2opqLH/wOSwdJ6ygczDC7ACLPzWNGKi4H8eWmIUCH0x47QXzEoTr6MgRmCTg5GMoY3psZZcR1PHUyVcP6hWSIJo09e2VF/HvA25TE5nCCvhHLVcrpjjFQDifRGLYmJCis297WkEjT0KWz6eucSJeL2/4u90O2aX1zG2Rpa06a+c76UrrZvKhvqCf1hF03w5htIeN8bg9qh8YxKbc6LW9ZoXd8gcufBiPXZ1e+2dIwP9Q690XfZ2oJt1HopyKe4q+6fwEzg7b3ZbdG8Vk8xa2XGFQpQnM6WRXBOzjEhmUEbTSThv+KifW3Ie0r/I21o5CpTiGvHaQsDJvQ== seu_email@email.com" >> ~/.ssh/authorized_keys

# 2. Defina permissões corretas
chmod 600 ~/.ssh/authorized_keys

# 3. Reinicie o SSH
sudo systemctl restart sshd
```

#### Passo 4: Testar Conexão
```powershell
ssh -i "d:\photoapp_v2\toni@photum.com.br" toni@photum.com.br
```

---

### Solução 3: Usar a Chave Ed25519 (Se Tiver a Privada)

Se você encontrar o arquivo da chave Ed25519 (a que já está no servidor), use-a diretamente:

```powershell
ssh -i "caminho\para\autossh-tunnel-ubuntu-digisac" toni@photum.com.br
```

---

## 📋 Resumo

| Chave | Tipo | Status |
|-------|------|--------|
| `autossh-tunnel-ubuntu-digisac` | Ed25519 | ✅ Está no servidor |
| `toni@photum.com.br` | RSA | ❌ Não está no servidor |

**Para usar `toni@photum.com.br`, você precisa adicioná-la ao servidor.**

---

## 🎯 Próximos Passos

1. **Decida qual chave usar:**
   - Se tiver a chave Ed25519 privada, use-a (já está no servidor)
   - Se quiser usar a RSA, adicione-a ao servidor

2. **Após resolver o SSH, execute os comandos de limpeza da VPS**

3. **Atualize o sistema**

---

**Escolha uma solução e siga as instruções!**