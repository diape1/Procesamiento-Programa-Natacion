import unittest
import os
from pdf_parser import extract_competition_data, generate_whatsapp_messages
from datetime import datetime

class TestPDFParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pdf_path = os.path.join("Procesados", "Sesion 1 - WM.pdf")
        if not os.path.exists(cls.pdf_path):
            raise unittest.SkipTest(f"No se encontró el archivo de prueba {cls.pdf_path}")
        cls.events = extract_competition_data(cls.pdf_path)

    def test_total_events_extracted(self):
        self.assertEqual(len(self.events), 12, "Deberían extraerse 12 eventos")

    def test_event_1_details(self):
        ev1 = self.events[0]
        self.assertEqual(ev1['num'], '1')
        self.assertEqual(len(ev1['heats']), 3, "Evento 1 debería tener 3 hits")
        total_swimmers = sum(len(h['swimmers']) for h in ev1['heats'])
        self.assertEqual(total_swimmers, 23, "Evento 1 debería tener 23 nadadores")
        first_swimmer = ev1['heats'][0]['swimmers'][0]
        self.assertEqual(first_swimmer['lane'], '0')
        self.assertEqual(first_swimmer['name'], 'Lugo Levario, Azul')

    def test_whatsapp_output_generation(self):
        from pdf_parser import calculate_timeline
        calculate_timeline(self.events, datetime.now(), delay_per_heat=12, delay_per_event=15, delay_style_change=5)
        
        m1, m2, m3 = generate_whatsapp_messages(self.events, "PLAN-CX", ["Reyes Olivera"])
        
        # Test series grouping formatting
        self.assertIn("2 series de 10 y 1 serie de 3", m1)
        
        # Test Ian/Iker precision
        self.assertIn("Reyes Olivera, Ian Alejandro", m2, "El mensaje 2 debería contener el nombre exacto")
        self.assertNotIn("Reyes Olivera, Iker Rodrigo", m2)
        
        # Test PLAN-CX filtering
        self.assertIn("Nadadores del Equipo PLAN-CX", m3)
        self.assertIn("Vera Jacome, Rogelio", m3)

if __name__ == '__main__':
    unittest.main()
