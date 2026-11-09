// Mining Tooltips: every tool's durability and mining level in its tooltip, and the level a block needs when you look at it.
// Levels are Ore Overhaul Long Climb's (its needs_level and incorrect_for_level tags); without it, vanilla's tiers.
use super::Game;
use horizon_client::hud::{HudBatch, rgba};
use horizon_client::items::{ItemStack, Items};
use horizon_client::text::Text;
use horizon_world::nbt::Tag;
use std::collections::HashMap;
use std::sync::OnceLock;

pub const ID: &str = "miningtips";
const TINKERS: &str = "ddsstinkers:tool";

#[derive(serde::Deserialize, Default)]
struct Levels {
    names: Vec<String>,
    vanilla: HashMap<String, i32>,
}

fn levels() -> &'static Levels {
    static L: OnceLock<Levels> = OnceLock::new();
    L.get_or_init(|| serde_json::from_slice(horizon_client::native_data!("miningtips", "levels.json")).unwrap_or_default())
}

fn named(level: i32) -> String {
    match levels().names.get(level.max(0) as usize) {
        Some(n) => format!("{level} ({n})"),
        None => level.to_string(),
    }
}

fn tinkers_tag(stack: &ItemStack) -> Option<&Tag> {
    stack.data()?.other(TINKERS)
}

fn int(tag: &Tag, key: &str) -> Option<i32> {
    match tag.get(key)? {
        Tag::Int(v) => Some(*v),
        _ => None,
    }
}

/// A tool's mining level: a modular tool's own, else the tier its rules leave out.
pub fn tool_level(items: &Items, stack: &ItemStack) -> Option<i32> {
    if let Some(t) = tinkers_tag(stack) {
        return int(t, "mine").filter(|m| *m != 0).and(int(t, "lvl"));
    }
    let info = items.get(&stack.item)?;
    for rule in &info.tool {
        for b in &rule.blocks {
            if let Some(n) = b.strip_prefix("#longclimb:incorrect_for_level_") {
                return n.parse().ok();
            }
            if let Some(tier) = b.strip_prefix("#minecraft:incorrect_for_").and_then(|r| r.strip_suffix("_tool")) {
                return levels().vanilla.get(tier).copied();
            }
        }
    }
    None
}

/// The level a block needs: the highest of Long Climb's tags it is in (vanilla's own tiers sit in the low ones too), else
/// vanilla's three.
pub fn needed_level(items: &Items, block: &str) -> Option<i32> {
    if let Some(n) = (0..=50).rev().find(|n| items.block_in_tag(&format!("longclimb:needs_level_{n}"), block)) {
        return Some(n);
    }
    [("diamond", 20), ("iron", 8), ("stone", 1)]
        .into_iter()
        .find(|(tier, _)| items.block_in_tag(&format!("minecraft:needs_{tier}_tool"), block))
        .map(|(_, n)| n)
}

/// Tooltip lines take their colour as `rgba` packs it.
fn col(rgb: u32) -> u32 {
    rgba((rgb >> 16 & 255) as u8, (rgb >> 8 & 255) as u8, (rgb & 255) as u8, 255)
}

pub fn tooltip(game: &Game<'_>, stack: &ItemStack, lines: &mut Vec<(Text, u32)>) {
    if !game.native_on(ID) {
        return;
    }
    let items = game.res.items();
    // Modular tools list their own numbers: their level gets its tier's name.
    if let Some(t) = tinkers_tag(stack) {
        if let Some(lv) = int(t, "lvl") {
            for line in lines.iter_mut() {
                if line.0.plain() == format!("Mining level {lv}") {
                    line.0 = Text::literal(format!("Mining level {}", named(lv)));
                    line.1 = col(0xFFAA00);
                }
            }
        }
        return;
    }
    if let Some(lv) = tool_level(items, stack) {
        lines.push((Text::literal(format!("Mining level {}", named(lv))), col(0xFFAA00)));
    }
    if let Some(info) = items.get(&stack.item)
        && info.max_damage > 0
    {
        let max = info.max_damage;
        let left = max.saturating_sub(stack.damage);
        let share = left as f32 / max as f32;
        let colour = if share > 0.5 { 0x55FF55 } else if share > 0.2 { 0xFFFF55 } else { 0xFF5555 };
        lines.push((Text::literal(format!("Durability {left} / {max}")), col(colour)));
    }
    // A block in the inventory: what it takes to mine.
    if let Some(lv) = needed_level(items, &stack.item) {
        lines.push((Text::literal(format!("Needs mining level {}", named(lv))), col(0xFFAA00)));
    }
}

/// Whether the line under the hotbar shows: on (only for a block you can't mine yet) or off. Tooltips always show.
fn shown(game: &Game<'_>) -> bool {
    game.native_setting(ID, "block").as_deref() != Some("off")
}

/// Above the hotbar, only while what you look at needs more than the tool in hand: the level it needs and what you hold.
pub fn hud(game: &Game<'_>, batch: &mut HudBatch) {
    // Tests read what the held item's tooltip would get, as text and colour.
    if std::env::var_os("MININGTIPS_DEBUG").is_some()
        && let Some(stack) = game.held()
    {
        static LAST: std::sync::Mutex<String> = std::sync::Mutex::new(String::new());
        let mut lines = Vec::new();
        tooltip(game, stack, &mut lines);
        let text: Vec<String> = lines.iter().map(|(t, c)| format!("{} #{c:08X}", t.plain())).collect();
        let key = format!("{} {}", stack.item, text.join(" | "));
        if let Ok(mut last) = LAST.lock()
            && *last != key
        {
            eprintln!("[miningtips] {key}");
            *last = key;
        }
    }
    if !game.native_on(ID) || !shown(game) || game.screen != super::Screen::Playing {
        return;
    }
    let Some(hit) = game.pick() else { return };
    let block = game.native_block(hit.pos);
    let items = game.res.items();
    let Some(need) = needed_level(items, &block) else { return };
    let held = game.held();
    if items.correct_for_drops(held, &block) {
        return;
    }
    let line = match held.and_then(|s| tool_level(items, s)) {
        Some(lv) => format!("Needs mining level {} - your tool is {}", named(need), named(lv)),
        None => format!("Needs mining level {} - and a pickaxe", named(need)),
    };
    let w = game.native_text_width(&line);
    game.native_text(batch, &line, [((batch.width - w) / 2.0).floor(), batch.height - 82.0], 0xFF5555, true);
}

pub fn listed(mods: &mut Vec<crate::game::native_hooks::NativeMod>) {
    mods.push(crate::game::native_hooks::NativeMod {
        id: ID.into(),
        title: "Mining Tooltips 1.1".into(),
        description: "Durability and mining level on every tool and ore, and a warning when the block you look at needs a better tool.".into(),
        keys: Vec::new(),
    });
}

pub fn settings(game: &mut Game<'_>, mod_id: &str, buttons: &mut Vec<String>) {
    if mod_id != ID {
        return;
    }
    buttons.push(format!("Level warning above the hotbar: {}", if shown(game) { "On" } else { "Off" }));
}

pub fn settings_click(game: &mut Game<'_>, mod_id: &str, button: usize) {
    if mod_id != ID || button != 0 {
        return;
    }
    let next = if shown(game) { "off" } else { "on" };
    game.native_set_setting(ID, "block", next);
}
