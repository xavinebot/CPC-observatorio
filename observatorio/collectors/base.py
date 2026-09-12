"""Clase base de los recolectores.

Un recolector descarga UNA fuente y devuelve puntos para una o varias series:
    {serie_id: [(fecha, valor), ...], ...}
Debe lanzar excepción si la fuente no responde o el formato no es el esperado (eso es un FALLO DE EJECUCIÓN,
distinto de un dato sospechoso, que va a cuarentena). `min_records` protege contra descargas vacías o truncadas.
"""
from __future__ import annotations


class Collector:
    name: str = "base"
    series: list[str] = []          # ids de las series que produce
    min_records: int = 1            # nº mínimo de puntos totales que debe devolver una descarga
    supports_backfill: bool = True  # si la fuente da histórico completo en cada descarga

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        raise NotImplementedError

    def check(self, result: dict[str, list[tuple]]) -> None:
        total = sum(len(v) for v in result.values())
        if total < self.min_records:
            raise RuntimeError(f"{self.name}: solo {total} registros (mínimo esperado {self.min_records}); "
                               f"la fuente ha cambiado de formato o la descarga está incompleta")
