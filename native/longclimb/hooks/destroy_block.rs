fn longclimb_destroy_block(game: &mut crate::game::Game<'_>, pos: [i32; 3], state: horizon_world::registry::BlockStateId, canceled: &mut bool) {
    crate::game::longclimb_table::destroy_block(game, pos, state, canceled);
}
