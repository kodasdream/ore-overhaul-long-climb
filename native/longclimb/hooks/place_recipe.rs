fn longclimb_place_recipe(game: &crate::game::Game<'_>, entry_index: usize) -> core::ops::ControlFlow<()> {
    let id = game.recipe_ui.book.as_ref().and_then(|b| b.entries.get(entry_index)).map(|e| e.id.clone());
    if id.is_some_and(|id| crate::game::longclimb_table::too_big(game, &id)) {
        core::ops::ControlFlow::Break(())
    } else {
        core::ops::ControlFlow::Continue(())
    }
}
