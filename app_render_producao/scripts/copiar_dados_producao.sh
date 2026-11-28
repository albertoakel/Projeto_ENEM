#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_APP_RENDER="${SOURCE_APP_RENDER:-$HERE/../app_render}"
SOURCE_APP_RENDER="$(cd "$SOURCE_APP_RENDER" && pwd)"
DEST="$HERE/data/consumo_otimizado/parquet_variants"
SOURCE_VARIANTS="$SOURCE_APP_RENDER/_diagnosticos_memoria_07/parquet_variants"

if [[ ! -d "$SOURCE_VARIANTS" ]]; then
  echo "Diretório de variantes não encontrado: $SOURCE_VARIANTS" >&2
  exit 1
fi

for base in painel faixa grupo dsp; do
  for ref in ESC PROVA; do
    src="$SOURCE_VARIANTS/$base/separado_rg_100000/$ref.parquet"
    dst="$DEST/$base/separado_rg_100000/$ref.parquet"
    if [[ ! -f "$src" ]]; then
      echo "Parquet ausente: $src" >&2
      exit 1
    fi
    mkdir -p "$(dirname "$dst")"
    cp -f "$src" "$dst"
    echo "Copiado: $base/$ref.parquet"
  done
done

shape_src="$SOURCE_APP_RENDER/data/shapefiles/PA_Municipios_2025"
shape_dst="$HERE/data/shapefiles/PA_Municipios_2025"
for ext in shp shx dbf prj; do
  f="$shape_src/PA_Municipios_2025.$ext"
  if [[ ! -f "$f" ]]; then
    echo "Componente do shapefile ausente: $f" >&2
    exit 1
  fi
done
mkdir -p "$shape_dst"
cp -f "$shape_src"/PA_Municipios_2025.{shp,shx,dbf,prj} "$shape_dst/"
if [[ -f "$shape_src/PA_Municipios_2025.cpg" ]]; then
  cp -f "$shape_src/PA_Municipios_2025.cpg" "$shape_dst/"
fi

echo
echo "Dados de produção preparados em: $HERE/data"
