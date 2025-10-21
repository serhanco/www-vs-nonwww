import dns.resolver
import requests
import ssl
import socket
import datetime
import pandas as pd
from cryptography import x509
from cryptography.hazmat.backends import default_backend

# ----------------------------------------------------------------------
# FONKSİYON 1: A KAYDI (IP) ÇÖZÜMLEME
# ----------------------------------------------------------------------
def resolve_domain(domain):
    """Belirtilen alan adının IP adreslerini çözer (sadece A kaydı)."""
    ip_list = []
    resolver = dns.resolver.Resolver()
    resolver.timeout = 2
    resolver.lifetime = 2
    
    try:
        answers = resolver.resolve(domain, 'A')
        for rdata in answers:
            ip_list.append(str(rdata))
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        pass 
    except Exception as e:
        ip_list.append(f"HATA: {type(e).__name__}")
        
    return ip_list

# ----------------------------------------------------------------------
# FONKSİYON 2: SSL DURUMU VE SÜRE KONTROLÜ
# ----------------------------------------------------------------------
def check_ssl_status(domain):
    """Belirtilen alan adının SSL sertifikası durumunu ve süresini kontrol eder."""
    context = ssl.create_default_context()
    
    try:
        # Sunucuya bağlan
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as conn:
                # Sertifikayı al
                certificate = conn.getpeercert(binary_form=True)
                
                # Sertifikayı ayrıştır
                x509_cert = x509.load_der_x509_certificate(certificate, default_backend())
                
                # Geçerlilik bitiş tarihini al
                expiry_date = x509_cert.not_valid_after.replace(tzinfo=datetime.timezone.utc)
                now = datetime.datetime.now(datetime.timezone.utc)
                
                # Kalan gün sayısını hesapla
                remaining_days = (expiry_date - now).days
                
                return {
                    'SSL Durumu': "✔️ AKTİF",
                    'Kalan Gün': max(0, remaining_days)
                }

    except socket.gaierror:
        return {'SSL Durumu': "❌ DNS/IP YOK", 'Kalan Gün': 'N/A'}
    except socket.timeout:
        return {'SSL Durumu': "❌ TIMEOUT", 'Kalan Gün': 'N/A'}
    except (ssl.SSLCertVerificationError, ssl.SSLError, ConnectionRefusedError):
        return {'SSL Durumu': "⚠️ SERTİFİKA HATASI", 'Kalan Gün': 'N/A'}
    except Exception:
        return {'SSL Durumu': "❌ PASİF/HATA", 'Kalan Gün': 'N/A'}


# ALAN ADI LISTENIZ
domain_list = [
    "acibademinternational.com", "acibadem.al", "acibadem.ar", "acibadem.rs", 
    "acibadem.fr", "acibadem.bg", "acibadem.com.ru", "acibadem.ba", 
    "acibadem.mk", "acibadem.com.de", "acibadem.hr", "acibadem.ge", 
    "acibadem.com.ro", "acibadem.ir", "acibadem.com.az", "acibadem.ua",
    "acibadem.ae" 
]

results = []

print("🚀 DNS ve SSL Kontrol İşlemi Başlatılıyor...\n")

for domain in domain_list:
    
    # DNS Kontrolü
    non_www_a = resolve_domain(domain)
    www_domain = f"www.{domain}"
    www_a = resolve_domain(www_domain)
    
    # SSL Kontrolü (Non-WWW)
    ssl_status = check_ssl_status(domain)
    
    # Uyum Kontrolü
    non_www_set = set(non_www_a)
    www_set = set(www_a)
    
    # Emojili Uyum Kontrolü Metinleri
    if non_www_set == www_set and non_www_set:
        uyum_kontrolu_metni = "✔️ EŞLEŞİYOR"
    elif not non_www_set and not www_set:
        uyum_kontrolu_metni = "⚠️ HER İKİSİ DE YOK"
    elif non_www_set and not www_set:
        uyum_kontrolu_metni = "❌ WWW KAYDI YOK"
    elif not non_www_set and www_set:
        uyum_kontrolu_metni = "❌ NON-WWW KAYDI YOK"
    else:
        uyum_kontrolu_metni = "🚨 FARKLI IP'ler"

    # Excel için Emojisiz Metin (Excel'de emoji sorunlarını engellemek için)
    uyum_kontrolu_excel = uyum_kontrolu_metni.split(' ', 1)[-1]
    
    # Sonuçları listeye ekle
    results.append({
        'Alan Adı': domain,
        'Non-WWW IP': ', '.join(non_www_a) if non_www_a else 'YOK',
        'WWW IP': ', '.join(www_a) if www_a else 'YOK',
        'Uyum Kontrolü (Konsol)': uyum_kontrolu_metni,
        'Uyum Kontrolü': uyum_kontrolu_excel, # Excel için sade metin
        'SSL Durumu': ssl_status['SSL Durumu'].replace('✔️ ', '').replace('❌ ', '').replace('⚠️ ', ''),
        'Kalan Gün': ssl_status['Kalan Gün']
    })

# ----------------------------------------------------------------------
# SONUÇLARI KAYDETME VE YAZDIRMA
# ----------------------------------------------------------------------

# 1. Pandas DataFrame Oluşturma
# Excel'e kaydederken Emojisiz sütunu kullanıyoruz.
df = pd.DataFrame(results).drop(columns=['Uyum Kontrolü (Konsol)']) 
df = df[['Alan Adı', 'Non-WWW IP', 'WWW IP', 'Uyum Kontrolü', 'SSL Durumu', 'Kalan Gün']] # Sütunları düzenleme

# 2. Dosya Adını Oluşturma
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
file_name = f"DNS_SSL_Kontrol_Raporu_{timestamp}.xlsx"

# 3. Excel'e Kaydetme
try:
    df.to_excel(file_name, index=False, sheet_name="Kontrol Sonuçları")
    print("\n" + "="*50)
    print(f"✅ Başarılı! Rapor Excel dosyasına kaydedildi:")
    print(f"   Dosya Adı: {file_name}")
    print("="*50)
except Exception as e:
    print(f"\n❌ HATA: Excel'e kaydederken bir sorun oluştu: {e}")


# 4. Konsola Tabloyu Yazdırma
print("\n---")
print("KONSOL RAPORU")
print("---")
# Konsol çıktısında Emojili sütunu kullanıyoruz.
print("{:<30} | {:<20} | {:<20} | {:<18} | {:<18} | {}".format(
    "ALAN ADI", "NON-WWW IP", "WWW IP", "UYUM KONTROLÜ", "SSL DURUMU", "KALAN GÜN"
))
print("---" * 95)

for item in results:
    non_www_a_str = item['Non-WWW IP']
    www_a_str = item['WWW IP']
    
    if len(non_www_a_str) > 20: non_www_a_str = non_www_a_str[:17] + "..."
    if len(www_a_str) > 20: www_a_str = www_a_str[:17] + "..."
        
    print("{:<30} | {:<20} | {:<20} | {:<18} | {:<18} | {}".format(
        item['Alan Adı'], 
        non_www_a_str, 
        www_a_str, 
        item['Uyum Kontrolü (Konsol)'], # Emojili sütun
        item['SSL Durumu'],
        item['Kalan Gün']
    ))

print("\n(Lütfen aynı klasördeki Excel dosyasını kontrol edin.)")