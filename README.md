# TikTok Benzeri Filtre Uygulaması

Bu proje, kullanıcıların yüzlerini tespit eden ve üzerine resim yerleştiren bir TikTok benzeri filtre uygulamasıdır. Kullanıcı, resimleri 1-10 arası sıralayabilir ve bu resimleri kafalarının üstünde görebilir.

## Özellikler

- Yüz tespiti
- Kullanıcı tarafından yüklenen resimlerin üzerine yerleştirilmesi
- Resimlerin sıralanması
- Kullanıcı dostu arayüz
- Kaydetme ve sıfırlama özellikleri

## Gereksinimler

Bu projeyi çalıştırmak için aşağıdaki Python kütüphanelerine ihtiyacınız var:

- OpenCV
- NumPy
- Pillow

## Kullanım

1. `images` klasörüne kullanmak istediğiniz resimleri ekleyin.
2. Uygulamayı başlatmak için aşağıdaki komutu çalıştırın:
 ```bash
python tiktok_filter.py
```
4. 3. Uygulama açıldığında, yüzünüzü kameraya doğru tutun. Uygulama yüzünüzü tespit edecek ve üzerine resim yerleştirecektir.
5. Butonlara tıklayarak resimleri sıralayabilirsiniz.
6. `S` tuşuna basarak sıralamayı kaydedebilirsiniz.
7. `R` tuşuna basarak sıralamayı sıfırlayabilirsiniz.
8. `B` tuşuna basarak son eklenen resmi geri alabilirsiniz.
9. `Q` tuşuna basarak uygulamadan çıkabilirsiniz.
