from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


PASTA_CONFIG = _base_dir() / "config"
ARQUIVO_CONFIG = PASTA_CONFIG / "settings.json"


def _pasta_desktop_padrao() -> Path:
    if sys.platform == "win32":
        return Path.home() / "Desktop"

    for candidato in ("Desktop", "Área de Trabalho", "Escritorio"):
        pasta = Path.home() / candidato
        if pasta.is_dir():
            return pasta

    return Path.home() / "Desktop"


CONFIG_PADRAO = {
    "pasta_saves": str(Path.home() / "Zomboid" / "Saves"),
    "destino_base": str(
        _pasta_desktop_padrao() / "Backups Project Zomboid"
    ),
    "max_backups": 2,
    "ultimo_mundo": "",
}


def carregar_configuracoes() -> dict[str, Any]:
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)

    if not ARQUIVO_CONFIG.exists():
        salvar_configuracoes(CONFIG_PADRAO.copy())
        return CONFIG_PADRAO.copy()

    try:
        with ARQUIVO_CONFIG.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        configuracoes = CONFIG_PADRAO.copy()

        # Migração automática das versões antigas.
        if "destino" in dados and "destino_base" not in dados:
            dados["destino_base"] = dados["destino"]

        configuracoes.update(dados)

        alterado = False
        for chave in ("pasta_saves", "destino_base"):
            caminho = configuracoes.get(chave, "")
            e_caminho_windows = len(caminho) > 1 and caminho[1] == ":"
            if sys.platform != "win32" and e_caminho_windows:
                configuracoes[chave] = CONFIG_PADRAO[chave]
                alterado = True
            elif sys.platform == "win32" and caminho.startswith("/"):
                configuracoes[chave] = CONFIG_PADRAO[chave]
                alterado = True

        if alterado:
            configuracoes["ultimo_mundo"] = ""
            salvar_configuracoes(configuracoes)

        return configuracoes

    except (json.JSONDecodeError, OSError):
        salvar_configuracoes(CONFIG_PADRAO.copy())
        return CONFIG_PADRAO.copy()


def salvar_configuracoes(configuracoes: dict[str, Any]) -> None:
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)

    with ARQUIVO_CONFIG.open("w", encoding="utf-8") as arquivo:
        json.dump(
            configuracoes,
            arquivo,
            ensure_ascii=False,
            indent=4,
        )
