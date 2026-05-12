import streamlit as st
import math

# --- Configuración de la página ---
st.set_page_config(page_title="Diseño Trafo - TME Grupo 2", layout="wide")
st.title("Calculador Interactivo de Transformador - Grupo 2 (TME)")
st.markdown("Basado en núcleo RM10 (Sin orificio central), Material N30 y carrete de 2 secciones B65814N1008D002.")

# --- Constantes y Materiales ---
MU_0 = 4 * math.pi * 1e-7
MU_R_N30 = 4300 # Permeabilidad inicial típica del N30
B_MAX_LIMIT = 0.100 # 100 mT
RHO_CU = 1.72e-8 # Resistividad del cobre a 20°C (Ohm*m)
KW = 0.3 # Coeficiente de bobinado dado

# Parámetros geométricos típicos RM10 (sin agujero central)
Ae = 98e-6 # m^2 (Área efectiva)
le = 44.6e-3 # m (Longitud magnética efectiva)
Aw_total = 41.5e-6 # m^2 Área de ventana utilizable TOTAL aproximada para RM10 (2 secciones reduce el área útil)
Aw_sec = Aw_total / 2 # Área por sección del carrete

cables_disponibles = [0.6, 0.45, 0.5, 0.3, 0.2] # en mm

# --- Interfaz en Pestañas ---
tab1, tab2, tab3 = st.tabs(["Parámetros del Núcleo", "Diseño de Bobinados", "Cálculos y Equivalentes"])

with tab1:
    st.header("Parámetros del Núcleo y Señal")
    st.markdown("- **Núcleo:** RM10 TDK (Without center hole)\n- **Material:** N30\n- **Bmax admitido:** 100 mT")
    st.metric(label="Área Efectiva (Ae)", value="98 mm²")
    st.metric(label="Longitud Magnética (le)", value="44.6 mm")
    
    st.subheader("Configuración del Gap")
    gap_mm = st.slider("Espesor del Entrehierro (Gap) [mm]", 0.0, 0.4, 0.1, 0.1)
    gap_m = gap_mm * 1e-3
    
    st.subheader("Parámetros del Circuito / Señal")
    col1, col2 = st.columns(2)
    with col1:
        f_hz = st.number_input("Frecuencia de conmutación [Hz]", value=50000, step=1000)
        v_in = st.number_input("Tensión de entrada (Amplitud onda cuadrada) [V]", value=12.0)
    with col2:
        duty = st.slider("Duty Cycle (D)", 0.01, 0.99, 0.50, 0.01)
        i_dc = st.number_input("Corriente DC en el primario [A]", value=1.0)

with tab2:
    st.header("Diseño de Bobinados")
    st.markdown("Recuerda: El primario va en una sección y los secundarios en la otra (Apilados).")
    
    col_p, col_s = st.columns(2)
    with col_p:
        st.subheader("Primario (Sección 1)")
        np = st.number_input("Vueltas (Np)", min_value=1, value=10, step=1)
        dia_p = st.selectbox("Diámetro de cable [mm] (Prim)", cables_disponibles, index=0)
        hilos_p = st.number_input("Hilos en paralelo (Prim)", min_value=1, value=1, step=1)
        
    with col_s:
        st.subheader("Secundario (Sección 2)")
        ns = st.number_input("Vueltas (Ns)", min_value=1, value=10, step=1)
        dia_s = st.selectbox("Diámetro de cable [mm] (Sec)", cables_disponibles, index=1)
        hilos_s = st.number_input("Hilos en paralelo (Sec)", min_value=1, value=1, step=1)

with tab3:
    st.header("Resultados y Verificaciones")
    
    # 1. Cálculos de Reluctancia e Inductancia
    R_nucleo = le / (MU_0 * MU_R_N30 * Ae)
    R_gap = gap_m / (MU_0 * Ae) if gap_m > 0 else 0
    R_total = R_nucleo + R_gap
    
    L_primario = (np**2) / R_total
    
    st.subheader("Magnéticos")
    st.write(f"**Reluctancia Total ($\mathcal{{R}}$):** {R_total:.2e} H⁻¹")
    st.write(f"**Inductancia Primario ($L_m$):** {L_primario*1e6:.2f} µH")
    
    # 2. Efecto Skin
    # Profundidad de penetración en mm = 66 / sqrt(f) para cobre
    skin_depth_mm = 66 / math.sqrt(f_hz)
    st.subheader("Efecto Skin")
    st.write(f"**Profundidad Skin ($\delta$) a {f_hz} Hz:** {skin_depth_mm:.3f} mm")
    
    def check_skin(dia, skin_d, bobinado):
        if dia > 2 * skin_d:
            st.error(f"¡Atención! El cable del {bobinado} ({dia} mm) supera 2$\delta$. Sufrirá fuerte efecto skin. Aumenta los hilos en paralelo y baja el diámetro.")
        elif dia > skin_d:
            st.warning(f"Precaución: El cable del {bobinado} ({dia} mm) es mayor que $\delta$ pero menor que 2$\delta$. Tolerable pero no ideal.")
        else:
            st.success(f"Cable del {bobinado} ({dia} mm) cumple bien con el efecto skin ($\leq \delta$).")

    check_skin(dia_p, skin_depth_mm, "Primario")
    check_skin(dia_s, skin_depth_mm, "Secundario")
    
    # 3. Cálculo de Bmax
    # Bmax = 1/2 * (V*t_on / (N*Ae)) + (N*Idc / (R*Ae))
    t_on = duty / f_hz
    B_ac = (v_in * t_on) / (np * Ae)
    B_ac_peak = B_ac / 2
    
    B_dc = (np * i_dc) / (R_total * Ae)
    B_max_calc = B_ac_peak + B_dc
    
    st.subheader("Flujo Magnético (Verificación de Saturación)")
    st.write(f"**B_AC peak:** {B_ac_peak*1000:.1f} mT")
    st.write(f"**B_DC:** {B_dc*1000:.1f} mT")
    st.write(f"**B_Max Total:** {B_max_calc*1000:.1f} mT")
    
    if B_max_calc > B_MAX_LIMIT:
        st.error(f"¡NÚCLEO SATURADO! Bmax = {B_max_calc*1000:.1f} mT > 100 mT. Aumenta el gap, sube Np, o baja la corriente/tensión.")
    else:
        st.success(f"Núcleo en zona lineal. Bmax = {B_max_calc*1000:.1f} mT $\leq$ 100 mT.")
        
    # 4. Verificación de Ventana (Factor de ocupación)
    area_cobre_p = np * hilos_p * math.pi * ((dia_p/2)**2) * 1e-6
    area_cobre_s = ns * hilos_s * math.pi * ((dia_s/2)**2) * 1e-6
    
    kw_p = area_cobre_p / Aw_sec
    kw_s = area_cobre_s / Aw_sec
    
    st.subheader("Verificación de Carrete (Kw = 0.3)")
    st.write(f"Kw Primario (Sección 1): {kw_p:.3f}")
    st.write(f"Kw Secundario (Sección 2): {kw_s:.3f}")
    
    if kw_p > KW:
        st.error("Primario: No entra en su sección del carrete. (Kw > 0.3)")
    else:
        st.success("Primario: Entra en su sección.")
        
    if kw_s > KW:
        st.error("Secundario: No entra en su sección del carrete. (Kw > 0.3)")
    else:
        st.success("Secundario: Entra en su sección.")
        
    # 5. Parámetros Equivalentes (Estimación básica DC)
    # Longitud media de espira estimada (MLT) para RM10 ~ 42 mm
    MLT = 42e-3 
    R_dc_p = RHO_CU * (np * MLT) / (hilos_p * math.pi * ((dia_p*1e-3/2)**2))
    R_dc_s = RHO_CU * (ns * MLT) / (hilos_s * math.pi * ((dia_s*1e-3/2)**2))
    
    st.subheader("Parámetros del Circuito Equivalente")
    st.write("*(Estimaciones aproximadas)*")
    st.write(f"**$R_{{DC}}$ Primario:** {R_dc_p*1000:.2f} m$\Omega$")
    st.write(f"**$R_{{DC}}$ Secundario:** {R_dc_s*1000:.2f} m$\Omega$")
    st.write(f"**Inductancia Magnetizante ($L_m$):** Referida al primario es la inductancia calculada arriba: {L_primario*1e6:.2f} µH")
    st.info("Nota sobre Inductancia de Dispersión ($L_{leakage}$) y Efecto Proximidad: Al usar un carrete de 2 secciones separando primario y secundario, la inductancia de dispersión será naturalmente ALTA. El efecto proximidad (Resistencia AC) aumentará severamente al usar hilos en paralelo gruesos apilados en lugar de Litz. Considera calcular el factor de Dowell analíticamente si requieres el valor exacto de Rac.")