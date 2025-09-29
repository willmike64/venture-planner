def calculate_parimutuel_odds(bet_pool):
    total_pool = sum(bet_pool.values())
    odds = {}
    for horse, amount in bet_pool.items():
        odds[horse] = round(total_pool / amount, 2) if amount else 10.0
    return odds

def calculate_win_place_show_payouts(race_results, bet_pools):
    payouts = {'win': {}, 'place': {}, 'show': {}}
    if not race_results:
        return payouts

    first = race_results[0][0]['name'] if isinstance(race_results[0][0], dict) else race_results[0][0]
    second = race_results[1][0]['name'] if len(race_results) > 1 and isinstance(race_results[1][0], dict) else (race_results[1][0] if len(race_results) > 1 else None)
    third = race_results[2][0]['name'] if len(race_results) > 2 and isinstance(race_results[2][0], dict) else (race_results[2][0] if len(race_results) > 2 else None)

    def assign_payout(pool, winners):
        total = sum(pool.values())
        bets_on_winners = sum(pool.get(w, 0) for w in winners)
        if bets_on_winners > 0:
            return {w: total / bets_on_winners for w in winners if w in pool}
        return {}

    payouts['win'] = assign_payout(bet_pools.get('win', {}), [first])
    payouts['place'] = assign_payout(bet_pools.get('place', {}), list(filter(None, [first, second])))
    payouts['show'] = assign_payout(bet_pools.get('show', {}), list(filter(None, [first, second, third])))

    return payouts

def get_effective_bet(amount, is_own_horse, partnership_bonus=1.0):
    owner_bonus = 1.5 if is_own_horse else 1.0
    return amount * owner_bonus * partnership_bonus

def clean_horse_name(name):
    return name.split(" (YOUR HORSE")[0].strip()
