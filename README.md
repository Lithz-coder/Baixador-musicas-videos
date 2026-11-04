# Baixador de Músicas e Vídeos

Aplicativo desktop em Python com interface Tkinter para baixar conteúdos compatíveis com `yt-dlp`, com opções de formato e qualidade.

> **Uso responsável:** utilize o aplicativo somente para baixar conteúdos que você possui, que estejam em domínio público ou cuja licença/autorizaçao permita o download. Respeite os termos da plataforma e os direitos autorais.

## Funcionalidades

- Inserção de um ou mais links.
- Suporte a vídeos e playlists.
- Conversão de áudio para MP3, M4A, WAV, OPUS e FLAC.
- Download de vídeo em MP4, MKV e WEBM.
- Seleção de qualidade de áudio e resolução de vídeo.
- Opção para baixar legendas e miniaturas.
- Escolha da pasta de destino.
- Barra de progresso, registro de mensagens e cancelamento.

## Requisitos

- Python 3.10 ou superior (recomendado).
- FFmpeg instalado e disponível no `PATH`.
- Dependências Python listadas em `requirements.txt`.

## Instalação no Windows

1. Instale o [Python](https://www.python.org/downloads/). Durante a instalação, marque **Add Python to PATH**.
2. Instale o [FFmpeg](https://ffmpeg.org/download.html) e configure a pasta `bin` no `PATH`.
3. Baixe ou clone este repositório.
4. Abra o terminal na pasta do projeto e execute:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Como executar

```bash
python baixador.py
```

Cole os links na janela, escolha formato, qualidade e pasta de destino e clique em **Baixar**.

## Estrutura do projeto

```text
baixador-musicas-videos/
├── baixador.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Problemas comuns

- **FFmpeg não encontrado:** confirme se a pasta `bin` do FFmpeg está no `PATH` e reinicie o terminal.
- **Erro ao baixar:** atualize o `yt-dlp` com `python -m pip install -U yt-dlp`.
- **Formato/codec indisponível:** verifique se o FFmpeg está instalado corretamente.

## Atualizar dependências

```bash
python -m pip install -U -r requirements.txt
```
