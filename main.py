import serial
import struct
import time

# =========================================================
# CONFIGURAÇÃO UART
# =========================================================

PORTA = "/dev/serial0"
BAUDRATE = 115200

ser = serial.Serial(
    port=PORTA,
    baudrate=BAUDRATE,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=2
)

# =========================================================
# MATRÍCULA (6 últimos dígitos)
# EXEMPLO: 042303
# =========================================================

MATRICULA = [0, 4, 2, 3, 0, 3]

# =========================================================
# CONFIG MODBUS
# =========================================================

ENDERECO = 0x01

# =========================================================
# UTILITÁRIOS
# =========================================================

def hex_bytes(data):
    return ' '.join(f'0x{b:02X}' for b in data)

def pack_int(valor):
    return struct.pack('<i', valor)

def unpack_int(data):
    return struct.unpack('<i', data)[0]

def pack_float(valor):
    return struct.pack('<f', valor)

def unpack_float(data):
    return struct.unpack('<f', data)[0]

def limpar_buffer():
    ser.reset_input_buffer()

def enviar(data):
    limpar_buffer()
    ser.write(data)

def receber(qtd):
    return ser.read(qtd)

# =========================================================
# CRC16 MODBUS
# =========================================================

def crc16(data):

    crc = 0xFFFF

    for pos in data:

        crc ^= pos

        for _ in range(8):

            if (crc & 1) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1

    return crc

def adicionar_crc(data):

    crc = crc16(data)

    return data + bytes([
        crc & 0xFF,
        (crc >> 8) & 0xFF
    ])

def validar_crc(data):

    if len(data) < 2:
        return False

    recebido = (data[-2] << 8) | data[-1]

    calculado = crc16(data[:-2])

    return recebido == calculado

# =========================================================
# SIMPLE
# =========================================================

def solicitar_int_simples():

    pacote = bytes([0xA1] + MATRICULA)

    print("\n===== SOLICITAR INT (SIMPLES) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    resposta = receber(4)

    print("RESP  :", hex_bytes(resposta))

    if len(resposta) != 4:
        print("ERRO: timeout")
        return

    valor = unpack_int(resposta)

    print("VALOR:", valor)

def solicitar_float_simples():

    pacote = bytes([0xA2] + MATRICULA)

    print("\n===== SOLICITAR FLOAT (SIMPLES) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    resposta = receber(4)

    print("RESP  :", hex_bytes(resposta))

    if len(resposta) != 4:
        print("ERRO: timeout")
        return

    valor = unpack_float(resposta)

    print("VALOR:", valor)

def solicitar_string_simples():

    pacote = bytes([0xA3] + MATRICULA)

    print("\n===== SOLICITAR STRING (SIMPLES) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    tamanho = receber(1)

    if len(tamanho) != 1:
        print("ERRO: timeout")
        return

    n = tamanho[0]

    resposta = receber(n)

    print("RESP  :", hex_bytes(tamanho + resposta))

    print("STRING:", resposta.decode())

def enviar_int_simples(valor):

    pacote = (
        bytes([0xB1])
        + pack_int(valor)
        + bytes(MATRICULA)
    )

    print("\n===== ENVIAR INT (SIMPLES) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    resposta = receber(4)

    print("RESP  :", hex_bytes(resposta))

    if len(resposta) != 4:
        print("ERRO: timeout")
        return

    resultado = unpack_int(resposta)

    print("RESULTADO:", resultado)

def enviar_float_simples(valor):

    pacote = (
        bytes([0xB2])
        + pack_float(valor)
        + bytes(MATRICULA)
    )

    print("\n===== ENVIAR FLOAT (SIMPLES) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    resposta = receber(4)

    print("RESP  :", hex_bytes(resposta))

    if len(resposta) != 4:
        print("ERRO: timeout")
        return

    resultado = unpack_float(resposta)

    print("RESULTADO:", resultado)

def enviar_string_simples(texto):

    texto_bytes = texto.encode()

    if len(texto_bytes) > 255:
        print("ERRO: string muito grande")
        return

    pacote = (
        bytes([0xB3])
        + bytes([len(texto_bytes)])
        + texto_bytes
        + bytes(MATRICULA)
    )

    print("\n===== ENVIAR STRING (SIMPLES) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    tamanho = receber(1)

    if len(tamanho) != 1:
        print("ERRO: timeout")
        return

    n = tamanho[0]

    resposta = receber(n)

    print("RESP  :", hex_bytes(tamanho + resposta))

    print("STRING:", resposta.decode())

# =========================================================
# MODBUS
# =========================================================

def criar_pacote_modbus(funcao, subcodigo, payload=b''):

    pacote = (
        bytes([ENDERECO])
        + bytes([funcao])
        + bytes([subcodigo])
        + payload
        + bytes(MATRICULA)
    )

    crc = crc16(pacote)

    pacote += bytes([
        (crc >> 8) & 0xFF,
        crc & 0xFF
    ])

    return pacote


def verificar_exception(resposta):

    if len(resposta) >= 2:

        funcao = resposta[1]

        if funcao & 0x80:

            print("EXCEÇÃO MODBUS")

            if len(resposta) >= 3:
                print("CÓDIGO:", resposta[2])

            return True

    return False

# =========================================================
# MODBUS - SOLICITAR
# =========================================================

def solicitar_int_modbus():

    pacote = criar_pacote_modbus(0x23, 0xA1)

    print("\n===== SOLICITAR INT (MODBUS) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    resposta = receber(6)

    print("RESP  :", hex_bytes(resposta))

    if len(resposta) != 6:
        print("ERRO: timeout")
        return

    if not validar_crc(resposta):
        print("ERRO: CRC inválido")
        return

    valor = unpack_int(resposta[:4])

    print("VALOR:", valor)

def solicitar_float_modbus():

    pacote = criar_pacote_modbus(0x23, 0xA2)

    print("\n===== SOLICITAR FLOAT (MODBUS) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    resposta = receber(6)

    print("RESP  :", hex_bytes(resposta))

    if len(resposta) != 6:
        print("ERRO: timeout")
        return

    if not validar_crc(resposta):
        print("ERRO: CRC inválido")
        return

    valor = unpack_float(resposta[:4])

    print("VALOR:", valor)

def solicitar_string_modbus():

    pacote = criar_pacote_modbus(0x23, 0xA3)

    print("\n===== SOLICITAR STRING (MODBUS) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    tamanho = receber(1)

    if len(tamanho) != 1:
        print("ERRO: timeout")
        return

    n = tamanho[0]

    dados_crc = receber(n + 2)

    pacote_resposta = tamanho + dados_crc

    print("RESP  :", hex_bytes(pacote_resposta))

    if len(dados_crc) != n + 2:
        print("ERRO: timeout")
        return

    if not validar_crc(pacote_resposta):
        print("ERRO: CRC inválido")
        return

    string_bytes = dados_crc[:-2]

    print("STRING:", string_bytes.decode())

# =========================================================
# MODBUS - ENVIAR
# =========================================================

def enviar_int_modbus(valor):

    payload = pack_int(valor)

    pacote = criar_pacote_modbus(
        0x16,
        0xB1,
        payload
    )

    print("\n===== ENVIAR INT (MODBUS) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    resposta = receber(6)

    print("RESP  :", hex_bytes(resposta))

    if len(resposta) != 6:
        print("ERRO: timeout")
        return

    if not validar_crc(resposta):
        print("ERRO: CRC inválido")
        return

    resultado = unpack_int(resposta[:4])

    print("RESULTADO:", resultado)

def enviar_float_modbus(valor):

    payload = pack_float(valor)

    pacote = criar_pacote_modbus(
        0x16,
        0xB2,
        payload
    )

    print("\n===== ENVIAR FLOAT (MODBUS) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    resposta = receber(6)

    print("RESP  :", hex_bytes(resposta))

    if len(resposta) != 6:
        print("ERRO: timeout")
        return

    if not validar_crc(resposta):
        print("ERRO: CRC inválido")
        return

    resultado = unpack_float(resposta[:4])

    print("RESULTADO:", resultado)

def enviar_string_modbus(texto):

    texto_bytes = texto.encode()

    if len(texto_bytes) > 255:
        print("ERRO: string muito grande")
        return

    payload = (
        bytes([len(texto_bytes)])
        + texto_bytes
    )

    pacote = criar_pacote_modbus(
        0x16,
        0xB3,
        payload
    )

    print("\n===== ENVIAR STRING (MODBUS) =====")
    print("ENVIO:", hex_bytes(pacote))

    enviar(pacote)

    tamanho = receber(1)

    if len(tamanho) != 1:
        print("ERRO: timeout")
        return

    n = tamanho[0]

    dados_crc = receber(n + 2)

    pacote_resposta = tamanho + dados_crc

    print("RESP  :", hex_bytes(pacote_resposta))

    if len(dados_crc) != n + 2:
        print("ERRO: timeout")
        return

    if not validar_crc(pacote_resposta):
        print("ERRO: CRC inválido")
        return

    string_bytes = dados_crc[:-2]

    print("STRING:", string_bytes.decode())

# =========================================================
# MENU
# =========================================================

while True:

    print("""
=================================================
                UART + MODBUS
=================================================

1  - Solicitar INT simples
2  - Solicitar FLOAT simples
3  - Solicitar STRING simples

4  - Enviar INT simples
5  - Enviar FLOAT simples
6  - Enviar STRING simples

7  - Solicitar INT MODBUS
8  - Solicitar FLOAT MODBUS
9  - Solicitar STRING MODBUS

10 - Enviar INT MODBUS
11 - Enviar FLOAT MODBUS
12 - Enviar STRING MODBUS

0  - Sair
=================================================
""")

    op = input("Escolha: ")

    try:

        if op == '1':
            solicitar_int_simples()

        elif op == '2':
            solicitar_float_simples()

        elif op == '3':
            solicitar_string_simples()

        elif op == '4':
            valor = int(input("Digite o inteiro: "))
            enviar_int_simples(valor)

        elif op == '5':
            valor = float(input("Digite o float: "))
            enviar_float_simples(valor)

        elif op == '6':
            texto = input("Digite a string: ")
            enviar_string_simples(texto)

        elif op == '7':
            solicitar_int_modbus()

        elif op == '8':
            solicitar_float_modbus()

        elif op == '9':
            solicitar_string_modbus()

        elif op == '10':
            valor = int(input("Digite o inteiro: "))
            enviar_int_modbus(valor)

        elif op == '11':
            valor = float(input("Digite o float: "))
            enviar_float_modbus(valor)

        elif op == '12':
            texto = input("Digite a string: ")
            enviar_string_modbus(texto)

        elif op == '0':
            print("Saindo...")
            break

        else:
            print("Opção inválida")

    except Exception as e:
        print("ERRO:", e)

    time.sleep(1)

ser.close()