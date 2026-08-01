from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable


def localizar_winrar() -> Path | None:
    caminhos = [
        Path(os.environ.get("ProgramFiles", "C:/Program Files"))
        / "WinRAR"
        / "WinRAR.exe",
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
        / "WinRAR"
        / "WinRAR.exe",
    ]

    for caminho in caminhos:
        if caminho.exists():
            return caminho

    encontrado = shutil.which("WinRAR.exe")
    return Path(encontrado) if encontrado else None


def localizar_tar() -> Path | None:
    encontrado = shutil.which("tar")
    return Path(encontrado) if encontrado else None


def _extensao_backup() -> str:
    return ".rar" if sys.platform == "win32" else ".tar.gz"


def _glob_backups() -> str:
    return "Zomboid_Backup_*.rar" if sys.platform == "win32" else "Zomboid_Backup_*.tar.gz"


def validar_pastas(raiz: Path, pastas: Iterable[str]) -> tuple[str, ...]:
    nomes = tuple(pastas)

    if not nomes:
        raise ValueError("Nenhuma pasta foi selecionada para o backup.")

    faltando = [
        nome for nome in nomes
        if not (raiz / nome).is_dir()
    ]

    if faltando:
        raise FileNotFoundError(
            "Não encontrei estas pastas:\n"
            + "\n".join(f"• {nome}" for nome in faltando)
            + f"\n\nLocal verificado:\n{raiz}"
        )

    return nomes


def apagar_backups_antigos(destino: Path, max_backups: int) -> None:
    backups = sorted(
        destino.glob(_glob_backups()),
        key=lambda arquivo: arquivo.stat().st_mtime,
        reverse=True,
    )

    for arquivo in backups[max_backups:]:
        arquivo.unlink(missing_ok=True)


def formatar_tamanho(bytes_total: int) -> str:
    tamanho = float(bytes_total)

    for unidade in ("B", "KB", "MB", "GB", "TB"):
        if tamanho < 1024 or unidade == "TB":
            return f"{tamanho:.2f} {unidade}"
        tamanho /= 1024

    return f"{bytes_total} B"


def _criar_backup_windows(
    winrar: Path,
    raiz: Path,
    nomes: tuple[str, ...],
    arquivo_backup: Path,
) -> None:
    comando = [
        str(winrar),
        "a",
        "-r",
        "-ep1",
        "-m5",
        "-y",
        "-idq",
        str(arquivo_backup),
        *nomes,
    ]

    processo = subprocess.run(
        comando,
        cwd=raiz,
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    if processo.returncode not in (0, 1):
        erro = processo.stderr.strip() or processo.stdout.strip()
        raise RuntimeError(
            f"O WinRAR não conseguiu criar o backup.\n\n{erro}"
        )


def _criar_backup_linux(
    tar: Path,
    raiz: Path,
    nomes: tuple[str, ...],
    arquivo_backup: Path,
) -> None:
    comando = [
        str(tar),
        "-czf",
        str(arquivo_backup),
        "-C",
        str(raiz),
        *nomes,
    ]

    processo = subprocess.run(
        comando,
        capture_output=True,
        text=True,
    )

    if processo.returncode != 0:
        erro = processo.stderr.strip() or processo.stdout.strip()
        raise RuntimeError(
            f"O tar não conseguiu criar o backup.\n\n{erro}"
        )


def criar_backup(
    raiz: Path,
    pastas: Iterable[str],
    destino: Path,
    max_backups: int = 2,
    atualizar_status: Callable[[str], None] | None = None,
    atualizar_progresso: Callable[[int, str], None] | None = None,
) -> dict[str, str]:
    def status(mensagem: str) -> None:
        if atualizar_status:
            atualizar_status(mensagem)

    def progresso(valor: int, mensagem: str) -> None:
        valor = max(0, min(100, valor))
        if atualizar_progresso:
            atualizar_progresso(valor, mensagem)
        status(mensagem)

    progresso(5, "Verificando as pastas do mundo...")
    nomes = validar_pastas(raiz, pastas)

    destino.mkdir(parents=True, exist_ok=True)
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    extensao = _extensao_backup()
    arquivo_backup = destino / f"Zomboid_Backup_{data_hora}{extensao}"

    if sys.platform == "win32":
        progresso(15, "Procurando o WinRAR...")
        winrar = localizar_winrar()

        if winrar is None:
            raise FileNotFoundError(
                "O WinRAR não foi encontrado.\n\n"
                "Verifique se ele está instalado em:\n"
                "C:\\Program Files\\WinRAR"
            )

        progresso(25, "Preparando a pasta de destino...")
        progresso(35, "Compactando o mundo com o WinRAR...")
        _criar_backup_windows(winrar, raiz, nomes, arquivo_backup)

    else:
        progresso(15, "Procurando o tar...")
        tar = localizar_tar()

        if tar is None:
            raise FileNotFoundError(
                "O 'tar' não foi encontrado no sistema.\n\n"
                "Instale-o com: sudo apt install tar"
            )

        progresso(25, "Preparando a pasta de destino...")
        progresso(35, "Compactando o mundo com tar...")
        _criar_backup_linux(tar, raiz, nomes, arquivo_backup)

    progresso(82, "Verificando o arquivo criado...")

    if not arquivo_backup.exists():
        raise RuntimeError("O arquivo de backup não foi criado.")

    progresso(90, "Removendo backups antigos...")
    apagar_backups_antigos(destino, max_backups)

    tamanho = formatar_tamanho(arquivo_backup.stat().st_size)
    progresso(100, "Backup concluído.")

    return {
        "arquivo": arquivo_backup.name,
        "caminho": str(arquivo_backup),
        "tamanho": tamanho,
        "data": datetime.now().strftime("%d/%m/%Y às %H:%M:%S"),
    }
