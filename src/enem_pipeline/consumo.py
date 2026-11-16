
"""Construção e auditoria da camada de Consumo a partir da Analítica."""

#update 06/11/2025
from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import pandas as pd

DIMENSIONS = [
    "ano",
    "CO_MUNICIPIO_TERRITORIO",
    "NO_MUNICIPIO_TERRITORIO",
    "TIPO_REFERENCIA_TERRITORIAL",
]

MERGE_KEYS = [
    "ano",
    "CO_MUNICIPIO_TERRITORIO",
    "TIPO_REFERENCIA_TERRITORIAL",
]

PANEL_PRODUCTS = [
    "demografia_municipal",
    "presenca_municipal",
    "desempenho_redacao_municipal",
    "desempenho_objetiva_municipal",
    "desempenho_areas_municipal",
    "escola_municipal",
]

CONSUMO_PRODUCTS = [
    "painel_municipal",
    "faixa_etaria_municipal",
    "desempenho_grupos_municipal",
    "desempenho_sexo_faixa_etaria_municipal",
]


def _save_parquet_safe(df: pd.DataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(
        destination.stem + "_tmp" + destination.suffix
    )

    if temporary.exists():
        temporary.unlink()

    df.to_parquet(temporary, index=False, compression="zstd")
    check = pd.read_parquet(temporary)

    if list(check.columns) != list(df.columns) or len(check) != len(df):
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            f"Falha na validação do Parquet temporário: {destination}"
        )

    temporary.replace(destination)


def _read_analytic_manifest(path: Path, uf: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Manifesto Analytic não encontrado: {path}"
        )

    df = pd.read_csv(path, sep=";", dtype={"uf": "string"})

    required = {"produto", "arquivo_analytic"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Colunas ausentes no manifesto Analytic: {sorted(missing)}"
        )

    if df["produto"].duplicated().any():
        raise ValueError("Manifesto Analytic contém produtos duplicados.")

    if "uf" in df.columns:
        ufs = set(df["uf"].dropna().astype(str).str.upper())
        if ufs and ufs != {uf.upper()}:
            raise ValueError(
                f"UF do manifesto ({sorted(ufs)}) não corresponde "
                f"à UF solicitada ({uf})."
            )

    missing_files = [
        str(p)
        for p in df["arquivo_analytic"]
        if not Path(str(p)).is_file()
    ]

    if missing_files:
        raise FileNotFoundError(
            "Arquivos Analytic ausentes:\n" + "\n".join(missing_files)
        )

    required_products = set(
        PANEL_PRODUCTS
        + [
            "faixa_etaria_municipal",
            "desempenho_grupos_municipal",
            "desempenho_sexo_faixa_etaria_municipal",
        ]
    )

    missing_products = required_products - set(df["produto"])

    if missing_products:
        raise ValueError(
            f"Produtos Analytic ausentes no manifesto: "
            f"{sorted(missing_products)}"
        )

    return df


def _assert_unique(
    df: pd.DataFrame,
    keys: list[str],
    product: str,
) -> None:
    missing = set(keys) - set(df.columns)

    if missing:
        raise ValueError(
            f"{product}: colunas-chave ausentes: {sorted(missing)}"
        )

    dup = int(df.duplicated(keys).sum())

    if dup:
        raise ValueError(
            f"{product}: {dup} duplicidades na chave {keys}."
        )


def _harmonize_dimensions(
    base: pd.DataFrame,
    other: pd.DataFrame,
    product: str,
) -> None:
    """Verifica nomes municipais dentro da mesma referência territorial."""

    col = "NO_MUNICIPIO_TERRITORIO"

    if not all(
        c in base.columns and c in other.columns
        for c in MERGE_KEYS + [col]
    ):
        return

    left = base[MERGE_KEYS + [col]].drop_duplicates()
    right = other[MERGE_KEYS + [col]].drop_duplicates()

    check = left.merge(
        right,
        on=MERGE_KEYS,
        how="inner",
        suffixes=("_base", "_other"),
    )

    bad = check[
        check[f"{col}_base"].notna()
        & check[f"{col}_other"].notna()
        & (
            check[f"{col}_base"].astype(str)
            != check[f"{col}_other"].astype(str)
        )
    ]

    if not bad.empty:
        raise ValueError(
            f"{product}: nomes municipais divergentes; exemplos:\n"
            f"{bad.head(5)}"
        )


def executar_camada_consumo(
    *,
    manifesto_analytic_path: str | Path,
    metadata_dir: str | Path,
    consumo_root: str | Path,
    uf: str,
    gravar: bool = True,
) -> dict[str, Any]:
    """Constrói painel municipal e produtos auxiliares."""

    started = time.perf_counter()

    metadata_dir = Path(metadata_dir)
    consumo_dir = Path(consumo_root) / f"uf={uf}"

    metadata_dir.mkdir(parents=True, exist_ok=True)
    consumo_dir.mkdir(parents=True, exist_ok=True)

    manifesto = _read_analytic_manifest(
        Path(manifesto_analytic_path),
        uf,
    )

    paths = dict(
        zip(manifesto["produto"], manifesto["arquivo_analytic"])
    )

    frames = {
        name: pd.read_parquet(path)
        for name, path in paths.items()
    }

    for df in frames.values():
        if "ano" in df.columns:
            df["ano"] = pd.to_numeric(
                df["ano"], errors="raise"
            ).astype("Int64")

        if "CO_MUNICIPIO_TERRITORIO" in df.columns:
            df["CO_MUNICIPIO_TERRITORIO"] = (
                df["CO_MUNICIPIO_TERRITORIO"].astype("string")
            )

    # ---------------------------------------------------------
    # 1. Base demográfica
    # ---------------------------------------------------------

    painel = frames["demografia_municipal"].copy()

    _assert_unique(
        painel,
        MERGE_KEYS,
        "demografia_municipal",
    )

    painel = painel[
        [c for c in DIMENSIONS if c in painel.columns]
        + [
            c for c in painel.columns
            if c not in DIMENSIONS and c != "base_origem"
        ]
    ]

    # ---------------------------------------------------------
    # 2. Integração dos produtos municipais
    # ---------------------------------------------------------

    rename_map = {
        "presenca_municipal": {
            "n_registros": "n_registros_presenca"
        },
        "desempenho_redacao_municipal": {
            "n_validos": "n_validos_redacao",
            "n_zeros": "n_zeros_redacao",
            "media": "media_redacao",
            "media_positivas": "media_positivas_redacao",
            "mediana": "mediana_redacao",
            "std": "std_redacao",
            "q1": "q1_redacao",
            "q3": "q3_redacao",
        },
        "desempenho_objetiva_municipal": {
            "n_validos": "n_validos_objetiva",
            "n_zeros": "n_zeros_objetiva",
            "media": "media_objetiva",
            "media_positivas": "media_positivas_objetiva",
            "mediana": "mediana_objetiva",
            "std": "std_objetiva",
            "q1": "q1_objetiva",
            "q3": "q3_objetiva",
        },
        "escola_municipal": {
            "n_registros": "n_registros_escola"
        },
    }

    for product in PANEL_PRODUCTS[1:]:

        df = frames[product].copy()

        _assert_unique(df, MERGE_KEYS, product)

        _harmonize_dimensions(
            painel,
            df,
            product,
        )

        df = df.rename(
            columns=rename_map.get(product, {})
        )

        metrics = [
            c for c in df.columns
            if c not in DIMENSIONS and c != "base_origem"
        ]

        collisions = set(metrics) & set(painel.columns)

        if collisions:
            raise ValueError(
                f"Colunas métricas duplicadas ao integrar "
                f"{product}: {sorted(collisions)}"
            )

        # Outer preserva municípios existentes em apenas uma base.
        # A referência territorial faz parte da chave.
        painel = painel.merge(
            df[MERGE_KEYS + ["NO_MUNICIPIO_TERRITORIO"] + metrics],
            on=MERGE_KEYS,
            how="outer",
            validate="one_to_one",
            suffixes=("", "_other"),
        )

        # Recupera o nome municipal quando a linha veio somente
        # do produto que está sendo integrado.
        nome_other = "NO_MUNICIPIO_TERRITORIO_other"

        if nome_other in painel.columns:
            painel["NO_MUNICIPIO_TERRITORIO"] = (
                painel["NO_MUNICIPIO_TERRITORIO"]
                .fillna(painel[nome_other])
            )
            painel = painel.drop(columns=[nome_other])

    # ---------------------------------------------------------
    # 3. Indicadores derivados
    # ---------------------------------------------------------

    if "n_validos_redacao" in painel.columns:
        painel["n_avaliados_redacao"] = (
            painel["n_validos_redacao"]
        )

    if "n_validos_objetiva" in painel.columns:
        painel["n_avaliados_objetiva"] = (
            painel["n_validos_objetiva"]
        )

    painel = painel.sort_values(
        [
            "ano",
            "TIPO_REFERENCIA_TERRITORIAL",
            "CO_MUNICIPIO_TERRITORIO",
        ]
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # 4. Produtos auxiliares
    # ---------------------------------------------------------

    faixa = frames["faixa_etaria_municipal"].copy()
    grupos = frames["desempenho_grupos_municipal"].copy()
    sexo_faixa = frames[
        "desempenho_sexo_faixa_etaria_municipal"
    ].copy()

    _assert_unique(
        painel,
        MERGE_KEYS,
        "painel_municipal",
    )

    _assert_unique(
        faixa,
        MERGE_KEYS + ["TP_FAIXA_ETARIA"],
        "faixa_etaria_municipal",
    )

    _assert_unique(
        grupos,
        MERGE_KEYS + [
            "tipo_grupo",
            "grupo",
            "disciplina",
        ],
        "desempenho_grupos_municipal",
    )

    _assert_unique(
        sexo_faixa,
        MERGE_KEYS + [
            "sexo",
            "faixa_etaria",
            "disciplina",
        ],
        "desempenho_sexo_faixa_etaria_municipal",
    )

    products = {
        "painel_municipal": painel,
        "faixa_etaria_municipal": faixa,
        "desempenho_grupos_municipal": grupos,
        "desempenho_sexo_faixa_etaria_municipal": sexo_faixa,
    }

    descriptions = {
        "painel_municipal": (
            "ano_municipio_referencia",
            "Painel integrado de indicadores municipais, "
            "respeitando a referência territorial.",
        ),
        "faixa_etaria_municipal": (
            "ano_municipio_referencia_faixa_etaria",
            "Distribuição de registros por faixa etária, "
            "município, referência territorial e ano.",
        ),
        "desempenho_grupos_municipal": (
            "ano_municipio_referencia_grupo_disciplina",
            "Estatísticas de notas por grupo, disciplina, "
            "município e referência territorial.",
        ),
        "desempenho_sexo_faixa_etaria_municipal": (
            "ano_municipio_referencia_sexo_faixa_etaria_disciplina",
            "Estatísticas de notas por sexo, faixa etária, disciplina, "
            "município e referência territorial.",
        ),
    }

    catalog_rows = []
    manifest_rows = []

    for name, df in products.items():

        destination = consumo_dir / f"{name}.parquet"

        if gravar:
            _save_parquet_safe(df, destination)

        granularity, description = descriptions[name]

        years = (
            sorted(
                pd.to_numeric(
                    df["ano"], errors="coerce"
                ).dropna().astype(int).unique().tolist()
            )
            if "ano" in df
            else []
        )

        period = (
            f"{min(years)}-{max(years)}"
            if years
            else "sem_periodo"
        )

        size_mb = (
            destination.stat().st_size / (1024**2)
            if gravar and destination.exists()
            else None
        )

        catalog_rows.append({
            "produto": name,
            "arquivo_consumo": str(destination),
            "granularidade": granularity,
            "periodo": period,
            "linhas": len(df),
            "colunas": len(df.columns),
            "descricao": description,
        })

        manifest_rows.append({
            "camada": "consumo",
            "uf": uf.upper(),
            "produto": name,
            "granularidade": granularity,
            "periodo": period,
            "arquivo_consumo": str(destination),
            "n_linhas": len(df),
            "n_colunas": len(df.columns),
            "tamanho_mb": size_mb,
        })

    catalog = pd.DataFrame(catalog_rows)
    manifest_out = pd.DataFrame(manifest_rows)

    if gravar:
        catalog.to_csv(
            metadata_dir / f"catalogo_consumo_{uf.upper()}.csv",
            sep=";",
            index=False,
            encoding="utf-8-sig",
        )

        manifest_out.to_csv(
            metadata_dir / f"manifesto_consumo_{uf.upper()}.csv",
            sep=";",
            index=False,
            encoding="utf-8-sig",
        )

    # ---------------------------------------------------------
    # 5. Auditoria
    # ---------------------------------------------------------

    audit_rows = []

    for name, df in products.items():
        audit_rows.append({
            "teste": f"produto_{name}_nao_vazio",
            "ok": not df.empty,
            "obtido": len(df),
        })

    audit_rows.extend([
        {
            "teste": "chave_painel_unica",
            "ok": not painel.duplicated(MERGE_KEYS).any(),
            "obtido": int(painel.duplicated(MERGE_KEYS).sum()),
        },
        {
            "teste": "chave_faixa_unica",
            "ok": not faixa.duplicated(
                MERGE_KEYS + ["TP_FAIXA_ETARIA"]
            ).any(),
            "obtido": int(
                faixa.duplicated(
                    MERGE_KEYS + ["TP_FAIXA_ETARIA"]
                ).sum()
            ),
        },
        {
            "teste": "chave_grupos_unica",
            "ok": not grupos.duplicated(
                MERGE_KEYS + [
                    "tipo_grupo",
                    "grupo",
                    "disciplina",
                ]
            ).any(),
            "obtido": int(
                grupos.duplicated(
                    MERGE_KEYS + [
                        "tipo_grupo",
                        "grupo",
                        "disciplina",
                    ]
                ).sum()
            ),
        },
        {
            "teste": "chave_sexo_faixa_unica",
            "ok": not sexo_faixa.duplicated(
                MERGE_KEYS + [
                    "sexo",
                    "faixa_etaria",
                    "disciplina",
                ]
            ).any(),
            "obtido": int(
                sexo_faixa.duplicated(
                    MERGE_KEYS + [
                        "sexo",
                        "faixa_etaria",
                        "disciplina",
                    ]
                ).sum()
            ),
        },
    ])

    school_cols = {
        "n_registros_escola",
        "n_escola_federal",
        "n_escola_estadual",
        "n_escola_municipal",
        "n_escola_privada",
        "n_escola_nao_informada",
    }

    if school_cols.issubset(painel.columns):

        mask = painel["n_escola_nao_informada"].notna()

        total_categories = painel[
            [
                "n_escola_federal",
                "n_escola_estadual",
                "n_escola_municipal",
                "n_escola_privada",
                "n_escola_nao_informada",
            ]
        ].sum(axis=1, min_count=5)

        mismatch = int(
            (
                (
                    painel.loc[mask, "n_registros_escola"]
                    - total_categories.loc[mask]
                ).fillna(0) != 0
            ).sum()
        )

        audit_rows.append({
            "teste": "reconciliacao_escola",
            "ok": mismatch == 0,
            "obtido": mismatch,
        })

    audit = pd.DataFrame(audit_rows)

    if gravar:
        audit.to_csv(
            metadata_dir / f"auditoria_consumo_{uf.upper()}.csv",
            sep=";",
            index=False,
            encoding="utf-8-sig",
        )

    return {
        "produtos": products,
        "catalogo": catalog,
        "manifesto": manifest_out,
        "auditoria": audit,
        "auditoria_ok": bool(audit["ok"].all()),
        "diretorio_consumo": consumo_dir,
        "duracao_segundos": time.perf_counter() - started,
    }
