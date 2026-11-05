#analytic.py
"""Construção da camada Analítica do ENEM a partir dos arquivos Gold.

Não altera Gold. Os produtos são agregados e não contêm identificadores individuais.
"""
from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import duckdb
import pandas as pd

DIMENSIONS = [
    "ano",
    "CO_MUNICIPIO_TERRITORIO",
    "NO_MUNICIPIO_TERRITORIO",
    "TIPO_REFERENCIA_TERRITORIAL",
]
SCORE_COLUMNS = {
    "REDACAO": "NU_NOTA_REDACAO",
    "OBJETIVA": "NU_NOTA_OBJETIVA",
    "CN": "NU_NOTA_CN",
    "CH": "NU_NOTA_CH",
    "LC": "NU_NOTA_LC",
    "MT": "NU_NOTA_MT",
}
EXPECTED_PRODUCTS = [
    "demografia_municipal",
    "faixa_etaria_municipal",
    "presenca_municipal",
    "desempenho_redacao_municipal",
    "desempenho_objetiva_municipal",
    "desempenho_areas_municipal",
    "escola_municipal",
    "desempenho_grupos_municipal",
]


def _ident(name: str) -> str:
    """Quote a known column identifier for DuckDB SQL."""
    return '"' + name.replace('"', '""') + '"'


def _schema(con: duckdb.DuckDBPyConnection, path: str) -> set[str]:
    rows = con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [path]).fetchall()
    return {row[0] for row in rows}


def _expr(columns: set[str], name: str, cast: str | None = None) -> str:
    if name not in columns:
        return f"CAST(NULL AS {cast})" if cast else "NULL"
    return f"TRY_CAST({_ident(name)} AS {cast})" if cast else _ident(name)


def _source_sql(path: str) -> str:
    # Path is passed as a query parameter; this helper is not used to interpolate it.
    return "read_parquet(?)"


def _base_select(con, path: str, columns: set[str]) -> pd.DataFrame:
    required = {"NU_ANO", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO", "TIPO_REFERENCIA_TERRITORIAL"}
    missing = required - columns
    if missing:
        raise ValueError(f"Gold sem colunas territoriais obrigatórias: {sorted(missing)} | {path}")
    sql = f"""
        SELECT
            TRY_CAST(NU_ANO AS INTEGER) AS ano,
            CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR) AS CO_MUNICIPIO_TERRITORIO,
            CAST(NO_MUNICIPIO_TERRITORIO AS VARCHAR) AS NO_MUNICIPIO_TERRITORIO,
            CAST(TIPO_REFERENCIA_TERRITORIAL AS VARCHAR) AS TIPO_REFERENCIA_TERRITORIAL
        FROM read_parquet(?)
    """
    return con.execute(sql, [path]).df()


def _group_sql(con, path: str, columns: set[str], select_metrics: str, where: str = "TRUE") -> pd.DataFrame:
    sql = f"""
        SELECT
            TRY_CAST(NU_ANO AS INTEGER) AS ano,
            CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR) AS CO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(NO_MUNICIPIO_TERRITORIO AS VARCHAR)) AS NO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(TIPO_REFERENCIA_TERRITORIAL AS VARCHAR)) AS TIPO_REFERENCIA_TERRITORIAL,
            {select_metrics}
        FROM read_parquet(?)
        WHERE {where}
        GROUP BY TRY_CAST(NU_ANO AS INTEGER), CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR)
    """
    return con.execute(sql, [path]).df()


def _sex_codes(con, path: str, columns: set[str]) -> tuple[str | None, str | None]:
    if "TP_SEXO" not in columns:
        return None, None
    values = con.execute(
        "SELECT DISTINCT UPPER(TRIM(CAST(TP_SEXO AS VARCHAR))) "
        "FROM read_parquet(?) WHERE TP_SEXO IS NOT NULL",
        [path],
    ).fetchall()
    domain = {str(row[0]) for row in values if row[0] is not None}
    if {"0", "1"}.issubset(domain):
        return "0", "1"
    if {"1", "2"}.issubset(domain):
        return "1", "2"
    if {"M", "F"}.issubset(domain):
        return "M", "F"
    return None, None


def _stats_sql(con, path: str, column: str, prefix: str = "", columns: set[str] | None = None) -> pd.DataFrame:
    c = _ident(column) if columns is None or column in columns else "NULL"
    return con.execute(
        f"""
        SELECT
            TRY_CAST(NU_ANO AS INTEGER) AS ano,
            CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR) AS CO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(NO_MUNICIPIO_TERRITORIO AS VARCHAR)) AS NO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(TIPO_REFERENCIA_TERRITORIAL AS VARCHAR)) AS TIPO_REFERENCIA_TERRITORIAL,
            COUNT({c}) AS n_validos{prefix},
            COUNT(*) FILTER (WHERE TRY_CAST({c} AS DOUBLE) = 0) AS n_zeros{prefix},
            AVG(TRY_CAST({c} AS DOUBLE)) AS media{prefix},
            AVG(TRY_CAST({c} AS DOUBLE)) FILTER (WHERE TRY_CAST({c} AS DOUBLE) > 0) AS media_positivas{prefix},
            MEDIAN(TRY_CAST({c} AS DOUBLE)) AS mediana{prefix},
            STDDEV_SAMP(TRY_CAST({c} AS DOUBLE)) AS std{prefix},
            QUANTILE_CONT(TRY_CAST({c} AS DOUBLE), 0.25) AS q1{prefix},
            QUANTILE_CONT(TRY_CAST({c} AS DOUBLE), 0.75) AS q3{prefix}
        FROM read_parquet(?)
        GROUP BY TRY_CAST(NU_ANO AS INTEGER), CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR)
        """,
        [path],
    ).df()


def _concat(frames: list[pd.DataFrame], columns: list[str] | None = None) -> pd.DataFrame:
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame(columns=columns or [])


def _sort(df: pd.DataFrame, extra: list[str] | None = None) -> pd.DataFrame:
    keys = [c for c in ["ano", "CO_MUNICIPIO_TERRITORIO", *(extra or [])] if c in df.columns]
    return df.sort_values(keys, kind="stable").reset_index(drop=True) if len(df) and keys else df.reset_index(drop=True)


def _sources_for_product(manifesto: pd.DataFrame, product: str, start: int, end: int) -> pd.DataFrame:
    m = manifesto.copy()
    m["ano"] = pd.to_numeric(m["ano"], errors="raise").astype(int)
    m = m[m["ano"].between(start, end)]
    if product in {"demografia_municipal", "faixa_etaria_municipal"}:
        m = m[(m["ano"] <= 2023) | (m["base"] == "participantes")]
        m = m[m["ano"] <= 2023] if not (m["ano"] >= 2024).any() else m
        m = m[(m["ano"] < 2024) | (m["base"] == "participantes")]
    elif product in {"presenca_municipal", "desempenho_redacao_municipal", "desempenho_areas_municipal", "escola_municipal"}:
        m = m[(m["ano"] < 2024) | (m["base"] == "resultados")]
    elif product == "desempenho_objetiva_municipal":
        m = m[m["ano"] <= 2008]
    elif product == "desempenho_grupos_municipal":
        m = m[(m["ano"] < 2024) | (m["base"] == "resultados")]
    return m.sort_values(["ano", "base"]).reset_index(drop=True)


def _make_demography(con, path, columns, ano, base):
    male, female = _sex_codes(con, path, columns)
    if male is None or female is None:
        male_expr = "CAST(NULL AS BIGINT) AS n_masculino"
        female_expr = "CAST(NULL AS BIGINT) AS n_feminino"
    else:
        male_expr = f"COUNT(*) FILTER (WHERE UPPER(TRIM(CAST(TP_SEXO AS VARCHAR))) = '{male}') AS n_masculino"
        female_expr = f"COUNT(*) FILTER (WHERE UPPER(TRIM(CAST(TP_SEXO AS VARCHAR))) = '{female}') AS n_feminino"
    sex_expr = _expr(columns, "TP_SEXO")
    age_expr = _expr(columns, "TP_FAIXA_ETARIA")
    sql = f"""
        SELECT TRY_CAST(NU_ANO AS INTEGER) AS ano,
            CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR) AS CO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(NO_MUNICIPIO_TERRITORIO AS VARCHAR)) AS NO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(TIPO_REFERENCIA_TERRITORIAL AS VARCHAR)) AS TIPO_REFERENCIA_TERRITORIAL,
            COUNT(*) AS n_participantes,
            {male_expr}, {female_expr},
            COUNT({age_expr}) AS n_faixa_etaria_informada
        FROM read_parquet(?)
        GROUP BY TRY_CAST(NU_ANO AS INTEGER), CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR)
    """
    df = con.execute(sql, [path]).df()
    df["base_origem"] = base
    denom = df["n_participantes"].where(df["n_participantes"] != 0)
    df["pct_masculino"] = 100 * df["n_masculino"] / denom
    df["pct_feminino"] = 100 * df["n_feminino"] / denom
    return df


def _make_age(con, path, columns, base):
    age = _expr(columns, "TP_FAIXA_ETARIA", "VARCHAR")
    sql = f"""
        SELECT TRY_CAST(NU_ANO AS INTEGER) AS ano,
            CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR) AS CO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(NO_MUNICIPIO_TERRITORIO AS VARCHAR)) AS NO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(TIPO_REFERENCIA_TERRITORIAL AS VARCHAR)) AS TIPO_REFERENCIA_TERRITORIAL,
            {age} AS TP_FAIXA_ETARIA, COUNT(*) AS n_participantes
        FROM read_parquet(?)
        WHERE {age} IS NOT NULL
        GROUP BY TRY_CAST(NU_ANO AS INTEGER), CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR), {age}
    """
    df = con.execute(sql, [path]).df()
    df["base_origem"] = base
    return df


def _make_presence(con, path, columns, base):
    presence = _expr(columns, "TP_PRESENCA", "INTEGER")
    sql = f"""
        SELECT TRY_CAST(NU_ANO AS INTEGER) AS ano,
            CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR) AS CO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(NO_MUNICIPIO_TERRITORIO AS VARCHAR)) AS NO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(TIPO_REFERENCIA_TERRITORIAL AS VARCHAR)) AS TIPO_REFERENCIA_TERRITORIAL,
            COUNT(*) AS n_registros,
            COUNT(*) FILTER (WHERE {presence} = 1) AS n_presentes,
            COUNT(*) FILTER (WHERE {presence} = 0) AS n_ausentes,
            COUNT({presence}) AS n_presenca_informada
        FROM read_parquet(?)
        GROUP BY TRY_CAST(NU_ANO AS INTEGER), CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR)
    """
    df = con.execute(sql, [path]).df()
    denom = df["n_presenca_informada"].where(df["n_presenca_informada"] != 0)
    df["pct_presenca"] = 100 * df["n_presentes"] / denom
    df["pct_ausencia"] = 100 * df["n_ausentes"] / denom
    df["base_origem"] = base
    return df


def _make_school(con, path, columns, ano, base):
    dep = _expr(columns, "TP_DEPENDENCIA_ADM_ESC", "INTEGER")
    common = """
        TRY_CAST(NU_ANO AS INTEGER) AS ano,
        CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR) AS CO_MUNICIPIO_TERRITORIO,
        ANY_VALUE(CAST(NO_MUNICIPIO_TERRITORIO AS VARCHAR)) AS NO_MUNICIPIO_TERRITORIO,
        ANY_VALUE(CAST(TIPO_REFERENCIA_TERRITORIAL AS VARCHAR)) AS TIPO_REFERENCIA_TERRITORIAL,
        COUNT(*) AS n_registros,
    """
    if ano < 2001:
        metrics = ", ".join(f"CAST(NULL AS BIGINT) AS {c}" for c in [
            "n_escola_federal", "n_escola_estadual", "n_escola_municipal", "n_escola_privada", "n_escola_nao_informada", "n_dependencia_informada"])
    else:
        metrics = f"""
            COUNT(*) FILTER (WHERE {dep}=1) AS n_escola_federal,
            COUNT(*) FILTER (WHERE {dep}=2) AS n_escola_estadual,
            COUNT(*) FILTER (WHERE {dep}=3) AS n_escola_municipal,
            COUNT(*) FILTER (WHERE {dep}=4) AS n_escola_privada,
            COUNT(*) FILTER (WHERE {dep} IS NULL) AS n_escola_nao_informada,
            COUNT({dep}) AS n_dependencia_informada
        """
    df = con.execute(
        f"SELECT {common} {metrics} FROM read_parquet(?) GROUP BY TRY_CAST(NU_ANO AS INTEGER), CAST(CO_MUNICIPIO_TERRITORIO AS VARCHAR)",
        [path],
    ).df()
    for label, col in {
        "pct_escola_federal": "n_escola_federal",
        "pct_escola_estadual": "n_escola_estadual",
        "pct_escola_municipal": "n_escola_municipal",
        "pct_escola_privada": "n_escola_privada",
        "pct_escola_nao_informada": "n_escola_nao_informada",
    }.items():
        df[label] = 100 * df[col] / df["n_registros"].where(df["n_registros"] != 0)
    df["base_origem"] = base
    return df


def _make_groups(con, path, columns, ano, base):
    disciplines: list[tuple[str, str]] = [("REDACAO", "NU_NOTA_REDACAO")]
    if ano <= 2008:
        disciplines.append(("OBJETIVA", "NU_NOTA_OBJETIVA"))
    else:
        disciplines.extend([(x, SCORE_COLUMNS[x]) for x in ["CN", "CH", "LC", "MT"]])

    male, female = _sex_codes(con, path, columns)
    pieces = []
    if ano < 2024 and male is not None and female is not None and "TP_SEXO" in columns:
        sex_case = f"CASE WHEN UPPER(TRIM(CAST(TP_SEXO AS VARCHAR)))='{male}' THEN 'MASCULINO' WHEN UPPER(TRIM(CAST(TP_SEXO AS VARCHAR)))='{female}' THEN 'FEMININO' END"
        for disc, col in disciplines:
            if col in columns:
                pieces.append(f"SELECT NU_ANO AS ano, CO_MUNICIPIO_TERRITORIO, NO_MUNICIPIO_TERRITORIO, TIPO_REFERENCIA_TERRITORIAL, 'SEXO' tipo_grupo, {sex_case} grupo, '{disc}' disciplina, TRY_CAST({_ident(col)} AS DOUBLE) nota FROM base WHERE {sex_case} IS NOT NULL")
    if ano >= 2001 and "TP_DEPENDENCIA_ADM_ESC" in columns:
        school_case = "CASE TRY_CAST(TP_DEPENDENCIA_ADM_ESC AS INTEGER) WHEN 1 THEN 'FEDERAL' WHEN 2 THEN 'ESTADUAL' WHEN 3 THEN 'MUNICIPAL' WHEN 4 THEN 'PRIVADA' ELSE 'NAO_INFORMADA' END"
        for disc, col in disciplines:
            if col in columns:
                pieces.append(f"SELECT NU_ANO AS ano, CO_MUNICIPIO_TERRITORIO, NO_MUNICIPIO_TERRITORIO, TIPO_REFERENCIA_TERRITORIAL, 'ESCOLA' tipo_grupo, {school_case} grupo, '{disc}' disciplina, TRY_CAST({_ident(col)} AS DOUBLE) nota FROM base")
    if ano < 2024 and "TP_FAIXA_ETARIA" in columns:
        for disc, col in disciplines:
            if col in columns:
                pieces.append(f"SELECT NU_ANO AS ano, CO_MUNICIPIO_TERRITORIO, NO_MUNICIPIO_TERRITORIO, TIPO_REFERENCIA_TERRITORIAL, 'FAIXA_ETARIA' tipo_grupo, CAST(TP_FAIXA_ETARIA AS VARCHAR) grupo, '{disc}' disciplina, TRY_CAST({_ident(col)} AS DOUBLE) nota FROM base WHERE TP_FAIXA_ETARIA IS NOT NULL")
    if not pieces:
        return pd.DataFrame(columns=DIMENSIONS + ["tipo_grupo", "grupo", "disciplina", "n_validos", "n_zeros", "media", "media_positivas", "mediana", "std", "q1", "q3", "base_origem"])
    source_columns = [c for c in ["NU_ANO", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO", "TIPO_REFERENCIA_TERRITORIAL", "TP_SEXO", "TP_DEPENDENCIA_ADM_ESC", "TP_FAIXA_ETARIA", *[col for _, col in disciplines]] if c in columns]
    select = ", ".join(_ident(c) for c in dict.fromkeys(source_columns))
    sql = f"""
        WITH base AS (SELECT {select} FROM read_parquet(?)),
        grupos AS ({' UNION ALL '.join(pieces)})
        SELECT TRY_CAST(g.ano AS INTEGER) AS ano,
            CAST(g.CO_MUNICIPIO_TERRITORIO AS VARCHAR) AS CO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(g.NO_MUNICIPIO_TERRITORIO AS VARCHAR)) AS NO_MUNICIPIO_TERRITORIO,
            ANY_VALUE(CAST(g.TIPO_REFERENCIA_TERRITORIAL AS VARCHAR)) AS TIPO_REFERENCIA_TERRITORIAL,
            g.tipo_grupo, g.grupo, g.disciplina,
            COUNT(g.nota) AS n_validos,
            COUNT(*) FILTER (WHERE g.nota = 0) AS n_zeros,
            AVG(g.nota) AS media,
            AVG(g.nota) FILTER (WHERE g.nota > 0) AS media_positivas,
            MEDIAN(g.nota) AS mediana, STDDEV_SAMP(g.nota) AS std,
            QUANTILE_CONT(g.nota, 0.25) AS q1, QUANTILE_CONT(g.nota, 0.75) AS q3
        FROM grupos g
        WHERE g.grupo IS NOT NULL AND g.nota IS NOT NULL
        GROUP BY g.ano, g.CO_MUNICIPIO_TERRITORIO, g.tipo_grupo, g.grupo, g.disciplina
    """
    df = con.execute(sql, [path]).df()
    df["base_origem"] = base
    return df


def _save_parquet_safe(df: pd.DataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.stem + "_tmp" + destination.suffix)
    if temporary.exists():
        temporary.unlink()
    df.to_parquet(temporary, index=False, compression="zstd")
    check = pd.read_parquet(temporary)
    if list(check.columns) != list(df.columns) or len(check) != len(df):
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Falha na validação do Parquet temporário: {destination}")
    temporary.replace(destination)


def executar_camada_analitica(
    *, manifesto_gold_path: str | Path, metadata_dir: str | Path,
    analytic_root: str | Path, uf: str, ano_inicial: int = 1998,
    ano_final: int = 2025, gravar: bool = True,
) -> dict[str, Any]:
    """Constrói oito produtos analíticos, catálogo e manifesto."""
    started = time.perf_counter()
    metadata_dir = Path(metadata_dir)
    analytic_dir = Path(analytic_root) / f"uf={uf}"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    analytic_dir.mkdir(parents=True, exist_ok=True)
    manifesto_path = Path(manifesto_gold_path)
    if not manifesto_path.exists():
        raise FileNotFoundError(f"Manifesto Gold não encontrado: {manifesto_path}")
    manifesto = pd.read_csv(manifesto_path, sep=";", dtype={"uf": "string"})
    required = {"ano", "base", "arquivo_gold"}
    missing = required - set(manifesto.columns)
    if missing:
        raise ValueError(f"Colunas ausentes no manifesto Gold: {sorted(missing)}")
    manifesto["ano"] = pd.to_numeric(manifesto["ano"], errors="raise").astype(int)
    manifesto = manifesto[manifesto["ano"].between(ano_inicial, ano_final)].copy()
    manifesto = manifesto[manifesto["arquivo_gold"].map(lambda x: Path(str(x)).is_file())]
    if manifesto.empty:
        raise ValueError("Manifesto não contém arquivos Gold existentes no período solicitado.")
    if "uf" in manifesto.columns:
        ufs = set(manifesto["uf"].dropna().astype(str).str.upper())
        if ufs and ufs != {uf.upper()}:
            raise ValueError(f"UF do manifesto ({sorted(ufs)}) não corresponde à UF solicitada ({uf}).")

    con = duckdb.connect()
    frames: dict[str, list[pd.DataFrame]] = {name: [] for name in EXPECTED_PRODUCTS}
    sources_audit = []
    try:
        for _, row in manifesto.sort_values(["ano", "base"]).iterrows():
            ano, base, path = int(row["ano"]), str(row["base"]), str(row["arquivo_gold"])
            columns = _schema(con, path)
            _base_select(con, path, columns)  # validates required dimensions
            sources_audit.append({"ano": ano, "base": base, "arquivo_gold": path, "colunas": len(columns)})

            if (ano < 2024 and base == "enem") or (ano >= 2024 and base == "participantes"):
                frames["demografia_municipal"].append(_make_demography(con, path, columns, ano, base))
                frames["faixa_etaria_municipal"].append(_make_age(con, path, columns, base))

            if (ano < 2024 and base == "enem") or (ano >= 2024 and base == "resultados"):
                frames["presenca_municipal"].append(_make_presence(con, path, columns, base))
                redacao = _stats_sql(con, path, "NU_NOTA_REDACAO", columns=columns)
                redacao["n_avaliados_redacao"] = redacao["n_validos"]
                frames["desempenho_redacao_municipal"].append(redacao)
                frames["escola_municipal"].append(_make_school(con, path, columns, ano, base))
                frames["desempenho_grupos_municipal"].append(_make_groups(con, path, columns, ano, base))

            if ano <= 2008 and base == "enem":
                objetiva = _stats_sql(con, path, "NU_NOTA_OBJETIVA", columns=columns)
                objetiva["n_avaliados_objetiva"] = objetiva["n_validos"]
                frames["desempenho_objetiva_municipal"].append(objetiva)

            if ano >= 2009 and ((ano < 2024 and base == "enem") or (ano >= 2024 and base == "resultados")):
                parts = []
                for area in ["CN", "CH", "LC", "MT"]:
                    col = SCORE_COLUMNS[area]
                    if col not in columns:
                        continue
                    df = _stats_sql(con, path, col, prefix=f"_{area}", columns=columns)
                    df = df.rename(columns={
                        f"n_validos_{area}": f"n_validos_{area.lower()}",
                        f"n_zeros_{area}": f"n_zeros_{area.lower()}",
                        f"media_{area}": f"media_{area.lower()}",
                        f"media_positivas_{area}": f"media_positivas_{area.lower()}",
                        f"mediana_{area}": f"mediana_{area.lower()}",
                        f"std_{area}": f"std_{area.lower()}",
                        f"q1_{area}": f"q1_{area.lower()}",
                        f"q3_{area}": f"q3_{area.lower()}",
                    })
                    parts.append(df)
                if parts:
                    areas = parts[0]
                    for part in parts[1:]:
                        metric_cols = [c for c in part.columns if c not in DIMENSIONS]
                        areas = areas.merge(part[DIMENSIONS + metric_cols], on=["ano", "CO_MUNICIPIO_TERRITORIO"], how="outer", validate="one_to_one", suffixes=("", "_dup"))
                        dup = [c for c in areas.columns if c.endswith("_dup")]
                        if dup:
                            areas = areas.drop(columns=dup)
                    for area in ["cn", "ch", "lc", "mt"]:
                        valid_col = f"n_validos_{area}"
                        if valid_col in areas.columns:
                            areas[f"n_avaliados_{area}"] = areas[valid_col]
                    areas["base_origem"] = base
                    frames["desempenho_areas_municipal"].append(areas)

        products = {name: _sort(_concat(parts)) for name, parts in frames.items()}
        # Product-specific source coverage and output metadata.
        descriptions = {
            "demografia_municipal": ("ano_municipio", "Contagem de registros e distribuição por sexo; sem identificadores individuais."),
            "faixa_etaria_municipal": ("ano_municipio_faixa_etaria", "Distribuição por faixa etária, município e ano."),
            "presenca_municipal": ("ano_municipio", "Presença/ausência geral quando TP_PRESENCA está disponível."),
            "desempenho_redacao_municipal": ("ano_municipio", "Estatísticas de redação, com contagem de zeros e média adicional apenas das notas positivas."),
            "desempenho_objetiva_municipal": ("ano_municipio", "Estatísticas da nota objetiva, incluindo zeros e média adicional das notas positivas, 1998–2008."),
            "desempenho_areas_municipal": ("ano_municipio", "Estatísticas de CN, CH, LC e MT, com contagem de zeros e média adicional das notas positivas, a partir de 2009."),
            "escola_municipal": ("ano_municipio", "Distribuição por dependência administrativa da escola."),
            "desempenho_grupos_municipal": ("ano_municipio_grupo_disciplina", "Desempenho por sexo, escola e faixa etária; em 2024–2025, apenas grupos disponíveis em resultados."),
        }
        catalog_rows, manifest_rows = [], []
        for name in EXPECTED_PRODUCTS:
            df = products[name]
            if df.empty:
                raise RuntimeError(f"Produto analítico vazio: {name}. Verifique fontes e disponibilidade de variáveis.")
            destination = analytic_dir / f"{name}.parquet"
            if gravar:
                _save_parquet_safe(df, destination)
            granularity, description = descriptions[name]
            years = sorted(pd.to_numeric(df["ano"], errors="coerce").dropna().astype(int).unique().tolist()) if "ano" in df else []
            period = f"{min(years)}-{max(years)}" if years else "sem_periodo"
            size_mb = destination.stat().st_size / (1024**2) if gravar and destination.exists() else None
            catalog_rows.append({"produto": name, "arquivo_analytic": str(destination), "granularidade": granularity, "periodo": period, "linhas": len(df), "colunas": len(df.columns), "descricao": description})
            manifest_rows.append({"camada": "analytic", "uf": uf.upper(), "produto": name, "granularidade": granularity, "periodo": period, "arquivo_analytic": str(destination), "n_linhas": len(df), "n_colunas": len(df.columns), "tamanho_mb": size_mb})

        catalog = pd.DataFrame(catalog_rows)
        manifest_out = pd.DataFrame(manifest_rows)
        if gravar:
            catalog.to_csv(metadata_dir / f"catalogo_analytic_{uf.upper()}.csv", sep=";", index=False, encoding="utf-8-sig")
            manifest_out.to_csv(metadata_dir / f"manifesto_analytic_{uf.upper()}.csv", sep=";", index=False, encoding="utf-8-sig")
        audit = pd.DataFrame(sources_audit)
        return {"produtos": products, "catalogo": catalog, "manifesto": manifest_out, "fontes_auditadas": audit, "duracao_segundos": time.perf_counter() - started, "diretorio_analytic": analytic_dir}
    finally:
        con.close()
