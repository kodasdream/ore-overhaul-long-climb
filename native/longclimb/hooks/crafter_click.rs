fn longclimb_crafter_click(game: &mut crate::game::Game<'_>, slot: usize, shift: bool) -> core::ops::ControlFlow<bool> {
    if crate::game::longclimb_table::click(game, slot, shift) {
        core::ops::ControlFlow::Break(true)
    } else {
        core::ops::ControlFlow::Continue(())
    }
}
