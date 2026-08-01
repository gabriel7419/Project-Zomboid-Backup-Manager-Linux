# 🧟 Zomboid Backup Manager

Um gerenciador moderno de backups para **Project Zomboid**.

<p align="center">
  <img src="screenshots/interface.png" alt="Zomboid Backup Manager" width="900">
</p>

---

## ✨ Recursos

- ✅ Backup de mundos Single-player
- ✅ Backup de mundos Multiplayer
- ✅ Detecção automática dos mundos
- ✅ Restauração com backup de segurança
- ✅ Histórico de atividades
- ✅ Configurações personalizáveis
- ✅ Interface moderna
- ✅ Executável para Windows
- ✅ Suporte a Linux

---

## 📦 Download

Baixe a versão mais recente na página de **Releases**.

---

## 🐧 Linux

### Executar pelo código-fonte

```bash
# 1. Instalar dependência do sistema (Arch)
sudo pacman -S tk

# 2. Criar o ambiente virtual e instalar dependências
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Rodar
.venv/bin/python3 main.py
```

### Gerar um executável

```bash
# 1. Instalar o PyInstaller no ambiente virtual
.venv/bin/pip install pyinstaller

# 2. Gerar o executável
.venv/bin/pyinstaller \
    --onefile \
    --name "ZomboidBackupManager" \
    --add-data "assets:assets" \
    --hidden-import customtkinter \
    --hidden-import darkdetect \
    --hidden-import PIL \
    --clean \
    --noconfirm \
    main.py

# 3. O executável estará em:
# dist/ZomboidBackupManager
```

> **Nota:** o executável gerado é específico para Linux x86-64 e não requer Python instalado.

---

## 👨‍💻 Desenvolvedor

**BooDoSnes**

Se encontrar algum bug ou tiver alguma sugestão, fique à vontade para abrir uma *Issue* ou entrar em contato.