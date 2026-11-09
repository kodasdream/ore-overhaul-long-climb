// Long Climb's own behaviour: the 5x5 table, the 3x3 hammers and excavators, and an AIOT's right clicks. These live here rather than
// in the Tinkers mod, so Long Climb keeps working with Tinkers off.
use super::{BlockEntity, Game};
use horizon_client::containers::{ModBlockEntity, ModContainer};
use horizon_client::hud::HudBatch;
use horizon_client::items::ItemStack;
use horizon_client::mod_api::NativeScreen;
use horizon_world::nbt::{Compound, JavaString, Tag};
use horizon_world::registry::BlockStateId;

const TABLE: &str = "longclimb:crafting_table_5x5";
const CELLS: usize = 25;
const RESULT: usize = 25;
/// The result slot's number in the open menu: containers start at 300.
const RESULT_SLOT: usize = 300 + RESULT;

pub fn block_entity(block: &str, entity: &mut Option<(String, Compound)>) {
    if block == TABLE && entity.is_none() {
        *entity = Some((block.to_owned(), Compound::new()));
    }
}

pub fn ticks(block: &str, ticks: &mut bool) {
    if block == TABLE {
        *ticks = true;
    }
}

pub fn container(block: &str, out: &mut Option<ModContainer>) {
    if block != TABLE {
        return;
    }
    let cells: Vec<usize> = (0..CELLS).collect();
    *out = Some(ModContainer {
        slots: CELLS + 1,
        faces: std::array::from_fn(|_| Vec::new()),
        inputs: cells,
        outputs: vec![RESULT],
        menu: Some("longclimb:crafting_5x5".to_owned()),
    });
}

pub fn screen(block: &str, out: &mut Option<NativeScreen>) {
    if block != TABLE {
        return;
    }
    let mut slots: Vec<Option<[f32; 2]>> = Vec::with_capacity(CELLS + 1);
    for r in 0..5 {
        for c in 0..5 {
            slots.push(Some([18.0 + c as f32 * 18.0, 18.0 + r as f32 * 18.0]));
        }
    }
    slots.push(Some([138.0, 54.0]));
    *out = Some(NativeScreen { width: 176.0, height: 200.0, slots, inventory_y: 118.0, inventory_x: 8.0, own_labels: false, own_background: false });
}

pub fn screen_draw(game: &Game<'_>, block: &str, batch: &mut HudBatch, origin: [f32; 2]) {
    if block != TABLE {
        return;
    }
    // An arrow from the grid to the result.
    let (x, y) = (origin[0] + 112.0, origin[1] + 60.0);
    game.native_fill(batch, [x, y, 14.0, 4.0], 0xFF70_7070);
    for i in 0..5 {
        let f = i as f32;
        game.native_fill(batch, [x + 14.0 + f, y - 4.0 + f, 1.0, 12.0 - f * 2.0], 0xFF70_7070);
    }
}

fn find(game: &Game<'_>, grid: &[Option<ItemStack>]) -> Option<(String, ItemStack)> {
    let scale = |id: i32| game.maps.data.get(&id).map(|m| m.scale);
    game.res.recipes().find_with(grid, 5, &scale).map(|(name, result)| (name.to_owned(), result))
}

fn remainders(game: &Game<'_>, recipe: &str, grid: &[Option<ItemStack>]) -> Vec<Option<ItemStack>> {
    match &game.world_tables {
        Some(t) => t.recipes.remainders(recipe, grid, 5),
        None => game.res.recipes().remainders(recipe, grid, 5),
    }
}

/// One of each ingredient goes, and what a recipe hands back (an empty bucket) takes its place.
fn consume(game: &mut Game<'_>, items: &mut [Option<ItemStack>], recipe: &str) {
    let rest = remainders(game, recipe, &items[..CELLS]);
    for cell in items[..CELLS].iter_mut() {
        if let Some(s) = cell {
            s.count -= 1;
            if s.count == 0 {
                *cell = None;
            }
        }
    }
    for (i, back) in rest.into_iter().enumerate() {
        let Some(back) = back else { continue };
        match &mut items[i] {
            cell @ None => *cell = Some(back),
            Some(c) if c.same_item_same_components(&back) => c.count += back.count,
            _ => game.give_or_drop(back),
        }
    }
}

fn set_offered(entity: &mut ModBlockEntity, on: bool) {
    entity.nbt.insert(JavaString::from("offered"), Tag::Byte(i8::from(on)));
}

fn offered(entity: &ModBlockEntity) -> bool {
    matches!(entity.nbt.get(&JavaString::from("offered")), Some(Tag::Byte(1)))
}

/// Keeps the result slot showing what the grid makes, and settles a result taken since: its ingredients go. Only here, never
/// during a click: the menu writes its own copy of the slots back after a click, which would undo (or fake) a change made then. A click reaches the
/// server's menu, which never tells whether it was a shift-click, so each one makes one result (vanilla's shift crafts a stack).
pub fn tick(game: &mut Game<'_>, pos: [i32; 3], entity: &mut ModBlockEntity) {
    if entity.id != TABLE || entity.items.len() <= RESULT {
        return;
    }
    if offered(entity) && entity.items[RESULT].is_none() {
        debug("tick-take", game, &entity.items, true);
        let mut items = entity.items.clone();
        if let Some((recipe, result)) = find(game, &items[..CELLS]) {
            let ingredients = items[..CELLS].to_vec();
            consume(game, &mut items, &recipe);
            credit(game, &recipe, &result, ingredients);
            entity.items = items;
        }
        set_offered(entity, false);
        // The slot stays empty this tick: refilled with the same item in the same tick, the server would see no change and
        // never tell the screen, which already shows it taken.
        return;
    }
    let made = find(game, &entity.items[..CELLS]).map(|(_, r)| r);
    if entity.items[RESULT] != made {
        let on = made.is_some();
        entity.items[RESULT] = made;
        set_offered(entity, on);
    }
    resend_result(game, pos);
}

/// Everyone with this table open is sent its result slot again each tick. A screen guesses at its own clicks and may wipe
/// the slot; the server, believing the screen already has the result, would otherwise never send it again.
fn resend_result(game: &mut Game<'_>, pos: [i32; 3]) {
    let key = (pos[0], pos[1], pos[2]);
    let Some(lan) = game.lan.as_mut() else { return };
    for g in lan.hub.guests.iter_mut() {
        if let Some(m) = g.menu.as_mut()
            && m.pos == Some(key)
            && m.sent.len() > RESULT
        {
            // A value the slot can never hold, so the next sync always differs and sends the real one.
            m.sent[RESULT] = Some(ItemStack { item: std::sync::Arc::from("longclimb:resend"), count: 0, damage: 0, extra: None });
        }
    }
}

fn debug(what: &str, game: &Game<'_>, items: &[Option<ItemStack>], offered: bool) {
    if std::env::var_os("LONGCLIMB_DEBUG").is_some() {
        let filled = items.iter().take(CELLS).flatten().count();
        eprintln!("[longclimb] {what} server={} offered={offered} cells={filled} result={:?} carried={:?}", game.serving.is_some(), items.get(RESULT).and_then(|r| r.as_ref()).map(|r| r.item.clone()), game.carried.as_ref().map(|c| (c.item.clone(), c.count)));
    }
}

/// What vanilla's `ResultSlot.onTake` hands out: the crafted stat, the recipe's advancement and the mods' hook.
fn credit(game: &mut Game<'_>, recipe: &str, taken: &ItemStack, ingredients: Vec<Option<ItemStack>>) {
    let player = game.native_acting_id();
    game.native_item_crafted(player, &format!("minecraft:{recipe}"), taken);
    game.tutorial_get_item(Some(taken));
    game.award_stat("crafted", &taken.item, taken.count as i32);
    game.award_crafted(&[(format!("minecraft:{recipe}"), ingredients)]);
}

/// A click on the result slot: as vanilla's `ResultSlot`, shift crafts all it can. True when the click was this table's.
pub fn click(game: &mut Game<'_>, slot: usize, shift: bool) -> bool {
    if slot != RESULT_SLOT {
        return false;
    }
    if std::env::var_os("LONGCLIMB_DEBUG").is_some() {
        eprintln!("[longclimb] click slot={slot} shift={shift} server={} container={:?}", game.serving.is_some(), game.container);
    }
    let Some(key) = game.container else { return false };
    let mut items = match game.world.block_entities.get(&key) {
        Some(BlockEntity::Mod(e)) if e.id == TABLE => e.items.clone(),
        _ => return false,
    };
    let mut crafted = 0;
    while let Some((recipe, result)) = find(game, &items[..CELLS]) {
        let made = (result.item.clone(), result.count);
        let taken = result.clone();
        let ingredients = items[..CELLS].to_vec();
        if shift {
            if game.give(result).is_some() {
                break;
            }
        } else {
            let max = game.res.items().get(&result.item).map_or(64, |i| i.max_stack);
            match &mut game.carried {
                None => game.carried = Some(result),
                Some(c) if c.same_item_same_components(&result) && c.count + result.count <= max => c.count += result.count,
                _ => break,
            }
        }
        consume(game, &mut items, &recipe);
        crafted += 1;
        let player = game.native_acting_id();
        game.native_item_crafted(player, &format!("minecraft:{recipe}"), &taken);
        game.tutorial_get_item(Some(&taken));
        game.award_stat("crafted", &made.0, made.1 as i32);
        game.award_crafted(&[(format!("minecraft:{recipe}"), ingredients)]);
        if !shift || crafted >= 64 {
            break;
        }
    }
    let now = find(game, &items[..CELLS]).map(|(_, r)| r);
    let on = now.is_some();
    items[RESULT] = now;
    if let Some(BlockEntity::Mod(e)) = game.world.block_entities.get_mut(&key) {
        e.items = items;
        set_offered(e, on);
    }
    game.world.modified.insert((key.0 >> 4, key.2 >> 4));
    game.container_changed(key);
    true
}

fn table_open(game: &Game<'_>) -> Option<(i32, i32, i32)> {
    let key = game.container?;
    match game.world.block_entities.get(&key) {
        Some(BlockEntity::Mod(e)) if e.id == TABLE => Some(key),
        _ => None,
    }
}

/// A recipe viewer's "+" with this table open: everything in the grid goes back, then the recipe is laid out from the inventory.
pub fn place(game: &mut Game<'_>, book_id: i32, all: bool) -> bool {
    let Some(key) = table_open(game) else { return false };
    let Some(catalog) = game.native_recipes() else { return true };
    let Some(recipe) = catalog.recipes.iter().find(|r| r.book_id == book_id) else { return true };
    let mut items = match game.world.block_entities.get(&key) {
        Some(BlockEntity::Mod(e)) => e.items.clone(),
        _ => return true,
    };
    for cell in items[..CELLS].iter_mut() {
        if let Some(stack) = cell.take() {
            game.give_or_drop(stack);
        }
    }
    let width = if recipe.width == 0 { 5 } else { recipe.width as usize };
    let rounds = if all { 64 } else { 1 };
    for _ in 0..rounds {
        let mut placed_all = true;
        for (i, choices) in recipe.slots.iter().enumerate() {
            if choices.is_empty() {
                continue;
            }
            let at = (i / width) * 5 + i % width;
            if at >= CELLS {
                continue;
            }
            let wanted = |s: &ItemStack| choices.iter().any(|c| catalog.items.get(c.item as usize).is_some_and(|it| it.id == *s.item));
            let source = (0..36).find(|&n| {
                game.inventory[n].as_ref().is_some_and(|s| {
                    wanted(s) && items[at].as_ref().is_none_or(|c| {
                        c.same_item_same_components(s) && c.count < game.res.items().get(&c.item).map_or(64, |t| t.max_stack)
                    })
                })
            });
            let Some(n) = source else {
                placed_all = false;
                continue;
            };
            let Some(stack) = game.inventory[n].as_mut() else { continue };
            let one = ItemStack { count: 1, ..stack.clone() };
            stack.count -= 1;
            if stack.count == 0 {
                game.inventory[n] = None;
            }
            match &mut items[at] {
                Some(c) => c.count += 1,
                cell @ None => *cell = Some(one),
            }
        }
        if !placed_all {
            break;
        }
    }
    let now = find(game, &items[..CELLS]).map(|(_, r)| r);
    let on = now.is_some();
    items[RESULT] = now;
    if let Some(BlockEntity::Mod(e)) = game.world.block_entities.get_mut(&key) {
        e.items = items;
        set_offered(e, on);
    }
    game.world.modified.insert((key.0 >> 4, key.2 >> 4));
    game.container_changed(key);
    true
}

/// With this table open, a viewer may offer every recipe's "+": nothing else unlocks mods' recipes.
pub fn known(game: &mut Game<'_>) -> Option<std::sync::Arc<[i32]>> {
    table_open(game)?;
    let catalog = game.native_recipes()?;
    Some(catalog.recipes.iter().map(|r| r.book_id).filter(|id| *id >= 0).collect())
}

/// Whether a recipe is too big for the grid the book is on: the book must not try.
pub fn too_big(game: &Game<'_>, id: &str) -> bool {
    let size = game.craft_size;
    game.res.recipes().placement(id).is_some_and(|p| match p.shaped {
        Some((w, h)) => w > size || h > size,
        None => p.ingredients.len() > size * size,
    })
}

/// A table leaving the world any way at all (broken, blown up, replaced): its result is only a preview and must not spill.
pub fn before_removal(level: &mut super::GameLevel<'_>, pos: horizon_core::position::BlockPos) {
    let key = (pos.x, pos.y, pos.z);
    if let Some(BlockEntity::Mod(e)) = level.world.block_entities.get_mut(&key)
        && e.id == TABLE
        && e.items.len() > RESULT
    {
        e.items[RESULT] = None;
    }
}

// --- Hammers and excavators ----------------------------------------------------------------------------------------------

static PENDING: std::sync::Mutex<Vec<[i32; 3]>> = std::sync::Mutex::new(Vec::new());
static BUSY: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);

fn area_tag(item: &str) -> Option<&'static str> {
    let name = item.strip_prefix("longclimb:")?;
    if name.ends_with("_hammer") {
        Some("minecraft:mineable/pickaxe")
    } else if name.ends_with("_excavator") {
        Some("minecraft:mineable/shovel")
    } else {
        None
    }
}

/// The eight blocks around the target, across the way the player looks.
fn around(game: &Game<'_>, pos: [i32; 3]) -> Vec<[i32; 3]> {
    let (yaw, pitch) = game.player.as_ref().map_or((0.0, 0.0), |p| (p.yaw, p.pitch));
    let flat = !(-45.0..=45.0).contains(&pitch);
    let a = yaw.rem_euclid(360.0);
    let along_x = !((45.0..135.0).contains(&a) || (225.0..315.0).contains(&a));
    let mut out = Vec::with_capacity(8);
    for u in -1..=1 {
        for v in -1..=1 {
            if u == 0 && v == 0 {
                continue;
            }
            out.push(if flat {
                [pos[0] + u, pos[1], pos[2] + v]
            } else if along_x {
                [pos[0] + u, pos[1] + v, pos[2]]
            } else {
                [pos[0], pos[1] + v, pos[2] + u]
            });
        }
    }
    out
}

pub fn destroy_block(game: &mut Game<'_>, pos: [i32; 3], _state: BlockStateId, _canceled: &mut bool) {
    // A table's result is only a preview: it must not spill with the block.
    let key = (pos[0], pos[1], pos[2]);
    if let Some(BlockEntity::Mod(e)) = game.world.block_entities.get_mut(&key)
        && e.id == TABLE
        && e.items.len() > RESULT
    {
        e.items[RESULT] = None;
    }
    if BUSY.load(std::sync::atomic::Ordering::Relaxed) || !(game.serving.is_some() || game.options.dedicated.is_some()) {
        return;
    }
    let Some(stack) = game.inventory[game.selected].clone() else { return };
    let Some(mine) = area_tag(&stack.item) else { return };
    let fits = |game: &Game<'_>, block: &str| {
        let items = game.res.items();
        items.block_in_tag(mine, block) && items.correct_for_drops(Some(&stack), block)
    };
    if !fits(game, &game.native_block(pos)) {
        return;
    }
    let hardness = |game: &Game<'_>, p: [i32; 3]| game.res.facts().get(game.world.block(p[0], p[1], p[2])).hardness;
    let limit = hardness(game, pos) * 10.0;
    for p in around(game, pos) {
        let h = hardness(game, p);
        if fits(game, &game.native_block(p)) && h >= 0.0 && h <= limit
            && let Ok(mut q) = PENDING.lock()
        {
            q.push(p);
        }
    }
}

pub fn player_tick(game: &mut Game<'_>) {
    let list = PENDING.lock().map(|mut q| std::mem::take(&mut *q)).unwrap_or_default();
    if list.is_empty() {
        return;
    }
    BUSY.store(true, std::sync::atomic::Ordering::Relaxed);
    for p in list {
        // The tool may have worn out partway: the rest would otherwise go by bare hand.
        if game.inventory[game.selected].is_none() {
            break;
        }
        let _ = game.break_block(p);
    }
    BUSY.store(false, std::sync::atomic::Ordering::Relaxed);
}

// --- An AIOT's right clicks ----------------------------------------------------------------------------------------------

/// A plain click makes a path, a sneaking click tills. Stripping logs comes with its axe template.
pub fn use_item_on(game: &mut Game<'_>, stack: &ItemStack, pos: [i32; 3], _face: [i32; 3], claimed: &mut bool) {
    let item = &*stack.item;
    if *claimed || !(item.starts_with("longclimb:") && item.ends_with("_aiot")) {
        return;
    }
    if game.native_block([pos[0], pos[1] + 1, pos[2]]) != "minecraft:air" {
        return;
    }
    let sneaking = game.keys.contains(&winit::keyboard::KeyCode::ShiftLeft);
    let block = game.native_block(pos);
    let dim = game.native_dimension().to_owned();
    let items = game.res.items();
    let (target, sound) = if sneaking && items.block_in_tag("minecraft:turns_into_farmland", &block) {
        ("minecraft:farmland", "minecraft:item.hoe.till")
    } else if !sneaking && items.block_in_tag("minecraft:turns_into_dirt_path", &block) {
        ("minecraft:dirt_path", "minecraft:item.shovel.flatten")
    } else {
        return;
    };
    let Some(state) = game.pack.assets.registry.default_state(target) else { return };
    if game.native_set_block(&dim, pos, state, 3) {
        game.native_run_command(&format!("playsound {sound} block @a {} {} {} 1 1", pos[0], pos[1], pos[2]));
        game.damage_held(1);
        *claimed = true;
    }
}

// --- The recipe panel ----------------------------------------------------------------------------------------------------

/// The panel's page as the game makes it, with room for a 5x5 grid and a long shapeless list.
pub fn panel_page(game: &mut Game<'_>, mod_id: &str, title: &str, tabs: &[super::native_hooks::NativeStack], tab: u32, views: &[super::native_hooks::NativeRecipeView]) {
    let mut recipes = views.to_vec();
    recipes.truncate(256);
    for r in &mut recipes {
        r.width = r.width.clamp(1, 5);
        r.height = r.height.clamp(1, 8);
        r.slots.truncate(40);
        for list in &mut r.slots {
            list.truncate(64);
        }
        r.results.truncate(64);
    }
    let page = (!recipes.is_empty()).then(|| {
        let mut tabs = tabs.to_vec();
        tabs.truncate(16);
        super::native_panel_recipes::RecipePage { title: title.to_owned(), tabs, tab, recipes }
    });
    game.panel.show_recipes(mod_id, page);
}
