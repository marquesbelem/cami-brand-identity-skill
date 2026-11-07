# 🎬 Intros Camis GameDev

| Arquivo | Formato | Duração | Uso |
| :--- | :--- | :--- | :--- |
| `intro_youtube_claro_1920x1080.mp4` | 16:9 · 1080p · 60 fps | 5,0 s | Abertura dos vídeos (padrão: tema claro) |
| `intro_youtube_escuro_1920x1080.mp4` | 16:9 · 1080p · 60 fps | 5,0 s | Variante tema escuro |
| `intro_shorts_claro_1080x1920.mp4` | 9:16 · 1080×1920 · 60 fps | 2,4 s | Abertura dos Shorts/Reels/TikTok (padrão) |
| `intro_shorts_escuro_1080x1920.mp4` | 9:16 · 1080×1920 · 60 fps | 2,4 s | Variante tema escuro |
| `trilha_youtube.wav` / `trilha_shorts.wav` | WAV 44,1 kHz · 16-bit | — | Trilhas isoladas para reutilizar na edição |

**Roteiro da animação:** os colchetes `{ }` se fecham ao som de um arpejo, abrem revelando o logo, os símbolos da marca aparecem com sons de "moeda", a barra de XP enche e termina com um **LEVEL UP!** (uma referência à gamificação, que é o diferencial da marca).

## 🔊 Licença do áudio (sem direitos autorais de terceiros)

As trilhas foram **compostas e sintetizadas do zero** pelo script `gerar_intros.py`, usando apenas osciladores matemáticos (ondas quadradas, triangulares, senoidais e ruído) gerados com `numpy`.

- Nenhum sample, loop, banco de sons ou música de terceiros é usado.
- A melodia, a harmonia e os efeitos são originais e pertencem à **Camis GameDev**.
- Podem ser usadas em vídeos monetizados no YouTube, Instagram, TikTok etc. sem risco de Content ID de terceiros.

> ⚠️ Não registre essas trilhas em serviços de Content ID (ex.: distribuidoras de música). Se fizer isso, seus próprios vídeos e os de parceiros podem receber reivindicações.

**Fontes usadas no vídeo:** Bungee e Raleway (SIL Open Font License), já incluídas em `assets/FONT`. A licença permite uso comercial em vídeos.

## 🔁 Como regerar ou customizar

```bash
pip install numpy pillow imageio-ffmpeg
python assets/INTRO/gerar_intros.py                    # claro + escuro, YouTube + Shorts
python assets/INTRO/gerar_intros.py --tema claro --formato shorts
```

Os textos (tagline, URL), as durações, as posições e a melodia ficam nos dicionários `FORMATOS`, `TEMAS`, `CHORDS` e `MELODIA` do script.

