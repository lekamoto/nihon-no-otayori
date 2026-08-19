import os
import json
import html
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# Configurações de Fuso Horário
BR_TZ = timezone(timedelta(hours=-3))  # Horário de Brasília (BRT)
JP_TZ = timezone(timedelta(hours=9))   # Horário de Tóquio (JST)

# Palavras-chave estritamente proibidas para o filtro de tom (Notícias Violentas/Trágicas)
BAD_WORDS_JP = ["死亡", "事故", "事件", "逮捕", "火災", "殺害", "容疑者", "暴行", "遺体", "浸水", "水難", "地震", "被害", "怪我"]
BAD_WORDS_PT = ["morte", "morre", "morrer", "acidente", "crime", "preso", "assalto", "homicídio", "tragédia", "vítima", "presos", "polícia", "facção", "tiroteio"]

# Acervo de Fotos Contextuais Reais e Serenas (Fallback caso a matéria venha sem imagem)
FALLBACK_IMAGES_JP = [
    "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&q=80",  # Jardim tradicional japonês
    "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=800&q=80",  # Tóquio serena / arquitetura
    "https://images.unsplash.com/photo-1545569341-9eb8b30979d9?w=800&q=80",  # Bambuzal de Kyoto
    "https://images.unsplash.com/photo-1528164344705-475426879c0d?w=800&q=80",  # Paisagem com Monte Fuji
    "https://images.unsplash.com/photo-1578637387939-43c525550085?w=800&q=80",  # Cultura e artes
]

FALLBACK_IMAGES_BR = [
    "https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=800&q=80",  # Paisagem do Rio de Janeiro
    "https://images.unsplash.com/photo-1516306580123-e6e52b1b7b5f?w=800&q=80",  # Natureza / Mata Atlântica
    "https://images.unsplash.com/photo-1596484552834-6a58f850e0a1?w=800&q=80",  # Parques e arquitetura urbana
    "https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=800&q=80",  # Cultura brasileira
]

# Base de Conhecimento de Vocabulário Moderno / Gairaigo (Pós-1960)
MODERN_VOCAB_DB = [
    {
        "term": "キャンペーン",
        "romaji": "Kyampēn",
        "meaning_ja": "【意味】目的を達成するために行う宣伝や社会的な活動。",
        "term_pt": "Campanha (キャンペーン)",
        "meaning_pt": "Ação organizada ou mobilização promocional/cultural para alcançar um objetivo."
    },
    {
        "term": "プロジェクト",
        "romaji": "Purojekuto",
        "meaning_ja": "【意味】特定の目標を達成するための計画や事業。",
        "term_pt": "Projeto (プロジェクト)",
        "meaning_pt": "Plano estruturado de trabalho ou empreendimento voltado a uma meta."
    },
    {
        "term": "ボランティア",
        "romaji": "Borantia",
        "meaning_ja": "【意味】社会や地域のために自主的に行う奉仕活動。",
        "term_pt": "Voluntariado (ボランティア)",
        "meaning_pt": "Atividade de apoio social ou comunitário realizada de forma espontânea."
    },
    {
        "term": "オンライン",
        "romaji": "Onrain",
        "meaning_ja": "【意味】インターネットなどの通信回線につながっている状態。",
        "term_pt": "Online (オンライン)",
        "meaning_pt": "Conectado à internet ou funcionando por meio de redes digitais."
    },
    {
        "term": "デジタル",
        "romaji": "Dejitaru",
        "meaning_ja": "【意味】情報を数値データとして電子機器で処理する技術。",
        "term_pt": "Digital (デジタル)",
        "meaning_pt": "Tecnologia que processa informações em formato eletrônico."
    },
    {
        "term": "パートナーシップ",
        "romaji": "Pātonāshippu",
        "meaning_ja": "【意味】お互いに協力し合う関係や提携。",
        "term_pt": "Parceria (パートナーシップ)",
        "meaning_pt": "Relação de cooperação ou aliança entre partes para um benefício mútuo."
    },
    {
        "term": "サステナブル",
        "romaji": "Sasutenaburu",
        "meaning_ja": "【意味】環境や社会の豊かさを未来へ持続できること。",
        "term_pt": "Sustentável (サステナブル)",
        "meaning_pt": "Prática que preserva recursos naturais e o bem-estar para futuras gerações."
    },
    {
        "term": "リサイクル",
        "romaji": "Risaikuru",
        "meaning_ja": "【意味】一度使ったものを再び資源として活用すること。",
        "term_pt": "Reciclagem (リサイクル)",
        "meaning_pt": "Reaproveitamento de materiais para diminuir o desperdício."
    },
    {
        "term": "プラットフォーム",
        "romaji": "Purattofōmu",
        "meaning_ja": "【意味】サービスや情報を提供する基盤となる仕組みやシステム。",
        "term_pt": "Plataforma (プラットフォーム)",
        "meaning_pt": "Base tecnológica ou sistema que viabiliza serviços e interações."
    },
    {
        "term": "コミュニティ",
        "romaji": "Komyuniti",
        "meaning_ja": "【意味】地域社会や同じ目的を持つ人々の温かい集まり。",
        "term_pt": "Comunidade (コミュニティ)",
        "meaning_pt": "Grupo de pessoas unidas por laços locais, sociais ou culturais."
    },
    {
        "term": "アプリ",
        "romaji": "Apuri",
        "meaning_ja": "【意味】スマートフォンなどで動く便利なソフトウェア（アプリケーションの略）。",
        "term_pt": "Aplicativo / App (アプリ)",
        "meaning_pt": "Programa leve utilizado em celulares e dispositivos modernos."
    },
    {
        "term": "スマート",
        "romaji": "Sumāto",
        "meaning_ja": "【意味】IT技術などを活用して賢く効率的であること。",
        "term_pt": "Smart / Inteligente (スマート)",
        "meaning_pt": "Uso de inteligência e automação para facilitar tarefas cotidianas."
    },
    {
        "term": "キャッシュレス",
        "romaji": "Kyasshuresu",
        "meaning_ja": "【意味】紙幣や硬貨を使わず、電子カードなどで支払うこと。",
        "term_pt": "Pagamento Digital (キャッシュレス)",
        "meaning_pt": "Transações financeiras realizadas sem o uso de dinheiro em espécie."
    },
    {
        "term": "ハイブリッド",
        "romaji": "Haiburiddo",
        "meaning_ja": "【意味】異なる複数の仕組みを組み合わせて良いところを活かすこと。",
        "term_pt": "Híbrido (ハイブリッド)",
        "meaning_pt": "Combinação de duas ou mais tecnologias ou modalidades distintas."
    },
    {
        "term": "モビリティ",
        "romaji": "Mobiriti",
        "meaning_ja": "【意味】人々や物の移動手段、移動のしやすさのこと。",
        "term_pt": "Mobilidade (モビリティ)",
        "meaning_pt": "Facilidade e infraestrutura de transporte e locomoção urbana."
    },
    {
        "term": "インフラ",
        "romaji": "Infura",
        "meaning_ja": "【意味】道路、水道、通信など社会生活を支える基盤設備（インフラストラクチャーの略）。",
        "term_pt": "Infraestrutura (インフラ)",
        "meaning_pt": "Conjunto de instalações e serviços essenciais para o funcionamento da sociedade."
    },
    {
        "term": "イベント",
        "romaji": "Ibento",
        "meaning_ja": "【意味】催し物、行事、特別な企画。",
        "term_pt": "Evento (イベント)",
        "meaning_pt": "Acontecimento ou celebração programada para o público."
    },
    {
        "term": "グローバル",
        "romaji": "Gurōbaru",
        "meaning_ja": "【意味】世界全体にわたる、地球規模の。",
        "term_pt": "Global (グローバル)",
        "meaning_pt": "De alcance internacional ou mundial."
    },
    {
        "term": "ネットワーク",
        "romaji": "Nettowāku",
        "meaning_ja": "【意味】コンピューターや人々の網の目のようにつながる連絡網。",
        "term_pt": "Rede / Network (ネットワーク)",
        "meaning_pt": "Sistema interconectado de comunicação, dados ou relacionamentos."
    },
    {
        "term": "メディア",
        "romaji": "Media",
        "meaning_ja": "【意味】テレビ、新聞、インターネットなどの情報伝達媒体。",
        "term_pt": "Mídia (メディア)",
        "meaning_pt": "Meios de comunicação e difusão de informação pública."
    },
    {
        "term": "インターネット",
        "romaji": "Intānetto",
        "meaning_ja": "【意味】世界中の電子機器を結ぶ情報通信網。",
        "term_pt": "Internet (インターネット)",
        "meaning_pt": "Rede mundial de computadores que possibilita o acesso e troca de informações."
    }
]

def get_today_date():
    return datetime.now(BR_TZ)

def is_valid_date(pubdate_str, target_dt, is_japan=False, max_days_old=7):
    """
    Valida a pubDate fornecida pelo RSS.
    Para notícias do Japão (NHK), aceita matérias recentes publicadas no feed público (max_days_old=7) no fuso JST (+9h).
    Para o Brasil (G1), aceita matérias de hoje / últimas 48h com tolerância para diferença de fuso UTC (-0.5 <= diff_days <= 3.0).
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
            return (-0.5 <= diff_days <= max_days_old)
        else:
            # Notícias do Brasil: mesmo dia calendário ou últimas 48h com tolerância a fuso UTC
            return (-0.5 <= diff_days <= 3.0)
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

def clean_html_text(raw_html):
    """
    Remove tags HTML brutas (ex: <img src=...>, <br />, <a>) e links de canais/vídeos
    para evitar vazamento de código no resumo.
    """
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', '', raw_html)
    # Remover chamadas de WhatsApp ou links de vídeo residuais
    clean = re.sub(r'✅WhatsApp\s*で.*', '', clean)
    clean = re.sub(r'Vídeo:\s*\d+\s*minuto.*', '', clean, flags=re.IGNORECASE)
    return html.unescape(clean).strip()

def summarize_text(text, max_sentences=2, max_length=150):
    """
    Remove tags HTML, resume e sintetiza o texto em no máximo 2 a 3 frases curtas.
    """
    if not text:
        return ""
    # Remover tags HTML brutas antes de resumir
    clean_text = clean_html_text(text).replace('\n', ' ').strip()
    
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
    1. FILTRO DE DATA (Mesmo dia / recentes no fuso correspondente)
    2. FILTRO DE CONTEÚDO VIOLENTO/POLICIAL
    3. RESUMO E SINTETIZAÇÃO AUTOMÁTICA
    4. EXTRAÇÃO INTELIGENTE DE IMAGENS COM FALLBACK CONTEXTUAL NÍTIDO
    """
    items = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            channel = root.find('channel')
            if channel is not None:
                item_index = 0
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

                    # 3. EXTRAÇÃO INTELIGENTE DE IMAGENS
                    image_url = ""
                    media = item.find('{http://search.yahoo.com/mrss/}content')
                    if media is not None and 'url' in media.attrib:
                        image_url = html.escape(media.attrib['url'].strip())
                    elif item.find('enclosure') is not None and 'url' in item.find('enclosure').attrib:
                        image_url = html.escape(item.find('enclosure').attrib['url'].strip())
                    elif item.find('{http://search.yahoo.com/mrss/}thumbnail') is not None and 'url' in item.find('{http://search.yahoo.com/mrss/}thumbnail').attrib:
                        image_url = html.escape(item.find('{http://search.yahoo.com/mrss/}thumbnail').attrib['url'].strip())
                    elif raw_desc:
                        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_desc)
                        if img_match:
                            image_url = html.escape(img_match.group(1).strip())

                    # Fallback com foto contextual real se não houver imagem no feed
                    if not image_url:
                        fallback_list = FALLBACK_IMAGES_JP if is_japan else FALLBACK_IMAGES_BR
                        image_url = fallback_list[item_index % len(fallback_list)]

                    # 4. RESUMO E SINTETIZAÇÃO
                    title = html.escape(raw_title.strip())
                    link = html.escape(raw_link.strip())
                    short_desc = summarize_text(raw_desc, max_sentences=2, max_length=160)
                    description = html.escape(short_desc)

                    items.append({
                        'title': title, 
                        'link': link, 
                        'description': description, 
                        'image': image_url, 
                        'pubDate': raw_pubdate
                    })
                    item_index += 1
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

def extract_vocabulary(nhk_news, g1_news_jp, max_words=4):
    """
    Identifica dinamicamente 3 a 5 palavras modernas / gairaigo presentes nas notícias do dia.
    Gera as seções formatadas em HTML para as versões em Japonês e Português.
    """
    combined_text_ja = ""
    for item in nhk_news:
        combined_text_ja += " " + item['title'] + " " + item['description']
    for item in g1_news_jp:
        combined_text_ja += " " + item['title'] + " " + item['description']

    matched_vocab = []
    for entry in MODERN_VOCAB_DB:
        if entry["term"] in combined_text_ja:
            matched_vocab.append(entry)
            if len(matched_vocab) >= max_words:
                break

    # Se menos que 3 palavras foram encontradas diretamente no texto das matérias,
    # complementar com termos modernos relevantes da base para enriquecer o vocabulário da leitora
    if len(matched_vocab) < 3 and (nhk_news or g1_news_jp):
        for entry in MODERN_VOCAB_DB:
            if entry not in matched_vocab:
                matched_vocab.append(entry)
                if len(matched_vocab) >= 3:
                    break

    if not matched_vocab:
        vocab_section_jp = """
    <section>
      <div class="section-title" style="background-color: #2E7D32;">📖 言葉の解説</div>
      <div style="font-size: 22px; color: #666; text-align: center; padding: 14px; font-style: italic;">
        (本日の該当言葉はありません)
      </div>
    </section>
"""
        vocab_section_pt = """
    <section>
      <div class="section-title" style="background-color: #2E7D32;">📖 Compreendendo Melhor as Palavras</div>
      <div style="font-size: 20px; color: #666; text-align: center; padding: 14px; font-style: italic;">
        (Sem termos destacados para a data de hoje)
      </div>
    </section>
"""
        return vocab_section_jp, vocab_section_pt

    # Montagem dos cartões em Japonês
    jp_cards = ""
    for idx, v in enumerate(matched_vocab, 1):
        jp_cards += f"""
      <div class="vocab-card">
        <div class="vocab-term">{idx}. {v['term']} ({v['romaji']})</div>
        <div class="vocab-meaning">{v['meaning_ja']}</div>
      </div>"""

    vocab_section_jp = f"""
    <section>
      <div class="section-title" style="background-color: #2E7D32;">📖 言葉の解説</div>
      {jp_cards}
    </section>
"""

    # Montagem dos cartões em Português
    pt_cards = ""
    for idx, v in enumerate(matched_vocab, 1):
        pt_cards += f"""
      <div class="vocab-card">
        <div class="vocab-term">{idx}. {v['term_pt']}</div>
        <div class="vocab-meaning">【Explicação】{v['meaning_pt']}</div>
      </div>"""

    vocab_section_pt = f"""
    <section>
      <div class="section-title" style="background-color: #2E7D32;">📖 Compreendendo Melhor as Palavras</div>
      {pt_cards}
    </section>
"""
    return vocab_section_jp, vocab_section_pt

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
    if nhk_news:
        jp_news_html = ""
        for idx, item in enumerate(nhk_news[:4], 1):
            img_tag = f'<img src="{item["image"]}" class="news-img" alt="Foto da Notícia">' if item.get('image') else ''
            jp_news_html += f"""
    <div class="news-item">
      {img_tag}
      <div class="news-title">{idx}. {item['title']}</div>
      <div class="news-body">{item['description']}</div>
    </div>
    """
    else:
        jp_news_html = """
    <div style="font-size: 22px; color: #666; text-align: center; padding: 24px 10px; font-style: italic;">
      (本日は穏やかな話題を中心に厳選しております)
    </div>
    """

    # Montagem do HTML das notícias do Brasil (em Japonês)
    if g1_news_jp:
        br_news_html = ""
        for idx, item in enumerate(g1_news_jp[:3], 1):
            img_tag = f'<img src="{item["image"]}" class="news-img" alt="Foto do Brasil">' if item.get('image') else ''
            br_news_html += f"""
    <div class="news-item">
      {img_tag}
      <div class="news-title">{idx}. {item['title']}</div>
      <div class="news-body">{item['description']}</div>
    </div>
    """
    else:
        br_news_html = """
    <div style="font-size: 22px; color: #666; text-align: center; padding: 24px 10px; font-style: italic;">
      (本日の該当ニュースはありません)
    </div>
    """

    # Seção de Vocabulário Dinâmica
    if nhk_news or g1_news_jp:
        vocab_section_jp, vocab_section_pt = extract_vocabulary(nhk_news, g1_news_jp, max_words=4)
    else:
        vocab_section_jp = ""
        vocab_section_pt = ""

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
    if nhk_news:
        jp_news_pt_html = ""
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
    else:
        jp_news_pt_html = """
    <div style="font-size: 20px; color: #666; text-align: center; padding: 24px 10px; font-style: italic;">
      (Sem notícias destacadas do Japão dentro dos critérios de serenidade para a data de hoje)
    </div>
    """

    if g1_news_jp:
        br_news_pt_html = ""
        for idx, item in enumerate(g1_news_jp[:3], 1):
            img_tag = f'<img src="{item["image"]}" class="news-img" alt="Brasil {idx}">' if item.get('image') else ''
            br_news_pt_html += f"""
    <div class="news-item">
      {img_tag}
      <div class="news-title">{idx}. {item['title_pt']}</div>
      <div class="news-body">{item['description_pt']}</div>
    </div>
    """
    else:
        br_news_pt_html = """
    <div style="font-size: 20px; color: #666; text-align: center; padding: 24px 10px; font-style: italic;">
      (Sem notícias destacadas do Brasil dentro dos critérios de serenidade para a data de hoje)
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

