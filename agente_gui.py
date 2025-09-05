import customtkinter as ctk
import threading
import requests
import psutil
import json
import time

# --- CONFIGURAÇÕES ---
URL_BASE_SERVIDOR = "http://127.0.0.1:8000/app" # Mude o IP se o servidor Django estiver em outra máquina
MONITORING_INTERVAL = 15 # Enviar dados a cada 15 segundos

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Agente de Monitoramento")
        self.geometry("400x250")

        self.monitorando = False
        self.thread_monitoramento = None
        self.computadores_disponiveis = {} # Dicionário para guardar nome -> mac_address

        # --- Widgets da Interface ---
        self.label = ctk.CTkLabel(self, text="Selecione o Computador a ser Monitorado:")
        self.label.pack(pady=10)

        self.combobox = ctk.CTkComboBox(self, values=["Carregando..."])
        self.combobox.pack(pady=5, padx=20, fill="x")

        self.botao_controle = ctk.CTkButton(self, text="Ligar Monitoramento", command=self.iniciar_parar_monitoramento)
        self.botao_controle.pack(pady=20)

        self.status_label = ctk.CTkLabel(self, text="Status: Desligado", text_color="gray")
        self.status_label.pack(pady=10)

        self.carregar_computadores()

    def carregar_computadores(self):
        """Busca a lista de computadores do servidor Django."""
        try:
            url = f"{URL_BASE_SERVIDOR}/api/listar-computadores/"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                computadores = response.json()
                # Limpa o dicionário e o combobox
                self.computadores_disponiveis.clear()
                nomes = []
                for comp in computadores:
                    # Guarda o nome e o mac_address para uso posterior
                    self.computadores_disponiveis[comp['nome']] = comp['endereco_mac']
                    nomes.append(comp['nome'])
                
                self.combobox.configure(values=nomes)
                if nomes:
                    self.combobox.set(nomes[0]) # Seleciona o primeiro por padrão
            else:
                self.combobox.configure(values=["Erro ao carregar"])
        except requests.exceptions.RequestException:
            self.combobox.configure(values=["Servidor offline"])

    def iniciar_parar_monitoramento(self):
        if self.monitorando:
            # --- LÓGICA PARA PARAR ---
            self.monitorando = False
            self.botao_controle.configure(text="Ligar Monitoramento", fg_color="#1f6aa5")
            self.status_label.configure(text="Status: Desligado", text_color="gray")
            print("Monitoramento parado.")
        else:
            # --- LÓGICA PARA INICIAR ---
            self.monitorando = True
            self.botao_controle.configure(text="Parar Monitoramento", fg_color="#d32f2f")
            self.status_label.configure(text=f"Status: Monitorando...", text_color="green")
            print("Monitoramento iniciado.")
            
            # Inicia o loop de monitoramento em uma thread separada para não travar a interface
            self.thread_monitoramento = threading.Thread(target=self.loop_de_monitoramento, daemon=True)
            self.thread_monitoramento.start()

    def loop_de_monitoramento(self):
        """O loop que coleta e envia dados enquanto 'monitorando' for True."""
        url_envio = f"{URL_BASE_SERVIDOR}/api/receive_monitoring/"
        
        while self.monitorando:
            nome_selecionado = self.combobox.get()
            mac_address = self.computadores_disponiveis.get(nome_selecionado)
            
            if not mac_address:
                print("Computador inválido selecionado. Parando.")
                self.monitorando = False
                break

            self.status_label.configure(text=f"Status: Coletando dados de '{nome_selecionado}'")
            
            dados = {
                'mac_address': mac_address,
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
            }

            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url_envio, data=json.dumps(dados), headers=headers, timeout=10)
                if response.status_code == 201:
                    print(f"Dados de '{nome_selecionado}' enviados com sucesso.")
                    self.status_label.configure(text=f"Status: Monitorando '{nome_selecionado}' (Enviado OK)")
                else:
                    print(f"Erro ao enviar dados: {response.status_code} - {response.text}")
                    self.status_label.configure(text="Status: Erro no envio", text_color="red")
            except requests.exceptions.RequestException as e:
                print(f"Falha de conexão: {e}")
                self.status_label.configure(text="Status: Servidor offline", text_color="red")

            time.sleep(MONITORING_INTERVAL)
        
        # Quando o loop termina
        self.status_label.configure(text="Status: Desligado", text_color="gray")


if __name__ == "__main__":
    app = App()
    app.mainloop()