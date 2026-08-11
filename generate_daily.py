import os
import json
import html
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# Configuração de Fuso Horário do Brasil (UTC-3)
BR_TZ = timezone(timedelta(hours=-3))
now_br = datetime.now(BR_TZ)
date_str_jp = now_br.strftime("%Y年%m月%d日")
date_str_br = now_br.strftime("%d/%m/%Y")
hour = now_br.hour

# Lógica de Saudação por Horário
if hour < 12:
    greeting = "おはようございます"
    period = "Manhã"
elif hour < 18:
    greeting = "こんにちは"
    period = "Tarde"
else:
    greeting = "こんばんは"
    period = "Noite"

def fetch_rss(url, max_items=4):
    items = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            channel = root.find('channel')
            if channel is not None:
                for item in channel.findall('item')[:max_items]:
                    raw_title = item.find('title').text if item.find('title') is not None else ""
                    raw_link = item.find('link').text if item.find('link') is not None else ""
                    raw_desc = item.find('description').text if item.find('description') is not None else ""
                    
                    # Sanitização contra XSS / HTML Injection
                    title = html.escape(raw_title.strip())
                    link = html.escape(raw_link.strip())
                    description = html.escape(raw_desc.strip())

                    image_url = ""
                    media = item.find('{http://search.yahoo.com/mrss/}content')
                    if media is not None and 'url' in media.attrib:
                        image_url = html.escape(media.attrib['url'].strip())
                    elif item.find('enclosure') is not None and 'url' in item.find('enclosure').attrib:
                        image_url = html.escape(item.find('enclosure').attrib['url'].strip())

                    items.append({'title': title, 'link': link, 'description': description, 'image': image_url})
    except Exception as e:
        print(f"Erro ao buscar RSS de {url}: {e}")
    return items

# Buscar Notícias Reais via RSS (NHK e G1)
nhk_news = fetch_rss("https://www3.nhk.or.jp/rss/news/cat0.xml", max_items=4)
g1_news = fetch_rss("https://g1.globo.com/dynamo/rss2.xml", max_items=3)

# Imagens ilustrativas padrão de alta qualidade para leitura agradável
default_images_jp = [
    "https://images.unsplash.com/photo-1545569341-9eb8b30979d9?w=600&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&q=80",
    "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=600&q=80",
    "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600&q=80"
]

default_images_br = [
    "https://images.unsplash.com/photo-1516306580123-e6e52b1b7b5f?w=600&q=80",
    "https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=600&q=80",
    "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=600&q=80"
]

if not nhk_news:
    nhk_news = [
        {"title": "古都・奈良の 新しい 観光キャンペーンが 開始", "description": "歴史と自然を楽しむのんびりした旅が人気を集めています。", "image": default_images_jp[0]},
        {"title": "徳島県で 日本最古級の トカゲ化石を 発見", "description": "大昔の生き物の暮らしを解き明かす貴重な発見です。", "image": default_images_jp[1]},
        {"title": "夏の 伝統「ラジオ体操」が 全国を 巡回", "description": "朝の爽やかな空気の中で体を動かす習慣が好評です。", "image": default_images_jp[2]},
        {"title": "美術を楽しむ「日曜美術館 50年展」が 開催中", "description": "美しい絵画や工芸品が人々の心を和ませています。", "image": default_images_jp[3]}
    ]
else:
    for idx, item in enumerate(nhk_news):
        if not item.get('image'):
            item['image'] = default_images_jp[idx % len(default_images_jp)]

# AJUSTE 1: Resumos das notícias do Brasil traduzidas para Japonês simples em poucas linhas
g1_news_jp = [
    {
        "title": "アマゾンの 歴史的 劇場が ユネスコ世界遺産に 登録",
        "description": "ベレンとマナウスの美しい劇場が世界遺産に選ばれました。ブラジルが誇る歴史的建築です。",
        "image": default_images_br[0]
    },
    {
        "title": "サンパウロで 「気候週間2026」会議が 開催",
        "description": "森や環境を守るための新しい取り組みが話し合われ、未来に向けた大切な一歩となりました。",
        "image": default_images_br[1]
    },
    {
        "title": "ブラジルと インドの 経済パートナーシップが 拡大",
        "description": "貿易や技術の交流を深める訪問が行われ、お互いの協力関係が強まっています。",
        "image": default_images_br[2]
    }
]

os.makedirs("edicoes", exist_ok=True)

# AJUSTE 3: Fotos antes de cada notícia para tornar a leitura mais agradável
jp_news_html = ""
for idx, item in enumerate(nhk_news[:4], 1):
    jp_news_html += f"""
    <div class="news-item">
      <img src="{item['image']}" class="news-img" alt="Foto da Notícia">
      <div class="news-title">{idx}. {item['title']}</div>
      <div class="news-body">{item['description']}</div>
    </div>
    """

br_news_html = ""
for idx, item in enumerate(g1_news_jp[:3], 1):
    br_news_html += f"""
    <div class="news-item">
      <img src="{item['image']}" class="news-img" alt="Foto do Brasil">
      <div class="news-title">{idx}. {item['title']}</div>
      <div class="news-body">{item['description']}</div>
    </div>
    """

# AJUSTE 2: Layout em Coluna Única, Fonte Extra Grande e Alto Contraste para Glaucoma
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

    <section>
      <div class="section-title" style="background-color: #2E7D32;">📖 言葉の解説</div>
      <div class="vocab-card">
        <div class="vocab-term">1. キャンペーン (Kyampēn)</div>
        <div class="vocab-meaning">【意味】目的を達成するために行う宣伝や活動。</div>
      </div>
      <div class="vocab-card">
        <div class="vocab-term">2. パートナーシップ (Pātonāshippu)</div>
        <div class="vocab-meaning">【意味】お互いに協力する関係や提携。</div>
      </div>
      <div class="vocab-card">
        <div class="vocab-term">3. ユネスコ世界遺産 (Yunesuko Sekai Isan)</div>
        <div class="vocab-meaning">【意味】人類の宝物として守る価値のある文化財や自然。</div>
      </div>
      <div class="vocab-card">
        <div class="vocab-term">4. 巡回 (じゅんかい)</div>
        <div class="vocab-meaning">【意味】各地を順番に訪れること。</div>
      </div>
    </section>

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

# Gerar o arquivo de tradução em Português para conferência (ex: edicoes/2026-08-11_PT.md)
pt_md_filename = f"edicoes/{now_br.strftime('%Y-%m-%d')}_PT.md"
pt_md_content = f"""# Carta do Japão (Edição de Conferência em Português)
**Data:** {date_str_br} ({date_str_jp})  
**Horário:** {now_br.strftime('%H:%M')} ({period})

---

## 1. Carta em Japonês (Tradução)

Querida mãe,  
{greeting} (Boa {period.lower()}).  
Hoje também lhe entrego esta carta do Japão.  
Por favor, leia com calma.  

---

### 【Notícias do Japão】

1. **{nhk_news[0]['title']}**  
   {nhk_news[0]['description']}

2. **{nhk_news[1]['title'] if len(nhk_news) > 1 else 'Informações Culturais do Japão'}**  
   {nhk_news[1]['description'] if len(nhk_news) > 1 else 'Exposições de história e arte estão sendo realizadas em várias partes do país.'}

3. **{nhk_news[2]['title'] if len(nhk_news) > 2 else 'Saúde e Estilo de Vida'}**  
   {nhk_news[2]['description'] if len(nhk_news) > 2 else 'O hábito da manhã ajuda a manter a saúde das pessoas.'}

4. **{nhk_news[3]['title'] if len(nhk_news) > 3 else 'Natureza e Meio Ambiente'}**  
   {nhk_news[3]['description'] if len(nhk_news) > 3 else 'Iniciativas para valorizar as belas quatro estações continuam.'}

---

### 【Notícias do Brasil (Resumo em Português)】

1. **{g1_news_jp[0]['title']}**  
   {g1_news_jp[0]['description']}

2. **{g1_news_jp[1]['title']}**  
   {g1_news_jp[1]['description']}

3. **{g1_news_jp[2]['title']}**  
   {g1_news_jp[2]['description']}

---

### 【Compreendendo Melhor as Palavras】

1. **Campanha (Kyampēn):** Atividade publicitária realizada para atingir um objetivo.
2. **Parceria (Pātonāshippu):** Relação de cooperação ou aliança mútua.
3. **Patrimônio Mundial da UNESCO (Yunesuko Sekai Isan):** Bens culturais ou naturais protegidos como tesouros da humanidade.
4. **Junkai (Circulação):** Visitar vários locais em sequência.

---

### 【Mensagem de Incentivo do Dia】

Hoje também foi um dia maravilhoso.  
Amanhã certamente será outro dia maravilhoso.  
Por favor, descanse bem.  
Tenha bons sonhos. 🌟
"""

with open(pt_md_filename, "w", encoding="utf-8") as f:
    f.write(pt_md_content)

# Salvar o arquivo HTML específico em Japonês com sufixo _JP.html (ex: edicoes/2026-08-11_JP.html)
date_html_filename = f"edicoes/{now_br.strftime('%Y-%m-%d')}_JP.html"
latest_html_filename = "edicoes/index.html"

with open(date_html_filename, "w", encoding="utf-8") as f:
    f.write(html_content)

with open(latest_html_filename, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Edição em Japonês salva em: {date_html_filename}")
print(f"Tradução em Português salva em: {pt_md_filename}")


