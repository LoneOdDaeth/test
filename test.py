import psutil
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
from datetime import datetime
import csv

class NetworkTrafficMonitor:
    def __init__(self, root):  # '__init__' doğru şekilde yazıldı
        self.root = root
        self.root.title("Ağ Trafiği Görselleştirme Aracı")
        self.root.configure(bg='#f0f0f0')
        
        # Grafik oluşturma
        self.figure, self.ax = plt.subplots(figsize=(16, 9))
        self.data_limit = -1  # Veri limiti başlangıçta tanımsız
        self.ax.set_title("Anlık Ağ Trafiği", fontsize=14, fontweight='bold')
        self.ax.set_xlabel("Zaman", fontsize=12)
        self.ax.set_ylabel("Veri Miktarı (MB)", fontsize=12)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        if self.data_limit > 0:
            self.ax.axhline(y=self.data_limit, color='red', linestyle='--', linewidth=2, label='Veri Limiti')

        # Veri saklama ve hesaplama için gerekli değişkenler
        self.upload_data = []
        self.download_data = []
        self.time_data = []
        self.start_time = time.time()
        initial_net_io = psutil.net_io_counters()
        self.prev_upload = initial_net_io.bytes_sent
        self.prev_download = initial_net_io.bytes_recv
        self.initial_upload = initial_net_io.bytes_sent
        self.initial_download = initial_net_io.bytes_recv
        
        # Grafik Canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
        
        # Toplam veri miktarı göstergeleri
        total_frame = tk.Frame(self.root, bg='#f0f0f0')
        total_frame.pack(side='top', pady=10)
        self.total_upload_label = tk.Label(total_frame, text="Toplam Gönderilen Veri: 0 MB", font=('Helvetica', 12), bg='#f0f0f0', fg='red')
        self.total_upload_label.pack(side='left', padx=10)
        self.total_download_label = tk.Label(total_frame, text="Toplam Alınan Veri: 0 MB", font=('Helvetica', 12), bg='#f0f0f0', fg='blue')
        self.total_download_label.pack(side='left', padx=10)
        self.data_limit_label = tk.Label(total_frame, text="Veri Limiti: - MB", font=('Helvetica', 12), bg='#f0f0f0', fg='black')
        self.data_limit_label.pack(side='left', padx=10)
        
        # Anlık hız göstergeleri
        speed_frame = tk.Frame(self.root, bg='#f0f0f0')
        speed_frame.pack(side='top', pady=5)
        self.upload_speed_label = tk.Label(speed_frame, text="Gönderim Hızı: 0 MB/s", font=('Helvetica', 12), bg='#f0f0f0', fg='red')
        self.upload_speed_label.pack(side='left', padx=10)
        self.download_speed_label = tk.Label(speed_frame, text="Alım Hızı: 0 MB/s", font=('Helvetica', 12), bg='#f0f0f0', fg='blue')
        self.download_speed_label.pack(side='left', padx=10)
        
        # Menü çubuğu
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Verileri Kaydet", command=self.save_data)
        file_menu.add_command(label="Grafiği Kaydet", command=self.save_graph)
        file_menu.add_command(label="Veri Limiti Ayarla", command=self.set_data_limit)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.root.quit)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        self.root.config(menu=menubar)
        
        # Veri limiti girişi
        self.data_limit_entry = tk.Entry(self.root, font=('Helvetica', 12))
        self.data_limit_entry.pack(side='top', pady=5)
        self.data_limit_entry.bind('<Return>', self.update_data_limit)

        # Ağ trafiği dağılımı tablosu
        table_frame = tk.Frame(self.root, bg='#f0f0f0')
        table_frame.pack(side='bottom', fill='x', padx=10, pady=10)
        self.traffic_table = ttk.Treeview(table_frame, columns=("Uygulama/Port", "Gönderilen Veri (MB)", "Alınan Veri (MB)"), show='headings')
        self.traffic_table.heading("Uygulama/Port", text="Uygulama/Port")
        self.traffic_table.heading("Gönderilen Veri (MB)", text="Gönderilen Veri (MB)")
        self.traffic_table.heading("Alınan Veri (MB)", text="Alınan Veri (MB)")
        self.traffic_table.pack(fill='x')
        
        # Verileri güncelleme
        self.start_monitoring()

    def update_data_limit(self, event=None):
        try:
            value = self.data_limit_entry.get()
            if value.strip():
                self.data_limit = float(value)
                self.data_limit_label.config(text=f"Veri Limiti: {self.data_limit} MB")
            else:
                self.data_limit = -1
                self.data_limit_label.config(text="Veri Limiti: - MB")
        except ValueError:
            messagebox.showerror("Geçersiz Giriş", "Lütfen geçerli bir sayı girin!")

    def set_data_limit(self):
        try:
            new_limit = simpledialog.askfloat("Veri Limiti", "Veri limiti belirleyin (MB):", minvalue=1, maxvalue=10000)
            if new_limit is not None:
                self.data_limit = new_limit
                self.data_limit_label.config(text=f"Veri Limiti: {self.data_limit} MB")
        except ValueError:
            messagebox.showerror("Geçersiz Giriş", "Lütfen geçerli bir sayı girin!")

    def start_monitoring(self):
        self.update_traffic_data()

    def update_traffic_data(self):
        net_io = psutil.net_io_counters()
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Veri oranını (hızı) hesapla
        upload = net_io.bytes_sent
        download = net_io.bytes_recv
        upload_speed = (upload - self.prev_upload) / (1024 * 1024)
        download_speed = (download - self.prev_download) / (1024 * 1024)
        self.prev_upload = upload
        self.prev_download = download
        
        # Anlık hızları güncelle
        self.upload_speed_label.config(text=f"Gönderim Hızı: {upload_speed:.2f} MB/s", fg='green')
        self.download_speed_label.config(text=f"Alım Hızı: {download_speed:.2f} MB/s")
        
        # Verileri sakla
        self.time_data.append(current_time)
        self.upload_data.append((upload - self.initial_upload) / (1024 * 1024))
        self.download_data.append((download - self.initial_download) / (1024 * 1024))
        
        # Toplam veri miktarını güncelle
        total_upload = (upload - self.initial_upload) / (1024 * 1024)
        total_download = (download - self.initial_download) / (1024 * 1024)
        self.total_upload_label.config(text=f"Toplam Gönderilen Veri: {total_upload:.2f} MB", fg='green')
        self.total_download_label.config(text=f"Toplam Alınan Veri: {total_download:.2f} MB")
        
        # Veri limiti kontrolü
        if self.data_limit > 0 and total_download > self.data_limit:
            self.data_limit_label.config(text=f"Veri Limiti Aşıldı: {self.data_limit} MB", fg='red')
        else:
            self.data_limit_label.config(text=f"Veri Limiti: {self.data_limit} MB" if self.data_limit > 0 else "Veri Limiti: - MB", fg='black')
        
        # Grafiği güncelleme
        self.ax.clear()
        if self.data_limit > 0:
            self.ax.axhline(y=self.data_limit, color='red', linestyle='--', linewidth=2, label='Veri Limiti')
        self.ax.plot(self.time_data, self.upload_data, label="Gönderilen Veri", color='green', linewidth=2)
        self.ax.plot(self.time_data, self.download_data, label="Alınan Veri", color='blue', linewidth=2)
        self.ax.set_title("Anlık Ağ Trafiği", fontsize=14, fontweight='bold')
        self.ax.set_xlabel("Zaman", fontsize=12)
        self.ax.set_ylabel("Veri Miktarı (MB)", fontsize=12)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.legend()
        self.canvas.draw()
        
        # Veri güncellemesini tekrar et
        self.root.after(1000, self.update_traffic_data)

    def save_data(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
            if file_path:
                with open(file_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Zaman", "Gönderilen Veri (MB)", "Alınan Veri (MB)"])
                    for i in range(len(self.time_data)):
                        writer.writerow([self.time_data[i], self.upload_data[i], self.download_data[i]])
                messagebox.showinfo("Başarılı", "Veriler başarıyla kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Veriler kaydedilirken bir hata oluştu: {str(e)}")

    def save_graph(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
            if file_path:
                self.figure.savefig(file_path)
                messagebox.showinfo("Başarılı", "Grafik başarıyla kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Grafik kaydedilirken bir hata oluştu: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkTrafficMonitor(root)
    root.mainloop()
