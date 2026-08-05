# README - Gerador de Carta/Revista Diária em Japonês (Versão 1.1)

Este projeto contém as configurações, instruções de prompt e modelos de layout para a produção diária de uma pequena revista/carta em japonês, criada sob medida para uma leitora idosa nipo-brasileira (88 anos, morando no Brasil há mais de 60 anos, com glaucoma e visão unilateral).

## 📁 Estrutura do Repositório

- `config.json` / `config.yaml`: Arquivos de configuração contendo todas as diretrizes de sistema, público-alvo, fontes de notícias (NHK e Globo), regras de saudação, acessibilidade e fluxo de trabalho.
- `prompt_instrucao.md`: Prompt detalhado e editável em Markdown para instruir agentes de IA na geração de novas edições.
- `edicao_teste.md`: Exemplo prático de uma edição completa gerada (com texto em japonês, furigana, explicações de vocabulário e tradução para o português).
- `render_story_preview.html`: Modelo de visualização HTML/CSS adaptado para o formato Story (9:16) em coluna única, com fontes extra grandes, alto contraste e suporte a furigana.

## 🚀 Como Usar

1. **Editar o Prompt:** Utilize o arquivo `prompt_instrucao.md` para ajustar regras ou incluir novas seções na carta.
2. **Gerar Novas Edições:** Forneça a instrução ao assistente AI baseado no arquivo de configuração e no prompt.
3. **Visualizar o Layout:** Abra o arquivo `render_story_preview.html` em qualquer navegador ou dispositivo móvel para verificar a renderização do Story (9:16).
