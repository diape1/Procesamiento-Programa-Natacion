import unittest
import pandas as pd
import numpy as np
import warnings
import os

class TestExhaustiveApp(unittest.TestCase):
    def setUp(self):
        # Create a mock CSV for tests
        self.mock_csv = "test_resultados_historicos_mock.csv"
        data = {
            "Nombre": ["Ian", "Ian", "Iker", "Iker", "Ian"],
            "Año": ["2023", "2024", "2023", "2024", "2024"],
            "Tipo": ["Oficial", "Recreativa", "Oficial", "Recreativa", "Oficial"],
            "Evento": ["Ev1", "Ev2", "Ev1", "Ev2", "Ev3"],
            "Fecha Inicio": ["2023-01-01", "2024-01-01", "2023-01-01", "2024-01-01", "2024-05-01"],
            "Fecha Fin": ["2023-01-01", "2024-01-01", "2023-01-01", "2024-01-01", "2024-05-01"],
            "Curso": ["CC", "CL", "CC", "CL", "CL"],
            "Estilo": ["Libre", "Libre", "Libre", "Dorso", "Mariposa"],
            "Distancia": ["50", "50", "50", "100", "50"],
            "Posicion": ["1", "2", "3", "1", "1"],
            "Tiempo": ["30.00", "28.50", "35.00", "1:15.00", "29.00"],
            "Segundos": [30.00, 28.50, 35.00, 75.00, 29.00],
            "Participantes": ["10", "15", "10", "8", "12"]
        }
        self.df_mock = pd.DataFrame(data)
        self.df_mock.to_csv(self.mock_csv, index=False)

    def tearDown(self):
        if os.path.exists(self.mock_csv):
            os.remove(self.mock_csv)
            
    def test_analytics_calculations_ian_libre_50(self):
        # Test analytics math for Ian, Libre, 50m
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            df = pd.read_csv(self.mock_csv).dropna(subset=["Segundos", "Fecha Inicio"])
            
            an_filtered = df[(df["Estilo"] == "Libre") & (df["Distancia"].astype(str) == "50") & (df["Nombre"] == "Ian")]
            an_filtered = an_filtered.sort_values(by="Fecha Inicio", ascending=True)
            
            self.assertFalse(an_filtered.empty, "Data should exist for Ian Libre 50")
            
            mejor_tiempo = an_filtered["Segundos"].min()
            self.assertEqual(mejor_tiempo, 28.50)
            
            primer_tiempo = an_filtered["Segundos"].iloc[0]
            ultimo_tiempo = an_filtered["Segundos"].iloc[-1]
            
            self.assertEqual(primer_tiempo, 30.00)
            self.assertEqual(ultimo_tiempo, 28.50)
            
            mejora = primer_tiempo - ultimo_tiempo
            self.assertEqual(mejora, 1.50)
            
            # Assert no warnings were raised
            self.assertEqual(len(w), 0, "Warnings were raised during calculation")

    def test_analytics_missing_swimmer(self):
        # Test when there's no data for a combination (e.g., Iker in Mariposa 50)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            df = pd.read_csv(self.mock_csv).dropna(subset=["Segundos", "Fecha Inicio"])
            an_filtered = df[(df["Estilo"] == "Mariposa") & (df["Distancia"].astype(str) == "50") & (df["Nombre"] == "Iker")]
            
            self.assertTrue(an_filtered.empty, "Data should be empty for Iker Mariposa 50")
            self.assertEqual(len(w), 0, "Warnings were raised during empty check")

    def test_malformed_time_format(self):
        # Test time parsing logic inside app.py simulation
        def parse_t(t_str):
            try:
                if ':' in t_str:
                    p = t_str.split(':')
                    return int(p[0]) * 60 + float(p[1])
                else:
                    return float(t_str)
            except:
                return None
                
        # Correct formats
        self.assertEqual(parse_t("45.20"), 45.20)
        self.assertEqual(parse_t("1:05.50"), 65.50)
        
        # Incorrect formats
        self.assertIsNone(parse_t("abc"))
        self.assertIsNone(parse_t("1:ab"))
        self.assertIsNone(parse_t(""))
        
    def test_file_format_corruption(self):
        # Test what happens if the CSV is missing columns or corrupted
        corrupted_csv = "corrupted_test.csv"
        with open(corrupted_csv, "w") as f:
            f.write("Col1,Col2\nVal1,Val2")
            
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                df = pd.read_csv(corrupted_csv)
                # App logic tries to dropna on "Segundos" and "Fecha Inicio"
                # This should raise a KeyError or we should catch it safely
                df_clean = df.dropna(subset=["Segundos", "Fecha Inicio"])
                self.fail("Should have raised KeyError")
            except KeyError:
                pass # Expected behavior
        
        if os.path.exists(corrupted_csv):
            os.remove(corrupted_csv)

    def test_pivot_table_generation(self):
        # Ensure pivot_table works for charting both swimmers
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            df = pd.read_csv(self.mock_csv).dropna(subset=["Segundos", "Fecha Inicio"])
            an_filtered = df[(df["Estilo"] == "Libre") & (df["Distancia"].astype(str) == "50")]
            an_filtered = an_filtered.sort_values(by="Fecha Inicio", ascending=True)
            
            chart_df = an_filtered.pivot_table(index="Fecha Inicio", columns="Nombre", values="Segundos", aggfunc="min")
            
            # Should have columns Ian and Iker
            self.assertIn("Ian", chart_df.columns)
            self.assertIn("Iker", chart_df.columns)
            
            # Ian at 2023-01-01 is 30.0, Iker is 35.0
            self.assertEqual(chart_df.loc["2023-01-01", "Ian"], 30.0)
            self.assertEqual(chart_df.loc["2023-01-01", "Iker"], 35.0)

if __name__ == '__main__':
    unittest.main()
