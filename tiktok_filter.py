#HOCAM BU KODDA images KLASORÜ İÇİNDE RESİMLER OLMASI LAZIM ONLARI DA DRIVE LINKI ÜZERİNDEN SİZLE PAYLAŞIYORUM 
#  https://drive.google.com/drive/folders/11DghKJI2EbkBvxMCPqybfS1FbDX0SXiM?usp=drive_link
# TikTok benzeri bir filtre uygulaması
# Bu uygulama, kullanıcının yüzünü tespit edip üzerine resim yerleştirir
# Kullanıcı bu resimleri 1-10 arası sıralayabilir
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import random
import time
from datetime import datetime

class TikTokFilter:
    def __init__(self):
        # Kamera başlatma ve ayarları
        self.cap = cv2.VideoCapture(0)
        # Kamera ayarlarını optimize et
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Temel değişkenler
        self.images = []  # Yüklenecek resimlerin listesi
        self.image_names = []  # Resim dosya isimlerini tutmak için
        self.current_image_index = 0  # Şu an gösterilen resmin indeksi
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.ranking_slots = [None] * 10  # 10 sıralama slotu
        self.all_slots_filled = False  # Tüm slotların dolu olup olmadığı
        self.completion_time = None  # Sıralamanın tamamlanma zamanı
        self.animation_frame = 0  # Animasyon için frame sayacı
        self.last_added_index = None  # Son eklenen resmin indeksini tutmak için
        self.last_face_position = None  # Son tespit edilen yüz pozisyonu
        self.face_detection_threshold = 0.3  # Yüz tespiti için eşik değeri
        
        # Sabit boyutlar
        self.head_image_size = (120, 120)  # Kafa üstündeki resim boyutu
        self.button_image_size = (80, 80)  # Buton yanındaki resim boyutu
        
        # Butonları ve resimleri yükle
        self.number_buttons = self.create_number_buttons()
        self.load_overlay_images()
        
        # FPS hesaplama için değişkenler
        self.prev_frame_time = 0
        self.new_frame_time = 0
        self.fps = 0
        
    def create_number_buttons(self):
        """1'den 10'a kadar numaralı butonları oluşturur"""
        buttons = []
        for i in range(1, 11):
            # Buton arka planı oluştur (beyaz)
            button = np.ones((60, 60, 3), dtype=np.uint8) * 255
            # Numarayı butona ekle (yeşil)
            cv2.putText(button, str(i), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            buttons.append(button)
        return buttons
        
    def load_overlay_images(self):
        """images klasöründen resimleri yükler ve karıştırır"""
        image_folder = "images"
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)
            print("'images' klasörü oluşturuldu. Lütfen bu klasöre overlay yapılacak resimleri ekleyin.")
            return

        for img_file in os.listdir(image_folder):
            if img_file.endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(image_folder, img_file)
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    if img.shape[2] == 3:  # RGB resim ise
                        # Alfa kanalı ekle
                        alpha = np.ones(img.shape[:2], dtype=img.dtype) * 255
                        img = cv2.merge((img, alpha))
                    # Tüm resimleri standart boyuta getir
                    img = cv2.resize(img, self.head_image_size)
                    self.images.append(img)
                    self.image_names.append(img_file)  # Dosya adını kaydet
                    
        if not self.images:
            print("'images' klasöründe resim bulunamadı!")
        else:
            # İmajları karıştır
            random.shuffle(self.images)
            random.shuffle(self.image_names)  # İsimleri de aynı şekilde karıştır
    
    def next_image(self):
        """Bir sonraki resme geçer"""
        if len(self.images) > 0 and not self.all_slots_filled:
            start_index = self.current_image_index
            while True:
                self.current_image_index = (self.current_image_index + 1) % len(self.images)
                # Eğer bu resim sıralamaya eklenmemişse, döngüden çık
                if self.current_image_index not in self.ranking_slots:
                    break
                # Eğer tüm resimler sıralamadaysa, döngüden çık
                if self.current_image_index == start_index:
                    break
    
    def overlay_image(self, frame, overlay, x, y, size=None):
        """Bir resmi başka bir resmin üzerine yerleştirir"""
        if overlay is None:
            return
            
        # İstenirse resmi yeniden boyutlandır
        if size is not None:
            overlay_resized = cv2.resize(overlay, size)
        else:
            overlay_resized = overlay.copy()
        
        # Çerçeve sınırlarını kontrol et
        overlay_h, overlay_w = overlay_resized.shape[:2]
        if x < 0: x = 0
        if y < 0: y = 0
        if x + overlay_w > frame.shape[1]: overlay_w = frame.shape[1] - x
        if y + overlay_h > frame.shape[0]: overlay_h = frame.shape[0] - y
        
        # Kırpma kontrolü
        if overlay_w <= 0 or overlay_h <= 0:
            return
            
        overlay_crop = overlay_resized[:overlay_h, :overlay_w]
        
        # Alpha kanalını kullanarak overlay yap
        alpha = overlay_crop[:, :, 3] / 255.0
        alpha = np.expand_dims(alpha, axis=-1)
        
        # Her renk kanalı için overlay işlemi
        for c in range(3):
            frame[y:y+overlay_h, x:x+overlay_w, c] = \
                frame[y:y+overlay_h, x:x+overlay_w, c] * (1 - alpha[:, :, 0]) + \
                overlay_crop[:, :, c] * alpha[:, :, 0]
    
    def check_if_all_slots_filled(self):
        """Tüm slotların dolu olup olmadığını kontrol eder"""
        for slot in self.ranking_slots:
            if slot is None:
                return False
        return True
    
    def add_buttons_to_frame(self, frame):
        """Frame'e numaralı butonları ekler"""
        height, width = frame.shape[:2]
        button_y = 30  # Butonları daha yukarıdan başlat
        button_spacing = 60  # Butonlar arası mesafeyi optimize et
        
        for i, button in enumerate(self.number_buttons):
            # Çerçeve sınırlarını kontrol et
            if button_y + 50 > height:
                break
                
            try:
                # Butonun boyutlarını al
                btn_h, btn_w = button.shape[:2]
                
                # Frame'in sınırlarını kontrol et
                end_y = min(button_y + btn_h, height)
                end_x = min(10 + btn_w, width)
                
                if end_x <= 10 or end_y <= button_y:
                    continue
                
                # Eğer bu slotta bir resim varsa, butonu vurgula
                button_copy = button.copy()
                if self.ranking_slots[i] is not None:
                    # Buton arka planını yeşil yap (dolu slot)
                    cv2.rectangle(button_copy, (0, 0), (btn_w-1, btn_h-1), (0, 255, 0), 3)
                    
                # Butonu frame'e yerleştir
                frame[button_y:end_y, 10:end_x] = button_copy[:end_y-button_y, :end_x-10]
                
                # Eğer bu slotta bir resim varsa, onu butonun yanına yerleştir
                if self.ranking_slots[i] is not None:
                    img_index = self.ranking_slots[i]
                    if img_index < len(self.images):
                        # Resmi butonun yanına yerleştir
                        button_right_x = 10 + btn_w + 10  # Butonun sağ kenarından 10 piksel sonra
                        # Resim boyutunu küçült
                        small_size = (int(self.button_image_size[0] * 0.8), int(self.button_image_size[1] * 0.8))
                        self.overlay_image(frame, self.images[img_index], button_right_x, button_y, small_size)
            except ValueError as e:
                print(f"Buton yerleştirme hatası: {e}")
                continue
                    
            button_y += button_spacing  # Butonlar arası mesafeyi optimize ettik
    
    def detect_faces_and_overlay(self, frame):
        """Yüz tespiti yapar ve resmi kafanın üstüne yerleştirir"""
        # Eğer tüm slotlar doluysa hiçbir şey yapma
        if self.all_slots_filled:
            return
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        if len(faces) > 0:
            # En büyük yüzü bul (muhtemelen kameraya en yakın olan)
            largest_face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = largest_face
            
            # Yüz pozisyonunu kaydet
            self.last_face_position = (x, y, w, h)
            
            if len(self.images) > 0:
                # Resmi kafanın üstüne yerleştir
                overlay_y = y - int(self.head_image_size[1] * 1.2)  # Kafanın üstüne
                if overlay_y < 0:
                    overlay_y = 0
                    
                overlay_x = x + int(w/2 - self.head_image_size[0]/2)  # Yüzün ortasına hizala
                if overlay_x < 0:
                    overlay_x = 0
                
                self.overlay_image(frame, self.images[self.current_image_index], 
                                 overlay_x, overlay_y)
        elif self.last_face_position is not None:
            # Eğer yüz tespit edilemezse ama son pozisyon biliniyorsa, son pozisyonu kullan
            x, y, w, h = self.last_face_position
            if len(self.images) > 0:
                overlay_y = y - int(self.head_image_size[1] * 1.2)
                if overlay_y < 0:
                    overlay_y = 0
                    
                overlay_x = x + int(w/2 - self.head_image_size[0]/2)
                if overlay_x < 0:
                    overlay_x = 0
                
                self.overlay_image(frame, self.images[self.current_image_index], 
                                 overlay_x, overlay_y)
    
    def handle_click(self, event, x, y, flags, param):
        """Fare tıklamalarını işler"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Eğer tüm slotlar doluysa, tıklamayı işleme
            if self.all_slots_filled:
                return
                
            # Butonlara tıklama kontrolü
            button_height = 50  # Buton yüksekliğini güncelledim
            button_spacing = 60  # Butonlar arası mesafeyi güncelledim
            button_width = 50  # Buton genişliğini güncelledim
            
            # Buton alanında mı?
            if 10 <= x <= 10 + button_width:
                button_index = (y - 30) // button_spacing  # Başlangıç yüksekliğini güncelledim
                if 0 <= button_index < 10:
                    # Eğer bu slot boşsa, doldur
                    if self.ranking_slots[button_index] is None:
                        self.ranking_slots[button_index] = self.current_image_index
                        self.last_added_index = button_index  # Son eklenen resmin indeksini kaydet
                        print(f"Resim {self.current_image_index+1} sıra numarası {button_index+1}'e yerleştirildi")
                        
                        # Tüm slotlar doldu mu kontrol et
                        self.all_slots_filled = self.check_if_all_slots_filled()
                        if self.all_slots_filled:
                            print("Tüm sıralama slotları dolduruldu!")
                            self.completion_time = time.time()
                        else:
                            # Hala boş slot var, bir sonraki resme geç
                            self.next_image()
            else:
                # Başka bir yere tıklanırsa bir sonraki resme geç
                self.next_image()
    
    def save_ranking(self):
        """Sıralama sonuçlarını dosyaya kaydeder"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ranking_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("Sıralama Sonuçları\n")
            f.write("==================\n\n")
            for i, img_index in enumerate(self.ranking_slots, 1):
                if img_index is not None:
                    img_name = self.image_names[img_index]  # Kaydedilen dosya adını kullan
                    f.write(f"{i}. Sıra: {img_name}\n")
        
        print(f"Sıralama sonuçları {filename} dosyasına kaydedildi.")
        self.save_message_time = time.time()  # Kaydetme mesajı için zamanı kaydet
    
    def reset_ranking(self):
        """Sıralamayı sıfırlar"""
        self.ranking_slots = [None] * 10
        self.all_slots_filled = False
        self.completion_time = None
        self.animation_frame = 0
        print("Sıralama sıfırlandı!")
    
    def draw_completion_animation(self, frame):
        """Tamamlanma animasyonunu çizer"""
        height, width = frame.shape[:2]
        center_x = width // 2
        center_y = height // 2
        
        # Animasyon parametreleri
        radius = 100 + int(20 * np.sin(self.animation_frame * 0.1))
        thickness = 3
        
        # Daire çiz
        cv2.circle(frame, (center_x, center_y), radius, (0, 255, 0), thickness)
        
        # Metin ekle
        text = "Siralama Tamamlandi"
        font_scale = 1.5
        thickness = 2
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Metin boyutunu hesapla
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
        text_x = center_x - text_width // 2
        text_y = center_y + text_height // 2
        
        # Metni çiz
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, (0, 255, 0), thickness)
        
        # Animasyon frame'ini güncelle
        self.animation_frame += 1
    
    def undo_last_placement(self):
        """Son eklenen resmi geri alır"""
        if self.last_added_index is not None:
            # Son eklenen resmin indeksini al
            last_image_index = self.ranking_slots[self.last_added_index]
            # Slotu temizle
            self.ranking_slots[self.last_added_index] = None
            # Mevcut resmi son eklenen resme ayarla
            self.current_image_index = last_image_index
            # Son eklenen indeksi geçici olarak sakla
            last_slot = self.last_added_index + 1
            # Son eklenen indeksi sıfırla
            self.last_added_index = None
            # Tüm slotlar dolu değil
            self.all_slots_filled = False
            self.completion_time = None
            print(f"Son eklenen resim geri alındı (Slot {last_slot})")
        else:
            print("Geri alınacak resim bulunamadı!")
    
    def run(self):
        """Ana program döngüsü"""
        cv2.namedWindow('Tiktok Placement', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Tiktok Placement', 1280, 720)
        cv2.setMouseCallback('Tiktok Placement', self.handle_click)
        self.save_message_time = 0  # Kaydetme mesajı için başlangıç zamanı
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # FPS hesaplama
            self.new_frame_time = time.time()
            self.fps = 1/(self.new_frame_time-self.prev_frame_time)
            self.prev_frame_time = self.new_frame_time
            
            frame = cv2.flip(frame, 1)
            
            # Butonları ekle
            self.add_buttons_to_frame(frame)
            
            # Yüz tespiti yap ve resmi yerleştir
            self.detect_faces_and_overlay(frame)
            
            # FPS'i ekrana yaz
            cv2.putText(frame, f"FPS: {int(self.fps)}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Sağ üst köşeye klavye kontrollerini ekle
            controls_y = 30
            controls_x = frame.shape[1] - 300  # Sağdan 300 piksel içeride başla
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            thickness = 2
            color = (255, 255, 255)
            
            controls = [
                "Kapatmak icin Q",
                "Geri almak icin B",
                "Gecmek icin N",
                "Sifirlamak icin R",
                "Kaydetmek icin S"
            ]
            
            for control in controls:
                cv2.putText(frame, control, (controls_x, controls_y), 
                           font, font_scale, color, thickness)
                controls_y += 30  # Her satır için 30 piksel aşağı in
            
            # Alt kısımdaki mesajları göster
            if not self.all_slots_filled:
                # Talimat yazısı
                cv2.putText(frame, "", 
                          (200, frame.shape[0]-30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            else:
                # Kaydetme mesajını göster (3 saniye boyunca)
                if time.time() - self.save_message_time < 3:
                    cv2.putText(frame, "Siralama Kaydedildi!", 
                              (200, frame.shape[0]-30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    # Kaydetme mesajı gösterilmiyorsa tamamlanma mesajını göster
                    cv2.putText(frame, "Siralama Tamamlandi!", 
                              (200, frame.shape[0]-30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Tiktok Placement', frame)
            
            # Klavye kontrolleri
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Çıkış
                break
            elif key == ord('n') and not self.all_slots_filled:  # Sonraki resim
                self.next_image()
            elif key == ord('r'):  # Sıralamayı sıfırla
                self.reset_ranking()
            elif key == ord('b'):  # Son eklenen resmi geri al
                self.undo_last_placement()
            elif key == ord('s'):  # Sıralamayı kaydet
                self.save_ranking()
                
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    filter = TikTokFilter()
    filter.run() 