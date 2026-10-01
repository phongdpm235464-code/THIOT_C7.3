from machine import Pin, PWM
import network
import urequests
import time

# ===== LỚP ĐIỀU KHIỂN SERVO =====
class Servo:
    """Lớp điều khiển Servo bằng PWM trên ESP32"""
    def __init__(self, pin_number):
        self.pwm = PWM(Pin(pin_number), freq=50)  
        self.pwm.duty(77)  
    
    def write(self, angle):
        angle = max(0, min(180, angle))
        duty = int(26 + (angle / 180) * (128 - 26))
        self.pwm.duty(duty)

# ===== CẤU HÌNH WIFI =====
WIFI_SSID = "Wokwi-GUEST"    
WIFI_PASS = ""                

# ===== CẤU HÌNH THINGSPEAK =====
# HÃY ĐỔI KEY NÀY THÀNH WRITE API KEY TRÊN TÀI KHOẢN CỦA BẠN (VD: 6MLG9LRQ2YRUSG6V)
WRITE_API_KEY = "6MLG9LRQ2YRUSG6V" 
THINGSPEAK_URL = "http://api.thingspeak.com/update"

# ===== CẤU HÌNH SERVO =====
SERVO_LEFT_PIN = 13     
SERVO_RIGHT_PIN = 14    

SEND_INTERVAL = 16000  # Đổi thành 16000 milliseconds (16 giây)

def connect_wifi():
    print("=" * 40)
    print("  IoT Lab 03 - Servo + ThingSpeak")
    print("  ESP32 MicroPython")
    print("=" * 40)
    
    wlan = network.WLAN(network.STA_IF) 
    wlan.active(True)                   
    
    if not wlan.isconnected():
        print(f"Đang kết nối WiFi: {WIFI_SSID}")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        
        timeout = 0
        while not wlan.isconnected() and timeout < 40:
            time.sleep(0.5)
            print(".", end="")
            timeout += 1
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"\n✓ Kết nối WiFi thành công!")
        print(f"  IP: {ip}")
        return True
    else:
        print("\n✗ Không thể kết nối WiFi!")
        return False

def send_to_thingspeak(angle_left, angle_right):
    try:
        url = (
            f"{THINGSPEAK_URL}"
            f"?api_key={WRITE_API_KEY}"
            f"&field1={angle_left}"
            f"&field2={angle_right}"
        )
        print("--- Gửi dữ liệu lên ThingSpeak ---")
        
        response = urequests.get(url)
        
        if response.status_code == 200:
            entry_id = response.text
            print(f"  ✓ Thành công! Entry #{entry_id}")
        else:
            print(f"  ✗ Lỗi HTTP: {response.status_code}")
        
        response.close() 
        
    except Exception as e:
        print(f"  ✗ Lỗi gửi dữ liệu: {e}")

def main():
    wifi_ok = connect_wifi()
    
    servo_left = Servo(SERVO_LEFT_PIN)
    servo_right = Servo(SERVO_RIGHT_PIN)
    print(f"✓ Servo trái khởi tạo trên GPIO {SERVO_LEFT_PIN}")
    print(f"✓ Servo phải khởi tạo trên GPIO {SERVO_RIGHT_PIN}")
    print("=" * 40)
    print("Bắt đầu điều khiển servo...\n")
    
    angle = 0           
    step = 5            
    going_up = True      
    
    # Dùng ticks_ms để đếm thời gian chính xác trong MicroPython
    last_send = time.ticks_ms() 
    
    while True:
        if going_up:
            angle += step
            if angle >= 180:
                angle = 180
                going_up = False    
        else:
            angle -= step
            if angle <= 0:
                angle = 0
                going_up = True     
        
        angle_left = angle           
        angle_right = 180 - angle    
        
        servo_left.write(angle_left)
        servo_right.write(angle_right)
        
        print(f"Servo trái: {angle_left:3d}° | Servo phải: {angle_right:3d}°")
        
        now = time.ticks_ms()
        # Kiểm tra xem đã trôi qua đủ 16000 ms chưa
        if wifi_ok and time.ticks_diff(now, last_send) >= SEND_INTERVAL:
            last_send = now
            send_to_thingspeak(angle_left, angle_right)
            print()
        
        time.sleep(0.2)

# Chạy chương trình
if __name__ == '__main__':
    main()