from machine import Pin, SoftI2C
import time

# ===================================================================
# SSD1306 EMBUTIDO
# ===================================================================
class SSD1306_I2C:
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = height // 8
        self.buffer = bytearray(self.pages * width)
        self.framebuf = framebuf.FrameBuffer(
            self.buffer, width, height, framebuf.MONO_VLSB)
        self._cmd = bytearray(2)
        self._head = bytearray(b'\x40')
        self._init()

    def _wc(self, c):
        self._cmd[0] = 0x80
        self._cmd[1] = c
        self.i2c.writeto(self.addr, self._cmd)

    def _init(self):
        for c in (
            0xAE, 0x20, 0x00, 0x40, 0xA1, 0xC8,
            0xA8, self.height - 1, 0xD3, 0x00,
            0xDA, 0x02 if self.height == 32 else 0x12,
            0xD5, 0x80, 0xD9, 0xF1, 0xDB, 0x30,
            0x81, 0xFF, 0xA4, 0xA6, 0x8D, 0x14, 0xAF,
        ):
            self._wc(c)
        self.fill(0)
        self.show()

    def show(self):
        self._wc(0x21); self._wc(0); self._wc(self.width - 1)
        self._wc(0x22); self._wc(0); self._wc(self.pages - 1)
        self.i2c.writevto(self.addr, [self._head, self.buffer])

    def fill(self, c):          self.framebuf.fill(c)
    def text(self, s, x, y, c=1): self.framebuf.text(s, x, y, c)
    def hline(self, x, y, w, c):  self.framebuf.hline(x, y, w, c)
    def vline(self, x, y, h, c):  self.framebuf.vline(x, y, h, c)
    def fill_rect(self, x, y, w, h, c): self.framebuf.fill_rect(x, y, w, h, c)
    def rect(self, x, y, w, h, c): self.framebuf.rect(x, y, w, h, c)

    def off(self):
        self.fill(0)
        self.show()
        self._wc(0xAE)


# ===================================================================
# TESTE
# ===================================================================

print("=== TESTE DE DISPLAY OLED ===\n")

# 1. Verificar se I2C consegue encontrar o display
print("1. Testando I2C scan...")
i2c = SoftI2C(sda=Pin(16), scl=Pin(17), freq=100000)
devices = i2c.scan()
print("   Dispositivos encontrados:", devices)

if not devices:
    print("   ERRO: Nenhum dispositivo encontrado!")
    print("   Verifique: SDA=GPIO0, SCL=GPIO1, cabos, GND, VCC")
else:
    print("   OK: Display encontrado no endereco 0x{:X}".format(devices[0]))

# 2. Tentar inicializar o display
print("\n2. Inicializando display...")
try:
    import framebuf
    oled = SSD1306_I2C(128, 64, i2c)
    print("   OK: Display inicializado com sucesso!")
except Exception as e:
    print("   ERRO ao inicializar:", e)
    import sys
    sys.exit(1)

# 3. Testar escrita no display
print("\n3. Testando escrita no display...")
try:
    oled.fill(0)
    oled.text("TESTE", 45, 10, 1)
    oled.text("Display OK!", 25, 30, 1)
    oled.text("v1.0", 50, 50, 1)
    oled.show()
    print("   OK: Texto exibido no display!")
except Exception as e:
    print("   ERRO ao escrever:", e)
    import sys
    sys.exit(1)

# 4. Animar um teste
print("\n4. Animacao de teste...")
try:
    for i in range(3):
        oled.fill(0)
        oled.text("Teste " + str(i+1), 35, 20, 1)
        oled.text("3 testes", 30, 40, 1)
        oled.show()
        time.sleep_ms(500)
        
        oled.fill(0)
        oled.show()
        time.sleep_ms(500)
    
    oled.fill(0)
    oled.text("SUCESSO!", 35, 25, 1)
    oled.show()
    print("   OK: Animacao executada!")
except Exception as e:
    print("   ERRO na animacao:", e)
    import sys
    sys.exit(1)

# 5. Teste de graficos
print("\n5. Testando graficos...")
try:
    time.sleep_ms(500)
    oled.fill(0)
    oled.text("Graficos:", 30, 5, 1)
    oled.hline(10, 20, 108, 1)
    oled.vline(64, 25, 30, 1)
    oled.rect(5, 30, 118, 32, 1)
    oled.show()
    time.sleep_ms(1000)
    print("   OK: Graficos desenhados!")
except Exception as e:
    print("   ERRO nos graficos:", e)
    import sys
    sys.exit(1)

# 6. Desligar
print("\n6. Desligando display...")
try:
    oled.off()
    print("   OK: Display desligado!")
except Exception as e:
    print("   ERRO ao desligar:", e)

print("\n=== TESTE CONCLUIDO COM SUCESSO ===")

