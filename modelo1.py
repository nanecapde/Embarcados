import RPi.GPIO as GPIO
import time

# LEDs
LED_VERDE = 17
LED_AMARELO = 18
LED_VERMELHO = 23

# Botões
BOTAO_PRINCIPAL = 1
BOTAO_CRUZAMENTO = 12

# Configuração GPIO
GPIO.setmode(GPIO.BCM)

GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_AMARELO, GPIO.OUT)
GPIO.setup(LED_VERMELHO, GPIO.OUT)

GPIO.setup(BOTAO_PRINCIPAL, GPIO.IN)
GPIO.setup(BOTAO_CRUZAMENTO, GPIO.IN)

pedido_pedestre = False

# Estados LEDs
def verde():
    GPIO.output(LED_VERDE, True)
    GPIO.output(LED_AMARELO, False)
    GPIO.output(LED_VERMELHO, False)

def amarelo():
    GPIO.output(LED_VERDE, False)
    GPIO.output(LED_AMARELO, True)
    GPIO.output(LED_VERMELHO, False)

def vermelho():
    GPIO.output(LED_VERDE, False)
    GPIO.output(LED_AMARELO, False)
    GPIO.output(LED_VERMELHO, True)

# Botão
def botao_pressionado(channel):
    global pedido_pedestre

    pedido_pedestre = True

    print("Botão de pedestre pressionado!")

GPIO.add_event_detect(
    BOTAO_PRINCIPAL,
    GPIO.RISING,
    callback=botao_pressionado,
    bouncetime=200
)

GPIO.add_event_detect(
    BOTAO_CRUZAMENTO,
    GPIO.RISING,
    callback=botao_pressionado,
    bouncetime=200
)

# Loop principal
try:

    while True:

        print("VERDE")
        verde()

        inicio_verde = time.time()

        while True:

            tempo_verde = time.time() - inicio_verde

            if tempo_verde >= 10:
                break

            if pedido_pedestre and tempo_verde >= 5:
                print("Mudança antecipada por pedestre")
                break

            time.sleep(0.1)

        pedido_pedestre = False

        print("AMARELO")
        amarelo()

        time.sleep(2)

        print("VERMELHO")
        vermelho()

        time.sleep(10)

except KeyboardInterrupt:
    print("\nEncerrando programa")

finally:
    GPIO.cleanup()