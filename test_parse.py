import unittest
import pandas as pd
import os
import subprocess
import warnings

class TestParseResultados(unittest.TestCase):
    def setUp(self):
        # We assume Tiempos Natación.xlsx is available.
        # Run the script to generate the CSV.
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            subprocess.run(["python", "parse_resultados.py"], check=True)
            self.warnings = w

    def test_csv_exists(self):
        self.assertTrue(os.path.exists("resultados_historicos.csv"))

    def test_csv_columns(self):
        df = pd.read_csv("resultados_historicos.csv")
        expected_cols = ["Nombre", "Año", "Tipo", "Evento", "Fecha Inicio", "Fecha Fin", "Curso", "Estilo", "Distancia", "Posicion", "Tiempo", "Segundos", "Participantes"]
        for col in expected_cols:
            self.assertIn(col, df.columns)

    def test_estacas(self):
        df = pd.read_csv("resultados_historicos.csv")
        # Find 'Las Estacas'
        estacas_df = df[df["Evento"].str.contains("Estacas", case=False, na=False)]
        if not estacas_df.empty:
            for _, row in estacas_df.iterrows():
                self.assertEqual(row["Curso"], "AA")
                self.assertEqual(row["Estilo"], "Libre Contra Corriente")
                self.assertEqual(str(row["Distancia"]).replace('.0',''), "1000")

    def test_cc_cl_resolution(self):
        df = pd.read_csv("resultados_historicos.csv")
        # Verify no NaN in Curso where possible
        official_df = df[df["Tipo"] == "Oficial"]
        for _, row in official_df.iterrows():
            self.assertIn(row["Curso"], ["CC", "CL", "AA"])
            
    def test_dates(self):
        df = pd.read_csv("resultados_historicos.csv")
        # Dates should be YYYY-MM-DD or empty
        for val in df["Fecha Inicio"].dropna():
            if str(val) != "nan" and str(val).strip() != "":
                # Could be string like 'Sexenal' if not found, but we stripped CC/CL.
                # Just check format roughly
                self.assertTrue(len(str(val)) == 10, f"Date format mismatch: {val}")


if __name__ == "__main__":
    unittest.main()

def test_time_parser():
    import parse_resultados
    assert parse_resultados.parse_time_to_seconds("1.15.20") == 75.2
    assert parse_resultados.parse_time_to_seconds("45.20") == 45.2
    assert parse_resultados.parse_time_to_seconds("1:05.40") == 65.4
