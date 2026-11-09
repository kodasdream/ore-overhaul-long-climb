fn longclimb_block_entity(block: &str, entity: &mut Option<(String, horizon_world::nbt::Compound)>) {
    crate::game::longclimb_table::block_entity(block, entity);
}
