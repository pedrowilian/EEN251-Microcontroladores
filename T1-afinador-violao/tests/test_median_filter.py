"""
Testes para a logica de mediana movel usada no main_loop.

A mediana movel esta inline em main() para evitar overhead de chamada
de funcao. Estes testes replicam a logica em formato testavel para
validar o comportamento e documentar o algoritmo.
"""
import main


def median_step(freq_history, hist_idx, hist_filled, freq, history_size):
    """
    Replica a logica da mediana movel inline em main().

    Adiciona freq ao buffer circular e calcula a mediana das leituras
    validas. Retorna (freq_smooth, novo_hist_idx, novo_hist_filled).
    """
    freq_history[hist_idx] = freq
    hist_idx = (hist_idx + 1) % history_size
    if hist_filled < history_size:
        hist_filled += 1

    if hist_filled >= 3:
        valid = list(freq_history[:hist_filled])
        valid.sort()
        freq_smooth = valid[hist_filled // 2]
    else:
        freq_smooth = freq

    return freq_smooth, hist_idx, hist_filled


class TestMedianaWarmup:
    """Durante o warm-up (menos de 3 leituras), retorna freq direto."""

    def test_primeira_leitura_usa_freq_direto(self):
        history = [0.0] * 5
        smooth, idx, filled = median_step(history, 0, 0, 110.0, 5)
        assert smooth == 110.0
        assert filled == 1
        assert idx == 1

    def test_segunda_leitura_usa_freq_direto(self):
        history = [0.0] * 5
        # primeira
        _, idx, filled = median_step(history, 0, 0, 110.0, 5)
        # segunda
        smooth, idx, filled = median_step(history, idx, filled, 109.5, 5)
        assert smooth == 109.5  # ainda warm-up (2 leituras)
        assert filled == 2

    def test_terceira_leitura_inicia_mediana(self):
        history = [0.0] * 5
        idx, filled = 0, 0
        for f in [110.0, 109.5, 110.5]:
            smooth, idx, filled = median_step(history, idx, filled, f, 5)
        # Com 3 leituras: ordenadas [109.5, 110.0, 110.5] -> mediana = 110.0
        assert smooth == 110.0
        assert filled == 3


class TestMedianaDescarteOutliers:
    """Mediana descarta outliers (objetivo principal da feature)."""

    def test_outlier_unico_e_descartado(self):
        # 4 leituras boas + 1 outlier (47.3 = harmonico errado)
        history = [0.0] * 5
        idx, filled = 0, 0
        leituras = [110.1, 110.2, 110.0, 47.3, 110.3]

        for f in leituras:
            smooth, idx, filled = median_step(history, idx, filled, f, 5)

        # Buffer: [110.1, 110.2, 110.0, 47.3, 110.3]
        # Ordenado: [47.3, 110.0, 110.1, 110.2, 110.3]
        # Mediana (idx 2): 110.1
        assert smooth == 110.1

    def test_outlier_extremo_alto_e_descartado(self):
        history = [0.0] * 5
        idx, filled = 0, 0
        for f in [110.0, 110.1, 110.2, 110.0, 999.0]:
            smooth, idx, filled = median_step(history, idx, filled, f, 5)
        # Ordenado: [110.0, 110.0, 110.1, 110.2, 999.0]
        # Mediana: 110.1
        assert smooth == 110.1

    def test_dois_outliers_em_cinco_ainda_funciona(self):
        # Mediana de 5 elementos resiste a ate 2 outliers (em qualquer lado)
        history = [0.0] * 5
        idx, filled = 0, 0
        for f in [110.0, 110.1, 47.0, 110.2, 999.0]:
            smooth, idx, filled = median_step(history, idx, filled, f, 5)
        # Ordenado: [47.0, 110.0, 110.1, 110.2, 999.0]
        # Mediana: 110.1
        assert smooth == 110.1


class TestBufferCircular:
    """Buffer circular sobrescreve leituras antigas em FIFO."""

    def test_indice_circular(self):
        history = [0.0] * 5
        idx, filled = 0, 0
        for f in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]:
            _, idx, filled = median_step(history, idx, filled, f, 5)
        # Apos 6 leituras, idx volta a 1 (sobrescreveu pos 0 com 6.0)
        assert idx == 1
        assert filled == 5  # capped no tamanho do buffer
        # Buffer atual: [6.0, 2.0, 3.0, 4.0, 5.0]
        assert history == [6.0, 2.0, 3.0, 4.0, 5.0]

    def test_filled_satura_no_history_size(self):
        history = [0.0] * 5
        idx, filled = 0, 0
        for f in [1.0] * 10:
            _, idx, filled = median_step(history, idx, filled, f, 5)
        assert filled == 5  # nao passa do tamanho do buffer


class TestMedianaSinalEstavel:
    """Sinal estavel deve dar mediana proxima dos valores reais."""

    def test_corda_a2_estavel(self):
        # Simulacao: corda A2 com pequenas variacoes (ruido de medicao)
        history = [0.0] * 5
        idx, filled = 0, 0
        leituras = [110.05, 110.12, 109.98, 110.08, 110.03]
        for f in leituras:
            smooth, idx, filled = median_step(history, idx, filled, f, 5)
        # Ordenado: [109.98, 110.03, 110.05, 110.08, 110.12] -> mediana = 110.05
        assert 109.9 < smooth < 110.2

    def test_corda_e2_estavel(self):
        history = [0.0] * 5
        idx, filled = 0, 0
        for f in [82.41, 82.38, 82.45, 82.40, 82.42]:
            smooth, idx, filled = median_step(history, idx, filled, f, 5)
        assert 82.3 < smooth < 82.5


class TestHistorySize:
    """Tamanhos diferentes de buffer comportam-se como esperado."""

    def test_history_size_3(self):
        history = [0.0] * 3
        idx, filled = 0, 0
        for f in [110.0, 109.5, 110.5]:
            smooth, idx, filled = median_step(history, idx, filled, f, 3)
        assert smooth == 110.0  # mediana de 3 elementos

    def test_history_size_7(self):
        history = [0.0] * 7
        idx, filled = 0, 0
        leituras = [110.0, 109.8, 110.2, 110.1, 109.9, 110.3, 47.0]
        for f in leituras:
            smooth, idx, filled = median_step(history, idx, filled, f, 7)
        # Ordenado: [47.0, 109.8, 109.9, 110.0, 110.1, 110.2, 110.3]
        # Mediana (idx 3): 110.0
        assert smooth == 110.0
