from __future__ import annotations

import sys
import customtkinter as ctk

from gui import ZomboidBackupApp
from settings import CONFIG_PADRAO, carregar_configuracoes


class TelaDeAbertura(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Zomboid Backup Manager")
        self.geometry("520x320")
        self.resizable(False, False)
        self.overrideredirect(True)

        self.configure(fg_color="#111318")

        self.centralizar_janela()

        painel = ctk.CTkFrame(
            self,
            corner_radius=22,
            fg_color="#191c22",
            border_width=1,
            border_color="#2a303b",
        )
        painel.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12,
        )

        titulo = ctk.CTkLabel(
            painel,
            text="PROJECT ZOMBOID",
            font=("Segoe UI", 31, "bold"),
        )
        titulo.pack(pady=(65, 0))

        subtitulo = ctk.CTkLabel(
            painel,
            text="BACKUP MANAGER",
            font=("Segoe UI", 17, "bold"),
            text_color="#8d96a8",
        )
        subtitulo.pack(pady=(2, 35))

        self.barra = ctk.CTkProgressBar(
            painel,
            width=330,
            height=10,
            mode="indeterminate",
        )
        self.barra.pack()
        self.barra.start()

        self.carregando = ctk.CTkLabel(
            painel,
            text="Detectando sistema operacional...",
            font=("Segoe UI", 12),
            text_color="#788191",
        )
        self.carregando.pack(pady=(12, 0))

        autor = ctk.CTkLabel(
            painel,
            text="Desenvolvido por BooDoSnes",
            font=("Segoe UI", 10),
            text_color="#5f6774",
        )
        autor.pack(side="bottom", pady=20)

        self.after(600, self._detectar_sistema)
        self.after(2200, self.abrir_programa)

    def centralizar_janela(self) -> None:
        largura = 520
        altura = 320

        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()

        posicao_x = int((largura_tela - largura) / 2)
        posicao_y = int((altura_tela - altura) / 2)

        self.geometry(
            f"{largura}x{altura}+{posicao_x}+{posicao_y}"
        )

    def _detectar_sistema(self) -> None:
        nome = "Linux" if sys.platform != "win32" else "Windows"
        self.carregando.configure(text=f"Sistema detectado: {nome}")
        self.after(700, self._detectar_pasta_saves)

    def _detectar_pasta_saves(self) -> None:
        config = carregar_configuracoes()
        pasta = config["pasta_saves"]
        self.carregando.configure(text=f"Pasta de saves: {pasta}")
        self.after(700, lambda: self.carregando.configure(text="Carregando seus backups..."))

    def abrir_programa(self) -> None:
        self.barra.stop()
        self.destroy()

        aplicativo = ZomboidBackupApp()
        aplicativo.mainloop()


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    abertura = TelaDeAbertura()
    abertura.mainloop()


if __name__ == "__main__":
    main()