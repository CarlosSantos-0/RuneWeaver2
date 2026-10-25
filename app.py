import streamlit as st
import random
import json
import os
import io
import math
from PIL import Image, ImageDraw, ImageOps

# Importações Modulares do Motor (Backend mantido intacto)
from familias import aeral, cristalina, glacial, sanguinea, sepulcral, metalica, comuns_grid, telurica, estelar, solar, lunar, ignea, marinha, gravitacional

st.set_page_config(page_title="RuneWeaver", layout="wide")
st.title("RuneWeaver: Gerador Procedural de Runas")

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
    Comprime a imagem para dimensões reduzidas e força a opacidade (sem anti-aliasing)
    para manter a fidelidade dos traços em formato Pixel Art.
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
# 2. MOTOR DE INTERCEÇÃO VETORIAL (JSON)
# ==========================================
class DrawRecorder:
    """
    Intercepta as chamadas de desenho (linhas, polígonos, arcos) para extrair e guardar
    os traços vetoriais exatos (polilinhas) que formam a runa, antes da rasterização.
    """
    def __init__(self, draw_obj):
        self.draw = draw_obj
        self.strokes = []

    def __getattr__(self, attr):
        return getattr(self.draw, attr)

    def _extract_points(self, xy):
        if isinstance(xy, (list, tuple)) and len(xy) > 0:
            if isinstance(xy[0], (int, float)):
                return [[float(xy[i]), float(xy[i+1])] for i in range(0, len(xy), 2)]
            elif isinstance(xy[0], (list, tuple)):
                return [[float(p[0]), float(p[1])] for p in xy]
        return []

    def line(self, xy, *args, **kwargs):
        self.draw.line(xy, *args, **kwargs)
        pts = self._extract_points(xy)
        if len(pts) >= 2:
            self.strokes.append(pts)

    def polygon(self, xy, *args, **kwargs):
        self.draw.polygon(xy, *args, **kwargs)
        pts = self._extract_points(xy)
        if len(pts) > 0:
            pts.append(pts[0])  # Fecha o traço geométrico para as partículas
            self.strokes.append(pts)

    def ellipse(self, xy, *args, **kwargs):
        self.draw.ellipse(xy, *args, **kwargs)
        pts = self._extract_points(xy)
        if len(pts) == 2:
            x0, y0, x1, y1 = pts[0][0], pts[0][1], pts[1][0], pts[1][1]
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            rx, ry = abs(x1 - x0) / 2, abs(y1 - y0) / 2
            # Ignora esferas de articulações minúsculas (<1.5px) para não sobrecarregar o Minecraft
            if rx <= 1.5 and ry <= 1.5:
                return
            
            # Converte a elipse perfeita numa polilinha densa de vértices (fragmentação)
            poly = []
            steps = max(12, int(3.14 * max(rx, ry) / 3))
            for i in range(steps + 1):
                angle = 2 * math.pi * i / steps
                poly.append([cx + rx * math.cos(angle), cy + ry * math.sin(angle)])
            self.strokes.append(poly)

    def arc(self, xy, start, end, *args, **kwargs):
        self.draw.arc(xy, start, end, *args, **kwargs)
        pts = self._extract_points(xy)
        if len(pts) == 2:
            x0, y0, x1, y1 = pts[0][0], pts[0][1], pts[1][0], pts[1][1]
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            rx, ry = abs(x1 - x0) / 2, abs(y1 - y0) / 2
            poly = []
            s_rad = math.radians(start)
            e_rad = math.radians(end)
            if e_rad < s_rad: e_rad += 2 * math.pi
            steps = max(6, int((e_rad - s_rad) * max(rx, ry) / 4))
            for i in range(steps + 1):
                angle = s_rad + (e_rad - s_rad) * i / steps
                poly.append([cx + rx * math.cos(angle), cy + ry * math.sin(angle)])
            self.strokes.append(poly)

def gerar_json_matriz(strokes, tamanho, mirror, flip, italic):
    """
    Aplica as distorções espaciais e normaliza os vértices para 0.0 - 1.0
    de acordo com as regras exatas do Minecraft 3D.
    """
    cy = tamanho / 2
    transformed = []
    
    for traco in strokes:
        new_traco = []
        for x, y in traco:
            nx, ny = x, y
            # 1. Aplica o processamento espacial escolhido
            if mirror:
                nx = tamanho - nx
            if flip:
                ny = tamanho - ny
            if italic:
                # O inverso matemático exato da matriz PIL afim (1, 0.3, -0.3*cy)
                nx = nx - 0.3 * ny + 0.3 * cy
                
            # 2. Normalização global (0 a 1) para a área da tela
            u = round(nx / tamanho, 4)
            v = round(ny / tamanho, 4)
            new_traco.append([u, v])
            
        if len(new_traco) >= 2:
            transformed.append(new_traco)
            
    return json.dumps({"strokes": transformed}, separators=(',', ':'))

# ==========================================
# 3. GESTÃO DE PRESETS (ARQUIVO EXTERNO)
# ==========================================
ARQUIVO_PRESETS = "presets.json"

def carregar_presets():
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

PRESETS_SALVOS = carregar_presets()

# ==========================================
# 4. PAINEL DE CONTROLE (Sidebar)
# ==========================================
st.sidebar.header("Painel de Controle")
modo = st.sidebar.radio("Modo de Operação", ["1. Criação Manual", "2. Carregar de Arquivo (Presets)"])

st.sidebar.markdown("---")
seed = st.sidebar.number_input("Seed de Geração", value=777)
random.seed(seed)

preset = {}

if modo == "1. Criação Manual":
    with st.sidebar.expander("1. Parâmetros Globais"):
        p_simetria_v = st.slider("Simetria Vertical (%)", 0, 100, 0) / 100.0
        p_simetria_h = st.slider("Simetria Horizontal (%)", 0, 100, 0) / 100.0
        cor_runa = st.color_picker("Cor Base", "#FFFFFF")
        espessura_linha = st.slider("Espessura do Traço", 2, 15, 6)

    with st.sidebar.expander("2. Módulos Comuns"):
        ativa_comuns = st.checkbox("Ativar Módulos Comuns")
        if ativa_comuns:
            p_haste = st.slider("Probabilidade de Eixo", 0, 100, 0) / 100.0
            p_anel = st.slider("Probabilidade de Forma Fechada", 0, 100, 0) / 100.0
            p_arco = st.slider("Probabilidade de Arco", 0, 100, 0) / 100.0
            p_ramos = st.slider("Probabilidade de Ramos", 0, 100, 0) / 100.0
            max_flutuantes = st.slider("Máximo de Flutuantes", 0, 10, 0)
            p_curvas = st.slider("Traços Curvos nos Comuns (%)", 0, 100, 0) / 100.0
        else: p_haste = p_anel = p_arco = p_ramos = p_curvas = 0.0; max_flutuantes = 0

    with st.sidebar.expander("3. Estilos Estruturais Básicos"):
        ativa_met = st.checkbox("Família Ironclad (Geometria Industrial)")
        if ativa_met:
            p_tri = st.slider("Triângulo Inscrito (%)", 0, 100, 0) / 100.0
            p_enc = st.slider("Enclausuramento (%)", 0, 100, 0) / 100.0
            p_sec = st.slider("Secantes Paralelas (%)", 0, 100, 0) / 100.0
            p_nuc = st.slider("Núcleo Inscrito (%)", 0, 100, 0) / 100.0
            p_anc = st.slider("Ancoragem de Vértice (%)", 0, 100, 0) / 100.0
        else: p_tri = p_enc = p_sec = p_nuc = p_anc = 0.0
        st.markdown("---")
        ativa_sep = st.checkbox("Família Ossa (Eixos e Interseções)")
        if ativa_sep:
            p_espinhal = st.slider("Eixo Principal (%)", 0, 100, 0) / 100.0
            p_cruz = st.slider("Terminações Cruzadas (%)", 0, 100, 0) / 100.0
            p_eco = st.slider("Arcos Concêntricos (%)", 0, 100, 0) / 100.0
        else: p_espinhal = p_cruz = p_eco = 0.0
        st.markdown("---")
        ativa_sang = st.checkbox("Família Cruor (Radial Orgânico)")
        if ativa_sang:
            p_estrela = st.slider("Padrão Catedral (%)", 0, 100, 0) / 100.0
            p_olho = st.slider("Núcleo Ocular (%)", 0, 100, 0) / 100.0
            p_punhal = st.slider("Ponta Afilada (%)", 0, 100, 0) / 100.0
            p_espinhos = st.slider("Ramificações Finas (%)", 0, 100, 0) / 100.0
        else: p_estrela = p_olho = p_punhal = p_espinhos = 0.0
        
    with st.sidebar.expander("4. Família Dendrítica"):
        ativa_glacial = st.checkbox("Ativar Família Dendrítica (Base em Grid)")
        if ativa_glacial:
            p_g_mastro = st.slider("Haste Principal (%)", 0, 100, 100) / 100.0
            p_g_mastros_duplos = st.slider("Hastes Duplas (%)", 0, 100, 40) / 100.0
            p_g_ramos = st.slider("Ramos Diagonais (%)", 0, 100, 80) / 100.0
            p_g_ramos_longos = st.slider("Ramos Longos (%)", 0, 100, 50) / 100.0
            p_g_duplos = st.slider("Sub-ramos (Setas) (%)", 0, 100, 50) / 100.0
            p_g_losangos = st.slider("Losangos Inscritos (%)", 0, 100, 50) / 100.0
            p_g_cristais = st.slider("Terminações Geométricas (%)", 0, 100, 40) / 100.0
        else: p_g_mastro = p_g_mastros_duplos = p_g_ramos = p_g_ramos_longos = p_g_duplos = p_g_losangos = p_g_cristais = 0.0

    with st.sidebar.expander("5. Família Zephyr"):
        ativa_aeral = st.checkbox("Ativar Família Zephyr (Fluxo Contínuo)")
        if ativa_aeral:
            p_a_fluxo = st.slider("Esqueleto Conectado (%)", 0, 100, 100) / 100.0
            p_a_espiral = st.slider("Terminações em Espiral (%)", 0, 100, 40) / 100.0
            p_a_lamina = st.slider("Curvas Acentuadas (%)", 0, 100, 50) / 100.0
            p_a_pontilhados = st.slider("Rastro (Pontilhados) (%)", 0, 100, 60) / 100.0
        else: p_a_fluxo = p_a_espiral = p_a_lamina = p_a_pontilhados = 0.0

    with st.sidebar.expander("6. Família Prisma"):
        ativa_cristalina = st.checkbox("Ativar Família Prisma (Cristais e Polígonos)")
        if ativa_cristalina:
            p_c_anel_base = st.slider("Polígono Envolvente (%)", 0, 100, 100) / 100.0
            p_c_poligono = st.slider("Polígonos Inscritos (%)", 0, 100, 90) / 100.0
            p_c_diagonais = st.slider("Diagonais Estruturais (%)", 0, 100, 80) / 100.0
            p_c_caleidoscopio = st.slider("Camadas Internas (%)", 0, 100, 70) / 100.0
            p_c_ressonancia = st.slider("Nós (Pontos) (%)", 0, 100, 80) / 100.0
        else: p_c_anel_base = p_c_poligono = p_c_diagonais = p_c_caleidoscopio = p_c_ressonancia = 0.0

    with st.sidebar.expander("7. Família Tectônica"):
        ativa_telurica = st.checkbox("Ativar Família Tectônica (Ortogonal/Labiríntica)")
        if ativa_telurica:
            p_t_ortogonal = st.slider("Densidade Ortogonal (%)", 0, 100, 70) / 100.0
            p_t_diagonais = st.slider("Fendas Diagonais (%)", 0, 100, 20) / 100.0
            p_t_blocos = st.slider("Preenchimento de Blocos Sólidos (%)", 0, 100, 50) / 100.0
        else: p_t_ortogonal = p_t_diagonais = p_t_blocos = 0.0

    with st.sidebar.expander("8. Família Astral"):
        ativa_estelar = st.checkbox("Ativar Família Astral (Redes Nodais)")
        if ativa_estelar:
            p_e_constelacao = st.slider("Malha Conectiva (%)", 0, 100, 90) / 100.0
            p_e_estrelas = st.slider("Nós de Conexão (Pontos) (%)", 0, 100, 100) / 100.0
            p_e_orbitas = st.slider("Arcos Orbitais (%)", 0, 100, 60) / 100.0
            p_e_eixo = st.slider("Eixo Estrutural (%)", 0, 100, 70) / 100.0
        else: p_e_constelacao = p_e_estrelas = p_e_orbitas = p_e_eixo = 0.0

    with st.sidebar.expander("9. Família Corona"):
        ativa_solar = st.checkbox("Ativar Família Corona (Radiante)")
        if ativa_solar:
            p_s_foco = st.slider("Núcleo Focal (%)", 0, 100, 80) / 100.0
            p_s_irradiacao = st.slider("Irradiação (Eixos) (%)", 0, 100, 70) / 100.0
            p_s_coroa = st.slider("Arcos Semicirculares (%)", 0, 100, 90) / 100.0
            p_s_eclipse = st.slider("Anel Exterior (%)", 0, 100, 30) / 100.0
        else: p_s_foco = p_s_irradiacao = p_s_coroa = p_s_eclipse = 0.0

    with st.sidebar.expander("10. Família Crescent"):
        ativa_lunar = st.checkbox("Ativar Família Crescent (Caligráfica)")
        if ativa_lunar:
            p_l_caligrafia = st.slider("Traços Fluidos (%)", 0, 100, 82) / 100.0
            p_l_fases = st.slider("Arcos Crescentes (%)", 0, 100, 88) / 100.0
            p_l_orbitas = st.slider("Círculos Orbitais (%)", 0, 100, 62) / 100.0
            p_l_auxiliares = st.slider("Traços Auxiliares (%)", 0, 100, 72) / 100.0
            p_l_hastes = st.slider("Hastes de Interseção (%)", 0, 100, 58) / 100.0
            p_l_internos = st.slider("Arcos Aninhados (%)", 0, 100, 62) / 100.0
        else: p_l_caligrafia = p_l_fases = p_l_orbitas = p_l_auxiliares = p_l_hastes = p_l_internos = 0.0

    with st.sidebar.expander("11. Família Pyre"):
        ativa_ignea = st.checkbox("Ativar Família Pyre (Dinâmica e Pinceladas)")
        if ativa_ignea:
            st.markdown("*Lâminas afiladas: do orgânico (cicatriz) ao estruturado (alfabeto).*")
            p_i_estr = st.slider("Estrutura (Orgânico ↔ Escrita) (%)", 0, 100, 65) / 100.0
            p_i_comp = st.slider("Complexidade (Glifos Compostos) (%)", 0, 100, 50) / 100.0
            p_i_rug = st.slider("Rugosidade de Borda (%)", 0, 100, 50) / 100.0
            p_i_chama = st.slider("Componente: Cuia de Chama (%)", 0, 100, 50) / 100.0
            p_i_catalise = st.slider("Componente: Irradiação (%)", 0, 100, 40) / 100.0
            p_i_reig = st.slider("Componente: Haste Partida (%)", 0, 100, 40) / 100.0
            p_i_cruz = st.slider("Componente: Cruz / Cortes (%)", 0, 100, 40) / 100.0
            p_i_lab = st.slider("Modificador: Labaredas (%)", 0, 100, 30) / 100.0
            p_i_fag = st.slider("Modificador: Fagulhas (%)", 0, 100, 40) / 100.0
        else: p_i_estr = p_i_comp = p_i_rug = p_i_chama = p_i_catalise = p_i_reig = p_i_cruz = p_i_lab = p_i_fag = 0.0

    with st.sidebar.expander("12. Família Tide"):
        ativa_marinha = st.checkbox("Ativar Família Tide (Contínua/Ondular)")
        if ativa_marinha:
            st.markdown("*Traço único de pena larga, com volutas, laços e marcas.*")
            p_m_corrente = st.slider("Ondulação Base (%)", 0, 100, 70) / 100.0
            p_m_contraste = st.slider("Contraste da Pena (%)", 0, 100, 80) / 100.0
            p_m_espirais = st.slider("Volutas nas Pontas (%)", 0, 100, 70) / 100.0
            p_m_lacos = st.slider("Laços Internos (%)", 0, 100, 40) / 100.0
            p_m_bojos = st.slider("Bojos (Formas Fechadas) (%)", 0, 100, 35) / 100.0
            p_m_ramos = st.slider("Ramos de Pincel (%)", 0, 100, 50) / 100.0
            p_m_marcas = st.slider("Marcas e Pontos (%)", 0, 100, 40) / 100.0
            p_m_ruptura = st.slider("Ganchos e Rupturas (%)", 0, 100, 30) / 100.0
            p_m_vertical = st.slider("Alinhamento Vertical (%)", 0, 100, 30) / 100.0
        else: p_m_corrente = p_m_contraste = p_m_espirais = p_m_lacos = p_m_bojos = p_m_ramos = p_m_marcas = p_m_ruptura = p_m_vertical = 0.0

    with st.sidebar.expander("13. Família Calculus"):
        ativa_gravitacional = st.checkbox("Ativar Família Calculus (Algébrica)")
        if ativa_gravitacional:
            st.markdown("*Geração baseada em matrizes, vetores ortogonais e alinhamento de equações.*")
            p_gr_complexidade = st.slider("Densidade da Equação (%)", 0, 100, 70) / 100.0
        else: p_gr_complexidade = 0.0

    with st.sidebar.expander("14. Sistema de Grid e Filtros"):
        grid_tamanho = st.slider("Resolução Subjacente (Grid)", 3, 7, 5)
        ativa_grid_livre = st.checkbox("Gerar Rotas Aleatórias no Grid", value=False)
        if ativa_grid_livre: grid_passos = st.slider("Passos da Rota", 2, 15, 6)
        else: grid_passos = 4
        st.markdown("---")
        efeito_italico = st.checkbox("Filtro: Distorção Afim (Itálico)", value=False)
        efeito_brush = st.checkbox("Filtro: Textura Brush", value=False)
        efeito_giz = st.checkbox("Filtro: Textura Giz", value=False)
        letra_de_mao = st.checkbox("Filtro: Traço Manual", value=False)

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
        "ignea": {"estrutura": p_i_estr, "complexidade": p_i_comp, "rugosidade": p_i_rug, "chama": p_i_chama, "catalise": p_i_catalise, "reignicao": p_i_reig, "cruzamentos": p_i_cruz, "labaredas": p_i_lab, "fagulhas": p_i_fag},
        "marinha": {"corrente": p_m_corrente, "contraste": p_m_contraste, "espirais": p_m_espirais, "lacos": p_m_lacos, "bojos": p_m_bojos, "ramos": p_m_ramos, "marcas": p_m_marcas, "ruptura": p_m_ruptura, "vertical": p_m_vertical},
        "gravitacional": {"complexidade": p_gr_complexidade},
        "grid": {"tamanho": grid_tamanho, "passos": grid_passos},
        "estilo": {"italico": efeito_italico, "brush": efeito_brush, "giz": efeito_giz, "letra_de_mao": letra_de_mao},
        "espessura": espessura_linha,
        "cor": cor_runa
    }
    st.sidebar.markdown(f"### Copie este JSON de Configuração:")
    st.sidebar.code(json.dumps({ "Nova Família de Runas": preset }, indent=4), language="json")

else:
    if PRESETS_SALVOS:
        escolha = st.sidebar.selectbox("Escolha a Família de Runas", list(PRESETS_SALVOS.keys()))
        preset = PRESETS_SALVOS[escolha]
        st.sidebar.markdown(f"### Lendo configuração de `{ARQUIVO_PRESETS}`:")
        st.sidebar.code(json.dumps(preset, indent=4), language="json")
    else:
        st.sidebar.error("Arquivo de presets não encontrado ou vazio.")

# ==========================================
# 5. COMPILADOR CENTRAL DE SÍMBOLOS
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
    real_draw = ImageDraw.Draw(base)
    
    # Substituto que interceta o canvas para guardar a matriz de vértices
    recorder = DrawRecorder(real_draw)
    
    usa_curvas = random.random() < config.get("modulos", {}).get("curvas", 0)

    # O Recorder processa as famílias, desenhando no PNG E guardando os vetores ao mesmo tempo
    if is_comuns: comuns_grid.aplicar_comuns(recorder, config, cx, cy, cor, esp, estilo, usa_curvas)
    if is_met: metalica.aplicar(recorder, config, cx, cy, cor, esp, estilo)
    if is_sep: sepulcral.aplicar(recorder, config, cx, cy, cor, esp, estilo)
    if is_sang: sanguinea.aplicar(recorder, config, cx, cy, cor, esp, estilo)
    if is_crist: cristalina.aplicar(recorder, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_aeral: aeral.aplicar(recorder, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_glacial: glacial.aplicar(recorder, config, n, step, margem, cor, esp, estilo)
    if is_telurica: telurica.aplicar(recorder, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_estelar: estelar.aplicar(recorder, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_solar: solar.aplicar(recorder, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_lunar: lunar.aplicar(recorder, config, cx, cy, cor, esp, estilo)
    if is_ignea: ignea.aplicar(recorder, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_marinha: marinha.aplicar(recorder, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_gravitacional: gravitacional.aplicar(recorder, config, cx, cy, n, step, margem, cor, esp, estilo)
    if is_grid: comuns_grid.aplicar_grid_livre(recorder, config, n, passos, step, margem, cor, esp, estilo)

    # Avaliação rigorosa das probabilidades UMA vez para a imagem e para o JSON
    mirror = random.random() < config.get("simetria", {}).get("vertical", 0)
    flip = random.random() < config.get("simetria", {}).get("horizontal", 0)
    italic = config.get("estilo", {}).get("italico", False)

    # 1. Aplicar transformações na Imagem 2D
    img_final = base.copy()
    if mirror: img_final.alpha_composite(ImageOps.mirror(img_final))
    if flip: img_final.alpha_composite(ImageOps.flip(img_final))
    if italic:
        matriz = (1, 0.3, -0.3 * cy, 0, 1, 0)
        img_final = img_final.transform(img_final.size, Image.AFFINE, matriz, resample=Image.BICUBIC)

    # Fundo de apresentação (Streamlit apenas)
    fundo = Image.new("RGBA", (tamanho, tamanho), (15, 15, 15, 255))
    fundo.alpha_composite(img_final)
    
    # 2. Aplicar transformações puramente matemáticas na Matriz Vetorial (JSON)
    json_data = gerar_json_matriz(recorder.strokes, tamanho, mirror, flip, italic)
    
    return fundo, img_final, json_data

# ==========================================
# 6. RENDERIZAÇÃO NA INTERFACE
# ==========================================
st.markdown("### Preview da Família Gerada")

if preset:
    cols = st.columns(4)
    for i in range(8):
        random.seed(seed + i)
        
        img_display, img_transp, json_matrix = desenhar_runa(preset)
        col = cols[i % 4]
        
        col.image(img_display, caption=f"ID #{seed+i}", use_container_width=True)
        
        with col.expander("Exportar Arquivos"):
            nome_customizado = st.text_input("Nome do arquivo:", value=f"simbolo_{seed+i}", key=f"nome_{seed+i}")
            nome_base = nome_customizado.strip() if nome_customizado.strip() else f"simbolo_{seed+i}"
            
            st.download_button(
                label="Resolução Alta (400x400)", 
                data=image_to_bytes(img_transp), 
                file_name=f"{nome_base}_normal.png", 
                mime="image/png",
                use_container_width=True
            )
            
            img_carta = converter_pixel_art(img_transp, 39, 41)
            st.download_button(
                label="Formato Medio (39x41)", 
                data=image_to_bytes(img_carta), 
                file_name=f"{nome_base}_carta.png", 
                mime="image/png",
                use_container_width=True
            )
            
            img_mini = converter_pixel_art(img_transp, 18, 18)
            st.download_button(
                label="Formato Miniatura (18x18)", 
                data=image_to_bytes(img_mini), 
                file_name=f"{nome_base}_mini.png", 
                mime="image/png",
                use_container_width=True
            )
            
            st.download_button(
                label="Arquivo JSON (Minecraft 3D)",
                data=json_matrix,
                file_name=f"{nome_base}.json",
                mime="application/json",
                use_container_width=True
            )
else:
    st.info("Painel aguardando configurações válidas para renderização.")

random.seed(seed)