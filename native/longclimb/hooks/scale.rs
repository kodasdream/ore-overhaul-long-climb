fn longclimb_scale_recipe(id: &str, recipe: &mut serde_json::Value) {
    crate::recipe_filters::longclimb_scale::rewrite(id, recipe);
}
