import os
import unittest
from datetime import datetime, timezone, timedelta
import generate_daily

BR_TZ = timezone(timedelta(hours=-3))
JP_TZ = timezone(timedelta(hours=9))

class TestAdvancedNewsFiltering(unittest.TestCase):

    def setUp(self):
        self.target_dt = datetime(2026, 8, 13, 20, 0, 0, tzinfo=BR_TZ)

    def test_violent_content_filter_jp(self):
        """Testa se matérias violentas em japonês são descartadas"""
        self.assertTrue(generate_daily.contains_violent_content("愛知県内で水難事故相次ぐ 2人死亡", "8日、事故が発生した", is_japan=True))
        self.assertFalse(generate_daily.contains_violent_content("新しい 観光キャンペーンが 開始", "歴史と自然を楽しむ旅", is_japan=True))

    def test_violent_content_filter_pt(self):
        """Testa se matérias violentas em português são descartadas"""
        self.assertTrue(generate_daily.contains_violent_content("Homem é preso após assalto", "A polícia capturou o suspeito", is_japan=False))
        self.assertFalse(generate_daily.contains_violent_content("Festival cultural reúne centenas de pessoas", "Evento celebrou a arte local", is_japan=False))

    def test_text_summarizer(self):
        """Testa se o resumo sintético reduz frases longas para no máximo 2 frases e limita tamanho"""
        text_long = "Primeira frase da notícia importante. Segunda frase sobre o evento cultural. Terceira frase muito longa que deveria ser cortada."
        summarized = generate_daily.summarize_text(text_long, max_sentences=2, max_length=100)
        self.assertNotIn("Terceira frase", summarized)
        self.assertTrue(summarized.endswith(".") or summarized.endswith("..."))

    def test_japan_timezone_date_filter(self):
        """Testa se o ajuste de fuso horário do Japão (JST) valida matérias recentes da NHK"""
        pubdate_nhk = "Thu, 13 Aug 2026 18:00:00 +0900"
        self.assertTrue(generate_daily.is_valid_date(pubdate_nhk, self.target_dt, is_japan=True))

    def test_vocabulary_extraction(self):
        """Testa a extração inteligente de termos modernos (Gairaigo) presentes nas notícias"""
        nhk_news = [{'title': '観光キャンペーンがスタート', 'description': 'オンラインで参加可能なプロジェクトです。'}]
        g1_news = [{'title': 'デジタル変革', 'description': 'アプリの活用が進む。'}]
        v_jp, v_pt = generate_daily.extract_vocabulary(nhk_news, g1_news)
        self.assertIn("キャンペーン", v_jp)
        self.assertIn("Campanha", v_pt)

    def test_empty_news_fallback_message(self):
        """Testa se mensagens amigáveis de fallback são incluídas quando não há notícias violentas/válidas"""
        jp_file, pt_file = generate_daily.generate_edition(self.target_dt)
        self.assertTrue(os.path.exists(jp_file))
        self.assertTrue(os.path.exists(pt_file))

if __name__ == '__main__':
    unittest.main()
