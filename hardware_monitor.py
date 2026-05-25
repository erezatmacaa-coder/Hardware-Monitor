import psutil
import time

# Çok basit bir donanım izleme aracı
def monitor():
    print("--- Donanım İzleme Başlatıldı ---")
    try:
        while True:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            print(f"CPU Kullanımı: %{cpu} | RAM Kullanımı: %{ram}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nİzleme durduruldu.")

if __name__ == "__main__":
    monitor()