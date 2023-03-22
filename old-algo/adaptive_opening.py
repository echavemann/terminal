import random
from operator import itemgetter

""" Adaptive opening defence. 
    Assesses the enemy's defence and makes an opening, so that our EMPs attack weaker side."""


def build_defences_with_adaptive_opening(
    game_state, units, is_right_opening, filter_locs
):
    destructor_locations = [[2, 13], [3, 13], [10, 13], [17, 13], [24, 13], [25, 13]]
    game_state.attempt_spawn(units.DESTRUCTOR, destructor_locations)
    if game_state.turn_number < 4:
        return [], True
    final_filter_locs = list(filter_locs)
    if game_state.turn_number % 4 == 0:
        is_right_opening = should_right_be_open(game_state, units)
    if is_right_opening:
        remove_filter_at = [[23, 13]]
        final_filter_locs.append([4, 13])
    else:
        remove_filter_at = [[4, 13]]
        final_filter_locs.append([23, 13])
    game_state.attempt_remove(remove_filter_at)
    final_filter_locs.sort(key=itemgetter(0), reverse=(not is_right_opening))
    game_state.attempt_spawn(units.FILTER, final_filter_locs)
    return final_filter_locs, is_right_opening


def should_right_be_open(game_state, units, weights=None):
    if not weights:
        weights = [1, 6]  
    weights_by_def_unit = dict(zip([units.FILTER, units.DESTRUCTOR], weights))
    left_strength, right_strength = (0, 0)
    for location in game_state.game_map:
        if game_state.contains_stationary_unit(location):
            for unit in game_state.game_map[location]:
                if unit.player_index == 1 and (
                    unit.unit_type == units.DESTRUCTOR or unit.unit_type == units.FILTER
                ):
                    if location[0] < 14:
                        left_strength += weights_by_def_unit[unit.unit_type]
                    else:
                        right_strength += weights_by_def_unit[unit.unit_type]

    if left_strength > right_strength:
        right = True
    elif left_strength < right_strength:
        right = False
    else:
        right = bool(random.randint(0, 1))
    return right
