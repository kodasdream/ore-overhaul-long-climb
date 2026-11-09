fn longclimb_panel_page(game: &mut crate::game::Game<'_>, mod_id: &str, title: &str, tabs: &[NativeStack], tab: u32, views: &[NativeRecipeView]) -> core::ops::ControlFlow<()> {
    crate::game::longclimb_table::panel_page(game, mod_id, title, tabs, tab, views);
    core::ops::ControlFlow::Break(())
}
