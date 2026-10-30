import { useState } from 'react';
import { BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer } from 'recharts';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return alert("Lütfen önce bir dosya seçin!");
    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setResults(data);
    } catch (err) {
      alert("Hata oluştu! Backend sunucusunun çalıştığından emin olun.");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(results.academic_text);
    alert("Akademik metin kopyalandı!");
  };

  return (
    <div style={{ padding: "40px", fontFamily: "sans-serif", maxWidth: "900px", margin: "auto", color: "#333" }}>
      
      {/* BAŞLIK */}
      <h1 style={{ color: "#2c3e50" }}>Klinik Veri Analiz Merkezi 🩺</h1>
      <p>Gelişmiş Klinik Veri Analiz ve İstatistik Motoru</p>

      {/* DOSYA YÜKLEME ALANI */}
      <div style={{ border: "2px dashed #3498db", padding: "20px", borderRadius: "8px", margin: "20px 0", backgroundColor: "#f0f8ff" }}>
        <input type="file" accept=".xlsx, .csv" onChange={(e) => setFile(e.target.files[0])} />
        <button 
          onClick={handleUpload} 
          disabled={loading}
          style={{ marginLeft: "10px", padding: "10px 20px", cursor: "pointer", backgroundColor: "#3498db", color: "white", border: "none", borderRadius: "5px", fontWeight: "bold" }}
        >
          {loading ? "Analiz Ediliyor..." : "Veriyi Analiz Et"}
        </button>
      </div>

      {results && (
        <div>
          <h2 style={{ borderBottom: "2px solid #eee", paddingBottom: "10px" }}>Rapor: {results.filename}</h2>
          
          {/* 1. OTOMATİK AKADEMİK METİN */}
          {results.academic_text && (
            <div style={{ padding: "20px", backgroundColor: "#fffae6", borderLeft: "5px solid #f59e0b", borderRadius: "8px", marginTop: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                <h3 style={{ margin: 0, color: "#d97706" }}>📝 Otomatik Makale Bulguları</h3>
                <button onClick={copyToClipboard} style={{ padding: "5px 10px", cursor: "pointer", backgroundColor: "#f59e0b", color: "white", border: "none", borderRadius: "4px" }}>
                  Kopyala
                </button>
              </div>
              <p style={{ fontStyle: "italic", lineHeight: "1.6", color: "#451a03", fontSize: "1.1em" }}>"{results.academic_text}"</p>
            </div>
          )}

          {/* 2. BÜYÜK GRAFİKLER */}
          <div style={{ display: "flex", gap: "20px", flexWrap: "wrap", marginTop: "30px" }}>
            {results.chart_data && results.chart_data.length > 0 && (
              <div style={{ flex: "1", minWidth: "400px", padding: "20px", backgroundColor: "#f9f9f9", borderRadius: "8px", boxShadow: "0 2px 5px rgba(0,0,0,0.1)" }}>
                <h3 style={{ textAlign: "center" }}>📊 Cinsiyete Göre Yaş</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={results.chart_data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="Cinsiyet" />
                    <YAxis />
                    <Tooltip cursor={{fill: 'transparent'}}/>
                    <Bar dataKey="Ortalama Yas" fill="#8884d8" radius={[5, 5, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {results.scatter_data && results.scatter_data.length > 0 && (
              <div style={{ flex: "1", minWidth: "400px", padding: "20px", backgroundColor: "#f9f9f9", borderRadius: "8px", boxShadow: "0 2px 5px rgba(0,0,0,0.1)" }}>
                <h3 style={{ textAlign: "center" }}>📈 Yaş ve Kan Basıncı</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" dataKey="Yas" name="Yaş" />
                    <YAxis type="number" dataKey="Kan_Basinci" name="Tansiyon" />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <Scatter data={results.scatter_data} fill="#82ca9d" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* 3. TEMEL İSTATİSTİK (T-TEST, KORELASYON VE KI-KARE) */}
          <div style={{ marginTop: "40px" }}>
            {results.group_test_result && (
              <div style={{ marginBottom: "20px", padding: "20px", backgroundColor: "#eef2ff", borderLeft: "5px solid #4f46e5", borderRadius: "4px" }}>
                <h3 style={{ margin: "0 0 10px 0" }}>🔬 {results.group_test_result.test_adi}</h3>
                <p style={{ margin: "5px 0" }}>{results.group_test_result.aciklama}</p>
                <p style={{ margin: "5px 0" }}><strong>P-Değeri:</strong> <span style={{ color: results.group_test_result.anlamli_mi ? "#16a34a" : "#dc2626", fontWeight: "bold" }}>{results.group_test_result.p_degeri}</span></p>
                <p style={{ margin: "5px 0" }}><strong>Sonuç:</strong> {results.group_test_result.anlamli_mi ? "Gruplar arası anlamlı FARK VAR (p < 0.05)" : "Anlamlı FARK YOK (p > 0.05)"}</p>
              </div>
            )}

            {results.correlation_result && (
              <div style={{ marginBottom: "20px", padding: "20px", backgroundColor: "#fff0f5", borderLeft: "5px solid #db2777", borderRadius: "4px" }}>
                <h3 style={{ margin: "0 0 10px 0" }}>🔗 Pearson Korelasyonu</h3>
                <p style={{ margin: "5px 0" }}>{results.correlation_result.aciklama}</p>
                <p style={{ margin: "5px 0" }}><strong>r (İlişki Gücü):</strong> {results.correlation_result.r_degeri}</p>
                <p style={{ margin: "5px 0" }}><strong>P-Değeri:</strong> <span style={{ color: results.correlation_result.anlamli_mi ? "#16a34a" : "#dc2626", fontWeight: "bold" }}>{results.correlation_result.p_degeri}</span></p>
              </div>
            )}

            {/* İŞTE UNUTTUĞUM O EKSİK KUTUCUK (Kİ-KARE) */}
            {results.chi_square_result && (
              <div style={{ marginBottom: "20px", padding: "20px", backgroundColor: "#f0fdf4", borderLeft: "5px solid #22c55e", borderRadius: "4px" }}>
                <h3 style={{ margin: "0 0 10px 0" }}>🧮 Kategorik İlişki (Ki-Kare Testi)</h3>
                <p style={{ margin: "5px 0" }}>{results.chi_square_result.aciklama}</p>
                <p style={{ margin: "5px 0" }}><strong>Ki-Kare Değeri:</strong> {results.chi_square_result.chi2_degeri}</p>
                <p style={{ margin: "5px 0" }}><strong>P-Değeri:</strong> <span style={{ color: results.chi_square_result.anlamli_mi ? "#16a34a" : "#dc2626", fontWeight: "bold" }}>{results.chi_square_result.p_degeri}</span></p>
              </div>
            )}
          </div>

          {/* 4. TABLO 1 VE NORMALLİK */}
          <div style={{ display: "flex", gap: "20px", marginTop: "30px" }}>
            <div style={{ flex: "1", padding: "20px", backgroundColor: "#f8f9fa", borderRadius: "8px" }}>
              <h3>📑 Tablo 1: Demografik Veriler</h3>
              <ul style={{ lineHeight: "1.8" }}>
                {results.demographics && Object.entries(results.demographics).map(([col, val]) => (
                  <li key={col}><strong>{col}:</strong> {val}</li>
                ))}
              </ul>
            </div>
            <div style={{ flex: "1", padding: "20px", backgroundColor: "#f8f9fa", borderRadius: "8px" }}>
              <h3>📐 Normallik Testleri (Shapiro-Wilk)</h3>
              <ul style={{ lineHeight: "1.8" }}>
                {results.normality && Object.entries(results.normality).map(([col, val]) => (
                  <li key={col}>
                    <strong>{col}:</strong> p = {val.p_value ?? "N/A"} ➔ <i>{val.next_step}</i>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* 5. İLERİ DÜZEY MODÜLLER VE MİNİ GRAFİKLER */}
          {results.advanced_modules && (
            <div style={{ marginTop: "40px", padding: "20px", backgroundColor: "#1e293b", color: "white", borderRadius: "8px" }}>
              <h3 style={{ borderBottom: "1px solid #475569", paddingBottom: "10px", margin: "0 0 10px 0" }}>🚀 İleri Düzey Araştırma Modülleri</h3>
              
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(350px, 1fr))", gap: "20px", marginTop: "20px" }}>
                {results.advanced_modules.map((mod, idx) => (
                  <div key={idx} style={{ backgroundColor: "#334155", padding: "15px", borderRadius: "6px", borderLeft: `5px solid ${mod.renk}`, display: "flex", flexDirection: "column" }}>
                    <h4 style={{ margin: "0 0 8px 0", color: "#f8fafc" }}>{mod.isim}</h4>
                    <div>
                      <span style={{ display: "inline-block", padding: "3px 8px", backgroundColor: mod.renk, color: "white", borderRadius: "12px", fontSize: "0.8em", marginBottom: "10px" }}>{mod.durum}</span>
                    </div>
                    <p style={{ margin: "0 0 10px 0", fontSize: "0.9em", color: "#94a3b8", flexGrow: 1 }}>{mod.detay}</p>
                    
                    {/* KUTU İÇİ DİNAMİK GRAFİK */}
                    {mod.chart_data && (
                      <div style={{ marginTop: "10px", padding: "10px", backgroundColor: "#1e293b", borderRadius: "6px", height: "160px" }}>
                        <h5 style={{ textAlign: "center", margin: "0 0 10px 0", color: "#cbd5e1", fontSize: "0.8em" }}>{mod.chart_title}</h5>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={mod.chart_data}>
                            <XAxis dataKey="isim" stroke="#cbd5e1" fontSize={11} interval={0} />
                            <Tooltip contentStyle={{ backgroundColor: "#334155", color: "#fff", border: "none", borderRadius: "4px" }}/>
                            <Bar dataKey="deger" fill={mod.renk} radius={[3, 3, 0, 0]} barSize={40} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}

export default App;