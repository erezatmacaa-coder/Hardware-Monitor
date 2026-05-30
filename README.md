# Hardware Monitor 💻

**Gerçek zamanlı sistem izleme aracı** — Terminal içinde canlı, renkli ve bilgilendirici bir gösterge paneli.

## Özellikler

- 🖥️ **CPU** — Çekirdek bazında kullanım, frekans, sıcaklık
- 🧠 **RAM** — Toplam/kullanılan/boş bellek + Swap
- 💾 **Disk** — Depolama kullanımı + I/O istatistikleri
- 🌐 **Ağ** — Her ağ arayüzü için hız, IP, veri transferi
- 🔋 **Pil** — Kalan yüzde, şarj durumu (dizüstü için)
- 🎮 **GPU** — NVIDIA ekran kartı kullanımı (varsa)
- 📊 **İşlemler** — En çok kaynak tüketen 10 işlem
- ⚡ **Canlı Güncelleme** — Saniyede bir otomatik yenileme

## Kurulum

```bash
pip install rich psutil
python hardware_monitor.py
```

> ⚠️ GPU bilgisi için: NVIDIA kartınızda `nvidia-smi` yüklü olmalı.
