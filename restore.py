from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from backup import criar_backup, localizar_winrar, localizar_tar
from utils import jogo_esta_aberto


def _extrair_backup(
    arquivo: Path,
    destino_extracao: Path,
) -> None:
    if sys.platform == "win32":
        winrar = localizar_winrar()
        if winrar is None:
            raise FileNotFoundError("O WinRAR não foi encontrado.")

        processo = subprocess.run(
            [
                str(winrar),
                "x",
                "-y",
                "-idq",
                str(arquivo),
                str(destino_extracao) + os.sep,
            ],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if processo.returncode not in (0, 1):
            erro = processo.stderr.strip() or processo.stdout.strip()
            raise RuntimeError(
                "O WinRAR não conseguiu extrair o backup.\n\n"
                f"{erro}"
            )

    else:
        tar = localizar_tar()
        if tar is None:
            raise FileNotFoundError(
                "O 'tar' não foi encontrado no sistema.\n\n"
                "Instale-o com: sudo apt install tar"
            )

        processo = subprocess.run(
            [
                str(tar),
                "-xzf",
                str(arquivo),
                "-C",
                str(destino_extracao),
            ],
            capture_output=True,
            text=True,
        )

        if processo.returncode != 0:
            erro = processo.stderr.strip() or processo.stdout.strip()
            raise RuntimeError(
                "O tar não conseguiu extrair o backup.\n\n"
                f"{erro}"
            )


def restaurar_backup(
    arquivo_backup: Path,
    raiz: Path,
    pastas: Iterable[str],
    pasta_backups: Path,
    atualizar_status: Callable[[str], None] | None = None,
    atualizar_progresso: Callable[[int, str], None] | None = None,
) -> Path:
    nomes = tuple(pastas)

    def status(mensagem: str) -> None:
        if atualizar_status:
            atualizar_status(mensagem)

    def progresso(valor: int, mensagem: str) -> None:
        valor = max(0, min(100, valor))
        if atualizar_progresso:
            atualizar_progresso(valor, mensagem)
        status(mensagem)

    progresso(5, "Verificando se o jogo está fechado...")

    if jogo_esta_aberto():
        raise RuntimeError(
            "O Project Zomboid está aberto.\n\n"
            "Feche o jogo antes de restaurar um backup."
        )

    progresso(10, "Validando o backup selecionado...")

    if not arquivo_backup.is_file():
        raise FileNotFoundError(
            "O arquivo de backup selecionado não foi encontrado."
        )

    progresso(15, "Verificando compressor disponível...")
    if sys.platform == "win32":
        if localizar_winrar() is None:
            raise FileNotFoundError("O WinRAR não foi encontrado.")
    else:
        if localizar_tar() is None:
            raise FileNotFoundError(
                "O 'tar' não foi encontrado no sistema.\n\n"
                "Instale-o com: sudo apt install tar"
            )

    raiz.mkdir(parents=True, exist_ok=True)
    pasta_backups.mkdir(parents=True, exist_ok=True)

    progresso(20, "Criando backup de segurança do mundo atual...")

    def progresso_seguranca(valor: int, mensagem: str) -> None:
        progresso(
            20 + int(valor * 0.30),
            f"Backup de segurança: {mensagem}",
        )

    resultado = criar_backup(
        raiz=raiz,
        pastas=nomes,
        destino=pasta_backups,
        max_backups=1000,
        atualizar_progresso=progresso_seguranca,
    )

    original = Path(resultado["caminho"])
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    seguranca = (
        pasta_backups
        / f"Seguranca_Antes_Restauracao_{data_hora}.rar"
    )
    original.rename(seguranca)

    progresso(55, "Extraindo o backup selecionado...")
    temporaria = Path(tempfile.mkdtemp(prefix="ZomboidRestore_"))

    try:
        _extrair_backup(arquivo_backup, temporaria)

        progresso(72, "Validando os arquivos extraídos...")

        faltando = [
            nome for nome in nomes
            if not (temporaria / nome).is_dir()
        ]

        if faltando:
            raise RuntimeError(
                "Este backup não pertence ao mundo selecionado.\n\n"
                "Pastas esperadas:\n"
                + "\n".join(f"• {nome}" for nome in nomes)
            )

        progresso(80, "Substituindo os arquivos do mundo...")

        for nome in nomes:
            origem_extraida = temporaria / nome
            destino_atual = raiz / nome

            if destino_atual.exists():
                shutil.rmtree(destino_atual)

            shutil.copytree(origem_extraida, destino_atual)

        progresso(100, "Restauração concluída.")
        return seguranca

    except Exception:
        progresso(
            90,
            "A restauração falhou. Recuperando o mundo atual...",
        )
        _recuperar_seguranca(
            backup_seguranca=seguranca,
            raiz=raiz,
            pastas=nomes,
        )
        raise

    finally:
        shutil.rmtree(temporaria, ignore_errors=True)


def _recuperar_seguranca(
    backup_seguranca: Path,
    raiz: Path,
    pastas: tuple[str, ...],
) -> None:
    temporaria = Path(tempfile.mkdtemp(prefix="ZomboidRecovery_"))

    try:
        _extrair_backup(backup_seguranca, temporaria)

        for nome in pastas:
            origem = temporaria / nome
            destino = raiz / nome

            if not origem.is_dir():
                continue

            if destino.exists():
                shutil.rmtree(destino)

            shutil.copytree(origem, destino)

    except Exception:
        pass

    finally:
        shutil.rmtree(temporaria, ignore_errors=True)
