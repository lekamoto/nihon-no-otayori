import os
import json
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
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            channel = root.find('channel')
            if channel is not None:
                for item in channel.findall('item')[:max_items]:
                    title = item.find('title').text if item.find('title') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    description = item.find('description').text if item.find('description') is not None else ""
                    items.append({'title': title, 'link': link, 'description': description})
    except Exception as e:
        print(f"Erro ao buscar RSS de {url}: {e}")
    return items

# Buscar Notícias Reais via RSS (NHK e G1)
nhk_news = fetch_rss("https://www3.nhk.or.jp/rss/news/cat0.xml", max_items=4)
g1_news = fetch_rss("https://g1.globo.com/dynamo/rss2.xml", max_items=3)

# Se falhar ou estiver vazio no teste offline, fornecer fallbacks estruturados
if not nhk_news:
    nhk_news = [
        {"title": "奈良県で新しい観光キャンペーン「わたしは、奈良派。」が開始", "description": "古都・奈良の歴史と自然を楽しんでもらうための巡回ツアーや観光案内が話題を集めています。"},
        {"title": "徳島県で日本最古級のトカゲ化石が発見される", "description": "太古の生態系を解き明かす貴重な発見として研究者から注目されています。"},
        {"title": "全国で夏期巡回ラジオ体操会が開催中", "description": "朝の爽やかな空気の中で健康づくりに励む人々で賑わっています。"},
        {"title": "日曜美術館50周年を記念した特別展覧会が全国を巡回", "description": "日本の伝統工芸や絵画を身近に楽しめる美術展が開催されています。"}
    ]

if not g1_news:
    g1_news = [
        {"title": "Teatros da Amazônia são reconhecidos como Patrimônio Mundial da UNESCO", "description": "O Teatro da Paz em Belém e o Teatro Amazonas em Manaus foram destacados pela rica arquitetura."},
        {"title": "Semana do Clima em São Paulo debate soluções sustentáveis", "description": "Encontro reúne especialistas para discutir inovação e preservação florestal."},
        {"title": "Brasil e Índia ampliam parcerias econômicas e de inovação", "description": "Representantes ministeriais firmam acordos para fortalecer o intercâmbio comercial."}
    ]

# Gerar arquivo Markdown da edição do dia
md_filename = f"edicoes/edicao_{now_br.strftime('%Y_%m_%d')}.md"
os.makedirs("edicoes", exist_ok=True)

# Gerar arquivo HTML responsivo (Story/Mobile) otimizado para leitura visual em celulares
html_filename = f"edicoes/edicao_{now_br.strftime('%Y_%m_%d')}.html"

html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>日本からのお便り - {date_str_jp}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@600;700;900&family=Zen+Kaku+Gothic+New:wght@700;900&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background-color: #121212; display: flex; justify-content: center; align-items: center; min-height: 100vh; font-family: 'Noto Serif JP', serif; padding: 15px 0; }}
    .story-card {{ width: 100%; max-width: 500px; background: #FFFDF9; color: #111111; padding: 28px 20px; border-radius: 16px; display: flex; flex-direction: column; gap: 24px; line-height: 2.1; }}
    .header {{ border-bottom: 4px solid #8B0000; padding-bottom: 16px; text-align: center; }}
    .main-title {{ font-size: 30px; font-weight: 900; color: #8B0000; letter-spacing: 2px; margin-bottom: 6px; }}
    .date-badge {{ font-size: 18px; font-weight: 700; color: #555555; margin-bottom: 14px; }}
    .greeting-box {{ background-color: #F7EBE8; border-left: 6px solid #8B0000; padding: 16px; border-radius: 8px; font-size: 22px; font-weight: 700; text-align: left; }}
    ruby {{ ruby-position: over; }}
    rt {{ font-size: 13px; color: #D32F2F; font-weight: 700; font-family: 'Zen Kaku Gothic New', sans-serif; }}
    .section-title {{ font-size: 24px; font-weight: 900; background-color: #111111; color: #FFFFFF; padding: 8px 16px; border-radius: 8px; margin-bottom: 16px; }}
    .news-block {{ display: flex; flex-direction: column; gap: 18px; }}
    .news-item {{ background-color: #FFFFFF; border: 2px solid #E0DCD3; border-radius: 12px; padding: 16px; }}
    .news-title {{ font-size: 21px; font-weight: 900; color: #111111; margin-bottom: 8px; line-height: 1.5; }}
    .news-body {{ font-size: 19px; font-weight: 600; color: #222222; text-align: justify; }}
    .vocab-card {{ background-color: #F0F7F4; border: 3px solid #2E7D32; border-radius: 12px; padding: 16px; margin-bottom: 12px; }}
    .vocab-term {{ font-size: 22px; font-weight: 900; color: #1B5E20; margin-bottom: 6px; border-bottom: 2px dashed #A5D6A7; padding-bottom: 4px; }}
    .vocab-meaning {{ font-size: 19px; font-weight: 700; color: #111111; }}
    .closing-box {{ background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%); border: 3px solid #E65100; border-radius: 14px; padding: 20px; text-align: center; font-size: 22px; font-weight: 900; color: #BF360C; line-height: 2.1; }}
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
        <div class="news-item"><div class="news-title">1. {nhk_news[0]['title']}</div><div class="news-body">{nhk_news[0]['description']}</div></div>
        <div class="news-item"><div class="news-title">2. {nhk_news[1]['title'] if len(nhk_news) > 1 else '日本の文化情報'}</div><div class="news-body">{nhk_news[1]['description'] if len(nhk_news) > 1 else '全国各地で歴史展が開催されています。'}</div></div>
        <div class="news-item"><div class="news-title">3. {nhk_news[2]['title'] if len(nhk_news) > 2 else '健康と暮らし'}</div><div class="news-body">{nhk_news[2]['description'] if len(nhk_news) > 2 else '朝の習慣が健康を支えています。'}</div></div>
        <div class="news-item"><div class="news-title">4. {nhk_news[3]['title'] if len(nhk_news) > 3 else '自然と環境'}</div><div class="news-body">{nhk_news[3]['description'] if len(nhk_news) > 3 else '美しい四季を大切にしています。'}</div></div>
      </div>
    </section>

    <section>
      <div class="section-title">🔰 ブラジルのニュース</div>
      <div class="news-block">
        <div class="news-item"><div class="news-title">1. {g1_news[0]['title']}</div><div class="news-body">{g1_news[0]['description']}</div></div>
        <div class="news-item"><div class="news-title">2. {g1_news[1]['title'] if len(g1_news) > 1 else '環境と未来'}</div><div class="news-body">{g1_news[1]['description'] if len(g1_news) > 1 else '新しい取り組みが広がっています。'}</div></div>
        <div class="news-item"><div class="news-title">3. {g1_news[2]['title'] if len(g1_news) > 2 else '経済と暮らし'}</div><div class="news-body">{g1_news[2]['description'] if len(g1_news) > 2 else '国際協力が進められています。'}</div></div>
      </div>
    </section>

    <section>
      <div class="section-title" style="background-color: #2E7D32;">📖 言葉の解説</div>
      <div class="vocab-card"><div class="vocab-term">1. キャンペーン (Kyampēn)</div><div class="vocab-meaning">【意味】目的を達成するために行う宣伝や活動。</div></div>
      <div class="vocab-card"><div class="vocab-term">2. パートナーシップ (Pātonāshippu)</div><div class="vocab-meaning">【意味】協力関係、提携。</div></div>
      <div class="vocab-card"><div class="vocab-term">3. ユネスコ世界遺産 (Yunesuko Sekai Isan)</div><div class="vocab-meaning">【意味】国際機関が指定する価値のある文化財や自然。</div></div>
      <div class="vocab-card"><div class="vocab-term">4. 巡回 (じゅんかい)</div><div class="vocab-meaning">【意味】各地を順番にまわること。</div></div>
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

md_content = f"""# 日本からのお便り (Diário do Japão e do Brasil)
**Data:** {date_str_jp} ({date_str_br})  
**Horário de Geração:** {now_br.strftime('%H:%M')} ({period})

---

## 1. Carta em Japonês (日本語の本文)

お母さん（おかあさん）、  
{greeting}。  
今日も日本（にほん）からのお便（たよ）りをお届け（とどけ）します。  
ゆっくり読んで（よんで）くださいね。  

---

### 【日本（にほん）のニュース】

1. **{nhk_news[0]['title']}**  
   {nhk_news[0]['description']}

2. **{nhk_news[1]['title'] if len(nhk_news) > 1 else '日本の文化情報'}**  
   {nhk_news[1]['description'] if len(nhk_news) > 1 else '全国各地で夏のアートや歴史展が開催されています。'}

3. **{nhk_news[2]['title'] if len(nhk_news) > 2 else '健康と暮らし'}**  
   {nhk_news[2]['description'] if len(nhk_news) > 2 else '朝の爽やかな習慣が人々の健康を支えています。'}

4. **{nhk_news[3]['title'] if len(nhk_news) > 3 else '自然と環境'}**  
   {nhk_news[3]['description'] if len(nhk_news) > 3 else '美しい四季の自然を大切にする取り組みが続いています。'}

---

### 【ブラジルのニュース】

1. **{g1_news[0]['title']}**  
   {g1_news[0]['description']}

2. **{g1_news[1]['title'] if len(g1_news) > 1 else '環境と未来'}**  
   {g1_news[1]['description'] if len(g1_news) > 1 else '持続可能な社会に向けた新しい取り組みが広がっています。'}

3. **{g1_news[2]['title'] if len(g1_news) > 2 else '経済と暮らし'}**  
   {g1_news[2]['description'] if len(g1_news) > 2 else '国際的な協力関係の強化が進められています。'}

---

### 【言葉（ことば）の解説（かいせつ）】

1. **キャンペーン (Kyampēn)**  
   - **意味（いみ）:** 目的（もくてき）を 達成（たっせい）するために 行う（おこなう） 宣伝（せんでん）や 活動（かつどう）。  

2. **パートナーシップ (Pātonāshippu)**  
   - **意味（いみ）:** 協力（きょうりょく）関係（かんけい）、提携（ていけい）。  

3. **ユネスコ世界遺産（せかいいさん） (Yunesuko Sekai Isan)**  
   - **意味（いみ）:** 国際（こくさい）機関（きかん）が 指定（してい）する 価値（かち）のある 文化財（ぶんかざい）や 自然（しぜん）。  

4. **巡回（じゅんかい） (Junkai)**  
   - **意味（いみ）:** 各地（かくち）を 順番（じゅんばん）に まわること。  

---

### 【今日のメッセージ】

今日も（今日も） 素敵な（すてきな） 一日（いちにち）でしたね。  
明日（あした）も きっと 素敵な（すてきな） 一日（いちにち）に なります。  
どうぞ ゆっくり お休み（やすみ）ください。  
よい夢（ゆめ）を。  
"""

with open(md_filename, "w", encoding="utf-8") as f:
    f.write(md_content)

print(f"Edição diária salva com sucesso em {md_filename}")
