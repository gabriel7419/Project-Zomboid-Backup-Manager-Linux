from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def formatar_tamanho(bytes_total: int) -> str:
    tamanho = float(bytes_total)

    for unidade in ("B", "KB", "MB", "GB", "TB"):
        if tamanho < 1024 or unidade == "TB":
            return f"{tamanho:.2f} {unidade}"

        tamanho /= 1024

    return f"{bytes_total} B"


def abrir_pasta(caminho: Path) -> None:
    caminho.mkdir(parents=True, exist_ok=True)

    if sys.platform == "win32":
        os.startfile(str(caminho))
    else:
        subprocess.Popen(["xdg-open", str(caminho)])


def abrir_jogo() -> None:
    if sys.platform == "win32":
        subprocess.Popen(
            ["cmd", "/c", "start", "", "steam://rungameid/108600"],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        subprocess.Popen(["xdg-open", "steam://rungameid/108600"])


def jogo_esta_aberto() -> bool:
    if sys.platform == "win32":
        processo = subprocess.run(
            ["tasklist"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        lista = processo.stdout.lower()
        nomes_possiveis = (
            "projectzomboid64.exe",
            "projectzomboid32.exe",
            "projectzomboid.exe",
            "zuluplatformx64architecture.exe",
        )
        return any(nome in lista for nome in nomes_possiveis)
    else:
        processo = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
        )
        lista = processo.stdout.lower()
        nomes_possiveis = (
            "projectzomboid64",
            "projectzomboid32",
            "projectzomboid",
        )
        return any(nome in lista for nome in nomes_possiveis)
from datetime import datetime


def registrar_historico(
    pasta_logs: Path,
    operacao: str,
    detalhes: str,
) -> None:
    pasta_logs.mkdir(
        parents=True,
        exist_ok=True,
    )

    arquivo_log = pasta_logs / "historico.txt"

    data = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    with arquivo_log.open(
        "a",
        encoding="utf-8",
    ) as arquivo:
        arquivo.write(
            f"[{data}] {operacao} - {detalhes}\n"
        )