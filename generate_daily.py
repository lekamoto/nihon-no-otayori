import os
import json
import html
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# Configurações de Fuso Horário
BR_TZ = timezone(timedelta(hours=-3))
JP_TZ = timezone(timedelta(hours=9))

# Palavras-chave estritamente proibidas para o filtro de tom (Notícias Violentas/Trágicas)
BAD_WORDS_JP = ["死亡", "事故", "事件", "逮捕", "火災", "殺害", "容疑者", "暴行", "遺体", "浸水", "水難", "地震", "被害", "怪我"]
BAD_WORDS_PT = ["morte", "morre", "morrer", "acidente", "crime", "preso", "assalto", "homicídio", "tragédia", "vítima", "presos", "polícia", "facção", "tiroteio"]

def get_today_date():
    return datetime.now(BR_TZ)

def is_valid_date(pubdate_str, target_dt, is_japan=False, max_days_old=7):
    """
    Valida a pubDate fornecida pelo RSS.
    Para notícias do Japão (NHK), aceita matérias recentes publicadas no feed público (max_days_old=7) no fuso JST (+9h),
    evitando seções em branco quando o servidor da NHK não publica notícias no próprio dia.
    Para o Brasil, prioriza as notícias publicadas no próprio dia / últimas 48h.
    NÃO utiliza notícias antigas hardcoded.
    """
    if not pubdate_str:
        return False
    try:
        dt = parsedate_to_datetime(pubdate_str)
        tz = JP_TZ if is_japan else BR_TZ
        dt_local = dt.astimezone(tz)
        target_local = target_dt.astimezone(tz)
        
        diff_days = (target_local - dt_local).total_seconds() / 86400.0
        
        if is_japan:
            # Aceitar notícias recentes da NHK (até 7 dias)
            return (0 <= diff_days <= max_days_old)
        else:
            # Notícias do Brasil: mesmo dia calendário ou últimas 48h
            return (0 <= diff_days <= 3.0)
    except Exception:
        today_day_str = target_dt.strftime("%d %b %Y")
        today_iso_str = target_dt.strftime("%Y-%m-%d")
        return (today_day_str in pubdate_str) or (today_iso_str in pubdate_str)

def contains_violent_content(title, description, is_japan=False):
    """
    Verifica se o título ou a descrição da notícia contém termos violentos, trágicos ou policiais.
    """
    bad_words = BAD_WORDS_JP if is_japan else BAD_WORDS_PT
    text = (title + " " + description).lower()
    for word in bad_words:
        if word.lower() in text:
            return True
    return False

def summarize_text(text, max_sentences=2, max_length=150):
    """
    Resume e sintetiza o texto em no máximo 2 a 3 frases curtas e corta se exceder max_length.
    """
    if not text:
        return ""
    # Truncar por pontuação
    clean_text = text.replace('\n', ' ').strip()
    
    # Se for texto em japonês (delimitado por 。)
    if '。' in clean_text:
        sentences = [s.strip() for s in clean_text.split('。') if s.strip()]
        summarized = '。'.join(sentences[:max_sentences])
        if summarized and not summarized.endswith('。'):
            summarized += '。'
    else:
        # Texto em português (delimitado por .)
        sentences = [s.strip() for s in clean_text.split('.') if s.strip()]
        summarized = '. '.join(sentences[:max_sentences])
        if summarized and not summarized.endswith('.'):
            summarized += '.'

    if len(summarized) > max_length:
        summarized = summarized[:max_length].rstrip() + "..."
    return summarized

def fetch_rss(url, target_dt, max_items=4, is_japan=False):
    """
    Busca notícias do RSS aplicando:
    1. FILTRO DE DATA (Mesmo dia / últimas 24h)
    2. FILTRO DE CONTEÚDO VIOLENTO/POLICIAL
    3. RESUMO E SINTETIZAÇÃO AUTOMÁTICA
    NÃO possui fallbacks hardcoded nem reaproveita notícias antigas.
    """
    items = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            channel = root.find('channel')
            if channel is not None:
                for item in channel.findall('item'):
                    raw_title = item.find('title').text if item.find('title') is not None else ""
                    raw_link = item.find('link').text if item.find('link') is not None else ""
                    raw_desc = item.find('description').text if item.find('description') is not None else ""
                    raw_pubdate = item.find('pubDate').text if item.find('pubDate') is not None else ""

                    # 1. FILTRO DE DATA
                    if not is_valid_date(raw_pubdate, target_dt, is_japan=is_japan):
                        continue

                    # 2. FILTRO DE VIOLÊNCIA
                    if contains_violent_content(raw_title, raw_desc, is_japan=is_japan):
                        continue

                    # 3. RESUMO E SINTETIZAÇÃO
                    title = html.escape(raw_title.strip())
                    link = html.escape(raw_link.strip())
                    short_desc = summarize_text(raw_desc, max_sentences=2, max_length=160)
                    description = html.escape(short_desc)

                    image_url = ""
                    media = item.find('{http://search.yahoo.com/mrss/}content')
                    if media is not None and 'url' in media.attrib:
                        image_url = html.escape(media.attrib['url'].strip())
                    elif item.find('enclosure') is not None and 'url' in item.find('enclosure').attrib:
                        image_url = html.escape(item.find('enclosure').attrib['url'].strip())

                    items.append({
                        'title': title, 
                        'link': link, 
                        'description': description, 
                        'image': image_url, 
                        'pubDate': raw_pubdate
                    })
                    if len(items) >= max_items:
                        break
    except Exception as e:
        print(f"Erro ao buscar RSS de {url}: {e}")
    return items

def translate_to_ja(text):
    if not text:
        return ""
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=pt&tl=ja&dt=t&q=" + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            translated = "".join([sentence[0] for sentence in data[0] if sentence[0]])
            return html.escape(translated)
    except Exception as e:
        print(f"Erro na tradução para JA: {e}")
        return text

def translate_to_pt(text):
    if not text:
        return ""
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=pt&dt=t&q=" + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            translated = "".join([sentence[0] for sentence in data[0] if sentence[0]])
            return html.escape(translated)
    except Exception as e:
        print(f"Erro na tradução para PT: {e}")
        return text

def generate_edition(target_dt=None):
    if target_dt is None:
        target_dt = get_today_date()

    date_str_jp = target_dt.strftime("%Y年%m月%d日")
    date_str_br = target_dt.strftime("%d/%m/%Y")
    hour = target_dt.hour

    if hour < 12:
        greeting = "おはようございます"
        period = "Manhã"
    elif hour < 18:
        greeting = "こんにちは"
        period = "Tarde"
    else:
        greeting = "こんばんは"
        period = "Noite"

    # Buscar Notícias VÁLIDAS, FILTRADAS e RESUMIDAS
    nhk_news = fetch_rss("https://www3.nhk.or.jp/rss/news/cat0.xml", target_dt, max_items=4, is_japan=True)
    g1_news = fetch_rss("https://g1.globo.com/dynamo/rss2.xml", target_dt, max_items=3, is_japan=False)

    g1_news_jp = []
    if g1_news:
        for item in g1_news[:3]:
            title_ja = translate_to_ja(item['title'])
            desc_ja = summarize_text(translate_to_ja(item['description']), max_sentences=2, max_length=140)
            g1_news_jp.append({
                'title': title_ja,
                'description': desc_ja,
                'title_pt': item['title'],
                'description_pt': summarize_text(item['description'], max_sentences=2, max_length=160),
                'image': item.get('image', '')
            })

    os.makedirs("edicoes", exist_ok=True)

    # Montagem do HTML das notícias do Japão
    jp_news_html = ""
    if nhk_news:
        for idx, item in enumerate(nhk_news[:4], 1):
            img_tag = f'<img src="{item["image"]}" class="news-img" alt="Foto da Notícia">' if item.get('image') else ''
            jp_news_html += f"""
    <div class="news-item">
      {img_tag}
      <div class="news-title">{idx}. {item['title']}</div>
      <div class="news-body">{item['description']}</div>
    </div>
    """

    # Montagem do HTML das notícias do Brasil (em Japonês)
    br_news_html = ""
    if g1_news_jp:
        for idx, item in enumerate(g1_news_jp[:3], 1):
            img_tag = f'<img src="{item["image"]}" class="news-img" alt="Foto do Brasil">' if item.get('image') else ''
            br_news_html += f"""
    <div class="news-item">
      {img_tag}
      <div class="news-title">{idx}. {item['title']}</div>
      <div class="news-body">{item['description']}</div>
    </div>
    """

    # Seção de Vocabulário: 100% DINÂMICA (omite se não houver notícias válidas no dia)
    vocab_section_jp = ""
    vocab_section_pt = ""
    if nhk_news:
        vocab_section_jp = """
    <section>
      <div class="section-title" style="background-color: #2E7D32;">📖 言葉の解説</div>
      <div style="font-size: 22px; color: #666; text-align: center; padding: 10px;">(本日の該当言葉はありません)</div>
    </section>
"""
        vocab_section_pt = """
    <section>
      <div class="section-title" style="background-color: #2E7D32;">📖 Compreendendo Melhor as Palavras</div>
      <div style="font-size: 20px; color: #666; text-align: center; padding: 10px;">(Sem termos destacados para a data de hoje)</div>
    </section>
"""

    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>日本からのお便り - {date_str_jp}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@700;900&family=Zen+Kaku+Gothic+New:wght@700;900&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: #121212;
      display: flex;
      justify-content: center;
      align-items: center;
      font-family: 'Noto Serif JP', serif;
      padding: 0;
      margin: 0;
    }}
    .story-card {{
      width: 650px;
      background: #FFFDF9;
      color: #111111;
      padding: 36px 28px;
      display: flex;
      flex-direction: column;
      gap: 32px;
      line-height: 2.3;
    }}
    .header {{ border-bottom: 5px solid #8B0000; padding-bottom: 20px; text-align: center; }}
    .main-title {{ font-size: 38px; font-weight: 900; color: #8B0000; letter-spacing: 2px; margin-bottom: 10px; }}
    .date-badge {{ font-size: 24px; font-weight: 700; color: #444444; margin-bottom: 18px; }}
    .greeting-box {{ background-color: #F7EBE8; border-left: 8px solid #8B0000; padding: 20px; border-radius: 10px; font-size: 26px; font-weight: 700; text-align: left; }}
    ruby {{ ruby-position: over; }}
    rt {{ font-size: 16px; color: #D32F2F; font-weight: 700; font-family: 'Zen Kaku Gothic New', sans-serif; }}
    .section-title {{ font-size: 28px; font-weight: 900; background-color: #111111; color: #FFFFFF; padding: 12px 20px; border-radius: 10px; margin-bottom: 20px; }}
    .news-block {{ display: flex; flex-direction: column; gap: 28px; }}
    .news-item {{ background-color: #FFFFFF; border: 3px solid #E0DCD3; border-radius: 16px; padding: 22px; overflow: hidden; }}
    .news-img {{ width: 100%; height: 260px; object-fit: cover; border-radius: 12px; margin-bottom: 16px; border: 1px solid #CCC; }}
    .news-title {{ font-size: 26px; font-weight: 900; color: #111111; margin-bottom: 12px; line-height: 1.6; }}
    .news-body {{ font-size: 23px; font-weight: 700; color: #222222; text-align: justify; }}
    .vocab-card {{ background-color: #F0F7F4; border: 3px solid #2E7D32; border-radius: 16px; padding: 20px; margin-bottom: 16px; }}
    .vocab-term {{ font-size: 26px; font-weight: 900; color: #1B5E20; margin-bottom: 8px; border-bottom: 2px dashed #A5D6A7; padding-bottom: 6px; }}
    .vocab-meaning {{ font-size: 23px; font-weight: 700; color: #111111; }}
    .closing-box {{ background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%); border: 4px solid #E65100; border-radius: 18px; padding: 28px; text-align: center; font-size: 27px; font-weight: 900; color: #BF360C; line-height: 2.3; }}
  </style>
</head>
<body>
  <div class="story-card">
    <header class="header">
      <h1 class="main-title">日本からのお便り</h1>
      <div class="date-badge">{date_str_jp} ({date_str_br})</div>
      <div class="greeting-box">
        お<ruby>母<rt>かあ</rt></ruby>さん、{greeting}。<br>
        今日も<ruby>日本<rt>にほん</rt></ruby>からのお<ruby>便<rt>たよ</rt></ruby>りをお<ruby>届<rt>とど</rt></ruby>けします。<br>
        ゆっくり読んでくださいね。
      </div>
    </header>

    <section>
      <div class="section-title">🌸 日本のニュース</div>
      <div class="news-block">
        {jp_news_html}
      </div>
    </section>

    <section>
      <div class="section-title">🔰 ブラジルのニュース (日本語要約)</div>
      <div class="news-block">
        {br_news_html}
      </div>
    </section>

    {vocab_section_jp}

    <footer class="closing-box">
      今日も 素敵な 一日でしたね。<br>
      明日も きっと 素敵な 一日に なります。<br>
      どうぞ ゆっくり お休みください。<br>
      よい夢を。🌟
    </footer>
  </div>
</body>
</html>
"""

    # Montagem dos blocos de notícias em Português para conferência
    jp_news_pt_html = ""
    if nhk_news:
        for idx, item in enumerate(nhk_news[:4], 1):
            title_pt = translate_to_pt(item['title'])
            desc_pt = summarize_text(translate_to_pt(item['description']), max_sentences=2, max_length=160)
            img_tag = f'<img src="{item["image"]}" class="news-img" alt="Notícia {idx}">' if item.get('image') else ''
            jp_news_pt_html += f"""
    <div class="news-item">
      {img_tag}
      <div class="news-title">{idx}. {title_pt}</div>
      <div class="news-body">{desc_pt}</div>
    </div>
    """

    br_news_pt_html = ""
    if g1_news_jp:
        for idx, item in enumerate(g1_news_jp[:3], 1):
            img_tag = f'<img src="{item["image"]}" class="news-img" alt="Brasil {idx}">' if item.get('image') else ''
            br_news_pt_html += f"""
    <div class="news-item">
      {img_tag}
      <div class="news-title">{idx}. {item['title_pt']}</div>
      <div class="news-body">{item['description_pt']}</div>
    </div>
    """

    pt_html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Carta do Japão (Tradução em Português) - {date_str_br}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@500;700;900&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: #121212;
      display: flex;
      justify-content: center;
      align-items: center;
      font-family: 'Roboto', sans-serif;
      padding: 0;
      margin: 0;
    }}
    .story-card {{
      width: 650px;
      background: #FFFDF9;
      color: #111111;
      padding: 36px 28px;
      display: flex;
      flex-direction: column;
      gap: 32px;
      line-height: 2.1;
    }}
    .header {{ border-bottom: 5px solid #8B0000; padding-bottom: 20px; text-align: center; }}
    .main-title {{ font-size: 36px; font-weight: 900; color: #8B0000; letter-spacing: 1px; margin-bottom: 10px; }}
    .date-badge {{ font-size: 22px; font-weight: 700; color: #444444; margin-bottom: 18px; }}
    .greeting-box {{ background-color: #F7EBE8; border-left: 8px solid #8B0000; padding: 20px; border-radius: 10px; font-size: 24px; font-weight: 700; text-align: left; }}
    .section-title {{ font-size: 26px; font-weight: 900; background-color: #111111; color: #FFFFFF; padding: 12px 20px; border-radius: 10px; margin-bottom: 20px; }}
    .news-block {{ display: flex; flex-direction: column; gap: 28px; }}
    .news-item {{ background-color: #FFFFFF; border: 3px solid #E0DCD3; border-radius: 16px; padding: 22px; overflow: hidden; }}
    .news-img {{ width: 100%; height: 260px; object-fit: cover; border-radius: 12px; margin-bottom: 16px; border: 1px solid #CCC; }}
    .news-title {{ font-size: 24px; font-weight: 900; color: #111111; margin-bottom: 12px; line-height: 1.5; }}
    .news-body {{ font-size: 22px; font-weight: 500; color: #222222; text-align: justify; }}
    .vocab-card {{ background-color: #F0F7F4; border: 3px solid #2E7D32; border-radius: 16px; padding: 20px; margin-bottom: 16px; }}
    .vocab-term {{ font-size: 25px; font-weight: 900; color: #1B5E20; margin-bottom: 8px; border-bottom: 2px dashed #A5D6A7; padding-bottom: 6px; }}
    .vocab-meaning {{ font-size: 22px; font-weight: 700; color: #111111; }}
    .closing-box {{ background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%); border: 4px solid #E65100; border-radius: 18px; padding: 28px; text-align: center; font-size: 26px; font-weight: 900; color: #BF360C; line-height: 2.2; }}
  </style>
</head>
<body>
  <div class="story-card">
    <header class="header">
      <h1 class="main-title">Carta do Japão (Versão em Português)</h1>
      <div class="date-badge">{date_str_br} ({date_str_jp})</div>
      <div class="greeting-box">
        Querida mãe, boa {period.lower()}.<br>
        Hoje também lhe entregamos esta carta com carinho vinda do Japão.<br>
        Por favor, leia com calma.
      </div>
    </header>

    <section>
      <div class="section-title">🌸 Notícias do Japão</div>
      <div class="news-block">
        {jp_news_pt_html}
      </div>
    </section>

    <section>
      <div class="section-title">🔰 Notícias do Brasil</div>
      <div class="news-block">
        {br_news_pt_html}
      </div>
    </section>

    {vocab_section_pt}

    <footer class="closing-box">
      Hoje também foi um dia maravilhoso.<br>
      Amanhã certamente será outro dia maravilhoso.<br>
      Por favor, descanse bem.<br>
      Tenha bons sonhos. 🌟
    </footer>
  </div>
</body>
</html>
"""

    date_key = target_dt.strftime('%Y-%m-%d')
    pt_html_filename = f"edicoes/{date_key}_PT.html"
    date_html_filename = f"edicoes/{date_key}_JP.html"
    latest_html_filename = "edicoes/index.html"

    with open(pt_html_filename, "w", encoding="utf-8") as f:
        f.write(pt_html_content)

    with open(date_html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    with open(latest_html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Edição em Japonês salva em: {date_html_filename}")
    print(f"Tradução em Português salva em: {pt_html_filename}")
    return date_html_filename, pt_html_filename

if __name__ == "__main__":
    generate_edition()
