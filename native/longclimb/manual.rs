// The Long Climb manual: a book opened with a key (B by default; Options > Mods changes it). Its pages are gen/manual.py's.
use super::Game;
use horizon_client::text::{ClickEvent, Style, Text};

pub const ID: &str = "longclimb";
pub const KEY: [&str; 3] = ["manual", "Open the Long Climb manual", "key.keyboard.b"];

#[derive(serde::Deserialize)]
struct Span {
    t: String,
    c: u32,
    b: bool,
    p: Option<i32>,
}
#[derive(serde::Deserialize)]
struct Manual {
    pages: Vec<Vec<Span>>,
}

fn pages() -> Vec<Text> {
    let Ok(m) = serde_json::from_slice::<Manual>(horizon_client::native_data!("longclimb", "manual.json")) else {
        return vec![Text::literal("The manual's pages are missing.")];
    };
    m.pages
        .into_iter()
        .map(|spans| {
            let mut page = Text::empty();
            for s in spans {
                let mut t = Text::colored(s.t, s.c);
                if s.b {
                    t = t.bold();
                }
                if let Some(p) = s.p {
                    t = t.underlined().with_style(&Style { click: Some(ClickEvent::ChangePage(p)), ..Style::default() });
                }
                page.push(t);
            }
            page
        })
        .collect()
}

/// The row in Options > Mods, with the manual's key.
pub fn listed(mods: &mut Vec<crate::game::native_hooks::NativeMod>) {
    mods.push(crate::game::native_hooks::NativeMod {
        id: ID.into(),
        title: "Ore Overhaul Long Climb".into(),
        description: "50 ore tiers, the 5x5 table, hammers, excavators and AIOTs. Its manual opens with a key.".into(),
        keys: vec![KEY.map(String::from)],
    });
}

static TAPPED: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);

/// A real key press, however short: the next frame opens the manual (a tap can begin and end between two frames).
pub fn key(game: &Game<'_>, event: &winit::event::KeyEvent) {
    if event.state != winit::event::ElementState::Pressed || event.repeat {
        return;
    }
    let winit::keyboard::PhysicalKey::Code(code) = event.physical_key else { return };
    if horizon_client_input::keybinds::key_name(code) == Some(game.native_mod_key(ID, KEY[0], KEY[2]).as_str()) {
        TAPPED.store(true, std::sync::atomic::Ordering::Relaxed);
    }
}

/// The key, pressed while playing: the manual opens on its first page. Checked once a frame against the keys held, so a
/// press counts once however long it is held.
pub fn frame(game: &mut Game<'_>) {
    use std::sync::atomic::{AtomicBool, Ordering};
    static HELD: AtomicBool = AtomicBool::new(false);
    if !game.native_on(ID) {
        return;
    }
    let chosen = game.native_mod_key(ID, KEY[0], KEY[2]);
    let down = game.keys.iter().any(|c| horizon_client_input::keybinds::key_name(*c) == Some(chosen.as_str()));
    let was = HELD.swap(down, Ordering::Relaxed);
    let tapped = TAPPED.swap(false, Ordering::Relaxed);
    if !(tapped || down && !was) || game.screen != super::Screen::Playing || game.book.is_some() {
        return;
    }
    game.book = Some(super::books::BookScreen::View { pages: pages(), page: 0, lectern: None });
    game.keys.clear();
    game.right = false;
    game.capture(false);
}

// --- The day clock -------------------------------------------------------------------------------------------------------

/// Whether the clock shows (on unless turned off in Options > Mods).
fn clock_on(game: &Game<'_>) -> bool {
    game.native_setting(ID, "clock").as_deref() != Some("off")
}

/// The world's time of day as a 24-hour clock: tick 0 is 06:00, 1000 ticks an hour.
pub fn clock_text(day_time: i64) -> String {
    let t = day_time.rem_euclid(24000);
    let hours = (t / 1000 + 6) % 24;
    let minutes = (t % 1000) * 60 / 1000;
    format!("{hours:02}:{minutes:02}")
}

/// Under the minimap, in its corner (top right without one), as wide as the map.
pub fn clock(game: &Game<'_>, batch: &mut horizon_client::hud::HudBatch, corners: &mut horizon_client::extras_hud::Corners) {
    if !game.native_on(ID) || !clock_on(game) || game.player.is_none() {
        return;
    }
    let (corner, width) = game
        .native_minimap_now()
        .map_or((horizon_client::extras::Corner::TopRight, 40.0), |m| (m.corner, m.size));
    let text = clock_text(game.native_day_time());
    let (x, y) = corners.place(corner, width, 10.0);
    let w = game.native_text_width(&text);
    game.native_fill(batch, [x + (width - w) / 2.0 - 2.0, y - 1.0, w + 4.0, 11.0], 0x7800_0000);
    game.native_text(batch, &text, [(x + (width - w) / 2.0).floor(), y], 0xFFFFFF, true);
}

pub fn settings(game: &mut Game<'_>, mod_id: &str, buttons: &mut Vec<String>) {
    if mod_id == ID {
        buttons.push(format!("Clock under the minimap: {}", if clock_on(game) { "On" } else { "Off" }));
    }
}

pub fn settings_click(game: &mut Game<'_>, mod_id: &str, button: usize) {
    if mod_id == ID && button == 0 {
        let next = if clock_on(game) { "off" } else { "on" };
        game.native_set_setting(ID, "clock", next);
    }
}
