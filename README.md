# LLM

**Onde LLMs Locais ganham mãos para trabalhar com arquivos e conhecimento.**

Um agente autônomo que permite sua LLM local (LM Studio/Ollama) executar ações reais no sistema de arquivos, com sistema RAG opcional para memória de longo prazo.

## 🚀 Início Rápido

```bash
# Instalar dependências
pip install -r requirements.txt --break-system-packages

# Ou

pip3 install -r requirements.txt --break-system-packages

# Configurar URL do servidor LLM
# Edite agent.py linha 6: BASE_URL = "http://localhost:1234/v1"

# Executar
python main.py

# Ou

python3 main.py

# Ver ajuda
> /help
```

## ✨ Funcionalidades

### 🔄 Sistema de Undo
- Snapshots automáticos antes de operações destrutivas
- `/undo` para reverter última ação
- Histórico completo de operações
- Restauração segura de arquivos

### 🧠 Planejamento Multi-Step
- Detecção automática de tarefas complexas
- Preview do plano antes da execução
- Confirmação interativa (y/n)
- Evita ações acidentais

### 📊 Gerenciamento de Contexto
- Compressão inteligente de histórico
- Truncamento de outputs longos
- Evita overflow de context window
- Mantém informações essenciais

## 🛠️ Tools Disponíveis

O agente possui acesso às seguintes ferramentas:

- **list_files** - Listar arquivos em um diretório
- **read_file** - Ler conteúdo de arquivos
- **write_file** - Criar novos arquivos
- **edit_file** - Editar arquivos existentes
- **delete_file** - Deletar arquivos
- **shell** - Executar comandos shell (timeout 10s)
- **add_to_rag** - Adicionar conhecimento ao RAG

Todas as operações são executadas dentro da pasta `./sandbox` por segurança.

## 📚 Sistema RAG (Opcional)

Sistema de memória de longo prazo com lazy loading - só carrega quando necessário.

### Comandos:

```bash
/rag                      # Ver ajuda e status
/rag enable               # Habilitar RAG (carrega modelo)
/rag disable              # Desabilitar RAG
/rag status               # Ver status atual
/rag add <texto>          # Adicionar texto
/rag add file:<path>      # Adicionar arquivo(s)
/rag view                 # Listar documentos
/rag clear                # Limpar base de conhecimento
```

**Características:**
- ✅ Lazy loading - inicia instantaneamente
- ✅ Busca semântica com embeddings
- ✅ Suporta múltiplos arquivos com glob patterns
- ✅ Persistência em ChromaDB

## 💡 Exemplos de Uso

```
> crie um arquivo hello.py que imprime olá mundo
> liste os arquivos
> leia o arquivo hello.py
> execute o comando python hello.py
> delete o arquivo hello.py
# Caso queira testar algo mais complexo:
> Eu tenho 5 arquivos, delete apenas os que dizem ser não importantes.
```

**Dica:** Use `/help` para ver mais exemplos e comandos disponíveis.

Com RAG habilitado:
```
> /rag enable
> /rag add file:docs/*.txt
> Do que você sabe com o RAG?
```

## ⚙️ Configuração

**Servidor LLM:**
- Edite `BASE_URL` em `agent.py` (linha 6)
- Compatível com LM Studio, Ollama, ou qualquer servidor OpenAI-compatible

**Sandbox:**
- Todas as operações de arquivo ocorrem em `./sandbox`
- Para mudar, edite `BASE_DIR` em `tools.py`

## 📦 Dependências

```
As dependências necessárias estão em requirements.txt
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Este projeto foca em simplicidade e eficiência.
