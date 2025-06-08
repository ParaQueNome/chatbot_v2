import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Modelo pré-treinado
MODEL_PATH = "nvidia/Nemotron-Research-Reasoning-Qwen-1.5B"

# Variável global para indicar se o modelo de chat foi carregado
modelo_chat_carregado = False
modelo_carregando = True

# Função para carregar o modelo em uma thread separada
def carregar_modelo():
    global tokenizer, model, modelo_chat_carregado, modelo_carregando
    device = "cuda" if torch.cuda.is_available() else "cpu"

    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForCausalLM.from_pretrained(MODEL_PATH).to(device)

        print(f"Model loaded successfully: {MODEL_PATH}")
        modelo_chat_carregado = True
        modelo_carregando = False

        # Atualizar o status na interface
        janela.after(0, lambda: status_label.config(text="Status: Model loaded", fg="green"))
    except Exception as e:
        print(f"Error loading model: {e}")
        modelo_carregando = False
        janela.after(0, lambda: messagebox.showerror("Error", f"Could not load model.\nError: {e}"))
        janela.after(0, lambda: status_label.config(text="Status: Error loading model", fg="red"))

# Função para gerar resposta
def gerar_resposta(texto_usuario):
    global tokenizer, model

    if not modelo_chat_carregado:
        return "Please wait while the model is loading."

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Construir o prompt
        prompt = f"You are AstroBot, an AI assistant specialized in astronomy. " \
                 f"Please answer the following question about astronomy: {texto_usuario}\n" \
                 f"AstroBot:"

        # Tokenizar a entrada
        inputs = tokenizer(prompt, return_tensors="pt").to(device)

        # Gerar a resposta
        outputs = model.generate(
            inputs.input_ids,
            max_length=250,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            pad_token_id=tokenizer.eos_token_id
        )

        # Decodificar a resposta
        resposta = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extrair apenas a resposta do AstroBot
        resposta = resposta.split("AstroBot:")[-1].strip()

        return resposta

    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'm sorry, I couldn't process your question about astronomy."

# Função para processar a resposta em uma thread separada
def processar_resposta(texto_usuario):
    global historico_conversa

    # Exibir mensagem do usuário
    caixa_conversa.insert(tk.END, f"You: {texto_usuario}\n", "user")
    caixa_conversa.see(tk.END)

    # Exibir typing
    caixa_conversa.insert(tk.END, "AstroBot is thinking...\n", "typing")
    caixa_conversa.see(tk.END)

    resposta_bot = gerar_resposta(texto_usuario)

    # Atualizar histórico
    historico_conversa.append({"role": "user", "content": texto_usuario})
    historico_conversa.append({"role": "assistant", "content": resposta_bot})

    # Limitar o tamanho do histórico para as últimas 10 trocas (ajuste conforme necessário)
    historico_conversa = historico_conversa[-10:]

    caixa_conversa.delete("end-2l", "end-1c")

    # Exibir resposta do bot
    caixa_conversa.insert(tk.END, f"AstroBot: {resposta_bot}\n\n", "bot")
    caixa_conversa.see(tk.END)

# Função para limpar o histórico
def limpar_historico():
    global historico_conversa

    # Limpar o histórico
    historico_conversa = []

    # Limpar a caixa de conversa
    caixa_conversa.delete("1.0", tk.END)

    # Adicionar a mensagem de boas-vindas novamente
    mensagem_boas_vindas = "Hi there! I'm AstroBot, your virtual assistant about astronomy. Ask me anything about the universe!"
    caixa_conversa.insert(tk.END, f"AstroBot: {mensagem_boas_vindas}\n\n", "bot")

    # Reinicializar o histórico com a mensagem de boas-vindas
    historico_conversa.append({"role": "assistant", "content": mensagem_boas_vindas})

# Interface gráfica
def enviar_mensagem():
    texto_usuario = entrada_texto.get("1.0", tk.END).strip()
    if not texto_usuario:
        return

    entrada_texto.delete("1.0", tk.END)

    botao_enviar.config(state=tk.DISABLED)
    status_label.config(text="Status: Generating response...", fg="blue")

    threading.Thread(target=lambda: processar_e_reativar(texto_usuario)).start()

def processar_e_reativar(texto_usuario):
    processar_resposta(texto_usuario)
    # Reativar botão após processamento
    janela.after(0, lambda: botao_enviar.config(state=tk.NORMAL))
    janela.after(0, lambda: status_label.config(text="Status: Ready", fg="green"))

# Função para pressionar Enter
def enviar_com_enter(event):
    enviar_mensagem()
    return "break"  # Impede a inserção de uma nova linha

# Configuração da janela
janela = tk.Tk()
janela.title("AstroBot - Your Astronomy Chatbot")
janela.geometry("600x700")
janela.configure(bg="#e6f2ff")

frame_principal = tk.Frame(janela, bg="#e6f2ff")
frame_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Status do carregamento do modelo
status_label = tk.Label(frame_principal, text="Status: Loading model...",
                        fg="orange", bg="#e6f2ff", font=("Arial", 10))
status_label.pack(anchor="w")

caixa_conversa = scrolledtext.ScrolledText(frame_principal, wrap=tk.WORD,
                                         font=("Arial", 12), bg="white", height=25)
caixa_conversa.tag_config("user", foreground="#0055AA", font=("Arial", 12, "bold"))
caixa_conversa.tag_config("bot", foreground="#008800", font=("Arial", 12))
caixa_conversa.tag_config("typing", foreground="gray", font=("Arial", 10, "italic"))
caixa_conversa.pack(fill=tk.BOTH, expand=True, pady=5)

frame_entrada = tk.Frame(janela, bg="#e6f2ff")
frame_entrada.pack(fill=tk.X)

entrada_texto = tk.Text(frame_entrada, height=3, font=("Arial", 12))
entrada_texto.pack(side=tk.LEFT, fill=tk.X, expand=True)
entrada_texto.bind("<Return>", enviar_com_enter)

botao_enviar = tk.Button(frame_entrada, text="Send", font=("Arial", 12),
                       bg="#3399ff", fg="white", command=enviar_mensagem)
botao_enviar.pack(side=tk.RIGHT, padx=5)

# Botão para limpar o histórico
botao_limpar_historico = tk.Button(frame_principal, text="Clear History", font=("Arial", 12),
                                  bg="#ff6666", fg="white", command=limpar_historico)
botao_limpar_historico.pack(side=tk.BOTTOM, pady=5)

# Mensagem de boas vindas
mensagem_boas_vindas = "Hi there! I'm AstroBot, your virtual assistant about astronomy. Ask me anything about the universe!"
caixa_conversa.insert(tk.END, f"AstroBot: {mensagem_boas_vindas}\n\n", "bot")

# Inicializar histórico de conversa
historico_conversa = [
    {"role": "assistant", "content": mensagem_boas_vindas}
]

# Iniciar carregamento do modelo em uma thread separada
threading.Thread(target=carregar_modelo, daemon=True).start()

janela.mainloop()