from __future__ import annotations

import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import shutil
import customtkinter as ctk

from backup import criar_backup
from restore import restaurar_backup
from settings import carregar_configuracoes, salvar_configuracoes
from utils import abrir_jogo, abrir_pasta, formatar_tamanho, registrar_historico
from worlds import Mundo, detectar_mundos, encontrar_mundo, filtrar_mundos


class ZomboidBackupApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.configuracoes = carregar_configuracoes()
        self.pasta_saves = Path(self.configuracoes["pasta_saves"])
        self.destino_base = Path(self.configuracoes["destino_base"])
        self.max_backups = int(self.configuracoes["max_backups"])

        self.mundos: list[Mundo] = []
        self.mundo_atual: Mundo | None = None
        self.destino = self.destino_base
        self.backup_selecionado: Path | None = None

        self.pasta_logs = Path(__file__).resolve().parent / "logs"
        self.operacao_em_andamento = False
        self.notificacao_atual: ctk.CTkFrame | None = None

        self.title("Zomboid Backup Manager")
        self.geometry("1040x760")
        self.minsize(1040, 760)
        self.resizable(False, False)
        self.configure(fg_color="#111318")

        self.carregar_mundos()
        self.criar_interface()
        self.selecionar_mundo_inicial()
        self.atualizar_tudo()

    def carregar_mundos(self) -> None:
        self.mundos = detectar_mundos(self.pasta_saves)

    def selecionar_mundo_inicial(self) -> None:
        salvo = encontrar_mundo(
            self.mundos,
            self.configuracoes.get("ultimo_mundo"),
        )

        if salvo is None and self.mundos:
            salvo = self.mundos[0]

        if salvo is None:
            self.combo_tipo.configure(values=["Nenhum mundo encontrado"])
            self.combo_tipo.set("Nenhum mundo encontrado")
            self.combo_mundo.configure(values=[""])
            self.combo_mundo.set("")
            self.aplicar_mundo(None)
            return

        self.combo_tipo.set(salvo.tipo_label)
        self.atualizar_combo_mundos(salvo.tipo_label)
        self.combo_mundo.set(salvo.nome_exibicao)
        self.aplicar_mundo(salvo)

    def aplicar_mundo(self, mundo: Mundo | None) -> None:
        self.mundo_atual = mundo
        self.backup_selecionado = None

        if mundo is None:
            self.destino = self.destino_base
        else:
            self.destino = (
                self.destino_base / mundo.pasta_backup
            )
            self.configuracoes["ultimo_mundo"] = mundo.identificador
            salvar_configuracoes(self.configuracoes)

        if hasattr(self, "label_destino_atual"):
            self.label_destino_atual.configure(
                text=f"Backups: {self.destino}"
            )

    def atualizar_combo_mundos(self, tipo_label: str) -> None:
        mundos = filtrar_mundos(self.mundos, tipo_label)
        valores = [mundo.nome_exibicao for mundo in mundos]
        self.combo_mundo.configure(values=valores or [""])
        if valores:
            self.combo_mundo.set(valores[0])

    def ao_mudar_tipo(self, tipo_label: str) -> None:
        if self.operacao_em_andamento:
            return

        self.atualizar_combo_mundos(tipo_label)
        self.ao_mudar_mundo(self.combo_mundo.get())

    def ao_mudar_mundo(self, nome_exibicao: str) -> None:
        if self.operacao_em_andamento:
            return

        tipo = self.combo_tipo.get()
        mundo = next(
            (
                item for item in self.mundos
                if item.tipo_label == tipo
                and item.nome_exibicao == nome_exibicao
            ),
            None,
        )
        self.aplicar_mundo(mundo)
        self.atualizar_tudo()

    def criar_interface(self) -> None:
        self.criar_barra_lateral()
        self.criar_area_principal()

    def criar_barra_lateral(self) -> None:
        lateral = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=0,
            fg_color="#171a21",
        )
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)

        marca = ctk.CTkFrame(lateral, fg_color="transparent")
        marca.pack(fill="x", padx=20, pady=(28, 0))

        detalhe = ctk.CTkFrame(
            marca,
            width=4,
            height=62,
            corner_radius=2,
            fg_color="#2b7bbb",
        )
        detalhe.pack(side="left", fill="y", padx=(0, 12))

        textos = ctk.CTkFrame(marca, fg_color="transparent")
        textos.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            textos,
            text="PROJECT\nZOMBOID",
            font=("Segoe UI", 25, "bold"),
            justify="left",
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            textos,
            text="BACKUP MANAGER",
            font=("Segoe UI", 10, "bold"),
            text_color="#8d96a8",
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkFrame(
            lateral,
            height=1,
            fg_color="#292e38",
        ).pack(fill="x", padx=20, pady=(22, 18))

        ctk.CTkLabel(
            lateral,
            text="AÇÕES PRINCIPAIS",
            font=("Segoe UI", 9, "bold"),
            text_color="#697180",
        ).pack(anchor="w", padx=24, pady=(0, 6))

        self.botao_backup = self.criar_botao_lateral(
            lateral,
            "↻   Fazer backup",
            lambda: self.iniciar_backup(False),
            principal=True,
        )
        self.botao_backup_jogo = self.criar_botao_lateral(
            lateral,
            "▶   Backup + jogo",
            lambda: self.iniciar_backup(True),
            principal=True,
        )

        ctk.CTkLabel(
            lateral,
            text="FERRAMENTAS",
            font=("Segoe UI", 9, "bold"),
            text_color="#697180",
        ).pack(anchor="w", padx=24, pady=(18, 6))

        self.criar_botao_lateral(
            lateral,
            "▷   Abrir jogo",
            abrir_jogo,
        )
        self.criar_botao_lateral(
            lateral,
            "▣   Abrir pasta",
            lambda: abrir_pasta(self.destino),
        )
        self.criar_botao_lateral(
            lateral,
            "⚙   Configurações",
            self.abrir_configuracoes,
        )
        self.criar_botao_lateral(
            lateral,
            "≡   Histórico",
            self.abrir_historico,
        )

        plataforma = "🐧 Linux" if sys.platform != "win32" else "🪟 Windows"
        ctk.CTkLabel(
            lateral,
            text=plataforma,
            font=("Segoe UI", 9),
            text_color="#4a5260",
        ).pack(side="bottom", pady=(0, 4))

        ctk.CTkLabel(
            lateral,
            text="Versão 4.0\nby BooDoSnes",
            font=("Segoe UI", 9),
            text_color="#697180",
        ).pack(side="bottom", pady=(20, 0))

    def criar_botao_lateral(
        self,
        pai,
        texto: str,
        comando,
        principal: bool = False,
    ) -> ctk.CTkButton:
        botao = ctk.CTkButton(
            pai,
            text=texto,
            height=44 if principal else 40,
            corner_radius=10,
            anchor="w",
            font=("Segoe UI", 13 if principal else 12, "bold" if principal else "normal"),
            fg_color="#2777b5" if principal else "#242a34",
            hover_color="#3189cc" if principal else "#303845",
            border_width=1,
            border_color="#3b8dcc" if principal else "#303743",
            command=comando,
        )
        botao.pack(fill="x", padx=20, pady=5 if principal else 4)
        return botao

    def criar_area_principal(self) -> None:
        principal = ctk.CTkFrame(self, fg_color="transparent")
        principal.pack(
            side="left",
            fill="both",
            expand=True,
            padx=28,
            pady=(18, 12),
        )

        topo = ctk.CTkFrame(principal, fg_color="transparent")
        topo.pack(fill="x")

        bloco = ctk.CTkFrame(topo, fg_color="transparent")
        bloco.pack(side="left")

        ctk.CTkLabel(
            bloco,
            text="Zomboid Backup Manager",
            font=("Segoe UI", 26, "bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            bloco,
            text="Faça backup de mundos single-player e multiplayer.",
            font=("Segoe UI", 12),
            text_color="#8d96a8",
        ).pack(anchor="w", pady=(2, 0))

        self.label_status_geral = ctk.CTkLabel(
            topo,
            text="● Sistema pronto",
            font=("Segoe UI", 13, "bold"),
            text_color="#56d17b",
        )
        self.label_status_geral.pack(side="right")

        ctk.CTkFrame(
            principal,
            height=1,
            fg_color="#292e38",
        ).pack(fill="x", pady=(10, 10))

        seletor = ctk.CTkFrame(
            principal,
            corner_radius=14,
            fg_color="#191c22",
        )
        seletor.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            seletor,
            text="Mundo ativo",
            font=("Segoe UI", 15, "bold"),
        ).grid(row=0, column=0, padx=18, pady=(10, 4), sticky="w")

        tipos = sorted({mundo.tipo_label for mundo in self.mundos})
        self.combo_tipo = ctk.CTkComboBox(
            seletor,
            width=180,
            values=tipos or ["Nenhum mundo encontrado"],
            state="readonly",
            command=self.ao_mudar_tipo,
        )
        self.combo_tipo.grid(row=1, column=0, padx=(18, 8), pady=(0, 12), sticky="w")

        self.combo_mundo = ctk.CTkComboBox(
            seletor,
            width=340,
            values=[""],
            state="readonly",
            command=self.ao_mudar_mundo,
        )
        self.combo_mundo.grid(row=1, column=1, padx=8, pady=(0, 12), sticky="w")

        self.label_destino_atual = ctk.CTkLabel(
            seletor,
            text="Backups:",
            font=("Segoe UI", 10),
            text_color="#8d96a8",
            anchor="w",
        )
        self.label_destino_atual.grid(
            row=2,
            column=0,
            columnspan=3,
            padx=18,
            pady=(0, 10),
            sticky="w",
        )
        seletor.grid_columnconfigure(2, weight=1)

        cards = ctk.CTkFrame(principal, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 10))

        self.card_ultimo = self.criar_card(cards, "ÚLTIMO BACKUP", "Nenhum")
        self.card_quantidade = self.criar_card(cards, "BACKUPS", "0 de 2")
        self.card_espaco = self.criar_card(cards, "ESPAÇO USADO", "0 B")

        self.card_ultimo.pack(side="left", fill="x", expand=True, padx=(0, 7))
        self.card_quantidade.pack(side="left", fill="x", expand=True, padx=7)
        self.card_espaco.pack(side="left", fill="x", expand=True, padx=(7, 0))

        self.label_mundo = ctk.CTkLabel(
            principal,
            text="Verificando...",
            font=("Segoe UI", 11),
            text_color="#8d96a8",
            anchor="w",
        )
        self.label_mundo.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            principal,
            text="Backups disponíveis",
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w", pady=(0, 7))

        self.lista_backups = ctk.CTkScrollableFrame(
            principal,
            height=105,
            fg_color="#191c22",
            corner_radius=14,
        )
        self.lista_backups.pack(fill="x", pady=(0, 9))

        acoes = ctk.CTkFrame(principal, fg_color="transparent")
        acoes.pack(fill="x", pady=(7, 0))

        self.botao_restaurar = ctk.CTkButton(
            acoes,
            text="Restaurar selecionado",
            height=40,
            state="disabled",
            command=self.confirmar_restauracao,
        )
        self.botao_restaurar.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.botao_excluir = ctk.CTkButton(
            acoes,
            text="Excluir selecionado",
            height=40,
            state="disabled",
            fg_color="#9f3a3a",
            hover_color="#b64646",
            command=self.excluir_backup,
        )
        self.botao_excluir.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.barra = ctk.CTkProgressBar(principal, height=10)
        self.barra.pack(fill="x", pady=(9, 3))
        self.barra.set(0)

        self.label_porcentagem = ctk.CTkLabel(
            principal,
            text="0%",
            font=("Segoe UI", 11, "bold"),
            text_color="#c7ced9",
        )
        self.label_porcentagem.pack()

        self.label_status = ctk.CTkLabel(
            principal,
            text="Pronto.",
            font=("Segoe UI", 11),
            text_color="#9ca3af",
        )
        self.label_status.pack()

    def criar_card(self, pai, titulo: str, valor: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            pai,
            height=74,
            corner_radius=14,
            fg_color="#191c22",
        )
        card.pack_propagate(False)

        ctk.CTkLabel(
            card,
            text=titulo,
            font=("Segoe UI", 9, "bold"),
            text_color="#838b99",
        ).pack(anchor="w", padx=16, pady=(9, 0))

        valor_label = ctk.CTkLabel(
            card,
            text=valor,
            font=("Segoe UI", 16, "bold"),
        )
        valor_label.pack(anchor="w", padx=16)

        card.label_valor = valor_label
        return card

    def atualizar_tudo(self) -> None:
        self.atualizar_mundo()
        self.atualizar_lista_backups()

    def atualizar_mundo(self) -> None:
        if self.mundo_atual is None:
            self.label_mundo.configure(
                text=(
                    "Nenhum mundo encontrado. Confira a pasta de saves "
                    "nas Configurações."
                ),
                text_color="#ff6b6b",
            )
            return

        faltando = [
            nome for nome in self.mundo_atual.pastas
            if not (self.mundo_atual.raiz / nome).is_dir()
        ]

        if faltando:
            self.label_mundo.configure(
                text="✕ Mundo incompleto: " + ", ".join(faltando),
                text_color="#ff6b6b",
            )
        else:
            self.label_mundo.configure(
                text=(
                    f"✓ {self.mundo_atual.tipo_label} • "
                    f"{self.mundo_atual.nome_exibicao} • "
                    f"{len(self.mundo_atual.pastas)} pasta(s)"
                ),
                text_color="#56d17b",
            )

    def obter_backups(self) -> list[Path]:
        if self.mundo_atual is None:
            return []

        self.destino.mkdir(parents=True, exist_ok=True)
        padrao = "Zomboid_Backup_*.rar" if sys.platform == "win32" else "Zomboid_Backup_*.tar.gz"

        return sorted(
            self.destino.glob(padrao),
            key=lambda arquivo: arquivo.stat().st_mtime,
            reverse=True,
        )

    def atualizar_lista_backups(self) -> None:
        for widget in self.lista_backups.winfo_children():
            widget.destroy()

        self.backup_selecionado = None
        self.botao_restaurar.configure(state="disabled")
        self.botao_excluir.configure(state="disabled")

        backups = self.obter_backups()
        tamanho_total = sum(a.stat().st_size for a in backups)

        self.card_quantidade.label_valor.configure(
            text=f"{len(backups)} de {self.max_backups}"
        )
        self.card_espaco.label_valor.configure(
            text=formatar_tamanho(tamanho_total)
        )

        if backups:
            data = datetime.fromtimestamp(backups[0].stat().st_mtime)
            self.card_ultimo.label_valor.configure(
                text=data.strftime("%d/%m %H:%M")
            )
        else:
            self.card_ultimo.label_valor.configure(text="Nenhum")
            ctk.CTkLabel(
                self.lista_backups,
                text="Nenhum backup deste mundo foi criado ainda.",
                text_color="#8c94a3",
            ).pack(pady=28)
            return

        for arquivo in backups:
            self.criar_item_backup(arquivo)

    def criar_item_backup(self, arquivo: Path) -> None:
        data = datetime.fromtimestamp(arquivo.stat().st_mtime)
        tamanho = formatar_tamanho(arquivo.stat().st_size)

        item = ctk.CTkButton(
            self.lista_backups,
            text=f"{data.strftime('%d/%m/%Y às %H:%M:%S')}     •     {tamanho}",
            height=42,
            anchor="w",
            fg_color="#252a33",
            hover_color="#303743",
            command=lambda: self.selecionar_backup(arquivo, item),
        )
        item.pack(fill="x", padx=4, pady=4)

    def selecionar_backup(self, arquivo: Path, botao) -> None:
        self.backup_selecionado = arquivo

        for widget in self.lista_backups.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.configure(fg_color="#252a33")

        botao.configure(fg_color="#1f6aa5")
        self.botao_restaurar.configure(state="normal")
        self.botao_excluir.configure(state="normal")

    def definir_status(self, mensagem: str) -> None:
        self.after(0, lambda: self.label_status.configure(text=mensagem))

    def atualizar_progresso(self, valor: int, mensagem: str) -> None:
        valor = max(0, min(100, valor))

        def atualizar() -> None:
            self.barra.configure(mode="determinate")
            self.barra.set(valor / 100)
            self.label_porcentagem.configure(text=f"{valor}%")
            self.label_status.configure(text=mensagem)

        self.after(0, atualizar)

    def definir_operacao_em_andamento(self, valor: bool) -> None:
        self.operacao_em_andamento = valor
        estado = "disabled" if valor else "normal"

        self.botao_backup.configure(state=estado)
        self.botao_backup_jogo.configure(state=estado)
        self.combo_tipo.configure(state="disabled" if valor else "readonly")
        self.combo_mundo.configure(state="disabled" if valor else "readonly")

        if valor:
            self.botao_restaurar.configure(state="disabled")
            self.botao_excluir.configure(state="disabled")
        elif self.backup_selecionado is not None:
            self.botao_restaurar.configure(state="normal")
            self.botao_excluir.configure(state="normal")

    def fechar_notificacao(self) -> None:
        if self.notificacao_atual is not None:
            try:
                self.notificacao_atual.destroy()
            except Exception:
                pass
            self.notificacao_atual = None

    def mostrar_notificacao(
        self,
        titulo: str,
        mensagem: str,
        tipo: str = "sucesso",
        duracao: int = 6500,
    ) -> None:
        self.fechar_notificacao()

        estilos = {
            "sucesso": ("#2f9e5b", "✓"),
            "erro": ("#c84d4d", "!"),
            "aviso": ("#c58a36", "i"),
        }
        cor, simbolo = estilos.get(tipo, estilos["aviso"])

        quadro = ctk.CTkFrame(
            self,
            width=360,
            corner_radius=14,
            fg_color="#20242c",
            border_width=1,
            border_color="#343a46",
        )
        quadro.place(
            relx=1,
            rely=1,
            x=-24,
            y=-24,
            anchor="se",
        )
        quadro.pack_propagate(False)
        self.notificacao_atual = quadro

        cabecalho = ctk.CTkFrame(quadro, fg_color="transparent")
        cabecalho.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(
            cabecalho,
            text=simbolo,
            width=28,
            height=28,
            corner_radius=14,
            fg_color=cor,
            font=("Segoe UI", 15, "bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            cabecalho,
            text=titulo,
            font=("Segoe UI", 15, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(10, 8))

        ctk.CTkButton(
            cabecalho,
            text="×",
            width=28,
            height=28,
            corner_radius=8,
            fg_color="#2b303a",
            hover_color="#3a414e",
            command=self.fechar_notificacao,
        ).pack(side="right")

        ctk.CTkLabel(
            quadro,
            text=mensagem,
            justify="left",
            anchor="w",
            wraplength=320,
            font=("Segoe UI", 12),
            text_color="#c2c8d2",
        ).pack(fill="x", padx=18, pady=(2, 16))

        quadro.update_idletasks()
        quadro.configure(height=max(115, quadro.winfo_reqheight()))

        self.after(
            duracao,
            lambda q=quadro: (
                self.fechar_notificacao()
                if self.notificacao_atual is q
                else None
            ),
        )

    @staticmethod
    def formatar_tempo(segundos: float) -> str:
        total = int(round(segundos))
        minutos, resto = divmod(total, 60)
        if minutos:
            return f"{minutos} min e {resto} s"
        return f"{max(1, resto)} s"

    def validar_mundo_ativo(self) -> Mundo:
        if self.mundo_atual is None:
            raise RuntimeError(
                "Nenhum mundo foi selecionado.\n\n"
                "Confira a pasta de saves nas Configurações."
            )
        return self.mundo_atual

    def iniciar_backup(self, abrir_depois: bool) -> None:
        if self.operacao_em_andamento:
            return

        try:
            self.validar_mundo_ativo()
        except Exception as erro:
            self.mostrar_notificacao(
                "Mundo não selecionado",
                str(erro),
                tipo="erro",
            )
            return

        self.definir_operacao_em_andamento(True)
        self.label_status_geral.configure(
            text="● Trabalhando",
            text_color="#ffca5c",
        )
        self.barra.set(0)
        self.label_porcentagem.configure(text="0%")

        threading.Thread(
            target=self.executar_backup,
            args=(abrir_depois,),
            daemon=True,
        ).start()

    def executar_backup(self, abrir_depois: bool) -> None:
        inicio = time.perf_counter()

        try:
            mundo = self.validar_mundo_ativo()
            resultado = criar_backup(
                raiz=mundo.raiz,
                pastas=mundo.pastas,
                destino=self.destino,
                max_backups=self.max_backups,
                atualizar_status=self.definir_status,
                atualizar_progresso=self.atualizar_progresso,
            )

            registrar_historico(
                self.pasta_logs,
                "BACKUP CRIADO",
                (
                    f"{mundo.tipo_label} | {mundo.nome_exibicao} | "
                    f"{resultado['arquivo']} | {resultado['tamanho']}"
                ),
            )

            self.after(0, self.atualizar_tudo)
            tempo = self.formatar_tempo(time.perf_counter() - inicio)

            self.after(
                0,
                lambda: self.mostrar_notificacao(
                    "Backup concluído",
                    (
                        f"Mundo: {mundo.nome_exibicao}\n"
                        f"Arquivo: {resultado['arquivo']}\n"
                        f"Tamanho: {resultado['tamanho']}\n"
                        f"Tempo: {tempo}"
                    ),
                ),
            )

            if abrir_depois:
                self.after(0, abrir_jogo)

        except Exception as erro:
            registrar_historico(
                self.pasta_logs,
                "ERRO NO BACKUP",
                str(erro).replace("\n", " "),
            )
            self.after(
                0,
                lambda e=erro: self.mostrar_notificacao(
                    "Erro no backup",
                    str(e),
                    tipo="erro",
                    duracao=9000,
                ),
            )
        finally:
            self.finalizar_operacao()

    def confirmar_restauracao(self) -> None:
        if not self.backup_selecionado:
            return

        mundo = self.validar_mundo_ativo()
        resposta = messagebox.askyesno(
            "Restaurar backup",
            (
                f"Mundo: {mundo.nome_exibicao}\n\n"
                f"Backup: {self.backup_selecionado.name}\n\n"
                "Os arquivos atuais deste mundo serão substituídos."
            ),
        )
        if not resposta:
            return

        self.definir_operacao_em_andamento(True)
        threading.Thread(
            target=self.executar_restauracao,
            daemon=True,
        ).start()

    def executar_restauracao(self) -> None:
        inicio = time.perf_counter()

        try:
            mundo = self.validar_mundo_ativo()
            arquivo = self.backup_selecionado

            if arquivo is None:
                raise RuntimeError("Nenhum backup foi selecionado.")

            seguranca = restaurar_backup(
                arquivo_backup=arquivo,
                raiz=mundo.raiz,
                pastas=mundo.pastas,
                pasta_backups=self.destino,
                atualizar_status=self.definir_status,
                atualizar_progresso=self.atualizar_progresso,
            )

            registrar_historico(
                self.pasta_logs,
                "BACKUP RESTAURADO",
                f"{mundo.nome_exibicao} | {arquivo.name}",
            )

            self.after(0, self.atualizar_tudo)
            tempo = self.formatar_tempo(time.perf_counter() - inicio)

            self.after(
                0,
                lambda: self.mostrar_notificacao(
                    "Restauração concluída",
                    (
                        f"Mundo: {mundo.nome_exibicao}\n"
                        f"Backup de segurança: {seguranca.name}\n"
                        f"Tempo: {tempo}"
                    ),
                    duracao=8500,
                ),
            )

        except Exception as erro:
            registrar_historico(
                self.pasta_logs,
                "ERRO NA RESTAURAÇÃO",
                str(erro).replace("\n", " "),
            )
            self.after(
                0,
                lambda e=erro: self.mostrar_notificacao(
                    "Erro na restauração",
                    str(e),
                    tipo="erro",
                    duracao=9000,
                ),
            )
        finally:
            self.finalizar_operacao()

    def finalizar_operacao(self) -> None:
        self.after(
            0,
            lambda: self.label_status_geral.configure(
                text="● Sistema pronto",
                text_color="#56d17b",
            ),
        )
        self.after(
            0,
            lambda: self.definir_operacao_em_andamento(False),
        )
        self.after(1200, lambda: self.barra.set(0))
        self.after(
            1200,
            lambda: self.label_porcentagem.configure(text="0%"),
        )
        self.after(
            1200,
            lambda: self.label_status.configure(text="Pronto."),
        )

    def excluir_backup(self) -> None:
        if not self.backup_selecionado:
            return

        arquivo = self.backup_selecionado
        if not messagebox.askyesno(
            "Excluir backup",
            (
                f"Deseja excluir definitivamente?\n\n{arquivo.name}\n\n"
                "Essa ação não pode ser desfeita."
            ),
        ):
            return

        try:
            arquivo.unlink()
            registrar_historico(
                self.pasta_logs,
                "BACKUP EXCLUÍDO",
                arquivo.name,
            )
            self.atualizar_lista_backups()
            self.mostrar_notificacao(
                "Backup excluído",
                arquivo.name,
            )
        except OSError as erro:
            self.mostrar_notificacao(
                "Erro ao excluir",
                str(erro),
                tipo="erro",
            )

    def abrir_historico(self) -> None:
        janela = ctk.CTkToplevel(self)
        janela.title("Histórico")
        janela.geometry("880x520")
        janela.configure(fg_color="#111318")
        janela.grab_set()

        ctk.CTkLabel(janela, text="Histórico de atividades", font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=25, pady=(22, 4))

        caixa = ctk.CTkTextbox(
            janela,
            corner_radius=12,
            fg_color="#191c22",
            border_width=1,
            border_color="#292e38",
            font=("Consolas", 12),
        )
        caixa.pack(fill="both", expand=True, padx=25, pady=(12, 15))

        arquivo = self.pasta_logs / "historico.txt"
        conteudo = arquivo.read_text(encoding="utf-8") if arquivo.exists() else "Nenhuma atividade registrada."
        caixa.insert("end", conteudo)
        caixa.configure(state="disabled")

        def limpar_historico():
            if arquivo.exists() and messagebox.askyesno("Limpar histórico","Deseja apagar todo o histórico?",parent=janela):
                arquivo.write_text("", encoding="utf-8")
                caixa.configure(state="normal")
                caixa.delete("1.0","end")
                caixa.insert("end","Nenhuma atividade registrada.")
                caixa.configure(state="disabled")
                messagebox.showinfo("Histórico","Histórico limpo com sucesso.",parent=janela)

        def exportar_historico():
            destino=filedialog.asksaveasfilename(parent=janela,defaultextension=".txt",filetypes=[("Arquivo de texto","*.txt")],initialfile="historico.txt")
            if destino:
                shutil.copy2(arquivo,destino)

        botoes=ctk.CTkFrame(janela,fg_color="transparent")
        botoes.pack(fill="x",padx=25,pady=(0,20))

        ctk.CTkButton(botoes,text="Exportar",command=exportar_historico).pack(side="left",expand=True,fill="x",padx=(0,5))
        ctk.CTkButton(botoes,text="Limpar histórico",fg_color="#b94a48",hover_color="#963b39",command=limpar_historico).pack(side="left",expand=True,fill="x",padx=5)
        ctk.CTkButton(botoes,text="Fechar",command=janela.destroy).pack(side="left",expand=True,fill="x",padx=(5,0))

    def abrir_configuracoes(self) -> None:
        janela = ctk.CTkToplevel(self)
        janela.title("Configurações")
        janela.geometry("650x470")
        janela.resizable(False, False)
        janela.grab_set()

        ctk.CTkLabel(
            janela,
            text="Configurações",
            font=("Segoe UI", 25, "bold"),
        ).pack(anchor="w", padx=30, pady=(25, 18))

        def campo_pasta(titulo: str, valor: Path):
            ctk.CTkLabel(
                janela,
                text=titulo,
                font=("Segoe UI", 13, "bold"),
            ).pack(anchor="w", padx=30)

            linha = ctk.CTkFrame(janela, fg_color="transparent")
            linha.pack(fill="x", padx=30, pady=(5, 14))

            entrada = ctk.CTkEntry(linha, height=38)
            entrada.pack(side="left", fill="x", expand=True, padx=(0, 8))
            entrada.insert(0, str(valor))

            def escolher() -> None:
                pasta = filedialog.askdirectory()
                if pasta:
                    entrada.delete(0, "end")
                    entrada.insert(0, pasta)

            ctk.CTkButton(
                linha,
                text="Escolher",
                width=100,
                height=38,
                command=escolher,
            ).pack(side="right")
            return entrada

        entrada_saves = campo_pasta(
            "Pasta de saves do Project Zomboid",
            self.pasta_saves,
        )
        entrada_destino = campo_pasta(
            "Pasta principal dos backups",
            self.destino_base,
        )

        ctk.CTkLabel(
            janela,
            text="Quantidade máxima de backups por mundo",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", padx=30)

        entrada_maximo = ctk.CTkEntry(janela, width=120, height=38)
        entrada_maximo.pack(anchor="w", padx=30, pady=(5, 22))
        entrada_maximo.insert(0, str(self.max_backups))

        def salvar() -> None:
            try:
                maximo = int(entrada_maximo.get())
                if not 1 <= maximo <= 100:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Valor inválido",
                    "Informe um número entre 1 e 100.",
                    parent=janela,
                )
                return

            self.pasta_saves = Path(entrada_saves.get().strip())
            self.destino_base = Path(entrada_destino.get().strip())
            self.max_backups = maximo

            self.configuracoes.update(
                {
                    "pasta_saves": str(self.pasta_saves),
                    "destino_base": str(self.destino_base),
                    "max_backups": self.max_backups,
                    "ultimo_mundo": "",
                }
            )
            salvar_configuracoes(self.configuracoes)

            self.carregar_mundos()
            tipos = sorted({m.tipo_label for m in self.mundos})
            self.combo_tipo.configure(
                values=tipos or ["Nenhum mundo encontrado"]
            )
            self.selecionar_mundo_inicial()
            self.atualizar_tudo()
            janela.destroy()

        ctk.CTkButton(
            janela,
            text="Salvar e detectar mundos",
            height=44,
            font=("Segoe UI", 14, "bold"),
            command=salvar,
        ).pack(fill="x", padx=30, pady=(0, 25))
