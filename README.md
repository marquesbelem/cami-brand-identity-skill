# 🎮 Camis GameDev - AI Brand Identity Skill & UI Showcase

Este repositório padroniza e automatiza a identidade visual, o design system e o tom de voz da **Camis GameDev** por meio de um System Prompt estruturado (`identity-skill-prompt.md`). O projeto atua como um motor de conformidade de marca e gerador de componentes de interface (UI) com suporte a múltiplos temas e faixas etárias.

---

## 📂 Estrutura do Repositório

```text
📁 cami-brand-identity-skill/
├── 📄 README.md                 <- Documentação completa e caso de estudo
├── 📄 identity-skill-prompt.md  <- System Prompt com suporte a múltiplos temas
├── 📄 CardTrilhas.jsx           <- Componente React pronto para demonstração de UI
└── 📁 assets/                   <- Variantes do logotipo e ativos visuais
```

---

## 🎨 Tokens de Design & Trilhas Multi-Tema

O motor interpreta e aplica regras de layout com base em três trilhas de desenvolvimento e faixas etárias distintas:

1. **Trilha Unity 3D / Profissional** (15+ anos e adultos):
   - Interfaces sofisticadas no estilo *dark mode*, foco em engenharia de software e fidelidade técnica.
2. **Trilha Roblox Crimson** (8 a 15 anos):
   - Estilo escuro vibrante e gamificado, voltado ao engajamento juvenil.
3. **Trilha Scratch Orange** (5 a 7 anos):
   - Layouts em blocos de alto contraste, amigáveis e intuitivos para alfabetização digital.

---

## 🛠️ Como Utilizar no seu Fluxo de Trabalho

### 1. Ativação via LLMs (Claude Projects / Custom GPTs / Instruções do Sistema)
1. Copie o conteúdo integral de `SKILL.md`.
2. Cole nas **Instruções de Sistema**, **Instruções Personalizadas** ou no **Contexto de Projeto** da sua IA.
3. Para solicitar a criação de elementos visuais ou textuais, especifique a trilha desejada:
   > *"Gere a seção Hero de uma nova landing page usando a configuração do sub-tema **Unity 3D (Dark Blue)**."*

### 2. Implementação em Código (React / Next.js / Tailwind CSS)
A skill pode exportar paletas e componentes diretamente no padrão Tailwind ou React.
   > *"Gere o componente de botão no padrão da marca para o **Tema Scratch (Orange)** usando Tailwind CSS."*

---

## 📈 Valor para o Portfólio (Design Tokens & Prompt Engineering)

Este projeto demonstra a habilidade prática de transformar brandbooks e diretrizes de design abstratas em infraestrutura executável por IA:

- **Parametrização de Design:** Arquitetura flexível baseada em sub-temas visuais atrelados aos objetivos pedagógicos e públicos de cada engine (Unity, Roblox, Scratch).
- **Consistência de Tom:** Alinhamento algorítmico de tom de voz para manter a comunicação técnica, corporativa e pedagogicamente acessível.


## Como usar em algum projeto

### Opção 1: Adicionar como Submódulo Git (Mais recomendado)
   1. Se o seu projeto já for versionado com Git, você pode linkar o repositório da skill mantendo as atualizações sincronizadas.
   2. Abra o terminal na pasta raiz do seu projeto e execute:
   ```text 
      # Adiciona a skill como submódulo dentro da pasta local de skills
      git submodule add https://github.com/marquesbelem/cami-brand-identity-skill.git .agent/skills/cami-brand-identity
   ```

### Opção 2: Clonar ou Copiar Diretamente na Raiz do Projeto
   1. Se não quiser usar submódulos, basta clonar ou copiar os arquivos diretamente para dentro da pasta `.agent/skills/` ou `.agents/skills/` do projeto:
   ```text
      # Na raiz do seu projeto:
      mkdir -p .agent/skills

      # Clona o repositório localmente
      git clone https://github.com/marquesbelem/cami-brand-identity-skill.git .agent/skills/cami-brand-identity
   ```

### Ativação no Workspace Local
   Para que o agente acione as diretrizes automaticamente sem que você precise digitar instruções repetitivas em toda mensagem, crie ou edite o arquivo de regras locais do projeto:

   Na raiz do seu projeto, abra ou crie o arquivo `.agent/rules` (ou .rules).
   Adicione a referência da skill:
   ```text
    Sempre que solicitado o desenvolvimento de interfaces, landing pages, componentes ou peças visuais para a marca "Camis GameDev", utilize as diretrizes e tokens definidos na skill:
   `.agent/skills/cami-brand-identity/SKILL.md`
   ```