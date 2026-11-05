
import duckdb

from src.enem_pipeline.config import (
    STAGING_DIR,
    SEPARADOR_MICRODADOS,
    obter_codificacao_microdados,
)

diretorio = STAGING_DIR / "ano=2024"
con = duckdb.connect()

for nome in ["PARTICIPANTES_2024.csv", "RESULTADOS_2024.csv"]:
    caminho = (diretorio / nome).as_posix().replace("'", "''")
    separador = SEPARADOR_MICRODADOS
    codificacao = obter_codificacao_microdados(2024)

    consulta = f"""
        SELECT
            COUNT(*) AS total_registros,
            COUNT(*) FILTER (
                WHERE SG_UF_PROVA = 'PA'
            ) AS registros_pa
        FROM read_csv(
            '{caminho}',
            delim='{separador}',
            header=true,
            encoding='{codificacao}',
            sample_size=20000
        )
    """

    resultado = con.execute(consulta).fetchone()
    print(
        f"{nome}: total={resultado[0]:,} | "
        f"PA={resultado[1]:,}"
    )

con.close()
