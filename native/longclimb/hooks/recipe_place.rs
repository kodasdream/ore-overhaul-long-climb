fn longclimb_recipe_place(game: &mut crate::game::Game<'_>, book_id: i32, all: bool) -> core::ops::ControlFlow<Result<(), String>> {
    if crate::game::longclimb_table::place(game, book_id, all) {
        core::ops::ControlFlow::Break(Ok(()))
    } else {
        core::ops::ControlFlow::Continue(())
    }
}
