import streamlit as st
import random
import json
import os
import io
from PIL import Image, ImageDraw, ImageOps

# Importações Modulares de todas as Famílias e Utilitários
from familias import aeral, cristalina, glacial, sanguinea, sepulcral, metalica, comuns_grid, telurica, estelar, solar, lunar, ignea, marinha, gravitacional

st.set_page_config(page_title="Omni-Forja de Caelion", layout="wide")
st.title("A Omni-Forja: Motor de Geração Rúnica")

# ==========================================
# 1. FUNÇÕES DE EXPORTAÇÃO E PIXEL ART
# ==========================================
def image_to_bytes(img):
    """Converte uma imagem PIL para bytes de forma a ser descarregada no Streamlit."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def converter_pixel_art(img_transparente, targ_w, targ_h, threshold=25):
    """
    Comprime a imagem para dimensões minúsculas e força a opacidade (sem anti-aliasing)
    para manter a fidelidade dos traços em formato Pixel Art para o Minecraft.
    """
    img_resized = img_transparente.resize((targ_w, targ_h), Image.Resampling.BOX)
    pixels = img_resized.load()
    
    for y in range(targ_h):
        for x in range(targ_w):
            r, g, b, a = pixels[x, y]
            if a > threshold:
                pixels[x, y] = (r, g, b, 255)
            else:
                pixels[x, y] = (0, 0, 0, 0)
                
    return img_resized


# ==========================================
# 2. O GRIMÓRIO (Carregado Externamente)
# ==========================================
ARQUIVO_PRESETS = "presets.json"

def carregar_grimorio():
    if os.path.exists(ARQUIVO_PRESETS):
        try:
            with open(ARQUIVO_PRESETS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.sidebar.error(f"Erro ao ler {ARQUIVO_PRESETS}: {e}")
            return {}
    else:
        st.sidebar.warning(f"Arquivo '{ARQUIVO_PRESETS}' não encontrado.")
        return {}

PRESETS_SALVOS = carregar_grimorio()

# ==========================================
# 3. CONTROLES E IMPORTAÇÃO (Sidebar)
# ==========================================
st.sidebar.header("Central de Comando")
modo = st.sidebar.radio("Modo de Operação", ["1. Criar Manualmente", "2. Usar Grimório (Arquivo Externo)"])

st.sidebar.markdown("---")
seed = st.sidebar.number_input("Semente de Geração (Seed)", value=777)
random.seed(seed)

preset = {}

if modo == "1. Criar Manualmente":
    with st.sidebar.expander("1. Estrutura e Estilo Geral"):
        p_simetria_v = st.slider("Simetria Vertical (%)", 0, 100, 0) / 100.0
        p_simetria_h = st.slider("Simetria Horizontal (%)", 0, 100, 0) / 100.0
        cor_runa = st.color_picker("Cor da Runa", "#FFFFFF")
        espessura_linha = st.slider("Espessura", 2, 15, 6)

    with st.sidebar.expander("2. Módulos Comuns"):
        ativa_comuns = st.checkbox("Ativar Módulos Comuns")
        if ativa_comuns:
            p_haste = st.slider("Chance de Eixo", 0, 100, 0) / 100.0
            p_anel = st.slider("Chance de Forma Fechada", 0, 100, 0) / 100.0
            p_arco = st.slider("Chance de Arco", 0, 100, 0) / 100.0
            p_ramos = st.slider("Chance de Ramos", 0, 100, 0) / 100.0
            max_flutuantes = st.slider("Max Flutuantes", 0, 10, 0)
            p_curvas = st.slider("Traços Curvos nos Comuns (%)", 0, 100, 0) / 100.0
        else: p_haste = p_anel = p_arco = p_ramos = p_curvas = 0.0; max_flutuantes = 0

    with st.sidebar.expander("3. Metálica / Sepulcral / Sanguínea"):
        ativa_met = st.checkbox("⚙️ Ativar Metálica")
        if ativa_met:
            p_tri = st.slider("Triângulo Inscrito (%)", 0, 100, 0) / 100.0
            p_enc = st.slider("Enclausuramento (%)", 0, 100, 0) / 100.0
            p_sec = st.slider("Secantes Paralelas (%)", 0, 100, 0) / 100.0
            p_nuc = st.slider("Núcleo Inscrito (%)", 0, 100, 0) / 100.0
            p_anc = st.slider("Ancoragem de Vértice (%)", 0, 100, 0) / 100.0
        else: p_tri = p_enc = p_sec = p_nuc = p_anc = 0.0
        st.markdown("---")
        ativa_sep = st.checkbox("💀 Ativar Sepulcral")
        if ativa_sep:
            p_espinhal = st.slider("Eixo Espinhal (%)", 0, 100, 0) / 100.0
            p_cruz = st.slider("Terminações em Cruz (%)", 0, 100, 0) / 100.0
            p_eco = st.slider("Arcos Ecoantes (%)", 0, 100, 0) / 100.0
        else: p_espinhal = p_cruz = p_eco = 0.0
        st.markdown("---")
        ativa_sang = st.checkbox("🩸 Ativar Sanguínea")
        if ativa_sang:
            p_estrela = st.slider("Estrela Catedral (%)", 0, 100, 0) / 100.0
            p_olho = st.slider("Olho Vital (%)", 0, 100, 0) / 100.0
            p_punhal = st.slider("Ponta de Punhal (%)", 0, 100, 0) / 100.0
            p_espinhos = st.slider("Espinhos / Capilares (%)", 0, 100, 0) / 100.0
        else: p_estrela = p_olho = p_punhal = p_espinhos = 0.0
        
    with st.sidebar.expander("4. Feitiçaria Glacial"):
        ativa_glacial = st.checkbox("❄️ Ativar Glacial (Grid Base)")
        if ativa_glacial:
            p_g_mastro = st.slider("Mastro Glacial (%)", 0, 100, 100) / 100.0
            p_g_mastros_duplos = st.slider("Mastros Duplos (%)", 0, 100, 40) / 100.0
            p_g_ramos = st.slider("Ramos Diagonais (%)", 0, 100, 80) / 100.0
            p_g_ramos_longos = st.slider("Ramos Longos (%)", 0, 100, 50) / 100.0
            p_g_duplos = st.slider("Galhos Duplos (Setas) (%)", 0, 100, 50) / 100.0
            p_g_losangos = st.slider("Losangos Inscritos (%)", 0, 100, 50) / 100.0
            p_g_cristais = st.slider("Cristais de Gelo (%)", 0, 100, 40) / 100.0
        else: p_g_mastro = p_g_mastros_duplos = p_g_ramos = p_g_ramos_longos = p_g_duplos = p_g_losangos = p_g_cristais = 0.0

    with st.sidebar.expander("5. Feitiçaria Aeral"):
        ativa_aeral = st.checkbox("🌪️ Ativar Aeral (Caligrafia)")
        if ativa_aeral:
            p_a_fluxo = st.slider("Esqueleto Conectado (Shodo) (%)", 0, 100, 100) / 100.0
            p_a_espiral = st.slider("Redemoinhos Soltos (%)", 0, 100, 40) / 100.0
            p_a_lamina = st.slider("Lâmina de Vento (%)", 0, 100, 50) / 100.0
            p_a_pontilhados = st.slider("Rastro de Ar (Pontilhados) (%)", 0, 100, 60) / 100.0
        else: p_a_fluxo = p_a_espiral = p_a_lamina = p_a_pontilhados = 0.0

    with st.sidebar.expander("6. Feitiçaria Cristalina"):
        ativa_cristalina = st.checkbox("💎 Ativar Cristalina")
        if ativa_cristalina:
            p_c_anel_base = st.slider("Anel de Contenção (Prisma) (%)", 0, 100, 100) / 100.0
            p_c_poligono = st.slider("Polígonos Inscritos (%)", 0, 100, 90) / 100.0
            p_c_diagonais = st.slider("Diagonais de Cristalização (%)", 0, 100, 80) / 100.0
            p_c_caleidoscopio = st.slider("Caleidoscópio (Camadas Internas) (%)", 0, 100, 70) / 100.0
            p_c_ressonancia = st.slider("Nós de Ressonância (Pontos) (%)", 0, 100, 80) / 100.0
        else: p_c_anel_base = p_c_poligono = p_c_diagonais = p_c_caleidoscopio = p_c_ressonancia = 0.0

    with st.sidebar.expander("7. Feitiçaria Telúrica"):
        ativa_telurica = st.checkbox("⛰️ Ativar Telúrica (Arquitetura)")
        if ativa_telurica:
            p_t_ortogonal = st.slider("Densidade Ortogonal (Labirinto) (%)", 0, 100, 70) / 100.0
            p_t_diagonais = st.slider("Fendas Diagonais (%)", 0, 100, 20) / 100.0
            p_t_blocos = st.slider("Preenchimento de Rochas (Blocos Sólidos) (%)", 0, 100, 50) / 100.0
        else: p_t_ortogonal = p_t_diagonais = p_t_blocos = 0.0

    with st.sidebar.expander("8. Feitiçaria Estelar"):
        ativa_estelar = st.checkbox("✨ Ativar Estelar (Constelações)")
        if ativa_estelar:
            p_e_constelacao = st.slider("Malha de Constelações (%)", 0, 100, 90) / 100.0
            p_e_estrelas = st.slider("Nós Estelares (Pontos) (%)", 0, 100, 100) / 100.0
            p_e_orbitas = st.slider("Arcos Orbitais (%)", 0, 100, 60) / 100.0
            p_e_eixo = st.slider("Eixo Astral (Criptografia) (%)", 0, 100, 70) / 100.0
        else: p_e_constelacao = p_e_estrelas = p_e_orbitas = p_e_eixo = 0.0

    with st.sidebar.expander("9. Feitiçaria Solar"):
        ativa_solar = st.checkbox("☀️ Ativar Solar (Ordem e Iluminação)")
        if ativa_solar:
            p_s_foco = st.slider("Núcleo Radiante (Foco) (%)", 0, 100, 80) / 100.0
            p_s_irradiacao = st.slider("Irradiação (Eixos) (%)", 0, 100, 70) / 100.0
            p_s_coroa = st.slider("Coroa Solar (Semicírculos) (%)", 0, 100, 90) / 100.0
            p_s_eclipse = st.slider("Eclipse (Anel Negro) (%)", 0, 100, 30) / 100.0
        else: p_s_foco = p_s_irradiacao = p_s_coroa = p_s_eclipse = 0.0

    with st.sidebar.expander("10. Feitiçaria Lunar"):
        ativa_lunar = st.checkbox("🌙 Ativar Lunar (Reflexão e Caligrafia)")
        if ativa_lunar:
            p_l_caligrafia = st.slider("Caligrafia Fluida (Laços e 'S') (%)", 0, 100, 82) / 100.0
            p_l_fases = st.slider("Fases da Lua (Arcos Crescentes) (%)", 0, 100, 88) / 100.0
            p_l_orbitas = st.slider("Órbitas e Eclipses (%)", 0, 100, 62) / 100.0
            p_l_auxiliares = st.slider("Traços Auxiliares e Pontos (%)", 0, 100, 72) / 100.0
            p_l_hastes = st.slider("Hastes e Travessões (%)", 0, 100, 58) / 100.0
            p_l_internos = st.slider("Arcos Internos Aninhados (%)", 0, 100, 62) / 100.0
        else: p_l_caligrafia = p_l_fases = p_l_orbitas = p_l_auxiliares = p_l_hastes = p_l_internos = 0.0

    with st.sidebar.expander("11. Feitiçaria Ígnea"):
        ativa_ignea = st.checkbox("🔥 Ativar Ígnea (Transformação)")
        if ativa_ignea:
            p_i_rug = st.slider("Rugosidade (Borda Queimada) (%)", 0, 100, 60) / 100.0
            p_i_fenix = st.slider("Fênix (Lâminas Cruzadas) (%)", 0, 100, 40) / 100.0
            p_i_chama = st.slider("Chama Viva (Base em Cuia) (%)", 0, 100, 30) / 100.0
            p_i_catalise = st.slider("Catálise (Explosão Radial) (%)", 0, 100, 20) / 100.0
            p_i_brasa = st.slider("Brasa (Traços Pesados e Lentos) (%)", 0, 100, 20) / 100.0
            p_i_reig = st.slider("Reignição (Lâmina Partida) (%)", 0, 100, 30) / 100.0
            p_i_cruz = st.slider("Cruzamentos Cortantes (%)", 0, 100, 60) / 100.0
            p_i_lab = st.slider("Labaredas (Ganchos de Fogo) (%)", 0, 100, 70) / 100.0
            p_i_fag = st.slider("Fagulhas e Centelhas (%)", 0, 100, 80) / 100.0
        else: p_i_rug = p_i_fenix = p_i_chama = p_i_catalise = p_i_brasa = p_i_reig = p_i_cruz = p_i_lab = p_i_fag = 0.0

    with st.sidebar.expander("12. Feitiçaria Marinha"):
        ativa_marinha = st.checkbox("🌊 Ativar Marinha (Fluade-Mare)")
        if ativa_marinha:
            p_m_corrente = st.slider("Ondulação do Rio (%)", 0, 100, 70) / 100.0
            p_m_lacos = st.slider("Laços Cursivos (%)", 0, 100, 50) / 100.0
            p_m_ondas = st.slider("Ondas e Esteiras de Tinta (%)", 0, 100, 70) / 100.0
            p_m_respingos = st.slider("Respingos (Gotas) (%)", 0, 100, 60) / 100.0
            p_m_ruptura = st.slider("Contra-Corrente (Ruptura) (%)", 0, 100, 50) / 100.0
            p_m_vertical = st.slider("Eixo Vertical (%)", 0, 100, 25) / 100.0
            cor_onda = st.color_picker("Cor das Ondas (Tinta)", "#3D8BFF")
        else: 
            p_m_corrente = p_m_lacos = p_m_ondas = p_m_respingos = p_m_ruptura = p_m_vertical = 0.0
            cor_onda = "#3D8BFF"
            
    with st.sidebar.expander("13. Feitiçaria Gravitacional"):
        ativa_gravitacional = st.checkbox("🪐 Ativar Gravitacional (Fórmulas de Sisk)")
        if ativa_gravitacional:
            p_gr_complexidade = st.slider("Complexidade Algébrica (Densidade) (%)", 0, 100, 70) / 100.0
        else: p_gr_complexidade = 0.0

    with st.sidebar.expander("14. Sistema de Grid e Texturas"):
        grid_tamanho = st.slider("Resolução do Grid Matemático", 3, 7, 5)
        ativa_grid_livre = st.checkbox("Desenhar Caminhos de Grid Aleatórios (Clássico)", value=False)
        if ativa_grid_livre: grid_passos = st.slider("Conexões Grid", 2, 15, 6)
        else: grid_passos = 4
        st.markdown("---")
        efeito_italico = st.checkbox("Itálico", value=False)
        efeito_brush = st.checkbox("Textura Brush (Tinta)", value=False)
        efeito_giz = st.checkbox("Textura Giz (Arranhado)", value=False)
        letra_de_mao = st.checkbox("Letra de Mão", value=False)

    preset = {
        "ativas": {
            "comuns": ativa_comuns, "metalica": ativa_met, "sepulcral": ativa_sep, 
            "sanguinea": ativa_sang, "glacial": ativa_glacial, "aeral": ativa_aeral, 
            "cristalina": ativa_cristalina, "telurica": ativa_telurica, "estelar": ativa_estelar, 
            "solar": ativa_solar, "lunar": ativa_lunar, "ignea": ativa_ignea, "marinha": ativa_marinha,
            "gravitacional": ativa_gravitacional, "grid_livre": ativa_grid_livre
        },
        "simetria": {"vertical": p_simetria_v, "horizontal": p_simetria_h},
        "modulos": {"curvas": p_curvas, "haste": p_haste, "anel": p_anel, "arco": p_arco, "ramos": p_ramos, "max_flutuantes": max_flutuantes},
        "metalica": {"triangulo": p_tri, "enclausuramento": p_enc, "secantes": p_sec, "nucleo": p_nuc, "ancoragem": p_anc},
        "sepulcral": {"espinhal": p_espinhal, "cruz": p_cruz, "eco": p_eco},
        "sanguinea": {"estrela": p_estrela, "olho": p_olho, "punhal": p_punhal, "espinhos": p_espinhos},
        "glacial": {"mastro": p_g_mastro, "mastros_duplos": p_g_mastros_duplos, "ramos": p_g_ramos, "ramos_longos": p_g_ramos_longos, "duplos": p_g_duplos, "losangos": p_g_losangos, "cristais": p_g_cristais},
        "aeral": {"fluxo": p_a_fluxo, "espiral": p_a_espiral, "lamina": p_a_lamina, "pontilhados": p_a_pontilhados},
        "cristalina": {"anel_base": p_c_anel_base, "poligono": p_c_poligono, "diagonais": p_c_diagonais, "caleidoscopio": p_c_caleidoscopio, "ressonancia": p_c_ressonancia},
        "telurica": {"ortogonal": p_t_ortogonal, "diagonais": p_t_diagonais, "blocos": p_t_blocos},
        "estelar": {"constelacao": p_e_constelacao, "estrelas": p_e_estrelas, "orbitas": p_e_orbitas, "eixo_astral": p_e_eixo},
        "solar": {"foco": p_s_foco, "irradiacao": p_s_irradiacao, "coroa": p_s_coroa, "eclipse": p_s_eclipse},
        "lunar": {"caligrafia": p_l_caligrafia, "fases": p_l_fases, "orbitas": p_l_orbitas, "auxiliares": p_l_auxiliares, "hastes": p_l_hastes, "arcos_internos": p_l_internos},
        "ignea": {"rugosidade": p_i_rug, "fenix": p_i_fenix, "chama": p_i_chama, "catalise": p_i_catalise, "brasa": p_i_brasa, "reignicao": p_i_reig, "cruzamentos": p_i_cruz, "labaredas": p_i_lab, "fagulhas": p_i_fag},
        "marinha": {"corrente": p_m_corrente, "lacos": p_m_lacos, "ondas": p_m_ondas, "respingos": p_m_respingos, "ruptura": p_m_ruptura, "vertical": p_m_vertical, "cor_onda": cor_onda},
        "gravitacional": {"complexidade": p_gr_complexidade},
        "grid": {"tamanho": grid_tamanho, "passos": grid_passos},
        "estilo": {"italico": efeito_italico, "brush": efeito_brush, "giz": efeito_giz, "letra_de_mao": letra_de_mao},
        "espessura": espessura_linha,
        "cor": cor_runa
    }
    st.sidebar.markdown(f"### Copie este JSON:")
    st.sidebar.code(json.dumps({ "Nova Família": preset }, indent=4), language="json")

else:
    if PRESETS_SALVOS:
        escolha = st.sidebar.selectbox("Escolha a Família do Grimório Externo", list(PRESETS_SALVOS.keys()))
        preset = PRESETS_SALVOS[escolha]
        st.sidebar.markdown(f"### Lendo de `{ARQUIVO_PRESETS}`:")
        st.sidebar.code(json.dumps(preset, indent=4), language="json")
    else:
        st.sidebar.error("Grimório Vazio.")

# ==========================================
# 4. COMPILADOR CENTRAL DE RUNAS
# ==========================================
def desenhar_runa(config):
    tamanho = 400
    cx, cy = tamanho // 2, tamanho // 2
    esp = config.get("espessura", 6)
    estilo = config.get("estilo", {})
    cor = config.get("cor", "white")
    
    ativas = config.get("ativas", {})
    is_comuns = ativas.get("comuns", False)
    is_met = ativas.get("metalica", False)
    is_sep = ativas.get("sepulcral", False)
    is_sang = ativas.get("sanguinea", False)
    is_crist = ativas.get("cristalina", False)
    is_aeral = ativas.get("aeral", False)
    is_glacial = ativas.get("glacial", False)
    is_telurica = ativas.get("telurica", False)
    is_estelar = ativas.get("estelar", False)
    is_solar = ativas.get("solar", False)
    is_lunar = ativas.get("lunar", False)
    is_ignea = ativas.get("ignea", False)
    is_marinha = ativas.get("marinha", False)
    is_gravitacional = ativas.get("gravitacional", False)
    is_grid = ativas.get("grid_livre", False)

    grid_cfg = config.get("grid", {})
    n = grid_cfg.get("tamanho", 5)
    passos = grid_cfg.get("passos", 4)
    margem = 100
    step = (tamanho - (margem * 2)) / max(1, n - 1)
    
    base = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    usa_curvas = random.random() < config.get("modulos", {}).get("curvas", 0)

    # Invoca as Famílias Modulares 
    if is_comuns: comuns_grid.aplicar_comuns(draw, config, cx, cy, cor, esp, estilo, usa_curvas)
    if is_met: metalica.aplicar(draw, config, cx, cy, cor, esp, estilo)
    if is_sep: sepulcral.aplicar(draw, config, cx, cy, cor, esp, estilo)
    if is_sang: sanguinea.aplicar(draw, config, cx, cy, cor, esp, estilo)
    if is_crist: cristalina.aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_aeral: aeral.aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_glacial: glacial.aplicar(draw, config, n, step, margem, cor, esp, estilo)
    if is_telurica: telurica.aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_estelar: estelar.aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_solar: solar.aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_lunar: lunar.aplicar(draw, config, cx, cy, cor, esp, estilo)
    if is_ignea: ignea.aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_marinha: marinha.aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_gravitacional: gravitacional.aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_grid: comuns_grid.aplicar_grid_livre(draw, config, n, passos, step, margem, cor, esp, estilo)

    # Curadoria Final (Simetria e Transformações)
    img_final = base.copy()
    if random.random() < config.get("simetria", {}).get("vertical", 0): img_final.alpha_composite(ImageOps.mirror(img_final))
    if random.random() < config.get("simetria", {}).get("horizontal", 0): img_final.alpha_composite(ImageOps.flip(img_final))
    if config.get("estilo", {}).get("italico", False):
        matriz = (1, 0.3, -0.3 * cy, 0, 1, 0)
        img_final = img_final.transform(img_final.size, Image.AFFINE, matriz, resample=Image.BICUBIC)

    # Imagem Final com fundo escuro (Apenas para visualização no Streamlit)
    fundo = Image.new("RGBA", (tamanho, tamanho), (15, 15, 15, 255))
    fundo.alpha_composite(img_final)
    
    return fundo, img_final

# ==========================================
# 5. EXIBIÇÃO E EXPORTAÇÃO NO STREAMLIT
# ==========================================
st.markdown("### Amostras da Família Carregada")

if preset:
    cols = st.columns(4)
    for i in range(8):
        random.seed(seed + i)
        
        img_display, img_transp = desenhar_runa(preset)
        col = cols[i % 4]
        
        col.image(img_display, caption=f"Runa #{seed+i}", use_column_width=True)
        
        with col.expander("📥 Opções de Exportação"):
            # Permite definir um nome customizado, default é "runa_ID"
            nome_customizado = st.text_input("Nome da Runa:", value=f"runa_{seed+i}", key=f"nome_{seed+i}")
            nome_base = nome_customizado.strip() if nome_customizado.strip() else f"runa_{seed+i}"
            
            st.download_button(
                label="📁 Normal (400x400)", 
                data=image_to_bytes(img_transp), 
                file_name=f"{nome_base}_normal.png", 
                mime="image/png",
                use_container_width=True
            )
            
            img_carta = converter_pixel_art(img_transp, 39, 41)
            st.download_button(
                label="🎴 Carta (39x41)", 
                data=image_to_bytes(img_carta), 
                file_name=f"{nome_base}_carta.png", 
                mime="image/png",
                use_container_width=True
            )
            
            img_mini = converter_pixel_art(img_transp, 18, 18)
            st.download_button(
                label="🤏 Miniatura (18x18)", 
                data=image_to_bytes(img_mini), 
                file_name=f"{nome_base}_mini.png", 
                mime="image/png",
                use_container_width=True
            )
else:
    st.info("O Grimório está vazio ou a configuração atual falhou a carregar.")

random.seed(seed)