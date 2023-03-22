
def build_defences(game_state, units, is_right_opening, filter_locs):
    encryptor_locations = [[13, 10], [14, 10]]
    game_state.attempt_spawn(units.ENCRYPTOR, encryptor_locations)
    game_state.attempt_upgrade(encryptor_locations)
    destructor_locations = (
        [[25, 12], [24, 11], [24, 10]]
        if is_right_opening
        else [[2, 12], [3, 11], [3, 10]]
    )
    game_state.attempt_spawn(units.DESTRUCTOR, destructor_locations)
    if all(map(game_state.contains_stationary_unit, destructor_locations)):
        game_state.attempt_upgrade(filter_locs)
    destructor_locations = [
        [17, 11],
        [6, 8],
        [10, 11],
        [15, 9],
        [12, 9],
        [15, 6],
        [12, 6],
    ]
    game_state.attempt_spawn(units.DESTRUCTOR, destructor_locations)

