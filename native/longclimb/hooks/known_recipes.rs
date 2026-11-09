fn longclimb_known_recipes(game: &mut crate::game::Game<'_>) -> core::ops::ControlFlow<Arc<[i32]>> {
    match crate::game::longclimb_table::known(game) {
        Some(all) => core::ops::ControlFlow::Break(all),
        None => core::ops::ControlFlow::Continue(()),
    }
}
