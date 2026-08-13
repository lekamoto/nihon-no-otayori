import unittest
from datetime import datetime, timezone, timedelta
import generate_daily

BR_TZ = timezone(timedelta(hours=-3))

class TestStrictDateAndNoFallback(unittest.TestCase):

    def setUp(self):
        self.target_dt = datetime(2026, 8, 13, 15, 0, 0, tzinfo=BR_TZ)

    def test_is_same_day_valid(self):
        # Data exatamente igual em RFC 822 / RSS format
        pubdate_today = "Thu, 13 Aug 2026 10:00:00 +0000"
        self.assertTrue(generate_daily.is_same_day(pubdate_today, self.target_dt))

    def test_is_same_day_invalid_yesterday(self):
        # Data de ontem
        pubdate_yesterday = "Wed, 12 Aug 2026 23:59:59 +0000"
        self.assertFalse(generate_daily.is_same_day(pubdate_yesterday, self.target_dt))

    def test_scenario_a_today_news(self):
        """TESTE A: RSS contém notícias de hoje. Resultado esperado: notícias de hoje aparecem."""
        pubdate = "Thu, 13 Aug 2026 12:00:00 -0300"
        self.assertTrue(generate_daily.is_same_day(pubdate, self.target_dt))

    def test_scenario_b_yesterday_news_only(self):
        """TESTE B: RSS contém somente notícias de ontem. Resultado esperado: nenhuma notícia aparece."""
        pubdate = "Wed, 12 Aug 2026 18:00:00 -0300"
        self.assertFalse(generate_daily.is_same_day(pubdate, self.target_dt))

    def test_scenario_c_mixed_news(self):
        """TESTE C: RSS contém notícias de ontem e de hoje. Resultado esperado: somente notícias de hoje são aceitas."""
        items = [
            {"pubDate": "Wed, 12 Aug 2026 18:00:00 -0300", "title": "Noticia de Ontem"},
            {"pubDate": "Thu, 13 Aug 2026 09:00:00 -0300", "title": "Noticia de Hoje"}
        ]
        valid_items = [item for item in items if generate_daily.is_same_day(item["pubDate"], self.target_dt)]
        self.assertEqual(len(valid_items), 1)
        self.assertEqual(valid_items[0]["title"], "Noticia de Hoje")

    def test_scenario_d_empty_rss_no_hardcoded(self):
        """TESTE D: RSS está vazio ou indisponível. Resultado esperado: nenhuma notícia hardcoded nem elemento de notícia aparece."""
        original_fetch = generate_daily.fetch_rss
        generate_daily.fetch_rss = lambda url, target_dt, max_items=4: []
        try:
            jp_file, pt_file = generate_daily.generate_edition(self.target_dt)
            with open(jp_file, "r", encoding="utf-8") as f:
                content = f.read()
            # Confirmar ausência de notícias hardcoded antigas
            self.assertNotIn("古都・奈良", content)
            self.assertNotIn("徳島県で 日本最古級", content)
            self.assertNotIn("巡回 (じゅんかい)", content)
            # Confirmar que o bloco de notícias está 100% vazio (sem itens de notícia no HTML)
            self.assertNotIn('<div class="news-title">', content)
            self.assertNotIn('<div class="news-body">', content)
        finally:
            generate_daily.fetch_rss = original_fetch

if __name__ == '__main__':
    unittest.main()
