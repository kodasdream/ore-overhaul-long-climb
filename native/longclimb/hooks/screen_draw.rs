fn longclimb_screen_draw(game: &crate::game::Game<'_>, block: &str, batch: &mut horizon_client::hud::HudBatch, origin: [f32; 2]) {
    crate::game::longclimb_table::screen_draw(game, block, batch, origin);
}
