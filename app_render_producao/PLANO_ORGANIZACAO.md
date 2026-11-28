# Organização da aplicação de produção

## Estrutura mantida no runtime

- `app.py`: ponto de entrada Dash/Gunicorn.
- `preparar_consumo_dashboard.py`: único programa auxiliar na raiz, responsável por preparar os Parquets de uma UF.
- `dash_utils/config.py`, `config_dash.py`, `data_loader.py`, `features_names.py`, `perf.py` e `ufs.py`.
- `pages/`: páginas de Visão Geral, Mapas, Análise Municipal e Perfil dos Participantes.
- `data/consumo/uf=<UF>/`: quatro Parquets originais preservados e uma pasta `otimizado/` com oito arquivos (`painel`, `faixa`, `grupo` e `dsp`, cada um separado em `ESC` e `PROVA`) e o manifesto.
- `data/shapefiles/<UF>_Municipios_2025/`: arquivos do shapefile da UF.
- `requirements.txt`, `.python-version`, `.gitignore` e `README.md`.

## Preparação por UF

A preparação é executada individualmente, sem menu ou lista interativa:

```bash
python preparar_consumo_dashboard.py --uf PA
```

O programa valida a existência dos quatro originais, identifica preparação já concluída ou parcial, e só reprocessa um conjunto existente com `--force`. O `--dry-run` permite verificar a origem sem gravar arquivos.

Os oito arquivos otimizados são gravados diretamente em:

```text
data/consumo/uf=PA/otimizado/
```

Os nomes identificam a base e a referência, por exemplo `painel_ESC.parquet` e `painel_PROVA.parquet`. O manifesto reúne os detalhes técnicos e o resultado das validações.

A preparação seleciona as colunas necessárias ao dashboard, normaliza `RESIDENCIA` para `ESC`, separa `ESC` e `PROVA`, grava Row Groups de 100.000 linhas com compressão Snappy e dictionary encoding. Não há downcast na gravação.

## Regras do loader

- Usa os Parquets otimizados quando os oito arquivos e o manifesto estão presentes e válidos.
- Usa os quatro originais quando ainda não existe preparação otimizada.
- Interrompe com orientação explícita quando encontra um conjunto parcial ou manifesto inválido.
- Aplica o downcasting durante a leitura, conforme os testes de memória.
- Mantém o cache de dados limitado a uma combinação UF/referência.

## Fora do runtime

Não fazem parte da aplicação de produção os notebooks de diagnóstico, variantes de `app_*.py`, logs, diretórios temporários, scripts experimentais, pastas de sandbox e arquivos de resultados de experimentos. O preparador fica na raiz, sem diretório `scripts/`.

## Escopo inicial

A distribuição inicial disponibiliza PA. Outras UFs só devem ser habilitadas no dashboard depois que os quatro Parquets originais, os oito otimizados e o shapefile correspondente estiverem preparados e validados.
