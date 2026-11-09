fn longclimb_before_removal(level: &mut crate::game::GameLevel<'_>, pos: BlockPos) {
    crate::game::longclimb_table::before_removal(level, pos);
}
