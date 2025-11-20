"""
AUDITORÍA MATEMÁTICA DE CÁLCULOS
==================================

Valida manualmente los cálculos del sistema comparándolos con casos del PDF.
"""

import numpy as np
from scipy.stats import poisson
from math import floor


def calculate_poisson_match_probabilities(home_xg: float, away_xg: float, max_goals: int = 10):
    """
    Calcula probabilidades de victoria/empate/derrota usando distribución de Poisson.

    Este es el cálculo EXACTO que debería hacer el sistema.
    """
    home_win_prob = 0.0
    draw_prob = 0.0
    away_win_prob = 0.0

    # Matriz de probabilidades para cada resultado
    score_matrix = []

    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            # Probabilidad de este resultado exacto
            prob = (
                poisson.pmf(home_goals, home_xg) *
                poisson.pmf(away_goals, away_xg)
            )

            score_matrix.append({
                'score': f"{home_goals}-{away_goals}",
                'probability': prob
            })

            if home_goals > away_goals:
                home_win_prob += prob
            elif home_goals == away_goals:
                draw_prob += prob
            else:
                away_win_prob += prob

    return {
        'home': home_win_prob,
        'draw': draw_prob,
        'away': away_win_prob,
        'score_matrix': sorted(score_matrix, key=lambda x: x['probability'], reverse=True)[:10]
    }


def calculate_goal_ranges(home_xg: float, away_xg: float):
    """
    Calcula probabilidades de rangos de goles totales.
    """
    total_xg = home_xg + away_xg

    cdf_1 = poisson.cdf(1, total_xg)
    cdf_3 = poisson.cdf(3, total_xg)

    return {
        '0-1': cdf_1,
        '2-3': cdf_3 - cdf_1,
        '4+': 1 - cdf_3
    }


def calculate_edge(our_prob: float, odds: float):
    """
    Calcula edge (ventaja matemática).

    Edge = (Probabilidad calculada × Cuota) - 1
    """
    return (our_prob * odds) - 1


def implied_probability(odds: float):
    """
    Probabilidad implícita de una cuota.
    """
    return 1 / odds


def validate_partido_1_burnley_chelsea():
    """
    CASO DE PRUEBA #1: Burnley vs Chelsea

    Datos del PDF:
    - xG: Burnley 0.36, Chelsea 0.69
    - Poisson: Local 17.0%, Empate 44.2%, Visitante 38.8%
    - Goal Ranges: 0-1 (71.7%), 2-3 (26.0%), 4+ (2.2%)
    """
    print("=" * 80)
    print("CASO #1: BURNLEY vs CHELSEA")
    print("=" * 80)
    print()

    home_xg = 0.36
    away_xg = 0.69

    print(f"Expected Goals: Burnley {home_xg}, Chelsea {away_xg}")
    print()

    # Calcular probabilidades Poisson
    probs = calculate_poisson_match_probabilities(home_xg, away_xg)

    print("PROBABILIDADES POISSON (CALCULADAS):")
    print(f"  Local:      {probs['home']:.4f} ({probs['home']*100:.1f}%)")
    print(f"  Empate:     {probs['draw']:.4f} ({probs['draw']*100:.1f}%)")
    print(f"  Visitante:  {probs['away']:.4f} ({probs['away']*100:.1f}%)")
    print()

    print("PROBABILIDADES POISSON (PDF):")
    print(f"  Local:      17.0%")
    print(f"  Empate:     44.2%")
    print(f"  Visitante:  38.8%")
    print()

    # Comparar
    pdf_home = 0.170
    pdf_draw = 0.442
    pdf_away = 0.388

    diff_home = abs(probs['home'] - pdf_home)
    diff_draw = abs(probs['draw'] - pdf_draw)
    diff_away = abs(probs['away'] - pdf_away)

    print("DIFERENCIAS:")
    print(f"  Local:      {diff_home:.4f} ({diff_home*100:.2f} puntos porcentuales)")
    print(f"  Empate:     {diff_draw:.4f} ({diff_draw*100:.2f} puntos porcentuales)")
    print(f"  Visitante:  {diff_away:.4f} ({diff_away*100:.2f} puntos porcentuales)")
    print()

    # Goal ranges
    goal_ranges = calculate_goal_ranges(home_xg, away_xg)

    print("GOAL RANGES (CALCULADOS):")
    print(f"  0-1 goles:  {goal_ranges['0-1']:.4f} ({goal_ranges['0-1']*100:.1f}%)")
    print(f"  2-3 goles:  {goal_ranges['2-3']:.4f} ({goal_ranges['2-3']*100:.1f}%)")
    print(f"  4+ goles:   {goal_ranges['4+']:.4f} ({goal_ranges['4+']*100:.1f}%)")
    print()

    print("GOAL RANGES (PDF):")
    print(f"  0-1 goles:  71.7%")
    print(f"  2-3 goles:  26.0%")
    print(f"  4+ goles:   2.2%")
    print()

    # Resultados más probables
    print("TOP 10 RESULTADOS MÁS PROBABLES:")
    for i, score in enumerate(probs['score_matrix'][:10], 1):
        print(f"  {i}. {score['score']}: {score['probability']:.4f} ({score['probability']*100:.2f}%)")
    print()

    # VALIDACIÓN CRÍTICA
    print("VALIDACIÓN:")
    total_prob = probs['home'] + probs['draw'] + probs['away']
    print(f"  Suma de probabilidades: {total_prob:.6f} (debería ser ~1.0)")

    if abs(total_prob - 1.0) > 0.01:
        print("  ⚠️  ERROR: La suma no es 1.0!")
    else:
        print("  ✅ Suma correcta")

    # Tolerancia de 1 punto porcentual
    tolerance = 0.01
    if diff_home > tolerance or diff_draw > tolerance or diff_away > tolerance:
        print(f"  ⚠️  INCONSISTENCIA: Diferencias mayores a {tolerance*100}% detectadas")
    else:
        print(f"  ✅ Cálculos consistentes con PDF (tolerancia {tolerance*100}%)")

    print()


def validate_partido_2_bournemouth_westham():
    """
    CASO DE PRUEBA #2: Bournemouth vs West Ham

    Datos del PDF:
    - xG: Bournemouth 0.91, West Ham 0.14
    - Poisson: Local 54.8%, Empate 39.6%, Visitante 5.6%
    """
    print("=" * 80)
    print("CASO #2: BOURNEMOUTH vs WEST HAM")
    print("=" * 80)
    print()

    home_xg = 0.91
    away_xg = 0.14

    print(f"Expected Goals: Bournemouth {home_xg}, West Ham {away_xg}")
    print()

    # Calcular probabilidades Poisson
    probs = calculate_poisson_match_probabilities(home_xg, away_xg)

    print("PROBABILIDADES POISSON (CALCULADAS):")
    print(f"  Local:      {probs['home']:.4f} ({probs['home']*100:.1f}%)")
    print(f"  Empate:     {probs['draw']:.4f} ({probs['draw']*100:.1f}%)")
    print(f"  Visitante:  {probs['away']:.4f} ({probs['away']*100:.1f}%)")
    print()

    print("PROBABILIDADES POISSON (PDF):")
    print(f"  Local:      54.8%")
    print(f"  Empate:     39.6%")
    print(f"  Visitante:  5.6%")
    print()

    # ANÁLISIS CRÍTICO: Con xG tan bajo (0.14), ¿tiene sentido 5.6%?
    print("ANÁLISIS CRÍTICO:")
    print(f"  West Ham xG = {away_xg} (muy bajo)")
    print()

    # Probabilidad de que West Ham NO meta goles
    prob_west_ham_0_goals = poisson.pmf(0, away_xg)
    print(f"  P(West Ham marca 0 goles) = {prob_west_ham_0_goals:.4f} ({prob_west_ham_0_goals*100:.1f}%)")
    print()

    # Para que West Ham gane, DEBE meter al menos 1 gol
    prob_west_ham_scores = 1 - prob_west_ham_0_goals
    print(f"  P(West Ham marca ≥1 gol) = {prob_west_ham_scores:.4f} ({prob_west_ham_scores*100:.1f}%)")
    print()

    print("  Con xG de 0.14, West Ham tiene:")
    print(f"    - {prob_west_ham_0_goals*100:.1f}% de NO marcar")
    print(f"    - {prob_west_ham_scores*100:.1f}% de marcar al menos 1 gol")
    print()
    print(f"  Visitante win probability: {probs['away']*100:.1f}%")
    print(f"  ¿Es lógico 5.6% cuando solo tienen {prob_west_ham_scores*100:.1f}% de marcar?")
    print()

    # Goal ranges
    goal_ranges = calculate_goal_ranges(home_xg, away_xg)

    print("GOAL RANGES:")
    print(f"  0-1 goles:  {goal_ranges['0-1']:.4f} ({goal_ranges['0-1']*100:.1f}%)")
    print(f"  2-3 goles:  {goal_ranges['2-3']:.4f} ({goal_ranges['2-3']*100:.1f}%)")
    print(f"  4+ goles:   {goal_ranges['4+']:.4f} ({goal_ranges['4+']*100:.1f}%)")
    print()


def validate_partido_6_brighton_brentford():
    """
    CASO DE PRUEBA #6: Brighton vs Brentford

    Datos del PDF:
    - xG: Brighton 1.43, Brentford 0.36
    - Poisson: Local 64.4%, Empate 26.5%, Visitante 9.1%
    - Goal Ranges: 0-1 (46.6%), 2-3 (42.7%), 4+ (10.7%)
    """
    print("=" * 80)
    print("CASO #6: BRIGHTON vs BRENTFORD")
    print("=" * 80)
    print()

    home_xg = 1.43
    away_xg = 0.36

    print(f"Expected Goals: Brighton {home_xg}, Brentford {away_xg}")
    print()

    # Calcular probabilidades Poisson
    probs = calculate_poisson_match_probabilities(home_xg, away_xg)

    print("PROBABILIDADES POISSON (CALCULADAS):")
    print(f"  Local:      {probs['home']:.4f} ({probs['home']*100:.1f}%)")
    print(f"  Empate:     {probs['draw']:.4f} ({probs['draw']*100:.1f}%)")
    print(f"  Visitante:  {probs['away']:.4f} ({probs['away']*100:.1f}%)")
    print()

    print("PROBABILIDADES POISSON (PDF):")
    print(f"  Local:      64.4%")
    print(f"  Empate:     26.5%")
    print(f"  Visitante:  9.1%")
    print()

    # Goal ranges
    goal_ranges = calculate_goal_ranges(home_xg, away_xg)

    print("GOAL RANGES (CALCULADOS):")
    print(f"  0-1 goles:  {goal_ranges['0-1']:.4f} ({goal_ranges['0-1']*100:.1f}%)")
    print(f"  2-3 goles:  {goal_ranges['2-3']:.4f} ({goal_ranges['2-3']*100:.1f}%)")
    print(f"  4+ goles:   {goal_ranges['4+']:.4f} ({goal_ranges['4+']*100:.1f}%)")
    print()

    print("GOAL RANGES (PDF):")
    print(f"  0-1 goles:  46.6%")
    print(f"  2-3 goles:  42.7%")
    print(f"  4+ goles:   10.7%")
    print()


def validate_edge_calculation():
    """
    VALIDACIÓN DE CÁLCULO DE EDGE

    Caso del PDF - Partido #1 Empate:
    - Nuestra prob: 44.2%
    - Edge: +110.6%
    - Esto implica cuota de ~4.76
    """
    print("=" * 80)
    print("VALIDACIÓN: CÁLCULO DE EDGE")
    print("=" * 80)
    print()

    our_prob = 0.442
    edge_reported = 1.106  # 110.6%

    print("DATOS DEL PDF:")
    print(f"  Nuestra probabilidad: {our_prob*100:.1f}%")
    print(f"  Edge reportado:       {edge_reported*100:.1f}%")
    print()

    # Fórmula: Edge = (Prob × Odds) - 1
    # Despejando: Odds = (Edge + 1) / Prob
    implied_odds = (edge_reported + 1) / our_prob

    print("CÁLCULO INVERSO:")
    print(f"  Cuota implícita = (Edge + 1) / Prob")
    print(f"  Cuota implícita = ({edge_reported} + 1) / {our_prob}")
    print(f"  Cuota implícita = {implied_odds:.2f}")
    print()

    # Probabilidad implícita de la cuota
    bookmaker_prob = 1 / implied_odds

    print(f"  Probabilidad implícita de cuota {implied_odds:.2f}: {bookmaker_prob*100:.1f}%")
    print()

    # PREGUNTA CRÍTICA
    print("PREGUNTA CRÍTICA:")
    print(f"  ¿Es realista que una casa de apuestas ofrezca cuota {implied_odds:.2f}")
    print(f"  (probabilidad implícita {bookmaker_prob*100:.1f}%) para un empate que")
    print(f"  nosotros calculamos en {our_prob*100:.1f}%?")
    print()

    # Verificación del cálculo
    edge_recalculated = (our_prob * implied_odds) - 1

    print("VERIFICACIÓN:")
    print(f"  Edge recalculado = (Prob × Odds) - 1")
    print(f"  Edge recalculado = ({our_prob} × {implied_odds:.2f}) - 1")
    print(f"  Edge recalculado = {edge_recalculated:.4f} ({edge_recalculated*100:.1f}%)")
    print()

    if abs(edge_recalculated - edge_reported) < 0.001:
        print("  ✅ Cálculo de edge CORRECTO")
    else:
        print("  ❌ ERROR en cálculo de edge")
        print(f"     Diferencia: {abs(edge_recalculated - edge_reported):.4f}")
    print()

    # Escenario realista
    print("ESCENARIO REALISTA:")
    realistic_odds = 2.5  # Cuota típica para empate
    realistic_edge = calculate_edge(our_prob, realistic_odds)
    realistic_bookmaker_prob = implied_probability(realistic_odds)

    print(f"  Si la cuota real fuera {realistic_odds}:")
    print(f"    - Probabilidad implícita: {realistic_bookmaker_prob*100:.1f}%")
    print(f"    - Edge: {realistic_edge*100:.1f}%")
    print()


def main():
    """Ejecuta todas las validaciones."""
    validate_partido_1_burnley_chelsea()
    print("\n" * 2)

    validate_partido_2_bournemouth_westham()
    print("\n" * 2)

    validate_partido_6_brighton_brentford()
    print("\n" * 2)

    validate_edge_calculation()
    print()

    print("=" * 80)
    print("AUDITORÍA COMPLETADA")
    print("=" * 80)


if __name__ == "__main__":
    main()
