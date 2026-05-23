import numpy as np
import matplotlib.pyplot as plt
import random
import streamlit as st
import time

# --- Konfigurasi Halaman Web ---
st.set_page_config(page_title="Simulasi Efek Fotolistrik", layout="wide")

# --- Variabel Global ---
if 'light_on' not in st.session_state:
    st.session_state.light_on = False
if 'electrons' not in st.session_state:
    st.session_state.electrons = []
if 'current_val' not in st.session_state:
    st.session_state.current_val = 0.0
if 'page' not in st.session_state:
    st.session_state.page = 'welcome'

# Konstanta Fisik (Sederhana untuk Simulasi)
H_PLANCK = 4.1357e-15  # eV.s
C_LIGHT = 3e8          # m/s
WORK_FUNCTION = 1.9    # eV (Contoh: Logam Alkali)
THRESHOLD_F = (WORK_FUNCTION / H_PLANCK) / 1e14 # dalam satuan 10^14 Hz

# Data Filter Praktikum
FILTER_DATA = {
    'Merah':  {'lambda': 5769.59, 'color': 'red'},
    'Kuning': {'lambda': 5460.74, 'color': 'yellow'},
    'Hijau':  {'lambda': 4347.50, 'color': 'green'}
}
current_filter_name = 'Merah'

def toggle_light():
    st.session_state.light_on = not st.session_state.light_on

def reset_simulasi():
    st.session_state.electrons = []
    st.session_state.current_val = 0.0

def jalankan_simulasi_web():
    st.title("Simulasi Efek Fotolistrik - Kelompok 2")
    
    # --- Sidebar Kontrol ---
    st.sidebar.header("Kontrol Eksperimen")
    filter_pilihan = st.sidebar.selectbox("Pilih Filter Warna", list(FILTER_DATA.keys()))
    
    lam = FILTER_DATA[filter_pilihan]['lambda']
    freq_default = (C_LIGHT / (lam * 1e-10)) / 1e14
    
    s_freq = st.sidebar.slider("Frekuensi (10^14 Hz)", 0.0, 10.0, freq_default)
    s_int = st.sidebar.slider("Intensitas Cahaya", 0.0, 1.0, 0.5)
    s_vs = st.sidebar.slider("Tegangan Henti / Vs (Volt)", -2.0, 8.0, 0.0)
    
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Nyalakan/Matikan Cahaya"):
        toggle_light()
    if col2.button("Keluar"):
        st.session_state.page = 'closing'
        st.rerun()

    # --- Pengaturan Tampilan & Estetika ---
    plt.style.use('dark_background')
    fig, (ax, ax_graph) = plt.subplots(1, 2, figsize=(15, 6))

    # Batas koordinat simulasi
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.set_aspect('equal')
    ax.axis('off')

    # --- Menggambar Komponen Statis ---
    txt_stats = ax.text(0.5, 5.2, "", color='white', fontsize=10, fontweight='bold', bbox=dict(facecolor='black', alpha=0.5))

    # 1. Tabung Vakum
    vacuum_tube = plt.Rectangle((3, 1.5), 5, 3, edgecolor='white', fill=False, lw=2, alpha=0.5)
    ax.add_patch(vacuum_tube)
    ax.text(5.5, 4.7, "Tabung Vakum", color='white', ha='center', fontsize=10, style='italic')

    # 2. Elektroda (Katoda dan Anoda)
    cathode = plt.Rectangle((3.2, 2), 0.2, 2, color='silver')
    anode = plt.Rectangle((7.6, 2), 0.2, 2, color='gold')
    ax.add_patch(cathode)
    ax.add_patch(anode)
    ax.text(3.3, 4.1, "Katoda", color='silver', ha='center', fontweight='bold')
    ax.text(7.7, 4.1, "Anoda", color='gold', ha='center', fontweight='bold')

    # 3. Sumber Cahaya (Lampu)
    light_source = plt.Circle((0.5, 3), 0.4, color='yellow', alpha=0.8)
    ax.add_patch(light_source)
    ax.text(0.5, 2.3, "Sumber Cahaya", color='yellow', ha='center')

    # 4. Filter Cahaya
    light_filter = plt.Rectangle((1.8, 2), 0.15, 2, color='red', alpha=0.6)
    ax.add_patch(light_filter)
    ax.text(1.87, 4.1, "Filter", color='cyan', ha='center')

    # 5. Amperemeter (Dial)
    ammeter_bg = plt.Circle((5.5, 0.5), 0.6, color='white', alpha=0.2)
    ax.add_patch(ammeter_bg)
    ax.text(5.5, 0.5, "A", color='white', fontsize=20, ha='center', va='center', fontweight='bold')
    needle, = ax.plot([], [], color='red', lw=2)
    ax.text(5.5, -0.2, "Amperemeter", color='white', ha='center')

    # 6. Kabel Penghubung
    ax.plot([3.3, 3.3, 5.5], [2, 0.5, 0.5], color='white', lw=1, alpha=0.5)
    ax.plot([7.7, 7.7, 5.5], [2, 0.5, 0.5], color='white', lw=1, alpha=0.5)

    # 7. Sinar Cahaya
    light_rays, = ax.plot([], [], color='yellow', lw=1, alpha=0.3)
    electron_particles = ax.scatter([], [], color='cyan', s=20, edgecolors='white')

    # --- Konfigurasi Grafik Vs vs f ---
    ax_graph.set_xlim(0, 10)
    ax_graph.set_ylim(0, 6)
    ax_graph.set_xlabel('Frekuensi (f)', color='white')
    ax_graph.set_ylabel('Potensial Henti (Vs)', color='white')
    ax_graph.set_title('Grafik Potensial Henti vs Frekuensi', color='cyan', fontsize=12)
    ax_graph.grid(True, alpha=0.2)
    ax_graph.plot([0, THRESHOLD_F, 10], [0, 0, (10 * H_PLANCK * 1e14 - WORK_FUNCTION)], color='cyan', linestyle='--', alpha=0.6)
    vs_point, = ax_graph.plot([], [], 'ro', markersize=8, label='Titik Kerja')
    
    # Placeholder untuk animasi
    sim_plot = st.empty()
    
    # --- Loop Animasi Manual (Streamlit) ---
    while st.session_state.page == 'sim':
        f_hz = s_freq * 1e14
        energy_photon = H_PLANCK * f_hz
        vs_theoretical = max(0, energy_photon - WORK_FUNCTION)
        current_lambda = (C_LIGHT / f_hz) * 1e10 if f_hz > 0 else 0
        
        # Logika Filter
        if s_freq < 5.3: color = 'red'
        elif s_freq < 6.0: color = 'yellow'
        else: color = 'green'
        light_passes = (color == FILTER_DATA[filter_pilihan]['color'])
        light_filter.set_color(FILTER_DATA[filter_pilihan]['color'])

        electrons_reaching_anode = 0
        if st.session_state.light_on:
            light_source.set_color(color)
            if light_passes:
                light_rays.set_data([0.5, 3.2], [3, 3])
                light_rays.set_color(color)
                if energy_photon > WORK_FUNCTION:
                    v0 = 0.03 + 0.06 * np.sqrt(vs_theoretical)
                    if random.random() < s_int:
                        st.session_state.electrons.append([3.4, random.uniform(2.1, 3.9), v0])
            else:
                light_rays.set_data([0.5, 1.8], [3, 3])
        else:
            light_rays.set_data([], [])
            light_source.set_color('yellow')

        # Pergerakan Elektron
        new_electrons = []
        plot_x, plot_y = [], []
        dv = 0.001 * s_vs
        
        for e in st.session_state.electrons:
            e[2] -= dv
            e[0] += e[2]
            if e[0] >= 7.6:
                electrons_reaching_anode += 1
            elif 3.2 < e[0] < 7.6:
                new_electrons.append(e)
                plot_x.append(e[0])
                plot_y.append(e[1])
        
        st.session_state.electrons = new_electrons
        target_i = s_int if electrons_reaching_anode > 0 else 0.0
        st.session_state.current_val += 0.1 * (target_i - st.session_state.current_val)

        # Update Visual
        vs_point.set_data([s_freq], [vs_theoretical])
        txt_stats.set_text(f"λ: {current_lambda:.2f} Å | f: {s_freq:.2f}x10¹⁴ Hz\nVs Teori: {vs_theoretical:.2f} V")
        angle = np.pi - (st.session_state.current_val * np.pi)
        needle.set_data([5.5, 5.5 + 0.5 * np.cos(angle)], [0.5, 0.5 + 0.5 * np.sin(angle)])
        electron_particles.set_offsets(np.c_[plot_x, plot_y])
        
        sim_plot.pyplot(fig)
        time.sleep(0.05)

if __name__ == "__main__":
    if st.session_state.page == 'welcome':
        st.title("Selamat Datang")
        st.info("Simulasi Efek Fotolistrik oleh Kelompok 2")
        if st.button("Mulai Simulasi"):
            st.session_state.page = 'sim'
            st.rerun()
    elif st.session_state.page == 'sim':
        jalankan_simulasi_web()
    elif st.session_state.page == 'closing':
        st.title("Terima Kasih")
        st.write("Simulasi Selesai.")
        if st.button("Kembali ke Awal"):
            st.session_state.page = 'welcome'
            reset_simulasi()
            st.rerun()
