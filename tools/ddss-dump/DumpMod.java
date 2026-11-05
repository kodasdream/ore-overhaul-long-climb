package ddssdump;

import java.io.*;
import java.lang.reflect.*;
import java.util.*;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.common.event.FMLServerStartedEvent;

/** One-off: writes TinkerRegistry's final state as JSON. Reflection only, so it needs no deobfuscated Minecraft on the compile path. */
@Mod(modid = "ddssdump", name = "DDSS Tinkers dump", version = "1", acceptableRemoteVersions = "*")
public class DumpMod {
    static Object call(Object o, String m, Object... args) {
        try {
            Class<?> c = o instanceof Class ? (Class<?>) o : o.getClass();
            for (Method x : c.getMethods()) {
                if (x.getName().equals(m) && x.getParameterCount() == args.length) {
                    x.setAccessible(true);
                    return x.invoke(o instanceof Class ? null : o, args);
                }
            }
        } catch (Throwable t) { return "ERR:" + t; }
        return "NOMETHOD:" + m;
    }
    static Object reg(Object o) {
        try {
            return Class.forName("net.minecraftforge.registries.IForgeRegistryEntry").getMethod("getRegistryName").invoke(o);
        } catch (Throwable t) { return "ERR:" + t; }
    }
    static Iterable<?> iter(Object o) {
        if (o instanceof Iterable) return (Iterable<?>) o;
        if (o instanceof Object[]) return Arrays.asList((Object[]) o);
        return Collections.emptyList();
    }
    static Object viaHandle(Object target, String cls, String name, Class<?> ret) {
        try {
            Class<?> c = Class.forName(cls);
            return java.lang.invoke.MethodHandles.lookup().findVirtual(c, name, java.lang.invoke.MethodType.methodType(ret)).invoke(target);
        } catch (Throwable t) { return "ERR:" + t; }
    }
    static String q(Object s) {
        String t = String.valueOf(s);
        StringBuilder b = new StringBuilder("\"");
        for (char ch : t.toCharArray()) {
            if (ch == '"' || ch == '\\') b.append('\\').append(ch);
            else if (ch < 32) b.append(' ');
            else if (ch > 126) b.append(String.format("\\u%04x", (int) ch));
            else b.append(ch);
        }
        return b.append('"').toString();
    }
    static String fields(Object o) throws Exception {
        StringBuilder b = new StringBuilder("{");
        boolean first = true;
        for (Field f : o.getClass().getFields()) {
            if (Modifier.isStatic(f.getModifiers())) continue;
            Object v = f.get(o);
            if (!(v instanceof Number || v instanceof String || v instanceof Boolean)) continue;
            if (!first) b.append(',');
            first = false;
            b.append(q(f.getName())).append(':').append(v instanceof Number || v instanceof Boolean ? String.valueOf(v) : q(v));
        }
        return b.append('}').toString();
    }
    static String stack(Object st) {
        if (st == null) return "null";
        Object item = call(st, "func_77973_b");
        Object reg = DumpMod.reg(item);
        Object meta = call(st, "func_77960_j");
        return q(reg + ":" + meta);
    }
    static String fluid(Object fs) {
        if (fs == null) return "null";
        try {
            Object fl = fs.getClass().getMethod("getFluid").invoke(fs);
            int amt = fs.getClass().getField("amount").getInt(fs);
            return "{\"fluid\":" + q(call(fl, "getName")) + ",\"amount\":" + amt + "}";
        } catch (Throwable t) { return q("ERR:" + t); }
    }

    static void casting(PrintWriter w, Object all) {
        boolean first = true;
        for (Object r : iter(all)) {
            if (!first) w.println(",");
            first = false;
            String fl = "null", out = "null", cast = "null";
            Object consume = "null", time = "null";
            try { fl = fluid(r.getClass().getField("fluid").get(r)); } catch (Throwable t) { }
            try { out = stack(r.getClass().getField("output").get(r)); } catch (Throwable t) { }
            try {
                Object c = r.getClass().getField("cast").get(r);
                if (c != null) {
                    StringBuilder b = new StringBuilder("[");
                    int n = 0;
                    for (Object st : iter(call(c, "getInputs"))) { if (n++ > 2) break; if (n > 1) b.append(','); b.append(stack(st)); }
                    cast = b.append(']').toString();
                }
            } catch (Throwable t) { }
            try { consume = call(r, "consumesCast"); time = call(r, "getTime"); } catch (Throwable t) { }
            w.print("{\"class\":" + q(r.getClass().getSimpleName()) + ",\"fluid\":" + fl + ",\"output\":" + out + ",\"cast\":" + cast + ",\"consume\":" + q(consume) + ",\"time\":" + q(time) + "}");
        }
    }

    @Mod.EventHandler
    public void started(FMLServerStartedEvent e) throws Exception {
        Class<?> reg = Class.forName("slimeknights.tconstruct.library.TinkerRegistry");
        PrintWriter w = new PrintWriter(new FileWriter("ddss_tinkers.json"), true);
        w.println("{\"materials\":[");
        boolean first = true;
        for (Object m : (Collection<?>) call(reg, "getAllMaterials")) {
            if (!first) w.println(",");
            first = false;
            w.print("{\"id\":" + q(call(m, "getIdentifier")));
            w.print(",\"color\":" + m.getClass().getField("materialTextColor").get(m));
            w.print(",\"craftable\":" + call(m, "isCraftable") + ",\"castable\":" + call(m, "isCastable") + ",\"hidden\":" + call(m, "isHidden"));
            Object fl = call(m, "getFluid");
            w.print(",\"fluid\":" + (fl == null ? "null" : q(call(fl, "getName"))));
            w.print(",\"rep\":" + stack(call(m, "getRepresentativeItem")));
            w.print(",\"shard\":" + stack(call(m, "getShard")));
            w.print(",\"stats\":{");
            boolean f2 = true;
            for (Object s : (Collection<?>) call(m, "getAllStats")) {
                if (!f2) w.print(",");
                f2 = false;
                w.print(q(call(s, "getIdentifier")) + ":" + fields(s));
            }
            w.print("},\"traits\":{");
            f2 = true;
            for (Object s : (Collection<?>) call(m, "getAllStats")) {
                String sid = String.valueOf(call(s, "getIdentifier"));
                Object ts = call(m, "getAllTraitsForStats", sid);
                if (!(ts instanceof Collection)) continue;
                if (!f2) w.print(",");
                f2 = false;
                w.print(q(sid) + ":[");
                boolean f3 = true;
                for (Object t : (Collection<?>) ts) {
                    if (!f3) w.print(",");
                    f3 = false;
                    w.print(q(call(t, "getIdentifier")));
                }
                w.print("]");
            }
            w.print("}}");
        }
        w.println("],\n\"parts\":[");
        first = true;
        for (Object p : (Collection<?>) call(reg, "getToolParts")) {
            if (!first) w.println(",");
            first = false;
            w.print("{\"id\":" + q(reg(p)) + ",\"cost\":" + viaHandle(p, "slimeknights.tconstruct.library.tools.IToolPart", "getCost", int.class) + "}");
        }
        w.println("],\n\"tools\":[");
        first = true;
        Set<Object> forge = new HashSet<Object>((Collection<?>) call(reg, "getToolForgeCrafting"));
        Set<Object> station = new HashSet<Object>((Collection<?>) call(reg, "getToolStationCrafting"));
        for (Object t : (Collection<?>) call(reg, "getTools")) {
            if (!first) w.println(",");
            first = false;
            w.print("{\"id\":" + q(reg(t)) + ",\"class\":" + q(t.getClass().getName()));
            w.print(",\"forge\":" + forge.contains(t) + ",\"station\":" + station.contains(t) + ",\"components\":[");
            boolean f2 = true;
            for (Object pmt : iter(viaHandle(t, "slimeknights.tconstruct.library.tinkering.TinkersItem", "getRequiredComponents", List.class))) {
                if (!f2) w.print(",");
                f2 = false;
                StringBuilder parts = new StringBuilder("[");
                Field pf = null;
                for (Field f : pmt.getClass().getDeclaredFields()) if (f.getName().equals("validParts")) pf = f;
                if (pf != null) {
                    pf.setAccessible(true);
                    boolean f3 = true;
                    for (Object tp : iter(pf.get(pmt))) {
                        if (!f3) parts.append(',');
                        f3 = false;
                        parts.append(q(reg(tp)));
                    }
                }
                parts.append(']');
                StringBuilder types = new StringBuilder("[");
                Field nf = null;
                for (Field f : pmt.getClass().getDeclaredFields()) if (f.getName().equals("neededTypes")) nf = f;
                if (nf != null) {
                    nf.setAccessible(true);
                    boolean f3 = true;
                    for (Object tp : iter(nf.get(pmt))) {
                        if (!f3) types.append(',');
                        f3 = false;
                        types.append(q(tp));
                    }
                }
                types.append(']');
                w.print("{\"parts\":" + parts + ",\"types\":" + types + "}");
            }
            w.print("]}");
        }
        w.println("],\n\"modifiers\":[");
        first = true;
        for (Object m : (Collection<?>) call(reg, "getAllModifiers")) {
            if (!first) w.println(",");
            first = false;
            w.print("{\"id\":" + q(call(m, "getIdentifier")) + ",\"class\":" + q(m.getClass().getName()) + ",\"hidden\":" + call(m, "isHidden") + "}");
        }
        w.println("],\n\"melting\":[");
        first = true;
        for (Object r : (Collection<?>) call(reg, "getAllMeltingRecipies")) {
            if (!first) w.println(",");
            first = false;
            Object in = r.getClass().getField("input").get(r);
            StringBuilder inputs = new StringBuilder("[");
            Object inputsObj = call(in, "getInputs");
            if (inputsObj instanceof Collection) {
                boolean f3 = true;
                int n = 0;
                for (Object st : (Collection<?>) inputsObj) {
                    if (n++ > 3) break;
                    if (!f3) inputs.append(',');
                    f3 = false;
                    inputs.append(stack(st));
                }
            }
            inputs.append(']');
            w.print("{\"inputs\":" + inputs + ",\"output\":" + fluid(r.getClass().getField("output").get(r)) + ",\"temp\":" + call(r, "getTemperature") + "}");
        }
        w.println("],\n\"alloys\":[");
        first = true;
        for (Object a : (Collection<?>) call(reg, "getAlloys")) {
            if (!first) w.println(",");
            first = false;
            StringBuilder fs = new StringBuilder("[");
            boolean f3 = true;
            for (Object x : (Collection<?>) call(a, "getFluids")) {
                if (!f3) fs.append(',');
                f3 = false;
                fs.append(fluid(x));
            }
            fs.append(']');
            w.print("{\"result\":" + fluid(call(a, "getResult")) + ",\"inputs\":" + fs + "}");
        }
        w.println("],\n\"fuels\":[");
        first = true;
        for (Object fu : (Collection<?>) call(reg, "getSmelteryFuels")) {
            if (!first) w.println(",");
            first = false;
            w.print(fluid(fu));
        }
        w.println("],\n\"table_casting\":[");
        casting(w, call(reg, "getAllTableCastingRecipes"));
        w.println("],\n\"basin_casting\":[");
        casting(w, call(reg, "getAllBasinCastingRecipes"));
        w.println("],\n\"drying\":[");
        first = true;
        for (Object r : iter(call(reg, "getAllDryingRecipes"))) {
            if (!first) w.println(",");
            first = false;
            w.print("{\"output\":" + stack(call(r, "getResult")) + ",\"time\":" + call(r, "getTime") + "}");
        }
        w.println("]}");
        w.close();
        System.out.println("DDSSDUMP-WRITTEN");
    }
}
