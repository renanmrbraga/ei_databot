from __future__ import annotations

import shutil
import time
import zipfile
from pathlib import Path

import requests
import urllib3
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from etl.core.config import (
    ANO_ED_BASICA_ATUAL,
    CPC_FOLDER,
    ED_BASICA_FOLDER,
    ENADE_FOLDER,
    IDD_FOLDER,
    IGC_FOLDER,
    RAW_GEO,
    SUPERIOR_FOLDER,
    URL_ED_BASICA_ATUAL,
    URL_GEO_MUNICIPIOS,
    URLS_CENSO_SUPERIOR,
    URLS_CONCEITO_ENADE,
    URLS_CPC,
    URLS_ED_BASICA_HISTORICO,
    URLS_IDD,
    URLS_IGC,
    ZIP_CACHE_DIR,
)
from etl.core.logger import get_logger

# Desativa avisos de certificado SSL autoassinado/legado dos servidores gov.br no Windows
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = get_logger()

# Pausa de cortesia entre requisições reais ao servidor
PAUSA_ENTRE_DOWNLOADS_SEG = 1.5


def _criar_sessao_http() -> requests.Session:
    session = requests.Session()
    session.verify = False
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
        }
    )
    retries = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def baixar_arquivo(
    url: str,
    destino: Path,
    session: requests.Session,
    forcar: bool = False,
) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists() and destino.stat().st_size > 0 and not forcar:
        logger.info("Arquivo já em cache: %s", destino.name)
        return destino

    logger.info("Baixando: %s -> %s", url, destino.name)

    with session.get(url, stream=True, timeout=120) as resposta:
        resposta.raise_for_status()
        total_bytes = int(resposta.headers.get("content-length", 0))

        temp_path = destino.with_suffix(destino.suffix + ".part")
        with (
            open(temp_path, "wb") as f,
            tqdm(
                total=total_bytes,
                unit="B",
                unit_scale=True,
                desc=destino.name,
                leave=False,
            ) as barra,
        ):
            for chunk in resposta.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    barra.update(len(chunk))

        temp_path.replace(destino)

    logger.info("Concluído: %s", destino.name)
    time.sleep(PAUSA_ENTRE_DOWNLOADS_SEG)
    return destino


def extrair_arquivos_do_zip(
    caminho_zip: Path,
    pasta_destino: Path,
    termos_busca: list[str],
) -> list[Path]:
    extraidos: list[Path] = []
    pasta_destino.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(caminho_zip, "r") as zf:
        for membro in zf.namelist():
            if membro.endswith("/"):
                continue

            membro_upper = membro.upper()
            if any(
                termo.upper() in membro_upper for termo in termos_busca
            ) and membro_upper.endswith((".CSV", ".TXT", ".XLSX")):
                nome_arquivo = Path(membro).name
                destino_final = pasta_destino / nome_arquivo

                if not destino_final.exists() or destino_final.stat().st_size == 0:
                    logger.info("Extraindo: %s", nome_arquivo)
                    with zf.open(membro) as src, open(destino_final, "wb") as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)

                extraidos.append(destino_final)

    return extraidos


def sincronizar_referencia_geo(session: requests.Session) -> None:
    destino_geo = Path(RAW_GEO)
    try:
        baixar_arquivo(URL_GEO_MUNICIPIOS, destino_geo, session=session)
    except (requests.RequestException, OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        logger.warning("Falha ao sincronizar referência geográfica (geo.csv): %s", exc)


def extrair_ies_e_cursos_censo_superior(caminho_zip: Path, pasta_destino: Path, ano: int) -> None:
    """Extrai Cursos e IES, padronizando a nomenclatura histórica do INEP para a camada Bronze."""
    pasta_destino.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(caminho_zip, "r") as zf:
        for membro in zf.namelist():
            if membro.endswith("/"):
                continue

            membro_upper = membro.upper()

            # 1. Extração de Cursos
            if "MICRODADOS_CADASTRO_CURSOS" in membro_upper and membro_upper.endswith(".CSV"):
                destino = pasta_destino / f"MICRODADOS_CADASTRO_CURSOS_{ano}.CSV"
                if not destino.exists() or destino.stat().st_size == 0:
                    logger.info("Extraindo Cursos %s -> %s", ano, destino.name)
                    with zf.open(membro) as src, open(destino, "wb") as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)

            # 2. Extração de IES (Trata o padrão antigo CADASTRO_IES e o novo ED_SUP_IES)
            elif any(
                termo in membro_upper
                for termo in ["MICRODADOS_ED_SUP_IES", "MICRODADOS_CADASTRO_IES"]
            ) and membro_upper.endswith(".CSV"):
                destino = pasta_destino / f"MICRODADOS_ED_SUP_IES_{ano}.CSV"
                if not destino.exists() or destino.stat().st_size == 0:
                    logger.info("Extraindo e padronizando IES %s -> %s", ano, destino.name)
                    with zf.open(membro) as src, open(destino, "wb") as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)


def sincronizar_censo_superior(session: requests.Session) -> None:
    for ano, url in URLS_CENSO_SUPERIOR.items():
        zip_path = ZIP_CACHE_DIR / f"censo_superior_{ano}.zip"
        try:
            baixar_arquivo(url, zip_path, session=session)
            extrair_ies_e_cursos_censo_superior(zip_path, SUPERIOR_FOLDER, ano)
        except (
            requests.RequestException,
            OSError,
            zipfile.BadZipFile,
            zipfile.LargeZipFile,
        ) as exc:
            logger.warning("Falha ao sincronizar Censo Superior %s: %s", ano, exc)


def sincronizar_censo_escolar(session: requests.Session) -> None:
    # Histórico (2018 a 2024)
    for ano, url in URLS_ED_BASICA_HISTORICO.items():
        zip_path = ZIP_CACHE_DIR / f"censo_escolar_{ano}.zip"
        try:
            baixar_arquivo(url, zip_path, session=session)
            extrair_arquivos_do_zip(
                zip_path,
                ED_BASICA_FOLDER,
                termos_busca=[
                    "microdados_ed_basica",
                    "Tabela_Escola",
                    "Tabela_Matricula",
                ],
            )
        except (
            requests.RequestException,
            OSError,
            zipfile.BadZipFile,
            zipfile.LargeZipFile,
        ) as exc:
            logger.warning("Falha ao sincronizar Censo Escolar %s: %s", ano, exc)

    # Ano atual (2025)
    zip_atual = ZIP_CACHE_DIR / f"censo_escolar_{ANO_ED_BASICA_ATUAL}.zip"
    try:
        baixar_arquivo(URL_ED_BASICA_ATUAL, zip_atual, session=session)
        extrair_arquivos_do_zip(
            zip_atual,
            ED_BASICA_FOLDER,
            termos_busca=[
                "microdados_ed_basica",
                "Tabela_Escola",
                "Tabela_Matricula",
            ],
        )
    except (requests.RequestException, OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        logger.warning(
            "Falha ao sincronizar Censo Escolar %s: %s",
            ANO_ED_BASICA_ATUAL,
            exc,
        )


def sincronizar_planilhas_indicadores(session: requests.Session) -> None:
    grupos = [
        ("ENADE", ENADE_FOLDER, URLS_CONCEITO_ENADE),
        ("CPC", CPC_FOLDER, URLS_CPC),
        ("IDD", IDD_FOLDER, URLS_IDD),
        ("IGC", IGC_FOLDER, URLS_IGC),
    ]

    for nome_grupo, pasta_destino, mapa_urls in grupos:
        pasta_destino.mkdir(parents=True, exist_ok=True)
        for nome_arquivo, url in mapa_urls.items():
            destino = pasta_destino / nome_arquivo
            try:
                baixar_arquivo(url, destino, session=session)
            except (
                requests.RequestException,
                OSError,
                zipfile.BadZipFile,
                zipfile.LargeZipFile,
            ) as exc:
                logger.warning(
                    "Falha ao baixar %s (%s): %s",
                    nome_grupo,
                    nome_arquivo,
                    exc,
                )


def main() -> None:
    logger.info("Iniciando rotina de download e sincronização de todas as fontes...")
    with _criar_sessao_http() as session:
        sincronizar_referencia_geo(session)
        sincronizar_censo_superior(session)
        sincronizar_censo_escolar(session)
        sincronizar_planilhas_indicadores(session)
    logger.info("Sincronização de downloads finalizada.")


if __name__ == "__main__":
    main()
