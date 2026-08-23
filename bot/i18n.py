"""ThunderWatch MY — Bahasa Melayu / English string tables for the bot."""

STRINGS = {
    "en": {
        "advisory_title": "⛈ *Thunderstorm Risk Advisory*",
        "elevated": "Elevated thunderstorm indicators detected *~{dist} km {direction}* of your location (based on current forecast data).",
        "trend_approaching": "Prevailing winds suggest possible movement toward your area over the next 1–2 hours.",
        "trend_receding": "Prevailing winds suggest the activity is moving away from your area.",
        "risk_line": "Risk Level: *{level}* (score {score}/100)",
        "rec": "Recommendation: {text}",
        "rec_severe": "Take shelter now; postpone all outdoor plans.",
        "rec_high": "Prepare for heavy rain; avoid outdoor activity.",
        "rec_moderate": "Keep an eye on the sky; plan indoor alternatives.",
        "rec_low": "No action needed right now.",
        "no_elevated": "No elevated thunderstorm risk within ~30 km right now (*{level}*, score {score}/100).",
        "warnings": "⚠️ Official MetMalaysia warning active: {titles}",
        "view_map": "🗺 View live map: {link}",
        "level_low": "Low", "level_moderate": "Moderate", "level_high": "High", "level_severe": "Severe",
        "welcome": "⛈ ThunderWatch MY — share your location (📎 → Location) or send 'lat lon' for storm risk near you.\nOr try the commute advisor: /commute",
        "lang_set": "🇲🇾 Language set to Bahasa Melayu. Send /en to switch back.",
        # commute
        "commute_help": "🚦 *Commute weather advisor*\n\nSend your route like this:\n`/commute Gombak | KL Sentral`\n\nI'll ask your transport mode, check weather along the route, and suggest a safer alternative if heavy rain is expected.",
        "commute_ask": "🚦 Commute check: *{origin}* → *{dest}*\nHow are you travelling?",
        "mode_motorcycle": "🏍 Motorcycle", "mode_car": "🚗 Car", "mode_pt": "🚆 Public Transport",
        "commute_title": "🚦 *Commute Weather Check: {origin} → {dest}*",
        "commute_meta": "Mode: {mode} · window: next 6 hours",
        "commute_ok": "✅ Conditions look manageable for your chosen mode (worst along route: *{level}*, score {score}/100{precip}).",
        "commute_ok_rain_jacket": "Ride safe — carry a rain jacket just in case.",
        "commute_heavy": "⚠️ *Heavy rain likely along your route* (peak around {when}, score {score}/100{precip}).",
        "commute_switch_moto": "Motorcycle travel is risky in these conditions. *Consider switching to public transport:*",
        "commute_alt_stations": "🚆 Walk/ride to *{o}* ({od} km away) → rail to *{d}* near your destination.",
        "commute_switch_car": "Expect slow traffic and reduced visibility. Leave earlier, or switch to rail if available:",
        "commute_alt_nearest": "🚆 Nearest station to you: *{o}* ({od} km).",
        "commute_note": "_Weather checked along the straight-line corridor between origin and destination; the map link shows the suggested driving route (OSRM)._",
        "commute_restart": "Start again with /commute.",
        "commute_geofail": "Sorry, I couldn't find one of those places. Try /commute again.",
        "mode_label_motorcycle": "Motorcycle 🏍", "mode_label_car": "Car 🚗", "mode_label_pt": "Public Transport 🚆",
    },
    "bm": {
        "advisory_title": "⛈ *Nasihat Risiko Ribut Petir*",
        "elevated": "Petunjuk ribut petir yang ketara dikesan *~{dist} km di {direction}* lokasi anda (berdasarkan data ramalan semasa).",
        "trend_approaching": "Angin semasa menunjukkan kemungkinan pergerakan ke arah kawasan anda dalam masa 1–2 jam.",
        "trend_receding": "Angin semasa menunjukkan ribut mungkin bergerak menjauhi kawasan anda.",
        "risk_line": "Tahap Risiko: *{level}* (skor {score}/100)",
        "rec": "Cadangan: {text}",
        "rec_severe": "Berteduh sekarang; tangguhkan semua aktiviti luar.",
        "rec_high": "Bersedia untuk hujan lebat; elakkan aktiviti luar.",
        "rec_moderate": "Pantau keadaan langit; sediakan pelan alternatif dalam bangunan.",
        "rec_low": "Tiada tindakan diperlukan buat masa ini.",
        "no_elevated": "Tiada risiko ribut petir yang ketara dalam lingkungan ~30 km buat masa ini (*{level}*, skor {score}/100).",
        "warnings": "⚠️ Amaran rasmi MetMalaysia aktif: {titles}",
        "view_map": "🗺 Lihat peta langsung: {link}",
        "level_low": "Rendah", "level_moderate": "Sederhana", "level_high": "Tinggi", "level_severe": "Kritikal",
        "welcome": "⛈ ThunderWatch MY — kongsi lokasi anda (📎 → Lokasi) atau hantar 'lat lon' untuk risiko ribut berhampiran anda.\nAtau cuba penasihat perjalanan: /commute",
        "lang_set": "🇬🇧 Language set to English. Hantar /bm untuk Bahasa Melayu.",
        # commute
        "commute_help": "🚦 *Penasihat cuaca perjalanan*\n\nHantar laluan anda seperti ini:\n`/commute Gombak | KL Sentral`\n\nSaya akan tanya mod pengangkutan anda, semak cuaca sepanjang laluan, dan cadangkan alternatif yang lebih selamat jika hujan lebat dijangka.",
        "commute_ask": "🚦 Semakan perjalanan: *{origin}* → *{dest}*\nApakah mod pengangkutan anda?",
        "mode_motorcycle": "🏍 Motosikal", "mode_car": "🚗 Kereta", "mode_pt": "🚆 Pengangkutan Awam",
        "commute_title": "🚦 *Semakan Cuaca Perjalanan: {origin} → {dest}*",
        "commute_meta": "Mod: {mode} · tempoh: 6 jam akan datang",
        "commute_ok": "✅ Keadaan kelihatan baik untuk mod pilihan anda (terburuk sepanjang laluan: *{level}*, skor {score}/100{precip}).",
        "commute_ok_rain_jacket": "Tunggang dengan selamat — bawa baju hujan untuk berjaga-jaga.",
        "commute_heavy": "⚠️ *Hujan lebat mungkin berlaku sepanjang laluan anda* (puncak sekitar {when}, skor {score}/100{precip}).",
        "commute_switch_moto": "Menunggang motosikal berisiko dalam keadaan ini. *Pertimbangkan untuk bertukar ke pengangkutan awam:*",
        "commute_alt_stations": "🚆 Pergi ke *{o}* ({od} km dari anda) → kereta api ke *{d}* berhampiran destinasi anda.",
        "commute_switch_car": "Jangkaan trafik perlahan dan penglihatan terhad. Bertolak lebih awal, atau tukar ke kereta api jika ada:",
        "commute_alt_nearest": "🚆 Stesen terdekat dengan anda: *{o}* ({od} km).",
        "commute_note": "_Cuaca disemak sepanjang koridor garis lurus antara asal dan destinasi; pautan peta menunjukkan laluan pemanduan yang dicadangkan (OSRM)._",
        "commute_restart": "Mulakan semula dengan /commute.",
        "commute_geofail": "Maaf, saya tidak dapat mencari salah satu lokasi itu. Cuba /commute sekali lagi.",
        "mode_label_motorcycle": "Motosikal 🏍", "mode_label_car": "Kereta 🚗", "mode_label_pt": "Pengangkutan Awam 🚆",
    },
}

LEVEL_KEYS = {"Low": "level_low", "Moderate": "level_moderate",
              "High": "level_high", "Severe": "level_severe"}


def t(lang, key, **kw):
    s = STRINGS.get(lang, STRINGS["en"]).get(key) or STRINGS["en"].get(key, key)
    return s.format(**kw) if kw else s


def level_name(lang, level):
    return t(lang, LEVEL_KEYS.get(level, "level_low"))
