fn longclimb_clock(game: &crate::game::Game<'_>, batch: &mut horizon_client::hud::HudBatch, corners: &mut horizon_client::extras_hud::Corners) {
    crate::game::longclimb_manual::clock(game, batch, corners);
}
