import threading
import time
import sys

# Tenta importar a biblioteca real, se falhar usa o Mock para Windows
try:
    import RPi.GPIO as GPIO
    print("Modo Real: Raspberry Pi detectado.")
except (ImportError, RuntimeError):
    import Mock.GPIO as GPIO
    print("Modo Simulação: Windows detectado (Usando Mock.GPIO).")

# --- CONFIGURAÇÃO DE PINOS (Tabelas 1, 4 e 5) ---
# Modelo 1
LEDS_M1 = {'verde': 17, 'amarelo': 18, 'vermelho': 23}
BOTOES_M1 = [1, 12]

# Modelo 2
BITS_M2 = [24, 8, 7] # Bit 0, Bit 1, Bit 2
BOTOES_M2 = {'principal': 25, 'cruzamento': 22}

# Variáveis globais para controle de pedestres
solicitacao_m1 = False
solicitacao_m2_principal = False
solicitacao_m2_cruzamento = False

# --- FUNÇÃO DE CALLBACK (REQUISITO 4 e 5) ---
def botao_pressionado(pino):
    global solicitacao_m1, solicitacao_m2_principal, solicitacao_m2_cruzamento
    # Imprime imediatamente ao detectar (Requisito 4)
    print(f"\n[EVENTO] Botão detectado no pino GPIO {pino}!")
    
    if pino in BOTOES_M1:
        solicitacao_m1 = True
    elif pino == BOTOES_M2['principal']:
        solicitacao_m2_principal = True
    elif pino == BOTOES_M2['cruzamento']:
        solicitacao_m2_cruzamento = True

# --- CONFIGURAÇÃO INICIAL ---
def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    # Configurar Saídas Modelo 1
    for pino in LEDS_M1.values():
        GPIO.setup(pino, GPIO.OUT)
        GPIO.output(pino, GPIO.LOW)
        
    # Configurar Saídas Modelo 2
    for pino in BITS_M2:
        GPIO.setup(pino, GPIO.OUT)
        GPIO.output(pino, GPIO.LOW)
        
    # Configurar Entradas (Botões) com Pull-Down e Debounce (Requisito 5)
    todos_botoes = BOTOES_M1 + list(BOTOES_M2.values())
    for pino in todos_botoes:
        GPIO.setup(pino, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # Bouncetime de 200ms conforme enunciado
        GPIO.add_event_detect(pino, GPIO.RISING, callback=botao_pressionado, bouncetime=200)

# --- FUNÇÃO DE TEMPORIZAÇÃO INTELIGENTE ---
def esperar(tempo_max, tempo_min, modelo_id):
    """
    Dorme pelo tempo_max, mas se uma solicitação de pedestre for detectada
    após o tempo_min, encerra a espera mais cedo.
    """
    global solicitacao_m1, solicitacao_m2_principal, solicitacao_m2_cruzamento
    
    inicio = time.time()
    while (time.time() - inicio) < tempo_max:
        decorrido = time.time() - inicio
        
        # Checa se pode interromper
        if decorrido >= tempo_min:
            if modelo_id == 1 and solicitacao_m1:
                print(">> Modelo 1: Antecipando mudança (Pedestre)")
                return
            if modelo_id == 2:
                # No Modelo 2, qualquer botão de pedestre afeta o ciclo atual
                if solicitacao_m2_principal or solicitacao_m2_cruzamento:
                    print(">> Modelo 2: Antecipando mudança (Pedestre)")
                    return
        
        time.sleep(0.1)

# --- LÓGICA MODELO 1 (3 LEDs Individuais) ---
def thread_modelo_1():
    global solicitacao_m1
    print("Iniciando Modelo 1...")
    while True:
        # VERDE (10s total, 5s min)
        GPIO.output(LEDS_M1['verde'], GPIO.HIGH)
        esperar(10, 5, 1)
        GPIO.output(LEDS_M1['verde'], GPIO.LOW)
        solicitacao_m1 = False # Atendido
        
        # AMARELO (2s)
        GPIO.output(LEDS_M1['amarelo'], GPIO.HIGH)
        time.sleep(2)
        GPIO.output(LEDS_M1['amarelo'], GPIO.LOW)
        
        # VERMELHO (10s)
        GPIO.output(LEDS_M1['vermelho'], GPIO.HIGH)
        time.sleep(10)
        GPIO.output(LEDS_M1['vermelho'], GPIO.LOW)

# --- MODELO 2 (Cruzamento 3 Bits) ---
def atualizar_bits_m2(codigo):
    # Converte decimal 0-7 para os 3 pinos de saída
    for i in range(3):
        bit = (codigo >> i) & 1
        GPIO.output(BITS_M2[i], GPIO.HIGH if bit else GPIO.LOW)

def thread_modelo_2():
    global solicitacao_m2_principal, solicitacao_m2_cruzamento
    print("Iniciando Modelo 2...")
    while True:
        # Estado 1: Via Principal Verde (20s max, 10s min)
        atualizar_bits_m2(1)
        esperar(20, 10, 2)
        solicitacao_m2_principal = False
        
        # Estado 2: Via Principal Amarelo (2s)
        atualizar_bits_m2(2)
        time.sleep(2)
        
        # Estado 4: Vermelho Total (2s)
        atualizar_bits_m2(4)
        time.sleep(2)
        
        # Estado 5: Via Cruzamento Verde (10s max, 5s min)
        atualizar_bits_m2(5)
        esperar(10, 5, 2)
        solicitacao_m2_cruzamento = False
        
        # Estado 6: Via Cruzamento Amarelo (2s)
        atualizar_bits_m2(6)
        time.sleep(2)
        
        # Estado 4: Vermelho Total (2s)
        atualizar_bits_m2(4)
        time.sleep(2)

# --- BLOCO PRINCIPAL ---
if __name__ == "__main__":
    setup()
    
    # Criando as Threads para execução simultânea (Requisito 2)
    t1 = threading.Thread(target=thread_modelo_1, daemon=True)
    t2 = threading.Thread(target=thread_modelo_2, daemon=True)
    
    t1.start()
    t2.start()
    
    print("\nSistema rodando. Pressione Ctrl+C para encerrar.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando e limpando GPIO...")
        GPIO.cleanup()